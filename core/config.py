"""
config.py
=========
Single source of truth for all competitor data across the pipeline:
  - CARD_OFFER_SITES     → used by screenshot_script.py + extract_card_data.py
  - COMPETITORS          → used by all news scrapers for title matching
  - NEWSROOM_SOURCES     → used by newsroom_scraper.py
  - GOOGLE_NEWS_QUERIES  → used by google_news_scraper.py

To update a URL or add a competitor, edit only this file.
"""

# ─────────────────────────────────────────────────────────────
# CARD OFFER SITES
# Used by: screenshot_script.py, extract_card_data.py
# wait_time = seconds to wait for JS to render before screenshot
# ─────────────────────────────────────────────────────────────

CARD_OFFER_SITES = [
    {
# ── AMEX ──────────────────────────────────────────
        "name":      "American Express Platinum Card",
        "company":   "American Express",
        "url":       "https://www.americanexpress.com/us/credit-cards/card/platinum/",
        "wait_time": 10,
    },

# ── Capital One ──────────────────────────────────────────
    {
        "name":      "Capital One Venture X",
        "company":   "Capital One",
        "url":       "https://www.capitalone.com/credit-cards/venture-x/",
        "wait_time": 10,
    },

# ── Chase ──────────────────────────────────────────
    {
        "name":      "Chase Sapphire Reserve® Credit Card",
        "company":   "Chase",
        "url":       "https://creditcards.chase.com/rewards-credit-cards/sapphire/preferred",
        "wait_time": 10,
    }


]

# ─────────────────────────────────────────────────────────────
# COMPETITOR NAMES
# Used by: all news scrapers for title keyword matching
# ─────────────────────────────────────────────────────────────

COMPETITORS = [
    "Chase",
    "Amex",
    "Capital One"
]

# ─────────────────────────────────────────────────────────────
# NEWSROOM SOURCES
# Used by: newsroom_scraper.py
# Queries target press releases syndicated via Google News RSS
# ─────────────────────────────────────────────────────────────

NEWSROOM_SOURCES = [
    
    # Card issuers
    {
        "company": "Chase",
        "type":    "card_issuer",
        "query":   '"JPMorgan Chase" OR "Chase" credit card (announcement OR "press release" OR launches OR introduces OR unveils)',
    },
    {
        "company": "American Express",
        "type":    "card_issuer",
        "query":   '"American Express" (announcement OR "press release" OR launches OR introduces OR unveils)',
    },
    {
        "company": "Capital One",
        "type":    "card_issuer",
        "query":   '"Capital One" (announcement OR "press release" OR launches OR introduces OR unveils)',
    }
]

# ─────────────────────────────────────────────────────────────
# GOOGLE NEWS QUERIES
# Used by: google_news_scraper.py
# Three buckets per competitor: loyalty, product, company news
# ─────────────────────────────────────────────────────────────

GOOGLE_NEWS_QUERIES = [
    
    {
        "company":        "Capital One",
        "loyalty_query":  '"Capital One Miles" OR "Venture Miles" loyalty program change OR update OR enhancement',
        "product_query":  '"Capital One Venture" OR "Capital One" travel card new OR launch OR bonus OR offer OR benefit',
        "company_query":  '"Capital One" earnings OR acquisition OR merger OR revenue OR performance OR fintech',
    },
    {
        "company":        "Chase",
        "loyalty_query":  '"Chase Ultimate Rewards" loyalty program change OR update OR devaluation OR enhancement',
        "product_query":  '"Chase Sapphire" OR "Chase" travel card new OR launch OR bonus OR offer OR benefit',
        "company_query":  '"JPMorgan Chase" earnings OR acquisition OR merger OR revenue OR performance',
    },
    {
        "company":        "American Express",
        "loyalty_query":  '"Membership Rewards" Amex loyalty program change OR update OR devaluation OR enhancement',
        "product_query":  '"Amex Platinum" OR "American Express" travel card new OR launch OR bonus OR offer OR benefit',
        "company_query":  '"American Express" earnings OR acquisition OR merger OR revenue OR performance',
    }
]
