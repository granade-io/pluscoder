# example.py or any other file using the search module
import asyncio
import os
from pathlib import Path

from pluscoder.repo import Repository
from pluscoder.search import DenseSearch
from pluscoder.search import HybridSearch
from pluscoder.search import LiteLLMEmbedding
from pluscoder.search import SearchEngine
from pluscoder.search import SparseSearch
from pluscoder.search import TokenBasedChunking

os.environ["COHERE_API_KEY"] = "1mDJaJPwj1BATZRNYyCMbEtKMdTZD47e9BvqW3xO"


async def main():
    # Initialize components
    chunking = TokenBasedChunking(chunk_size=512, overlap=64)
    embedding = LiteLLMEmbedding(
        # model_name="vertex_ai/text-embedding-005",
        batch_size=64
    )
    search_algo = HybridSearch([DenseSearch(embedding_model=embedding), SparseSearch()])

    # Create search engine with persistence using factory pattern
    storage_dir = Path() / ".pluscoder" / "search_index"
    engine = await SearchEngine.create(
        chunking_strategy=chunking, search_algorithm=search_algo, embedding_model=embedding, storage_dir=storage_dir
    )

    repo = Repository()
    tracked_files = repo.get_tracked_files()

    # Build initial index (only needed first time or for full rebuild)
    initial_files = [Path(file) for file in tracked_files if ".py" in file]
    print("Building initial index")
    await engine.build_index(initial_files)

    # Query loop
    while True:
        query = input("\nEnter your search query (or press Enter to quit): ").strip()
        if not query:
            break

        # result = engine.search(query)
        result = await engine.async_search(query)
        print("\nSearch results:")
        print("-" * 50)
        for search_result in result:
            print(f"Score: {search_result.score}")
            print(f"Rank: {search_result.rank}")
            print(search_result.chunk.content)
            print("-" * 50)


if __name__ == "__main__":
    asyncio.run(main())
