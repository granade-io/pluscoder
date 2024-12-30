
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
    First time you run `pluscoder` you will be prompted to specify your preferred LLM provider and model.  You can also specify the provider and model using the `provider` and `model` options. Check all available providers at the [Configuration](documentation/config.md#providers).

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

To optimize the chat experience, we recommend to enable repository indexing. For that just remove the `skip_repo_index` flag and specify an embedding model using the `embedding_model` config.

```bash
export OPENAI_API_KEY=<your_openai_api_key>
pluscoder --model gpt-4o --embedding_model cohere/embed-english-v3.0
```

!!! info
    Using an embedding model usually incurs additional costs. We recommend using it along `repo_exclude_files` [config](documentation/configuration.md#repository-settings) option to exclude specific files from indexing.

## Programmatically

PlusCoder provides an API to interact with the system programmatically. Here's an example of how to use it to run an agent in the current workdir with a given input:

```python
from pluscoder import workflow, build_agents

# Obtain predefined & company-wide agents
agents = build_agents()

# Select specific agent
dev_agent = agents.get('developer')

# Runs agent in the current workdir
workflow.run(agent=dev_agent, input="Write a detailed README.md file specifying develop environment setup using commands present in Makefile")
```


| **Command**                     | **Description**                                                                                         |
|----------------------------------|---------------------------------------------------------------------------------------------------------|
| `/clear`                         | Reset entire chat history.                                                                              |
| `/diff`                          | Show last commit diff.                                                                                  |
| `/config <key> <value>`          | Override any pluscoder configuration. e.g., `/config auto-commits false`                                |
| `/undo`                          | Revert last commit and remove last message from chat history.                                           |
| `/agent`                         | Start a conversation with a new agent from scratch.                                                     |
| `/help`                          | Display help information for available commands.                                                        |
| `/init`                          | (Re)Initialize repository understanding the code base to generate project overview and code guidelines. |
| `/show_repo`                     | Display information about the current repository.                                                       |
| `/show_repomap`                  | Show the repository map with file structure and summaries.                                              |
| `/show_config`                   | Display the current configuration settings.                                                             |
| `/custom <prompt_name> <additional instructions>` | Execute a pre-configured custom prompt command.                                        |


### CLI Actions

PlusCoder provides an enhanced command-line interface for efficient interaction:

> :warning: **Note**: Some of these features are not available in Docker.

|               | **Action**                                      | **Description**                                                     |
|--------------------------|---------------------------------------------------|------------------------------------------------------------------|
| **Input History**         | Press the **Up Arrow**                            | Recall and reuse previous inputs.                                |
| **Multiline Input**       | Press **Ctrl + Return**                           | Create a new line for multiline commands.                        |
| **Input Clearing**        | Press **Ctrl + C**                                | Clear the current text in the input field.                       |
| **File Autocomplete**     | Start typing a filename. Use **Tab** to alternate suggestions.                                | Get suggestions and autocomplete file paths.                     |
| **Paste Support**         | Paste multiline text directly                     | Use standard paste commands in the input field.                  |
| **Quick Confirmation**    | Use **'y'** or **'Y'**                            | Quickly confirm prompts or actions.                              |
| **Image Uploading**       | Write `img::<url>` or `img::<local_path>`         | Upload images to the system.                                     |
| **Coping Images**         | Press **Ctrl + V**                                | Copy images and paste it directly into. |

---

## Next Steps

* Read the [PlusCoder Configuration](01_pluscoder_configuration.md) documentation to learn how to configure PlusCoder for your projects with the `.pluscoder-config.yml` file.
* Read the [Adding Custom Agents](02_custom_agents.md) tutorial to learn how to add custom agents to PlusCoder.
* Learn the [Tips and Tricks](03_tips_and_tricks.md) to get the most out of PlusCoder.
* Check out the [Workflows+Coder](https://gitlab.com/codematos/workflows) section for an example.
****