import httpx

from . import config


class EmbeddingError(RuntimeError):
    pass


async def _embed_texts_ollama(texts: list[str]) -> list[list[float]]:
    vectors: list[list[float]] = []
    async with httpx.AsyncClient(timeout=60.0) as client:
        for text in texts:
            try:
                resp = await client.post(
                    f"{config.OLLAMA_URL}/api/embeddings",
                    json={"model": config.EMBED_MODEL, "prompt": text},
                )
                resp.raise_for_status()
            except httpx.ConnectError as exc:
                raise EmbeddingError(
                    f"Could not reach Ollama at {config.OLLAMA_URL}. "
                    "Is `ollama serve` running?"
                ) from exc
            except httpx.HTTPStatusError as exc:
                raise EmbeddingError(
                    f"Ollama embedding request failed: {exc.response.text}"
                ) from exc
            data = resp.json()
            embedding = data.get("embedding")
            if not embedding:
                raise EmbeddingError(
                    f"Ollama returned no embedding. Is model '{config.EMBED_MODEL}' pulled? "
                    f"Run: ollama pull {config.EMBED_MODEL}"
                )
            vectors.append(embedding)
    return vectors


async def _embed_texts_openai(texts: list[str]) -> list[list[float]]:
    if not config.OPENAI_API_KEY:
        raise EmbeddingError("OPENAI_API_KEY is not set.")

    headers = {"Authorization": f"Bearer {config.OPENAI_API_KEY}"}
    payload = {
        "model": config.OPENAI_EMBED_MODEL,
        "input": texts,
        "dimensions": config.OPENAI_EMBED_DIMENSIONS,
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            resp = await client.post(
                "https://api.openai.com/v1/embeddings", json=payload, headers=headers
            )
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise EmbeddingError(f"OpenAI embedding request failed: {exc.response.text}") from exc
        except httpx.ConnectError as exc:
            raise EmbeddingError("Could not reach OpenAI's API.") from exc

    data = resp.json()
    ordered = sorted(data["data"], key=lambda item: item["index"])
    return [item["embedding"] for item in ordered]


async def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    if config.EMBEDDINGS_PROVIDER == "openai":
        return await _embed_texts_openai(texts)
    return await _embed_texts_ollama(texts)


async def embed_query(text: str) -> list[float]:
    vectors = await embed_texts([text])
    return vectors[0]
