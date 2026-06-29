"""Football news -> Instagram post content generator."""
from agents import FULL_GRAPHIC_GUIDELINES
from scrapers.football_scraper import get_top_story


def build_prompt(story=None):
    """Build the GPT user prompt for a football news story.

    Uses the given pre-fetched `story` (e.g. a user-selected option) if
    provided, otherwise scrapes the top trending story itself.
    """
    if story is None:
        story = get_top_story()

    if story:
        headline = story["headline"]
        summary = story["summary"]
        data_note = (
            "\n\nThe HEADLINE and SUMMARY above are REAL scraped data from a "
            "live football news feed — live data IS available for this post. "
            "Base the caption and stats bullets ONLY on facts stated in them "
            "— do not add any scores, numbers, or names that aren't mentioned "
            'there, and do NOT include a "Live data unavailable" bullet.'
        )
    else:
        headline = "Live data unavailable"
        summary = "No live news could be fetched right now."
        data_note = (
            "\n\nNo live news data is available. Write a general caption about "
            'football fan culture with a "stay tuned for the latest news" '
            'framing — do NOT invent any specific stats, scores, or facts. Set '
            '"stats_bullets" to exactly one item: "Follow @thefootbroshow for '
            'more football news & stats".'
        )

    return f"""Based on this football news:
HEADLINE: {headline}
SUMMARY: {summary}{data_note}

Generate:
1. A punchy IMAGE HEADLINE — a short, bold breaking-news-style hook (4-8 words, ALL CAPS, no emojis) that will be displayed in huge letters on the post image, e.g. "NEYMAR'S FINAL WORLD CUP?"
2. A SHORT Instagram CAPTION (max 150 words) — punchy, fan-friendly, opinionated. Add 1-2 emojis per line. End with a CTA like "Drop your thoughts below \U0001F447" or "Agree? Let us know \U0001F525"
3. A FULL GRAPHIC IMAGE PROMPT for gpt-image-1 that bakes the headline and the
   key stats bullets below directly into the image as on-image text/graphics.
   {FULL_GRAPHIC_GUIDELINES}
4. Exactly 4 KEY STATS bullets — short, factual, sourced from the SUMMARY above only. No invented stats.
5. Exactly 4 FUN FACTS — verified football trivia, historical context, or interesting facts about the players/clubs/competition in this story. Start each with a relevant emoji (⚽ 🏆 🔥 📊 🎯 ⭐ 🏟️). Must be accurate.
6. Top 5 SEO hashtags for football Instagram (mix of broad + niche)

Respond in JSON format:
{{
  "headline": "...",
  "caption": "...",
  "image_prompt": "...",
  "stats_bullets": ["• ...", "• ...", "• ...", "• ..."],
  "fun_facts": ["⚽ ...", "🏆 ...", "🔥 ...", "📊 ..."],
  "hashtags": ["#tag1", "#tag2", "#tag3", "#tag4", "#tag5"]
}}"""
