"""
config.py
=========
Anonymized config for public portfolio demo.
Uses 3 card issuers as competitors (no airline PII).
"""

CARD_OFFER_SITES = [
    {
        "name":      "Issuer A Platinum Card",
        "company":   "Issuer A",
        "url":       "https://www.americanexpress.com/us/credit-cards/card/platinum/",
        "wait_time": 10,
    },
    {
        "name":      "Issuer B Venture X",
        "company":   "Issuer B",
        "url":       "https://www.capitalone.com/credit-cards/venture-x/",
        "wait_time": 10,
    },
    {
        "name":      "Issuer C Sapphire Reserve",
        "company":   "Issuer C",
        "url":       "https://creditcards.chase.com/rewards-credit-cards/sapphire/reserve",
        "wait_time": 10,
    },
]

COMPETITORS = ["Issuer A", "Issuer B", "Issuer C"]

NEWSROOM_SOURCES = [
    {
        "company": "Issuer A",
        "type":    "card_issuer",
        "query":   '"American Express" (announcement OR "press release" OR launches OR introduces OR unveils)',
    },
    {
        "company": "Issuer B",
        "type":    "card_issuer",
        "query":   '"Capital One" (announcement OR "press release" OR launches OR introduces OR unveils)',
    },
    {
        "company": "Issuer C",
        "type":    "card_issuer",
        "query":   '"JPMorgan Chase" OR "Chase" credit card (announcement OR "press release" OR launches OR introduces OR unveils)',
    },
]

GOOGLE_NEWS_QUERIES = [
    {
        "company":        "Issuer A",
        "loyalty_query":  '"Membership Rewards" loyalty program change OR update OR devaluation OR enhancement',
        "product_query":  '"Amex Platinum" OR "American Express" travel card new OR launch OR bonus OR offer OR benefit',
        "company_query":  '"American Express" earnings OR acquisition OR merger OR revenue OR performance',
    },
    {
        "company":        "Issuer B",
        "loyalty_query":  '"Capital One Miles" OR "Venture Miles" loyalty program change OR update OR enhancement',
        "product_query":  '"Capital One Venture" OR "Capital One" travel card new OR launch OR bonus OR offer OR benefit',
        "company_query":  '"Capital One" earnings OR acquisition OR merger OR revenue OR performance OR fintech',
    },
    {
        "company":        "Issuer C",
        "loyalty_query":  '"Chase Ultimate Rewards" loyalty program change OR update OR devaluation OR enhancement',
        "product_query":  '"Chase Sapphire" OR "Chase" travel card new OR launch OR bonus OR offer OR benefit',
        "company_query":  '"JPMorgan Chase" earnings OR acquisition OR merger OR revenue OR performance',
    },
]

# Test config — 2 competitors only
GOOGLE_NEWS_QUERIES_TEST = GOOGLE_NEWS_QUERIES[:2]
NEWSROOM_SOURCES_TEST    = NEWSROOM_SOURCES[:2]
