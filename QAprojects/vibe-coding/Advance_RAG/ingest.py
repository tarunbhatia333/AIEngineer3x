"""Stage 1 (Ingest) pipeline: Read -> Build docs -> Chunk -> Embed -> Index.

`ingest_pipeline()` is a generator so app.py can stream each stage over SSE;
`main()` below drives the same generator from the CLI, per the README:

    python ingest.py data/test_cases.csv --text-cols title,steps,expected,tags \\
        --meta-cols id,jira_id,priority,module
"""
from __future__ import annotations

import argparse
import os

import pandas as pd

from chunking import build_documents, chunk_documents, chunk_stats
from config import VECTORSTORE_PROVIDER
from embeddings import get_embedder
from vectorstore import get_collection, get_hashing_encoder, get_sparse_index, upsert_chunks, collection_info

EMBED_BATCH = 32


def read_input(path: str) -> pd.DataFrame:
    ext = os.path.splitext(path)[1].lower()
    if ext in (".xlsx", ".xls"):
        return pd.read_excel(path)
    return pd.read_csv(path)


def read_upload(file_storage) -> pd.DataFrame:
    """Parses an uploaded file straight from memory — no disk write, so this
    works the same whether the filesystem is writable (local dev) or not
    (Vercel's read-only function filesystem)."""
    ext = os.path.splitext(file_storage.filename)[1].lower()
    if ext in (".xlsx", ".xls"):
        return pd.read_excel(file_storage.stream)
    return pd.read_csv(file_storage.stream)


def _sparse_preview_tokens(text: str, top_k: int = 5) -> dict:
    """Token -> weight preview for the Embed-stage UI card, using whichever
    sparse encoder is actually in play for the active VECTORSTORE_PROVIDER."""
    if VECTORSTORE_PROVIDER == "pinecone":
        return get_hashing_encoder().top_tokens(text, top_k=top_k)
    return get_sparse_index().weighted_vector(text, top_k=top_k)


def ingest_pipeline(df: pd.DataFrame, text_cols: list[str], meta_cols: list[str], reset: bool = True):
    """Yields {"stage": ..., "data": ...} events for each pipeline stage."""

    # Stage: Read
    yield {"stage": "read", "data": {
        "rows": len(df),
        "columns": list(df.columns),
    }}

    # Stage: Build docs
    docs = build_documents(df, text_cols, meta_cols)
    yield {"stage": "build_docs", "data": {
        "doc_count": len(docs),
        "text_cols": text_cols,
        "meta_cols": meta_cols,
        "sample": docs[0]["text"][:400] if docs else "",
    }}

    # Stage: Chunk
    chunks = chunk_documents(docs)
    stats = chunk_stats(chunks)
    overlap_preview = None
    for c in chunks:
        if "::chunk" in c["id"]:
            overlap_preview = c
            break
    yield {"stage": "chunk", "data": {
        **stats,
        "samples": [
            {"id": c["id"], "text": c["text"][:300], "char_len": c["char_len"]}
            for c in chunks[:3]
        ],
        "overlap_sample": (
            {"id": overlap_preview["id"], "text": overlap_preview["text"][:300]}
            if overlap_preview else None
        ),
    }}

    if reset:
        get_collection(reset=True)
    embedder = get_embedder()

    # Stage: Embed (+ index incrementally per batch)
    total = len(chunks)
    done = 0
    preview_sent = False
    for start in range(0, total, EMBED_BATCH):
        batch = chunks[start:start + EMBED_BATCH]
        vectors = embedder.encode([c["text"] for c in batch])
        upsert_chunks(batch, vectors)
        done += len(batch)

        preview = None
        if not preview_sent:
            preview = {
                "dense_dims_shown": vectors[0][:8],
                "dense_total_dims": len(vectors[0]),
                "sparse_top5": _sparse_preview_tokens(batch[0]["text"], top_k=5),
                "example_chunk_id": batch[0]["id"],
            }
            preview_sent = True

        yield {"stage": "embed", "data": {
            "done": done,
            "total": total,
            "progress_pct": round(done / total * 100, 1) if total else 100,
            **({"preview": preview} if preview else {}),
        }}

    # Stage: Index
    yield {"stage": "index", "data": collection_info()}


def main():
    parser = argparse.ArgumentParser(description="Ingest a CSV/XLSX of VWO test cases into the hybrid store.")
    parser.add_argument("path", help="Path to .csv/.xlsx/.xls file")
    parser.add_argument("--text-cols", required=True, help="Comma-separated columns to embed")
    parser.add_argument("--meta-cols", required=True, help="Comma-separated columns to keep as filterable payload")
    parser.add_argument("--no-reset", action="store_true", help="Append instead of recreating the collection")
    args = parser.parse_args()

    df = read_input(args.path)
    text_cols = [c.strip() for c in args.text_cols.split(",")]
    meta_cols = [c.strip() for c in args.meta_cols.split(",")]

    for event in ingest_pipeline(df, text_cols, meta_cols, reset=not args.no_reset):
        stage, data = event["stage"], event["data"]
        if stage == "embed":
            print(f"\r[embed] {data['done']}/{data['total']} ({data['progress_pct']}%)", end="", flush=True)
            if data["done"] == data["total"]:
                print()
        else:
            print(f"[{stage}] {data}")


if __name__ == "__main__":
    main()
