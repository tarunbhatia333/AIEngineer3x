import chromadb
from chromadb.config import Settings

from . import config

_client = None


def get_client():
    global _client
    if _client is None:
        url = config.CHROMA_URL.replace("http://", "").replace("https://", "")
        host, _, port = url.partition(":")
        _client = chromadb.HttpClient(
            host=host or "localhost",
            port=int(port or "8000"),
            settings=Settings(anonymized_telemetry=False),
        )
    return _client


def get_collection(name: str):
    client = get_client()
    return client.get_or_create_collection(name=name, metadata={"hnsw:space": "cosine"})


def reset_collection(name: str):
    client = get_client()
    try:
        client.delete_collection(name=name)
    except Exception:
        pass
    return get_collection(name)


def list_collections() -> list[str]:
    client = get_client()
    return [c.name for c in client.list_collections()]


def add_chunks(collection_name: str, ids, embeddings, documents, metadatas):
    collection = get_collection(collection_name)
    collection.add(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)


def query(collection_name: str, embedding: list[float], top_k: int):
    collection = get_collection(collection_name)
    if collection.count() == 0:
        return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}
    return collection.query(query_embeddings=[embedding], n_results=min(top_k, collection.count()))
