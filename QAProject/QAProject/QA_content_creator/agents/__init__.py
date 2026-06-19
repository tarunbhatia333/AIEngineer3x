"""Shared utilities for the QA Content Agent's LinkedIn/Medium agents.

Content generation tries Groq (Llama 3.3) first to save OpenAI credits, then
OpenAI (GPT-4o), then falls back to Gemini if OpenAI hits a rate limit/quota
and GEMINI_API_KEY is set — same fallback-chain pattern as the FBS reference
app, so this app never hard-fails on a single provider's free-tier limit.
"""
import json
import os
from datetime import date

import openai
from openai import OpenAI

_TODAY = date.today().strftime("%B %d, %Y")

VOICE_GUIDELINES = (
    "\"SOUNDS HUMAN, NOT AI\" VOICE RULES (this audience spots AI copy instantly):\n"
    "AVOID:\n"
    "- Stock AI openers: \"In today's fast-paced world...\", \"Let's dive in\", "
    "\"Unlock the power of...\", \"Game-changer\", \"It's not just X, it's Y\"\n"
    "- Heavy em-dash usage — at most ONE em-dash in the whole post\n"
    "- Emoji stacking — max 1 emoji, often zero (dev/QA audience, not lifestyle content)\n"
    "- A generic closing CTA repeated every time (e.g. always \"What are your thoughts?\")\n"
    "- Perfectly uniform sentence length / corporate-smooth rhythm\n"
    "- Hashtag stuffing inside the body text — hashtags belong at the end only\n"
    "USE:\n"
    "- First-person practitioner framing (\"Spent this morning debugging a flaky "
    "Playwright test and—\") rather than third-person announcer voice\n"
    "- One concrete, specific detail (a real error message shape, a real tool "
    "name + version from the grounding data, a real number) to anchor the post\n"
    "- Mixed sentence length: a short punchy line next to a longer explanatory one\n"
    "- A varied, topic-specific closing line/question each time, never a template\n"
    "- Contractions throughout (\"it's\", \"didn't\", \"you'll\")\n\n"
    "Example of the target voice (do not copy verbatim, just match the register):\n"
    "\"Spent the morning chasing a flaky Playwright test that only failed in CI. "
    "Turns out it was a race condition in our own wait helper, not the framework. "
    "Classic. Worth a reminder: if a test is flaky in CI but stable locally, check "
    "your waits before you blame the tool.\"\n"
)

IMAGE_BRAND_GUIDELINES = (
    "PALETTE: near-black background (#0D0D0D–#111111) with orange accent "
    "(#FF6B00–#FF7A00), clean bold sans-serif (Space Grotesk / Inter / Sora "
    "style) for any baked-in headline text.\n"
    "AESTHETIC: tech-editorial, not cartoonish — terminal/code-snippet "
    "fragments, abstract circuit or network line art, geometric shapes, "
    "minimal icons. No stock-photo people, no realistic photos of named "
    "individuals. Should look credible on a QA professional's LinkedIn feed, "
    "not like a meme.\n"
    "CRITICAL: every name, version number, stat, or fact drawn into the "
    "image must come ONLY from the real facts given in this prompt — never "
    "invent or guess a detail that wasn't explicitly provided."
)

LINKEDIN_IMAGE_GUIDELINES = (
    "Vertical 1080x1350 (4:5 feed post). Bake in a short hook headline and, "
    "where the content is cheatsheet/listicle-style, 2-4 short bullet lines "
    "(e.g. \"3 Playwright locator strategies\") written VERBATIM in this "
    "prompt, not described abstractly. Reserve a bottom ~130px strip clear "
    "and uncluttered for a brand lockup to be drawn afterward.\n" + IMAGE_BRAND_GUIDELINES
)

MEDIUM_IMAGE_GUIDELINES = (
    "Horizontal 1200x630 standard article cover. Simpler than a feed post: "
    "title text only, no bullet list (the article body carries the detail). "
    "Reserve a bottom ~80px strip clear and uncluttered for a brand lockup "
    "to be drawn afterward.\n" + IMAGE_BRAND_GUIDELINES
)

SYSTEM_PROMPT = (
    "You are a senior QA engineer / test-automation practitioner writing "
    "content for software testing professionals on LinkedIn and Medium — "
    "topics: Selenium, Playwright, AI agents in QA, vibe coding, and n8n "
    "workflows for QA.\n"
    f"Today's date is {_TODAY}. All content must read as current as of today.\n"
    "Never write placeholder text such as [Tool Name], [Version], [Number], "
    "etc. — output must always read like a finished post, never a "
    "fill-in-the-blank template.\n\n"
    "IMPORTANT — anti-hallucination rule: never invent a tool version, "
    "benchmark number, statistic, or quote. QA audiences spot fake "
    "specifics immediately (a wrong Selenium version, a made-up \"study "
    "found X%\" with no source). Any specific number, version, or claim "
    "must trace back to the real data given to you in the user prompt. If "
    "no such fact is available, phrase it as general/timeless advice "
    "instead of guessing.\n\n"
    + VOICE_GUIDELINES
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
