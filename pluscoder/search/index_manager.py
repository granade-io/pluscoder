"""Index manager for search functionality."""

import hashlib
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Dict
from typing import List
from typing import Optional

from pluscoder.search.algorithms import SearchAlgorithm
from pluscoder.search.chunking import ChunkingStrategy
from pluscoder.search.embeddings import EmbeddingModel
from pluscoder.search.models import FileMetadata
from pluscoder.search.storage import IndexStorage

if TYPE_CHECKING:
    from pluscoder.search.models import Chunk


class IndexManager:
    """Manages the creation and updates of search indices."""

    def __init__(
        self,
        chunking_strategy: ChunkingStrategy,
        search_algorithm: SearchAlgorithm,
        storage: IndexStorage,
        embedding_model: Optional[EmbeddingModel] = None,
    ):
        self.chunking_strategy = chunking_strategy
        self.search_algorithm = search_algorithm
        self.embedding_model = embedding_model
        self.storage = storage
        self.chunks: "List[Chunk]" = []
        self.file_hashes: Dict[Path, str] = {}

    @classmethod
    async def create(
        cls,
        chunking_strategy: ChunkingStrategy,
        search_algorithm: SearchAlgorithm,
        storage: IndexStorage,
        embedding_model: Optional[EmbeddingModel] = None,
    ) -> "IndexManager":
        """Create and build IndexManager asynchronously."""
        return cls(
            chunking_strategy=chunking_strategy,
            search_algorithm=search_algorithm,
            storage=storage,
            embedding_model=embedding_model,
        )

    def _save_state(self) -> None:
        """Save current state."""
        self.storage.save("chunks", self.chunks)
        self.storage.save("file_hashes", self.file_hashes)

    def _get_file_hash(self, file_path: Path) -> str:
        """Calculate file hash."""
        return hashlib.sha256(file_path.read_bytes()).hexdigest()

    async def build_index(self, file_paths: List[Path], cache: bool = True) -> None:
        """Build search index from files."""

        if cache:
            self.chunks = self.storage.load("chunks") or []
            self.file_hashes = self.storage.load("file_hashes") or {}

            if self.chunks and self.file_hashes:
                await self.search_algorithm.build_index(self.chunks)
                return

        self.chunks = []
        self.file_hashes = {}

        for file_path in file_paths:
            await self._process_file(file_path)

        if self.embedding_model and self.chunks:
            embeddings = await self.embedding_model.embed_chunks(self.chunks)
            for chunk, embedding in zip(self.chunks, embeddings, strict=False):
                chunk.embedding = embedding

        await self.search_algorithm.build_index(self.chunks)
        self._save_state()

    async def _process_file(self, file_path: Path) -> None:
        """Process a single file."""
        text = file_path.read_text()
        file_hash = self._get_file_hash(file_path)
        self.file_hashes[file_path] = file_hash

        file_metadata = FileMetadata(
            file_name=file_path.name,
            file_path=file_path,
            file_extension=file_path.suffix,
            file_size=file_path.stat().st_size,
            created=file_path.stat().st_ctime,
            last_modified=file_path.stat().st_mtime,
        )
        chunks = self.chunking_strategy.chunk_text(text, file_metadata)
        self.chunks.extend(chunks)

    async def add_files(self, file_paths: List[Path]) -> None:
        """Add new files to index."""
        for file_path in file_paths:
            if file_path not in self.file_hashes:
                await self._process_file(file_path)

        if self.embedding_model:
            new_chunks = [c for c in self.chunks if not c.embedding]
            if new_chunks:
                embeddings = await self.embedding_model.embed_chunks(new_chunks)
                for chunk, embedding in zip(new_chunks, embeddings, strict=False):
                    chunk.embedding = embedding

        await self.search_algorithm.build_index(self.chunks)
        self._save_state()

    async def remove_files(self, file_paths: List[Path]) -> None:
        """Remove files from index."""
        paths_set = set(file_paths)
        self.chunks = [c for c in self.chunks if c.file_metadata.file_path not in paths_set]
        for path in file_paths:
            self.file_hashes.pop(path, None)

        await self.search_algorithm.build_index(self.chunks)
        self._save_state()

    async def update_files(self, file_paths: List[Path]) -> None:
        """Update existing files in index."""
        await self.remove_files(file_paths)
        await self.add_files(file_paths)
