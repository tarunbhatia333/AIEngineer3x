"""AI image generation for FootBro Show posts.

Tries OpenAI's gpt-image-1 first. If the OpenAI account has hit its rate
limit / daily quota, falls back to Gemini image generation (if
GEMINI_API_KEY is set) so the app keeps working on a free OpenAI plan.

Returns raw image bytes in both cases — image_composer accepts that
directly (as well as URLs and local paths).
"""
import base64
import os

import openai
from openai import OpenAI

from agents import (
    QUOTA_EXCEEDED_MESSAGE,
    QuotaExceededError,
    _format_gemini_error,
    _format_openai_error,
    _log,
)

GEMINI_IMAGE_MODEL = "gemini-2.5-flash-image"

_client = None


def get_client():
    """Return a lazily-created OpenAI client using OPENAI_API_KEY from the environment."""
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    return _client


def generate_image(prompt, size="1536x1024", quality="medium", logs=None):
    """Generate an image for the given prompt.

    Uses a wide landscape gpt-image-1 size so the result can be cropped to
    the top portion of a 1080x1350 (4:5) Instagram post. Falls back to
    Gemini on an OpenAI rate limit / quota error. If `logs` is a list,
    detailed provider error info is appended to it for display/debugging.
    """
    try:
        client = get_client()
        response = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size=size,
            quality=quality,
            n=1,
        )
        return base64.b64decode(response.data[0].b64_json)
    except openai.RateLimitError as exc:
        _log(logs, f"Image generation (gpt-image-1): {_format_openai_error(exc)}")
        if not os.environ.get("GEMINI_API_KEY"):
            raise QuotaExceededError(QUOTA_EXCEEDED_MESSAGE) from exc

        from google.genai import errors as genai_errors

        _log(logs, f"Falling back to Gemini ({GEMINI_IMAGE_MODEL}) for image generation...")
        try:
            return _generate_image_gemini(prompt)
        except genai_errors.ClientError as gexc:
            _log(logs, f"Image generation ({GEMINI_IMAGE_MODEL}): {_format_gemini_error(gexc)}")
            if gexc.code == 429:
                raise QuotaExceededError(QUOTA_EXCEEDED_MESSAGE) from gexc
            raise


def _generate_image_gemini(prompt):
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    response = client.models.generate_content(
        model=GEMINI_IMAGE_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"]),
    )

    for part in response.candidates[0].content.parts:
        if part.inline_data and part.inline_data.data:
            return part.inline_data.data

    raise RuntimeError("Gemini did not return an image for this prompt.")
