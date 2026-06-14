"""Recently completed match -> match review Instagram post content generator."""
from agents import IMAGE_PROMPT_GUIDELINES
from scrapers.football_scraper import get_recent_results


def build_prompt():
    """Fetch a recently completed match and build the GPT user prompt for it."""
    results = get_recent_results()
    result = results[0] if results else None

    if result:
        score = f"{result['home_score']} - {result['away_score']}"
        match_details = (
            f"{result['home_team']} {score} {result['away_team']} "
            f"({result['competition']})\n"
            f"Venue: {result['venue']}\n"
            f"Status: {result['status']}"
        )
        data_note = (
            "\n\nThe result above (teams, score, competition, venue, status) is "
            "REAL scraped data — live data IS available for this post. Base "
            "the stats bullets ONLY on these facts — do not invent possession, "
            "shots, ratings, MOTM, or attendance figures that aren't given "
            'here, and do NOT include a "Live data unavailable" bullet.'
        )
    else:
        match_details = "No live result data is available right now."
        data_note = (
            '\n\nNo live result data is available. Write a general caption '
            'about recent football talking points with a "stay tuned for '
            'results" framing — do NOT invent any specific teams, scores, or '
            'stats. Set "stats_bullets" to exactly one item: "Follow '
            '@thefootbroshow for more football news & stats".'
        )

    return f"""Write a match review for: {match_details}{data_note}

Generate:
1. A punchy IMAGE HEADLINE — a short, bold breaking-news-style hook (4-8 words, ALL CAPS, no emojis) themed around the result, e.g. "BARCELONA DEMOLISH REAL MADRID 4-0"
2. Instagram CAPTION — reaction-style, fan voice, hot take, 150 words max
3. Stats bullets for image (up to 5 bullets, each grounded in the real result details above — never invent a stat that isn't given)
4. DALL-E image prompt (post-match celebration or drama, {IMAGE_PROMPT_GUIDELINES})
5. Top 5 hashtags

Respond in JSON:
{{
  "headline": "...",
  "caption": "...",
  "stats_bullets": ["• Bullet 1", "• Bullet 2", "• Bullet 3", "• Bullet 4", "• Bullet 5"],
  "image_prompt": "...",
  "hashtags": ["#tag1", "#tag2", "#tag3", "#tag4", "#tag5"]
}}"""
