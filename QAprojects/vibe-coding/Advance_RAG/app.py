"""Flask app tying the two pipelines together:

  Stage 1 (Ingest): /upload -> /api/upload (preview) -> /api/ingest/stream (SSE)
  Stage 2 (Chat):   /chat   -> /api/chat/stream (SSE)
  Explorer:         /chunks -> /api/chunks (paginated JSON)

Upload and Ingest live on one page and one request each: the browser holds
the File object in memory and resends it (as multipart) to /api/ingest/stream
once columns are chosen, so nothing about running the pipeline depends on
server-side state surviving between requests — required on Vercel, where a
"cold start" may be a completely fresh process with no memory of the request
before it. STATE below is kept anyway, but only for cosmetic, best-effort
pointers (last filename shown, last chat citations) that are fine to lose on
a cold start; the actual chunks/vectors always live in the vector store.
"""
from __future__ import annotations

import json
import os

from flask import Flask, Response, jsonify, redirect, render_template, request, stream_with_context

import config
from embeddings import get_embedder
from generation import detect_mode, stream_answer
from ingest import ingest_pipeline, read_upload
from query_rewrite import rewrite_query
from vectorstore import collection_info, hybrid_search_multi, list_all_chunks, rerank

app = Flask(__name__)

STATE = {
    "filename": None,
    "last_citations": [],  # chunk ids used in the most recent chat answer
}


def sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _validated_upload():
    """Shared by /api/upload and /api/ingest/stream: pulls `file` out of the
    request, checks its extension, and returns (FileStorage, error_response)."""
    file = request.files.get("file")
    if not file or not file.filename:
        return None, (jsonify({"error": "No file provided"}), 400)
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in (".csv", ".xlsx", ".xls"):
        return None, (jsonify({"error": "Only .csv, .xlsx, .xls are supported"}), 400)
    return file, None


# --- pages -------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("upload.html", filename=STATE["filename"], model_profile=config.MODEL_PROFILE)


@app.route("/upload")
def upload_page():
    return render_template("upload.html", filename=STATE["filename"], model_profile=config.MODEL_PROFILE)


@app.route("/ingest")
def ingest_page_redirect():
    # Upload and Ingest are one page/flow now (see module docstring) — this
    # route stays only so old links/bookmarks still land somewhere sensible.
    return redirect("/upload")


@app.route("/chunks")
def chunks_page():
    return render_template("chunks.html", model_profile=config.MODEL_PROFILE)


@app.route("/chat")
def chat_page():
    return render_template("chat.html", model_profile=config.MODEL_PROFILE, collection=collection_info())


# --- upload API (preview only, stateless) ---------------------------------------

@app.route("/api/upload", methods=["POST"])
def api_upload():
    file, error = _validated_upload()
    if error:
        return error

    try:
        df = read_upload(file)
    except Exception as exc:
        return jsonify({"error": f"Could not parse file: {exc}"}), 400

    STATE["filename"] = file.filename

    head = df.head(5).fillna("").astype(str).to_dict(orient="records")
    dtypes = {col: str(dtype) for col, dtype in df.dtypes.items()}

    return jsonify({
        "filename": file.filename,
        "rows": len(df),
        "columns": list(df.columns),
        "dtypes": dtypes,
        "head": head,
    })


# --- ingest API (SSE) ------------------------------------------------------------
# Takes the file again (multipart) rather than trusting a previous request's
# server-side state — see module docstring.

@app.route("/api/ingest/stream", methods=["POST"])
def api_ingest_stream():
    file, error = _validated_upload()
    if error:
        return error

    text_cols = [c for c in request.form.get("text_cols", "").split(",") if c]
    meta_cols = [c for c in request.form.get("meta_cols", "").split(",") if c]
    if not text_cols:
        return jsonify({"error": "Select at least one text column"}), 400

    try:
        df = read_upload(file)
    except Exception as exc:
        return jsonify({"error": f"Could not parse file: {exc}"}), 400

    def generate():
        try:
            for event in ingest_pipeline(df, text_cols, meta_cols, reset=True):
                yield sse(event["stage"], event["data"])
            yield sse("done", {})
        except Exception as exc:
            yield sse("error", {"message": str(exc)})

    return Response(stream_with_context(generate()), mimetype="text/event-stream")


# --- chunk explorer API ---------------------------------------------------------

@app.route("/api/chunks")
def api_chunks():
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 50))
    search = request.args.get("search", "").strip().lower()
    priority = request.args.get("priority", "").strip()
    module = request.args.get("module", "").strip()
    jira_id = request.args.get("jira_id", "").strip()

    chunks = list_all_chunks()

    if search:
        chunks = [c for c in chunks if search in c["text"].lower()]
    if priority:
        chunks = [c for c in chunks if str(c["metadata"].get("priority", "")).lower() == priority.lower()]
    if module:
        chunks = [c for c in chunks if str(c["metadata"].get("module", "")).lower() == module.lower()]
    if jira_id:
        chunks = [c for c in chunks if jira_id.lower() in str(c["metadata"].get("jira_id", "")).lower()]

    total = len(chunks)
    start = (page - 1) * page_size
    page_chunks = chunks[start:start + page_size]

    return jsonify({
        "total": total,
        "page": page,
        "page_size": page_size,
        "chunks": page_chunks,
        "last_citations": STATE["last_citations"],
    })


# --- chat API (SSE) --------------------------------------------------------------

@app.route("/api/chat/stream", methods=["POST"])
def api_chat_stream():
    body = request.get_json(force=True)
    query = (body.get("query") or "").strip()
    if not query:
        return jsonify({"error": "Empty query"}), 400

    def generate():
        try:
            rewrites = rewrite_query(query)
            yield sse("rewrite", {"queries": rewrites})

            embedder = get_embedder()
            vectors = embedder.encode(rewrites)
            search = hybrid_search_multi(rewrites, vectors, config.TOP_N_HYBRID)
            yield sse("retrieve", {
                "dense": search["dense"],
                "sparse": search["sparse"],
                "fused": search["fused"],
            })

            reranked = rerank(query, list(search["fused"]), top_k=config.TOP_K_RERANK)
            yield sse("rerank", {"chunks": reranked})

            STATE["last_citations"] = [c["id"] for c in reranked]

            mode = detect_mode(query)
            yield sse("mode", {"mode": mode})

            answer = ""
            for delta in stream_answer(query, reranked, mode=mode):
                answer += delta
                yield sse("token", {"delta": delta})

            yield sse("done", {"answer": answer, "citations": STATE["last_citations"]})
        except Exception as exc:
            yield sse("error", {"message": str(exc)})

    return Response(stream_with_context(generate()), mimetype="text/event-stream")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=config.PORT, debug=True, threaded=True)
