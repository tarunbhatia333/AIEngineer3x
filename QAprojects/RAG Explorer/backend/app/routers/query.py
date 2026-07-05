from fastapi import APIRouter, HTTPException

from .. import config, vectorstore
from ..embeddings import EmbeddingError, embed_query
from ..llm import LLMError, generate_answer
from ..schemas import QueryRequest, QueryResponse, RetrievedChunk

router = APIRouter(prefix="/api/query", tags=["query"])


@router.post("", response_model=QueryResponse)
async def run_query(req: QueryRequest):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    top_k = req.top_k or config.TOP_K

    try:
        query_embedding = await embed_query(req.question)
    except EmbeddingError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    result = vectorstore.query(req.collection, query_embedding, top_k)

    chunks: list[RetrievedChunk] = []
    documents = result["documents"][0]
    metadatas = result["metadatas"][0]
    distances = result["distances"][0]
    for doc, meta, dist in zip(documents, metadatas, distances):
        chunks.append(
            RetrievedChunk(
                text=doc,
                source=meta.get("source", "unknown"),
                page=meta.get("page", 0),
                index=meta.get("index", 0),
                score=round(1 - dist, 4),
            )
        )

    if not chunks:
        raise HTTPException(
            status_code=404,
            detail="No chunks found in this collection. Ingest a document first.",
        )

    try:
        answer = await generate_answer(req.question, [c.model_dump() for c in chunks])
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return QueryResponse(chunks=chunks, answer=answer)
