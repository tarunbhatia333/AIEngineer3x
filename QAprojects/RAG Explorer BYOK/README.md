# RAG Explorer (Bring Your Own Key)

A full-stack RAG (Retrieval-Augmented Generation) explorer that visually walks through
the entire pipeline — **PDF/Upload → Chunking → Embedding → Vector Storage →
Retrieval → LLM Answer**.

**Live demo:** https://rag-explorer-byok.vercel.app

This is the **public, bring-your-own-key** variant of RAG Explorer: instead of the
server holding Groq/OpenAI/Pinecone credentials, each visitor enters their own API
keys on a **Settings** page. Keys are stored only in that visitor's browser
(`localStorage`) and sent directly to the backend as request headers on each call —
they are never saved, logged, or persisted on the server.

- **Frontend:** React + Vite
- **Backend:** Python FastAPI
- **LLM:** Groq (`openai/gpt-oss-120b`)

Ships with two interchangeable backends for embeddings + vector storage, picked
automatically based on environment (or overridden via env vars):

| | Local dev (default) | Vercel / production (default) |
|---|---|---|
| Embeddings | `nomic-embed-text` via local Ollama | OpenAI `text-embedding-3-small` |
| Vector store | ChromaDB (local server, persists to `./chroma-data`) | Pinecone (serverless index, auto-created) |

## What this is

RAG Explorer is a teaching/demo tool for **Retrieval-Augmented Generation** — it
answers questions about a document by first *retrieving* the most relevant passages
and then asking an LLM to *generate* an answer grounded in only those passages,
instead of the LLM answering from memory alone. The point of the app is to make
every step of that process **visible**, not hidden behind a single "Ask" button.

**What it does, in short:**
1. Takes a source document (a bundled default PDF, or one you upload — PDF/.txt/.md).
2. Splits it into overlapping text chunks and turns each chunk into a vector
   embedding (a list of numbers capturing its meaning).
3. Stores those embeddings in a vector database.
4. When you ask a question, it embeds the question the same way, finds the
   chunks whose embeddings are most similar (nearest-neighbor search), and shows
   you those chunks with their similarity scores *before* answering.
5. Sends the question + retrieved chunks to an LLM, which writes the final answer
   using only that retrieved context.
6. A pipeline stepper animates through each of these stages live as a query runs,
   so you can see ingestion and retrieval happening rather than just getting a
   black-box chat response.

You can switch the active knowledge base between the default document and any
file you upload, each ingested into its own isolated collection/namespace. You can
also switch the accent color (blue / orange / green) from the header.

## Bring your own keys

Open **Settings** (gear icon, top right) and paste in:

| Key | Used for | Get one at |
|---|---|---|
| Groq API key | Generating the final answer | https://console.groq.com/keys |
| OpenAI API key | Embedding your documents and questions | https://platform.openai.com/api-keys |
| Pinecone API key | The vector store (an index is auto-created on first use) | https://app.pinecone.io |

These are stored only in your browser and sent as request headers
(`X-Groq-Key`, `X-OpenAI-Key`, `X-Pinecone-Key`) with every API call — the
backend reads them per-request and never writes them to disk, a database, or logs.
Until all three are set, ingestion and querying are disabled with a banner
pointing you to Settings.

## Architecture

```
 Frontend (React + Vite)
   Settings (keys → localStorage)    ThemeSwitcher (blue/orange/green)
   PipelineStepper · UploadPanel · ChatPanel · RetrievedChunks · AnswerPanel
             │
             │  HTTP  /api/*  (JSON + X-Groq-Key / X-OpenAI-Key / X-Pinecone-Key headers)
             ▼
 Backend (FastAPI)
   keys.py — reads the 3 headers into an ApiKeys object via FastAPI Depends()
   routers/
     ingest.py       — upload a file, or re-ingest the default PDF
     query.py        — embed question → retrieve → call LLM → return answer
     collections.py  — list / activate / delete knowledge-base collections
             │
             ▼
   chunking.py  →  embeddings.py  →  vectorstore.py  →  llm.py
             │             │               │              │
             ▼             ▼               ▼              ▼
      PDF/txt/md     Embeddings       Vector store       Groq
      → chunks     Ollama (local)   Chroma (local)    LLM API
                    OpenAI (cloud)   Pinecone (cloud)  (per-visitor key)
```

**Request flow for a query:**
`question → embed(question) using the visitor's OpenAI key → nearest-neighbor
search in Pinecone using their Pinecone key → top-K chunks (shown in UI with
scores) → chunks + question sent to Groq using their Groq key → answer (shown
separately from the chunks)`

**Request flow for ingestion (default doc or upload):**
`PDF/txt/md → extract text per page → split into overlapping chunks → embed each
chunk (visitor's key) → upsert (id, embedding, {text, source, page}) into the
vector store under a collection/namespace (visitor's key)`

**No server-side secrets:** `backend/app/config.py` holds no Groq/OpenAI/Pinecone
API keys at all — every function in `embeddings.py`, `llm.py`, and `vectorstore.py`
takes the relevant key as an explicit parameter, sourced from the request headers
via `keys.py`. The embeddings/vector-store *provider choice* (ollama vs openai,
chroma vs pinecone) still switches automatically based on the `VERCEL` env var,
same as before — only the credentials themselves moved to per-request headers.

## Requirements

- Python 3.10+
- Node.js 18+
- [Ollama](https://ollama.com) installed locally (only needed for local dev's
  default Ollama/Chroma path — not needed if you only test against Vercel)

## Setup (local dev)

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
uvicorn main:app --reload --port 8787
```

No `.env` file is required to get started — the Groq key (always needed, for
answer generation) is entered on the Settings page in the browser. `backend/.env.example`
lists optional overrides (ports, chunking size, provider selection, etc.) if you want them.

### 3. ChromaDB (vector store)

From the project root (in a separate terminal — the `chroma` CLI comes from the
backend's virtualenv you just created):

```bash
npm run chroma
```

This starts a local Chroma server on `http://localhost:8010`, persisting to `./chroma-data`.
Start this **before** the backend, since the backend connects to it on startup.

Unlike the original RAG Explorer, there's no automatic ingestion on startup here —
there's no server-side key to do it with. Once you've added your Groq key in
Settings, click **"Re-ingest default PDF"** in the Knowledge Base panel to seed it.

### 4. Frontend (React)

```bash
cd frontend
npm install
npm run dev
```

Open the printed URL (default `http://localhost:5173`), go to **Settings**, add
your key(s), then use the app.

## Using it

1. **Add your keys** — open Settings and paste your Groq / OpenAI / Pinecone keys.
   They're saved to this browser only.
2. **Ingest the default doc** — click "Re-ingest default PDF" once (no auto-ingest
   on startup in this BYOK variant, since there's no server-side key to ingest with).
3. **Upload your own** — drag a `.pdf`, `.txt`, or `.md` file onto the "Knowledge Base"
   panel. It's chunked, embedded, and stored in its own collection/namespace. The
   uploaded doc becomes the active knowledge base automatically — switch back to
   the default (or between multiple uploads) with the **Use** button.
4. **Ask a question** — type it into the chat box. The app embeds your question,
   retrieves the top 4 (`TOP_K`) most relevant chunks from the active collection
   (shown with similarity score + source/page), then sends them to Groq for the
   final answer. The pipeline stepper at the top animates through each stage as it runs.
5. **Reset** — delete an uploaded collection with the ✕ button, or re-ingest the
   default PDF at any time.
6. **Change the theme** — pick blue / orange / green from the header.

## Deploying to Vercel

The frontend (static build) and backend (a single Python serverless function at
`api/index.py`) deploy together as one Vercel project — `vercel.json` builds the
Vite app and rewrites `/api/*` to the Python function, so they share an origin
(no CORS to configure).

```bash
npx vercel --prod
```

That's it — **no environment variables need to be set** for Groq/OpenAI/Pinecone,
since this variant never reads them server-side. The first deploy creates the
Pinecone index automatically (dimension 1536, cosine metric) under whichever
visitor's Pinecone key first triggers it. Each visitor adds their own keys via
Settings after opening the deployed site.

Uploads on Vercel are processed in a temp directory scoped to that invocation —
they're chunked/embedded/stored in the vector DB immediately, not kept as
persistent files (unlike local dev, where they're saved under `uploads/`).

## Configuration

Non-secret settings only (no API keys live here in this variant) — copy
`backend/.env.example` to `backend/.env` to override any of these:

| Variable | Default | Purpose |
|---|---|---|
| `GROQ_MODEL` | `openai/gpt-oss-120b` | Groq chat model |
| `EMBEDDINGS_PROVIDER` | `ollama` locally, `openai` on Vercel | `ollama` or `openai` |
| `VECTORSTORE_PROVIDER` | `chroma` locally, `pinecone` on Vercel | `chroma` or `pinecone` |
| `OLLAMA_URL` | `http://localhost:11434` | Local Ollama server |
| `EMBED_MODEL` | `nomic-embed-text` | Ollama embedding model |
| `CHROMA_URL` | `http://localhost:8010` | Local Chroma server |
| `OPENAI_EMBED_MODEL` | `text-embedding-3-small` | OpenAI embedding model |
| `PINECONE_INDEX` | `rag-explorer` | Pinecone index name (auto-created) |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | `1200` / `200` | Chunking parameters |
| `TOP_K` | `4` | Chunks retrieved per query |
| `PORT` | `8787` | Backend port (local dev only) |

## Project layout

```
RAG Explorer BYOK/
├── data/                 # default source PDF(s)
├── uploads/              # user-uploaded files (local dev only)
├── chroma-data/          # Chroma's persistent storage (gitignored, local dev only)
├── api/
│   └── index.py          # Vercel serverless entrypoint (imports backend/main.py's app)
├── vercel.json            # builds frontend + rewrites /api/* to api/index.py
├── requirements.txt        # lean deps for the Vercel function (fastapi, pinecone, ...)
├── backend/
│   ├── main.py           # FastAPI app entrypoint (no startup auto-ingest)
│   ├── requirements.txt  # full local-dev deps (adds chromadb, uvicorn)
│   └── app/
│       ├── config.py     # non-secret config only; picks providers based on VERCEL env var
│       ├── keys.py       # reads X-Groq-Key/X-OpenAI-Key/X-Pinecone-Key headers
│       ├── chunking.py   # PDF/txt parsing + overlapping chunk splitting
│       ├── embeddings.py # Ollama (local) or OpenAI (cloud) embedding calls — takes api_key param
│       ├── vectorstore.py# Chroma (local) or Pinecone (cloud) client wrapper — takes api_key param
│       ├── llm.py        # Groq chat completion call — takes api_key param
│       ├── ingest.py     # chunk → embed → store pipeline
│       ├── state.py      # active-collection tracking
│       └── routers/      # /api/ingest, /api/query, /api/collections
└── frontend/
    └── src/
        ├── App.jsx
        ├── api.js         # attaches saved keys as headers to every request
        ├── keys.js        # localStorage read/write/clear for the 3 keys
        └── components/
            ├── SettingsPage.jsx    # where visitors enter their keys
            ├── ThemeSwitcher.jsx   # blue / orange / green accent picker
            ├── PipelineStepper.jsx
            ├── UploadPanel.jsx
            ├── ChatPanel.jsx
            ├── RetrievedChunks.jsx
            └── AnswerPanel.jsx
```

## Troubleshooting

- **"Missing Groq/OpenAI/Pinecone API key. Add it on the Settings page."** — exactly
  what it says; open Settings and paste that key.
- **"Could not reach Ollama"** (local dev only) — make sure `ollama serve` is
  running and `ollama pull nomic-embed-text` has completed.
- **"Ollama returned no embedding"** (local dev only) — the embed model isn't
  pulled yet; run `ollama pull nomic-embed-text`.
- **Empty retrieval / "No chunks found"** — ingest a document first (click
  "Re-ingest default PDF", or upload your own).
- **Pinecone request failed** — usually an invalid key, or the account/project
  it belongs to lacking access; check the key on https://app.pinecone.io.
