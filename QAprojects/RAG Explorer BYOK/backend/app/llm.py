import httpx

from . import config

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


class LLMError(RuntimeError):
    pass


SYSTEM_PROMPT = (
    "You are a helpful assistant answering questions using only the provided context. "
    "If the answer is not contained in the context, say you don't know. "
    "Cite chunk numbers like [chunk 1] when relevant."
)


async def generate_answer(question: str, chunks: list[dict], api_key: str | None = None) -> str:
    if not api_key:
        raise LLMError("Missing Groq API key. Add it on the Settings page.")

    context = "\n\n".join(
        f"[chunk {i + 1}] (source: {c['source']}, page: {c.get('page', '?')})\n{c['text']}"
        for i, c in enumerate(chunks)
    )
    user_content = f"Context:\n{context}\n\nQuestion: {question}"

    payload = {
        "model": config.GROQ_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.2,
    }
    headers = {"Authorization": f"Bearer {api_key}"}

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            resp = await client.post(GROQ_URL, json=payload, headers=headers)
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise LLMError(f"Groq API error: {exc.response.text}") from exc
        except httpx.ConnectError as exc:
            raise LLMError("Could not reach Groq API. Check your network connection.") from exc

    data = resp.json()
    return data["choices"][0]["message"]["content"]
