"""
generate_html.py
================
Reads monthly_market_trends_*.json + reddit_sentiment_*.json
Generates docs/dashboard.html matching the portfolio design.

Run: python core/generate_html.py
     python core/generate_html.py --data-dir data
"""

import glob, json, os, argparse
from datetime import datetime

DOCS_DIR = "docs"

def find_latest(pattern):
    files = sorted(glob.glob(pattern), reverse=True)
    return files[0] if files else None

def load_json(path):
    if not path: return {}
    try:
        with open(path) as f: return json.load(f)
    except: return {}

def generate_html(data_dir="data"):
    brief  = load_json(find_latest(os.path.join(data_dir, "monthly_market_trends_*.json")))
    reddit = load_json(find_latest(os.path.join("social", "data", "reddit_sentiment_*.json")))
    if not reddit:
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
    reddit_by_company    = {s["competitor"]: s for s in reddit.get("competitor_sentiment", [])}

    CATEGORY_ORDER = {"Product Launch": 0, "Ecosystem": 1, "Company News": 2}
    CAT_STYLES = {
        "Product Launch": ("#7da4ff", "rgba(26,86,255,.15)", "rgba(26,86,255,.3)"),
        "Ecosystem":      ("#5ee8c8", "rgba(0,184,148,.12)", "rgba(0,184,148,.25)"),
        "Company News":   ("#f5c842", "rgba(245,166,35,.12)", "rgba(245,166,35,.25)"),
    }
    trend_colors = ["t-blue", "t-white", "t-green", "t-grey", "t-black"]
    trend_icons  = ["💻", "📉", "🔓", "🏢", "🛡"]

    # ── Exec summary bullets ──────────────────────────────────
    exec_bullets = ""
    for company in companies:
        summary = competitor_summaries.get(company, "")
        if summary:
            # Take first sentence only for bullet
            first = summary.split(".")[0].strip() + "."
            exec_bullets += f'<div class="exec-bullet"><span><strong>{company}</strong> {first}</span></div>\n'

    # ── Activity chart data ───────────────────────────────────
    chart_labels = json.dumps(companies)
    chart_values = json.dumps([
        sum(t.get("article_count", 0) for t in theme_summaries if t["company"] == c)
        for c in companies
    ])

    # ── Sentiment rows ────────────────────────────────────────
    sent_rows = ""
    for s in sorted(reddit.get("competitor_sentiment", []), key=lambda x: x.get("total_posts", 0), reverse=True):
        if not s.get("total_posts"): continue
        sent  = s["sentiment"]
        s_col = {"positive": "var(--blue)", "negative": "var(--red)", "neutral": "var(--gold)"}.get(sent, "var(--muted)")
        s_icon= {"positive": "🟢", "negative": "🔴", "neutral": "⚪"}.get(sent, "⚪")
        pct   = round(s["positive"] / max(s["total_posts"], 1) * 100)
        sent_rows += f"""<div class="sent-row">
          <span class="sent-name">{s['competitor']}</span>
          <div class="sent-bar-bg"><div class="sent-bar" style="width:{pct}%;background:{s_col}"></div></div>
          <span class="sent-label" style="color:{s_col}">{s_icon} {sent.title()}</span>
        </div>"""

    # ── Trends ────────────────────────────────────────────────
    def trend_card(i, trend, col):
        parts = trend.split(":", 1)
        title = parts[0].strip().upper() if len(parts) > 1 else f"TREND {i+1}"
        body  = parts[1].strip() if len(parts) > 1 else trend
        icon  = trend_icons[i % len(trend_icons)]
        return f"""<div class="trend-card {col}">
          <div class="trend-num">0{i+1}</div>
          <div class="trend-icon">{icon}</div>
          <div class="trend-title">{title}</div>
          <div class="trend-body">{body}</div>
        </div>"""

    trends_row1 = "".join(trend_card(i, market_trends[i], trend_colors[i % len(trend_colors)])
                          for i in range(min(3, len(market_trends))))
    trends_row2 = "".join(trend_card(i, market_trends[i], trend_colors[i % len(trend_colors)])
                          for i in range(3, min(5, len(market_trends)))) if len(market_trends) > 3 else ""
    trends_row2_html = f'<div class="trends-row2">{trends_row2}</div>' if trends_row2 else ""

    # ── Competitor cards ──────────────────────────────────────
    comp_html = ""
    avatar_grads = [
        "linear-gradient(135deg,#1a56ff,#00b894)",
        "linear-gradient(135deg,#00b894,#1a56ff)",
        "linear-gradient(135deg,#1a56ff,#0f36cc)",
        "linear-gradient(135deg,#f5a623,#e8634a)",
        "linear-gradient(135deg,#00b894,#0f36cc)",
    ]
    nav_chips = "".join(
        f'<a href="#c{i}" class="nav-chip">{c}</a>'
        for i, c in enumerate(companies)
    )

    for idx, company in enumerate(companies):
        themes = sorted(
            [t for t in theme_summaries if t["company"] == company],
            key=lambda t: (CATEGORY_ORDER.get(t.get("category", ""), 3), -t.get("article_count", 0))
        )[:8]  # cap at 8 themes per competitor
        summary  = competitor_summaries.get(company, "")
        rd       = reddit_by_company.get(company, {})
        grad     = avatar_grads[idx % len(avatar_grads)]
        total_articles = sum(t.get("article_count", 0) for t in themes)

        # Theme rows
        theme_rows = ""
        for t in themes:
            cat = t.get("category", "")
            col, bg, bdr = CAT_STYLES.get(cat, ("#aaa", "rgba(255,255,255,.08)", "rgba(255,255,255,.15)"))
            url    = t.get("best_url", "#")
            source = t.get("best_source", "")
            count  = t.get("article_count", 0)
            dr     = t.get("date_range", "")
            s      = t.get("summary", "") or t.get("best_headline", "") or t.get("theme", "")
            src_html = f'<a href="{url}" target="_blank" class="src-link">{source} ↗</a>' if url and url != "#" else source
            theme_rows += f"""<div class="theme-item">
              <span class="cat-tag" style="color:{col};background:{bg};border-color:{bdr}">{cat}</span>
              <p class="theme-body">{s}</p>
              <div class="theme-foot">{count} articles · {dr}{" · " + src_html if source else ""}</div>
            </div>"""

        # Reddit/social block
        reddit_html = ""
        if rd and rd.get("total_posts", 0) > 0:
            sent   = rd.get("sentiment", "neutral")
            s_col  = {"positive": "var(--blue)", "negative": "var(--red)", "neutral": "var(--gold)"}.get(sent, "var(--muted)")
            s_icon = {"positive": "🟢", "negative": "🔴", "neutral": "⚪"}.get(sent, "⚪")
            posts  = ""
            for p in rd.get("top_posts", [])[:3]:
                pi = {"positive": "🟢", "negative": "🔴", "neutral": "⚪"}.get(p.get("sentiment", "neutral"), "⚪")
                posts += f"""<a href="{p.get('url','#')}" target="_blank" class="rpost">
                  <span class="rpost-icon">{pi}</span>
                  <span class="rpost-title">{p.get('title','')[:88]}{'…' if len(p.get('title',''))>88 else ''}</span>
                  <span class="rpost-score">▲{p.get('score',0)}</span>
                </a>"""
            reddit_html = f"""<div class="comp-reddit-wrap">
              <div class="reddit-head">
                <span class="reddit-label">Social</span>
                <span class="reddit-badge" style="color:{s_col}">{s_icon} {sent.title()} · {rd['total_posts']} posts</span>
              </div>
              {posts}
            </div>"""

        comp_html += f"""<div class="comp-card" id="c{idx}">
          <div class="comp-header">
            <div class="comp-avatar" style="background:{grad}">{company[0]}</div>
            <div>
              <div class="comp-name">{company.upper()}</div>
              <div class="comp-meta">{len(themes)} themes · {total_articles} articles</div>
            </div>
          </div>
          <div class="comp-summary-wrap">
            <p class="comp-summary">{summary}</p>
          </div>
          <div class="comp-themes-wrap">
            <div class="themes-label">Themes</div>
            {theme_rows}
          </div>
          {reddit_html}
        </div>"""

    generated_at = datetime.now().strftime("%B %d, %Y")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Competitive Intelligence — {year_month}</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{{
  --blue:#1a56ff;--blue-dark:#0f36cc;
  --black:#0a0a0a;--white:#fff;
  --bg:#f2f2f2;--surf:#fff;--border:#e0e0e0;
  --ink:#111;--ink2:#3d3d4e;--muted:#666;--muted2:#aaa;
  --teal:#00b894;--green:#00b894;--gold:#f5a623;--red:#e53935;
  --display:'Bebas Neue',sans-serif;
  --body:'DM Sans',sans-serif;--mono:'JetBrains Mono',monospace;
}}
*{{box-sizing:border-box;margin:0;padding:0}}
html{{scroll-behavior:smooth}}
body{{background:var(--bg);color:var(--ink);font-family:var(--body);font-size:14px;line-height:1.6;-webkit-font-smoothing:antialiased}}
.topnav{{position:sticky;top:0;z-index:100;height:56px;display:flex;align-items:center;gap:1.5rem;padding:0 2rem;background:var(--black);border-bottom:1px solid rgba(255,255,255,.07)}}
.topnav-brand{{font-family:var(--display);font-size:18px;letter-spacing:.06em;color:var(--white)}}
.nav-chips{{display:flex;gap:.2rem;overflow-x:auto;scrollbar-width:none;flex:1}}
.nav-chip{{font-family:var(--mono);font-size:11px;color:rgba(255,255,255,.4);text-decoration:none;padding:.25rem .65rem;border-radius:20px;white-space:nowrap;transition:all .15s}}
.nav-chip:hover{{color:var(--white);background:rgba(255,255,255,.08)}}
.topnav-right{{display:flex;gap:.75rem;align-items:center;flex-shrink:0}}
.topnav-date{{font-family:var(--mono);font-size:11px;color:rgba(255,255,255,.3)}}
.topnav-back{{font-size:12px;font-weight:600;color:var(--white);background:var(--blue);text-decoration:none;padding:.35rem .9rem;border-radius:4px;white-space:nowrap}}
.topnav-back:hover{{background:var(--blue-dark)}}
.hero{{background:var(--blue);padding:3rem 2rem 2.5rem;position:relative;overflow:hidden}}
.hero::before{{content:'';position:absolute;top:-40%;right:-10%;width:500px;height:500px;border-radius:50%;background:radial-gradient(circle,rgba(255,255,255,.1) 0%,transparent 65%);pointer-events:none}}
.hero-inner{{max-width:1080px;margin:0 auto;position:relative;z-index:1}}
.hero-title{{font-family:var(--display);font-size:clamp(32px,5vw,52px);letter-spacing:.03em;line-height:1;color:var(--white)}}
.hero-title em{{font-style:normal;color:rgba(255,255,255,.6)}}
.hero-meta{{font-family:var(--mono);font-size:11px;color:rgba(255,255,255,.5);margin-top:.4rem}}
.hero-competitors{{display:flex;gap:.5rem;flex-wrap:wrap;margin-top:.75rem}}
.hero-comp{{font-family:var(--mono);font-size:11px;font-weight:500;color:rgba(255,255,255,.9);background:rgba(255,255,255,.15);border:1px solid rgba(255,255,255,.25);padding:.25rem .75rem;border-radius:20px}}
.page{{max-width:1080px;margin:0 auto;padding:2rem 2rem 5rem}}
.dash-section{{margin-bottom:2.5rem}}
.section-head{{display:flex;align-items:baseline;gap:.75rem;margin-bottom:1rem}}
.section-label{{font-family:var(--display);font-size:13px;letter-spacing:.1em;color:var(--muted)}}
.section-count{{font-family:var(--mono);font-size:11px;color:var(--muted2)}}
.two-col{{display:grid;grid-template-columns:1fr 1fr;gap:1.5rem;margin-bottom:2.5rem}}
.exec-card{{background:var(--green);border-radius:10px;padding:1.8rem 2rem;position:relative;overflow:hidden}}
.exec-label{{font-family:var(--mono);font-size:10px;color:rgba(255,255,255,.6);text-transform:uppercase;letter-spacing:.08em;margin-bottom:.75rem}}
.exec-text{{font-size:14px;color:rgba(255,255,255,.95);line-height:1.8;font-weight:300}}
.exec-bullets{{margin-top:.75rem;display:flex;flex-direction:column;gap:.4rem}}
.exec-bullet{{display:flex;align-items:flex-start;gap:.6rem;font-size:13px;color:rgba(255,255,255,.9);line-height:1.6;font-weight:300}}
.exec-bullet::before{{content:'';width:6px;height:6px;border-radius:50%;background:rgba(255,255,255,.7);flex-shrink:0;margin-top:.5rem}}
.chart-card{{background:var(--surf);border:1px solid var(--border);border-radius:10px;padding:1.4rem}}
.chart-label{{font-family:var(--display);font-size:12px;letter-spacing:.08em;color:var(--muted);margin-bottom:1rem}}
.chart-wrap{{height:180px}}
.sent-table{{display:flex;flex-direction:column;gap:.3rem;margin-top:.5rem}}
.sent-row{{display:flex;align-items:center;gap:.75rem;padding:.5rem .7rem;background:var(--bg);border-radius:6px}}
.sent-name{{font-size:12px;font-weight:600;width:90px;flex-shrink:0}}
.sent-bar-bg{{flex:1;height:5px;background:#e0e0e0;border-radius:3px;overflow:hidden}}
.sent-bar{{height:100%;border-radius:3px}}
.sent-label{{font-family:var(--mono);font-size:10px;font-weight:600;width:80px;text-align:right}}
.trends-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem}}
.trends-row2{{display:grid;grid-template-columns:repeat(2,1fr);gap:1rem;margin-top:1rem}}
.trend-card{{border-radius:10px;padding:1.4rem;position:relative;border:1px solid transparent;transition:transform .2s,box-shadow .2s}}
.trend-card:hover{{transform:translateY(-3px);box-shadow:0 8px 24px rgba(0,0,0,.1)}}
.t-blue{{background:var(--blue);border-color:var(--blue)}}
.t-white{{background:var(--white);border-color:var(--border)}}
.t-green{{background:var(--green);border-color:var(--green)}}
.t-grey{{background:#e8e8e8;border-color:#d4d4d4}}
.t-black{{background:var(--black);border-color:var(--black)}}
.trend-num{{font-family:var(--mono);font-size:10px;margin-bottom:.5rem;letter-spacing:.06em}}
.t-blue .trend-num,.t-green .trend-num,.t-black .trend-num{{color:rgba(255,255,255,.4)}}
.t-white .trend-num,.t-grey .trend-num{{color:var(--muted)}}
.trend-icon{{font-size:22px;margin-bottom:.5rem;line-height:1}}
.trend-title{{font-family:var(--display);font-size:17px;letter-spacing:.02em;margin-bottom:.4rem;line-height:1.1}}
.t-blue .trend-title,.t-green .trend-title,.t-black .trend-title{{color:var(--white)}}
.t-white .trend-title,.t-grey .trend-title{{color:var(--black)}}
.trend-body{{font-size:12px;line-height:1.6;font-weight:300}}
.t-blue .trend-body,.t-green .trend-body,.t-black .trend-body{{color:rgba(255,255,255,.7)}}
.t-white .trend-body,.t-grey .trend-body{{color:var(--muted)}}
.comp-grid{{display:flex;flex-direction:column;gap:1.25rem}}
.comp-card{{background:var(--surf);border:1px solid var(--border);border-radius:12px;overflow:hidden;transition:box-shadow .2s}}
.comp-card:hover{{box-shadow:0 4px 20px rgba(0,0,0,.07)}}
.comp-header{{display:flex;align-items:center;gap:.85rem;padding:1.4rem 1.6rem;border-bottom:1px solid var(--border)}}
.comp-avatar{{width:40px;height:40px;border-radius:10px;flex-shrink:0;display:flex;align-items:center;justify-content:center;font-family:var(--display);font-size:18px;letter-spacing:.02em;color:white}}
.comp-name{{font-family:var(--display);font-size:20px;letter-spacing:.03em}}
.comp-meta{{font-family:var(--mono);font-size:11px;color:var(--muted)}}
.comp-summary-wrap{{background:var(--blue);padding:1.1rem 1.6rem}}
.comp-summary{{font-size:13px;color:rgba(255,255,255,.9);line-height:1.75;font-weight:300}}
.comp-themes-wrap{{background:var(--green);padding:1rem 1.6rem}}
.themes-label{{font-family:var(--mono);font-size:10px;color:rgba(255,255,255,.55);text-transform:uppercase;letter-spacing:.08em;margin-bottom:.65rem}}
.theme-item{{padding:.65rem .85rem;background:rgba(255,255,255,.12);border-radius:6px;border:1px solid rgba(255,255,255,.15);margin-bottom:.4rem;transition:border-color .15s}}
.theme-item:last-child{{margin-bottom:0}}
.theme-item:hover{{border-color:rgba(255,255,255,.4)}}
.cat-tag{{display:inline-block;font-family:var(--mono);font-size:10px;font-weight:600;padding:2px 7px;border-radius:3px;border:1px solid;margin-bottom:.3rem;letter-spacing:.03em}}
.theme-body{{font-size:12px;color:rgba(255,255,255,.85);margin-bottom:.2rem;line-height:1.5}}
.theme-foot{{font-size:11px;color:rgba(255,255,255,.45)}}
.src-link{{color:rgba(255,255,255,.7);text-decoration:none}}
.src-link:hover{{text-decoration:underline}}
.comp-reddit-wrap{{background:var(--white);padding:1rem 1.6rem;border-top:1px solid var(--border)}}
.reddit-head{{display:flex;align-items:center;gap:.75rem;margin-bottom:.65rem;flex-wrap:wrap}}
.reddit-label{{font-family:var(--mono);font-size:10px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}}
.reddit-badge{{font-size:12px;font-weight:600;font-family:var(--mono)}}
.rpost{{display:flex;align-items:baseline;gap:.5rem;padding:.4rem 0;border-bottom:1px solid var(--border);text-decoration:none;color:var(--ink2);transition:color .15s}}
.rpost:last-child{{border-bottom:none}}
.rpost:hover .rpost-title{{color:var(--blue)}}
.rpost-icon{{font-size:11px;flex-shrink:0}}
.rpost-title{{font-size:12px;flex:1;line-height:1.4}}
.rpost-score{{font-family:var(--mono);font-size:10px;color:var(--muted);flex-shrink:0}}
.dash-footer{{margin-top:4rem;padding-top:2rem;border-top:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;font-family:var(--mono);font-size:11px;color:var(--muted2)}}
.dash-footer a{{color:var(--blue);text-decoration:none}}
@media(max-width:768px){{
  .trends-grid,.trends-row2,.two-col{{grid-template-columns:1fr}}
  .page{{padding:1.5rem 1rem}}
  .hero{{padding:2rem 1rem 1.5rem}}
}}
</style>
</head>
<body>

<nav class="topnav">
  <span class="topnav-brand">COMPETITIVE INTEL</span>
  <div class="nav-chips">
    <a href="#exec" class="nav-chip">Executive Summary</a>
    <a href="#trends" class="nav-chip">Market Trends</a>
    <a href="#competitors" class="nav-chip">Competitor Analysis</a>
  </div>
  <div class="topnav-right">
    <span class="topnav-date">{year_month}</span>
    <a href="index.html" class="topnav-back">← Back</a>
  </div>
</nav>

<div class="hero">
  <div class="hero-inner">
    <h1 class="hero-title">COMPETITIVE BRIEF <em>/ {year_month}</em></h1>
    <p class="hero-meta">Generated {generated_at}</p>
    <div class="hero-competitors">
      {"".join(f'<span class="hero-comp">{c}</span>' for c in companies)}
    </div>
  </div>
</div>

<main class="page">

  <section class="dash-section" id="exec" style="margin-top:2rem;scroll-margin-top:58px">
    <div class="section-head"><span class="section-label">EXECUTIVE SUMMARY</span></div>
    <div class="exec-card">
      <div class="exec-label">{year_month}</div>
      <p class="exec-text">{exec_summary}</p>
      <div class="exec-bullets">{exec_bullets}</div>
    </div>
  </section>

  <div class="two-col">
    <div class="chart-card">
      <div class="chart-label">ACTIVITY BY COMPETITOR</div>
      <div class="chart-wrap"><canvas id="activityChart"></canvas></div>
    </div>
    <div class="chart-card">
      <div class="chart-label">SOCIAL SENTIMENT</div>
      <div class="sent-table">{sent_rows if sent_rows else '<p style="font-size:12px;color:var(--muted);padding:.5rem 0">No social data available for this period.</p>'}</div>
    </div>
  </div>

  <section class="dash-section" id="trends" style="scroll-margin-top:58px">
    <div class="section-head">
      <span class="section-label">MARKET TRENDS</span>
      <span class="section-count">{len(market_trends)} identified this month</span>
    </div>
    <div class="trends-grid">{trends_row1}</div>
    {trends_row2_html}
  </section>

  <section class="dash-section" id="competitors" style="scroll-margin-top:58px">
    <div class="section-head">
      <span class="section-label">COMPETITOR ANALYSIS</span>
      <span class="section-count">{len(companies)} competitors</span>
    </div>
    <div class="comp-grid">{comp_html}</div>
  </section>

  <footer class="dash-footer">
    <span>AI Competitive Intelligence System</span>
    <span>Built by <a href="https://www.linkedin.com/in/riditasmiah" target="_blank">Ridi Tasmiah</a> · <a href="https://github.com/tasmiahr/ai-competitive-intelligence" target="_blank">GitHub ↗</a></span>
  </footer>

</main>

<script>
new Chart(document.getElementById('activityChart').getContext('2d'),{{
  type:'bar',
  data:{{
    labels:{chart_labels},
    datasets:[{{
      data:{chart_values},
      backgroundColor:'rgba(26,86,255,.15)',
      borderColor:'rgba(26,86,255,.7)',
      borderWidth:1.5,borderRadius:6,borderSkipped:false,
      hoverBackgroundColor:'rgba(26,86,255,.25)',
    }}]
  }},
  options:{{
    responsive:true,maintainAspectRatio:false,
    plugins:{{
      legend:{{display:false}},
      tooltip:{{
        callbacks:{{label:ctx=>` ${{ctx.parsed.y}} articles`}},
        backgroundColor:'rgba(10,10,20,.9)',padding:10,cornerRadius:6,
        titleFont:{{family:'JetBrains Mono',size:11}},
        bodyFont:{{family:'JetBrains Mono',size:11}},
      }}
    }},
    scales:{{
      x:{{grid:{{display:false}},ticks:{{color:'#aaa',font:{{size:11,family:'JetBrains Mono'}}}}}},
      y:{{grid:{{color:'rgba(0,0,0,.05)'}},ticks:{{color:'#aaa',font:{{size:11,family:'JetBrains Mono'}}}}}}
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
    print(f"   {len(companies)} competitors · {len(theme_summaries)} themes · {len(market_trends)} trends")
    return out

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir",   default="data")
    parser.add_argument("--output-dir", default="data")
    args = parser.parse_args()
    generate_html(args.data_dir)

if __name__ == "__main__":
    main()
