
# Quick Start

You can run PlusCoder in two ways:

- **[Interactively](#interactively)**: Chat with PlusCoder agents in your terminal and instruct them to interact with your local files and directories.
- **[Programmatically](#programmatically)**: Write scripts to interact with PlusCoder using its API. Running it in your local machine or cloud environments.

## Interactively

### Basic chat with agents

After [installing](installation.md) PlusCoder, start a chat with pre-defined & company-wide agents by running:

```bash
cd /path/to/your/project
export OPENAI_API_KEY=<your_openai_api_key>
pluscoder --model gpt-4o --skip_repo_index

```

!!! info
    You can also specify any CLI config flag using environment variables or inside pluscoder-config.yaml file. Check configuration options at [Configuration](documentation/config.md) or by running `pluscoder -h`.

!!! info
    First time you run `pluscoder` you will be prompted to specify your preferred LLM provider and model.  You can also specify the provider and model using the `provider` and `model` options. Check all supported providers at [Providers Section](documentation/providers.md).

Agents by default can read/write local repository files. You can run agents using read-only mode by adding the `read_only` flag.

```bash
pluscoder --read_only --skip_repo_index
```

Check repository files that agents have access to by running:

```bash
pluscoder --show_repo
```

Or using the in-chat command `/show_repo`.

### Optimized chat with indexed repository

To optimize the chat experience, we recommend to enable [repository indexing](documentation/indexing.md). For that just remove the `skip_repo_index` flag and specify an embedding model using the `embedding_model` config.

```bash
export OPENAI_API_KEY=<your_openai_api_key>
export COHERE_API_KEY=<your_cohere_api_key>
pluscoder --model gpt-4o --embedding_model cohere/embed-english-v3.0
```

!!! info
    Using an embedding model usually incurs additional costs. We recommend using it along `repo_exclude_files` [config](documentation/configuration.md#repository-settings) option to exclude specific files from indexing.

### Automated runs with CLI

You can use `auto_confirm` flag to automatically confirm all prompts. This is useful for automated runs.

```bash
pluscoder --auto_confirm yes --user_input "Write unit tests for all functions in the `utils.py` file"
```

## Programmatically

PlusCoder provides an API to interact with the system programmatically. Here's an example of how to use it to run an agent in the current workdir with a given input:

```python
from pluscoder.agents.core import DeveloperAgent
from pluscoder.type import AgentConfig
from pluscoder.workflow import run_agent


async def main():
    # Select specific agent
    developer_agent: AgentConfig = DeveloperAgent.to_agent_config(model="gpt-4o")

    # Runs agent in the current workdir
    await run_agent(
        agent=developer_agent,
        input="Write a detailed README.md file specifying develop environment setup using commands present in Makefile"
    )
```

## Next Steps

- Read the [Configuration](documentation/configuration.md) section for more customization.
- Read [Agents](documentation/agents.md) section to learn how to use pre-defined agents and to setup custom ones.
- Check [Examples](examples/index.md) section to learn how to setup PlusCoder for different common use-cases.