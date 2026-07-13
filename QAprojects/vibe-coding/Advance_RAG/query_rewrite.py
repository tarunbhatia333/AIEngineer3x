"""Stage 2 step 1: generate alternate phrasings of the user's question before
retrieval, so hybrid search sees more surface forms of the same intent
(e.g. "how do I..." vs "steps to..." vs the domain term itself).
"""
from __future__ import annotations

import json

from groq import Groq

from config import GROQ_API_KEY, GROQ_REWRITE_MODEL, REWRITE_ENABLED, NUM_REWRITES

_client = None

_SYSTEM = (
    "You rewrite search queries for a hybrid (dense + sparse) retrieval system "
    "over VWO A/B-testing QA test cases. Given a user question, produce "
    f"{NUM_REWRITES} alternate phrasings that preserve the exact meaning but vary "
    "vocabulary, phrasing, and specificity (e.g. one more literal/keyword-heavy, "
    "one more natural-language, one that expands abbreviations). "
    "Respond with ONLY a JSON array of strings, nothing else."
)


def _get_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=GROQ_API_KEY)
    return _client


def rewrite_query(query: str) -> list[str]:
    """Returns the original query plus up to NUM_REWRITES alternates. Falls
    back to just [query] if rewriting is disabled or the call fails."""
    if not REWRITE_ENABLED:
        return [query]

    try:
        resp = _get_client().chat.completions.create(
            model=GROQ_REWRITE_MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": query},
            ],
            temperature=0.5,
            max_tokens=300,
        )
        content = resp.choices[0].message.content.strip()
        if content.startswith("```"):
            content = content.strip("`").split("\n", 1)[-1]
        rewrites = json.loads(content)
        rewrites = [r for r in rewrites if isinstance(r, str) and r.strip()][:NUM_REWRITES]
        return [query] + rewrites if rewrites else [query]
    except Exception:
        return [query]
