"""Football news and fixture/result scraping for FootBro Show agents.

News comes from RSS feeds (Goal, ESPN). Fixtures and results come from
ESPN's public scoreboard JSON endpoints for the top European/world leagues.
All functions fail soft — on any network/parse error they return an empty
list so agents can fall back to GPT's own knowledge.
"""
import calendar
from datetime import datetime, timedelta
from urllib.parse import urlparse

import feedparser
import requests

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) FootBroContentAgent/1.0"
REQUEST_TIMEOUT = 10

RSS_FEEDS = [
    "https://www.goal.com/feeds/en/news",
    "https://www.espn.com/espn/rss/soccer/news",
    "http://feeds.bbci.co.uk/sport/football/rss.xml",
    "https://www.skysports.com/rss/11095",
    "https://www.theguardian.com/football/rss",
]

# ESPN soccer league codes -> display names (top leagues + international).
TOP_LEAGUES = {
    "uefa.champions": "UEFA Champions League",
    "eng.1": "Premier League",
    "esp.1": "La Liga",
    "ita.1": "Serie A",
    "ger.1": "Bundesliga",
    "fra.1": "Ligue 1",
    "ind.1": "Indian Super League",
    "fifa.world": "International",
}

ESPN_SCOREBOARD_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/{league}/scoreboard"


def get_latest_news(limit=5):
    """Fetch and aggregate the latest football news from RSS feeds, sorted by recency."""
    articles = []
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url, request_headers={"User-Agent": USER_AGENT})
            for entry in feed.entries[:10]:
                image_url = _extract_entry_image(entry)
                articles.append({
                    "headline": entry.get("title", "").strip(),
                    "summary": _clean_summary(entry.get("summary", "")),
                    "source_url": entry.get("link", ""),
                    "image_url": image_url,
                    "published_parsed": entry.get("published_parsed"),
                })
        except Exception:
            continue

    articles.sort(key=lambda a: a["published_parsed"] or 0, reverse=True)
    return articles[:limit]


def get_top_story():
    """Return a real football news story, or None if every data source failed.

    Tries the RSS feeds first. If they're all empty (network issue/blocked
    feed), falls back to building a story from real ESPN scoreboard data
    (a recent result, or failing that, today's headline fixture) so the
    rest of the app still has real facts to work with.
    """
    for article in get_latest_news(limit=10):
        summary = (article["summary"] or "").strip()
        if summary and summary.lower() != "null":
            return article

    results = get_recent_results()
    if results:
        r = results[0]
        score = f"{r['home_score']}-{r['away_score']}"
        return {
            "headline": f"{r['home_team']} {score} {r['away_team']} ({r['competition']})",
            "summary": (
                f"{r['home_team']} and {r['away_team']} played out a {score} "
                f"result in the {r['competition']} at {r['venue']}. "
                f"Match status: {r['status']}."
            ),
            "source_url": "",
            "image_url": "",
            "published_parsed": None,
        }

    fixtures = get_today_fixtures()
    if fixtures:
        f = fixtures[0]
        return {
            "headline": f"{f['home_team']} vs {f['away_team']} ({f['competition']})",
            "summary": (
                f"{f['home_team']} face {f['away_team']} in the "
                f"{f['competition']} at {f['venue']}."
            ),
            "source_url": "",
            "image_url": "",
            "published_parsed": None,
        }

    return None


def get_today_fixtures():
    """Return upcoming (not yet started) fixtures across the top leagues.

    Checks today first, then the next couple of days, so a quiet matchday
    doesn't leave the app with no real data to work with.
    """
    return _collect_events(state="pre", date_offsets=(0, 1, 2))


def get_recent_results():
    """Return recently completed fixtures across the top leagues.

    Checks today first, then looks back a couple of days, so the app
    almost always has a real recent result to work with.
    """
    return _collect_events(state="post", date_offsets=(0, -1, -2))


def _collect_events(state, date_offsets=(0,)):
    for offset in date_offsets:
        date_str = (datetime.utcnow() + timedelta(days=offset)).strftime("%Y%m%d")
        events_out = []
        for league_code, league_name in TOP_LEAGUES.items():
            try:
                resp = requests.get(
                    ESPN_SCOREBOARD_URL.format(league=league_code),
                    params={"dates": date_str},
                    headers={"User-Agent": USER_AGENT},
                    timeout=REQUEST_TIMEOUT,
                )
                resp.raise_for_status()
                data = resp.json()
            except Exception:
                continue

            for event in data.get("events", []):
                try:
                    event_state = event.get("status", {}).get("type", {}).get("state")
                    if event_state != state:
                        continue
                    events_out.append(_parse_event(event, league_name))
                except Exception:
                    continue

        if events_out:
            return events_out

    return []


def _parse_event(event, league_name):
    competition = event.get("competitions", [{}])[0]
    competitors = competition.get("competitors", [])

    home = next((c for c in competitors if c.get("homeAway") == "home"), {})
    away = next((c for c in competitors if c.get("homeAway") == "away"), {})

    return {
        "home_team": home.get("team", {}).get("displayName", "Home"),
        "away_team": away.get("team", {}).get("displayName", "Away"),
        "home_score": home.get("score"),
        "away_score": away.get("score"),
        "home_form": _form_string(home),
        "away_form": _form_string(away),
        "competition": league_name,
        "date": event.get("date", ""),
        "venue": competition.get("venue", {}).get("fullName", ""),
        "status": event.get("status", {}).get("type", {}).get("description", ""),
    }


def _form_string(competitor):
    forms = competitor.get("form") or competitor.get("statistics") or ""
    if isinstance(forms, list):
        return ", ".join(str(f) for f in forms)
    return str(forms)


def _clean_summary(html_summary, max_len=400):
    try:
        from bs4 import BeautifulSoup
        text = BeautifulSoup(html_summary, "lxml").get_text(separator=" ", strip=True)
    except Exception:
        text = html_summary
    return text[:max_len]


def _extract_entry_image(entry):
    if "media_content" in entry and entry.media_content:
        return entry.media_content[0].get("url", "")
    if "media_thumbnail" in entry and entry.media_thumbnail:
        return entry.media_thumbnail[0].get("url", "")
    return ""


def _time_ago(published_parsed):
    """Format an RSS `published_parsed` struct_time as e.g. '2 hours ago'."""
    if not published_parsed:
        return "recently"

    published = datetime.utcfromtimestamp(calendar.timegm(published_parsed))
    seconds = max((datetime.utcnow() - published).total_seconds(), 0)

    if seconds < 60:
        return "just now"
    minutes = int(seconds // 60)
    if minutes < 60:
        return f"{minutes} min{'s' if minutes != 1 else ''} ago"
    hours = int(minutes // 60)
    if hours < 24:
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    days = int(hours // 24)
    return f"{days} day{'s' if days != 1 else ''} ago"


def _source_name(url):
    """Derive a display source name (e.g. 'Goal.com') from an article URL."""
    if not url:
        return "Unknown source"
    host = urlparse(url).netloc.replace("www.", "")
    return host or "Unknown source"
