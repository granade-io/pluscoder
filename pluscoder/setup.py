import asyncio
import os
import re
from pathlib import Path

from rich.prompt import Prompt

from pluscoder import tools
from pluscoder.config import Settings
from pluscoder.config import config
from pluscoder.exceptions import GitCloneException
from pluscoder.exceptions import NotGitRepositoryException
from pluscoder.io_utils import io
from pluscoder.model import get_default_model_for_provider
from pluscoder.model import get_inferred_provider
from pluscoder.model import get_model_validation_message
from pluscoder.repo import Repository
from pluscoder.type import AgentInstructions
from pluscoder.type import TokenUsage

# TODO: Move this?
CONFIG_FILE = ".pluscoder-config.yml"
CONFIG_OPTIONS = ["provider", "model", "auto_commits", "allow_dirty_commits"]

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
# overview_filename: PROJECT_OVERVIEW.md     # Project overview filename
# log_filename: pluscoder.log                # Log filename
# overview_file_path: PROJECT_OVERVIEW.md    # Path to project overview file
# guidelines_file_path: CODING_GUIDELINES.md # Path to coding guidelines file

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
        io.console.print(error_msg, style="bold red")

    return example_config_text


def additional_config():
    gitignore_path = ".gitignore"
    files_to_ignore = ["PROJECT_OVERVIEW.md", "CODING_GUIDELINES.md"]

    if os.path.exists(gitignore_path):
        with open(gitignore_path) as f:
            content = f.read().splitlines()

        files_to_add = [file for file in files_to_ignore if file not in content]

        if files_to_add:
            if io.confirm(f"Do you want to add {', '.join(files_to_add)} to .gitignore?"):
                with open(gitignore_path, "a") as f:
                    f.write("\n" + "\n".join(files_to_add) + "\n")
                io.event(f"> Added {', '.join(files_to_add)} to .gitignore")
            else:
                io.event("> No changes made to .gitignore")
        else:
            io.event("> PROJECT_OVERVIEW.md and CODING_GUIDELINES.md are already in .gitignore")
    elif io.confirm(
        "> .gitignore file not found. Do you want to create it with PROJECT_OVERVIEW.md and CODING_GUIDELINES.md?"
    ):
        with open(gitignore_path, "w") as f:
            f.write("\n".join(files_to_ignore) + "\n")
        io.event("> Created .gitignore with PROJECT_OVERVIEW.md and CODING_GUIDELINES.md")
    else:
        io.event("> Skipped creating .gitignore")

    # DEfault ignore files
    git_dir = Path(".git")
    exclude_file = git_dir / "info" / "exclude"
    exclude_file.parent.mkdir(parents=True, exist_ok=True)

    with open(exclude_file, "a+") as f:
        f.seek(0)
        content = f.read()
        if ".pluscoder/" not in content:
            f.write("\n.pluscoder/")


TASK_LIST = [
    {
        "objective": "Provide a high-level summary of the repository’s purpose, key features, and technology stack to offer clear context for future developers.",
        "details": """
        - Review key files that define the project detailed description, structure, configuration, and deployment. Example files may include:
            - `README.md` or any existing documentation for an initial understanding of the project.
            - Source files located in directories such as `src/` or `app/` to understand the core functionality and implementation.
            - Configuration files like `docker-compose.yml`, `Dockerfile`, `.gitlab-ci.yml` to analyze how the project is set up for deployment and CI/CD.
        - Document the project's purpose, architecture, infrastructure (e.g., CI/CD pipelines, containerization), and key components in `PROJECT_OVERVIEW.md`.
        - Ensure the overview includes relationships between core components (e.g., how the Dockerfile facilitates deployment, or how CI/CD pipelines are managed).
        """,
        "restrictions": "Use example files for reference, but adapt based on the actual structure of the repository. Do not modify any `.md` files other than `PROJECT_OVERVIEW.md`.",
        "outcome": "A high-level project summary documented in `PROJECT_OVERVIEW.md`, providing details into the repository’s architecture, purpose, and structure aimed for other developers to understand the project.",
        "agent": "developer",
        "completed": False,
        "is_finished": False,
    },
    {
        "objective": "Provide concise descriptions of the core project files to assist maintainers and future developers in understanding the purpose and structure of the repository.",
        "details": """
        - Read the current `PROJECT_OVERVIEW.md` file and identify any additional key files to read to provide context on the project’s structure.
        - Analyze and document key files that form the backbone of the project. Examples for reference may include:
            - Most important files: Core source code files such as those found in `src/main.py`, `app/` directory, or equivalent locations.
            - `docker-compose.yml`, `Dockerfile`, CI/CD files, scripts, etc to explain project setup, config, deployment and infrastructure.
            - Dependency files like `requirements.txt`, `package.json` to provide context on the project’s dependencies and libraries.
            - Test files in directories like `tests/` and utility files in directories such as `src/utils/`.
        - For each key file, provide a brief explanation of its purpose, functionality, and how it fits within the overall structure of the project.
        """,
        "restrictions": "Focus on source code files. Use example files for reference only. Adapt to the repository’s actual structure. Do not introduce descriptions for unnecessary files.",
        "outcome": "A new section in `PROJECT_OVERVIEW.md` with descriptions of the key project files, giving future developers a clear understanding of the repository’s structure and file interactions.",
        "agent": "developer",
        "completed": False,
        "is_finished": False,
    },
    {
        "objective": "Detect code that is reused or imported multiple times across different files to identify reusable patterns such as constants, functions, or classes. Document these patterns in `CODING_GUIDELINES.md` to provide visibility for future developers.",
        "details": """
        - Review files in the repository to locate:
            - **Reusable constants**: Identify global constants or configuration variables that are reused across multiple files.
            - **Functions and Classes**: Detect utility functions, helper methods, or classes that are imported or used in multiple parts of the codebase.
        - Focus only on code that is explicitly reused or imported across different files. Include:
            - File paths where the code is reused.
            - A brief description of what the reused code does and why it’s beneficial to reuse in multiple locations.
        - Document the identified reusable patterns in `CODING_GUIDELINES.md` and provide examples of how to use these patterns effectively in the repository.
        """,
        "restrictions": "Only document code that is reused across multiple files. Avoid generalizing patterns unless there is explicit reuse.",
        "outcome": "A section in `CODING_GUIDELINES.md` that highlights reusable constants, functions, and classes, including their file paths, descriptions, and examples of usage, providing guidance for maintaining reusability in the repository.",
        "agent": "developer",
        "completed": False,
        "is_finished": False,
    },
    {
        "objective": "Identify and document specific coding standards, conventions, and patterns within the repository that do not relate to code reuse but provide clear structure and practices for future developers.",
        "details": """
        - Focus on the following aspects:
            - **Class and Function Naming Conventions**: Document naming conventions for classes and functions (e.g., PascalCase for classes, snake_case for functions).
            - **Code Structure and File Organization**: Identify patterns on how the codebase is structured and organized (e.g., grouping of related functionalities, file naming conventions, or decoupling strategies between business logic and infrastructure).
            - **Error Handling**: Analyze how errors are handled throughout the codebase (e.g., consistent use of `try/except`, custom error classes, or error logging conventions).
            - **Logging Practices**: Identify if there are any standards for logging, such as using a centralized logging utility or class (e.g., formatting standards, log levels, or centralized log files).
            - **Commenting and Documentation**: Identify patterns in docstrings or comments, including preferred formats (e.g., PEP257 for Python or JSDoc for JavaScript). Provide examples of how to correctly document code.
            - **Configuration and Environment Handling**: Check how environment variables or configuration settings are managed (e.g., in `.env` or config files) and if there are established patterns for handling configurations consistently across the project.
        - Provide **brief explanations** and **code examples** to clarify each of these patterns and standards for future developers.
        - Ensure alignment with any findings documented in the `PROJECT_OVERVIEW.md` from Task 1 to provide consistency across the repository's documentation.
        """,
        "restrictions": "Focus on non-reuse patterns, avoiding overlap with Task 5, which handles code reuse. Only document explicit standards found in the repository.",
        "outcome": "An updated `CODING_GUIDELINES.md` providing detailed documentation on naming conventions, error handling, logging, file organization, and documentation practices, with examples to guide future developers.",
        "agent": "developer",
        "completed": False,
        "is_finished": False,
    },
    # {
    #     "objective": "Create or update a `.env` file with configurations for running tests, linting, and lint fixes based on the repository setup.",
    #     "details": """
    #     - Inspect `package.json`, `requirements.txt`, `tests/`, and `.gitlab-ci.yml` to detect relevant test and linting commands.
    #     - Identify the correct commands for testing (`<detected_test_command>`), linting (`<detected_lint_command>`), and lint fixes (`<detected_lint_fix_command>`).
    #     - Populate the `.env` file or create it with the following values:
    #         ```
    #         RUN_TESTS_AFTER_EDIT=false
    #         RUN_LINT_AFTER_EDIT=false
    #         TEST_COMMAND=<detected_test_command>
    #         LINT_COMMAND=<detected_lint_command>
    #         AUTO_RUN_LINTER_FIX=false
    #         LINT_FIX_COMMAND=<detected_lint_fix_command>
    #         ```
    #     """,
    #     "restrictions": "Only add configurations for detected commands. Do not introduce new tools or commands not found in the repository.",
    #     "outcome": "An updated `.env` file with accurate commands for running tests, linting, and automated lint fixes based on the repository’s configuration.",
    #     "agent": "domain_stakeholder",
    #     "completed": False,
    #     "is_finished": False
    # }
]


def initialize_repository():
    from pluscoder.workflow import build_agents
    from pluscoder.workflow import build_workflow
    from pluscoder.workflow import run_workflow

    io.event("> Starting repository initialization...")
    agents_configs = build_agents()
    app = build_workflow(agents_configs)

    # Setup config to automatize agents calls
    auto_confirm = config.auto_confirm
    use_repomap = config.use_repomap
    auto_commits = config.auto_commits
    config.auto_confirm = True
    config.use_repomap = False
    config.auto_commits = False

    tool_data = {}
    tool_data[tools.delegate_tasks.name] = AgentInstructions(
        general_objective="Number test sequence",
        task_list=TASK_LIST,
        resources=[],
    ).dict()

    initial_state = {
        "agents_configs": agents_configs,
        "chat_agent": agents_configs["orchestrator"],
        "status": "active",
        "max_iterations": 1,
        "current_iterations": 0,
        "messages": [],
        "tool_data": tool_data,
        "return_to_user": False,
        "accumulated_token_usage": TokenUsage.default(),
        "token_usage": None,
        "is_task_list_workflow": True,
        "max_agent_deflections": 2,
        "current_agent_deflections": 0,
    }

    asyncio.run(run_workflow(app, initial_state))

    # Restore config values
    config.auto_confirm = auto_confirm
    config.use_repomap = use_repomap
    config.auto_commits = auto_commits

    # Check if both files were created
    if not (Path(config.overview_file_path).exists() and Path(config.guidelines_file_path).exists()):
        io.console.print(
            "Error: Could not create `PROJECT_OVERVIEW.md` and `CODING_GUIDELINES.md`. Please try again.",
            style="bold red",
        )
        return

    # Update the 'initialized' field in persistent mode
    config.update(initialized="true", persist=True)

    io.event("> Repository initialization completed.")
    io.console.print(
        "Files `PROJECT_OVERVIEW.md` and `CODING_GUIDELINES.md` were generated and will be used as context for Pluscoder.\n"
    )


def setup() -> bool:
    # TODO: Get repository path from config
    try:
        repo = Repository(io=io, repository_path=config.repository, validate=True)
        repo.change_repository(repo.repository_path)
        config.reconfigure()
    except GitCloneException as e:
        io.console.print(str(e), style="bold red")
        return False
    except NotGitRepositoryException as e:
        io.console.print(str(e), style="bold red")
        return False
    except ValueError as e:
        io.console.print(f"Invalid repository path: {e}", style="bold red")
        return False

    if (not Path(CONFIG_FILE).exists() or not config.initialized) and config.init:
        io.console.print(
            "Welcome to Pluscoder! Let's customize your project configuration.",
            style="bold green",
        )

        # Load example config and prompt for configuration
        config_data = prompt_for_config()

        # Write the updated config & update re-initialize config
        write_yaml(CONFIG_FILE, config_data)
        config.__init__(**{})

        repo.create_default_files()

        io.event(f"> Configuration saved to {CONFIG_FILE}.")

        # Additional configuration
        additional_config()

        io.console.print(
            "Initialization will analyze your project for better agent assistance generating `PROJECT_OVERVIEW.md` and `CODING_GUIDELINES.md` files."
        )
        if io.confirm("Do you want to initialize it now (takes ~1min)? (recommended)"):
            initialize_repository()
        else:
            io.event("> Skipping initialization. You can run it later using the /init command.")
    elif not Path(CONFIG_FILE).exists() and not config.init:
        io.event("> Skipping initialization due to --no-init flag.")
        # Path.touch(CONFIG_FILE)

    # Check repository setup
    if not repo.setup():
        io.event("> Exiting pluscoder")
        return False
    return True
