"""Main search engine interface."""

from pathlib import Path
from typing import List
from typing import Optional

from pluscoder.agents.event.base import EventEmitter
from pluscoder.search.algorithms import SearchAlgorithm
from pluscoder.search.chunking import ChunkingStrategy
from pluscoder.search.embeddings import EmbeddingModel
from pluscoder.search.index_manager import IndexManager
from pluscoder.search.models import SearchResult
from pluscoder.search.storage import IndexStorage


class SearchEngine:
    """Main search engine interface."""

    # Private class variable to store singleton instance
    __instance = None

    def __init__(
        self,
        chunking_strategy: ChunkingStrategy,
        search_algorithm: SearchAlgorithm,
        storage_dir: Optional[Path] = None,
        embedding_model: Optional[EmbeddingModel] = None,
    ) -> None:
        """Initialize search engine."""
        if not hasattr(self, "is_initialized"):
            storage_dir = storage_dir or Path.home() / ".pluscoder" / "search_index"
            storage_dir.mkdir(parents=True, exist_ok=True)
            self.storage = IndexStorage(storage_dir)
            self.chunking_strategy = chunking_strategy
            self.search_algorithm = search_algorithm
            self.embedding_model = embedding_model
            self.index_manager = None
            self.events = EventEmitter()
            self.is_initialized = True

    def __new__(cls, *args, **kwargs):
        """Ensure singleton instance."""
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    @classmethod
    def get_instance(cls) -> "SearchEngine":
        """Get singleton instance."""
        if cls.__instance is None or not getattr(cls.__instance, "is_initialized", False):
            msg = "SearchEngine not initialized. Use create() first."
            raise RuntimeError(msg)
        return cls.__instance

    @classmethod
    async def create(
        cls,
        chunking_strategy: ChunkingStrategy,
        search_algorithm: SearchAlgorithm,
        storage_dir: Optional[Path] = None,
        embedding_model: Optional[EmbeddingModel] = None,
    ) -> "SearchEngine":
        """Create and initialize SearchEngine asynchronously."""
        if cls.__instance and getattr(cls.__instance, "is_initialized", False):
            return cls.__instance

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
        await self.events.emit("indexing_started", files=file_paths)
        await self.index_manager.build_index(file_paths)
        await self.events.emit("indexing_completed")

    async def add_files(self, file_paths: List[Path]) -> None:
        """Add new files to the index."""
        await self.index_manager.add_files(file_paths)

    async def remove_files(self, file_paths: List[Path]) -> None:
        """Remove files from the index."""
        await self.index_manager.remove_files(file_paths)

    async def update_files(self, file_paths: List[Path]) -> None:
        """Update existing files in the index."""
        await self.index_manager.update_files(file_paths)

    def search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        """Search the index synchronously."""
        import asyncio

        try:
            # Get current event loop, create if none exists
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If inside event loop, create new one for sync execution
                loop = asyncio.new_event_loop()
            return loop.run_until_complete(self.index_manager.search_algorithm.search(query, top_k))
        except Exception as e:
            error_msg = "Search failed: " + str(e)
            raise RuntimeError(error_msg) from e
