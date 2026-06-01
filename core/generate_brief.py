"""
generate_brief.py
=================
Reads news themes from the latest news_themes_*.xlsx,
generates per-competitor summaries and executive summary using Claude.

NO Claude calls for individual theme summaries — uses existing
summaries already in the Excel file from google_news_scraper.py.

Claude is used ONLY for:
1. Per-competitor summary (one call per competitor)
2. Executive summary + top 3 market trends (one final call)

Outputs:
  data/monthly_market_trends_YYYY_MM.json  — structured data for dashboard
  data/monthly_market_trends_YYYY_MM.md    — markdown version

Run via GitHub Actions — add to monthly_scrape.yml as final step.
"""

import anthropic
import argparse
import glob
import json
import os
import re
import time
from datetime import datetime
from pathlib import Path

import pandas as pd

# ─────────────────────────────────────────────
# PROMPTS — Claude used only here
# ─────────────────────────────────────────────

SINGLE_CALL_PROMPT = """You are a competitive intelligence analyst tracking the AI and technology competitive landscape.

Month: {month}
Competitors: {competitors}

Here are all competitive news themes this month, grouped by competitor.
Themes are ordered: Product Launch and Ecosystem themes first, then Company News.

{all_themes}

Return a single JSON object with EXACTLY this structure — no markdown, no preamble:
{{
  "executive_summary": "4-5 sentence summary of the most important competitive developments this month. Reference specific competitors, key product launches, strategic moves, and market implications.",
  "market_trends": [
    "Trend title: 2 sentence explanation of the AI/tech market trend with specific competitor examples",
    "Trend title: 2 sentence explanation with specific competitor examples",
    "Trend title: 2 sentence explanation with specific competitor examples",
    "Trend title: 2 sentence explanation with specific competitor examples",
    "Trend title: 2 sentence explanation with specific competitor examples"
  ],
  "competitor_summaries": {{
    "CompetitorName": "3-4 sentence paragraph. Lead with card product/loyalty program changes and their competitive implications. Then cover company news that affects card strategy. If only corrupted or unavailable data exists for some themes, write the summary based on the themes you do have — never say you cannot provide a summary.",
    "CompetitorName2": "..."
  }}
}}

IMPORTANT:
- market_trends must have EXACTLY 5 items, no more, no less
- competitor_summaries must include ALL competitors listed above
- For competitors with limited data, write what you can from available themes
- Never return "I cannot provide" — always write something based on available data
- Do NOT reference "travel credit cards", "card products", or "payment products" — focus on AI and technology competitive dynamics
- Return ONLY the JSON object, no markdown fences
}}"""


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def find_latest_themes(data_dir):
    """Find most recent news_themes xlsx."""
    files = glob.glob(os.path.join(data_dir, "news_themes_*.xlsx"))
    if not files:
        files = glob.glob(os.path.join(data_dir, "google_news_*.xlsx"))
    return sorted(files)[-1] if files else None


def extract_year_month(filepath):
    match = re.search(r"(\d{4})_(\d{2})", filepath)
    if match:
        return f"{match.group(1)}-{match.group(2)}"
    return datetime.now().strftime("%Y-%m")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def generate_brief(data_dir, year_month=None):
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set")
        return None

    client = anthropic.Anthropic(api_key=api_key)

    # Find themes file
    themes_file = find_latest_themes(data_dir)
    if not themes_file:
        print(f"❌ No themes file found in {data_dir}")
        return None

    year_month = year_month or extract_year_month(themes_file)
    print(f"\n{'='*60}")
    print(f"  Generating brief for {year_month}")
    print(f"  Source: {themes_file}")
    print(f"{'='*60}\n")

    # Load Themes sheet
    try:
        df = pd.read_excel(themes_file, sheet_name="Themes")
    except Exception as e:
        print(f"❌ Could not read Themes sheet: {e}")
        return None

    # Normalize column names
    df.columns = [c.lower().replace(" ", "_").replace("#", "num") for c in df.columns]
    rename_map = {"num_articles": "article_count"}
    df = df.rename(columns=rename_map)

    if df.empty:
        print("❌ No themes found")
        return None

    print(f"  Loaded {len(df)} themes across {df['company'].nunique()} competitors\n")

    # ── Build theme_summaries from Excel — NO Claude calls ────
    # Use whatever summary is already in the Excel summary column
    theme_summaries = []
    for _, row in df.iterrows():
        theme_summaries.append({
            "company":        str(row.get("company", "")),
            "category":       str(row.get("category", "")),
            "theme":          str(row.get("theme", "")),
            "article_count":  int(row.get("article_count", 0)) if pd.notna(row.get("article_count")) else 0,
            "date_range":     str(row.get("date_range", "")) if pd.notna(row.get("date_range")) else "",
            "summary":        str(row.get("summary", "")) if pd.notna(row.get("summary")) else "",
            "best_headline":  str(row.get("best_headline", "")) if pd.notna(row.get("best_headline")) else "",
            "best_source":    str(row.get("best_source", "")) if pd.notna(row.get("best_source")) else "",
            "best_url":       str(row.get("best_url", "")) if pd.notna(row.get("best_url")) else "",
        })

    # ── Single Claude call for everything ────────────────────
    print("  🤖 Single Claude call — competitor summaries + exec summary + trends...")
    competitors = sorted(df["company"].unique())
    competitor_summaries = {}
    exec_summary = ""
    market_trends = []
    claude_calls = 0

    # Build all themes text grouped by competitor
    # Use Claude-generated summaries from Excel — already concise, fits in one prompt
    # Order: Credit Card Product + Loyalty first, Company News last
    CATEGORY_ORDER = {"Product Launch": 0, "Ecosystem": 1, "Company News": 2}
    all_themes_lines = []

    def is_clean_summary(text):
        if not text or len(str(text)) < 20:
            return False
        t = str(text).lower()
        bad = ["cannot provide", "corrupted", "javascript", "i cannot",
               "unable to", "i cannot extract", "no readable", "obfuscated"]
        return not any(b in t for b in bad)

    for company in competitors:
        company_themes = sorted(
            [t for t in theme_summaries if t["company"] == company],
            key=lambda t: (CATEGORY_ORDER.get(t.get("category", ""), 3), -t.get("article_count", 0))
        )
        if not company_themes:
            continue
        all_themes_lines.append(f"\n### {company}")
        for t in company_themes[:8]:  # cap at 8 themes per competitor
            # Use Claude summary from Excel — already one clean sentence
            summary = t.get("summary", "")
            if not is_clean_summary(summary):
                # Fall back to headline if summary is bad
                summary = t.get("best_headline") or t["theme"]
            all_themes_lines.append(f"- [{t.get('category','')}] {summary}")

    all_themes_text = "\n".join(all_themes_lines)

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4000,
            messages=[{"role": "user", "content": SINGLE_CALL_PROMPT.format(
                month=year_month,
                competitors=", ".join(competitors),
                all_themes=all_themes_text,
            )}]
        )
        raw = response.content[0].text.strip()
        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        import json as _json
        result = _json.loads(raw)

        exec_summary         = result.get("executive_summary", "")
        market_trends        = result.get("market_trends", [])
        competitor_summaries = result.get("competitor_summaries", {})
        claude_calls         = 1

        print(f"  ✅ All summaries generated in 1 API call")
        print(f"     Competitors: {len(competitor_summaries)} | Trends: {len(market_trends)}")

    except Exception as e:
        print(f"  ⚠️  Claude call failed: {e}")
        exec_summary = f"This month tracked {len(competitors)} competitors across {len(theme_summaries)} themes."
        for company in competitors:
            company_themes = [t for t in theme_summaries if t["company"] == company]
            competitor_summaries[company] = (
                f"{company} had {len(company_themes)} notable developments this month."
            )

    # ── Step 3: Save outputs ───────────────────────────────────
    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True)

    fname = f"monthly_market_trends_{year_month.replace('-', '_')}"

    brief = {
        "year_month":           year_month,
        "generated_at":         datetime.now().isoformat(),
        "executive_summary":    exec_summary,
        "market_trends":        market_trends,
        "competitor_summaries": competitor_summaries,
        "theme_summaries":      theme_summaries,
    }

    # JSON
    json_path = os.path.join(output_dir, f"{fname}.json")
    with open(json_path, "w") as f:
        json.dump(brief, f, indent=2)
    print(f"\n  💾 JSON → {json_path}")

    # Markdown
    md_lines = [
        f"# Competitive Intelligence Brief — {year_month}",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | "
        f"Claude calls: {claude_calls}*",
        "", "---", "",
        "## Executive Summary", "", exec_summary, "",
    ]

    if market_trends:
        md_lines += ["## Top 3 Market Trends", ""]
        for i, trend in enumerate(market_trends, 1):
            parts = trend.split(":", 1)
            title = parts[0].strip() if len(parts) > 1 else f"Trend {i}"
            body  = parts[1].strip() if len(parts) > 1 else trend
            md_lines += [f"### Trend {i}: {title}", body, ""]

    md_lines += ["---", "", "## Competitor Analysis", ""]
    for company in competitors:
        company_themes = [t for t in theme_summaries if t["company"] == company]
        if not company_themes:
            continue
        md_lines += [f"### {company}", "", competitor_summaries.get(company, ""), ""]
        for t in sorted(company_themes, key=lambda x: x["article_count"], reverse=True):
            md_lines.append(f"- {t['summary'] or t['theme']}")
            if t["best_url"]:
                md_lines.append(f"  *[{t['best_source']}]({t['best_url']}) · "
                                 f"{t['article_count']} articles · {t['date_range']}*")
        md_lines.append("")

    md_path = os.path.join(output_dir, f"{fname}.md")
    with open(md_path, "w") as f:
        f.write("\n".join(md_lines))
    print(f"  💾 Markdown → {md_path}")

    # Cost summary
    est_cost = claude_calls * 0.003
    print(f"\n{'='*60}")
    print(f"  ✅ Brief complete!")
    print(f"  Claude calls: {claude_calls} (competitors + exec summary only)")
    print(f"  Estimated cost: ~${est_cost:.3f}")
    print(f"{'='*60}\n")

    return brief


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="news/data",
                        help="Directory containing news_themes_*.xlsx")
    parser.add_argument("--year",  type=int)
    parser.add_argument("--month", type=int)
    args = parser.parse_args()

    year_month = None
    if args.year and args.month:
        year_month = f"{args.year}-{args.month:02d}"

    generate_brief(args.data_dir, year_month)


if __name__ == "__main__":
    main()
