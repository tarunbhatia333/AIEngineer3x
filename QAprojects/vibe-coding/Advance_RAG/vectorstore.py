"""Hybrid vector store, branching on config.VECTORSTORE_PROVIDER:

- "chroma"   (local dev) dense HNSW search native to Chroma, paired with the
             hand-rolled TF-IDF SparseIndex living beside it on disk.
- "pinecone" (Vercel)    a single Pinecone index storing both dense values and
             hashing-trick sparse_values per vector (metric="dotproduct", the
             mode Pinecone requires for hybrid). Dense-only and sparse-only
             rankings are obtained as two separate queries against that same
             index — a real dense vector with no sparse_vector for the first,
             an all-zero dense vector with a real sparse_vector for the second
             (the zero vector contributes nothing to the dot product, isolating
             the sparse score) — so both providers hand the exact same
             (id, score) ranked-list shape to rrf_fuse() below.

rrf_fuse(), rerank(), and hybrid_search_multi() are provider-agnostic: they
only ever see (id, score) tuples and hydrated dicts, never Chroma/Pinecone
objects directly.
"""
from __future__ import annotations

from config import (
    VECTORSTORE_PROVIDER,
    CHROMA_DIR,
    COLLECTION_NAME,
    RRF_K,
    TOP_K_RERANK,
    PINECONE_API_KEY,
    PINECONE_INDEX,
    PINECONE_CLOUD,
    PINECONE_REGION,
    PINECONE_NAMESPACE,
    OPENAI_EMBED_DIMENSIONS,
)
from sparse_index import SparseIndex, HashingSparseEncoder
from reranker import get_reranker

_client = None
_sparse = None
_pinecone_index_cache = None
_hashing_encoder = None


def get_sparse_index() -> SparseIndex:
    global _sparse
    if _sparse is None:
        _sparse = SparseIndex()
    return _sparse


def get_hashing_encoder() -> HashingSparseEncoder:
    global _hashing_encoder
    if _hashing_encoder is None:
        _hashing_encoder = HashingSparseEncoder()
    return _hashing_encoder


# --- Chroma backend (local dev) ---------------------------------------------

def _chroma_client():
    global _client
    if _client is None:
        import chromadb
        _client = chromadb.PersistentClient(path=CHROMA_DIR)
    return _client


def _chroma_collection(reset: bool = False):
    client = _chroma_client()
    if reset:
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass
        get_sparse_index().reset()
    return client.get_or_create_collection(name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"})


# --- Pinecone backend (Vercel) -----------------------------------------------

def _pinecone_index():
    global _pinecone_index_cache
    if _pinecone_index_cache is None:
        from pinecone import Pinecone, ServerlessSpec
        pc = Pinecone(api_key=PINECONE_API_KEY)
        existing = [idx["name"] for idx in pc.list_indexes()]
        if PINECONE_INDEX not in existing:
            pc.create_index(
                name=PINECONE_INDEX,
                dimension=OPENAI_EMBED_DIMENSIONS,
                metric="dotproduct",
                spec=ServerlessSpec(cloud=PINECONE_CLOUD, region=PINECONE_REGION),
            )
        _pinecone_index_cache = pc.Index(PINECONE_INDEX)
    return _pinecone_index_cache


def _pinecone_reset():
    try:
        _pinecone_index().delete(delete_all=True, namespace=PINECONE_NAMESPACE)
    except Exception:
        pass  # namespace may not exist yet on a brand-new index


# --- provider-agnostic API ---------------------------------------------------

def get_collection(reset: bool = False):
    """Only meaningful for Chroma — kept for callers that still want a handle;
    on Pinecone this just performs the reset (if asked) and returns None."""
    if VECTORSTORE_PROVIDER == "pinecone":
        if reset:
            _pinecone_reset()
        return None
    return _chroma_collection(reset=reset)


def collection_info() -> dict:
    if VECTORSTORE_PROVIDER == "pinecone":
        stats = _pinecone_index().describe_index_stats()
        count = stats.get("namespaces", {}).get(PINECONE_NAMESPACE, {}).get("vector_count", 0)
        return {"name": PINECONE_NAMESPACE, "count": count, "path": f"pinecone:{PINECONE_INDEX}"}
    col = _chroma_collection()
    return {"name": COLLECTION_NAME, "count": col.count(), "path": CHROMA_DIR}


# --- indexing ----------------------------------------------------------------

def upsert_chunks(chunks: list[dict], dense_vectors: list[list[float]]):
    if VECTORSTORE_PROVIDER == "pinecone":
        encoder = get_hashing_encoder()
        vectors = []
        for c, dense in zip(chunks, dense_vectors):
            vectors.append({
                "id": c["id"],
                "values": dense,
                "sparse_values": encoder.vector(c["text"]),
                "metadata": {**(c["metadata"] or {}), "text": c["text"]},
            })
        index = _pinecone_index()
        batch = 100
        for i in range(0, len(vectors), batch):
            index.upsert(vectors=vectors[i:i + batch], namespace=PINECONE_NAMESPACE)
        return

    col = _chroma_collection()
    col.upsert(
        ids=[c["id"] for c in chunks],
        embeddings=dense_vectors,
        documents=[c["text"] for c in chunks],
        metadatas=[c["metadata"] or {"_": ""} for c in chunks],
    )
    get_sparse_index().add_documents([{"id": c["id"], "text": c["text"]} for c in chunks])


# --- retrieval -----------------------------------------------------------------

def dense_search(query_vector: list[float], top_n: int, where: dict | None = None) -> list[tuple[str, float]]:
    if VECTORSTORE_PROVIDER == "pinecone":
        result = _pinecone_index().query(
            vector=query_vector, top_k=top_n, namespace=PINECONE_NAMESPACE,
            filter=where or None, include_metadata=False,
        )
        return [(m["id"], float(m["score"])) for m in result.get("matches", [])]

    col = _chroma_collection()
    if col.count() == 0:
        return []
    result = col.query(query_embeddings=[query_vector], n_results=min(top_n, col.count()), where=where or None)
    ids = result["ids"][0]
    distances = result["distances"][0]
    return [(i, 1 - d) for i, d in zip(ids, distances)]  # cosine distance -> similarity


def sparse_search(query_text: str, top_n: int) -> list[tuple[str, float]]:
    if VECTORSTORE_PROVIDER == "pinecone":
        sparse_vec = get_hashing_encoder().vector(query_text)
        if not sparse_vec["indices"]:
            return []
        zero_vector = [0.0] * OPENAI_EMBED_DIMENSIONS
        result = _pinecone_index().query(
            vector=zero_vector, sparse_vector=sparse_vec, top_k=top_n,
            namespace=PINECONE_NAMESPACE, include_metadata=False,
        )
        return [(m["id"], float(m["score"])) for m in result.get("matches", [])]

    return get_sparse_index().search(query_text, top_n)


def rrf_fuse(*ranked_lists: list[tuple[str, float]], k: int = RRF_K) -> list[tuple[str, float]]:
    """Reciprocal Rank Fusion over any number of ranked (id, score) lists —
    used both for the simple dense+sparse case and for merging the extra
    ranked lists produced by each query rewrite. Provider-agnostic: it never
    looks at the score, only the rank position within each list."""
    scores: dict[str, float] = {}
    for ranked in ranked_lists:
        for rank, (chunk_id, _) in enumerate(ranked):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (k + rank + 1)
    return sorted(scores.items(), key=lambda kv: kv[1], reverse=True)


def fetch_by_ids(ids: list[str]) -> dict[str, dict]:
    """id -> {text, metadata}."""
    if not ids:
        return {}

    if VECTORSTORE_PROVIDER == "pinecone":
        index = _pinecone_index()
        out = {}
        batch = 100
        for i in range(0, len(ids), batch):
            result = index.fetch(ids=ids[i:i + batch], namespace=PINECONE_NAMESPACE)
            for vid, vec in result.get("vectors", {}).items():
                meta = dict(vec.get("metadata", {}))
                text = meta.pop("text", "")
                out[vid] = {"text": text, "metadata": meta}
        return out

    col = _chroma_collection()
    result = col.get(ids=ids, include=["documents", "metadatas"])
    return {
        i: {"text": doc, "metadata": meta}
        for i, doc, meta in zip(result["ids"], result["documents"], result["metadatas"])
    }


def _hydrate(ranked: list[tuple[str, float]], docs: dict[str, dict]) -> list[dict]:
    out = []
    for chunk_id, score in ranked:
        if chunk_id not in docs:
            continue
        out.append({"id": chunk_id, "score": round(float(score), 4), **docs[chunk_id]})
    return out


def hybrid_search_multi(query_texts: list[str], query_vectors: list[list[float]], top_n: int, where: dict | None = None) -> dict:
    """Runs dense + sparse search for EVERY query variant (original + rewrites)
    and RRF-fuses all of them together, so a rewrite that surfaces a chunk the
    original phrasing missed still boosts it into the final ranking.

    The 'dense'/'sparse' lists returned are for the *original* query only
    (query_texts[0]) — used purely for the chat UI's transparency panel —
    while 'fused' reflects the full multi-query fusion.
    """
    all_dense, all_sparse = [], []
    for qtext, qvec in zip(query_texts, query_vectors):
        all_dense.append(dense_search(qvec, top_n, where=where))
        all_sparse.append(sparse_search(qtext, top_n))

    fused = rrf_fuse(*all_dense, *all_sparse)[:top_n]

    all_ids = list({i for lst in (*all_dense, *all_sparse) for i, _ in lst})
    docs = fetch_by_ids(all_ids)

    return {
        "dense": _hydrate(all_dense[0], docs),
        "sparse": _hydrate(all_sparse[0], docs),
        "fused": _hydrate(fused, docs),
        "docs": docs,
    }


def rerank(query: str, candidates: list[dict], top_k: int = TOP_K_RERANK) -> list[dict]:
    """candidates: list of {id, text, score(fused), ...}. Returns top_k with a
    `rerank_score` added and `before_rank` preserved for the before/after
    table in the UI."""
    if not candidates:
        return []
    model = get_reranker()
    passages = [c["text"] for c in candidates]
    scores = model.score(query, passages)
    for c, s in zip(candidates, scores):
        c["rerank_score"] = round(float(s), 4)
    ranked = sorted(
        [dict(c, before_rank=i + 1) for i, c in enumerate(candidates)],
        key=lambda c: c["rerank_score"],
        reverse=True,
    )
    for after_rank, c in enumerate(ranked, start=1):
        c["after_rank"] = after_rank
    return ranked[:top_k]


# --- chunk explorer ------------------------------------------------------------

def list_all_chunks() -> list[dict]:
    if VECTORSTORE_PROVIDER == "pinecone":
        index = _pinecone_index()
        ids = []
        for page in index.list(namespace=PINECONE_NAMESPACE):
            ids.extend(item.id for item in page.vectors)
        docs = fetch_by_ids(ids)
        return [{"id": i, "text": d["text"], "metadata": d["metadata"]} for i, d in docs.items()]

    col = _chroma_collection()
    if col.count() == 0:
        return []
    result = col.get(include=["documents", "metadatas"])
    return [
        {"id": i, "text": doc, "metadata": meta}
        for i, doc, meta in zip(result["ids"], result["documents"], result["metadatas"])
    ]
