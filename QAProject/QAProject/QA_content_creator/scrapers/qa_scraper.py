"""QA / test-automation / AI-in-QA / vibe-coding / n8n content scraping.

Pulls real, current items from RSS feeds, dev.to's public API, the Hacker
News Algolia API, Reddit's read-only RSS feeds, and GitHub's search API.
Every source function fails soft to `[]` on any network/parse error so one
dead feed never breaks the whole pool — agents.* always have something real
to ground their prompts in, or gracefully have nothing and say so.
"""
import calendar
from datetime import datetime
from urllib.parse import urlparse

import feedparser
import requests

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) QAContentAgent/1.0"
REQUEST_TIMEOUT = 10

RSS_FEEDS = [
    "https://www.ministryoftesting.com/feed",
    "https://www.selenium.dev/blog/index.xml",
    "https://testguild.com/feed/",
    "https://applitools.com/blog/feed/",
    "https://blog.n8n.io/rss/",
]

DEVTO_TAGS = ["testing", "qa", "automation", "ai", "playwright", "selenium"]

HN_QUERIES = [
    "test automation",
    "AI agent QA",
    "vibe coding",
    "Selenium",
    "Playwright",
    "n8n",
]

REDDIT_SUBREDDITS = ["QualityAssurance", "softwaretesting", "selenium", "n8n", "automation"]

GITHUB_TOPICS = ["selenium", "playwright", "test-automation", "ai-agents", "n8n"]


def get_rss_items(limit=20):
    """Fetch and aggregate items from QA/automation blog RSS feeds, sorted by recency."""
    items = []
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url, request_headers={"User-Agent": USER_AGENT})
            for entry in feed.entries[:10]:
                items.append({
                    "type": "rss",
                    "headline": entry.get("title", "").strip(),
                    "summary": _clean_summary(entry.get("summary", "")),
                    "source_url": entry.get("link", ""),
                    "published_parsed": entry.get("published_parsed"),
                })
        except Exception:
            continue

    items.sort(key=lambda a: a["published_parsed"] or 0, reverse=True)
    return items[:limit]


def get_devto_items(limit=20):
    """Fetch recent dev.to articles tagged with QA/automation/AI topics."""
    items = []
    for tag in DEVTO_TAGS:
        try:
            resp = requests.get(
                "https://dev.to/api/articles",
                params={"tag": tag, "per_page": 6},
                headers={"User-Agent": USER_AGENT},
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            for article in resp.json():
                items.append({
                    "type": "devto",
                    "headline": article.get("title", "").strip(),
                    "summary": article.get("description", ""),
                    "source_url": article.get("url", ""),
                    "published_parsed": _parse_iso(article.get("published_at")),
                })
        except Exception:
            continue
    return items[:limit]


def get_hn_items(limit=20):
    """Query the Hacker News Algolia API for recent QA/automation/AI-agent stories."""
    items = []
    for query in HN_QUERIES:
        try:
            resp = requests.get(
                "https://hn.algolia.com/api/v1/search_by_date",
                params={"query": query, "tags": "story", "hitsPerPage": 5},
                headers={"User-Agent": USER_AGENT},
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            for hit in resp.json().get("hits", []):
                items.append({
                    "type": "hackernews",
                    "headline": hit.get("title", "").strip(),
                    "summary": hit.get("story_text") or hit.get("title", ""),
                    "source_url": hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
                    "published_parsed": _parse_iso(hit.get("created_at")),
                })
        except Exception:
            continue
    return items[:limit]


def get_reddit_items(limit=20):
    """Fetch recent posts from QA/automation subreddits via their read-only RSS feeds."""
    items = []
    for sub in REDDIT_SUBREDDITS:
        try:
            feed = feedparser.parse(
                f"https://www.reddit.com/r/{sub}/.rss",
                request_headers={"User-Agent": USER_AGENT},
            )
            for entry in feed.entries[:5]:
                items.append({
                    "type": "reddit",
                    "headline": entry.get("title", "").strip(),
                    "summary": _clean_summary(entry.get("summary", "")),
                    "source_url": entry.get("link", ""),
                    "published_parsed": entry.get("published_parsed"),
                })
        except Exception:
            continue
    return items[:limit]


def get_github_items(limit=15):
    """Fetch recently-updated trending repos for QA/automation/AI-agent GitHub topics."""
    items = []
    for topic in GITHUB_TOPICS:
        try:
            resp = requests.get(
                "https://api.github.com/search/repositories",
                params={"q": f"topic:{topic}", "sort": "updated", "per_page": 3},
                headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"},
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            for repo in resp.json().get("items", []):
                items.append({
                    "type": "github",
                    "headline": f"{repo.get('full_name')} — {repo.get('description') or 'no description'}",
                    "summary": (
                        f"{repo.get('full_name')} has {repo.get('stargazers_count')} stars. "
                        f"Description: {repo.get('description') or 'n/a'}"
                    ),
                    "source_url": repo.get("html_url", ""),
                    "published_parsed": _parse_iso(repo.get("updated_at")),
                })
        except Exception:
            continue
    return items[:limit]


def get_item_pool(limit=40):
    """Aggregate every source into one pool, sorted most-recent-first, fail-soft per source."""
    pool = (
        get_rss_items()
        + get_devto_items()
        + get_hn_items()
        + get_reddit_items()
        + get_github_items()
    )
    pool.sort(key=lambda a: a["published_parsed"] or 0, reverse=True)
    return pool[:limit]


def get_top_item():
    """Return the single most relevant/recent real item, or None if every source failed."""
    pool = get_item_pool(limit=10)
    return pool[0] if pool else None


def _clean_summary(html_summary, max_len=400):
    try:
        from bs4 import BeautifulSoup
        text = BeautifulSoup(html_summary, "lxml").get_text(separator=" ", strip=True)
    except Exception:
        text = html_summary
    return (text or "")[:max_len]


def _parse_iso(iso_str):
    """Parse an ISO-8601 timestamp into a struct_time, matching feedparser's format."""
    if not iso_str:
        return None
    try:
        cleaned = iso_str.replace("Z", "+00:00")
        return datetime.fromisoformat(cleaned).utctimetuple()
    except Exception:
        return None


def _time_ago(published_parsed):
    """Format a `published_parsed` struct_time as e.g. '2 hours ago'."""
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
    """Derive a display source name (e.g. 'dev.to') from an item URL."""
    if not url:
        return "Unknown source"
    host = urlparse(url).netloc.replace("www.", "")
    return host or "Unknown source"
