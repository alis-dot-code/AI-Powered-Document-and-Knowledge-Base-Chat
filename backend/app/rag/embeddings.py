"""
OpenAI embedding wrapper with batching and retry.
Returns list[list[float]] in the same order as input texts.
"""
import asyncio
from typing import Any

from openai import AsyncOpenAI

from app.config import settings

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _client


async def embed_texts(
    texts: list[str],
    batch_size: int = 100,
) -> list[list[float]]:
    """Embed texts in batches. Returns embeddings in input order."""
    client = _get_client()
    all_embeddings: list[list[float]] = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        response = await client.embeddings.create(
            model=settings.openai_embedding_model,
            input=batch,
            dimensions=settings.openai_embedding_dimensions,
        )
        # Response items are sorted by index
        sorted_data = sorted(response.data, key=lambda d: d.index)
        all_embeddings.extend(item.embedding for item in sorted_data)

    return all_embeddings


def embed_texts_sync(texts: list[str], batch_size: int = 100) -> list[list[float]]:
    """Synchronous wrapper used by Celery workers."""
    return asyncio.get_event_loop().run_until_complete(
        embed_texts(texts, batch_size=batch_size)
    )
