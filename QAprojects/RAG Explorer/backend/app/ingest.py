from . import config, state, vectorstore
from .chunking import chunk_file
from .embeddings import embed_texts


async def ingest_file(path: str, source: str, collection_name: str, label: str) -> int:
    vectorstore.reset_collection(collection_name)
    chunks = chunk_file(path, source)
    if not chunks:
        state.set_meta(collection_name, label, source)
        return 0

    texts = [c.text for c in chunks]
    embeddings = await embed_texts(texts)

    ids = [f"{collection_name}-{c.index}" for c in chunks]
    metadatas = [
        {"source": c.source, "page": c.page, "index": c.index} for c in chunks
    ]
    vectorstore.add_chunks(collection_name, ids, embeddings, texts, metadatas)
    state.set_meta(collection_name, label, source)
    return len(chunks)


async def ingest_default(force: bool = False) -> int:
    if not force and vectorstore.collection_count(config.DEFAULT_COLLECTION) > 0:
        state.set_meta(config.DEFAULT_COLLECTION, "Default (VWO PRD)", config.DEFAULT_PDF_NAME)
        return vectorstore.collection_count(config.DEFAULT_COLLECTION)

    path = config.DATA_DIR / config.DEFAULT_PDF_NAME
    if not path.exists():
        return 0
    return await ingest_file(
        str(path), config.DEFAULT_PDF_NAME, config.DEFAULT_COLLECTION, "Default (VWO PRD)"
    )
