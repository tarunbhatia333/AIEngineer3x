# RAG Explorer (Local-First)

A full-stack RAG (Retrieval-Augmented Generation) explorer that visually walks through
the entire pipeline — **PDF/Upload → Chunking → Embedding → ChromaDB Storage →
Retrieval → LLM Answer** — running entirely on your machine.

- **Frontend:** React + Vite
- **Backend:** Python FastAPI
- **Vector DB:** ChromaDB (local, persistent to `./chroma-data`)
- **Embeddings:** `nomic-embed-text` via local Ollama
- **LLM:** Groq (`openai/gpt-oss-120b`)

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

## Configuration

All runtime config lives in `backend/.env` (copy from `backend/.env.example`).
Only `GROQ_API_KEY` is required — everything else has a sensible default:

| Variable | Default | Purpose |
|---|---|---|
| `GROQ_API_KEY` | *(required)* | Groq API key |
| `GROQ_MODEL` | `openai/gpt-oss-120b` | Groq chat model |
| `OLLAMA_URL` | `http://localhost:11434` | Local Ollama server |
| `EMBED_MODEL` | `nomic-embed-text` | Ollama embedding model |
| `CHROMA_URL` | `http://localhost:8010` | Local Chroma server |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | `1200` / `200` | Chunking parameters |
| `TOP_K` | `4` | Chunks retrieved per query |
| `PORT` | `8787` | Backend port |

## Project layout

```
RAG Explorer/
├── data/                 # default source PDF(s)
├── uploads/              # user-uploaded files
├── chroma-data/          # Chroma's persistent storage (gitignored)
├── backend/
│   ├── main.py           # FastAPI app entrypoint
│   └── app/
│       ├── config.py
│       ├── chunking.py   # PDF/txt parsing + overlapping chunk splitting
│       ├── embeddings.py # Ollama embedding calls
│       ├── vectorstore.py# Chroma client wrapper
│       ├── llm.py        # Groq chat completion call
│       ├── ingest.py     # chunk → embed → store pipeline
│       ├── state.py      # active-collection tracking
│       └── routers/      # /api/ingest, /api/query, /api/collections
└── frontend/
    └── src/
        ├── App.jsx
        ├── api.js
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
