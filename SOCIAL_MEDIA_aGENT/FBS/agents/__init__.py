"""Shared utilities for FootBro Show content agents.

Content generation tries OpenAI (GPT-4o) first. If the OpenAI account has
hit its rate limit / daily quota, it automatically falls back to Gemini
(if GEMINI_API_KEY is set) so the app keeps working on a free OpenAI plan.
"""
import json
import os

import openai
from openai import OpenAI

SYSTEM_PROMPT = (
    'You are the social media manager for "The FootBro Show" (@thefootbroshow) — '
    "a football podcast by fans, for fans.\n"
    "Your job is to write engaging, punchy Instagram content for football fans.\n"
    "Always write in a conversational, opinionated, hype tone.\n"
    "Keep it real. No corporate speak.\n"
    "Never write placeholder text such as [Player Name], [Team Name], [Stadium "
    "Name], [Minute], [Score], etc. — output must always read like a finished "
    "post, never a fill-in-the-blank template.\n\n"
    "IMPORTANT: Never hallucinate or invent football stats, scores, player "
    "names, attendance figures, or match facts.\n\n"
    'All bullet point stats in the image MUST come from real data given to you '
    "in the prompt below. If the prompt tells you no live data is available, "
    'set "stats_bullets" to exactly one item: "Follow @thefootbroshow for more '
    'football news & stats" instead of generating fictional stats.'
)

IMAGE_PROMPT_GUIDELINES = (
    "dramatic editorial sports-photography style, breaking-news aesthetic, "
    "real football players/managers/fans in an emotional or action moment, "
    "dramatic lighting, ultra-HD, cinematic, horizontal wide crop, suitable "
    "for the top portion of a 1080x1350 (4:5) Instagram post, for a football "
    "fan podcast called The FootBro Show. Do NOT include any text, words, "
    "letters, captions, logos, or watermarks anywhere in the image — pure "
    "photography only"
)

OPENAI_TEXT_MODEL = "gpt-4o"
GEMINI_TEXT_MODEL = "gemini-2.0-flash"
GROQ_TEXT_MODEL = "llama-3.3-70b-versatile"
GROQ_BASE_URL = "https://api.groq.com/openai/v1"

QUOTA_EXCEEDED_MESSAGE = (
    "Daily free quota reached for AI content generation (OpenAI and Gemini). "
    "Please try again later or once your quota resets."
)

_client = None
_groq_client = None


class QuotaExceededError(Exception):
    """Raised when every configured AI provider's free quota is exhausted."""


def build_full_prompt(user_prompt, system_prompt=SYSTEM_PROMPT):
    """Combine the system + user prompt into one block for manual copy/paste use."""
    return f"{system_prompt}\n\n{user_prompt}"


def _format_openai_error(exc, provider="OpenAI"):
    """Build a short human-readable string from an OpenAI-SDK-style error."""
    try:
        error = (exc.body or {}).get("error", {})
        code = error.get("code") or exc.status_code
        message = error.get("message") or str(exc)
        return f"{provider} [{code}]: {message}"
    except Exception:
        return f"{provider}: {exc}"


def _format_gemini_error(exc):
    """Build a short human-readable string from a Gemini SDK error."""
    try:
        return f"Gemini [{exc.code}]: {exc.message}"
    except Exception:
        return f"Gemini: {exc}"


def _log(logs, message):
    if logs is not None:
        logs.append(message)


def get_client():
    """Return a lazily-created OpenAI client using OPENAI_API_KEY from the environment."""
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    return _client


def get_groq_client():
    """Return a lazily-created Groq client (OpenAI-compatible) using GROQ_API_KEY."""
    global _groq_client
    if _groq_client is None:
        _groq_client = OpenAI(api_key=os.environ.get("GROQ_API_KEY"), base_url=GROQ_BASE_URL)
    return _groq_client


def generate_content(user_prompt, system_prompt=SYSTEM_PROMPT, model=OPENAI_TEXT_MODEL, logs=None):
    """Generate JSON post content, trying Groq (Llama 3.3) first to save OpenAI credits.

    Falls back to OpenAI (GPT-4o), then to Gemini if OpenAI reports a rate
    limit / quota error and GEMINI_API_KEY is configured. Raises
    QuotaExceededError if every configured provider's free quota is
    exhausted. If `logs` is a list, detailed provider error info is appended
    to it for display/debugging.
    """
    if os.environ.get("GROQ_API_KEY"):
        try:
            client = get_groq_client()
            response = client.chat.completions.create(
                model=GROQ_TEXT_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.9,
            )
            return json.loads(response.choices[0].message.content)
        except Exception as exc:
            _log(logs, f"Content generation ({GROQ_TEXT_MODEL} via Groq): {_format_openai_error(exc, 'Groq')}")
            _log(logs, f"Falling back to OpenAI ({model}) for content generation...")

    try:
        client = get_client()
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.9,
        )
        return json.loads(response.choices[0].message.content)
    except openai.RateLimitError as exc:
        _log(logs, f"Content generation ({model}): {_format_openai_error(exc)}")
        if not os.environ.get("GEMINI_API_KEY"):
            raise QuotaExceededError(QUOTA_EXCEEDED_MESSAGE) from exc

        from google.genai import errors as genai_errors

        _log(logs, f"Falling back to Gemini ({GEMINI_TEXT_MODEL}) for content generation...")
        try:
            return _generate_content_gemini(user_prompt, system_prompt)
        except genai_errors.ClientError as gexc:
            _log(logs, f"Content generation ({GEMINI_TEXT_MODEL}): {_format_gemini_error(gexc)}")
            if gexc.code == 429:
                raise QuotaExceededError(QUOTA_EXCEEDED_MESSAGE) from gexc
            raise


def _generate_content_gemini(user_prompt, system_prompt):
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    response = client.models.generate_content(
        model=GEMINI_TEXT_MODEL,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
            temperature=0.9,
        ),
    )
    return json.loads(response.text)
