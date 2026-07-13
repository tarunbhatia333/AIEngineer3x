"""Dense embedding backend, swappable via config.MODEL_PROFILE.

Sparse vectors are NOT produced here: because we're on Chromadb (no native
sparse vector type), sparse retrieval is handled uniformly by
sparse_index.SparseIndex (a hand-rolled TF-IDF inverted index) regardless of
MODEL_PROFILE. Only the dense encoder and the reranker (see reranker.py)
change between "light" and "full". This module gives both profiles the same
`.encode(texts) -> list[list[float]]` interface so the rest of the app never
has to know which one is active.
"""
from __future__ import annotations

from config import (
    EMBEDDINGS_PROVIDER,
    MODEL_PROFILE,
    LIGHT_DENSE_MODEL,
    FULL_DENSE_MODEL,
    OPENAI_API_KEY,
    OPENAI_EMBED_MODEL,
)

_embedder = None


class LightDenseEmbedder:
    """BAAI/bge-small-en-v1.5 via sentence-transformers. ~130MB, CPU-friendly."""

    name = LIGHT_DENSE_MODEL

    def __init__(self):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(self.name)

    def encode(self, texts: list[str]) -> list[list[float]]:
        vecs = self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return [v.tolist() for v in vecs]


class FullDenseEmbedder:
    """BAAI/bge-m3 via FlagEmbedding. ~2.3GB, matches the spec exactly.

    Requires `pip install FlagEmbedding torch` (see requirements.txt). Only
    loaded when MODEL_PROFILE=full so the default (light) install stays small.
    """

    name = FULL_DENSE_MODEL

    def __init__(self):
        from FlagEmbedding import BGEM3FlagModel
        self.model = BGEM3FlagModel(self.name, use_fp16=True)

    def encode(self, texts: list[str]) -> list[list[float]]:
        out = self.model.encode(texts, return_dense=True, return_sparse=False, return_colbert_vecs=False)
        return [v.tolist() if hasattr(v, "tolist") else list(v) for v in out["dense_vecs"]]


class OpenAIDenseEmbedder:
    """Hosted dense embeddings, used on Vercel where local models can't run
    (no persistent disk to cache them on, and torch/sentence-transformers
    would blow the serverless function's size limit)."""

    name = OPENAI_EMBED_MODEL

    def __init__(self):
        from openai import OpenAI
        self.client = OpenAI(api_key=OPENAI_API_KEY)

    def encode(self, texts: list[str]) -> list[list[float]]:
        resp = self.client.embeddings.create(model=self.name, input=texts)
        return [d.embedding for d in resp.data]


def get_embedder():
    global _embedder
    if _embedder is None:
        if EMBEDDINGS_PROVIDER == "openai":
            _embedder = OpenAIDenseEmbedder()
        elif MODEL_PROFILE == "full":
            _embedder = FullDenseEmbedder()
        else:
            _embedder = LightDenseEmbedder()
    return _embedder
