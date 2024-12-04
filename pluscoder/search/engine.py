"""Main search engine interface."""

from pathlib import Path
from typing import List
from typing import Optional

from pluscoder.search.algorithms import SearchAlgorithm
from pluscoder.search.chunking import ChunkingStrategy
from pluscoder.search.embeddings import EmbeddingModel
from pluscoder.search.index_manager import IndexManager
from pluscoder.search.models import SearchResult
from pluscoder.search.storage import IndexStorage


class SearchEngine:
    """Main search engine interface."""

    def __init__(
        self,
        chunking_strategy: ChunkingStrategy,
        search_algorithm: SearchAlgorithm,
        storage_dir: Optional[Path] = None,
        embedding_model: Optional[EmbeddingModel] = None,
    ):
        storage_dir = storage_dir or Path.home() / ".pluscoder" / "search_index"
        self.storage = IndexStorage(storage_dir)
        self.chunking_strategy = chunking_strategy
        self.search_algorithm = search_algorithm
        self.embedding_model = embedding_model
        self.index_manager = None

    @classmethod
    async def create(
        cls,
        chunking_strategy: ChunkingStrategy,
        search_algorithm: SearchAlgorithm,
        storage_dir: Optional[Path] = None,
        embedding_model: Optional[EmbeddingModel] = None,
    ) -> "SearchEngine":
        """Create and initialize SearchEngine asynchronously."""
        instance = cls(
            chunking_strategy=chunking_strategy,
            search_algorithm=search_algorithm,
            storage_dir=storage_dir,
            embedding_model=embedding_model,
        )
        instance.index_manager = await IndexManager.create(
            chunking_strategy=chunking_strategy,
            search_algorithm=search_algorithm,
            embedding_model=embedding_model,
            storage=instance.storage,
        )
        return instance

    async def build_index(self, file_paths: List[Path]) -> None:
        """Build or rebuild the search index."""
        await self.index_manager.build_index(file_paths)

    async def add_files(self, file_paths: List[Path]) -> None:
        """Add new files to the index."""
        await self.index_manager.add_files(file_paths)

    async def remove_files(self, file_paths: List[Path]) -> None:
        """Remove files from the index."""
        await self.index_manager.remove_files(file_paths)

    async def update_files(self, file_paths: List[Path]) -> None:
        """Update existing files in the index."""
        await self.index_manager.update_files(file_paths)

    async def search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        """Search the index."""
        return await self.index_manager.search_algorithm.search(query, top_k)
