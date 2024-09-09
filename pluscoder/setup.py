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
Your objective is to understand this repository, edit some files to improve readability and to generate/update some relevant core .md files.add()

For that:
1. Read key files of this repository to understand what is this about. Read config files, Dockerfiles, dependencies, etc. ANY file to understand the project, its cicd, deployment, infrastucture, etc.
2. Generate a Task List to:
    1. Create/Update PROJECT_OVERVIEW.md:
        - Summarize the project's purpose, goals, key features, related infrastructure & stack
        - Include the path of core files the description in the instructions of this task
    2. Add core file tree to PROJECT_OVERVIEW.md:
        - Suggest the agent to read key files, and provide them suggested paths for the task.
        - Ask him to append a file tree with descriptions of each file to the PROJECT_OVERVIEW.md file (or update current file tree if exists)
    3. Create/Update CODING_GUIDELINES.md:
        - Detect some patterns, standards and practices present in the codebase (like docstrings type, repo structure, coding style, utilities, logging, etc.)
        - Include the path of key files that can help with that task
    4. Create/Update .env files with pluscoder configurations only:
        - Based on the project type (python, javascript, node, etc.), requirements and some config files, detect these 3 command: running tests, linting and linting fix
        - Load .env file (or create it if doesn't exist) and append these values:
            RUN_TESTS_AFTER_EDIT=false
            RUN_LINT_AFTER_EDIT=false
            TEST_COMMAND=<detected_test_command>
            LINT_COMMAND=<detected_lint_command>
            AUTO_RUN_LINTER_FIX=false
            LINT_FIX_COMMAND=<detected_lint_fix_command>
    
Based on the previous requirement, you must read key files, and only then generate a task list, with these 4 tasks to delegate.
* WRITE THE PLAN AND DELEGATE THESE TASK TO THE AGENTS INMEDIATELY WITHOUT CONFIRMATION.*
"""

def initialize_repository():
    io.event("Starting repository initialization...")
    
    # Setup config to automatize agents calls
    auto_confirm = config.auto_confirm
    config.auto_confirm = True
    
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