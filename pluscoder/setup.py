import asyncio
from pathlib import Path
import yaml
from pluscoder import tools
from pluscoder.type import AgentInstructions, AgentState, OrchestrationState, TokenUsage
from pluscoder.config import config, Settings
from pluscoder.io_utils import io
from pluscoder.repo import Repository
from pluscoder.state_utils import get_model_token_info

from pluscoder.workflow import run_workflow
from rich.prompt import Prompt
CONFIG_FILE = '.pluscoder-config.yml'
CONFIG_OPTIONS = [
    'model', 'provider', 'auto_commits', 'allow_dirty_commits'
]

def get_config_descriptions():
    return {field: Settings.model_fields[field].description for field in CONFIG_OPTIONS}

def get_config_defaults():
    return {field: getattr(config, field) for field in CONFIG_OPTIONS}

def read_yaml(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

def write_yaml(file_path, data):
    with open(file_path, 'w') as file:
        yaml.dump(data, file)

def prompt_for_config():
    config_data = {}
    descriptions = get_config_descriptions()
    defaults = get_config_defaults()

    for option in CONFIG_OPTIONS:
        description = descriptions[option]
        default = defaults[option]

        prompt = f"{option} ({description})"
        
        if isinstance(default, bool):
            value = Prompt.ask(prompt, default=str(default).lower(), choices=["true", "false"])
            value = value.lower() == "true"
        elif isinstance(default, int):
            value = Prompt.ask(prompt, default=str(default), validator=int)
        elif isinstance(default, float):
            value = Prompt.ask(prompt, default=str(default), validator=float)
        else:
            value = Prompt.ask(prompt, default=str(default))

        config_data[option] = value

    return config_data


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
        "agent": "domain_stakeholder",
        "completed": False,
        "is_finished": False
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
        "agent": "domain_stakeholder",
        "completed": False,
        "is_finished": False
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
        "agent": "domain_stakeholder",
        "completed": False,
        "is_finished": False
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
        "agent": "domain_stakeholder",
        "completed": False,
        "is_finished": False
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
    io.event("> Starting repository initialization...")
    
    # Setup config to automatize agents calls
    auto_confirm = config.auto_confirm
    use_repomap = config.use_repomap
    auto_commits = config.auto_commits
    config.auto_confirm = True
    config.use_repomap = True
    config.auto_commits = False
    
    orchestrator_state = AgentState.default()
    orchestrator_state["tool_data"][tools.delegate_tasks.name] = AgentInstructions(
        general_objective="Number test sequence",
        task_list=TASK_LIST
        ).dict()
    
    initial_state = OrchestrationState(**{
        "return_to_user": False,
        "orchestrator_state": orchestrator_state,
        "domain_stakeholder_state": AgentState.default(),
        "planning_state": AgentState.default(),
        "developer_state": AgentState.default(),
        "domain_expert_state": AgentState.default(),
        "accumulated_token_usage": TokenUsage.default(),
        "chat_agent": "orchestrator",
        "is_task_list_workflow": True,
    })

    asyncio.run(run_workflow(initial_state))
    
    # Restore config values
    config.auto_confirm = auto_confirm
    config.use_repomap = use_repomap
    config.auto_commits = auto_commits
    
    # Check if both files were created
    if not (Path(config.overview_file_path).exists() and Path(config.guidelines_file_path).exists()):
        io.console.print("Error: Could not create `PROJECT_OVERVIEW.md` and `CODING_GUIDELINES.md`. Please try again.", style="bold red")
        return
    
    io.event("> Repository initialization completed.")
    io.console.print("Files `PROJECT_OVERVIEW.md` and `CODING_GUIDELINES.md` were generated and will be used as context for Pluscoder.\n")

def setup() -> bool:
    repo = Repository(io=io)
    
    if not Path(CONFIG_FILE).exists() and config.init:
        
        io.console.print("Welcome to Pluscoder! Let's customize your project configuration.", style="bold green")
        
        # Prompt for configuration
        config_data = prompt_for_config()
        write_yaml(CONFIG_FILE, config_data)
        repo.create_default_files()
        
        io.event(f"> Configuration saved to {CONFIG_FILE}.")

        io.console.print("Initialization will analyze your project for better agent assistance generating `PROJECT_OVERVIEW.md` and `CODING_GUIDELINES.md` files.")
        if io.confirm("Do you want to initialize it now (takes ~1min)? (recommended)"):
            initialize_repository()
            
            
            io.event(f"> Configuration saved to {CONFIG_FILE}")
        else:
            io.event("> Skipping initialization. You can run it later using the /init command.")
            
            # Create a default configuration file
            write_yaml(CONFIG_FILE, {'initialized': False})
    elif not Path(CONFIG_FILE).exists() and not config.init:
        io.event("> Skipping initialization due to --no-init flag.")
        # Path.touch(CONFIG_FILE)
        

    # Check repository setup
    if not repo.setup():
        io.event("> Exiting pluscoder")
        return False
    
    # Warns token cost
    if not get_model_token_info(config.model):
        io.console.print(f"Token usage info not available for model `{config.model}`. Cost calculation can be unaccurate.", style="bold dark_goldenrod")
        
    
    return True