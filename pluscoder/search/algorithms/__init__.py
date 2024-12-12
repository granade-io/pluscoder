"""Search algorithms implementation."""

import asyncio
import hashlib
from abc import ABC
from abc import abstractmethod
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

import bm25s
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from pluscoder.search.embeddings import EmbeddingModel
from pluscoder.search.models import Chunk
from pluscoder.search.models import SearchResult


class SearchAlgorithm(ABC):
    """Abstract base class for search algorithms."""

    @abstractmethod
    async def build_index(self, chunks: List[Chunk], from_cache: bool = False) -> None:
        """Build search index from chunks."""

    @abstractmethod
    async def search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        """Search the index."""


class DenseSearch(SearchAlgorithm):
    """Vector similarity search implementation."""

    def __init__(self, embedding_model: EmbeddingModel):
        self.embedding_model = embedding_model
        self.chunks: List[Chunk] = []
        self.index: Optional[np.ndarray] = None

    async def build_index(self, chunks: List[Chunk], from_cache: bool = False) -> None:
        """Build search index from chunks."""
        self.chunks = chunks

        # Filter chunks that need embedding
        chunks_to_embed = [chunk for chunk in chunks if not chunk.embedding]

        # Calculate embeddings only for chunks without them
        if chunks_to_embed:
            new_embeddings = await self.embedding_model.embed_document(chunks_to_embed)
            for chunk, embedding in zip(chunks_to_embed, new_embeddings, strict=False):
                chunk.embedding = embedding

        # Build final index from all chunks
        self.index = np.array([chunk.embedding for chunk in chunks])

    async def search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        # Get query embedding
        query_embedding = (
            await self.embedding_model.embed_queries([Chunk(content=query, metadata=None, embedding=None)])
        )[0]

        # Calculate similarity scores
        similarity_scores = cosine_similarity([query_embedding], self.index)[0]
        top_indices = np.argsort(-similarity_scores)[:top_k]

        # Create search results
        results = []
        for rank, idx in enumerate(top_indices):
            result = SearchResult.from_chunk(chunk=self.chunks[idx], score=float(similarity_scores[idx]), rank=rank)
            results.append(result)

        return results


class SparseSearch(SearchAlgorithm):
    """BM25 search implementation."""

    def __init__(self, stopwords: Optional[List[str]] = None):
        self.chunks: List[Chunk] = []
        self.bm25 = None
        self.stopwords = stopwords or []

    async def build_index(self, chunks: List[Chunk], from_cache: bool = False) -> None:
        self.chunks = chunks
        corpus = [chunk.content for chunk in chunks]

        # Create and index BM25
        self.bm25 = bm25s.BM25(corpus=corpus, backend="numpy")
        self.bm25.index(
            corpus=bm25s.tokenize(texts=corpus, lower=True, stopwords=self.stopwords, show_progress=False),
            show_progress=False,
        )

    async def search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        if not self.bm25:
            raise ValueError("Index not built")

        # Get BM25 scores and documents
        results, scores = self.bm25.retrieve(
            bm25s.tokenize(query, lower=True, stopwords=self.stopwords, show_progress=False),
            k=top_k,
            backend_selection="numpy",
            show_progress=False,
        )

        # Map results back to chunks and create search results
        search_results = []
        for rank, (doc, score) in enumerate(zip(results[0], scores[0], strict=False)):
            chunk_idx = next(i for i, chunk in enumerate(self.chunks) if chunk.content == doc)
            result = SearchResult.from_chunk(chunk=self.chunks[chunk_idx], score=float(score), rank=rank)
            search_results.append(result)

        return search_results


class HybridSearch(SearchAlgorithm):
    """Combines multiple search algorithms using reciprocal rank fusion."""

    def __init__(self, algorithms: List[SearchAlgorithm], k: int = 60):
        self.algorithms = algorithms
        self.k = k

    async def build_index(self, chunks: List[Chunk], from_cache: bool = False) -> None:
        for algo in self.algorithms:
            await algo.build_index(chunks, from_cache)

    async def search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        # Get results from each algorithm
        all_results = await asyncio.gather(*[algo.search(query, top_k=top_k) for algo in self.algorithms])

        # Combine using reciprocal rank fusion
        chunk_scores: Dict[str, Tuple[Chunk, float]] = {}

        for results in all_results:
            for result in results:
                chunk = result.chunk
                chunk_hash = hashlib.sha256(chunk.content.encode()).hexdigest()
                rank = result.rank
                score = 1 / (rank + self.k)
                current_score = chunk_scores.get(chunk_hash, (chunk, 0))[1]
                chunk_scores[chunk_hash] = (chunk, current_score + score)

        # Sort by final scores
        sorted_chunks = sorted(chunk_scores.values(), key=lambda x: x[1], reverse=True)[:top_k]

        # Create final results
        return [
            SearchResult.from_chunk(chunk=chunk, score=score, rank=rank)
            for rank, (chunk, score) in enumerate(sorted_chunks)
        ]
