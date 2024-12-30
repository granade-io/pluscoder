# Pluscoder

PlusCoder is an AI-assisted software development tool designed to enhance and streamline the software development process. It leverages multiple specialized AI agents to assist with various aspects of development, from planning and implementation to validation and project management.

## Key Features

1. Automated repository analysis and documentation
2. Automated context reading and file editing by agents
3. Multi-agent task-based workflows executions for complex requirements
4. User approvals for key points in the workflow or fully automated runs
5. Auto-commit on editions
6. Cost and token tracking for LLM interactions
7. Flexible configuration system supporting command-line arguments, environment variables, and default values
8. Support for multiple LLM models (LLMLite, OpenAI, AWS Bedrock, Anthropic)
9. Enhanced user interaction with rich console output and auto-completion
10. Real-time task execution progress display
11. File downloading and context addition during agent interactions
12. Custom agent creation for specialized tasks

## Requirements
- `uv` python package manager
- Credentials for AWS Bedrock, Anthropic, OpenAI, VertexAI or other providers through LLMLite

## Usage:

First, ensure you have set your PlusCoder API token (installer configures it automatically):
```bash
export PLUSCODER_TOKEN=<your_token_here>
```

**Docker**:

> **Note:** Image pasting (ctrl+v) is not supported through Docker

```bash
# Pass required tokens through environment
docker run --env PLUSCODER_TOKEN --env ANTHROPIC_API_KEY -v $(pwd):/app -it --rm registry.gitlab.com/codematos/pluscoder:latest --auto_commits f
```

**Python**:

   ```bash
   # Install pluscoder
   pip install --no-cache git+https://gitlab.com/codematos/pluscoder.git

   # Run with PLUSCODER_TOKEN set in environment
   pluscoder --auto_commits f --model claude-3-5-sonnet-20240620
   ```

> **Note:** Pluscoder requires a git repository

> **Note:** First time you run pluscoder in a repo you'll be prompted to initialize the repository through an LLM code base analysis.

## CLI Interaction

Pluscoder provides an enhanced command-line interface for efficient interaction:

1. **Input History**: Use the up arrow key to recall and reuse previous inputs.
2. **Multiline Input**: Press Ctrl+Return to start a new line within the input field, allowing for complex multiline commands or descriptions.
3. **Input Clearing**: Use Ctrl+C to quickly clear the current text in the input field.
4. **File Autocomplete**: Type any file name (at any directory level) to see suggestions and autocomplete file paths.
5. **Paste Support**: Easily paste multiline text directly into the input field.
6. **Quick Confirmation**: Use 'y' or 'Y' to quickly confirm prompts or actions.
7. **Image Uploading**: Write `img::<url>` or `img::<local_path>` to send these files to multi-modal LLMs ad part of the prompt.
8. **Image Pasting**: Ctrl+V to paste images directly into the input field. The system will automatically handle clipboard images, save them to temporary files, and convert file paths to base64-encoded strings for processing.

These features are designed to streamline your interaction with Pluscoder, making it easier to navigate, input commands, and manage your development workflow.

## Orchestrated Task based executions

1. Start Pluscoder in your terminal and choose the `Orchestrator` agent (option 1).
2. Ask for a plan with your requirements, review it and give feedback until satisfied.
3. Tell the orchestrator to `delegate` the plan and approve by typing `y` when prompted.
4. The Orchestrator will delegate and execute tasks using specialized agents.
5. Monitor real-time progress updates and type `y` to continue to the next task after each completion.
6. Review the summary of completed work and changes to project files.
7. Provide new requirements or iterate for complex projects as needed.

Note: Pluscoder can modify project files; always review changes to ensure alignment with your goals.

Note: Using the '--auto_confirm' flag when starting Pluscoder will automatically confirm any plan and task execution without prompting.

## Available Commands

PlusCoder supports the following commands during interaction:

- `/clear`: Reset entire chat history.
- `/diff`: Show last commit diff.
- `/config <key> <value>`: Override any pluscoder configuration. e.g., `/config auto-commits false`
- `/undo`: Revert last commit along all messages until last user message is removed.
- `/agent`: Start a conversation with a new agent from scratch.
- `/agent_create`: Creates a persistent specialized agent to work with.
- `/help`: Display help information for available commands.
- `/init`: (Re)Initialize repository understanding the code base to generate project overview and code guidelines md files.
- `/show_repo`: Display information about the current repository.
- `/show_repomap`: Show the repository map with file structure and summaries.
- `/show_config`: Display the current configuration settings.
- `/custom <prompt_name> <additional instructions>`: Execute a pre-configured custom prompt command.


## Development

1. Create a virtual environment and activate it:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   # pip install -e path/to/pluscoder/root
   # pip install -e .
   ```

3. Edit the `.env` file and set the appropriate values for your environment.

4. Set up pre-commit hooks:
   ```bash
   # Install pre-commit
   pip install pre-commit

   # Install the git hook scripts
   pre-commit install
   ```

5. Run:

   ```bash
   # as python module
   python -m pluscoder.main [options]

   # as bash command
   pluscoder [options]
   ```

6. Test:

   ```bash
   pytest
   ```

