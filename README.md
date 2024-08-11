## Requirements
- Requires python 3.12
- AWS Creds with Bedrock proper permissions

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

5. Run:

   ```bash
   python -m pluscoder.main [options]
   # plus-coder [options]
   ```

6. Test:

   ```bash
   pytest
   ```

## Available Commands

PlusCoder supports the following commands during interaction:

- `/clear`: Reset entire chat history.
- `/diff`: Show last commit diff.
- `/config <key> <value>`: Override any pluscoder configuration. e.g., `/config auto-commits false`
- `/undo`: Revert last commit and remove last message from chat history.
- `/agent`: Start a conversation with a new agent from scratch.
- `/help`: Display help information for available commands.

## Configuration

PlusCoder can be configured using environment variables, command-line arguments, or the `/config` command during runtime. Here are the available configuration options:

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
- `OPENAI_API_KEY`: OpenAI API key
- `OPENAI_API_BASE`: OpenAI API base URL

### AWS Settings
- `AWS_ACCESS_KEY_ID`: AWS Access Key ID
- `AWS_SECRET_ACCESS_KEY`: AWS Secret Access Key
- `AWS_PROFILE`: AWS profile name (default: "default")

### Git Settings
- `AUTO_COMMITS`: Enable/disable automatic Git commits (default: True)
- `ALLOW_DIRTY_COMMITS`: Allow commits in a dirty repository (default: True)

You can set these options using environment variables, command-line arguments (e.g., `--streaming false`), or the `/config` command during runtime (e.g., `/config streaming false`).

