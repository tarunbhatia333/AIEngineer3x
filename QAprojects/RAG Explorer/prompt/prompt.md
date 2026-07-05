# Build: RAG Explorer (Local-First)

## Goal
Build a full-stack RAG (Retrieval-Augmented Generation) Explorer application that
visually demonstrates the entire RAG pipeline — ingestion, chunking, embedding,
storage, retrieval, and answer generation — using a React frontend and a local
backend. The app must run entirely on localhost for testing before any deployment.

## Tech Stack (required)
- Frontend: React (Vite)
- Backend: Python (FastAPI) or Node (Express) — pick one and keep it consistent
- Vector DB: ChromaDB, running locally (persistent local storage, no cloud)
- Embedding model: Nomic Embed (nomic-embed-text), served via local Ollama
- LLM provider: Groq API, model `openai/gpt-oss-120b`
- Default source doc: `data/Product_Requirements_Document_VWO.pdf`

## Functional Requirements

1. **Default ingestion**
   - On startup, read the default PDF from the `data/` folder.
   - Parse and split it into overlapping chunks (size/overlap configurable via .env).
   - Generate embeddings for each chunk using Nomic Embed (via local Ollama).
   - Store chunks + embeddings + metadata (source filename, chunk index) in a local
     ChromaDB collection.

2. **Custom file upload**
   - Add an "Upload Document" option in the UI (PDF, and optionally .txt/.md).
   - Uploaded files should be saved to a local `uploads/` folder.
   - Run the same chunk → embed → store pipeline on the uploaded file, into either
     a new ChromaDB collection or a clearly labeled namespace, so the user can
     switch between "default doc" and "my uploaded doc" as the active knowledge base.
   - Show ingestion progress/status in the UI (chunk count, embedding progress).

3. **Query interface**
   - A chat-style input where the user types a question.
   - On submit:
     - Embed the query with Nomic Embed.
     - Retrieve the **top 4** most relevant chunks (TOP_K) from the active
       ChromaDB collection.
     - Display these 4 chunks in the UI (with similarity score + chunk source)
       before showing the final answer, so retrieval is visible, not hidden.
     - Send the retrieved chunks + question to Groq (`openai/gpt-oss-120b`) to
       generate the final answer.
     - Display the generated answer clearly, separate from the retrieved chunks.

4. **Pipeline visualization**
   - The UI should visually represent each stage of the flow as the query runs:
     `PDF/Upload → Chunking → Embedding → ChromaDB Storage → Retrieval → LLM Answer`
   - Highlight/animate the active stage as processing happens (a simple stepper or
     pipeline diagram is enough — doesn't need to be fancy).

## Local Hosting Requirements
- The app must run fully locally with clear, simple commands, e.g.:
  - Backend: `pip install -r requirements.txt` → `uvicorn main:app --reload`
  - Frontend: `npm install` → `npm run dev`
  - ChromaDB: `npm run chroma` (or equivalent local server start command)
  - Ollama: `ollama pull nomic-embed-text` then `ollama serve` (if not already running)
- ChromaDB should persist to a local directory (e.g. `./chroma-data`) — no external
  hosted vector DB.
- Use a `.env` file (git-ignored) for all config/secrets — see `.env.example` below.
  Only `.env.example` (with blank/placeholder values) should ever be committed.
- Include a top-level `README.md` with exact setup and run steps, and note any
  required Python/Node versions.

## .env.example (structure to follow — real values go only in local .env, never committed)

\`\`\`bash
# Copy to .env and fill in. Only GROQ_API_KEY is required.

# Groq — get a free key at https://console.groq.com/keys
GROQ_API_KEY=

# --- everything below has sensible defaults; override only if needed ---

# Groq LLM ("OpenGPT 120B")
GROQ_MODEL=openai/gpt-oss-120b

# Ollama (local) — the Nomic Embed model must be pulled: `ollama pull nomic-embed-text`
OLLAMA_URL=http://localhost:11434
EMBED_MODEL=nomic-embed-text

# Local ChromaDB server (started by `npm run chroma`)
CHROMA_URL=http://localhost:8000
CHROMA_COLLECTION=vwo_prd

# Folder the backend reads PDFs from (default: the sibling data/ folder)
DATA_DIR=../data

# Chunking
CHUNK_SIZE=1200
CHUNK_OVERLAP=200
TOP_K=4

# Backend port
PORT=8787
\`\`\`

## Nice-to-have (only if time permits)
- Ability to clear/reset a collection from the UI.
- Display which collection (default vs uploaded) is currently active.
- Basic error handling shown in the UI (e.g. failed embedding, Groq API errors,
  Ollama/ChromaDB not running).

## Deliverable
A working local project (frontend + backend + README + .env.example) that I can
run on my machine with the commands above and immediately test end-to-end:
ingest the default PDF, upload my own file, ask questions, and see retrieval +
generation happening step by step.