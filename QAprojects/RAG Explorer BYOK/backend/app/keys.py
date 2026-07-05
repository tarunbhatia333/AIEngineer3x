from dataclasses import dataclass

from fastapi import Header


@dataclass
class ApiKeys:
    groq: str | None
    openai: str | None
    pinecone: str | None


async def get_api_keys(
    x_groq_key: str | None = Header(default=None, alias="X-Groq-Key"),
    x_openai_key: str | None = Header(default=None, alias="X-OpenAI-Key"),
    x_pinecone_key: str | None = Header(default=None, alias="X-Pinecone-Key"),
) -> ApiKeys:
    return ApiKeys(groq=x_groq_key or None, openai=x_openai_key or None, pinecone=x_pinecone_key or None)
