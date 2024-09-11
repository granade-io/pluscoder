import asyncio
from pathlib import Path
from pluscoder.type import AgentState, OrchestrationState, TokenUsage
from langchain_core.messages import HumanMessage
from pluscoder.config import config
from pluscoder.io_utils import io
from pluscoder.repo import Repository
from pluscoder.state_utils import get_model_token_info

from pluscoder.workflow import run_workflow

INIT_FILE = '.plus_coder.json'

SETUP_PROMPT = """
Your objective is to fully understand this repository, add md files to improve readability, detect coding standards, and generate/update relevant core .md files. You will delegate tasks to sub-agents who will complete specific aspects of this mission.

For that:
1. **Read and analyze** key files of this repository to understand its purpose, structure, and functionality. This includes:
   - **Configuration files**: such as `docker-compose.yml`, `Dockerfile`, `.gitlab-ci.yml`
   - **Dependency files**: such as `requirements.txt`, `package.json`, etc
   - **Source files**: located in `src/`, `app/`, etc.
   - **Tests and utilities**: located in `tests/`, `src/utils/`, etc.

2. **Adapt, Generate and Delegate Task List**: You will delegate the following tasks to sub-agents to assist with this analysis. Adapt each task with real file paths of this repository, specific objectives, and detailed instructions about your previous analysis you did the code base. 
    - Only `PROJECT_OVERVIEW.md`, `CODING_GUIDELINES.md`, and env files are allowed to be updated/edited in this process.
    - Update tasks in the list below to include context of this project and file paths
    - DO NOT add any new task to the list

### Task Delegation:

General Objective: Understand this new project repository and its key points

### [1] **Understand the Project and Generate Project Overview**:
   - **Objective**: Provide a clear, high-level summary of the repository’s purpose, key features, and stack.
   - **Details**: Read the following key files to gather the necessary information:
      - `README.md` or any existing project documentation (for initial context).
      - Configuration files such as `docker-compose.yml`, `Dockerfile`, `.gitlab-ci.yml` to understand the deployment, CI/CD structure.
      - Review source files in `src/` or `app/` to identify the core functionality.
      - Summarize the project’s purpose, goals, infrastructure, and key technologies in `PROJECT_OVERVIEW.md`. Ensure relationships with other core files are included (e.g., how the `Dockerfile` supports deployment or how `.gitlab-ci.yml` relates to CI/CD).
   - **Agent**: Stakeholder Agent

### [2] **Create Core File Descriptions**:
   - **Objective**: Append descriptions for core project files in the `PROJECT_OVERVIEW.md` to assist future developers.
   - **Details**: Analyze and document the key files in the project:
      - Critical files include: <INCLUDE RECOMMENDED FILES HERE>
      - Provide concise explanations of what each file does, and how they interact within the project. These explanations will help maintainers understand the flow and structure of the repository.
      - Reference any files or summaries generated in Task 1 to ensure consistency between tasks.
   - **Agent**: Stakeholder Agent

### [3] **Define and Update Coding Guidelines**:
   - **Objective**: Identify coding practices and standards used within the codebase and document them in `CODING_GUIDELINES.md`.
   - **Details**: The agent must:
      - Analyze files focusing on existing patterns, utilities, reusable functions, clases or variables that are already being reused in some files.
      - Analyze also commenting styles, docstring formats, testing, error handling, logging, or any pattern **explicitly present** in the code base.
      - Only write coding standards that are **explicitly present in the code**. For example, if docstrings follow a specific format like PEP257, this should be noted with a **brief** description and **code example**.
      - Ensure the guidelines remain concise and directly applicable to this repository. Do not introduce general standards—focus only on **what is visible in the code**.
      - Path examples to inspect: `src/utils/`, `tests/`, `src/main.py`, `src/config.py`
      - Ensure that the `CODING_GUIDELINES.md` integrates seamlessly with `PROJECT_OVERVIEW.md` created in Task 1.
   - **Agent**: Stakeholder Agent

### [4] **Update `.env` Configuration for Developer Tools**:
   - **Objective**: Create or update a `.env` file with configurations for running tests, linting, and automated lint fixes.
   - **Details**: Based on the repository setup, the agent must:
      - Identify the test command used by inspecting files such as `package.json` (Node.js), `setup.py` (Python), requirements or other relevante files
      - Detect linting tools and relevant commands (`eslint`, `flake8`, `pylint`, etc).
      - Inspect paths like `package.json`, `requirements.txt`, `tests/`, `.gitlab-ci.yml` to determine the correct commands for running tests, linting, and lint fixes.
      - Check CODING_GUIDELINES.md file for any testing information
      - Insert the following values into the `.env` file (create it if it doesn’t exist):
        ```
        RUN_TESTS_AFTER_EDIT=false
        RUN_LINT_AFTER_EDIT=false
        TEST_COMMAND=<detected_test_command>
        LINT_COMMAND=<detected_lint_command>
        AUTO_RUN_LINTER_FIX=false
        LINT_FIX_COMMAND=<detected_lint_fix_command>
        ```
   - **Agent**: Stakeholder Agent

*After analyzing files and adapt the plan delegate it inmediately the more complete possible without further confirmation.*
"""

def initialize_repository():
    io.event("Starting repository initialization...")
    
    # Setup config to automatize agents calls
    auto_confirm = config.auto_confirm
    use_repomap = config.use_repomap
    config.auto_confirm = True
    config.use_repomap = True
    
    initial_state = OrchestrationState(**{
        "return_to_user": False,
        "orchestrator_state": AgentState(messages=[
            HumanMessage(content="""Please perform the following initialization tasks for this repository:
1. Read key files of the project and summarize them in the PROJECT_OVERVIEW.md file.
2. Detect linting and test commands used in this repository and document them in the PROJECT_OVERVIEW.md file.
3. Iterate over all Python files in the project and improve their docstrings where necessary.""")
        ]),
        "domain_stakeholder_state": AgentState.default(),
        "planning_state": AgentState.default(),
        "developer_state": AgentState.default(),
        "domain_expert_state": AgentState.default(),
        "accumulated_token_usage": TokenUsage.default(),
        "chat_agent": "orchestrator",
    })

    asyncio.run(run_workflow(initial_state))
    
    # Restore config values
    config.auto_confirm = auto_confirm
    config.use_repomap = use_repomap
    
    Path(INIT_FILE).touch()

def setup() -> bool:
    
    if not Path(INIT_FILE).exists():
        if io.confirm("Pluscoder hasn't been initialized for this repository. Do you want to initialize it now?"):
            initialize_repository()
        else:
            io.event("Skipping initialization. You can run it later using the /init command.")
    
    # Check repository setup
    repo = Repository(io=io)
    if not repo.setup():
        io.console.print("Exiting pluscoder", style="bold dark_goldenrod")
        return False
    
    # Warns token cost
    if not get_model_token_info(config.model):
        io.console.print(f"Token usage info not available for model `{config.model}`. Cost calculation can be unaccurate.", style="bold dark_goldenrod")
    
    return True

def force_init():
    io.event("Forcing repository initialization...")
    initialize_repository()