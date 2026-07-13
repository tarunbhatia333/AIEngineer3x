"""Cross-encoder reranker, swappable via config.MODEL_PROFILE.

Both profiles expose `.score(query, passages) -> list[float]` so the calling
code (vectorstore.rerank) is identical either way.
"""
from __future__ import annotations

import json

from config import (
    MODEL_PROFILE,
    RERANK_PROVIDER,
    LIGHT_RERANK_MODEL,
    FULL_RERANK_MODEL,
    GROQ_API_KEY,
    GROQ_RERANK_MODEL,
)

_reranker = None


class LightReranker:
    """cross-encoder/ms-marco-MiniLM-L-6-v2. ~90MB, CPU-friendly."""

    name = LIGHT_RERANK_MODEL

    def __init__(self):
        from sentence_transformers import CrossEncoder
        self.model = CrossEncoder(self.name)

    def score(self, query: str, passages: list[str]) -> list[float]:
        pairs = [[query, p] for p in passages]
        scores = self.model.predict(pairs)
        return [float(s) for s in scores]


class FullReranker:
    """BAAI/bge-reranker-v2-m3 via FlagEmbedding. ~570MB, matches the spec.

    Requires `pip install FlagEmbedding torch`. Only loaded when
    MODEL_PROFILE=full.
    """

    name = FULL_RERANK_MODEL

    def __init__(self):
        from FlagEmbedding import FlagReranker
        self.model = FlagReranker(self.name, use_fp16=True)

    def score(self, query: str, passages: list[str]) -> list[float]:
        pairs = [[query, p] for p in passages]
        scores = self.model.compute_score(pairs, normalize=True)
        if isinstance(scores, float):
            scores = [scores]
        return [float(s) for s in scores]


class LLMReranker:
    """No local cross-encoder on Vercel (too large for the function bundle,
    and a fresh cold start would re-download it every time anyway) — Groq
    scores each candidate against the query directly instead. Same interface,
    lower precision than a real cross-encoder, no extra API/vendor beyond the
    Groq key this build already needs for rewriting and generation."""

    name = GROQ_RERANK_MODEL

    def __init__(self):
        from groq import Groq
        self.client = Groq(api_key=GROQ_API_KEY)

    def score(self, query: str, passages: list[str]) -> list[float]:
        numbered = "\n\n".join(f"[{i + 1}] {p}" for i, p in enumerate(passages))
        prompt = (
            "Score how relevant each numbered passage is to the query, on a 0-100 scale "
            "(100 = directly answers the query, 0 = unrelated). "
            f"Query: {query}\n\nPassages:\n{numbered}\n\n"
            "Respond with ONLY a JSON array of numbers, one score per passage, in order. "
            "Example for 3 passages: [72, 5, 91]"
        )
        try:
            resp = self.client.chat.completions.create(
                model=self.name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=200,
            )
            content = resp.choices[0].message.content.strip()
            if content.startswith("```"):
                content = content.strip("`").split("\n", 1)[-1]
            scores = json.loads(content)
            if len(scores) == len(passages):
                return [float(s) for s in scores]
        except Exception:
            pass
        # fall back to preserving fused order (descending placeholder scores)
        return [float(len(passages) - i) for i in range(len(passages))]


def get_reranker():
    global _reranker
    if _reranker is None:
        if RERANK_PROVIDER == "llm":
            _reranker = LLMReranker()
        elif MODEL_PROFILE == "full":
            _reranker = FullReranker()
        else:
            _reranker = LightReranker()
    return _reranker
