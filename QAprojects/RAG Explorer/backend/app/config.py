import os
import tempfile
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / ".env")

IS_SERVERLESS = bool(os.getenv("VERCEL"))

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

# Embeddings: "ollama" (local, default) or "openai" (hosted, used on Vercel)
EMBEDDINGS_PROVIDER = os.getenv("EMBEDDINGS_PROVIDER", "openai" if IS_SERVERLESS else "ollama")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
OPENAI_EMBED_DIMENSIONS = int(os.getenv("OPENAI_EMBED_DIMENSIONS", "1536"))

# Vector store: "chroma" (local, default) or "pinecone" (hosted, used on Vercel)
VECTORSTORE_PROVIDER = os.getenv("VECTORSTORE_PROVIDER", "pinecone" if IS_SERVERLESS else "chroma")
CHROMA_URL = os.getenv("CHROMA_URL", "http://localhost:8010")
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "vwo_prd")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
PINECONE_INDEX = os.getenv("PINECONE_INDEX", "rag-explorer")
PINECONE_CLOUD = os.getenv("PINECONE_CLOUD", "aws")
PINECONE_REGION = os.getenv("PINECONE_REGION", "us-east-1")

DATA_DIR = (BACKEND_DIR / os.getenv("DATA_DIR", "../data")).resolve()

if IS_SERVERLESS:
    UPLOADS_DIR = Path(os.getenv("UPLOADS_DIR", tempfile.gettempdir())) / "rag-explorer-uploads"
else:
    UPLOADS_DIR = (BACKEND_DIR / os.getenv("UPLOADS_DIR", "../uploads")).resolve()

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1200"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))
TOP_K = int(os.getenv("TOP_K", "4"))

PORT = int(os.getenv("PORT", "8787"))

DEFAULT_PDF_NAME = "Product_Requirements_Document_VWO.pdf"
DEFAULT_COLLECTION = "default"
UPLOAD_COLLECTION_PREFIX = "upload"

UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
if not IS_SERVERLESS:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
