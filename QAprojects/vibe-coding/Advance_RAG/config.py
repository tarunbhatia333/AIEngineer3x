"""Central tunables for the Advance RAG demo. Change values here, not in the modules that use them.

Two deployment targets share this one codebase:

- local dev: persistent Chroma + local dense embedder/reranker (MODEL_PROFILE
  light/full), exactly as originally built and tested.
- Vercel (serverless): no persistent local disk and no room for torch/
  sentence-transformers in the function bundle, so IS_SERVERLESS flips three
  providers to hosted/stateless equivalents: OpenAI embeddings, a Pinecone
  hybrid (dense+sparse) index instead of Chroma, and a Groq LLM-based
  reranker instead of a local cross-encoder. See embeddings.py, vectorstore.py,
  reranker.py, sparse_index.py for the provider-selection logic this feeds.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

# Vercel sets VERCEL=1 in the function's environment automatically.
IS_SERVERLESS = bool(os.getenv("VERCEL"))

# --- model profile switch (local dev only) ---------------------------------
# "light"  -> small, fast local models (default; good for laptops / demos)
# "full"   -> BAAI/bge-m3 + BAAI/bge-reranker-v2-m3 as specified, requires
#             `pip install -r requirements-local.txt` with the full extras uncommented
MODEL_PROFILE = os.getenv("MODEL_PROFILE", "light").strip().lower()

LIGHT_DENSE_MODEL = "BAAI/bge-small-en-v1.5"
LIGHT_RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
FULL_DENSE_MODEL = "BAAI/bge-m3"
FULL_RERANK_MODEL = "BAAI/bge-reranker-v2-m3"

# --- provider switches -------------------------------------------------------
# "local" (default off-Vercel) or "openai" (default on Vercel)
EMBEDDINGS_PROVIDER = os.getenv("EMBEDDINGS_PROVIDER", "openai" if IS_SERVERLESS else "local")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
OPENAI_EMBED_DIMENSIONS = int(os.getenv("OPENAI_EMBED_DIMENSIONS", "1536"))

# "chroma" (default off-Vercel) or "pinecone" (default on Vercel)
VECTORSTORE_PROVIDER = os.getenv("VECTORSTORE_PROVIDER", "pinecone" if IS_SERVERLESS else "chroma")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
PINECONE_INDEX = os.getenv("PINECONE_INDEX", "advance-rag-explorer")
PINECONE_CLOUD = os.getenv("PINECONE_CLOUD", "aws")
PINECONE_REGION = os.getenv("PINECONE_REGION", "us-east-1")
PINECONE_NAMESPACE = os.getenv("PINECONE_NAMESPACE", "vwo_test_cases")
# Hashing-trick sparse vectors are stateless (no persisted vocabulary needed),
# which is what makes them viable across cold, independent serverless calls.
SPARSE_HASH_BUCKETS = int(os.getenv("SPARSE_HASH_BUCKETS", 2**18))

# "local" (default off-Vercel, cross-encoder) or "llm" (default on Vercel, Groq-scored)
RERANK_PROVIDER = os.getenv("RERANK_PROVIDER", "llm" if IS_SERVERLESS else "local")

# --- storage -----------------------------------------------------------------
# Uploads are never written to disk (see app.py / ingest.read_upload) — parsed
# straight from the request stream, so there's nothing to clean up and no
# assumption about a writable filesystem either.
CHROMA_DIR = str(BASE_DIR / "chroma_data")
COLLECTION_NAME = "vwo_test_cases"
SPARSE_INDEX_PATH = str(BASE_DIR / "chroma_data" / "sparse_index.json")

# --- pipeline knobs (see README "Tunables" table) --------------------------
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 1000))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 150))
TOP_N_HYBRID = int(os.getenv("TOP_N_HYBRID", 20))
TOP_K_RERANK = int(os.getenv("TOP_K_RERANK", 4))
RRF_K = int(os.getenv("RRF_K", 60))
REWRITE_ENABLED = os.getenv("REWRITE_ENABLED", "true").strip().lower() != "false"
NUM_REWRITES = 3

# --- LLM (Groq) --------------------------------------------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_REWRITE_MODEL = os.getenv("GROQ_REWRITE_MODEL", "llama-3.1-8b-instant")
GROQ_GEN_MODEL = os.getenv("GROQ_GEN_MODEL", "llama-3.3-70b-versatile")
GROQ_RERANK_MODEL = os.getenv("GROQ_RERANK_MODEL", "llama-3.1-8b-instant")

# --- server ------------------------------------------------------------------
PORT = int(os.getenv("PORT", 5050))
