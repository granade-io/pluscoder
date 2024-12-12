"""Models for embedding providers and configurations."""

from abc import ABC
from abc import abstractmethod
from typing import List

from pydantic import BaseModel
from pydantic import Field

from pluscoder.search.models import Chunk


class EmbeddingModel(ABC):
    """Abstract base class for embedding models."""

    @abstractmethod
    async def embed_document(self, chunks: List[Chunk]) -> List[List[float]]:
        """Generate embeddings for chunks."""

    @classmethod
    def has_embeddings(cls, storage):
        chunks = storage.load("chunks") or []
        return len(chunks) and bool(chunks[0].embedding)


class ProviderConfig(BaseModel):
    """Base configuration for embedding providers"""


class CohereConfig(ProviderConfig):
    """Cohere-specific configuration
    See: https://docs.litellm.ai/docs/embedding/supported_embedding#example
    """

    input_type: str = Field(
        default="search_document",
        description="Input type for embedding. Options: search_document, search_query",
    )


class VertexAIConfig(ProviderConfig):
    """Vertex AI configuration
    See: https://cloud.google.com/vertex-ai/generative-ai/docs/embeddings/task-types
    """
