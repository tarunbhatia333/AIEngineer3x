"""Today's big fixture -> match preview Instagram post content generator."""
from agents import IMAGE_PROMPT_GUIDELINES
from scrapers.football_scraper import get_today_fixtures


def build_prompt():
    """Fetch today's headline fixture and build the GPT user prompt for it."""
    fixtures = get_today_fixtures()
    fixture = fixtures[0] if fixtures else None

    if fixture:
        match_details = (
            f"{fixture['home_team']} vs {fixture['away_team']} "
            f"({fixture['competition']}, {fixture['date']})\n"
            f"Venue: {fixture['venue']}\n"
            f"{fixture['home_team']} recent form: {fixture['home_form'] or 'unknown'}\n"
            f"{fixture['away_team']} recent form: {fixture['away_form'] or 'unknown'}"
        )
        data_note = (
            "\n\nThe match details above (teams, competition, date, venue, "
            "recent form) are REAL scraped data — live data IS available for "
            "this post. Base the stats bullets ONLY on these facts — do not "
            "invent head-to-head records, attendance, or other numbers not "
            'given here, and do NOT include a "Live data unavailable" bullet.'
        )
        stakes_note = "- Stakes and storylines\n- Key players to watch (2-3 each side)\n- FootBro Show prediction"
    else:
        match_details = "No live fixture data is available right now."
        data_note = (
            '\n\nNo live fixture data is available. Write a general caption '
            'about today\'s football action with a "stay tuned for fixtures" '
            'framing — do NOT invent any specific teams, scores, or stats. Set '
            '"stats_bullets" to exactly one item: "Follow @thefootbroshow for '
            'more football news & stats".'
        )
        stakes_note = "- General hype for today's football action\n- FootBro Show talking points"

    return f"""Create a match preview for: {match_details}{data_note}

Include:
{stakes_note}

Generate:
1. A punchy IMAGE HEADLINE — a short, bold breaking-news-style hook (4-8 words, ALL CAPS, no emojis) themed around the fixture, e.g. "ARSENAL vs CHELSEA: TITLE DECIDER?"
2. Instagram CAPTION (punchy, 150 words max, fan-voice, emojis)
3. Bullet point stats block (up to 5 bullets, each grounded in the real match details above — never invent a stat that isn't given)
4. DALL-E image prompt (epic pre-match atmosphere, stadium, both team colors, {IMAGE_PROMPT_GUIDELINES})
5. Top 5 hashtags

Respond in JSON:
{{
  "headline": "...",
  "caption": "...",
  "stats_bullets": ["• Bullet 1", "• Bullet 2", "• Bullet 3", "• Bullet 4", "• Bullet 5"],
  "image_prompt": "...",
  "hashtags": ["#tag1", "#tag2", "#tag3", "#tag4", "#tag5"]
}}"""
