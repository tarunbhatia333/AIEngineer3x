"""Vercel Python serverless entrypoint — exposes the Flask app as `app`,
which Vercel's Python runtime auto-detects and wraps as a WSGI handler."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import app  # noqa: E402
