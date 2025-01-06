# Repository Indexing

## Overview

PlusCoder came along with a powerful indexing system that allows you to index your repositories and search through them. The indexing system is based on the [bm25s](https://github.com/xhluca/bm25s) library and embedding. This allows you to just ask anything to agents and they will find any relevant file to handle your request, by performing an hybrid search using `bm25` and `embeddings`.

!!! tip "Indexing algorithm"
    By default, `bm25` is always enabled when using the CLI. `embedding` algorithm is enabled by specifying the `embedding_model` option that works with LiteLLM provider. You can skip the `embedding` algorithm by specifying the `skip_repo_index` option or by unsetting the `embedding_model` option.

## Indexing through CLI

CLI repository indexing occurs out of the box. When you run the CLI, it will index all files tracked in your repository by default. 

**bm25 search only (no embedding indexation):**
```bash
# Will index all files in the repository by using bm25 only
export OPENAI_API_KEY=<your_openai_api_key>
pluscoder --default_agent developer --model gpt-4o
```

**hybrid search (bm25 and embedding indexation):**
```bash
# Will index all files in the repository by using bm25 and embedding
export OPENAI_API_KEY=<your_openai_api_key>
export COHERE_API_KEY=<your_cohere_api_key>
pluscoder --default_agent developer --model gpt-4o --embedding_model cohere/embed-english-v3.0
```

## Indexing through Python

You can also index your repository programmatically, which is not done by default.

**bm25 search only (no embedding indexation):**

```python
from pluscoder.agents.core import DeveloperAgent
from pluscoder.search.builtin import setup_search_engine
from pluscoder.type import AgentConfig
from pluscoder.workflow import run_agent

async def main():
    # Setup search engine globally so agents can use it
    await setup_search_engine(show_progress=True)

    # Select specific agent
    developer_agent: AgentConfig = DeveloperAgent.to_agent_config(model="gpt-4o")

    # Agents will use the search engine to find relevant files automatically thanks to global setup
    await run_agent(agent=developer_agent, input="Refactor models and endpoint following REFACTORING_GUIDELINES.md")
```

**hybrid search (bm25 and embedding indexation):**

```python
from pluscoder.agents.core import DeveloperAgent
from pluscoder.search.builtin import setup_search_engine
from pluscoder.type import AgentConfig
from pluscoder.workflow import run_agent

async def main():
    # Setup search engine globally so agents can use it
    await setup_search_engine(show_progress=True, embedding_model="cohere/embed-english-v3.0")

    # Select specific agent
    developer_agent: AgentConfig = DeveloperAgent.to_agent_config(model="gpt-4o")

    # Agents will use the search engine to find relevant files automatically thanks to global setup
    await run_agent(agent=developer_agent, input="Refactor models and endpoint following REFACTORING_GUIDELINES.md")
```

## Indexing persistency

The indexing system is persistent and will be saved in the `.pluscoder` directory in your repository. This allows you to keep the index up-to-date and avoid re-indexing the repository every time you run the CLI or the Python API.

!!! tip "Re-indexing"
    CLI detects changes in the repository and will re-index the repository if it detects any changes. This is useful when you add, update or remove files from the repository.

!!! tip "Removing indexing"
    You can remove the index by deleting the `.pluscoder` directory in your repository, or more specifically the `.pluscoder/search_index` directory inside it. This will force the CLI to re-index the repository next time you run it.