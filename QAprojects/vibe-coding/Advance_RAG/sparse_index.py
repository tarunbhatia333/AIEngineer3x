"""Hand-rolled sparse (lexical) index.

Chroma's OSS build has no native sparse/BM25 vector type, so hybrid retrieval
here pairs Chroma's dense HNSW index with this small TF-IDF-style inverted
index. Conceptually it plays the same role bge-m3's "sparse vector" output
would play in the full-model profile: a token -> weight map per chunk, added
to the fused ranking via RRF. See config.MODEL_PROFILE to switch a real
neural sparse encoder in instead.
"""
from __future__ import annotations

import json
import math
import os
import re
from collections import defaultdict

import hashlib

from config import SPARSE_INDEX_PATH, SPARSE_HASH_BUCKETS

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "is", "are", "was", "were", "be",
    "to", "of", "in", "on", "for", "with", "as", "at", "by", "it", "this",
    "that", "from", "has", "have", "had", "not", "no", "so", "if", "then",
    "than", "into", "such", "can", "will", "should", "would", "each",
}


def tokenize(text: str) -> list[str]:
    tokens = _TOKEN_RE.findall(text.lower())
    return [t for t in tokens if len(t) > 1 and t not in _STOPWORDS]


class SparseIndex:
    def __init__(self, path: str = SPARSE_INDEX_PATH):
        self.path = path
        self.n_docs = 0
        self.doc_freq: dict[str, int] = defaultdict(int)
        # token -> {chunk_id: term_frequency}
        self.postings: dict[str, dict[str, int]] = defaultdict(dict)
        self._load()

    # --- persistence ---------------------------------------------------
    def _load(self):
        if not os.path.exists(self.path):
            return
        with open(self.path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        self.n_docs = raw.get("n_docs", 0)
        self.doc_freq = defaultdict(int, raw.get("doc_freq", {}))
        self.postings = defaultdict(dict, raw.get("postings", {}))

    def save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump({
                "n_docs": self.n_docs,
                "doc_freq": dict(self.doc_freq),
                "postings": dict(self.postings),
            }, f)

    def reset(self):
        self.n_docs = 0
        self.doc_freq = defaultdict(int)
        self.postings = defaultdict(dict)
        if os.path.exists(self.path):
            os.remove(self.path)

    # --- indexing --------------------------------------------------------
    def _idf(self, token: str) -> float:
        df = self.doc_freq.get(token, 0)
        return math.log((self.n_docs + 1) / (df + 1)) + 1.0

    def add_documents(self, chunks: list[dict]):
        """chunks: list of {id, text}. Updates doc_freq/postings and persists."""
        for chunk in chunks:
            tokens = tokenize(chunk["text"])
            if not tokens:
                continue
            tf: dict[str, int] = defaultdict(int)
            for tok in tokens:
                tf[tok] += 1
            for tok, count in tf.items():
                self.postings[tok][chunk["id"]] = count
                self.doc_freq[tok] += 1
            self.n_docs += 1
        self.save()

    def weighted_vector(self, text: str, top_k: int = 5) -> dict[str, float]:
        """token -> tf-idf weight for a single piece of text (used for both
        the Embed-stage 'sparse top-5 tokens' preview and query encoding)."""
        tokens = tokenize(text)
        tf: dict[str, int] = defaultdict(int)
        for tok in tokens:
            tf[tok] += 1
        weights = {tok: (1 + math.log(count)) * self._idf(tok) for tok, count in tf.items()}
        if top_k:
            return dict(sorted(weights.items(), key=lambda kv: kv[1], reverse=True)[:top_k])
        return weights

    def search(self, query_text: str, top_n: int) -> list[tuple[str, float]]:
        query_weights = self.weighted_vector(query_text, top_k=0)
        scores: dict[str, float] = defaultdict(float)
        for tok, q_weight in query_weights.items():
            doc_hits = self.postings.get(tok)
            if not doc_hits:
                continue
            idf = self._idf(tok)
            for chunk_id, tf in doc_hits.items():
                doc_weight = (1 + math.log(tf)) * idf
                scores[chunk_id] += q_weight * doc_weight
        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        return ranked[:top_n]


def _hash_token(token: str, buckets: int = SPARSE_HASH_BUCKETS) -> int:
    digest = hashlib.md5(token.encode("utf-8")).hexdigest()
    return int(digest, 16) % buckets


class HashingSparseEncoder:
    """Stateless stand-in for SparseIndex, used on Vercel.

    SparseIndex needs a persisted, growing vocabulary + document-frequency
    table on local disk — there's no such disk on serverless, and a fresh
    cold start can't rebuild it from nothing. The hashing trick sidesteps
    that: every token maps to a bucket via a pure function of the string
    (no lookup table required), so it produces a stable sparse vector with
    zero shared state between calls. What's lost versus SparseIndex is
    corpus-wide IDF weighting (no persisted doc-frequency counts to draw on)
    and a small amount of precision from hash collisions; term-frequency
    weighting alone still captures "this chunk repeats this exact token",
    which is the property sparse retrieval is here for.

    Output indices/weights are shaped for Pinecone's sparse_values format
    directly: {"indices": [...], "values": [...]}.
    """

    def __init__(self, buckets: int = SPARSE_HASH_BUCKETS):
        self.buckets = buckets

    def vector(self, text: str) -> dict:
        tokens = tokenize(text)
        if not tokens:
            return {"indices": [], "values": []}
        tf: dict[int, float] = defaultdict(float)
        counts: dict[str, int] = defaultdict(int)
        for tok in tokens:
            counts[tok] += 1
        for tok, count in counts.items():
            idx = _hash_token(tok, self.buckets)
            tf[idx] += 1 + math.log(count)
        indices = list(tf.keys())
        values = [tf[i] for i in indices]
        return {"indices": indices, "values": values}

    def top_tokens(self, text: str, top_k: int = 5) -> dict[str, float]:
        """Human-readable preview (token -> weight) for the Embed-stage UI —
        the hashed indices sent to Pinecone aren't reversible, so this keeps
        the token strings around purely for display."""
        tokens = tokenize(text)
        counts: dict[str, int] = defaultdict(int)
        for tok in tokens:
            counts[tok] += 1
        weights = {tok: 1 + math.log(count) for tok, count in counts.items()}
        return dict(sorted(weights.items(), key=lambda kv: kv[1], reverse=True)[:top_k])
