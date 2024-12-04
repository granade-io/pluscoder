"""Search module for code search functionality."""

from pluscoder.search.algorithms import DenseSearch
from pluscoder.search.algorithms import HybridSearch
from pluscoder.search.algorithms import SearchAlgorithm
from pluscoder.search.algorithms import SparseSearch
from pluscoder.search.chunking import CharacterBasedChunking
from pluscoder.search.chunking import ChunkingStrategy
from pluscoder.search.chunking import TokenBasedChunking
from pluscoder.search.embeddings import EmbeddingModel
from pluscoder.search.embeddings import LiteLLMEmbedding
from pluscoder.search.engine import SearchEngine
from pluscoder.search.models import Chunk
from pluscoder.search.models import ChunkMetadata
from pluscoder.search.models import SearchResult

__all__ = [
    "Chunk",
    "ChunkMetadata",
    "SearchResult",
    "ChunkingStrategy",
    "TokenBasedChunking",
    "CharacterBasedChunking",
    "EmbeddingModel",
    "LiteLLMEmbedding",
    "SearchAlgorithm",
    "DenseSearch",
    "SparseSearch",
    "HybridSearch",
    "SearchEngine",
]
