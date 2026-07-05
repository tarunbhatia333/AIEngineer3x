import re
import time

from fastapi import APIRouter, File, HTTPException, UploadFile

from .. import config, ingest, state
from ..embeddings import EmbeddingError
from ..schemas import IngestResult
from ..vectorstore import VectorStoreError

router = APIRouter(prefix="/api/ingest", tags=["ingest"])


def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


@router.post("/default", response_model=IngestResult)
async def reingest_default():
    try:
        count = await ingest.ingest_default(force=True)
    except (EmbeddingError, VectorStoreError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if count == 0:
        raise HTTPException(
            status_code=404,
            detail=f"Default PDF not found at data/{config.DEFAULT_PDF_NAME}",
        )
    return IngestResult(collection=config.DEFAULT_COLLECTION, source=config.DEFAULT_PDF_NAME, chunk_count=count)


@router.post("/upload", response_model=IngestResult)
async def upload_and_ingest(file: UploadFile = File(...)):
    allowed = (".pdf", ".txt", ".md")
    if not file.filename.lower().endswith(allowed):
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed: {allowed}")

    dest_path = config.UPLOADS_DIR / file.filename
    contents = await file.read()
    with open(dest_path, "wb") as f:
        f.write(contents)

    collection_name = f"{config.UPLOAD_COLLECTION_PREFIX}-{_slugify(file.filename)}-{int(time.time())}"
    try:
        count = await ingest.ingest_file(str(dest_path), file.filename, collection_name, file.filename)
    except (EmbeddingError, VectorStoreError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    if count == 0:
        raise HTTPException(status_code=422, detail="No extractable text found in the uploaded file.")

    state.set_active(collection_name)
    return IngestResult(collection=collection_name, source=file.filename, chunk_count=count)
