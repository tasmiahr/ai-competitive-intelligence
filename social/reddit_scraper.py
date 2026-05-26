"""
reddit_scraper.py
=================
Scrapes Reddit for competitor mentions using public JSON endpoints.
No API key required. Uses .json suffix on Reddit search URLs.

Monitors: r/creditcards, r/churning, r/awardtravel, r/personalfinance

Outputs:
  data/reddit_sentiment_YYYY_MM.json  — structured data for dashboard
  data/reddit_sentiment_YYYY_MM.csv   — flat CSV

Run: python reddit_scraper.py
     python reddit_scraper.py --year 2026 --month 5
"""

import argparse
import csv
import json
import os
import re
import time
from datetime import datetime, timezone

import requests

OUTPUT_DIR = "social/data"

SUBREDDITS = [
    "creditcards",
    "churning",
    "awardtravel",
    "personalfinance",
]

# Seconds to wait between requests — be respectful
REQUEST_DELAY = 2

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; competitive-intel-research/1.0)",
    "Accept": "application/json",
}


def get_target_month(year=None, month=None):
    if year and month:
        return int(year), int(month)
    today = datetime.now(timezone.utc)
    if today.month == 1:
        return today.year - 1, 12
    return today.year, today.month - 1


def in_target_month(timestamp, year, month):
    """Check if a Unix timestamp falls in the target month."""
    dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    return dt.year == year and dt.month == month


def search_subreddit(subreddit, query, year, month, limit=25):
    """Search a subreddit for posts mentioning a query in the target month."""
    url = (
        f"https://www.reddit.com/r/{subreddit}/search.json"
        f"?q={requests.utils.quote(query)}&sort=top&t=month&limit={limit}&restrict_sr=1"
    )
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        posts = data.get("data", {}).get("children", [])
        results = []
        for post in posts:
            p = post.get("data", {})
            created = p.get("created_utc", 0)
            if not in_target_month(created, year, month):
                continue
            results.append({
                "subreddit":    subreddit,
                "post_id":      p.get("id", ""),
                "title":        p.get("title", ""),
                "text":         (p.get("selftext", "") or "")[:500],
                "score":        p.get("score", 0),
                "num_comments": p.get("num_comments", 0),
                "url":          f"https://reddit.com{p.get('permalink','')}",
                "created_utc":  created,
                "date":         datetime.fromtimestamp(created, tz=timezone.utc).strftime("%Y-%m-%d"),
            })
        return results
    except Exception as e:
        print(f"    ⚠️  {subreddit} / '{query}': {e}")
        return []


def score_sentiment(text):
    """
    Simple keyword-based sentiment scoring.
    Returns: 'positive', 'negative', or 'neutral'
    """
    text_lower = (text or "").lower()
    positive_words = [
        "great", "love", "best", "excellent", "amazing", "worth it",
        "recommend", "fantastic", "awesome", "good deal", "solid",
        "approved", "bonus posted", "churned", "retention offer",
        "lucrative", "generous", "free night", "strong", "wins",
    ]
    negative_words = [
        "worst", "terrible", "bad", "avoid", "scam", "fraud",
        "disappointed", "cancelled", "denied", "rejected", "poor",
        "horrible", "useless", "devalued", "devaluation", "clawback",
        "shutdown", "closed", "lost", "hate", "never again", "rip",
        "sued", "lawsuit", "breach", "issue", "problem", "broken",
    ]
    pos = sum(1 for w in positive_words if w in text_lower)
    neg = sum(1 for w in negative_words if w in text_lower)
    if pos > neg:
        return "positive"
    if neg > pos:
        return "negative"
    return "neutral"


def analyze_competitor_sentiment(posts, competitor):
    """Aggregate sentiment stats for a competitor from a list of posts."""
    if not posts:
        return {
            "competitor": competitor,
            "total_posts": 0,
            "total_score": 0,
            "total_comments": 0,
            "positive": 0,
            "negative": 0,
            "neutral": 0,
            "sentiment": "neutral",
            "top_posts": [],
        }

    sentiments = []
    for p in posts:
        combined = f"{p['title']} {p['text']}"
        p["sentiment"] = score_sentiment(combined)
        sentiments.append(p["sentiment"])

    pos = sentiments.count("positive")
    neg = sentiments.count("negative")
    neu = sentiments.count("neutral")

    overall = "neutral"
    if pos > neg and pos > neu:
        overall = "positive"
    elif neg > pos and neg > neu:
        overall = "negative"

    top_posts = sorted(posts, key=lambda x: x["score"], reverse=True)[:5]

    return {
        "competitor":     competitor,
        "total_posts":    len(posts),
        "total_score":    sum(p["score"] for p in posts),
        "total_comments": sum(p["num_comments"] for p in posts),
        "positive":       pos,
        "negative":       neg,
        "neutral":        neu,
        "sentiment":      overall,
        "top_posts":      top_posts,
    }


def build_competitor_queries(competitors):
    """
    Build search queries per competitor.
    Maps competitor names to relevant search terms.
    """
    query_map = {
        "Delta":            ["Delta SkyMiles", "Delta credit card", "Delta Amex"],
        "American Airlines": ["AAdvantage credit card", "Citi AAdvantage", "AA miles card"],
        "Southwest":        ["Southwest Rapid Rewards", "Southwest credit card", "Southwest card"],
        "JetBlue":          ["JetBlue TrueBlue", "JetBlue card", "JetBlue Barclays"],
        "Alaska Airlines":  ["Alaska Airlines card", "Alaska Mileage Plan", "Bank of America Alaska"],
        "United":           ["United MileagePlus", "United Explorer card", "Chase United"],
        "Frontier":         ["Frontier Airlines card", "Frontier miles"],
        "Spirit":           ["Spirit Airlines card", "Spirit miles"],
        "Allegiant":        ["Allegiant credit card", "Allegiant miles"],
        "Hawaiian":         ["Hawaiian Airlines card", "HawaiianMiles"],
        "Chase":            ["Chase Sapphire", "Chase Sapphire Reserve", "Chase travel card"],
        "Capital One":      ["Capital One Venture", "Capital One miles", "Venture X"],
        "American Express": ["Amex Platinum", "Membership Rewards", "Amex travel card"],
        "Citi":             ["Citi ThankYou", "Citi Premier", "Citi travel card"],
        # Generic fallback
        "Issuer A":         ["Amex Platinum", "American Express travel"],
        "Issuer B":         ["Capital One Venture", "Venture X"],
        "Issuer C":         ["Chase Sapphire", "Chase travel card"],
    }
    result = {}
    for comp in competitors:
        result[comp] = query_map.get(comp, [comp])
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--year",      type=int)
    parser.add_argument("--month",     type=int)
    parser.add_argument("--data-dir",  default=OUTPUT_DIR)
    args = parser.parse_args()

    year, month = get_target_month(args.year, args.month)
    os.makedirs(args.data_dir, exist_ok=True)

    # Load competitors from config
    try:
        import sys
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from config import GOOGLE_NEWS_QUERIES
        competitors = [q["company"] for q in GOOGLE_NEWS_QUERIES]
    except ImportError:
        competitors = ["Chase", "Capital One", "American Express"]

    print(f"\n{'='*60}")
    print(f"  Reddit Sentiment Scraper  |  {year}-{month:02d}")
    print(f"  Competitors: {len(competitors)} | Subreddits: {len(SUBREDDITS)}")
    print(f"{'='*60}\n")

    query_map = build_competitor_queries(competitors)
    all_posts  = []
    comp_stats = []

    for competitor in competitors:
        print(f"\n  🔍 {competitor}")
        queries  = query_map.get(competitor, [competitor])
        comp_posts = []

        for subreddit in SUBREDDITS:
            for query in queries[:2]:  # max 2 queries per competitor to avoid rate limits
                print(f"    r/{subreddit} → '{query}'")
                posts = search_subreddit(subreddit, query, year, month)
                print(f"      {len(posts)} posts")

                for p in posts:
                    p["competitor"] = competitor
                    p["query"]      = query
                    combined = f"{p['title']} {p['text']}"
                    p["sentiment"] = score_sentiment(combined)
                    comp_posts.append(p)
                    all_posts.append(p)

                time.sleep(REQUEST_DELAY)

        # Deduplicate by post_id
        seen = set()
        unique_posts = []
        for p in comp_posts:
            if p["post_id"] not in seen:
                seen.add(p["post_id"])
                unique_posts.append(p)

        stats = analyze_competitor_sentiment(unique_posts, competitor)
        comp_stats.append(stats)
        print(f"  → {stats['total_posts']} posts | sentiment: {stats['sentiment']} "
              f"(+{stats['positive']} / -{stats['negative']} / ~{stats['neutral']})")

    # ── Save JSON ──────────────────────────────────────────────
    output = {
        "year_month":          f"{year}-{month:02d}",
        "generated_at":        datetime.now().isoformat(),
        "subreddits_monitored": SUBREDDITS,
        "competitor_sentiment": comp_stats,
        "total_posts":         len(all_posts),
    }

    json_path = os.path.join(args.data_dir, f"reddit_sentiment_{year}_{month:02d}.json")
    with open(json_path, "w") as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\n  💾 JSON → {json_path}")

    # ── Save CSV ───────────────────────────────────────────────
    csv_path = os.path.join(args.data_dir, f"reddit_sentiment_{year}_{month:02d}.csv")
    fieldnames = ["competitor", "subreddit", "date", "title", "score",
                  "num_comments", "sentiment", "url"]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for p in sorted(all_posts, key=lambda x: (x["competitor"], -x["score"])):
            w.writerow({k: p.get(k, "") for k in fieldnames})
    print(f"  💾 CSV  → {csv_path}")

    print(f"\n{'='*60}")
    print(f"  ✅ Done! {len(all_posts)} total posts across {len(competitors)} competitors")
    for s in sorted(comp_stats, key=lambda x: x["total_posts"], reverse=True):
        bar = "🟢" if s["sentiment"] == "positive" else ("🔴" if s["sentiment"] == "negative" else "⚪")
        print(f"  {bar} {s['competitor']}: {s['total_posts']} posts | "
              f"+{s['positive']} -{s['negative']} ~{s['neutral']}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
