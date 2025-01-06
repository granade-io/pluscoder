from pathlib import Path
from typing import Optional

from pluscoder.io_utils import io
from pluscoder.repo import Repository


async def setup_search_engine(embedding_model: Optional[str] = None, show_progress: bool = False):
    """Initialize the search engine with appropriate algorithm."""
    from pluscoder.agents.event.config import event_emitter
    from pluscoder.search.algorithms import DenseSearch
    from pluscoder.search.algorithms import HybridSearch
    from pluscoder.search.algorithms import SparseSearch
    from pluscoder.search.chunking import TokenBasedChunking
    from pluscoder.search.embeddings import LiteLLMEmbedding
    from pluscoder.search.engine import SearchEngine

    try:
        if show_progress:
            io.live.start("indexing")
        storage_dir = Path(".pluscoder") / "search_index"
        chunking = TokenBasedChunking(chunk_size=512, overlap=64)

        # Configure search algorithm and embedding model based on config
        embedding_model = None
        algorithm = SparseSearch()

        if embedding_model:
            embedding_model = LiteLLMEmbedding(model_name=embedding_model)
            dense = DenseSearch(embedding_model)
            sparse = SparseSearch()
            algorithm = HybridSearch([dense, sparse])

        # Create engine with final configuration
        engine = await SearchEngine.create(
            chunking_strategy=chunking,
            search_algorithm=algorithm,
            storage_dir=storage_dir,
            embedding_model=embedding_model,
        )
        # Connect to global event emitter
        engine.events = event_emitter

        # Get tracked files
        repo = Repository(io)
        files = [Path(f) for f in repo.get_tracked_files()]

        # Always re-index
        await engine.build_index(files, reindex=True)

        if show_progress:
            io.live.stop("indexing")

    except Exception as e:
        io.print(f"Error: Failed to initialize search engine: {e}", style="bold red")
        raise
