# Advance RAG Explorer

End-to-end teaching demo for The Testing Academy. Upgrades a basic RAG demo
with techniques that matter at scale on a real corpus (VWO test cases):

- **Hybrid retrieval** — dense embeddings + a hand-rolled sparse (TF-IDF)
  inverted index, fused with Reciprocal Rank Fusion (RRF)
- **Vector DB** — Chromadb (persistent, embedded — no server/Docker needed),
  with native metadata filters
- **Re-ranking** — a cross-encoder re-scores the fused candidates
- **Query rewriting** — Groq generates alternate phrasings before retrieval
- **Generation** — Groq, streamed token-by-token over SSE

UI uses a Claude-inspired theme (warm cream + coral) with a two-pane layout:
left = pipeline stage tracker (live), right = active content / chat.

**Live demo:** https://advance-rag-explorer.vercel.app — public, no login, running
against real OpenAI/Pinecone/Groq quota. See "Deployment" below before sharing
this link further.

> **Note on the vector DB / model choice.** The original spec for this demo
> named Qdrant in most places but Chromadb in one bullet. This build commits
> to **Chromadb**, per your call — see [`vectorstore.py`](vectorstore.py).
> Because OSS Chroma has no native sparse-vector type, sparse retrieval here
> is a small hand-rolled TF-IDF inverted index ([`sparse_index.py`](sparse_index.py))
> that plays the same role bge-m3's neural sparse output would on Qdrant.
> Similarly, `bge-m3` / `bge-reranker-v2-m3` are **not** the default models —
> see "Model profile" below.

---

## Deployment

Two deployment targets share this one codebase, switched automatically by
`config.IS_SERVERLESS` (true whenever Vercel's own `VERCEL=1` env var is
present — nothing to set by hand):

| | Local dev (default) | Vercel (serverless) |
|---|---|---|
| Dense embeddings | local model (`MODEL_PROFILE` light/full) | OpenAI `text-embedding-3-small` |
| Vector store | Chroma, persistent local dir | Pinecone, hybrid dense+sparse index (`metric=dotproduct`) |
| Sparse retrieval | hand-rolled TF-IDF (`sparse_index.SparseIndex`) | stateless hashing-trick encoder (`sparse_index.HashingSparseEncoder`) — no persisted vocabulary needed, since a serverless cold start has nowhere to keep one |
| Reranker | local cross-encoder | Groq LLM-as-reranker (`reranker.LLMReranker`) |
| Upload → Ingest | can rely on server memory across requests | **cannot** — Vercel functions don't share memory between invocations, so the browser re-sends the actual file on "Start Ingestion" instead of trusting a previous request's state (see `app.py` module docstring) |

Why Vercel needs all this instead of just running the local version: no
persistent local disk (Chroma's embedded store and the TF-IDF index's JSON
file both need one), and no room in the function bundle for
torch/sentence-transformers (Vercel's Python function has a hard size limit
those blow past). Pinecone's hybrid index still gets queried as two separate
dense-only / sparse-only rankings (the sparse-only query zeroes out the dense
vector so it contributes nothing to the score), then fused with the exact
same `rrf_fuse()` used locally — so the retrieval *logic* is identical, only
where the vectors live and how they're produced differs.

**Redeploying after code changes:**
```bash
npx vercel@latest deploy --prod --token <your Vercel token>
```
Env vars (`GROQ_API_KEY`, `OPENAI_API_KEY`, `PINECONE_API_KEY`) are already
set on the Vercel project (`advance-rag-explorer`) — `vercel env ls` to check,
`vercel env add <NAME> production` to change one.

**Before sharing the live link further:** it has no authentication. Anyone
with the URL can upload files and chat, spending your actual OpenAI/Pinecone/
Groq quota. Fine for a short personal test; add a password gate (or take the
deployment down) before sending it anywhere public.

---

## Pipeline

```
Stage 1 (Ingest):
  CSV/XLSX -> rows -> assemble docs -> chunk (1 row = 1 chunk if small) ->
  dense embed + sparse TF-IDF -> Chroma collection 'vwo_test_cases'

Stage 2 (Chat):
  Question -> rewrite (Groq, x3) -> embed each variant -> dense + sparse
  search per variant -> RRF fuse across ALL variants -> cross-encoder
  rerank -> Groq -> grounded, streamed answer with [Chunk N] citations
```

---

## Model profile

Two swappable profiles, one constant in [`config.py`](config.py):

| `MODEL_PROFILE` | Dense embedder | Reranker | Install |
|---|---|---|---|
| `light` (default) | `BAAI/bge-small-en-v1.5` (~130MB) | `cross-encoder/ms-marco-MiniLM-L-6-v2` (~90MB) | `requirements.txt` as-is |
| `full` | `BAAI/bge-m3` (~2.3GB) | `BAAI/bge-reranker-v2-m3` (~570MB) | uncomment the `FlagEmbedding`/`torch` lines in `requirements.txt` |

Both profiles share the exact same interface (`embeddings.get_embedder()`,
`reranker.get_reranker()`), so flipping `MODEL_PROFILE=full` in `.env` is the
only change needed once the extra packages are installed.

---

## Setup

```bash
cd Advance_RAG
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements-local.txt
```

`requirements.txt` alone (no `chromadb`/`sentence-transformers`) is what
Vercel installs for the serverless deployment — see "Deployment" above.
Local dev needs `requirements-local.txt`, which layers those on top.

Chroma runs **embedded** by default (file store at `./chroma_data/`) — no
Docker, no server. `.env` needs a `GROQ_API_KEY` (see `.env.sample`).

---

## Run

```bash
python app.py
# open http://127.0.0.1:5050
```

A small `data/sample_test_cases.csv` (15 rows) is included so you can walk
the full pipeline immediately. Swap in your real ~5,000-row VWO export any
time via `/upload`.

The first request on `MODEL_PROFILE=light` downloads ~220MB of models from
Hugging Face (small, fast). On `full` it's ~3GB and noticeably slower to
warm up — subsequent requests are fast either way.

### CLI ingestion (optional)

```bash
python ingest.py data/sample_test_cases.csv \
  --text-cols title,steps,expected,tags \
  --meta-cols id,jira_id,priority,module
```

---

## What you can see in the UI

### `/upload` (upload + ingest, one page, live SSE)
- File picker accepts `.csv`, `.xlsx`, `.xls`.
- After upload: row count, columns, first 5 rows, dtypes.
- Pick text columns (concatenated into the embedded document) and metadata
  columns (kept as filterable payload), then "Start Ingestion" — the browser
  re-sends the same file alongside your column choices; nothing about running
  the pipeline depends on server state from the upload request.
- Stage tracker: Read → Build docs → Chunk → Embed → Index.
- **Chunk**: histogram, total chunks, avg/min/max chars, sample chunks with
  overlap highlighted.
- **Embed**: progress bar, dense vector preview (first 8 dims), sparse top-5
  tokens by TF-IDF weight.
- **Index**: Chroma collection name, chunk count, store path.

### `/chunks`
- Paginated viewer (50/page) over the entire collection.
- Search box (substring) + filters (`priority`, `module`, `jira_id`).
- Each chunk card: id, metadata, full text.
- Chunks used in the most recent chat answer are outlined in coral.

### `/chat`
- Chat box on the right; pipeline stage tracker on the left updates live per
  query (Rewrite → Retrieve → Rerank → Generate).
- Each turn has a collapsible "pipeline detail" panel showing:
  - The 3 query rewrites
  - Dense top-N vs sparse top-N vs RRF-fused top-N
  - Rerank before/after table
  - Final answer with clickable `[Chunk N]` citations
- Two modes auto-detected:
  - **Answer** — grounded Q&A on the test cases.
  - **Generate** — phrases like "create a new test case for JIRA VWO-1234"
    produce a structured test case (Title / Preconditions / Steps / Expected
    / Priority / Tags) using retrieved similar test cases as style templates.

---

## Tunables (top of `config.py`)

| Knob               | Default | Meaning                                          |
|--------------------|---------|--------------------------------------------------|
| `CHUNK_SIZE`       | 1000    | Max chars per chunk before splitting             |
| `CHUNK_OVERLAP`    | 150     | Chars repeated between adjacent chunks           |
| `TOP_N_HYBRID`     | 20      | Candidates per dense / sparse search             |
| `TOP_K_RERANK`     | 4       | Final chunks sent to LLM after rerank            |
| `RRF_K`            | 60      | Reciprocal Rank Fusion smoothing constant        |
| `REWRITE_ENABLED`  | True    | Use Groq to generate alt phrasings before search |
| `MODEL_PROFILE`    | light   | `light` or `full` — see "Model profile" above    |

---

## Project layout

```
config.py            tunables + model profile + provider switches (local vs Vercel)
chunking.py           Stage 1: doc assembly + chunking + stats
sparse_index.py       TF-IDF inverted index (local) + stateless hashing encoder (Vercel)
embeddings.py          dense embedder: local (light/full) or OpenAI (Vercel)
reranker.py            reranker: local cross-encoder or Groq LLM-as-reranker (Vercel)
vectorstore.py        Chroma or Pinecone hybrid: upsert, dense/sparse search, RRF, rerank
query_rewrite.py      Groq-based query rewriting
generation.py         Groq streaming generation, mode detection, citations
ingest.py             Stage 1 pipeline orchestration + CLI entrypoint
app.py                Flask app: pages + JSON/SSE APIs (stateless upload/ingest)
api/index.py          Vercel serverless entrypoint (re-exports app.py's Flask app)
vercel.json           Vercel routing + static-file bundling config
templates/            Jinja2 pages (base/upload/chunks/chat)
static/               Claude-inspired CSS + shared JS (SSE client, tracker)
explainer.html         standalone architecture write-up (open directly, no server)
```

---

## Troubleshooting

- **Groq 401** — `.env` is missing or `GROQ_API_KEY` is wrong.
- **First query is slow** — models are downloading + warming up. Subsequent
  calls are sub-second (light profile) or a few seconds (full profile, CPU).
- **Out-of-memory on `full` profile** — reduce `EMBED_BATCH` in `ingest.py`,
  or stay on `light`.
- **Port 5050 busy** — set `PORT` in `.env`.
- **`/ingest` redirects to `/upload`** — expected; they're one page/flow now
  (see "Deployment" above for why). Old bookmarks still land somewhere sensible.
- **Chunk Explorer looks empty right after ingesting on Vercel** — Pinecone's
  `list()` endpoint (used to enumerate chunks) can lag a few seconds behind an
  upsert. Refresh once.
- **`keys_private.md` in this folder** — that file has live plaintext API
  keys and is git-ignored, but it isn't used by any code here (the app reads
  from `.env`, also git-ignored). Consider deleting or rotating those keys —
  see the security note in `explainer.html`.
