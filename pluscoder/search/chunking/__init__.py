"""Text chunking strategies implementation."""

from abc import ABC
from abc import abstractmethod
from pathlib import Path
from typing import List

import tiktoken

from pluscoder.search.models import Chunk
from pluscoder.search.models import ChunkMetadata
from pluscoder.search.models import FileMetadata
from pluscoder.search.models import TextMetadata


class ChunkingStrategy(ABC):
    """Abstract base class for text chunking strategies."""

    @abstractmethod
    def chunk_text(self, text: str, file_metadata: FileMetadata) -> List[Chunk]:
        """Chunk text into smaller pieces."""


class CharacterBasedChunking(ChunkingStrategy):
    """Character-based chunking implementation."""

    def __init__(self, chunk_size: int = 1024, overlap: int = 128):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_text(self, text: str, file_metadata: FileMetadata) -> List[Chunk]:
        # Create text metadata
        text_metadata = TextMetadata(
            num_characters=len(text),
            num_words=len(text.split()),
            num_lines=text.count("\n") + 1,
            num_chunks=0,  # Will be updated after chunking
        )

        chunks = []
        start = 0
        chunk_number = 0

        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            content = text[start:end]

            chunk_data = {
                "content": content,
                "number": chunk_number,
                "start": start,
                "end": end,
                "is_last": end >= len(text),
            }

            chunk = Chunk(
                content=content,
                file_metadata=file_metadata,
                text_metadata=text_metadata,
                chunk_metadata=ChunkMetadata.from_chunk_data(chunk_data),
            )
            chunks.append(chunk)

            start += self.chunk_size - self.overlap
            chunk_number += 1

        # Update num_chunks in text_metadata for all chunks
        text_metadata.num_chunks = len(chunks)
        for chunk in chunks:
            chunk.text_metadata = text_metadata

        return chunks


class TokenBasedChunking(ChunkingStrategy):
    """Token-based chunking implementation."""

    def __init__(self, chunk_size: int = 512, overlap: int = 64, model: str = "gpt2"):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.tokenizer = tiktoken.get_encoding(model)

    def chunk_text(self, text: str, file_metadata: FileMetadata) -> List[Chunk]:
        # Create text metadata
        text_metadata = TextMetadata(
            num_characters=len(text),
            num_words=len(text.split()),
            num_lines=text.count("\n") + 1,
            num_chunks=0,  # Will be updated after chunking
        )

        chunks = []
        tokens = self.tokenizer.encode(text, allowed_special=set(), disallowed_special="all")

        start_token = 0
        chunk_number = 0

        while start_token < len(tokens):
            end_token = min(start_token + self.chunk_size, len(tokens))
            chunk_tokens = tokens[start_token:end_token]
            content = self.tokenizer.decode(chunk_tokens, errors="replace")

            # Find character positions
            prefix = self.tokenizer.decode(tokens[:start_token])
            start_char = len(prefix)
            end_char = start_char + len(content)

            chunk_data = {
                "content": content,
                "number": chunk_number,
                "start": start_char,
                "end": end_char,
                "is_last": end_token >= len(tokens),
            }

            chunk = Chunk(
                content=content,
                file_metadata=file_metadata,
                text_metadata=text_metadata,
                chunk_metadata=ChunkMetadata.from_chunk_data(chunk_data),
            )
            chunks.append(chunk)

            start_token += self.chunk_size - self.overlap
            chunk_number += 1

        # Update num_chunks in text_metadata for all chunks
        text_metadata.num_chunks = len(chunks)
        for chunk in chunks:
            chunk.text_metadata = text_metadata

        return chunks
