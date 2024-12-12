"""Embedding models implementation."""

import asyncio
from typing import List

from litellm import aembedding
from tenacity import RetryError
from tenacity import retry
from tenacity import stop_after_attempt
from tenacity import wait_exponential

from pluscoder.agents.event.config import event_emitter
from pluscoder.search.embeddings.models import EmbeddingModel
from pluscoder.search.embeddings.models import ProviderConfig
from pluscoder.search.embeddings.providers import get_provider_config
from pluscoder.search.models import Chunk


class LiteLLMEmbedding(EmbeddingModel):
    """LiteLLM embedding implementation supporting multiple providers."""

    def __init__(
        self,
        model_name: str = "cohere/embed-english-v3.0",
        batch_size: int = 64,
    ):
        self.model_name = model_name
        self.batch_size = batch_size

    async def embed_document(self, chunks: List[Chunk]) -> List[List[float]]:
        """Generate embeddings for chunks in batches."""
        all_embeddings = []

        provider_config = get_provider_config(self.model_name, "search_document")
        await event_emitter.emit("indexing_started", chunks=len(chunks))

        # Split chunks into batches
        for i in range(0, len(chunks), self.batch_size):
            batch = chunks[i : i + self.batch_size]
            batch_embeddings = await self._embed_batch(batch, provider_config)
            await event_emitter.emit("indexing_progress", data={"chunks": self.batch_size})
            all_embeddings.extend(batch_embeddings)
            if i + self.batch_size < len(chunks):
                await asyncio.sleep(60)  # Rate limiting

        return all_embeddings

    async def embed_queries(self, queries: List[Chunk]) -> List[List[float]]:
        """Generate embeddings for a query."""
        all_embeddings = []

        provider_config = get_provider_config(self.model_name, "search_query")

        # Split chunks into batches
        for i in range(0, len(queries), self.batch_size):
            batch = queries[i : i + self.batch_size]
            batch_embeddings = await self._embed_batch(batch, provider_config)
            all_embeddings.extend(batch_embeddings)

        return all_embeddings

    async def _embed_batch_retry(self, chunks: List[Chunk]) -> List[List[float]]:
        try:
            provider_config = get_provider_config(self.model_name)
            return await self._embed_batch(chunks, provider_config)
        except RetryError:
            return [[0.0] * 1024] * len(chunks)

    @retry(
        wait=wait_exponential(multiplier=1, min=4, max=60),
        stop=stop_after_attempt(10),
    )
    async def _embed_batch(
        self,
        chunks: List[Chunk],
        provider_config: ProviderConfig,
    ) -> List[List[float]]:
        """Embed a batch of chunks."""
        texts = [chunk.content for chunk in chunks]

        response = await aembedding(
            model=self.model_name,
            input=texts,
            **provider_config.model_dump(),
        )
        return [embed["embedding"] for embed in response.data]


# @retry(
#     wait=wait_exponential(multiplier=1, min=4, max=60),
#     stop=stop_after_attempt(10),
# )
# async def __embed(model: str, input: str | list[str], **kwargs) -> list[list[float]]:
#     response = await aembedding(model=model, input=[input] if isinstance(input, str) else input, **kwargs)
#     return [embed["embedding"] for embed in response.data]


# async def __embed_batch(
#     model: str,
#     input: list[str],
#     batch_size: int,
#     delay: int,
#     **kwargs,
# ) -> list[list[float]]:
#     embeddings: list[list[float]] = []
#     for idx in range(0, len(input), batch_size):
#         batch: list[str] = input[idx : idx + batch_size]
#         embedding: list[list[float]] = await __embed(model=model, input=batch, **kwargs)
#         embeddings.extend(embedding)
#         await asyncio.sleep(delay=delay)  # workaround for rate limiting issues
#     return embeddings
