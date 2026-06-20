"""QA/automation item -> LinkedIn post content generator."""
from agents import LINKEDIN_IMAGE_GUIDELINES
from scrapers.qa_scraper import get_item_pool, get_top_item


def _live_data_snapshot():
    """Pull a snapshot of real, current QA/automation items to ground GPT's
    output — its own training data can be stale, so any specific tool name,
    version, or stat it writes must trace back to one of these lines."""
    lines = []
    try:
        for item in get_item_pool(limit=10):
            lines.append(f"- [{item['type'].upper()}] {item['headline']}: {item['summary'][:200]}")
    except Exception:
        pass
    return "\n".join(lines) if lines else "(no live data available right now)"


def build_prompt(item=None, custom_topic=None):
    """Build the GPT user prompt for a LinkedIn post.

    Uses the given pre-fetched `item` (a user-selected option card) if
    provided — grounded directly in that item's real data. If `custom_topic`
    is given instead (the free-text custom-topic path), grounds the post in
    a LIVE DATA SNAPSHOT of recent real items instead of a single picked one.
    With neither, falls back to the single most relevant recent item.
    """
    if custom_topic:
        snapshot = _live_data_snapshot()
        data_block = f"The user wants a LinkedIn post about: {custom_topic}"
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
                "data IS available for this post. Base the post and any "
                "specifics ONLY on facts stated above — do not add any tool "
                "version, number, or claim that isn't mentioned there."
            )
        else:
            data_block = "No single item was picked."
            data_note = (
                "\n\nNo single item was picked. Write a general, timeless post "
                "about the topic below — do NOT invent any specific tool "
                "version, statistic, or claim."
            )

    return f"""{data_block}{data_note}

Generate a LinkedIn post for QA/test-automation/AI-in-QA practitioners.

Generate:
1. A short HOOK headline (4-10 words) for internal use/preview — not necessarily baked into the image.
2. A LinkedIn CAPTION, ~150-200 words, practitioner voice (see voice rules in system prompt). One concrete specific detail anchored in real data above if available. Mixed sentence length. A varied, topic-specific closing line — not a generic template CTA.
3. A FULL GRAPHIC IMAGE PROMPT for gpt-image-1 that bakes the hook headline and, if this content is cheatsheet/listicle-style, 2-4 short bullet lines written VERBATIM in this prompt. {LINKEDIN_IMAGE_GUIDELINES}
4. Top 3-5 LinkedIn hashtags (QA/automation tag pool — mix of broad + niche, e.g. #QualityAssurance #TestAutomation #Playwright).

Respond in JSON format:
{{
  "headline": "...",
  "caption": "...",
  "image_prompt": "...",
  "hashtags": ["#tag1", "#tag2", "#tag3"]
}}"""
