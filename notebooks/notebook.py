# %% [markdown] ## Imports and Constants

import asyncio
import functools
import hashlib
import itertools
import json
import logging
import os
import re
import traceback
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import AbstractSet
from typing import Any
from typing import Callable
from typing import Collection
from typing import Generator
from typing import Iterable
from typing import Literal
from typing import NamedTuple
from typing import Sequence
from typing import TypeVar

import anthropic
import bm25s
import cohere
import numpy as np
import numpy.typing as npt
import tiktoken
from git import Repo
from google.cloud import discoveryengine_v1 as discoveryengine
from pydantic import BaseModel
from pydantic import Field
from rich.console import Console
from rich.syntax import Syntax
from sklearn.metrics import pairwise_distances
from sklearn.metrics.pairwise import cosine_similarity
from tqdm.auto import tqdm

from pluscoder.config.config import config
from pluscoder.repo import Repository

try:
    from rich import print as pprint
except ImportError:
    from pprint import pprint

assert pprint is not None  # noqa: S101

T = TypeVar("T")

logger = logging.getLogger(__name__)

settings = config


co: cohere.AsyncClient = cohere.AsyncClient(
    api_key=os.getenv(
        key="COHERE_API_KEY",
        default=getattr(settings, "COHERE_API_KEY", None) or "",
    ),
)

# constants for error messages
_UNEXPECTED_EMBEDDINGS_FORMAT_ERROR_MESSAGE = "Unexpected embeddings format"
_COHERE_EMBEDDING_FAILED_ERROR_MESSAGE = "Cohere embedding failed with error: %s"
_QUERY_MUST_BE_STRING_ERROR_MESSAGE = "Query must be a string"

#             model                     dimensions      max tokens (context length)        modality                             similarity metric
#       embed-english-v3.0                 1024                  512                     Text, Images       Cosine Similarity, Dot Product Similarity, Euclidean Distance
#       embed-multilingual-v3.0            1024                  512                     Text, Images       Cosine Similarity, Dot Product Similarity, Euclidean Distance
#       embed-english-light-v3.0            384                  512                     Text, Images       Cosine Similarity, Dot Product Similarity, Euclidean Distance
#       embed-multilingual-light-v3.0       384                  512                     Text, Images       Cosine Similarity, Dot Product Similarity, Euclidean Distance

#         embedding types               dimensions     memory saving                 description
#             float                        1024             1x              float32 embeddings with 4 bytes per dimension
#             int8                         1024             4x              signed int8 embeddings in the range [-128, 127]. 1 byte per dimension
#             uint8                        1024             4x              unsigned int8 embeddings in the range [0, 255]. 1 byte per dimension
#             binary                        128             32x             one bit per dimension. 8 bits are packaged to one int8 byte. So a 1024 dimensional embedding will become 128 int8-values. Embeddings must be compared with hamming distance.
#             ubinary                       128             32x             one bit per dimension. 8 bits are packaged to one uint8 byte. So a 1024 dimensional embedding will become 128 uint8-values. Embeddings must be compared with hamming distance.


EmbedModel = (
    Any
    | Literal[
        "embed-english-v3.0",
        "embed-multilingual-v3.0",
        "embed-english-light-v3.0",
        "embed-multilingual-light-v3.0",
    ]
)

EMBEDDING_MODEL: EmbedModel = "embed-english-v3.0"
EMBEDDING_TYPE: cohere.types.embedding_type.EmbeddingType = "binary"  # "ubinary"

CHUNK_SIZE: Literal[512] = 512
CHUNK_OVERLAP: Literal[64] = 64

# list of tuples of stopwords for different languages
_STOPWORD_LISTS = (
    bm25s.stopwords.STOPWORDS_EN,
    bm25s.stopwords.STOPWORDS_EN_PLUS,
    # bm25s.stopwords.STOPWORDS_GERMAN,
    # bm25s.stopwords.STOPWORDS_DUTCH,
    # bm25s.stopwords.STOPWORDS_FRENCH,
    bm25s.stopwords.STOPWORDS_SPANISH,
    # bm25s.stopwords.STOPWORDS_PORTUGUESE,
    # bm25s.stopwords.STOPWORDS_ITALIAN,
    # bm25s.stopwords.STOPWORDS_RUSSIAN,
    # bm25s.stopwords.STOPWORDS_SWEDISH,
    # bm25s.stopwords.STOPWORDS_NORWEGIAN,
    # bm25s.stopwords.STOPWORDS_CHINESE,
)
UNIQUE_STOPWORDS_LIST = list(set(itertools.chain.from_iterable(_STOPWORD_LISTS)))

TOP_K_DENSE = 10  # 5
TOP_K_SPARSE = 10  # 50
TOP_K_HYBRID = min(
    max(TOP_K_DENSE, TOP_K_SPARSE),
    5,
)


# cache files for the TikToken library
def download_tiktoken_data() -> None:
    # This will trigger the download and caching of the necessary files
    _ = tiktoken.get_encoding(encoding_name="o200k_base")
    _ = tiktoken.get_encoding(encoding_name="cl100k_base")
    _ = tiktoken.get_encoding(encoding_name="gpt2")


print("Downloading TikToken data (or loading from cache) ...")
download_tiktoken_data()
print("TikToken data downloaded (or loaded from cache)")

# %% [markdown] ## Cohere Embeddings and Vector Retrieval Example

query: str = "Who was Alan Turing?"

documents: list[str] = [
    # Most relevant
    "Alan Turing invented the concept of the Turing machine, which became the foundation of computer science and computational theory.",
    "During WWII, Turing's cryptanalysis work at Bletchley Park helped break the German Enigma code machine.",
    # Unrelated documents
    "The Great Barrier Reef is the world's largest coral reef system, stretching over 2,300 kilometers off Australia's coast.",
    "In 1969, Neil Armstrong became the first human to walk on the Moon during the Apollo 11 mission.",
    "The Renaissance was a period of cultural, artistic, and scientific revival that began in Italy in the late 14th century.",
    "Photosynthesis is the process by which plants convert light energy into chemical energy to produce glucose.",
    "Vincent van Gogh painted 'The Starry Night' in 1889 while at the Saint-Paul-de-Mausole asylum.",
    "The Amazon rainforest produces about 20% of Earth's oxygen and is home to millions of different species.",
    "The Great Wall of China is over 21,000 kilometers long and was built over several centuries.",
    "Mount Everest, the highest peak on Earth, reaches an elevation of 8,848 meters above sea level.",
]


# %%


async def _embed(
    texts: str | list[str],
    model: EmbedModel,
    input_type: cohere.types.embed_input_type.EmbedInputType,
    embedding_types: list[cohere.types.embedding_type.EmbeddingType],
    truncate: cohere.types.embed_request_truncate.EmbedRequestTruncate | None = None,
) -> cohere.types.embed_by_type_response_embeddings.EmbedByTypeResponseEmbeddings:
    try:
        response: cohere.types.embed_response.EmbedResponse
        response = await co.embed(
            texts=texts if isinstance(texts, list) else [texts],
            model=model,
            input_type=input_type,
            embedding_types=embedding_types,
            truncate=truncate,
        )

        if isinstance(response.embeddings, list):
            logger.error(_UNEXPECTED_EMBEDDINGS_FORMAT_ERROR_MESSAGE)
            raise ValueError(_UNEXPECTED_EMBEDDINGS_FORMAT_ERROR_MESSAGE)

        return response.embeddings

    except Exception as exc:
        logger.exception(_COHERE_EMBEDDING_FAILED_ERROR_MESSAGE, exc)
        raise


async def _generate_embedding(
    texts: str | list[str],
    model: EmbedModel,
    input_type: cohere.types.embed_input_type.EmbedInputType,
    embedding_type: cohere.types.embedding_type.EmbeddingType,
    truncate: cohere.types.embed_request_truncate.EmbedRequestTruncate | None = None,
):
    emb = await _embed(
        texts=texts,
        model=model,
        input_type=input_type,
        embedding_types=[embedding_type],
        truncate=truncate,
    )

    dtype_map: dict[cohere.types.embedding_type.EmbeddingType, npt.DTypeLike] = {
        "float": np.float32,  # 1024 dimensions
        "int8": np.int8,  # 1024 dimensions
        "uint8": np.uint8,  # 1024 dimensions
        "binary": np.int8,  # 128 dimensions
        "ubinary": np.uint8,  # 128 dimensions
    }

    return np.asarray(getattr(emb, embedding_type), dtype=dtype_map[embedding_type])


async def generate_query_embedding(
    query: str | list[str],
    model: EmbedModel,
    embedding_type: cohere.types.embedding_type.EmbeddingType,
    truncate: cohere.types.embed_request_truncate.EmbedRequestTruncate | None = None,
) -> np.ndarray:
    """Generate embeddings for search queries."""
    texts = query
    input_type: Literal["search_query"] = "search_query"
    return await _generate_embedding(
        texts=texts,
        model=model,
        input_type=input_type,
        embedding_type=embedding_type,
        truncate=truncate,
    )


async def generate_document_embeddings(
    documents: list[str],
    model: EmbedModel,
    embedding_type: cohere.types.embedding_type.EmbeddingType,
    truncate: cohere.types.embed_request_truncate.EmbedRequestTruncate | None = None,
) -> np.ndarray:
    """Generate embeddings for documents."""
    texts = documents
    input_type: Literal["search_document"] = "search_document"
    return await _generate_embedding(
        texts=texts,
        model=model,
        input_type=input_type,
        embedding_type=embedding_type,
        truncate=truncate,
    )


class VectorRetrievalResult(NamedTuple):
    """Named tuple for vector retrieval results."""

    scores: npt.NDArray[np.intp]
    """The similarity scores between the query and each item in the index."""

    indices: npt.NDArray[np.intp]
    """The indices of the top-k most similar items in the index to the query."""


def hamming_similarity(
    X: npt.NDArray[Any],  # noqa: N803,
    Y: npt.NDArray[Any] | None = None,  # noqa: N803
    n_jobs: int | None = None,
) -> npt.NDArray[Any]:
    """Compute the Hamming similarity matrix from a vector array X and optional Y."""
    # REF: https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.distance.hamming.html
    return 1 - pairwise_distances(X=X, Y=Y, metric="hamming", n_jobs=n_jobs, force_all_finite=True)


# NOTE: Use "hamming" for packed binary embeddings (e.g. "ubinary" or "binary") and "cosine" for non-packed embeddings (e.g. "float", "int8", "uint8")
async def vector_retreival(
    query: str,
    top_k: int = 5,
    vector_index: npt.NDArray[Any] | None = None,  # np.uint8
    embedding_type: cohere.types.embedding_type.EmbeddingType = "ubinary",
    *,
    verbose: bool = True,
) -> VectorRetrievalResult:
    """
    Retrieve the top-k most similar items from an index based on a query, using a similarity metric.

    Args:
        query: The query string to search for.
        top_k: The number of top similar items to retrieve. Defaults to 5.
        vector_index: The index array containing embeddings to search against. Defaults to None.

    Returns:
        A tuple containing the similarity scores and indices of the top-k most similar items.
    """
    # n is the number of items in the index
    # m is the number of queries (m = 1 for a single query)
    # d is the number of dimensions in the embedding
    # k is the number of top similar items to retrieve

    # query embeddings shape : (m, d) where m = 1
    # index embeddings shape : (n, d)

    # the similarity scores between the query and each item in the index
    # similarity scores (m, n) where m = 1

    # indices of the top-k most similar items in the index to the query
    # indices shape : (m, k) where m = 1

    # embeddings dtype is given by the embedding_type ( e.g. for "ubinary" is np.uint8 )
    if not isinstance(query, str) or isinstance(query, list):
        logger.error(_QUERY_MUST_BE_STRING_ERROR_MESSAGE)
        raise ValueError(_QUERY_MUST_BE_STRING_ERROR_MESSAGE)

    similarity_metric: Literal["cosine", "hamming"] = "hamming" if embedding_type in {"binary", "ubinary"} else "cosine"

    similarity_function = {
        "cosine": functools.partial(cosine_similarity, dense_output=True),
        "hamming": functools.partial(hamming_similarity, n_jobs=-1),
    }[similarity_metric]

    query_embedding = await generate_query_embedding(
        query=query,
        model=EMBEDDING_MODEL,
        embedding_type=embedding_type,
    )

    similarity_scores = similarity_function(X=query_embedding, Y=vector_index)

    if verbose:
        print(f" similarity_metric: {similarity_metric} ".center(80, "*"))

        print()
        print()
        print("BEFORE: similarity_scores".center(80, "*"))
        print(similarity_scores.shape)
        print(similarity_scores.dtype)
        print("*" * 80)
        pprint(similarity_scores)
        print("*" * 80)
        print()
        print()

    # get the top-k most similar items
    indices = np.argsort(a=-similarity_scores)[:top_k]

    if verbose:
        assert vector_index is not None  # noqa: S101

        print("query_embedding".center(80, "*"))
        print(query_embedding.shape)
        print(query_embedding.dtype)
        print("-" * 80)
        pprint(query_embedding)
        print("-" * 80)

        print("vector_index".center(80, "*"))
        print(vector_index.shape)
        print(vector_index.dtype)
        print("-" * 80)
        pprint(vector_index)
        print("-" * 80)

        print("top_k".center(80, "*"))
        print(top_k)
        print("-" * 80)

        print("similarity_scores".center(80, "*"))
        print(similarity_scores.shape)
        print(similarity_scores.dtype)
        print("-" * 80)
        pprint(similarity_scores)
        print("-" * 80)

        print("indices".center(80, "*"))
        print(indices.shape)
        print(indices.dtype)
        print("-" * 80)
        pprint(indices)
        print("-" * 80)

    return VectorRetrievalResult(
        scores=similarity_scores,
        indices=indices,
    )


# embed the documents to create an index
doc_embeddings = await generate_document_embeddings(  # noqa: F704, PLE1142 # pyright: ignore
    documents=documents,
    model=EMBEDDING_MODEL,
    embedding_type=EMBEDDING_TYPE,
    truncate=None,
)

# retrieve the top-k most relevant documents based on the query
result = await vector_retreival(  # noqa: F704, PLE1142 # pyright: ignore
    query=query,
    top_k=TOP_K_DENSE,
    vector_index=doc_embeddings,
    embedding_type=EMBEDDING_TYPE,
)

similarity_scores = result.scores  # similarity scores between the query and each document in the index
indices = result.indices.flatten().tolist()  # indices of the top-k most similar documents to the query

# print the top k most relevant documents and their similarity scores
for idx in indices:
    print(f"id: {idx}")
    print(f"Document: {documents[idx]}")
    print(f"Similarity score: {similarity_scores[0][idx]:.4f}")
    print()


# %%


def create_chunks(  # naive fixed-size chunking
    document: str,
    *,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[str]:
    """Create chunks of text from a document using a naive fixed-size chunking."""
    return [document[i : i + chunk_size] for i in range(0, len(document), chunk_size - overlap)]


def __split_text_on_tokens(  # naive token-based fixed-size chunking
    *,
    text: str,
    tokens_per_chunk: int,
    chunk_overlap: int,
    encode: Callable[[str], list[int]],
    decode: Callable[[list[int]], str],
) -> list[str]:
    """Create chunks of text using naive token-based fixed-size chunking.

    Args:
        text: Text to split into chunks
        tokens_per_chunk: Maximum number of tokens per chunk
        chunk_overlap: Number of tokens to overlap between chunks
        encode: Function to convert text to token ids
        decode: Function to convert token ids back to text

    Returns:
        List of text chunks with specified overlap
    """
    input_ids = encode(text)
    return [
        decode(input_ids[i : i + tokens_per_chunk])
        for i in range(0, len(input_ids), tokens_per_chunk - chunk_overlap)
        if i < len(input_ids)
    ]


# REF: https://github.com/langchain-ai/langchain/blob/b509747c7f13c5cad2226e62a3c9d948664fa193/libs/text-splitters/langchain_text_splitters/base.py#L300-L311
# REF: https://github.com/langchain-ai/langchain/blob/b509747c7f13c5cad2226e62a3c9d948664fa193/libs/text-splitters/langchain_text_splitters/base.py#L314-L328
def split_text_on_tokens(  # naive token-based fixed-size chunking
    text: str,
    *,
    tokens_per_chunk: int,
    chunk_overlap: int,
    encode: Callable[[str], list[int]],
    decode: Callable[[list[int]], str],
) -> list[str]:
    """Create chunks of text using naive token-based fixed-size chunking.

    Args:
        text: Input text to split
        tokens_per_chunk: Maximum number of tokens per chunk
        chunk_overlap: Overlap in tokens between chunks
        encode: Function to encode text to token ids
        decode: Function to decode token ids to text

    Returns:
        List of text chunks
    """
    splits: list[str] = []
    input_ids = encode(text)
    start_idx = 0
    cur_idx = min(start_idx + tokens_per_chunk, len(input_ids))
    chunk_ids = input_ids[start_idx:cur_idx]

    while start_idx < len(input_ids):
        splits.append(decode(chunk_ids))
        if cur_idx == len(input_ids):
            break
        start_idx += tokens_per_chunk - chunk_overlap
        cur_idx = min(start_idx + tokens_per_chunk, len(input_ids))
        chunk_ids = input_ids[start_idx:cur_idx]

    return splits


encoding_name: str = "gpt2"
tokenizer: tiktoken.Encoding = tiktoken.get_encoding(encoding_name=encoding_name)


def encode_fn(text: str) -> list[int]:
    allowed_special: AbstractSet[str] | Literal["all"] = set()
    disallowed_special: Collection[str] | Literal["all"] = "all"
    return tokenizer.encode(
        text,
        allowed_special=allowed_special,
        disallowed_special=disallowed_special,
    )


def decode_fn(tokens: Sequence[int]) -> str:
    """
    Decodes a list of tokens into a string.
    WARNING: the default behaviour of this function is lossy,
    since decoded bytes are not guaranteed to be valid UTF-8.
    You can control this behaviour using the errors parameter,
    for instance, setting errors=strict.
    """
    return tokenizer.decode(tokens, errors="replace")


# 1 token ~ 4 characters
tokens_chunk_size: int = 32 // 4
tokens_chunk_overlap: int = tokens_chunk_size // 8

# 1 token ~ 4 characters
characters_chunk_size: int = tokens_chunk_size * 4
characters_chunk_overlap: int = tokens_chunk_overlap * 4

MAX_IDX_TO_PRINT = 3

print(" Naive fixed-size chunking ".upper().center(80, "*"))
for idx, document in enumerate(documents):
    chunks: list[str] = create_chunks(
        document=document,
        chunk_size=characters_chunk_size,
        overlap=characters_chunk_overlap,
    )
    print(f" Document {idx + 1} ".center(80, "-"))
    print(f"Number of chunks: {len(chunks)}")
    print("-" * 80)
    pprint(chunks)
    print("*" * 80)

    if idx == MAX_IDX_TO_PRINT:
        break

print(" Naive token-based fixed-size chunking ".upper().center(80, "*"))
for idx, document in enumerate(documents):
    chunks: list[str] = split_text_on_tokens(
        text=document,
        tokens_per_chunk=tokens_chunk_size,
        chunk_overlap=tokens_chunk_overlap,
        encode=encode_fn,
        decode=decode_fn,
    )
    print(f" Document {idx + 1} ".center(80, "-"))
    print(f"Number of chunks: {len(chunks)}")
    print("-" * 80)
    pprint(chunks)

    if idx == MAX_IDX_TO_PRINT:
        break


# %% [markdown] ## BM25 Search


def exception_to_string(exc: BaseException) -> str:
    """Generates a string that contains an exception plus stack frames based on an exception."""
    formatted = traceback.format_exception(exc)
    return "".join(formatted)


def is_file_empty(file: Path) -> bool:
    try:
        is_size_zero = file.stat().st_size == 0
        is_content_empty = file.read_text(encoding="utf-8").strip() == ""
        return is_size_zero or is_content_empty
    except Exception as exc:
        print(f"Warning: {exception_to_string(exc=exc)}")
        return False


_ROOT_DIR = Path(__file__).resolve().absolute().parent.parent


def get_root_path() -> Path:
    """Get the root path of the project."""
    return _ROOT_DIR


def get_tracked_files() -> list[str]:
    try:
        repo_exclude_files = [
            ".*.(png|jpg|jpeg|svg)",
        ]  # config.repo_exclude_files

        root_path = get_root_path()

        # Open the repository
        repo = Repo(
            path=root_path,
            search_parent_directories=True,
        )

        # Get all tracked files
        tracked_files = set(repo.git.ls_files().splitlines())

        # Get untracked files (excluding ignored ones)
        untracked_files = set(repo.git.ls_files(others=True, exclude_standard=True).splitlines())

        # Combine and sort the results
        all_files = sorted(tracked_files.union(untracked_files))

        # Filter out files based on repo_exclude_files patterns
        exclude_patterns = [re.compile(pattern) for pattern in repo_exclude_files]
        return [file for file in all_files if not any(pattern.match(file) for pattern in exclude_patterns)]

    except Exception as exc:
        print(
            f"An error occurred: {exc}",
            flush=True,
        )
        return []


# %%


def print_tree(files: Sequence[Path] | Iterable[Path]) -> None:
    """Print the files in a tree structure.

    Args:
        files: A list of file paths.
    """

    tree = {}
    for file in files:
        parts = file.parts
        current_level = tree
        for part in parts:
            if part not in current_level:
                current_level[part] = {}
            current_level = current_level[part]

    def print_tree_recursive(current_level: dict, prefix: str = "") -> None:
        for i, (key, subtree) in enumerate(current_level.items()):
            connector = "└── " if i == len(current_level) - 1 else "├── "
            print(f"{prefix}{connector}{key}")
            if subtree:
                new_prefix = prefix + ("    " if i == len(current_level) - 1 else "│   ")
                print_tree_recursive(current_level=subtree, prefix=new_prefix)

    print_tree_recursive(current_level=tree, prefix="")


def is_excluded(path: Path) -> bool:
    return any(
        (
            str(path.resolve().absolute().name).startswith("."),
            ".git" in path.parts,
            ".github" in path.parts,
            ".vscode" in path.parts,
            ".ipynb_checkpoints" in path.parts,
            ".pytest_cache" in path.parts,
            ".env" in path.parts,
        )
    )


# %%

if 1:
    _tracked_files: list[str] = Repository(repository_path=get_root_path()).get_tracked_files()
else:
    _tracked_files: list[str] = get_tracked_files()
tracked_files: list[str] = [get_root_path().joinpath(path).as_posix() for path in _tracked_files]

# NOTE: IGNORE NOTEBOOKS DIRECTORY OR FILES FOR NOW
tracked_files = [path for path in tracked_files if "notebooks" not in path]

# print_tree(files=[Path(path) for path in tracked_files])

# %%

file_path_list: list[Path] = sorted(
    (
        Path(path).resolve().absolute()
        for path in tracked_files
        if not is_excluded(path=Path(path).resolve().absolute())
        and Path(path).resolve().absolute().suffix == ".py"
        and (Path(path).resolve().absolute() != Path(__file__).resolve().absolute())
    ),
    key=lambda file: file.as_posix(),
)

print()
print("Root path:", get_root_path())
print()
print("Number of tracked files found    :", len(tracked_files), flush=True)
print()
print("Number of files to process       :", len(file_path_list), flush=True)
print()
print("Percentage of files to process   :", f"{len(file_path_list) / len(tracked_files) * 100:.2f}%", flush=True)
print()
print("Files to process:", flush=True)
print_tree(files=file_path_list)
print()


# %% [markdown] ## Text Chunking


def calculate_hash(text: str, algorithm: Literal["sha256", "sha512", "md5"] = "sha256") -> str:
    # MD5       :   128-bit hash (faster but less secure)
    # SHA-256   :   256-bit hash (medium speed and security)
    # SHA-512   :   512-bit hash (slower but more secure)

    # hash = hashlib.md5(self.content.encode("utf-8"), usedforsecurity=False).hexdigest()
    # hash = hashlib.sha256(self.content.encode("utf-8")).hexdigest()
    # hash = hashlib.sha512(self.content.encode("utf-8")).hexdigest()

    # Create a digest object based on the specified algorithm
    digest = hashlib.new(algorithm)

    # Update the digest with the text string's content
    digest.update(text.encode("utf-8"))

    # Get the hexadecimal representation of the checksum
    return digest.hexdigest()


class Chunk(BaseModel):
    """A chunk of text with metadata."""

    class Metadata(BaseModel):
        """Metadata for each chunk."""

        class FileMetadata(BaseModel):
            """Metadata for the file."""

            file_name: str
            """Name of the file."""

            file_path: str
            """Path to the file."""

            file_extension: str
            """File extension."""

            file_size: int
            """File size in bytes."""

            created: float
            """Creation timestamp (epoch time)."""

            last_modified: float
            """Last modified timestamp (epoch time)."""

        class TextMetadata(BaseModel):
            """Metadata for the text."""

            num_characters: int
            """Number of characters in the text."""

            num_words: int
            """Number of words in the text."""

            num_lines: int
            """Number of lines in the text."""

            num_chunks: int
            """Number of chunks in the text."""

        class ChunkMetadata(BaseModel):
            """Metadata for the chunk."""

            chunk_id: str
            """Unique id for the chunk (hash of the chunk content)"""

            chunk_number: int
            """Chunk number (relative to the document)"""

            chunk_start_index: int
            """Start character index of the chunk in the document."""

            chunk_end_index: int
            """End character index of the chunk in the document."""

            chunk_word_count: int
            """Number of words in the chunk."""

            chunk_char_count: int
            """Number of characters in the chunk."""

            is_last_chunk: bool
            """Whether the chunk is the last chunk in the document."""

        class Extra(BaseModel):
            title: str
            """Title of the chunk."""

            summary: str = ""
            """Summary of the chunk."""

            content_vector: list[float] = []
            """Vector representation of the content."""

            summary_vector: list[float] = []
            """Vector representation of the summary."""

            title_vector: list[float] = []
            """Vector representation of the title."""

        file: FileMetadata
        """Metadata for the file."""

        text: TextMetadata
        """Metadata for the text."""

        chunk: ChunkMetadata
        """Metadata for the chunk."""

    content: str
    """The content of the chunk."""

    metadata: Metadata
    """Metadata for the chunk."""

    hash: str | None = None
    """The hash of the chunk content."""


def extract_text_chunks_with_metadata(
    file_path: Path,
    chunking_function: Callable[[str], list[str]],
) -> list[Chunk]:
    path: Path = file_path.resolve().absolute()

    try:
        text = file_path.read_text(encoding="utf-8")
        chunks = chunking_function(text)

        file_metadata: Chunk.Metadata.FileMetadata = Chunk.Metadata.FileMetadata(
            file_name=path.name,
            file_path=str(path),
            file_extension=path.suffix,
            file_size=path.stat().st_size,
            created=path.stat().st_ctime,
            last_modified=path.stat().st_mtime,
        )

        text_metadata: Chunk.Metadata.TextMetadata = Chunk.Metadata.TextMetadata(
            num_characters=len(text),
            num_words=len(text.split()),
            num_lines=len(text.split("\n")),
            num_chunks=len(chunks),
        )

        return [
            Chunk(
                content=chunk,
                metadata=Chunk.Metadata(
                    file=file_metadata,
                    text=text_metadata,
                    chunk=Chunk.Metadata.ChunkMetadata(
                        # Hash the chunk content to generate a unique id
                        chunk_id=str(calculate_hash(text=chunk, algorithm="sha256")),
                        chunk_number=idx,
                        chunk_start_index=text.find(chunk),  # start character index
                        chunk_end_index=text.find(chunk) + len(chunk),  # end character index
                        chunk_word_count=len(chunk.split()),
                        chunk_char_count=len(chunk),
                        is_last_chunk=idx == len(chunks) - 1,
                    ),
                ),
            )
            for idx, chunk in enumerate(chunks)
        ]
    except Exception as exc:
        logger.warning("Error processing file: %s", path, exc_info=True)
        print(f"Warning: {exception_to_string(exc=exc)}", flush=True)
        return []


naive_fixed_size_chunking: Callable[[str], list[str]] = functools.partial(
    create_chunks,
    chunk_size=CHUNK_SIZE,
    overlap=CHUNK_OVERLAP,
)

naive_token_based_fixed_size_chunking: Callable[[str], list[str]] = functools.partial(
    split_text_on_tokens,
    tokens_per_chunk=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    encode=encode_fn,
    decode=decode_fn,
)


TOKEN_BASED = True
chunking_function: Callable[[str], list[str]] = (
    naive_token_based_fixed_size_chunking if TOKEN_BASED else naive_fixed_size_chunking
)


# TODO:(diegovalenzuelaiturra): split files into chunks should be non-blocking and parallel
def map_in_thread(
    func: Callable[[T], Any],
    iterable: Iterable[T],
    n_workers: int = 1,
) -> Generator[Any, None, None]:
    """Apply a function to an iterable using a thread pool executor.

    Args:
        func (Callable[[T], Any]): The function to apply.
        iterable (Iterable[T]): The input iterable.
        n_workers (int): The number of worker threads.

    Yields:
        Any: The results of applying the function to the iterable.

    """
    with ThreadPoolExecutor(max_workers=n_workers) as pool:
        yield from pool.map(func, iterable)


# cap the number of threads to avoid overloading the system
thread_count: int = int(os.environ.get("MAX_THREADS", 3))  # 1

results: list[Chunk] = []

for result in map_in_thread(
    func=functools.partial(
        extract_text_chunks_with_metadata,
        chunking_function=chunking_function,
    ),
    iterable=(Path(path) for path in file_path_list),
    n_workers=thread_count,
):
    results.extend(result)


print("Number of chunks:", len(results))


# %% [markdown]  # Keyword Extraction

# SOURCE: pluscoder/workflow.py

# Sample questions for the orchestration workflow
questions = [
    "What is the primary goal of this orchestration workflow, and how does it integrate with the broader application?",
    "What are the key responsibilities of each type of agent (e.g., DeveloperAgent, OrchestratorAgent, DomainExpertAgent), and how do they interact within the system?",
    "How does the XMLStreamParser handle the output parsing for the agents, and are there any specific formats it expects or produces?",
    "What kind of tools are defined in tools.base_tools, and what functionalities do these tools provide to the agents?",
    "How is state managed and updated within the orchestration process, especially in terms of message handling and task completion?",
    "What are the potential error-handling mechanisms in place if an agent fails to complete a task or returns an unexpected result?",
    "How does the system ensure that the accumulated token usage is correctly tracked and updated across different agent interactions?",
    "What considerations or limitations are there for running this orchestration process in terms of performance, scalability, and resource management?",
    "How does the orchestrator agent validate that a task is completed successfully, and what happens if the validation fails?",
    "What types of user commands can be handled by the handle_command function, and how do these commands modify the state or workflow?",
]

# Sample queries and corresponding instructions
queries = [
    "Where should I add a new agent configuration if I want to introduce a new type of agent, like a 'QA Agent'?",
    "Which part of the code handles task completion, and where can I add a log message to mark a checkpoint?",
    "How can I modify the user_router() function to ensure that the user is prompted for input at more stages during the workflow?",
    "What changes are needed to make the orchestration state persistent across different runs, and where should I implement state serialization and deserialization?",
    "Where should I add start_time and end_time attributes in the OrchestrationState, and how can I log the task duration in the _agent_node() function?",
    "How can I extend the handle_command() function to include additional user commands, and what parts of the code would be impacted?",
    "Which function should I modify to add extra validation checks for task completion, and how would that affect the workflow?",
    "Where should I place try-except blocks to ensure that unexpected exceptions during agent interactions are caught and logged?",
    "How do I update tools.base_tools and modify AgentConfig so that specific agents can use new specialized tools?",
    "What would be the best way to introduce an internal data exchange layer between agents, and which parts of _agent_node() and _orchestrator_agent_node() would I need to modify?",
    "What is the process for adding retry logic for tasks in the _orchestrator_agent_node(), and how can I maintain a retry counter in the OrchestrationState?",
    "How do I enhance the final summary generation in the _orchestrator_agent_node() to include detailed performance metrics and agent response data?",
]

# Sample instructions for the queries
instructions = [
    "Add a new AgentConfig for a new agent (e.g., 'QA Agent') in the build_agents() function.",
    "Insert io.console.log('Checkpoint reached after task completion') in the _orchestrator_agent_node() function where the task is marked as complete.",
    "Modify the user_router() function to introduce conditions that return user_input at key stages, such as before task delegation.",
    "Implement state serialization and deserialization logic before and after the run_workflow() function to ensure persistence.",
    "Add start_time and end_time attributes in the OrchestrationState and log the duration within the _agent_node() function.",
    "Expand the handle_command() function to parse and execute new custom commands based on user input.",
    "Extend the OrchestratorAgent.validate_current_task_completed() function to include additional validation checks.",
    "Add try-except blocks within the _agent_node() and _orchestrator_agent_node() functions to catch and log any raised exceptions.",
    "Update tools.base_tools and modify the AgentConfig to accept specialized tools for specific agents in the build_agents() function.",
    "Introduce an internal data exchange layer between agents and modify the logic in _agent_node() and _orchestrator_agent_node() to handle data sharing.",
    "Modify the _orchestrator_agent_node() function to include retry logic and maintain a retry counter in the OrchestrationState.",
    "Enhance the final summary generation logic in the _orchestrator_agent_node() function to include task performance and agent response metrics.",
]

# sample questions, queries, and instructions
questions = questions[:3]
queries = queries[:3]
instructions = instructions[:3]

# %%


client = anthropic.AsyncAnthropic()

# "Generate Key words for search, which will be related to user's query"


async def extract_keywords(query: str) -> str:
    system_prompt = """
You are a natural language processing specialist with expertise in text analysis, keyword extraction, and semantic understanding, possessing strong programming skills in JSON data structures and experience with query processing systems.
Your background includes working with information retrieval systems, semantic analysis, and text mining techniques, with a particular focus on query interpretation and keyword optimization.
Your task is to analyze a natural language user query and extract a comprehensive set of relevant keywords.
The extracted keywords should effectively represent:

1. Primary actions or verbs
2. Important nouns, entities, and proper names
3. Significant adjectives and descriptors
4. Domain-specific terminology
5. Temporal indicators (dates, time periods)
6. Location-related terms
7. Technical terms or jargon
8. Common variations and synonyms

Focus on identifying terms that are:
- Essential to understanding the query's intent
- Specific rather than generic
- Contextually relevant
- Useful for search and matching purposes

Exclude:
- Common stop words
- Articles and prepositions
- Generic terms that don't add meaning
- Redundant variations of the same concept

Format your response as a JSON object with a single key "keywords" containing an array of strings, where each string is a relevant keyword or phrase. Include synonyms.

Example format:
{{
    "keywords": ["keyword1", "keyword2", "keyword3"]
}}

"""

    query = "\n<QUERY>\n" + """{query}""".format(query=query) + "\n</QUERY>\n"

    message = await client.messages.create(  # pyright: ignore
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024 * 8,
        temperature=1,
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": query,
                    }
                ],
            }
        ],
    )

    return message.content[0].text


class KeywordExtractionResult(NamedTuple):
    query: str = Field(
        ...,
        description="The user query to extract keywords from.",
    )
    keywords: list[str] = Field(
        [],
        description="The extracted keywords from the query",
    )


messages = await asyncio.gather(  # noqa: PLE1142, F704 # pyright: ignore
    *[
        extract_keywords(
            query=query,
        )
        for query in instructions
    ]
)

keyword_extraction_result_list: list[KeywordExtractionResult] = []
for query, message in zip(instructions, messages, strict=True):
    try:
        keywords = json.loads(message)
        keywords = keywords.get("keywords", [])
        keywords = list(set(keywords))
    except json.JSONDecodeError as exc:
        keywords = json.loads(message.replace("```json", "").replace("```JSON", "").replace("```", ""))
        keywords = keywords.get("keywords", [])
        keywords = list(set(keywords))
    except Exception as exc:
        print(f"Query: {query}")
        print(f"Messsage: {message}")
        print(f"Error: {exc}")
        raise

    keyword_extraction_result = KeywordExtractionResult(
        query=query,
        keywords=keywords,
    )
    keyword_extraction_result_list.append(keyword_extraction_result)
    pprint(keyword_extraction_result)


# %% [markdown] ## Sparse Vector Search


def get_chunks_content(chunks: list[Chunk]) -> list[str]:
    return [chunk.content for chunk in chunks]


# Get the content of the chunks to use as the corpus
corpus: list[str] = get_chunks_content(chunks=results)

# Create the BM25 model and index the corpus
retriever = bm25s.BM25(corpus=corpus, backend="auto")
retriever.index(
    corpus=bm25s.tokenize(
        texts=corpus,
        lower=True,
        stopwords=UNIQUE_STOPWORDS_LIST,
    ),
)


def find_start_line_number(file_path: Path, start_index: int) -> int:
    with open(file_path, "r", encoding="utf-8") as file:
        text = file.read()
        return text.count("\n", 0, start_index) + 1


def find_end_line_number(file_path: Path, end_index: int) -> int:
    with open(file_path, "r", encoding="utf-8") as file:
        text = file.read()
        return text.count("\n", 0, end_index) + 1


# Query the corpus and get top-k results


def bm25_retreival(
    query: str,
    k: int,
    bm25_index: bm25s.BM25,
) -> list[int]:
    """
    Retrieve the top-k document indices based on the BM25 algorithm for a given query.

    Args:
        query: The search query string.
        k: The number of top documents to retrieve.
        bm25_index: The BM25 index object used for retrieval.
    Returns:
        A list of indices of the top-k documents that match the query.
    """

    results, scores = bm25_index.retrieve(bm25s.tokenize(query), k=k)

    return [corpus.index(doc) for doc in results[0]]


for kwe_result in keyword_extraction_result_list:
    query = kwe_result.query
    keywords = kwe_result.keywords

    print("".center(80, "$"), flush=True)
    pprint(" Query ".upper().center(80, "."), flush=True)
    print(query)
    pprint("".center(80, "."), flush=True)
    print()
    print(" Keywords ".upper().center(80, "."), flush=True)
    pprint(keywords, flush=True)
    print("".center(80, "."), flush=True)
    print()

    if not keywords:
        print("No keywords extracted. Using the query as is.", flush=True)
        _results, _scores = retriever.retrieve(
            bm25s.tokenize(query),
            k=TOP_K_SPARSE,
        )
    else:
        _results, _scores = retriever.retrieve(
            bm25s.tokenize(" ".join(keywords)),
            k=TOP_K_SPARSE,
        )

    # print(_results.shape)  # (1, TOP_K)
    # print(_scores.shape)  # (1, TOP_K)

    print("".center(80, "$"), flush=True)
    print("".center(80, "$"), flush=True)
    print("".center(80, "$"), flush=True)

    for idx, doc in enumerate(_results[0]):
        assert results[corpus.index(doc)].content == doc, f"Content mismatch for document: {doc}"  # noqa: S101
        print()
        print(
            f" Result {idx + 1} ".upper().center(80, "*"),
            flush=True,
        )
        print()
        print(
            f" Chunk Index {corpus.index(doc)} ".upper().center(80, "-"),
            flush=True,
        )
        print()
        pprint(
            f"Score : {_scores[0][idx]}".upper(),
            flush=True,
        )
        print(
            f"File Name: {results[corpus.index(doc)].metadata.file.file_name}",
            flush=True,
        )
        print()
        print(
            f"File Path: {results[corpus.index(doc)].metadata.file.file_path}",
            flush=True,
        )
        print(
            f"File Path (short): {Path(results[corpus.index(doc)].metadata.file.file_path).relative_to(get_root_path())}",
            flush=True,
        )
        print()
        print(
            "Reference: {file_path}:{chunk_start_line}:{chunk_end_line}".format(
                file_path=results[corpus.index(doc)].metadata.file.file_path,
                chunk_start_line=find_start_line_number(
                    file_path=Path(results[corpus.index(doc)].metadata.file.file_path),
                    start_index=results[corpus.index(doc)].metadata.chunk.chunk_start_index,
                ),
                chunk_end_line=find_end_line_number(
                    file_path=Path(results[corpus.index(doc)].metadata.file.file_path),
                    end_index=results[corpus.index(doc)].metadata.chunk.chunk_end_index,
                ),
            ),
            flush=True,
        )
        print()
        print(" Content ".upper().center(80, "-"), flush=True)
        print()
        Console().print(Syntax(doc, "python"))
        print()
        print(" Metadata ".upper().center(80, "-"), flush=True)
        print()
        pprint(results[corpus.index(doc)].metadata)
        print()
        print("-" * 80)

        if idx == 2:
            break

    print("".center(80, "$"), flush=True)
    print("".center(80, "$"), flush=True)
    print("".center(80, "$"), flush=True)


# %% [markdown] ## Dense Vector Search


print()
print()
print()
print()
print()
print()
pprint("".center(80, "@"), flush=True)
pprint("".center(80, "@"), flush=True)
pprint("".center(80, "@"), flush=True)
pprint("".center(80, "@"), flush=True)
pprint("".center(80, "@"), flush=True)
pprint("".center(80, "@"), flush=True)
pprint("".center(80, "@"), flush=True)
print()
print()
print()
print()
print()
print()

BATCH_SIZE = 92


async def batch_generate_document_embeddings(
    documents: list[str],
    model: EmbedModel,
    embedding_type: cohere.types.embedding_type.EmbeddingType,
    truncate: cohere.types.embed_request_truncate.EmbedRequestTruncate | None = None,
    *,
    time_to_wait: float = 60,
):
    # Split documents into batches
    batches = [documents[i : i + BATCH_SIZE] for i in range(0, len(documents), BATCH_SIZE)]
    embeddings = []

    for batch in tqdm(
        batches,
        desc="Generating embeddings",
        unit="batch",
        leave=False,
        total=len(batches),
    ):
        batch_embeddings = await generate_document_embeddings(
            documents=batch,
            model=model,
            embedding_type=embedding_type,
            truncate=truncate,
        )
        embeddings.append(batch_embeddings)
        await asyncio.sleep(time_to_wait)  # Yield control to the event loop

    # Concatenate all batch embeddings into a single ndarray
    return np.concatenate(embeddings, axis=0)


if BATCH_SIZE is None:
    # embed the documents to create an index
    doc_embeddings = await generate_document_embeddings(  # noqa: F704, PLE1142 # pyright: ignore
        documents=documents,
        model=EMBEDDING_MODEL,
        embedding_type=EMBEDDING_TYPE,
        truncate=None,
    )
else:
    doc_embeddings = await batch_generate_document_embeddings(  # noqa: F704, PLE1142 # pyright: ignore
        documents=documents,
        model=EMBEDDING_MODEL,
        embedding_type=EMBEDDING_TYPE,
        truncate=None,
        time_to_wait=60,
    )

documents = corpus


for kwe_result in keyword_extraction_result_list:
    query = kwe_result.query

    print("".center(80, "$"), flush=True)
    pprint(" Query ".upper().center(80, "."), flush=True)
    print(query)
    pprint("".center(80, "."), flush=True)
    print()

    # retrieve the top-k most relevant documents based on the query
    result = await vector_retreival(  # noqa: F704, PLE1142 # pyright: ignore
        query=query,
        top_k=TOP_K_DENSE,
        vector_index=doc_embeddings,
        embedding_type=EMBEDDING_TYPE,
        verbose=False,
    )

    similarity_scores = result.scores  # similarity scores between the query and each document in the index
    indices = result.indices.flatten().tolist()  # indices of the top-k most similar documents to the query

    print("".center(80, "$"), flush=True)
    print("".center(80, "$"), flush=True)
    print("".center(80, "$"), flush=True)

    # print the top k most relevant documents and their similarity scores
    for idx in indices:
        doc = documents[idx]
        assert results[corpus.index(doc)].content == doc, f"Content mismatch for document: {doc}"  # noqa: S101

        print()
        print(
            f" Result {idx + 1} ".upper().center(80, "*"),
            flush=True,
        )
        print()
        print(
            f" Chunk Index {corpus.index(doc)} ".upper().center(80, "-"),
            flush=True,
        )
        print()
        pprint(
            f"Score : {similarity_scores[0][idx]:.4f}".upper(),
            flush=True,
        )
        print()
        print(
            f"File Name: {results[corpus.index(doc)].metadata.file.file_name}",
            flush=True,
        )
        print()
        print(
            f"File Path: {results[corpus.index(doc)].metadata.file.file_path}",
            flush=True,
        )
        print(
            f"File Path (short): {Path(results[corpus.index(doc)].metadata.file.file_path).relative_to(get_root_path())}",
            flush=True,
        )
        print()
        print(
            "Reference: {file_path}:{chunk_start_line}:{chunk_end_line}".format(
                file_path=results[corpus.index(doc)].metadata.file.file_path,
                chunk_start_line=find_start_line_number(
                    file_path=Path(results[corpus.index(doc)].metadata.file.file_path),
                    start_index=results[corpus.index(doc)].metadata.chunk.chunk_start_index,
                ),
                chunk_end_line=find_end_line_number(
                    file_path=Path(results[corpus.index(doc)].metadata.file.file_path),
                    end_index=results[corpus.index(doc)].metadata.chunk.chunk_end_index,
                ),
            ),
            flush=True,
        )
        print()
        print(" Content ".upper().center(80, "-"), flush=True)
        print()
        Console().print(Syntax(doc, "python"))
        print()
        print(" Metadata ".upper().center(80, "-"), flush=True)
        print()
        pprint(results[corpus.index(doc)].metadata)
        print()
        print("-" * 80)

        if idx == 2:
            break

    print("".center(80, "$"), flush=True)
    print("".center(80, "$"), flush=True)
    print("".center(80, "$"), flush=True)


print()
print()
print()
print()
print()
print()
pprint("".center(80, "@"), flush=True)
pprint("".center(80, "@"), flush=True)
pprint("".center(80, "@"), flush=True)
pprint("".center(80, "@"), flush=True)
pprint("".center(80, "@"), flush=True)
pprint("".center(80, "@"), flush=True)
pprint("".center(80, "@"), flush=True)
print()
print()
print()
print()
print()
print()

# %% [markdown] ## Hybrid Search


def reciprocal_rank_fusion(
    *list_of_list_ranks_system,
    K: int = 60,  # noqa: N803
) -> tuple[list[tuple[int, float]], list[int]]:
    """
    Fuse rank from multiple IR systems using Reciprocal Rank Fusion.

    Args:
        * list_of_list_ranks_system: Ranked results from different IR system.
        K: A constant used in the RRF formula (default is 60).

    Returns:
        Tuple of list of sorted documents by score and sorted documents
    """
    # Dictionary to store RRF mapping
    rrf_map = defaultdict(float)

    # Calculate RRF score for each result in each list
    for rank_list in list_of_list_ranks_system:
        for rank, item in enumerate(rank_list, 1):
            rrf_map[item] += 1 / (rank + K)

    # Sort items based on their RRF scores in descending order
    sorted_items = sorted(rrf_map.items(), key=lambda x: x[1], reverse=True)

    # Return tuple of list of sorted documents by score and sorted documents
    return sorted_items, [item for item, score in sorted_items]


USE_QUERY_KEYWORDS = False

for kwe_result in keyword_extraction_result_list:
    query = kwe_result.query
    keywords = kwe_result.keywords

    print()
    print("".center(80, "$"), flush=True)
    print()
    pprint(f" Use Query Keywords : {USE_QUERY_KEYWORDS} ".upper().center(80, "."), flush=True)
    pprint(" Query ".upper().center(80, "."), flush=True)
    print(query)
    pprint("".center(80, "."), flush=True)
    print()

    print(" Keywords ".upper().center(80, "."), flush=True)
    pprint(keywords, flush=True)
    query_keywords = " ".join(keywords)
    query_keywords = query_keywords.strip().lower()
    pprint(" Query Keywords ".upper().center(80, "."), flush=True)
    print()
    print(query_keywords)
    print()
    pprint("".center(80, "."), flush=True)

    # ranked lists from different sources
    # source: vector search (dense)
    vector_top_k: list[int] = (
        (
            await vector_retreival(  # noqa: PLE1142, F704 # pyright: ignore
                query=query,
                top_k=TOP_K_DENSE,
                vector_index=doc_embeddings,
                embedding_type=EMBEDDING_TYPE,
                verbose=False,
            )
        )
        .indices.flatten()
        .tolist()
    )  # indices of the top-k most similar documents to the query

    # source: bm25 search (sparse)
    bm25_top_k = bm25_retreival(
        query=query_keywords if USE_QUERY_KEYWORDS else query,
        k=TOP_K_SPARSE,
        bm25_index=retriever,
    )

    # Combine the lists using RRF
    hybrid_top_k = reciprocal_rank_fusion(vector_top_k, bm25_top_k)
    hybrid_top_k[1]

    print("".center(80, "$"), flush=True)
    print("".center(80, "$"), flush=True)
    print("".center(80, "$"), flush=True)

    # NOTE: the reordering of the chunks based on the RRF score
    # print the top k most relevant documents
    for _idx, index in enumerate(hybrid_top_k[1]):
        doc = corpus[index]
        assert results[corpus.index(doc)].content == doc, f"Content mismatch for document: {doc}"  # noqa: S101

        print()
        print(
            f" Chunk Index {corpus.index(doc)} ".upper().center(80, "-"),
            flush=True,
        )
        print()
        print(
            f"File Name: {results[corpus.index(doc)].metadata.file.file_name}",
            flush=True,
        )
        print()
        print(
            f"File Path: {results[corpus.index(doc)].metadata.file.file_path}",
            flush=True,
        )
        print(
            f"File Path (short): {Path(results[corpus.index(doc)].metadata.file.file_path).relative_to(get_root_path())}",
            flush=True,
        )
        print()
        print(
            "Reference: {file_path}:{chunk_start_line}:{chunk_end_line}".format(
                file_path=results[corpus.index(doc)].metadata.file.file_path,
                chunk_start_line=find_start_line_number(
                    file_path=Path(results[corpus.index(doc)].metadata.file.file_path),
                    start_index=results[corpus.index(doc)].metadata.chunk.chunk_start_index,
                ),
                chunk_end_line=find_end_line_number(
                    file_path=Path(results[corpus.index(doc)].metadata.file.file_path),
                    end_index=results[corpus.index(doc)].metadata.chunk.chunk_end_index,
                ),
            ),
            flush=True,
        )
        print()
        print(" Content ".upper().center(80, "-"), flush=True)
        print()
        Console().print(Syntax(doc, "python"))
        print()
        print(" Metadata ".upper().center(80, "-"), flush=True)
        print()
        pprint(results[corpus.index(doc)].metadata)
        print()
        print("-" * 80)

        if _idx == TOP_K_HYBRID - 1:
            break

    print("".center(80, "$"), flush=True)
    print("".center(80, "$"), flush=True)
    print("".center(80, "$"), flush=True)

    break


# %%

# REF: https://github.com/cohere-ai/DiskVectorIndex
# REF: https://github.com/togethercomputer/together-cookbook/blob/9c7ab7cf281eed884e5689e8ec88e7ae3a00f724/Open_Contextual_RAG.ipynb

# %%


settings = config

project_id = os.getenv(
    key="PROJECT_ID",
    default=getattr(settings, "PROJECT_ID", None) or "",
)


client = discoveryengine.RankServiceClient()

# The full resource name of the ranking config.
# Format: projects/{project_id}/locations/{location}/rankingConfigs/default_ranking_config
ranking_config = client.ranking_config_path(
    project=project_id,
    location="global",
    ranking_config="default_ranking_config",
)
request = discoveryengine.RankRequest(
    ranking_config=ranking_config,
    model="semantic-ranker-512@latest",
    top_n=10,
    query="What is Google Gemini?",
    records=[
        discoveryengine.RankingRecord(
            id="1",
            title="Gemini",
            content="The Gemini zodiac symbol often depicts two figures standing side-by-side.",
        ),
        discoveryengine.RankingRecord(
            id="2",
            title="Gemini",
            content="Gemini is a cutting edge large language model created by Google.",
        ),
        discoveryengine.RankingRecord(
            id="3",
            title="Gemini Constellation",
            content="Gemini is a constellation that can be seen in the night sky.",
        ),
    ],
)

response = client.rank(request=request)

# Handle the response
print(response)

# %%
