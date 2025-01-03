import re
from pathlib import Path

from rich.prompt import Prompt

from pluscoder.config import Settings
from pluscoder.config import config
from pluscoder.exceptions import GitCloneException
from pluscoder.exceptions import NotGitRepositoryException
from pluscoder.io_utils import io
from pluscoder.repo import Repository

# TODO: Move this?
CONFIG_FILE = ".pluscoder-config.yml"
CONFIG_OPTIONS = ["provider", "model", "embedding_model", "auto_commits", "allow_dirty_commits"]

CONFIG_TEMPLATE = """
#------------------------------------------------------------------------------
# PlusCoder Configuration
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
# Application Behavior
#------------------------------------------------------------------------------
# streaming: true                 # Enable/disable LLM streaming
# user_feedback: true             # Enable/disable user feedback
# display_internal_outputs: false # Display internal agent outputs
# auto_confirm: false             # Auto-confirm pluscoder execution
# init: true                      # Enable/disable initial setup
# initialized: false              # Pluscoder was or not initialized
# read_only: false                # Enable/disable read-only mode
# user_input: ""                  # Predefined user input

#------------------------------------------------------------------------------
# File Paths
#------------------------------------------------------------------------------
# log_filename: pluscoder.log                # Log filename

#------------------------------------------------------------------------------
# Model and API Settings
#------------------------------------------------------------------------------
# model: anthropic.claude-3-5-sonnet-20240620-v1:0 # LLM model to use
# orchestrator_model: null            # Model to use for the orchestrator agent (default: same as model)
# weak_model: null                    # Weaker LLM model for less complex tasks (default: same as model)
# provider: null                      # Provider (aws_bedrock, openai, litellm, anthropic, vertexai)
# orchestrator_model_provider: null   # Provider for orchestrator model (default: same as provider)
# weak_model_provider: null           # Provider for weak model (default: same as provider)

#------------------------------------------------------------------------------
# Git Settings
#------------------------------------------------------------------------------
# auto_commits: true       # Enable/disable automatic Git commits
# allow_dirty_commits: true # Allow commits in a dirty repository

#------------------------------------------------------------------------------
# Test and Lint Settings
#------------------------------------------------------------------------------
# run_tests_after_edit: false  # Run tests after file edits
# run_lint_after_edit: false   # Run linter after file edits
# test_command:                # Command to run tests
# lint_command:                # Command to run linter
# auto_run_linter_fix: false   # Auto-run linter fix before linting
# lint_fix_command:            # Command to run linter fix

#------------------------------------------------------------------------------
# Repomap Settings
#------------------------------------------------------------------------------
# use_repomap: false           # Enable/disable repomap feature
# repomap_level: 2             # Repomap detail level (0: minimal, 1: moderate, 2: detailed)
# repomap_exclude_files: []    # List of files to exclude from repomap
# repo_exclude_files: []       # Regex patterns to exclude files from repo operations

#------------------------------------------------------------------------------
# Display Options
#------------------------------------------------------------------------------
# show_repo: false             # Show repository information
# show_repomap: false          # Show repository map
# show_config: false           # Show configuration information
# hide_thinking_blocks: false  # Hide thinking blocks in LLM output
# hide_output_blocks: false    # Hide output blocks in LLM output
# hide_source_blocks: false    # Hide source blocks in LLM output

#------------------------------------------------------------------------------
# Custom Prompt Commands
#------------------------------------------------------------------------------
# Customs instructions to agents when using /custom <prompt_name> <additional instruction>
# Example: /custom hello then ask what are their needs
# custom_prompt_commands:
#   - prompt_name: hello
#     description: Greet the user says hello
#     prompt: Say hello to user

#------------------------------------------------------------------------------
# Custom Agents
#------------------------------------------------------------------------------
# Define custom agents with specific roles and capabilities
# custom_agents:
#   - name: CodeReviewer
#     prompt: "You are a code reviewer. Your task is to review code changes and provide feedback on code quality, best practices, and potential issues."
#     description: "Code reviewer"
#     read_only: true
#   - name: DocumentationWriter
#     prompt: "You are a technical writer specializing in software documentation. Your task is to create and update project documentation, including README files, API documentation, and user guides."
#     description: "Documentation Writer Description"
#     read_only: false
#   - name: SecurityAuditor
#     prompt: "You are a security expert. Your task is to review code and configurations for potential security vulnerabilities and suggest improvements to enhance the overall security of the project."
#     description: "Security Auditor Description"
#     read_only: true
"""


def get_config_descriptions():
    return {field: Settings.model_fields[field].description for field in CONFIG_OPTIONS}


def get_config_defaults():
    return {field: getattr(config, field) for field in CONFIG_OPTIONS}


def read_file_as_text(file_path):
    try:
        with open(file_path) as file:
            return file.read()
    except FileNotFoundError:
        return ""


def load_example_config():
    return CONFIG_TEMPLATE


def write_yaml(file_path, data):
    with open(file_path, "w") as file:
        file.write(data)


def prompt_for_config():
    from pluscoder.model import get_default_embedding_model
    from pluscoder.model import get_default_model_for_provider
    from pluscoder.model import get_inferred_provider
    from pluscoder.model import get_model_validation_message

    example_config_text = load_example_config()
    descriptions = get_config_descriptions()
    current_config = get_config_defaults()

    for option in CONFIG_OPTIONS:
        description = descriptions[option]
        if option == "provider" and not config.provider:
            default = get_inferred_provider()
        elif option == "model":
            default = config.model or get_default_model_for_provider(current_config.get("provider"))
            current_config[option] = default
        elif option == "embedding_model":
            default = config.embedding_model or get_default_embedding_model(current_config.get("provider"))
            current_config[option] = default
        else:
            default = current_config[option]

        prompt = f"{option} ({description})"

        if isinstance(default, bool):
            value = Prompt.ask(prompt, default=str(default).lower(), choices=["true", "false"])
            value = value.lower() == "true"
        elif isinstance(default, int):
            value = Prompt.ask(prompt, default=str(default), validator=int)
        elif isinstance(default, float):
            value = Prompt.ask(prompt, default=str(default), validator=float)
        else:
            value = Prompt.ask(prompt, default=str(default) if default is not None else "null")

        # Update the config text with the new value
        current_config[option] = value
        example_config_text = re.sub(
            rf"^#?\s*{option}:.*$",
            f"{option}: {value}",
            example_config_text,
            flags=re.MULTILINE,
        )

    if not current_config["provider"]:
        io.event(f"> Inferred provider is '{get_inferred_provider()}'")

    error_msg = get_model_validation_message(current_config["provider"])
    if error_msg:
        io.print(error_msg, style="bold red")

    return example_config_text


def additional_config():
    # Default ignore files
    git_dir = Path(".git")
    exclude_file = git_dir / "info" / "exclude"
    exclude_file.parent.mkdir(parents=True, exist_ok=True)

    with open(exclude_file, "a+") as f:
        f.seek(0)
        content = f.read()
        if ".pluscoder/" not in content:
            f.write("\n.pluscoder/")


def setup() -> bool:
    # TODO: Get repository path from config
    try:
        repo = Repository(io=io, repository_path=config.repository, validate=True)
        repo.change_repository(repo.repository_path)
        config.reconfigure()
    except GitCloneException as e:
        io.print(str(e), style="bold red")
        return False
    except NotGitRepositoryException as e:
        io.print(str(e), style="bold red")
        return False
    except ValueError as e:
        io.print(f"Invalid repository path: {e}", style="bold red")
        return False

    if (not Path(CONFIG_FILE).exists() or not config.initialized) and config.init:
        io.print(
            "Welcome to Pluscoder! Let's customize your project configuration.",
            style="bold green",
        )

        # Load example config and prompt for configuration
        config_data = prompt_for_config()

        # Write the updated config & update re-initialize config
        write_yaml(CONFIG_FILE, config_data)
        config.__init__(**{})

        io.event(f"> Configuration saved to {CONFIG_FILE}.")

        # Additional configuration
        additional_config()

    elif not Path(CONFIG_FILE).exists() and not config.init:
        io.event("> Skipping initialization due to --no-init flag.")
        # Path.touch(CONFIG_FILE)
    return True
