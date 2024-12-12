"""Data models for search functionality."""

import hashlib
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from pydantic import BaseModel
from pydantic import Field


def calculate_hash(text: str, algorithm: str = "sha256") -> str:
    """Calculate hash of text content."""
    digest = hashlib.new(algorithm)
    digest.update(text.encode("utf-8"))
    return digest.hexdigest()


class FileMetadata(BaseModel):
    """Metadata for a file."""

    file_name: str = Field(..., description="Name of the file")
    file_path: Path = Field(..., description="Path to the file")
    file_extension: str = Field(..., description="File extension")
    file_size: int = Field(..., description="File size in bytes")
    created: float = Field(..., description="Creation timestamp")
    last_modified: float = Field(..., description="Last modified timestamp")
    file_hash: str = Field(..., description="SHA256 hash of file content")


class TextMetadata(BaseModel):
    """Metadata for the full text content."""

    num_characters: int = Field(..., description="Total number of characters")
    num_words: int = Field(..., description="Total number of words")
    num_lines: int = Field(..., description="Total number of lines")
    num_chunks: int = Field(..., description="Total number of chunks")


class ChunkMetadata(BaseModel):
    """Metadata for a text chunk."""

    chunk_id: str = Field(..., description="Unique chunk identifier")
    chunk_number: int = Field(..., description="Chunk sequence number")
    chunk_start_index: int = Field(..., description="Start index in original text")
    chunk_end_index: int = Field(..., description="End index in original text")
    chunk_word_count: int = Field(..., description="Number of words in chunk")
    chunk_char_count: int = Field(..., description="Number of characters in chunk")
    is_last_chunk: bool = Field(..., description="Whether this is the last chunk")

    @classmethod
    def from_chunk_data(cls, chunk_data: Dict[str, Any]) -> "ChunkMetadata":
        """Create metadata from chunk information."""
        return cls(
            chunk_id=calculate_hash(chunk_data["content"]),
            chunk_number=chunk_data["number"],
            chunk_start_index=chunk_data["start"],
            chunk_end_index=chunk_data["end"],
            chunk_word_count=len(chunk_data["content"].split()),
            chunk_char_count=len(chunk_data["content"]),
            is_last_chunk=chunk_data["is_last"],
        )


class ChunkExtra(BaseModel):
    """Extra chunk metadata for ML/AI processing."""

    title: str = Field("", description="Generated title for the chunk")
    summary: str = Field("", description="Generated summary of the chunk")
    content_vector: List[float] = Field(default_factory=list, description="Content embedding vector")
    summary_vector: List[float] = Field(default_factory=list, description="Summary embedding vector")
    title_vector: List[float] = Field(default_factory=list, description="Title embedding vector")


class Chunk(BaseModel):
    """A chunk of text with its metadata."""

    content: str = Field(..., description="The chunk text content")
    file_metadata: Optional[FileMetadata] = None
    text_metadata: Optional[TextMetadata] = None
    chunk_metadata: Optional[ChunkMetadata] = None
    extra: Optional[ChunkExtra] = Field(None, description="Optional ML/AI metadata")
    embedding: Optional[List[float]] = Field(None, description="Vector embedding of chunk content")

    @classmethod
    def from_text(
        cls, content: str, file_path: Path, text_metadata: TextMetadata, chunk_data: Dict[str, Any]
    ) -> "Chunk":
        """Create a chunk from text content and metadata."""
        stats = file_path.stat()

        file_md = FileMetadata(
            file_name=file_path.name,
            file_path=file_path,
            file_extension=file_path.suffix,
            file_size=stats.st_size,
            created=stats.st_ctime,
            last_modified=stats.st_mtime,
        )

        chunk_md = ChunkMetadata.from_chunk_data(chunk_data)

        return cls(content=content, file_metadata=file_md, text_metadata=text_metadata, chunk_metadata=chunk_md)


class SearchResult(BaseModel):
    """A search result with score and chunk."""

    chunk: Chunk
    score: float
    rank: int
    start_line: int
    end_line: int

    @classmethod
    def from_chunk(cls, chunk: Chunk, score: float, rank: int) -> "SearchResult":
        """Create search result from chunk."""
        # Find line numbers for the chunk
        with open(chunk.file_metadata.file_path, "r", encoding="utf-8") as f:
            text = f.read()
            start_line = text.count("\n", 0, chunk.chunk_metadata.chunk_start_index) + 1
            end_line = text.count("\n", 0, chunk.chunk_metadata.chunk_end_index) + 1

        return cls(chunk=chunk, score=score, rank=rank, start_line=start_line, end_line=end_line)
