## Installation

You have tree options to install PlusCoder, depending of the type of user you are:

### a. **You + Coder**

1. **install.sh**: This is **the easiest way** to install and PlusCoder. Just run the following command in your terminal. You can select the python or docker version.

> :information_source: **Note**: This script needs Docker or Python 3.12 to be installed and running in your system. This may change in the future.
> :information_source: **Note**: If you are using Python, you need to have the right access to the repository.


```bash
curl -s https://raw.githubusercontent.com/codematos/pluscoder/main/install.sh | bash
# pluscoder -h
```

This script will install PlusCoder in your system, add the and add the `pluscoder` command to your `PATH`.

1. **Python**: If you prefer to install PlusCoder using Python manually, you can run the following command:

> :information_source: **Note**: This method requires Python 3.12 and the right access to the repository. This may change in the future.

```bash
conda create -n pc python=3.12
conda activate pc
pip install git+https://gitlab.com/codematos/pluscoder.git
alias pluscoder-python="$(which python) -m pluscoder"
# pluscoder -h
```

2. **Docker**: You can also use PlusCoder with Docker manually. Just run the following command:

```bash
export PLUSCODER_IMAGE=registry.gitlab.com/codematos/pluscoder:latest
alias pluscoder-docker="docker run --env-file <(env) -v $(pwd):/app -it --rm $PLUSCODER_IMAGE"
# pluscoder-docker -h
```

### b. **Contributor**


---

## PlusCoder CLI

This section provides an overview of the PlusCoder CLI and how to use it to interact with the PlusCoder system through some examples.

Once you set up the necessary credentials, you can start using PlusCoder in your projects.



> :information_source: **Note**: You need to have the necessary credentials for AWS Bedrock, Anthropic, OpenAI, or other providers through LLMLite.


### Basic Usage

The entry point for PlusCoder is the `pluscoder` command. You can run it in your terminal to start the PlusCoder CLI.

> :information_source: **Note**: PlusCoder only works in a **git repository**. If you are not in a git repository, you will see an error message.

```bash
# Open a terminal in the project directory
pluscoder
```

This command will start the PlusCoder CLI in interactive mode, allowing you to interact with the system using the available agents and features.

You can run `pluscoder -h` for a full list of options for the PlusCoder CLI.

But The most important options are:

- `--provider`: Provider to use. (`aws_bedrock`, `openai`, `litellm`, `anthropic`) If not provided, it will use check the configured credentials to select a provider.
- `--model`: LLM model from the `provider`. It will use the default model according to the provider.
- `--auto_commits`: Enable/disable automatic Git commits (default: `True`)
- `--default_agent`: Default agent to use. If not provided, you will be prompted to select an agent.

### Single Prompt

You can also run PlusCoder with a single prompt using the `--user_input` option. This is useful for running a single prompt without entering the interactive mode.

```bash
pluscoder --user_input "Create a new feature" --default_agent "Developer"
```

### Working with a Repository

The first time you run PlusCoder in a repository, you'll be prompted to initialize the repository through an LLM code base analysis. This process generates a project overview and code guidelines for the repository.

```bash
pluscoder
```

#### Steps to Initialize a Repository (WIP)

1. step 1

2. step 2

3. step 3

### CLI Commands

PlusCoder supports several commands during interaction:


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