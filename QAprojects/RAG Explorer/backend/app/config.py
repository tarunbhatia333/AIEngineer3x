import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / ".env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")

CHROMA_URL = os.getenv("CHROMA_URL", "http://localhost:8010")
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "vwo_prd")

DATA_DIR = (BACKEND_DIR / os.getenv("DATA_DIR", "../data")).resolve()
UPLOADS_DIR = (BACKEND_DIR / os.getenv("UPLOADS_DIR", "../uploads")).resolve()

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1200"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))
TOP_K = int(os.getenv("TOP_K", "4"))

PORT = int(os.getenv("PORT", "8787"))

DEFAULT_PDF_NAME = "Product_Requirements_Document_VWO.pdf"
DEFAULT_COLLECTION = "default"
UPLOAD_COLLECTION_PREFIX = "upload"

DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
