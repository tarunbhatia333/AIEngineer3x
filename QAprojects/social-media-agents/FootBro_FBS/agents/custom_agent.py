"""Free-form user prompt -> Instagram post content generator."""
from agents import FULL_GRAPHIC_GUIDELINES
from scrapers.football_scraper import get_latest_news, get_recent_results, get_today_fixtures


def _live_data_snapshot():
    """Pull a snapshot of real, current football facts to ground GPT's output —
    GPT's own training data can be months/years stale, so anything specific it
    writes (a score, a fixture, a stat) must trace back to one of these lines."""
    lines = []

    try:
        for a in get_latest_news(limit=8):
            lines.append(f"- NEWS: {a['headline']}")
    except Exception:
        pass

    try:
        for r in get_recent_results():
            lines.append(
                f"- RESULT: {r['home_team']} {r['home_score']}-{r['away_score']} "
                f"{r['away_team']} ({r['competition']})"
            )
    except Exception:
        pass

    try:
        for f in get_today_fixtures():
            lines.append(
                f"- FIXTURE: {f['home_team']} vs {f['away_team']} ({f['competition']}, {f['date']})"
            )
    except Exception:
        pass

    return "\n".join(lines) if lines else "(no live data available right now)"


def build_prompt(user_input):
    """Build the GPT user prompt for an arbitrary football-related topic."""
    snapshot = _live_data_snapshot()
    return f"""The user wants Instagram content about: {user_input}

LIVE FOOTBALL DATA SNAPSHOT (scraped just now from ESPN/Goal/Sky Sports/BBC/Guardian RSS feeds):
{snapshot}

Your own training knowledge may be outdated. If the topic above requires any specific score,
fixture, date, or recent stat, you MUST source it ONLY from the LIVE FOOTBALL DATA SNAPSHOT
above — never invent or recall one from memory. If the snapshot doesn't contain a fact you'd
need, write around it (stay general) instead of guessing.

Generate:
1. A punchy IMAGE HEADLINE — a short, bold breaking-news-style hook (4-8 words, ALL CAPS, no emojis) based on the topic
2. Instagram CAPTION (punchy, opinionated, 150 words, FootBro Show voice)
3. Exactly 4 KEY STATS bullets — real, well-known facts or stats about the topic you are confident are accurate. Never invent numbers.
4. Exactly 4 FUN FACTS — surprising trivia, historical records, or context about the topic. Start each with a relevant emoji (⚽ 🏆 🔥 📊 🎯 ⭐ 🏟️ etc.). Must be accurate and verifiable.
5. A FULL GRAPHIC IMAGE PROMPT for gpt-image-1 that bakes the headline and key
   stats bullets directly into the image as on-image text/graphics. If the
   user's topic above itself describes a multi-match roundup or a ranking
   (e.g. several results plus a "who's leading" comparison), break the image
   into multiple clearly labeled sections — one per match/item — plus a small
   ranked leaderboard table for the comparison. Otherwise keep it to a single
   focused section about the topic. {FULL_GRAPHIC_GUIDELINES}
6. Top 5 hashtags

Respond in JSON format:
{{
  "headline": "...",
  "caption": "...",
  "stats_bullets": ["• ...", "• ...", "• ...", "• ..."],
  "fun_facts": ["⚽ ...", "🏆 ...", "🔥 ...", "📊 ..."],
  "image_prompt": "...",
  "hashtags": ["#tag1", "#tag2", "#tag3", "#tag4", "#tag5"]
}}"""
