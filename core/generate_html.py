"""
generate_html.py
================
Reads monthly_market_trends_*.json and generates
docs/dashboard.html — a fully self-contained dashboard
with all data baked in. No server needed, opens in any browser.

Run: python generate_html.py
     python generate_html.py --data-dir data
"""

import glob
import json
import os
import argparse
from datetime import datetime
from pathlib import Path

DOCS_DIR = "docs"


def find_latest_brief(data_dir):
    files = sorted(glob.glob(os.path.join(data_dir, "monthly_market_trends_*.json")), reverse=True)
    return files[0] if files else None


def generate_html(data_dir="data"):
    brief_file = find_latest_brief(data_dir)
    if not brief_file:
        print(f"❌ No monthly_market_trends_*.json found in {data_dir}")
        return

    with open(brief_file) as f:
        brief = json.load(f)

    year_month          = brief.get("year_month", "")
    exec_summary        = brief.get("executive_summary", "")
    market_trends       = brief.get("market_trends", [])
    competitor_summaries = brief.get("competitor_summaries", {})
    theme_summaries     = brief.get("theme_summaries", [])

    # Build competitor sections HTML
    CATEGORY_ORDER = {"Credit Card Product": 0, "Loyalty / Program": 1, "Company News": 2}
    competitor_html = ""
    companies = list(competitor_summaries.keys())

    for company in companies:
        themes = sorted(
            [t for t in theme_summaries if t["company"] == company],
            key=lambda t: (CATEGORY_ORDER.get(t.get("category", ""), 3), -t.get("article_count", 0))
        )
        summary = competitor_summaries.get(company, "")
        theme_rows = ""
        for t in themes:
            cat_color = {"Credit Card Product": "#00d4aa", "Loyalty / Program": "#7c6fcd", "Company News": "#e8634a"}.get(t.get("category", ""), "#888")
            url = t.get("best_url", "#")
            source = t.get("best_source", "")
            count = t.get("article_count", 0)
            date_range = t.get("date_range", "")
            s = t.get("summary", "") or t.get("best_headline", "") or t.get("theme", "")
            source_link = f'<a href="{url}" target="_blank" class="source-link">{source}</a>' if url and url != "#" else source
            theme_rows += f"""
            <div class="theme-row">
                <span class="cat-badge" style="background:{cat_color}20;color:{cat_color};border-color:{cat_color}40">{t.get("category","")}</span>
                <p class="theme-text">{s}</p>
                <div class="theme-meta">{count} articles · {date_range}{" · " + source_link if source else ""}</div>
            </div>"""

        competitor_html += f"""
        <div class="competitor-card" id="comp-{company.lower().replace(' ','-')}">
            <div class="comp-header">
                <span class="comp-initial">{company[0]}</span>
                <div>
                    <h3 class="comp-name">{company}</h3>
                    <span class="comp-count">{len(themes)} themes</span>
                </div>
            </div>
            <p class="comp-summary">{summary}</p>
            <div class="themes-list">{theme_rows}</div>
        </div>"""

    # Build trends HTML
    trends_html = ""
    trend_icons = ["📈", "🔄", "💳", "✈️", "⚡"]
    for i, trend in enumerate(market_trends[:5]):
        parts = trend.split(":", 1)
        title = parts[0].strip() if len(parts) > 1 else f"Trend {i+1}"
        body  = parts[1].strip() if len(parts) > 1 else trend
        icon  = trend_icons[i % len(trend_icons)]
        trends_html += f"""
        <div class="trend-card">
            <div class="trend-number">{icon}</div>
            <h4 class="trend-title">{title}</h4>
            <p class="trend-body">{body}</p>
        </div>"""

    # Pre-build trends row 2 HTML to avoid nested f-string issues
    def _tc(i, trend):
        parts = trend.split(":",1)
        title = parts[0].strip() if len(parts)>1 else f"Trend {i+1}"
        body  = parts[1].strip() if len(parts)>1 else trend
        icon  = trend_icons[i % len(trend_icons)]
        return f'<div class="trend-card"><div class="trend-number">{icon}</div><h4 class="trend-title">{title}</h4><p class="trend-body">{body}</p></div>'

    trends_html = "".join(_tc(i, market_trends[i]) for i in range(min(3,len(market_trends))))
    if len(market_trends) > 3:
        inner = "".join(_tc(i, market_trends[i]) for i in range(3,min(5,len(market_trends))))
        trends_row2_html = f'<div class="trends-row2">{inner}</div>'
    else:
        trends_row2_html = ""

    # Build activity chart data
    chart_data = {}
    for t in theme_summaries:
        c = t["company"]
        chart_data[c] = chart_data.get(c, 0) + t.get("article_count", 0)

    chart_labels = json.dumps(list(chart_data.keys()))
    chart_values = json.dumps(list(chart_data.values()))

    # Nav links
    nav_links = "".join(
        f'<a href="#comp-{c.lower().replace(" ","-")}" class="nav-link">{c}</a>'
        for c in companies
    )

    generated_at = datetime.now().strftime("%B %d, %Y")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Competitive Intelligence Brief — {year_month}</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&family=DM+Mono:wght@400;500&display=swap');

  :root {{
    --bg:        #0a0a0f;
    --surface:   #13131a;
    --surface2:  #1a1a25;
    --border:    #2a2a3a;
    --accent:    #00d4aa;
    --accent2:   #7c6fcd;
    --danger:    #e8634a;
    --text:      #e8e8f0;
    --muted:     #6b6b80;
    --font:      'DM Sans', sans-serif;
    --mono:      'DM Mono', monospace;
  }}

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    background: var(--bg);
    color: var(--text);
    font-family: var(--font);
    font-size: 14px;
    line-height: 1.6;
    min-height: 100vh;
  }}

  /* NAV */
  .nav {{
    position: sticky; top: 0; z-index: 100;
    background: rgba(10,10,15,0.92);
    backdrop-filter: blur(12px);
    border-bottom: 1px solid var(--border);
    padding: 0 2rem;
    display: flex; align-items: center; gap: 2rem;
    height: 56px;
  }}
  .nav-brand {{
    font-weight: 700; font-size: 13px; letter-spacing: 0.08em;
    text-transform: uppercase; color: var(--accent);
    white-space: nowrap;
  }}
  .nav-links {{ display: flex; gap: 0.25rem; overflow-x: auto; scrollbar-width: none; flex: 1; }}
  .nav-link {{
    color: var(--muted); text-decoration: none; font-size: 12px;
    padding: 0.3rem 0.7rem; border-radius: 4px; white-space: nowrap;
    transition: all 0.15s;
  }}
  .nav-link:hover {{ color: var(--text); background: var(--surface2); }}
  .nav-date {{ font-size: 11px; color: var(--muted); font-family: var(--mono); white-space: nowrap; }}

  /* LAYOUT */
  .page {{ max-width: 1100px; margin: 0 auto; padding: 2.5rem 2rem 4rem; }}

  /* HEADER */
  .page-header {{ margin-bottom: 2.5rem; }}
  .page-title {{ font-size: 28px; font-weight: 700; letter-spacing: -0.02em; }}
  .page-title span {{ color: var(--accent); }}
  .page-sub {{ color: var(--muted); font-size: 13px; margin-top: 0.4rem; }}

  /* SECTION LABEL */
  .section-label {{
    font-size: 10px; font-weight: 700; letter-spacing: 0.15em;
    text-transform: uppercase; color: var(--muted);
    margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem;
  }}
  .section-label::after {{
    content: ''; flex: 1; height: 1px; background: var(--border);
  }}

  /* EXEC SUMMARY */
  .exec-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent);
    border-radius: 10px;
    padding: 1.5rem 2rem;
    margin-bottom: 2.5rem;
    font-size: 15px; line-height: 1.75; color: #c8c8d8;
  }}

  /* KPI ROW */
  .kpi-row {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 2.5rem; }}
  .kpi-card {{
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 10px; padding: 1.2rem 1.5rem;
    transition: border-color 0.2s;
  }}
  .kpi-card:hover {{ border-color: var(--accent); }}
  .kpi-value {{ font-size: 28px; font-weight: 700; color: var(--accent); font-family: var(--mono); }}
  .kpi-label {{ font-size: 11px; color: var(--muted); margin-top: 0.3rem; text-transform: uppercase; letter-spacing: 0.08em; }}

  /* TRENDS */
  .trends-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-bottom: 2.5rem; }}
  .trends-grid .trend-card:nth-child(4),
  .trends-grid .trend-card:nth-child(5) {{ grid-column: span 1; }}
  .trends-row2 {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem; margin-bottom: 2.5rem; }}
  .trend-card {{
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 10px; padding: 1.2rem 1.4rem;
    transition: transform 0.2s, border-color 0.2s;
  }}
  .trend-card:hover {{ transform: translateY(-2px); border-color: var(--accent2); }}
  .trend-number {{ font-size: 20px; margin-bottom: 0.5rem; }}
  .trend-title {{ font-size: 13px; font-weight: 600; color: var(--text); margin-bottom: 0.5rem; }}
  .trend-body {{ font-size: 12px; color: var(--muted); line-height: 1.6; }}

  /* CHART */
  .chart-card {{
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 10px; padding: 1.5rem;
    margin-bottom: 2.5rem;
  }}
  .chart-wrap {{ height: 220px; }}

  /* COMPETITOR CARDS */
  .competitors-grid {{ display: flex; flex-direction: column; gap: 1.5rem; }}
  .competitor-card {{
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 12px; padding: 1.5rem 2rem;
    transition: border-color 0.2s;
  }}
  .competitor-card:hover {{ border-color: var(--border); }}
  .comp-header {{ display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem; }}
  .comp-initial {{
    width: 40px; height: 40px; border-radius: 10px;
    background: linear-gradient(135deg, var(--accent2), var(--accent));
    display: flex; align-items: center; justify-content: center;
    font-weight: 700; font-size: 16px; flex-shrink: 0;
  }}
  .comp-name {{ font-size: 16px; font-weight: 600; }}
  .comp-count {{ font-size: 11px; color: var(--muted); }}
  .comp-summary {{
    font-size: 13px; color: #b0b0c0; line-height: 1.7;
    padding: 1rem 1.2rem; background: var(--surface2);
    border-radius: 8px; margin-bottom: 1.2rem;
    border-left: 2px solid var(--accent2);
  }}
  .themes-list {{ display: flex; flex-direction: column; gap: 0.5rem; }}
  .theme-row {{
    padding: 0.8rem 1rem; background: var(--bg);
    border-radius: 8px; border: 1px solid var(--border);
    transition: border-color 0.15s;
  }}
  .theme-row:hover {{ border-color: var(--border); }}
  .cat-badge {{
    display: inline-block; font-size: 10px; font-weight: 600;
    letter-spacing: 0.05em; padding: 2px 8px; border-radius: 20px;
    border: 1px solid; margin-bottom: 0.4rem;
  }}
  .theme-text {{ font-size: 13px; color: var(--text); margin-bottom: 0.3rem; }}
  .theme-meta {{ font-size: 11px; color: var(--muted); }}
  .source-link {{ color: var(--accent); text-decoration: none; }}
  .source-link:hover {{ text-decoration: underline; }}

  /* FOOTER */
  .footer {{
    margin-top: 4rem; padding-top: 2rem;
    border-top: 1px solid var(--border);
    text-align: center; font-size: 11px; color: var(--muted);
  }}
  .footer a {{ color: var(--accent); text-decoration: none; }}

  /* RESPONSIVE */
  @media (max-width: 768px) {{
    .kpi-row {{ grid-template-columns: repeat(2, 1fr); }}
    .trends-grid {{ grid-template-columns: 1fr; }}
    .trends-row2 {{ grid-template-columns: 1fr; }}
    .page {{ padding: 1.5rem 1rem; }}
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

  <header class="page-header">
    <h1 class="page-title">Competitive Intelligence Brief <span>/ {year_month}</span></h1>
    <p class="page-sub">Travel credit card market monitor · Generated {generated_at} · Powered by Claude AI + DBSCAN clustering</p>
  </header>

  <!-- KPIs -->
  <div class="kpi-row">
    <div class="kpi-card">
      <div class="kpi-value">{len(companies)}</div>
      <div class="kpi-label">Competitors Tracked</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-value">{len(theme_summaries)}</div>
      <div class="kpi-label">News Themes</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-value">{sum(t.get("article_count",0) for t in theme_summaries)}</div>
      <div class="kpi-label">Articles Processed</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-value">{len(market_trends)}</div>
      <div class="kpi-label">Market Trends</div>
    </div>
  </div>

  <!-- EXEC SUMMARY -->
  <div class="section-label">Executive Summary</div>
  <div class="exec-card">{exec_summary}</div>

  <!-- TRENDS ROW 1 -->
  <div class="section-label">Top Market Trends</div>
  <div class="trends-grid">{trends_html}</div>
  {trends_row2_html}

  <!-- ACTIVITY CHART -->
  <div class="section-label">Activity by Competitor</div>
  <div class="chart-card">
    <div class="chart-wrap">
      <canvas id="activityChart"></canvas>
    </div>
  </div>

  <!-- COMPETITOR SECTIONS -->
  <div class="section-label">Competitor Analysis</div>
  <div class="competitors-grid">{competitor_html}</div>

  <footer class="footer">
    <p>Built by Ridi Tasmiah · AI-Powered Competitive Intelligence Pipeline ·
    <a href="https://github.com/tasmiahr/ai-competitive-intelligence" target="_blank">View on GitHub</a></p>
    <p style="margin-top:0.5rem">Python · Claude AI · DBSCAN · Google News RSS · GitHub Actions</p>
  </footer>

</main>

<script>
const ctx = document.getElementById('activityChart').getContext('2d');
new Chart(ctx, {{
  type: 'bar',
  data: {{
    labels: {chart_labels},
    datasets: [{{
      label: 'Total Articles',
      data: {chart_values},
      backgroundColor: 'rgba(0, 212, 170, 0.15)',
      borderColor: 'rgba(0, 212, 170, 0.8)',
      borderWidth: 1.5,
      borderRadius: 6,
    }}]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    plugins: {{ legend: {{ display: false }} }},
    scales: {{
      x: {{ grid: {{ color: 'rgba(255,255,255,0.04)' }}, ticks: {{ color: '#6b6b80', font: {{ size: 11 }} }} }},
      y: {{ grid: {{ color: 'rgba(255,255,255,0.04)' }}, ticks: {{ color: '#6b6b80', font: {{ size: 11 }} }} }}
    }}
  }}
}});
</script>

</body>
</html>"""

    os.makedirs(DOCS_DIR, exist_ok=True)
    out_path = os.path.join(DOCS_DIR, "dashboard.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ Dashboard → {out_path}")
    print(f"   Competitors: {len(companies)} | Themes: {len(theme_summaries)} | Trends: {len(market_trends)}")
    return out_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="data")
    args = parser.parse_args()
    generate_html(args.data_dir)


if __name__ == "__main__":
    main()
