"""Vercel's Python builder auto-detects a WSGI `app` object exported from a
file under api/ and wraps it as the serverless function entrypoint. app.py
itself lives at the project root (not under api/) so it can be run directly
for local dev with `python app.py` — this file just re-exports it.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import app  # noqa: E402
