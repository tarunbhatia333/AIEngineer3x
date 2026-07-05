# RAG Explorer

A full-stack RAG (Retrieval-Augmented Generation) explorer that visually walks through
the entire pipeline — **PDF/Upload → Chunking → Embedding → Vector Storage →
Retrieval → LLM Answer**.

- **Frontend:** React + Vite
- **Backend:** Python FastAPI
- **LLM:** Groq (`openai/gpt-oss-120b`)

Ships with two interchangeable backends for embeddings + vector storage, picked
automatically based on environment (or overridden via env vars):

| | Local dev (default) | Vercel / production (default) |
|---|---|---|
| Embeddings | `nomic-embed-text` via local Ollama | OpenAI `text-embedding-3-small` |
| Vector store | ChromaDB (local server, persists to `./chroma-data`) | Pinecone (serverless index, auto-created) |

This project started as a strictly local-first app (see `prompt/prompt.md`); the
Ollama/Chroma path still works exactly as before for local dev. The OpenAI/Pinecone
path was added so it can also run as a real deployment on Vercel, where a local
Ollama process and a local Chroma server aren't reachable.

## Requirements

- Python 3.10+
- Node.js 18+
- [Ollama](https://ollama.com) installed locally
- A free [Groq API key](https://console.groq.com/keys)

## Setup

### 1. Ollama (embeddings)

```bash
ollama pull nomic-embed-text
ollama serve   # skip if it's already running
```

### 2. Backend (FastAPI) — installs ChromaDB's CLI too

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate         # Windows (use `source .venv/bin/activate` on macOS/Linux)
pip install -r requirements.txt
copy .env.example .env         # Windows (use `cp` on macOS/Linux)
# edit .env and set GROQ_API_KEY
uvicorn main:app --reload --port 8787
```

### 3. ChromaDB (vector store)

From the project root (in a separate terminal — the `chroma` CLI comes from the
backend's virtualenv you just created):

```bash
npm run chroma
```

This starts a local Chroma server on `http://localhost:8010`, persisting to `./chroma-data`.
Start this **before** the backend, since the backend connects to it on startup.

On startup, the backend automatically ingests the default PDF at
`data/Product_Requirements_Document_VWO.pdf` into the `default` Chroma collection.

### 4. Frontend (React)

```bash
cd frontend
npm install
npm run dev
```

Open the printed URL (default `http://localhost:5173`).

## Using it

1. **Default doc** — already ingested on backend startup; just start asking questions.
2. **Upload your own** — drag a `.pdf`, `.txt`, or `.md` file onto the "Knowledge Base"
   panel. It's saved to `uploads/`, chunked, embedded, and stored in its own Chroma
   collection. The uploaded doc becomes the active knowledge base automatically —
   switch back to the default (or between multiple uploads) with the **Use** button.
3. **Ask a question** — type it into the chat box. The app embeds your question,
   retrieves the top 4 (`TOP_K`) most relevant chunks from the active collection
   (shown with similarity score + source/page), then sends them to Groq for the
   final answer. The pipeline stepper at the top animates through each stage as it runs.
4. **Reset** — delete an uploaded collection with the ✕ button, or re-ingest the
   default PDF at any time.

## Deploying to Vercel

The frontend (static build) and backend (a single Python serverless function at
`api/index.py`) deploy together as one Vercel project — `vercel.json` builds the
Vite app and rewrites `/api/*` to the Python function, so they share an origin
(no CORS to configure).

1. Set these **Environment Variables** in the Vercel project (Settings → Environment Variables):
   - `GROQ_API_KEY`
   - `OPENAI_API_KEY`
   - `PINECONE_API_KEY`
   - (optional) `PINECONE_INDEX`, `PINECONE_CLOUD`, `PINECONE_REGION` — defaults are `rag-explorer` / `aws` / `us-east-1`.
   - Vercel sets `VERCEL=1` automatically, which is what switches the app to the
     OpenAI/Pinecone providers — you don't need to set `EMBEDDINGS_PROVIDER` /
     `VECTORSTORE_PROVIDER` yourself.
2. Deploy from the project root (`RAG Explorer/`):
   ```bash
   npx vercel --prod
   ```
   The first deploy creates the Pinecone index automatically (dimension 1536,
   cosine metric) if it doesn't exist yet.
3. On first request, the backend auto-ingests the default PDF into Pinecone (skipped
   on subsequent cold starts once it's already populated — see `ingest_default()`
   in `backend/app/ingest.py`).

Uploads on Vercel are processed in a temp directory scoped to that invocation —
they're chunked/embedded/stored in Pinecone immediately, not kept as persistent files
(unlike local dev, where they're saved under `uploads/`).

## Configuration

All runtime config lives in `backend/.env` (copy from `backend/.env.example`).
For local dev, only `GROQ_API_KEY` is required — everything else has a sensible default:

| Variable | Default | Purpose |
|---|---|---|
| `GROQ_API_KEY` | *(required)* | Groq API key |
| `GROQ_MODEL` | `openai/gpt-oss-120b` | Groq chat model |
| `EMBEDDINGS_PROVIDER` | `ollama` locally, `openai` on Vercel | `ollama` or `openai` |
| `VECTORSTORE_PROVIDER` | `chroma` locally, `pinecone` on Vercel | `chroma` or `pinecone` |
| `OLLAMA_URL` | `http://localhost:11434` | Local Ollama server |
| `EMBED_MODEL` | `nomic-embed-text` | Ollama embedding model |
| `CHROMA_URL` | `http://localhost:8010` | Local Chroma server |
| `OPENAI_API_KEY` | *(required on Vercel)* | OpenAI API key |
| `OPENAI_EMBED_MODEL` | `text-embedding-3-small` | OpenAI embedding model |
| `PINECONE_API_KEY` | *(required on Vercel)* | Pinecone API key |
| `PINECONE_INDEX` | `rag-explorer` | Pinecone index name (auto-created) |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | `1200` / `200` | Chunking parameters |
| `TOP_K` | `4` | Chunks retrieved per query |
| `PORT` | `8787` | Backend port (local dev only) |

## Project layout

```
RAG Explorer/
├── data/                 # default source PDF(s)
├── uploads/              # user-uploaded files (local dev only)
├── chroma-data/          # Chroma's persistent storage (gitignored, local dev only)
├── api/
│   └── index.py          # Vercel serverless entrypoint (imports backend/main.py's app)
├── vercel.json            # builds frontend + rewrites /api/* to api/index.py
├── requirements.txt        # lean deps for the Vercel function (fastapi, pinecone, ...)
├── backend/
│   ├── main.py           # FastAPI app entrypoint
│   ├── requirements.txt  # full local-dev deps (adds chromadb, uvicorn)
│   └── app/
│       ├── config.py     # picks providers based on VERCEL env var
│       ├── chunking.py   # PDF/txt parsing + overlapping chunk splitting
│       ├── embeddings.py # Ollama (local) or OpenAI (cloud) embedding calls
│       ├── vectorstore.py# Chroma (local) or Pinecone (cloud) client wrapper
│       ├── llm.py        # Groq chat completion call
│       ├── ingest.py     # chunk → embed → store pipeline
│       ├── state.py      # active-collection tracking
│       └── routers/      # /api/ingest, /api/query, /api/collections
└── frontend/
    └── src/
        ├── App.jsx
        ├── api.js         # same-origin in prod, localhost:8787 in dev
        └── components/   # PipelineStepper, UploadPanel, ChatPanel, ...
```

## Troubleshooting

- **"Could not reach Ollama"** — make sure `ollama serve` is running and
  `ollama pull nomic-embed-text` has completed.
- **"Ollama returned no embedding"** — the embed model isn't pulled yet; run
  `ollama pull nomic-embed-text`.
- **Groq errors** — check `GROQ_API_KEY` is set in `backend/.env` and valid.
- **Empty retrieval / "No chunks found"** — ingest a document first (the default
  PDF ingests automatically on backend startup; check the backend console for errors).
- **"OPENAI_API_KEY is not set"** (Vercel) — set it in the project's Environment Variables.
- **"PINECONE_API_KEY is not set" or index errors** (Vercel) — set `PINECONE_API_KEY`;
  the index is created automatically on first use.
