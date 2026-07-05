from pydantic import BaseModel


class IngestResult(BaseModel):
    collection: str
    source: str
    chunk_count: int


class RetrievedChunk(BaseModel):
    text: str
    source: str
    page: int
    index: int
    score: float


class QueryRequest(BaseModel):
    question: str
    collection: str = "default"
    top_k: int | None = None


class QueryResponse(BaseModel):
    chunks: list[RetrievedChunk]
    answer: str


class CollectionInfo(BaseModel):
    name: str
    label: str
    chunk_count: int
    is_active: bool


class CollectionsResponse(BaseModel):
    collections: list[CollectionInfo]
    active: str
