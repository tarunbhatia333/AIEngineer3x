"""QA/automation item -> Medium article content generator."""
from agents import MEDIUM_IMAGE_GUIDELINES
from scrapers.qa_scraper import get_item_pool, get_top_item


def _live_data_snapshot():
    """Same grounding pattern as the LinkedIn agent, sampled for depth — a
    Medium article needs enough real detail to support 600-900 words."""
    lines = []
    try:
        for item in get_item_pool(limit=12):
            lines.append(f"- [{item['type'].upper()}] {item['headline']}: {item['summary'][:300]}")
    except Exception:
        pass
    return "\n".join(lines) if lines else "(no live data available right now)"


def build_prompt(item=None, custom_topic=None):
    """Build the GPT user prompt for a Medium article.

    Uses the given pre-fetched `item` (a user-selected option card) if
    provided. If `custom_topic` is given instead (the free-text custom-topic
    path), grounds the article in a LIVE DATA SNAPSHOT of recent real items.
    With neither, falls back to the single most relevant recent item.
    """
    if custom_topic:
        snapshot = _live_data_snapshot()
        data_block = f"The user wants a Medium article about: {custom_topic}"
        data_note = (
            f"\n\nLIVE QA/AUTOMATION DATA SNAPSHOT (scraped just now):\n{snapshot}\n\n"
            "Your own training knowledge may be outdated. If the topic above "
            "requires any specific tool version, statistic, or claim, you "
            "MUST source it ONLY from the snapshot above — never invent or "
            "recall one from memory. If the snapshot doesn't contain a fact "
            "you'd need, write around it (stay general) instead of guessing."
        )
    else:
        if item is None:
            item = get_top_item()

        if item:
            data_block = f"HEADLINE: {item['headline']}\nDETAIL: {item['summary']}"
            data_note = (
                "\n\nThe HEADLINE and DETAIL above are REAL scraped data — live "
                "data IS available for this article. Base the article ONLY on "
                "facts stated above plus general, well-established QA/testing "
                "knowledge — do not add any tool version, number, or claim that "
                "isn't mentioned there or generally well known and timeless."
            )
        else:
            data_block = "No single item was picked."
            data_note = (
                "\n\nNo single item was picked. Write a general, timeless "
                "article about the topic below — do NOT invent any specific "
                "tool version, statistic, or claim."
            )

    return f"""{data_block}{data_note}

Generate a Medium article for QA/test-automation/AI-in-QA practitioners.

Generate:
1. An SEO-aware TITLE (specific, practical, not clickbait).
2. A long-form intro PARAGRAPH (2-4 sentences) that hooks a practitioner reader, practitioner voice (see voice rules in system prompt).
3. An ARTICLE BODY of roughly 600-900 words, in Markdown, with a few subheadings — practical, specific, grounded only in the real data above plus general well-established QA/testing knowledge. Mixed sentence length, contractions, no AI-cliche openers, no hashtag stuffing in the body, at most one em-dash total.
4. A FULL COVER IMAGE PROMPT for gpt-image-1 — simpler than a feed post, title text only, no bullet list. {MEDIUM_IMAGE_GUIDELINES}
5. Exactly 5 Medium tags, lowercase (e.g. "software-testing", "test-automation", "ai", "automation", "qa").

Respond in JSON format:
{{
  "title": "...",
  "intro": "...",
  "body_markdown": "...",
  "image_prompt": "...",
  "tags": ["software-testing", "test-automation", "ai", "automation", "qa"]
}}"""
