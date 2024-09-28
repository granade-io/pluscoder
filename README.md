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
8.  Support for multiple LLM models (LLMLite, OpenAI, AWS Bedrock, Anthropic)
9.  Enhanced user interaction with rich console output and auto-completion
10. Real-time task execution progress display

## Requirements
- Requires python 3.12
- Credentials for AWS Bedrock, Anthropic, OpenAI or other providers throught LLMLite

## Usage:

Use pluscoder inside a git repository:

   ```bash
   # Install pluscoder
   pip install --no-cache git+https://gitlab.com/codematos/pluscoder.git

   # Run, pluscoder will detect credentials automatically
   plus-coder --auto-commits f --model claude-3-5-sonnet-20240620
   ```

> **Note:** First time you run pluscoder in a repo you'll be prompted to initialize the repository through an LLM code base analysis.

## CLI Interaction

Pluscoder provides an enhanced command-line interface for efficient interaction:

1. **Input History**: Use the up arrow key to recall and reuse previous inputs.
2. **Multiline Input**: Press Ctrl+Return to start a new line within the input field, allowing for complex multiline commands or descriptions.
3. **Input Clearing**: Use Ctrl+C to quickly clear the current text in the input field.
4. **File Autocomplete**: Type any file name (at any directory level) to see suggestions and autocomplete file paths.
5. **Paste Support**: Easily paste multiline text directly into the input field.
6. **Quick Confirmation**: Use 'y' or 'Y' to quickly confirm prompts or actions.

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

Note: Using the '--auto-confirm' flag when starting Pluscoder will automatically confirm any plan and task execution without prompting.

## Available Commands

PlusCoder supports the following commands during interaction:

- `/clear`: Reset entire chat history.
- `/diff`: Show last commit diff.
- `/config <key> <value>`: Override any pluscoder configuration. e.g., `/config auto-commits false`
- `/undo`: Revert last commit and remove last message from chat history.
- `/agent`: Start a conversation with a new agent from scratch.
- `/help`: Display help information for available commands.
- `/init`: (Re)Initialize repository understanding the code base to generate project overview and code guidelines md files.
- `/show_repo`: Display information about the current repository.
- `/show_repomap`: Show the repository map with file structure and summaries.
- `/show_config`: Display the current configuration settings.

## Command-line Arguments

In addition to the runtime commands, PlusCoder supports the following command-line arguments:

- `--show-repo`: Display information about the current repository and exit.
- `--show-repomap`: Show the repository map with file structure and summaries and exit.
- `--show-config`: Display the current configuration settings and exit.

These arguments can be used when launching PlusCoder to quickly access specific information without entering the interactive mode.

## Configuration

PlusCoder can be configured using environment variables (you can use your `.env`), command-line arguments, or the `/config` command during runtime. Here are the available configuration options:

### Application Behavior
- `STREAMING`: Enable/disable LLM streaming (default: True)
- `USER_FEEDBACK`: Enable/disable user feedback (default: True)
- `DISPLAY_INTERNAL_OUTPUTS`: Display internal agent outputs (default: False)
- `AUTO_CONFIRM`: Enable/disable auto confirmation of pluscoder execution (default: False)

### File Paths
- `OVERVIEW_FILENAME`: Filename for project overview (default: "PROJECT_OVERVIEW.md")
- `LOG_FILENAME`: Filename for logs (default: "pluscoder.log")
- `OVERVIEW_FILE_PATH`: Path to the project overview file (default: "PROJECT_OVERVIEW.md")
- `GUIDELINES_FILE_PATH`: Path to the coding guidelines file (default: "CODING_GUIDELINES.md")

### Model and API Settings
- `MODEL`: LLM model to use (default: "anthropic.claude-3-5-sonnet-20240620-v1:0")
- `PROVIDER`: Provider to use. If none, provider will be selected based on available credentaial variables. Options: aws_bedrock, openai, litellm, anthropic (default: None)
- `OPENAI_API_KEY`: OpenAI API key
- `OPENAI_API_BASE`: OpenAI API base URL
- `ANTHROPIC_API_KEY`: Anthropic API key
- `AWS_ACCESS_KEY_ID`: AWS Access Key ID
- `AWS_SECRET_ACCESS_KEY`: AWS Secret Access Key
- `AWS_PROFILE`: AWS profile name (default: "default")

### Git Settings
- `AUTO_COMMITS`: Enable/disable automatic Git commits (default: True)
- `ALLOW_DIRTY_COMMITS`: Allow commits in a dirty repository (default: True)

### Test and Lint Settings
- `RUN_TESTS_AFTER_EDIT`: Run tests after file edits (default: False)
- `RUN_LINT_AFTER_EDIT`: Run linter after file edits (default: False)
- `TEST_COMMAND`: Command to run tests (default: None)
- `LINT_COMMAND`: Command to run linter (default: None)
- `AUTO_RUN_LINTER_FIX`: Automatically run linter fix before linting (default: False)
- `LINT_FIX_COMMAND`: Command to run linter fix (default: None)

### Repomap Settings
- `USE_REPOMAP`: Enable/disable repomap feature (default: True)
- `REPOMAP_LEVEL`: Set the level of detail for repomap (default: 2)
- `REPOMAP_INCLUDE_FILES`: Comma-separated list of files to include in repomap (default: None)
- `REPOMAP_EXCLUDE_FILES`: Comma-separated list of files to exclude from repomap (default: None)
- `REPO_EXCLUDE_FILES`: Comma-separated list of regex patterns to exclude files from repo operations (default: None)

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
   plus-coder [options]
   ```

7. Test:

   ```bash
   pytest
   ```

## Setting up Pre-commit

The `setup_precommit.sh` script will:
1. Install pre-commit
2. Set up the git hooks
3. Add the necessary environment variables to the `.env` file