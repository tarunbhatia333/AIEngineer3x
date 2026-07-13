"""Stage 2 final step: build a grounded prompt from reranked chunks and
stream the answer from Groq. Two auto-detected modes:

- "answer"   grounded Q&A over the retrieved test cases, cites [Chunk N]
- "generate" writes a new, structured test case using retrieved cases as
             style templates (triggered by phrases like "create a test case
             for JIRA VWO-1234")
"""
from __future__ import annotations

from groq import Groq

from config import GROQ_API_KEY, GROQ_GEN_MODEL

_client = None

_GENERATE_TRIGGERS = (
    "create a new test case", "create a test case", "generate a test case",
    "write a test case", "add a test case", "new test case for",
    "generate test case", "draft a test case",
)


def _get_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=GROQ_API_KEY)
    return _client


def detect_mode(query: str) -> str:
    q = query.lower()
    return "generate" if any(trigger in q for trigger in _GENERATE_TRIGGERS) else "answer"


def build_context(chunks: list[dict]) -> str:
    parts = []
    for i, c in enumerate(chunks, start=1):
        meta = c.get("metadata") or {}
        meta_str = ", ".join(f"{k}={v}" for k, v in meta.items() if v)
        parts.append(f"[Chunk {i}] ({meta_str})\n{c['text']}")
    return "\n\n".join(parts)


_ANSWER_SYSTEM = (
    "You are a QA knowledge assistant for The Testing Academy, answering questions "
    "about a VWO A/B-testing test-case suite using ONLY the provided context chunks. "
    "Cite every claim with its chunk marker, e.g. [Chunk 2]. "
    "If the context doesn't contain the answer, say so plainly instead of guessing."
)

_GENERATE_SYSTEM = (
    "You are a QA test-case author for The Testing Academy. Using the retrieved "
    "test cases below as style/format templates (not as facts to copy verbatim), "
    "write ONE new test case for the user's request. Always respond in exactly "
    "this structure:\n\n"
    "**Title:** ...\n**Preconditions:** ...\n**Steps:**\n1. ...\n2. ...\n"
    "**Expected Result:** ...\n**Priority:** ...\n**Tags:** ...\n\n"
    "Reference which retrieved chunks inspired the format with [Chunk N] markers."
)


def stream_answer(query: str, chunks: list[dict], mode: str | None = None):
    """Yields text deltas as they arrive from Groq."""
    mode = mode or detect_mode(query)
    system = _GENERATE_SYSTEM if mode == "generate" else _ANSWER_SYSTEM
    context = build_context(chunks)

    user_msg = f"Context:\n{context}\n\nRequest: {query}" if context else f"Request: {query}\n\n(No matching context was retrieved.)"

    stream = _get_client().chat.completions.create(
        model=GROQ_GEN_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.3,
        stream=True,
    )
    for event in stream:
        delta = event.choices[0].delta.content
        if delta:
            yield delta
