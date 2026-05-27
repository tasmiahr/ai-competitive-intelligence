"""
generate_html.py
================
Reads monthly_market_trends_*.json + reddit_sentiment_*.json
and generates docs/dashboard.html — fully self-contained.

Run: python core/generate_html.py
     python core/generate_html.py --data-dir data
"""

import glob
import json
import os
import argparse
from datetime import datetime
from pathlib import Path

DOCS_DIR = "docs"


def find_latest(pattern):
    files = sorted(glob.glob(pattern), reverse=True)
    return files[0] if files else None


def load_json(path):
    if not path:
        return {}
    try:
        with open(path) as f:
            return json.load(f)
    except:
        return {}


def generate_html(data_dir="data"):
    # Brief lives in root data/, Reddit in social/data/
    brief   = load_json(find_latest(os.path.join(data_dir, "monthly_market_trends_*.json")))
    reddit  = load_json(find_latest(os.path.join("social", "data", "reddit_sentiment_*.json")))
    if not reddit:
        # fallback to same data_dir
        reddit = load_json(find_latest(os.path.join(data_dir, "reddit_sentiment_*.json")))

    if not brief:
        print(f"❌ No monthly_market_trends_*.json found in {data_dir}")
        return

    year_month           = brief.get("year_month", "")
    exec_summary         = brief.get("executive_summary", "")
    market_trends        = brief.get("market_trends", [])
    competitor_summaries = brief.get("competitor_summaries", {})
    theme_summaries      = brief.get("theme_summaries", [])
    companies            = list(competitor_summaries.keys())

    # ── Reddit sentiment lookup ────────────────────────────────
    reddit_by_company = {}
    for s in reddit.get("competitor_sentiment", []):
        reddit_by_company[s["competitor"]] = s

    # ── Competitor sections ────────────────────────────────────
    CATEGORY_ORDER = {"Credit Card Product": 0, "Loyalty / Program": 1, "Company News": 2}
    trend_icons    = ["📈", "🔄", "💳", "✈️", "⚡"]

    competitor_html = ""
    for company in companies:
        themes = sorted(
            [t for t in theme_summaries if t["company"] == company],
            key=lambda t: (CATEGORY_ORDER.get(t.get("category",""), 3), -t.get("article_count", 0))
        )
        summary = competitor_summaries.get(company, "")
        rd      = reddit_by_company.get(company, {})

        # Theme rows
        theme_rows = ""
        for t in themes:
            cat_color = {
                "Credit Card Product": "#00d4aa",
                "Loyalty / Program":   "#7c6fcd",
                "Company News":        "#e8634a",
            }.get(t.get("category",""), "#888")
            url    = t.get("best_url", "#")
            source = t.get("best_source", "")
            count  = t.get("article_count", 0)
            dr     = t.get("date_range", "")
            s      = t.get("summary","") or t.get("best_headline","") or t.get("theme","")
            src_link = (f'<a href="{url}" target="_blank" class="source-link">{source}</a>'
                        if url and url != "#" else source)
            theme_rows += f"""
            <div class="theme-row">
                <span class="cat-badge" style="background:{cat_color}20;color:{cat_color};border-color:{cat_color}40">{t.get("category","")}</span>
                <p class="theme-text">{s}</p>
                <div class="theme-meta">{count} articles · {dr}{" · 🔗 " + src_link if source else ""}</div>
            </div>"""

        # Reddit mini-section
        reddit_html = ""
        if rd and rd.get("total_posts", 0) > 0:
            sent   = rd.get("sentiment", "neutral")
            s_icon = {"positive": "🟢", "negative": "🔴", "neutral": "⚪"}.get(sent, "⚪")
            s_color= {"positive": "#00d4aa", "negative": "#e8634a", "neutral": "#6b6b80"}.get(sent, "#6b6b80")
            top_posts_html = ""
            for tp in rd.get("top_posts", [])[:3]:
                p_sent  = tp.get("sentiment", "neutral")
                p_icon  = {"positive": "🟢", "negative": "🔴", "neutral": "⚪"}.get(p_sent, "⚪")
                top_posts_html += f"""
                <div class="reddit-post">
                    <span class="reddit-sent">{p_icon}</span>
                    <div>
                        <a href="{tp.get('url','#')}" target="_blank" class="reddit-title">{tp.get('title','')[:90]}{'...' if len(tp.get('title','')) > 90 else ''}</a>
                        <div class="reddit-meta">r/{tp.get('subreddit','')} · ▲{tp.get('score',0)} · 💬{tp.get('num_comments',0)}</div>
                    </div>
                </div>"""

            reddit_html = f"""
            <div class="reddit-section">
                <div class="reddit-header">
                    <span class="reddit-label">📱 Reddit Sentiment</span>
                    <span class="sentiment-badge" style="color:{s_color};border-color:{s_color}40;background:{s_color}10">
                        {s_icon} {sent.title()} · {rd['total_posts']} posts
                    </span>
                    <span class="sentiment-counts">
                        🟢 {rd['positive']} &nbsp; 🔴 {rd['negative']} &nbsp; ⚪ {rd['neutral']}
                    </span>
                </div>
                {top_posts_html}
            </div>"""

        competitor_html += f"""
        <div class="competitor-card" id="comp-{company.lower().replace(' ','-').replace('/','')}">
            <div class="comp-header">
                <span class="comp-initial">{company[0]}</span>
                <div>
                    <h3 class="comp-name">{company}</h3>
                    <span class="comp-count">{len(themes)} themes</span>
                </div>
            </div>
            <p class="comp-summary">{summary}</p>
            <div class="themes-list">{theme_rows}</div>
            {reddit_html}
        </div>"""

    # ── Trends ─────────────────────────────────────────────────
    def trend_card(i, trend):
        parts = trend.split(":", 1)
        title = parts[0].strip() if len(parts) > 1 else f"Trend {i+1}"
        body  = parts[1].strip() if len(parts) > 1 else trend
        icon  = trend_icons[i % len(trend_icons)]
        return f"""<div class="trend-card">
            <div class="trend-number">{icon}</div>
            <h4 class="trend-title">{title}</h4>
            <p class="trend-body">{body}</p>
        </div>"""

    trends_row1 = "".join(trend_card(i, market_trends[i]) for i in range(min(3, len(market_trends))))
    trends_row2 = "".join(trend_card(i, market_trends[i]) for i in range(3, min(5, len(market_trends)))) if len(market_trends) > 3 else ""

    # ── Reddit overall sentiment section ──────────────────────
    reddit_overview_html = ""
    if reddit.get("competitor_sentiment"):
        rows = ""
        for s in sorted(reddit["competitor_sentiment"], key=lambda x: x["total_posts"], reverse=True):
            if s["total_posts"] == 0:
                continue
            sent   = s["sentiment"]
            s_icon = {"positive": "🟢", "negative": "🔴", "neutral": "⚪"}.get(sent, "⚪")
            s_color= {"positive": "#00d4aa", "negative": "#e8634a", "neutral": "#6b6b80"}.get(sent, "#6b6b80")
            pct_pos = round(s["positive"] / max(s["total_posts"], 1) * 100)
            rows += f"""
            <div class="sentiment-row">
                <span class="sentiment-company">{s['competitor']}</span>
                <div class="sentiment-bar-wrap">
                    <div class="sentiment-bar" style="width:{pct_pos}%;background:{s_color}"></div>
                </div>
                <span class="sentiment-score" style="color:{s_color}">{s_icon} {sent.title()}</span>
                <span class="sentiment-count">{s['total_posts']} posts</span>
            </div>"""

        reddit_overview_html = f"""
        <div class="section-label">📱 Reddit Sentiment Overview</div>
        <div class="reddit-overview-card">
            <div class="reddit-overview-header">
                <span>Competitor</span><span>Positive %</span><span>Sentiment</span><span>Posts</span>
            </div>
            {rows}
        </div>"""

    # ── Chart data ─────────────────────────────────────────────
    chart_data   = {c: sum(t.get("article_count",0) for t in theme_summaries if t["company"]==c) for c in companies}
    chart_labels = json.dumps(list(chart_data.keys()))
    chart_values = json.dumps(list(chart_data.values()))

    # ── Nav ────────────────────────────────────────────────────
    nav_links = "".join(
        f'<a href="#comp-{c.lower().replace(" ","-").replace("/","")}" class="nav-link">{c}</a>'
        for c in companies
    )

    generated_at = datetime.now().strftime("%B %d, %Y")
    total_articles = sum(t.get("article_count",0) for t in theme_summaries)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Competitive Intelligence — {year_month}</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');
:root {{
  --bg:#0a0a0f; --surface:#13131a; --surface2:#1a1a25; --border:#2a2a3a;
  --accent:#00d4aa; --accent2:#7c6fcd; --danger:#e8634a;
  --text:#e8e8f0; --muted:#6b6b80;
  --font:'DM Sans',sans-serif; --mono:'DM Mono',monospace;
}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--bg);color:var(--text);font-family:var(--font);font-size:14px;line-height:1.6}}
.nav{{position:sticky;top:0;z-index:100;background:rgba(10,10,15,0.92);backdrop-filter:blur(12px);border-bottom:1px solid var(--border);padding:0 2rem;display:flex;align-items:center;gap:2rem;height:56px}}
.nav-brand{{font-weight:700;font-size:13px;letter-spacing:.08em;text-transform:uppercase;color:var(--accent);white-space:nowrap}}
.nav-links{{display:flex;gap:.25rem;overflow-x:auto;scrollbar-width:none;flex:1}}
.nav-link{{color:var(--muted);text-decoration:none;font-size:12px;padding:.3rem .7rem;border-radius:4px;white-space:nowrap;transition:all .15s}}
.nav-link:hover{{color:var(--text);background:var(--surface2)}}
.nav-date{{font-size:11px;color:var(--muted);font-family:var(--mono);white-space:nowrap}}
.page{{max-width:1100px;margin:0 auto;padding:2.5rem 2rem 4rem}}
.page-title{{font-size:28px;font-weight:700;letter-spacing:-.02em}}
.page-title span{{color:var(--accent)}}
.page-sub{{color:var(--muted);font-size:13px;margin-top:.4rem;margin-bottom:2rem}}
.section-label{{font-size:10px;font-weight:700;letter-spacing:.15em;text-transform:uppercase;color:var(--muted);margin:2rem 0 1rem;display:flex;align-items:center;gap:.5rem}}
.section-label::after{{content:'';flex:1;height:1px;background:var(--border)}}
.exec-card{{background:var(--surface);border:1px solid var(--border);border-left:3px solid var(--accent);border-radius:10px;padding:1.5rem 2rem;margin-bottom:2rem;font-size:15px;line-height:1.75;color:#c8c8d8}}
.kpi-row{{display:grid;grid-template-columns:repeat(4,1fr);gap:1rem;margin-bottom:2rem}}
.kpi-card{{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:1.2rem 1.5rem;transition:border-color .2s}}
.kpi-card:hover{{border-color:var(--accent)}}
.kpi-value{{font-size:28px;font-weight:700;color:var(--accent);font-family:var(--mono)}}
.kpi-label{{font-size:11px;color:var(--muted);margin-top:.3rem;text-transform:uppercase;letter-spacing:.08em}}
.trends-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;margin-bottom:1rem}}
.trends-row2{{display:grid;grid-template-columns:repeat(2,1fr);gap:1rem;margin-bottom:2rem}}
.trend-card{{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:1.2rem 1.4rem;transition:transform .2s,border-color .2s}}
.trend-card:hover{{transform:translateY(-2px);border-color:var(--accent2)}}
.trend-number{{font-size:20px;margin-bottom:.5rem}}
.trend-title{{font-size:13px;font-weight:600;color:var(--text);margin-bottom:.5rem}}
.trend-body{{font-size:12px;color:var(--muted);line-height:1.6}}
.chart-card{{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:1.5rem;margin-bottom:2rem}}
.chart-wrap{{height:220px}}
/* Reddit overview */
.reddit-overview-card{{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:1.2rem 1.5rem;margin-bottom:2rem}}
.reddit-overview-header{{display:grid;grid-template-columns:160px 1fr 100px 70px;gap:1rem;font-size:10px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);padding-bottom:.75rem;border-bottom:1px solid var(--border);margin-bottom:.75rem}}
.sentiment-row{{display:grid;grid-template-columns:160px 1fr 100px 70px;gap:1rem;align-items:center;padding:.5rem 0;border-bottom:1px solid rgba(255,255,255,0.03)}}
.sentiment-company{{font-size:13px;font-weight:500}}
.sentiment-bar-wrap{{height:6px;background:var(--border);border-radius:3px;overflow:hidden}}
.sentiment-bar{{height:100%;border-radius:3px;transition:width .6s ease}}
.sentiment-score{{font-size:12px;font-weight:600}}
.sentiment-count{{font-size:11px;color:var(--muted);text-align:right}}
/* Competitor cards */
.competitors-grid{{display:flex;flex-direction:column;gap:1.5rem}}
.competitor-card{{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:1.5rem 2rem}}
.comp-header{{display:flex;align-items:center;gap:1rem;margin-bottom:1rem}}
.comp-initial{{width:40px;height:40px;border-radius:10px;background:linear-gradient(135deg,var(--accent2),var(--accent));display:flex;align-items:center;justify-content:center;font-weight:700;font-size:16px;flex-shrink:0}}
.comp-name{{font-size:16px;font-weight:600}}
.comp-count{{font-size:11px;color:var(--muted)}}
.comp-summary{{font-size:13px;color:#b0b0c0;line-height:1.7;padding:1rem 1.2rem;background:var(--surface2);border-radius:8px;margin-bottom:1.2rem;border-left:2px solid var(--accent2)}}
.themes-list{{display:flex;flex-direction:column;gap:.5rem;margin-bottom:1rem}}
.theme-row{{padding:.8rem 1rem;background:var(--bg);border-radius:8px;border:1px solid var(--border)}}
.cat-badge{{display:inline-block;font-size:10px;font-weight:600;letter-spacing:.05em;padding:2px 8px;border-radius:20px;border:1px solid;margin-bottom:.4rem}}
.theme-text{{font-size:13px;color:var(--text);margin-bottom:.3rem}}
.theme-meta{{font-size:11px;color:var(--muted)}}
.source-link{{color:var(--accent);text-decoration:none}}
.source-link:hover{{text-decoration:underline}}
/* Reddit per-competitor */
.reddit-section{{background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:1rem;margin-top:.5rem}}
.reddit-header{{display:flex;align-items:center;gap:.75rem;margin-bottom:.75rem;flex-wrap:wrap}}
.reddit-label{{font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}}
.sentiment-badge{{font-size:11px;font-weight:600;padding:3px 10px;border-radius:20px;border:1px solid}}
.sentiment-counts{{font-size:11px;color:var(--muted)}}
.reddit-post{{display:flex;gap:.75rem;align-items:flex-start;padding:.6rem 0;border-bottom:1px solid rgba(255,255,255,0.04)}}
.reddit-post:last-child{{border-bottom:none}}
.reddit-sent{{font-size:14px;flex-shrink:0;margin-top:2px}}
.reddit-title{{font-size:12px;color:var(--text);text-decoration:none;display:block;margin-bottom:.2rem;line-height:1.4}}
.reddit-title:hover{{color:var(--accent)}}
.reddit-meta{{font-size:11px;color:var(--muted)}}
.footer{{margin-top:4rem;padding-top:2rem;border-top:1px solid var(--border);text-align:center;font-size:11px;color:var(--muted)}}
.footer a{{color:var(--accent);text-decoration:none}}
@media(max-width:768px){{
  .kpi-row{{grid-template-columns:repeat(2,1fr)}}
  .trends-grid{{grid-template-columns:1fr}}
  .trends-row2{{grid-template-columns:1fr}}
  .reddit-overview-header,.sentiment-row{{grid-template-columns:120px 1fr 80px 50px}}
  .page{{padding:1.5rem 1rem}}
}}
</style>
</head>
<body>

<nav class="nav">
  <span class="nav-brand">🛡 Competitive Intel</span>
  <div class="nav-links">{nav_links}</div>
  <span class="nav-date">{year_month}</span>
</nav>

<main class="page">
  <h1 class="page-title">Competitive Intelligence Brief <span>/ {year_month}</span></h1>
  <p class="page-sub">Travel credit card market monitor · Generated {generated_at} · Claude AI + DBSCAN + Reddit Sentiment</p>

  <div class="kpi-row">
    <div class="kpi-card"><div class="kpi-value">{len(companies)}</div><div class="kpi-label">Competitors</div></div>
    <div class="kpi-card"><div class="kpi-value">{len(theme_summaries)}</div><div class="kpi-label">News Themes</div></div>
    <div class="kpi-card"><div class="kpi-value">{total_articles}</div><div class="kpi-label">Articles Processed</div></div>
    <div class="kpi-card"><div class="kpi-value">{reddit.get('total_posts',0)}</div><div class="kpi-label">Reddit Posts</div></div>
  </div>

  <div class="section-label">Executive Summary</div>
  <div class="exec-card">{exec_summary}</div>

  <div class="section-label">Top Market Trends</div>
  <div class="trends-grid">{trends_row1}</div>
  {"<div class='trends-row2'>" + trends_row2 + "</div>" if trends_row2 else ""}

  <div class="section-label">Activity by Competitor</div>
  <div class="chart-card">
    <div class="chart-wrap"><canvas id="activityChart"></canvas></div>
  </div>

  {reddit_overview_html}

  <div class="section-label">Competitor Analysis</div>
  <div class="competitors-grid">{competitor_html}</div>

  <footer class="footer">
    <p>Built by Ridi Tasmiah ·
    <a href="https://github.com/tasmiahr/ai-competitive-intelligence" target="_blank">GitHub</a> ·
    Python · Claude AI · DBSCAN · Reddit · GitHub Actions</p>
  </footer>
</main>

<script>
new Chart(document.getElementById('activityChart').getContext('2d'), {{
  type:'bar',
  data:{{
    labels:{chart_labels},
    datasets:[{{
      label:'Total Articles',
      data:{chart_values},
      backgroundColor:'rgba(0,212,170,0.15)',
      borderColor:'rgba(0,212,170,0.8)',
      borderWidth:1.5,borderRadius:6
    }}]
  }},
  options:{{
    responsive:true,maintainAspectRatio:false,
    plugins:{{legend:{{display:false}}}},
    scales:{{
      x:{{grid:{{color:'rgba(255,255,255,0.04)'}},ticks:{{color:'#6b6b80',font:{{size:11}}}}}},
      y:{{grid:{{color:'rgba(255,255,255,0.04)'}},ticks:{{color:'#6b6b80',font:{{size:11}}}}}}
    }}
  }}
}});
</script>
</body>
</html>"""

    os.makedirs(DOCS_DIR, exist_ok=True)
    out = os.path.join(DOCS_DIR, "dashboard.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ Dashboard → {out}")
    print(f"   Brief: {len(companies)} competitors | {len(theme_summaries)} themes | {len(market_trends)} trends")
    print(f"   Reddit: {reddit.get('total_posts',0)} posts across {len(reddit.get('competitor_sentiment',[]))} competitors")
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="data")
    args = parser.parse_args()
    generate_html(args.data_dir)


if __name__ == "__main__":
    main()
