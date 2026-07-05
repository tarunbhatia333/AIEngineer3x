from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import config, ingest, state
from app.routers import collections, ingest as ingest_router, query


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await ingest.ingest_default()
        state.set_active(config.DEFAULT_COLLECTION)
    except Exception as exc:  # noqa: BLE001 - startup should not crash the server
        print(f"[startup] Default ingestion skipped: {exc}")
    yield


app = FastAPI(title="RAG Explorer API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest_router.router)
app.include_router(query.router)
app.include_router(collections.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=config.PORT, reload=True)
