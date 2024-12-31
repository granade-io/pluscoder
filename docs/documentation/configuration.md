# Configuration

## Configuration methods

PlusCoder can be configured using several methods (following this precedence order):

1. The `/config` in-chat command at runtime
2. Command-line arguments when running `pluscoder` command.
3. Dotenv variables ( `.env` file in the repository root)
4. `.pluscoder-config.yml` config file in the repository root
5. Environment variables
6. Global PlusCoder yaml config file (`~/.config/pluscoder/config.yml` or `AppData/Local/pluscoder/config.yml`)
7. Global environment variables file (`~/.config/pluscoder/vars.env` or `AppData/Local/pluscoder/vars.env`)

Same option can be configured using different methods as mentioned:

=== "CLI"
    ```bash
    pluscoder --model gpt-4o
    # other options...
    ```
=== ".env"
    ```bash
    MODEL=gpt-4o
    # other options...
    ```
=== ".pluscoder-config.yml"
    ```yaml
    model: gpt-4o
    # other options...
    ```
=== "Env Vars"
    ```bash
    export MODEL=gpt-4o
    pluscoder
    ```
=== "Global config.yml"
    ```yaml
    model: gpt-4o
    # other options...
    ```
=== "Global vars.env"
    ```bash
    MODEL=gpt-4o
    # other options...
    ```

!!! warning "Credentials"
    Credentials and keys must be provided as environment variables, using `.env` or global `~/.config/pluscoder/vars.env` env file. Passing credentials in other files won't work.

To display current configuration settings, run in-chat command `/show_config` or pass config flag `show_config`.

```bash
pluscoder --show_config
```

!!! note "Global configuration files location"
    `--show_config` will also display configuration files location specific to your operating system.

## Configuration options

### Application Behavior
- `read_only`: Enable/disable read-only mode to avoid file editions (default: `False`)
- `streaming`: Enable/disable LLM streaming (default: `True`)
- `auto_confirm`: Enable/disable auto confirmation of pluscoder execution (default: `False`)
- `hide_thinking_blocks`: Hide thinking blocks in LLM output (default: `True`)
- `hide_output_blocks`: Hide output blocks in LLM output (default: `False`)
- `hide_source_blocks`: Hide source blocks in LLM output (default: `False`)
- `show_token_usage`: Show token usage/cost (default: `True`)
- `default_agent`: Specify the name/number of the default agent to use. If not specified selection will be interactive (default: `None`)

### File Paths
- `log_filename`: Filename for logs (default: `"pluscoder.log"`)

### Models and Providers

*Models*:

- `model`: LLM model to use. Required. (default: `None`)
- `orchestrator_model`: LLM model to use for orchestrator (default: same as `MODEL`)
- `embedding_model`: Embedding model to use for building vector database of the repository (default: `None`).

!!! info "Indexing with Embedding Model"
    To improve LLMs performance, we strongly recommend using an embedding model. This will allow PlusCoder to index the repository and provide better context to the AI. Check some examples at [Indexing](documentation/indexing.md).

*Provider*:

- `provider`: LLM provider to use. If `None`, provider will be selected based on available environment variables credentials. Options: `aws_bedrock`, `openai`, `litellm`, `anthropic`, `vertexai`, `google` (default: `None`)
- `orchestrator_model_provider`: Provider to use for [orchestrator agent](documentation/agents.md#orchestrator) (default: same as `PROVIDER`)

### Provider Credentials

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

### Repository Settings
Use these when running PlusCoder in remote repositories for automated runs. Check how at [Automated Runs](documentation/automation.md).

- `repository`: Git repository path or URL to clone and process (default: `None`)
- `source_branch`: Specify source branch to checkout when cloning repository (default: `None`)
- `repo_exclude_files`: List of regex patterns to exclude files from repo operations (default: `[]`)
- `repo_include_only_files`: List of regex patterns to include only specific files from repo operations (default: `[]`)

=== ".pluscoder-config.yml"
```yaml
# exclude files based on their extensions from agents context
repo_exclude_files: [".(png|jpg|jpeg|svg)"]
# include only Python and Markdown files
repo_include_only_files: [".py"]
```

!!! warning "Known issue"
    Do not use \\ (backslash) symbol in the regex patterns to scape characters, yaml won't parse. Use `.` instead.
  
### Git Settings

- `auto_commits`: Enable/disable automatic Git commits after successful agent file editions (default: `False`)
- `allow_dirty_commits`: Allow commits in a dirty repository (default: `False`)

### Test and Lint Settings
Tests and Lint commands are executed after any file edition. Agents will try to fix any error found by these commands.

- `run_tests_after_edit`: Run tests after file edits (default: `False`)
- `run_lint_after_edit`: Run linter after file edits (default: `False`)
- `test_command`: Command to run tests (default: `None`)
- `lint_command`: Command to run linter (default: `None`)
- `auto_run_linter_fix`: Automatically run linter fix before linting (default: `False`)
- `lint_fix_command`: Command to run linter fix (default: `None`)

=== ".pluscoder-config.yml"
```yaml
run_tests_after_edit: true
run_lint_after_edit: true
auto_run_linter_fix: true
test_command: make test
lint_command: make lint
lint_fix_command: make lint-fix
```

### Custom Prompt Commands

Custom prompt commands allow you to define pre-configured prompts/instruction that can be easily executed during runtime and passed to agents.

- `custom_prompt_commands`: List of custom prompts (default: `[]`). Each containing:
    - `prompt_name`: A unique name for the command
    - `description`: A brief description of what the command does
    - `prompt`: The prompt suffix text to be sent to the agent along a custom message

=== ".pluscoder-config.yml"
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
      Follow instructions above without editing files
```

During the chat in the interactive mode, you can use these custom instructions as follows:

=== "In-chat"
```bash
/custom docstring
/custom brainstorm i want a new api endpoints to register users and authenticate them
```
### Custom Agents

PlusCoder supports the creation of custom agents with different specializations. These agents can be defined in the configuration and used alongside the predefined agents.

- `custom_agents` List of custom agent configurations (default: `[]`). Each containing:
     - `name`: A unique name for the agent
     - `description`: a description of the agent
     - `prompt`: The system prompt defining the agent's role and capabilities
     - `repository_interaction`: Where or not the agent can interact with the repository. Useful for agents repository agnostic.
     - `read_only`: Boolean indicating whether the agent is restricted to read-only file operations
     - `reminder`: Reminder to the agent to send with every user message
     - `default_context_files`: Files that the agent will read automatically every chat session or execution

=== ".pluscoder-config.yml"
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

Custom agents can be selected at the start of the chat in the interactive mode, by using `default_agent` option or by using the `/agent` command followed by the agent name.

=== "CLI"
    ```bash
    # choose agent by name
    pluscoder --default_agent codereviewer
    # or by number in the given list
    pluscoder --default_agent 4
    ```
=== "In-chat"
    ```bash
    /agent CodeReviewer
    ```

You can also create a custom agent using the `/agent_create` [command](documentation/commands#agent-creation).

## Related Docs
- [Agents](agents.md)
- [CLI Usage](cli.md)