"""Embedding models implementation."""

import asyncio
from abc import ABC
from abc import abstractmethod
from typing import List

import cohere
import numpy as np
from litellm import embedding
from tqdm.auto import tqdm

from pluscoder.search.models import Chunk


class EmbeddingModel(ABC):
    """Abstract base class for embedding models."""

    @abstractmethod
    async def embed_chunks(self, chunks: List[Chunk]) -> List[List[float]]:
        """Generate embeddings for chunks."""


class LiteLLMEmbedding(EmbeddingModel):
    """Cohere embedding implementation."""

    def __init__(
        self,
        model_name: str = "embed-english-v3.0",
        batch_size: int = 64,
        embedding_type: str = "ubinary",
    ):
        self.model_name = model_name
        self.batch_size = batch_size
        self.embedding_type = embedding_type

    async def embed_chunks(self, chunks: List[Chunk]) -> List[List[float]]:
        """Generate embeddings for chunks in batches."""
        all_embeddings = []

        # Split chunks into batches
        for i in range(0, len(chunks), self.batch_size):
            batch = chunks[i : i + self.batch_size]
            batch_embeddings = await self._embed_batch(batch)
            all_embeddings.extend(batch_embeddings)
            await asyncio.sleep(1)  # Rate limiting

        return all_embeddings

    async def _embed_batch(self, chunks: List[Chunk]) -> List[List[float]]:
        """Embed a batch of chunks."""
        try:
            texts = [chunk.content for chunk in chunks]
            response = embedding(model=self.model_name, input=texts, input_type="search_document")

            return [embed["embedding"] for embed in response.data]

        except Exception as e:
            # Log error and return empty embeddings
            print(f"Embedding error: {e!s}")
            return [[0.0] * 1024] * len(chunks)  # Default size for empty embeddings
