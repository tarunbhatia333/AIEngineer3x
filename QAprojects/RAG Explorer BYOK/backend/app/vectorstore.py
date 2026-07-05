import time

from . import config

_chroma_client = None
_pinecone_index_cache: dict[str, object] = {}


class VectorStoreError(RuntimeError):
    pass


# ---- Chroma (local) ----------------------------------------------------

def _chroma_client_get():
    global _chroma_client
    if _chroma_client is None:
        import chromadb
        from chromadb.config import Settings

        url = config.CHROMA_URL.replace("http://", "").replace("https://", "")
        host, _, port = url.partition(":")
        try:
            _chroma_client = chromadb.HttpClient(
                host=host or "localhost",
                port=int(port or "8010"),
                settings=Settings(anonymized_telemetry=False),
            )
        except Exception as exc:
            raise VectorStoreError(
                f"Could not reach ChromaDB at {config.CHROMA_URL}. Is `npm run chroma` running?"
            ) from exc
    return _chroma_client


def _chroma_collection(name: str):
    client = _chroma_client_get()
    return client.get_or_create_collection(name=name, metadata={"hnsw:space": "cosine"})


# ---- Pinecone (hosted, bring-your-own-key) --------------------------------

def _pinecone_index_get(api_key: str | None):
    if not api_key:
        raise VectorStoreError("Missing Pinecone API key. Add it on the Settings page.")
    if api_key in _pinecone_index_cache:
        return _pinecone_index_cache[api_key]

    from pinecone import Pinecone, ServerlessSpec

    try:
        pc = Pinecone(api_key=api_key)
        existing = [idx["name"] for idx in pc.list_indexes()]
        if config.PINECONE_INDEX not in existing:
            pc.create_index(
                name=config.PINECONE_INDEX,
                dimension=config.OPENAI_EMBED_DIMENSIONS,
                metric="cosine",
                spec=ServerlessSpec(cloud=config.PINECONE_CLOUD, region=config.PINECONE_REGION),
            )
            while not pc.describe_index(config.PINECONE_INDEX).status["ready"]:
                time.sleep(1)
        index = pc.Index(config.PINECONE_INDEX)
    except Exception as exc:
        raise VectorStoreError(f"Pinecone request failed: {exc}") from exc

    _pinecone_index_cache[api_key] = index
    return index


# ---- Provider-agnostic API ------------------------------------------------

def list_collections(api_key: str | None = None) -> list[str]:
    if config.VECTORSTORE_PROVIDER == "pinecone":
        stats = _pinecone_index_get(api_key).describe_index_stats()
        return list(stats.get("namespaces", {}).keys())
    return [c.name for c in _chroma_client_get().list_collections()]


def collection_count(name: str, api_key: str | None = None) -> int:
    if config.VECTORSTORE_PROVIDER == "pinecone":
        stats = _pinecone_index_get(api_key).describe_index_stats()
        return stats.get("namespaces", {}).get(name, {}).get("vector_count", 0)
    return _chroma_collection(name).count()


def reset_collection(name: str, api_key: str | None = None):
    """Clear any existing vectors so a fresh ingest starts empty."""
    if config.VECTORSTORE_PROVIDER == "pinecone":
        try:
            _pinecone_index_get(api_key).delete(delete_all=True, namespace=name)
        except VectorStoreError:
            raise
        except Exception:
            pass  # namespace didn't exist yet
        return
    client = _chroma_client_get()
    try:
        client.delete_collection(name=name)
    except Exception:
        pass
    _chroma_collection(name)


def delete_collection(name: str, api_key: str | None = None):
    if config.VECTORSTORE_PROVIDER == "pinecone":
        try:
            _pinecone_index_get(api_key).delete(delete_all=True, namespace=name)
        except VectorStoreError:
            raise
        except Exception:
            pass
        return
    try:
        _chroma_client_get().delete_collection(name=name)
    except Exception:
        pass


def add_chunks(collection_name: str, ids, embeddings, documents, metadatas, api_key: str | None = None):
    if config.VECTORSTORE_PROVIDER == "pinecone":
        vectors = [
            {"id": id_, "values": emb, "metadata": {**meta, "text": doc}}
            for id_, emb, doc, meta in zip(ids, embeddings, documents, metadatas)
        ]
        _pinecone_index_get(api_key).upsert(vectors=vectors, namespace=collection_name)
        return
    _chroma_collection(collection_name).add(
        ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas
    )


def query(collection_name: str, embedding: list[float], top_k: int, api_key: str | None = None) -> list[dict]:
    """Returns a flat list of {text, source, page, index, score} dicts."""
    if config.VECTORSTORE_PROVIDER == "pinecone":
        result = _pinecone_index_get(api_key).query(
            vector=embedding, top_k=top_k, namespace=collection_name, include_metadata=True
        )
        return [
            {
                "text": match["metadata"].get("text", ""),
                "source": match["metadata"].get("source", "unknown"),
                "page": match["metadata"].get("page", 0),
                "index": match["metadata"].get("index", 0),
                "score": round(match["score"], 4),
            }
            for match in result.get("matches", [])
        ]

    collection = _chroma_collection(collection_name)
    if collection.count() == 0:
        return []
    raw = collection.query(query_embeddings=[embedding], n_results=min(top_k, collection.count()))
    chunks = []
    for doc, meta, dist in zip(raw["documents"][0], raw["metadatas"][0], raw["distances"][0]):
        chunks.append(
            {
                "text": doc,
                "source": meta.get("source", "unknown"),
                "page": meta.get("page", 0),
                "index": meta.get("index", 0),
                "score": round(1 - dist, 4),
            }
        )
    return chunks
