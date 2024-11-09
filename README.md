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
8. Support for multiple LLM models (LLMLite, OpenAI, AWS Bedrock, Anthropic, VertexAI)
9. Enhanced user interaction with rich console output and auto-completion
10. Real-time task execution progress display
11. File downloading and context addition during agent interactions
12. Custom agent creation for specialized tasks

## Requirements
- Requires python 3.12 or Docker
- Credentials for AWS Bedrock, Anthropic, OpenAI, VertexAI or other providers through LLMLite

## Usage:

First, ensure you have set your PlusCoder API token:
```bash
export PLUSCODER_TOKEN=your_token_here
```

**Docker**:

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
- `/agent_create`: Creates a persistent specialized agent to chat with.
- `/help`: Display help information for available commands.
- `/init`: (Re)Initialize repository understanding the code base to generate project overview and code guidelines md files.
- `/show_repo`: Display information about the current repository.
- `/show_repomap`: Show the repository map with file structure and summaries.
- `/show_config`: Display the current configuration settings.
- `/custom <prompt_name> <additional instructions>`: Execute a pre-configured custom prompt command.

## Configuration

PlusCoder can be configured using several methods (using this priotity):
1. The `/config` command during runtime
2. Command-line arguments
3. Dot env variables ( `.env` file)
4. A `.pluscoder-config.yml` file for persistent configuration
5. Environment variables

Display current configuration settings using command `/show_config` or cmd line arg `--show_config`.

### Application Behavior
- `PLUSCODER_TOKEN`: Your PlusCoder API authentication token
- `READ_ONLY`: Enable/disable read-only mode to avoid file editions (default: `False`)
- `STREAMING`: Enable/disable LLM streaming (default: `True`)
- `USER_FEEDBACK`: Enable/disable user feedback (default: `True`)
- `DISPLAY_INTERNAL_OUTPUTS`: Display internal agent outputs (default: `False`)
- `AUTO_CONFIRM`: Enable/disable auto confirmation of pluscoder execution (default: `False`)
- `HIDE_THINKING_BLOCKS`: Hide thinking blocks in LLM output (default: `True`)
- `HIDE_OUTPUT_BLOCKS`: Hide output blocks in LLM output (default: `False`)
- `HIDE_SOURCE_BLOCKS`: Hide source blocks in LLM output (default: `False`)
- `SHOW_TOKEN_USAGE`: Show token usage/cost (default: `True`)
- `DEFAULT_AGENT`: Specify the name/number of the default agent to use. If not specified selection is interactive (default: `None`)

### File Paths
- `OVERVIEW_FILENAME`: Filename for project overview (default: `"PROJECT_OVERVIEW.md"`)
- `LOG_FILENAME`: Filename for logs (default: `"pluscoder.log"`)
- `OVERVIEW_FILE_PATH`: Path to the project overview file (default: `"PROJECT_OVERVIEW.md"`)
- `GUIDELINES_FILE_PATH`: Path to the coding guidelines file (default: `"CODING_GUIDELINES.md"`)

### Models and Providers

*Models*:
- `MODEL`: LLM model to use (default: `None`)
- `ORCHESTRATOR_MODEL`: LLM model to use for orchestrator (default: same as `MODEL`)
- `WEAK_MODEL`: Weaker LLM model to use for less complex tasks (default: same as `MODEL`). (CURRENLY NOT BEING USED)

*Provider*:
- `PROVIDER`: Provider to use. If `None`, provider will be selected based on available credentaial variables. Options: aws_bedrock, openai, litellm, anthropic, vertexai (default: `None`)
- `ORCHESTRATOR_MODEL_PROVIDER`: Provider to use for orchestrator model (default: same as `PROVIDER`)
- `WEAK_MODEL_PROVIDER`: Provider to use for weak model (default: same as `PROVIDER`). (CURRENLY NOT BEING USED)

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
- `AUTO_COMMITS`: Enable/disable automatic Git commits (default: `True`)
- `ALLOW_DIRTY_COMMITS`: Allow commits in a dirty repository (default: `True`)

### Test and Lint Settings
- `RUN_TESTS_AFTER_EDIT`: Run tests after file edits (default: `False`)
- `RUN_LINT_AFTER_EDIT`: Run linter after file edits (default: `False`)
- `TEST_COMMAND`: Command to run tests (default: `None`)
- `LINT_COMMAND`: Command to run linter (default: `None`)
- `AUTO_RUN_LINTER_FIX`: Automatically run linter fix before linting (default: `False`)
- `LINT_FIX_COMMAND`: Command to run linter fix (default: `None`)

### Repomap Settings
- `USE_REPOMAP`: Enable/disable repomap feature (default: `False`)
- `REPOMAP_LEVEL`: Set the level of detail for repomap (default: `2`)
- `REPOMAP_INCLUDE_FILES`: Comma-separated list of files to include in repomap (default: `[]`)
- `REPOMAP_EXCLUDE_FILES`: Comma-separated list of files to exclude from repomap (default: `[]`)
- `REPO_EXCLUDE_FILES`: Json list with list of custom prompts configs (default: `[]`)

### Custom Prompt Commands

Custom prompt commands allow you to define pre-configured prompts/instruction that can be easily executed during runtime and passed to agents.

To configure custom prompt commands:

1. Open or create the `.pluscoder-config.yml` file in your project root.
2. Add a `custom_prompt_commands` section with a list of custom prompts, each containing:
   - `prompt_name`: A unique name for the command
   - `description`: A brief description of what the command does
   - `prompt`: The actual prompt text to be sent to the AI

Example:

```yaml
custom_prompt_commands:
  - prompt_name: "docstring"
    prompt: "Please add docstring to these files"
    description: "Generate docstring for specified files"
  - prompt_name: "feature"
    prompt: |
      New feature:
      1. Load relevant files related to this request
      2. Ask me key questions to understand better the requirements
      3. Implement the feature
      4. Update README.md with proper documentation
      feature request: 
    description: "Generate a new feature and documentation"
```

### Custom Agents

PlusCoder supports the creation of custom agents for specialized tasks. These agents can be defined in the configuration and used alongside the predefined agents.

**Create a new agent helped by an llm using `/agent_create`command.**

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


## Command-line Arguments

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

3. Create a `.env` file from the example:
   ```bash
   cp .env.example .env
   ```

4. Edit the `.env` file and set the appropriate values for your environment.

5. Set up pre-commit hooks:
   ```bash
   # Install pre-commit
   pip install pre-commit

   # Install the git hook scripts
   pre-commit install
   ```

6. Run:

   ```bash
   # as python module
   python -m pluscoder.main [options]

   # as bash command
   pluscoder [options]
   ```

7. Test:

   ```bash
   pytest
   ```
