from fastapi import APIRouter, Depends, HTTPException

from .. import config, vectorstore
from ..embeddings import EmbeddingError, embed_query
from ..keys import ApiKeys, get_api_keys
from ..llm import LLMError, generate_answer
from ..schemas import QueryRequest, QueryResponse, RetrievedChunk
from ..vectorstore import VectorStoreError

router = APIRouter(prefix="/api/query", tags=["query"])


@router.post("", response_model=QueryResponse)
async def run_query(req: QueryRequest, keys: ApiKeys = Depends(get_api_keys)):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    top_k = req.top_k or config.TOP_K

    try:
        query_embedding = await embed_query(req.question, api_key=keys.openai)
    except EmbeddingError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    try:
        results = vectorstore.query(req.collection, query_embedding, top_k, api_key=keys.pinecone)
    except VectorStoreError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    chunks = [RetrievedChunk(**r) for r in results]

    if not chunks:
        raise HTTPException(
            status_code=404,
            detail="No chunks found in this collection. Ingest a document first.",
        )

    try:
        answer = await generate_answer(req.question, [c.model_dump() for c in chunks], api_key=keys.groq)
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return QueryResponse(chunks=chunks, answer=answer)
