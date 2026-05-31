"""
config.py
=========
Public portfolio config — tracks Big Tech AI competitive landscape.
Apple, Google, Microsoft, Amazon, Meta.
"""

# ─────────────────────────────────────────────────────────────
# CARD OFFER SITES
# Used by: website/screenshot_script.py, website/compare_screenshots.py
# Tracks key product/pricing pages for each competitor
# ─────────────────────────────────────────────────────────────

CARD_OFFER_SITES = [
    {
        "name":      "Apple Intelligence",
        "company":   "Apple",
        "url":       "https://www.apple.com/apple-intelligence/",
        "wait_time": 8,
    },
    {
        "name":      "Google Gemini",
        "company":   "Google",
        "url":       "https://gemini.google.com/",
        "wait_time": 8,
    },
    {
        "name":      "Microsoft Copilot",
        "company":   "Microsoft",
        "url":       "https://copilot.microsoft.com/",
        "wait_time": 8,
    },
    {
        "name":      "Amazon Bedrock",
        "company":   "Amazon",
        "url":       "https://aws.amazon.com/bedrock/",
        "wait_time": 8,
    },
    {
        "name":      "Meta AI",
        "company":   "Meta",
        "url":       "https://ai.meta.com/",
        "wait_time": 8,
    },
]

# ─────────────────────────────────────────────────────────────
# COMPETITOR NAMES
# ─────────────────────────────────────────────────────────────

COMPETITORS = ["Apple", "Google", "Microsoft", "Amazon", "Meta"]

# ─────────────────────────────────────────────────────────────
# NEWSROOM SOURCES
# Press releases and official announcements
# ─────────────────────────────────────────────────────────────

NEWSROOM_SOURCES = [
    {
        "company": "Apple",
        "type":    "tech",
        "query":   '"Apple" AI OR "Apple Intelligence" OR "Core ML" (announcement OR launches OR introduces OR unveils)',
    },
    {
        "company": "Google",
        "type":    "tech",
        "query":   '"Google" Gemini OR "Google AI" OR "Google DeepMind" (announcement OR launches OR introduces OR unveils)',
    },
    {
        "company": "Microsoft",
        "type":    "tech",
        "query":   '"Microsoft" Copilot OR "Azure AI" OR "Microsoft AI" (announcement OR launches OR introduces OR unveils)',
    },
    {
        "company": "Amazon",
        "type":    "tech",
        "query":   '"Amazon" Bedrock OR "AWS AI" OR "Amazon AI" (announcement OR launches OR introduces OR unveils)',
    },
    {
        "company": "Meta",
        "type":    "tech",
        "query":   '"Meta AI" OR "Llama" OR "Meta" AI (announcement OR launches OR introduces OR unveils)',
    },
]

# ─────────────────────────────────────────────────────────────
# GOOGLE NEWS QUERIES
# Three buckets per competitor:
#   product_query  → product launches, features, updates
#   loyalty_query  → ecosystem, partnerships, platform changes
#   company_query  → earnings, strategy, regulation, M&A
# ─────────────────────────────────────────────────────────────

GOOGLE_NEWS_QUERIES = [
    {
        "company":        "Apple",
        "product_query":  '"Apple Intelligence" OR "Apple AI" OR "Core ML" new OR launch OR update OR feature OR release',
        "loyalty_query":  '"Apple" ecosystem OR developer OR "App Store" AI OR partnership OR platform update',
        "company_query":  '"Apple" earnings OR revenue OR acquisition OR regulation OR "market share" OR strategy',
    },
    {
        "company":        "Google",
        "product_query":  '"Gemini" OR "Google AI" new OR launch OR update OR feature OR release OR benchmark',
        "loyalty_query":  '"Google Cloud" OR "Google Workspace" OR "Vertex AI" partnership OR platform OR developer OR update',
        "company_query":  '"Alphabet" OR "Google" earnings OR revenue OR acquisition OR regulation OR antitrust OR strategy',
    },
    {
        "company":        "Microsoft",
        "product_query":  '"Copilot" OR "Azure AI" OR "Microsoft AI" new OR launch OR update OR feature OR release',
        "loyalty_query":  '"Microsoft 365" OR "Azure" OR "GitHub Copilot" partnership OR platform OR developer OR update',
        "company_query":  '"Microsoft" earnings OR revenue OR acquisition OR regulation OR strategy OR "market share"',
    },
    {
        "company":        "Amazon",
        "product_query":  '"Amazon Bedrock" OR "AWS AI" OR "Amazon AI" OR "Nova" new OR launch OR update OR feature OR release',
        "loyalty_query":  '"AWS" OR "Amazon Web Services" partnership OR platform OR developer OR pricing OR update',
        "company_query":  '"Amazon" earnings OR revenue OR acquisition OR regulation OR "AWS" strategy OR "market share"',
    },
    {
        "company":        "Meta",
        "product_query":  '"Llama" OR "Meta AI" OR "Meta" AI new OR launch OR update OR feature OR release OR open source',
        "loyalty_query":  '"Meta" developer OR platform OR partnership OR "WhatsApp" OR "Instagram" AI update',
        "company_query":  '"Meta" earnings OR revenue OR acquisition OR regulation OR strategy OR "Reality Labs"',
    },
]

# For test runs — 2 competitors only
GOOGLE_NEWS_QUERIES_TEST = GOOGLE_NEWS_QUERIES[:2]
NEWSROOM_SOURCES_TEST    = NEWSROOM_SOURCES[:2]
