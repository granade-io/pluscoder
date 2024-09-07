## Requirements
- Requires python 3.12
- AWS Creds with Bedrock proper permissions

## Usage:

Use pluscoder inside a git repository:

   ```bash
   # Install pluscoder
   pip install --no-cache git+https://gitlab.com/codematos/pluscoder.git

   # Run
   plus-coder --auto-commits f --model claude-3-5-sonnet-20240620 --provider anthropic
   ```

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

## Available Commands

PlusCoder supports the following commands during interaction:

- `/clear`: Reset entire chat history.
- `/diff`: Show last commit diff.
- `/config <key> <value>`: Override any pluscoder configuration. e.g., `/config auto-commits false`
- `/undo`: Revert last commit and remove last message from chat history.
- `/agent`: Start a conversation with a new agent from scratch.
- `/help`: Display help information for available commands.

## Configuration

PlusCoder can be configured using environment variables (you can use your `.env`), command-line arguments, or the `/config` command during runtime. Here are the available configuration options:

### Application Behavior
- `STREAMING`: Enable/disable LLM streaming (default: True)
- `USER_FEEDBACK`: Enable/disable user feedback (default: True)
- `DISPLAY_INTERNAL_OUTPUTS`: Display internal agent outputs (default: False)

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

You can set these options using environment variables, command-line arguments (e.g., `--streaming false`), or the `/config` command during runtime (e.g., `/config streaming false`).

