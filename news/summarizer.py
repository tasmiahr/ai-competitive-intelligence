"""
summarizer.py
=============
Shared Claude-based summarization used by all three scrapers.
Uses anthropic client.
Requires: pip install anthropic
Secret:   ANTHROPIC_API_KEY
"""
import os
import re
import requests

CLAUDE_MODEL = "claude-haiku-4-5-20251001"

FOCUS_BY_SOURCE = {
    "tpg":      "what the market/media says about this competitor's product or loyalty program",
    "newsroom": "what the company announced and what it reveals about their strategic priorities",
    "google":   "loyalty program changes, new products/features, market moves, or financial health signals",
}

SUMMARY_PROMPT = (
    "You are a competitive intelligence analyst for a travel credit card product team.\n\n"
    "Article title: {title}\n"
    "Competitor: {competitor}\n"
    "Focus: {focus}\n\n"
    "Article text:\n{text}\n\n"
    "Write ONE sentence using EXACTLY this format (max 25 words):\n"
    "\"[Competitor] [did X], [competitive implication].\"\n\n"
    "Return only the sentence. No preamble, no quotes around it."
)

WEB_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

_client = None
_api_key_checked = False


def _get_client():
    global _client, _api_key_checked
    if _api_key_checked:
        return _client
    _api_key_checked = True
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    print(f"  🔑 ANTHROPIC_API_KEY: {'set (' + str(len(api_key)) + ' chars)' if api_key else '❌ NOT SET'}")
    if not api_key:
        return None
    try:
        import anthropic
        _client = anthropic.Anthropic(api_key=api_key)
        print(f"  ✅ Claude client ready ({CLAUDE_MODEL})")
        return _client
    except Exception as e:
        print(f"  ❌ Claude init failed: {e}")
        return None


def fetch_text(url, max_chars=5000):
    try:
        resp = requests.get(url, headers=WEB_HEADERS, timeout=15)
        resp.raise_for_status()
        text = re.sub(r"<[^>]+>", " ", resp.text)
        text = re.sub(r"&[a-z]+;", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        print(f"      📄 Fetched {len(text)} chars")
        return text[:max_chars]
    except Exception as e:
        print(f"      ⚠️  Page fetch failed: {e}")
        return ""


def summarize(url, competitor, source_type="tpg", title=""):
    client = _get_client()
    if client is None:
        return ""

    text = fetch_text(url)
    if not text:
        print(f"      ⚠️  No page text — using title only")
        text = f"Article title: {title}" if title else "(page unavailable)"

    focus  = FOCUS_BY_SOURCE.get(source_type, FOCUS_BY_SOURCE["tpg"])
    prompt = SUMMARY_PROMPT.format(
        title=title or url,
        competitor=competitor,
        focus=focus,
        text=text,
    )

    try:
        import anthropic
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=100,
            messages=[{"role": "user", "content": prompt}]
        )
        summary = response.content[0].text.strip().strip('"').strip("'")
        print(f"      ✅ {summary[:80]}...")
        return summary
    except Exception as e:
        print(f"      ❌ Claude error for {competitor}: {e}")
        return ""


def check_api_key():
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return False, "ANTHROPIC_API_KEY not set — summaries will be blank"
    try:
        import anthropic  # noqa
        return True, "✅ Claude API ready"
    except ImportError:
        return False, "anthropic not installed — run: pip install anthropic"
