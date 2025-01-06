"""Main search engine interface."""

from pathlib import Path
from typing import List
from typing import Optional

from pluscoder.agents.event.config import event_emitter
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
            self.storage = IndexStorage(storage_dir, getattr(embedding_model, "model_name", None))
            self.chunking_strategy = chunking_strategy
            self.search_algorithm = search_algorithm
            self.embedding_model = embedding_model
            self.index_manager = None
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
            return None
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

    def _is_indexable_file(self, file_path: Path) -> bool:
        """Check if file should be indexed based on extension."""
        text_extensions = {
            # Code files
            ".py",
            ".js",
            ".jsx",
            ".ts",
            ".java",
            ".c",
            ".cpp",
            ".h",
            ".hpp",
            ".cs",
            ".rb",
            ".php",
            ".go",
            ".rs",
            ".swift",
            ".kt",
            ".scala",
            # Text files
            ".md",
            ".txt",
            ".json",
            ".yml",
            ".yaml",
            ".xml",
            ".html",
            ".css",
            ".sql",
            ".sh",
            ".bash",
            ".env",
            ".ini",
            ".cfg",
            ".conf",
            # Documentation
            ".rst",
            ".adoc",
            ".tex",
        }
        return file_path.suffix.lower() in text_extensions

    async def build_index(self, file_paths: List[Path], reindex: bool = True) -> None:
        """Build or rebuild the search index."""
        # Filter only indexable files
        indexable_files = [f for f in file_paths if self._is_indexable_file(f)]

        await self.index_manager.build_index(indexable_files, reindex)
        await event_emitter.emit("indexing_completed")

    async def add_files(self, file_paths: List[Path]) -> None:
        """Add new files to the index."""
        # Filter only indexable files
        indexable_files = [f for f in file_paths if self._is_indexable_file(f)]

        for file_path in indexable_files:
            await self.index_manager.add_files([file_path])
            await event_emitter.emit("indexing_progress", {"file_processed": str(file_path)})

        await event_emitter.emit("indexing_completed")

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
            loop = asyncio.get_running_loop()
            # If exists, run in current loop
            return loop.create_task(self.index_manager.search_algorithm.search(query, top_k))
        except RuntimeError:
            # If no loop exists, create new one
            return asyncio.run(self.index_manager.search_algorithm.search(query, top_k))
        except Exception as e:
            error_msg = "Search failed: " + str(e)
            raise RuntimeError(error_msg) from e

    async def async_search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        try:
            return await self.index_manager.search_algorithm.search(query, top_k)
        except Exception as e:
            error_msg = "Search failed: " + str(e)
            raise RuntimeError(error_msg) from e
