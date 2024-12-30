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

    def _get_file_metadata(self, file_path: Path, file_hash: str) -> FileMetadata:
        """Create FileMetadata with file hash."""
        stats = file_path.stat()
        return FileMetadata(
            file_name=file_path.name,
            file_path=file_path,
            file_extension=file_path.suffix,
            file_size=stats.st_size,
            created=stats.st_ctime,
            last_modified=stats.st_mtime,
            file_hash=file_hash,
        )

    def _analyze_file_changes(
        self, current_files: List[Path], file_hashes: dict
    ) -> tuple[set[Path], set[Path], set[Path]]:
        """Analyze which files are new, modified or deleted."""
        current_files_set = set(current_files)
        cached_files_set = set(file_hashes.keys())

        # Find new and deleted files
        new_files = current_files_set - cached_files_set
        deleted_files = cached_files_set - current_files_set

        # Check for modified files
        modified_files = set()
        for file_path in current_files_set & cached_files_set:
            if not file_path.exists():
                deleted_files = deleted_files | {file_path}
                new_files.discard(file_path)
                continue
            current_hash = self._get_file_hash(file_path)
            if current_hash != file_hashes.get(file_path):
                modified_files.add(file_path)

        for file_path in new_files.copy():
            if not file_path.exists():
                new_files.discard(file_path)
                deleted_files = deleted_files | {file_path}

        return new_files, modified_files, deleted_files

    def _remove_chunks_for_files(self, files_to_remove: set[Path]) -> None:
        """Remove chunks for given files."""
        if not files_to_remove:
            return

        # Remove chunks for specified files
        self.chunks = [chunk for chunk in self.chunks if chunk.file_metadata.file_path not in files_to_remove]

        # Remove hashes for those files
        for file_path in files_to_remove:
            self.file_hashes.pop(file_path, None)

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

    def reindex_needed(self, file_paths: List[Path]) -> List[Path]:
        """Check which files need reindexing based on changes and embedding status."""
        # Check if we have any embeddings
        chunks = self.storage.load("chunks") or []
        has_embeddings = all(bool(chunk) for chunk in chunks if chunk.embedding)

        if not has_embeddings:
            return file_paths

        # Check for file changes
        file_hashes = self.storage.load("file_hashes") or {}
        new_files, modified_files, _ = self._analyze_file_changes(file_paths, file_hashes)
        return list(new_files | modified_files)

    def _save_state(self) -> None:
        """Save current state."""
        self.storage.save("chunks", self.chunks)
        self.storage.save("file_hashes", self.file_hashes)

    def _get_file_hash(self, file_path: Path) -> str:
        """Calculate file hash."""
        return hashlib.sha256(file_path.read_bytes()).hexdigest()

    async def build_index(self, file_paths: List[Path], cache: bool = True, reindex: bool = True) -> None:
        """Build search index from files."""
        if not cache:
            # If not using cache, process all files as new
            self.chunks = []
            self.file_hashes = {}
            for file_path in file_paths:
                await self._process_file(file_path)
        else:
            # Load cached state
            self.chunks = self.storage.load("chunks") or []
            self.file_hashes = self.storage.load("file_hashes") or {}

            # Analyze which files changed
            new_files, modified_files, deleted_files = self._analyze_file_changes(file_paths, self.file_hashes)

            # Remove chunks for deleted and modified files
            self._remove_chunks_for_files(deleted_files | modified_files)

            # Process only new and modified files only if reindex is enabled
            if reindex:
                for file_path in new_files | modified_files:
                    await self._process_file(file_path)

        # Build search index and save state only after processing
        await self.search_algorithm.build_index(self.chunks, from_cache=True)
        self._save_state()

    async def _process_file(self, file_path: Path) -> None:
        """Process a single file."""
        text = file_path.read_text()
        file_hash = self._get_file_hash(file_path)
        self.file_hashes[file_path] = file_hash

        # Create metadata with file hash
        file_metadata = self._get_file_metadata(file_path, file_hash)

        # Generate and add chunks
        chunks = self.chunking_strategy.chunk_text(text, file_metadata)
        self.chunks.extend(chunks)

    async def add_files(self, file_paths: List[Path]) -> None:
        """Add new files to index."""
        # Analyze which files are truly new
        new_files, modified_files, _ = self._analyze_file_changes(file_paths)
        files_to_process = new_files | modified_files

        # Only process if there are new files
        if files_to_process:
            for file_path in files_to_process:
                await self._process_file(file_path)

            # Handle embeddings for new chunks if model exists
            if self.embedding_model:
                new_chunks = [c for c in self.chunks if not c.embedding]
                if new_chunks:
                    embeddings = await self.embedding_model.embed_document(new_chunks)
                    for chunk, embedding in zip(new_chunks, embeddings, strict=False):
                        chunk.embedding = embedding

            # Build index and save state
            await self.search_algorithm.build_index(self.chunks, from_cache=True)
            self._save_state()

    async def remove_files(self, file_paths: List[Path]) -> None:
        """Remove files from index."""
        paths_set = set(file_paths)
        self.chunks = [c for c in self.chunks if c.file_metadata.file_path not in paths_set]
        for path in file_paths:
            self.file_hashes.pop(path, None)

        await self.search_algorithm.build_index(self.chunks, from_cache=True)
        self._save_state()

    async def update_files(self, file_paths: List[Path]) -> None:
        """Update existing files in index."""
        # Get current state of files
        _, modified_files, _ = self._analyze_file_changes(file_paths)

        if modified_files:
            # Remove chunks for modified files
            self._remove_chunks_for_files(modified_files)

            # Process modified files
            for file_path in modified_files:
                await self._process_file(file_path)

            # Build index and save state
            await self.search_algorithm.build_index(self.chunks, from_cache=True)
            self._save_state()
