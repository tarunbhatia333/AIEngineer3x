import httpx

from . import config


class EmbeddingError(RuntimeError):
    pass


async def embed_texts(texts: list[str]) -> list[list[float]]:
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


async def embed_query(text: str) -> list[float]:
    vectors = await embed_texts([text])
    return vectors[0]
