"""AI image generation for QA Content Agent posts.

Tries OpenAI's gpt-image-1 first. On a rate limit / billing / quota error,
cascades through whichever fallback providers are configured: Gemini image
generation (GEMINI_API_KEY), then Hugging Face's Inference API running
FLUX.1-schnell (HUGGINGFACE_API_KEY). If every configured provider fails,
raises QuotaExceededError so the caller can fall back to a PIL placeholder.

If a `reference_image` (raw bytes, e.g. a user-uploaded file) is given, it's
used as a visual base via OpenAI's image-edit endpoint, then Gemini's
multimodal image+text input, before falling through to the text-to-image
chain above — Hugging Face's text-to-image endpoint has no reference-image
support, so the reference is dropped (not an error) once it reaches that tier.

Returns raw image bytes in all cases — image_composer accepts that directly
(as well as URLs and local paths).
"""
import base64
import os
from io import BytesIO

import openai
import requests
from openai import OpenAI

from agents import QUOTA_EXCEEDED_MESSAGE, QuotaExceededError, _format_openai_error, _log

GEMINI_IMAGE_MODEL = "gemini-2.5-flash-image"
HF_IMAGE_MODEL = "black-forest-labs/FLUX.1-schnell"
HF_API_URL = f"https://router.huggingface.co/hf-inference/models/{HF_IMAGE_MODEL}"

_client = None


def get_client():
    """Return a lazily-created OpenAI client using OPENAI_API_KEY from the environment."""
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    return _client


def generate_image(prompt, reference_image=None, size="1024x1536", quality="high", logs=None):
    """Generate an image for the given prompt.

    `size` should be the gpt-image-1 size closest to the target canvas
    ratio — 1024x1536 (portrait) for LinkedIn's 1080x1350, 1536x1024
    (landscape) for Medium's 1200x630. `reference_image`, if given, is raw
    image bytes used as a visual base (see module docstring). If `logs` is
    a list, detailed provider error info is appended to it for
    display/debugging.
    """
    if reference_image:
        image = _generate_with_reference(prompt, reference_image, size, quality, logs)
        if image:
            return image
        _log(logs, "Reference image isn't supported by the remaining providers — continuing with text-only generation.")

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
    except (openai.RateLimitError, openai.BadRequestError) as exc:
        is_moderation = (
            isinstance(exc, openai.BadRequestError)
            and isinstance(exc.body, dict)
            and exc.body.get("error", {}).get("code") == "moderation_blocked"
        )
        _log(logs, f"Image generation (gpt-image-1): {_format_openai_error(exc)}")
        if is_moderation:
            raise RuntimeError(
                "Image prompt was blocked by OpenAI content moderation. "
                "Try a different topic."
            ) from exc
        return _fallback_chain(prompt, logs)


def _generate_with_reference(prompt, reference_image, size, quality, logs):
    """Try the reference-image-aware tiers (OpenAI edit, then Gemini multimodal)."""
    try:
        client = get_client()
        image_file = BytesIO(reference_image)
        image_file.name = "reference.png"
        response = client.images.edit(
            model="gpt-image-1",
            image=image_file,
            prompt=prompt,
            size=size,
            quality=quality,
        )
        return base64.b64decode(response.data[0].b64_json)
    except Exception as exc:
        _log(logs, f"Image edit (gpt-image-1, with reference image): {exc}")

    if os.environ.get("GEMINI_API_KEY"):
        try:
            return _generate_image_gemini(prompt, reference_image=reference_image)
        except Exception as exc:
            _log(logs, f"Image generation ({GEMINI_IMAGE_MODEL}, with reference image): {exc}")

    return None


def _fallback_chain(prompt, logs):
    """Try every configured fallback provider in turn; raise QuotaExceededError if all fail."""
    if os.environ.get("GEMINI_API_KEY"):
        _log(logs, f"Falling back to Gemini ({GEMINI_IMAGE_MODEL}) due to rate limit...")
        try:
            return _generate_image_gemini(prompt)
        except Exception as exc:
            _log(logs, f"Image generation ({GEMINI_IMAGE_MODEL}): {exc}")

    if os.environ.get("HUGGINGFACE_API_KEY"):
        _log(logs, f"Falling back to Hugging Face ({HF_IMAGE_MODEL})...")
        try:
            return _generate_image_huggingface(prompt)
        except Exception as exc:
            _log(logs, f"Image generation ({HF_IMAGE_MODEL} via Hugging Face): {exc}")

    raise QuotaExceededError(QUOTA_EXCEEDED_MESSAGE)


def _generate_image_gemini(prompt, reference_image=None):
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    contents = [prompt]
    if reference_image:
        contents = [types.Part.from_bytes(data=reference_image, mime_type="image/png"), prompt]

    response = client.models.generate_content(
        model=GEMINI_IMAGE_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"]),
    )

    for part in response.candidates[0].content.parts:
        if part.inline_data and part.inline_data.data:
            return part.inline_data.data

    raise RuntimeError("Gemini did not return an image for this prompt.")


def _generate_image_huggingface(prompt):
    resp = requests.post(
        HF_API_URL,
        headers={"Authorization": f"Bearer {os.environ.get('HUGGINGFACE_API_KEY')}"},
        json={"inputs": prompt},
        timeout=60,
    )
    content_type = resp.headers.get("content-type", "")
    if resp.ok and content_type.startswith("image/"):
        return resp.content

    try:
        detail = resp.json()
        message = detail.get("error") or detail
    except ValueError:
        message = resp.text[:300]
    raise RuntimeError(f"Hugging Face [{resp.status_code}]: {message}")
