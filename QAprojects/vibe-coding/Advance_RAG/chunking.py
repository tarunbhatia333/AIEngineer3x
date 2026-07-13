"""Stage 1 helpers: turn a dataframe into assembled docs, then into chunks.

1 row -> 1 doc. A doc becomes 1 chunk if it fits under CHUNK_SIZE, otherwise it
is split into overlapping windows (CHUNK_OVERLAP chars shared between
neighbours) so a cross-encoder / embedder never has to reason about a
truncated sentence at a chunk boundary.
"""
from __future__ import annotations

import pandas as pd

from config import CHUNK_SIZE, CHUNK_OVERLAP


def build_documents(df: pd.DataFrame, text_cols: list[str], meta_cols: list[str]) -> list[dict]:
    """One row -> one assembled document. `text` is the concatenation of the
    chosen text columns (label: value), `metadata` carries the chosen columns
    verbatim so they can be used as Chroma `where` filters later."""
    docs = []
    for i, row in df.iterrows():
        parts = []
        for col in text_cols:
            val = row.get(col)
            if pd.isna(val):
                continue
            parts.append(f"{col}: {val}")
        text = "\n".join(parts)

        metadata = {}
        for col in meta_cols:
            val = row.get(col)
            if pd.isna(val):
                val = ""
            metadata[col] = str(val)

        doc_id = str(row.get("id", i))
        docs.append({"doc_id": doc_id, "text": text, "metadata": metadata})
    return docs


def _split_with_overlap(text: str, size: int, overlap: int) -> list[str]:
    if len(text) <= size:
        return [text]
    windows = []
    start = 0
    step = max(size - overlap, 1)
    while start < len(text):
        end = min(start + size, len(text))
        windows.append(text[start:end])
        if end == len(text):
            break
        start += step
    return windows


def chunk_documents(docs: list[dict], chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[dict]:
    """Docs -> chunks. Each chunk dict: id, doc_id, text, metadata, char_len."""
    chunks = []
    for doc in docs:
        windows = _split_with_overlap(doc["text"], chunk_size, overlap)
        for idx, window in enumerate(windows):
            chunk_id = doc["doc_id"] if len(windows) == 1 else f"{doc['doc_id']}::chunk{idx}"
            chunks.append({
                "id": chunk_id,
                "doc_id": doc["doc_id"],
                "text": window,
                "metadata": dict(doc["metadata"]),
                "char_len": len(window),
            })
    return chunks


def chunk_stats(chunks: list[dict]) -> dict:
    """Stats + a coarse histogram for the /ingest UI's Chunk stage card."""
    if not chunks:
        return {"total": 0, "avg_chars": 0, "min_chars": 0, "max_chars": 0, "histogram": []}

    lengths = [c["char_len"] for c in chunks]
    bucket_size = 200
    buckets: dict[int, int] = {}
    for length in lengths:
        bucket = (length // bucket_size) * bucket_size
        buckets[bucket] = buckets.get(bucket, 0) + 1
    histogram = [{"range": f"{b}-{b + bucket_size}", "count": c} for b, c in sorted(buckets.items())]

    return {
        "total": len(chunks),
        "avg_chars": round(sum(lengths) / len(lengths), 1),
        "min_chars": min(lengths),
        "max_chars": max(lengths),
        "histogram": histogram,
    }
