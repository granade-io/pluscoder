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
- `/undo`: Revert last commit and remove last message from chat history.
- `/agent`: Start a conversation with a new agent from scratch.
- `/agent_create`: Creates a persistent specialized agent to work with.
- `/help`: Display help information for available commands.
- `/init`: (Re)Initialize repository understanding the code base to generate project overview and code guidelines md files.
- `/show_repo`: Display information about the current repository.
- `/show_repomap`: Show the repository map with file structure and summaries.
- `/show_config`: Display the current configuration settings.
- `/custom <prompt_name> <additional instructions>`: Execute a pre-configured custom prompt command.

## Configuration

PlusCoder can be configured using several methods (using this priority):
1. The `/config` command during runtime
2. Command-line arguments
3. Dot env variables ( `.env` file)
4. A `.pluscoder-config.yml` file for persistent configuration
5. Environment variables
6. Global pluscoder yaml config file (`~/.config/pluscoder/config.yml` or `AppData/Local/pluscoder/config.yml`)

> **Note**: Credentials must be provided as environment variables, or using `.env` or global `~/.config/pluscoder/var.env` file. Passing credentials in other files won't work.

Display current configuration settings using command `/show_config` or cmd line arg `--show_config`.

### Application Behavior
- `pluscoder_token`: Your PlusCoder API authentication token
- `read_only`: Enable/disable read-only mode to avoid file editions (default: `False`)
- `streaming`: Enable/disable LLM streaming (default: `True`)
- `user_feedback`: Enable/disable user feedback (default: `True`)
- `display_internal_outputs`: Display internal agent outputs (default: `False`)
- `auto_confirm`: Enable/disable auto confirmation of pluscoder execution (default: `False`)
- `hide_thinking_blocks`: Hide thinking blocks in LLM output (default: `True`)
- `hide_output_blocks`: Hide output blocks in LLM output (default: `False`)
- `hide_source_blocks`: Hide source blocks in LLM output (default: `False`)
- `show_token_usage`: Show token usage/cost (default: `True`)
- `default_agent`: Specify the name/number of the default agent to use. If not specified selection will be interactive (default: `None`)

### File Paths
- `overview_filename`: Filename for project overview (default: `"PROJECT_OVERVIEW.md"`)
- `log_filename`: Filename for logs (default: `"pluscoder.log"`)
- `overview_file_path`: Path to the project overview file (default: `"PROJECT_OVERVIEW.md"`)
- `guidelines_file_path`: Path to the coding guidelines file (default: `"CODING_GUIDELINES.md"`)

### Models and Providers

*Models*:
- `model`: LLM model to use (default: `None`)
- `orchestrator_model`: LLM model to use for orchestrator (default: same as `MODEL`)
- `weak_model`: Weaker LLM model to use for less complex tasks (default: same as `MODEL`). (CURRENTLY NOT BEING USED)

*Provider*:
- `provider`: Provider to use. If `None`, provider will be selected based on available credential variables. Options: aws_bedrock, openai, litellm, anthropic, vertexai (default: `None`)
- `orchestrator_model_provider`: Provider to use for orchestrator model (default: same as `PROVIDER`)
- `weak_model_provider`: Provider to use for weak model (default: same as `PROVIDER`). (CURRENTLY NOT BEING USED)

### Model Credentials

Define these at `.env`, `~/.config/pluscoder/vars.env` or using `export VAR=value`:

*OpenAI*:
- `OPENAI_API_KEY`: OpenAI API key. (default: `None`)
- `OPENAI_API_BASE`: OpenAI API base URL. (default: `None`)

*Anthropic*:
- `ANTHROPIC_API_KEY`: Anthropic API key. (default: `None`)

*AWS*
- `AWS_ACCESS_KEY_ID`: AWS Access Key ID. (default: `None`)
- `AWS_SECRET_ACCESS_KEY`: AWS Secret Access Key. (default: `None`)
- `AWS_PROFILE`: AWS profile name (default: `"default"`)

### Git Settings
- `auto_commits`: Enable/disable automatic Git commits (default: `True`)
- `allow_dirty_commits`: Allow commits in a dirty repository (default: `True`)

### Test and Lint Settings
Configure any lint/test command. Agents will try to fix any error found automatically.

- `run_tests_after_edit`: Run tests after file edits (default: `False`)
- `run_lint_after_edit`: Run linter after file edits (default: `False`)
- `test_command`: Command to run tests (default: `None`)
- `lint_command`: Command to run linter (default: `None`)
- `auto_run_linter_fix`: Automatically run linter fix before linting (default: `False`)
- `lint_fix_command`: Command to run linter fix (default: `None`)

### Repository Settings
Use these when running pluscoder in remote repositories for automated runs.

- `repository`: Git repository path or URL to clone and process (default: `None`)
- `source_branch`: Specify source branch to checkout when cloning repository (default: `None`)

### Repomap Settings
Currently these are deprecated and not being used anymore.

- `use_repomap`: Enable/disable repomap feature (default: `False`)
- `repomap_level`: Set the level of detail for repomap (default: `2`)
- `repomap_include_files`: Comma-separated list of files to include in repomap (default: `[]`)
- `repomap_exclude_files`: Comma-separated list of files to exclude from repomap (default: `[]`)
- `repo_exclude_files`: Json list with list of custom prompts configs (default: `[]`)

### Custom Prompt Commands

Custom prompt commands allow you to define pre-configured prompts/instruction that can be easily executed during runtime and passed to agents.

To configure custom prompt commands:

1. Open or create the `.pluscoder-config.yml` file in your project root.
2. Add a `custom_prompt_commands` section with a list of custom prompts, each containing:
   - `prompt_name`: A unique name for the command
   - `description`: A brief description of what the command does
   - `prompt`: The prompt suffix text to be sent to the AI along a custom message

Example:

```yaml
custom_prompt_commands:
  - prompt_name: docstring
    prompt: |
      Please add docstring to these files above
    description: "Generate docstring for specified files"
  - prompt_name: brainstorm
    description: Propose ideas for implementation without editing code base.
    prompt: |
      Based on the previous request, please perform a brainstorm of how could this achieved. 
        1. Read key files, analyze them
        2. Tell me with a bullet point list, the role of each involved file
        3. Tell me a proposed plan in natural language
      Remember; DO NOT edit files yet.
```

Usage: 

```bash
/custom docstring
/custom brainstorm i want a new api endpoints to register users and authenticate them
```
### Custom Agents

PlusCoder supports the creation of custom agents for specialized tasks. These agents can be defined in the configuration and used alongside the predefined agents.

**Create a new agent helped by an llm using `/agent_create` command.**

To configure custom agents manually:

1. Open or create the `.pluscoder-config.yml` file in your project root.
2. Add a `custom_agents` section with a list of custom agent configurations, each containing:
   - `name`: A unique name for the agent
   - `description`: a description of the agent
   - `prompt`: The system prompt defining the agent's role and capabilities
   - `repository_interaction`: Where or not the agent can interact with the repository. Useful for agents repository agnostic.
   - `read_only`: Boolean indicating whether the agent is restricted to read-only file operations
   - `reminder`: Reminder to the agent to send with every user message
   - `default_context_files`: Files that the agent will read automatically every chat session or execution

Example:

```yaml
custom_agents:
  - name: CodeReviewer
    description: Agent description
    prompt: "You are a code reviewer. Your task is to review code changes and provide feedback on code quality, best practices, and potential issues."
    read_only: true
  - name: DocumentationWriter
    description: Agent description
    prompt: "You are a technical writer specializing in software documentation. Your task is to create and update project documentation, including README files, API documentation, and user guides."
    read_only: false
```

Custom agents can be selected and used in the same way as predefined agents during the PlusCoder workflow. They will appear in the agent selection menu and can be assigned tasks by the Orchestrator agent.


## Command-line arguments

You can specify any configuration using command-line arguments:

- `--show_repo`: Display information about the current repository and exit.
- `--show_repomap`: Show the repository map with file structure and summaries and exit.
- `--show_config`: Display the current configuration settings and exit.

These arguments can be used when launching PlusCoder to quickly access specific information without entering the interactive mode.

You can set these options using environment variables, command-line arguments (e.g., `--streaming false`), or the `/config` command during runtime (e.g., `/config streaming false`).

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

