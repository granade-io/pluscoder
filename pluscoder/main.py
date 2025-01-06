#!/usr/bin/env python3
import asyncio
import sys
import traceback
from pathlib import Path

from dotenv import load_dotenv
from rich.prompt import Prompt

from pluscoder.__version__ import __version__
from pluscoder.config import config
from pluscoder.config.utils import get_global_env_filepath
from pluscoder.display_utils import display_agent
from pluscoder.io_utils import io
from pluscoder.repo import Repository


def banner() -> None:
    """Display the Pluscoder banner."""
    io.print(
        f"""
[bold green]
-------------------------------------------------------------------------------

                      @@@@@@@   @@@@@@   @@@@@@@   @@@@@@@@  @@@@@@@
                     @@@@@@@@  @@@@@@@@  @@@@@@@@  @@@@@@@@  @@@@@@@@
             @@!     !@@       @@!  @@@  @@!  @@@  @@!       @@!  @@@
             !@!     !@!       !@!  @!@  !@!  @!@  !@!       !@!  @!@
          @!@!@!@!@  !@!       @!@  !@!  @!@  !@!  @!!!:!    @!@!!@!
          !!!@!@!!!  !!!       !@!  !!!  !@!  !!!  !!!!!:    !!@!@!
             !!:     :!!       !!:  !!!  !!:  !!!  !!:       !!: :!!
             :!:     :!:       :!:  !:!  :!:  !:!  :!:       :!:  !:!
                      ::: :::  ::::: ::   :::: ::   :: ::::  ::   :::
                      :: :: :   : :  :   :: :  :   : :: ::    :   : :

-------------------------------------------------------------------------------

{'Looking for help, check the documentation at'.center(80)}

{'https://gitlab.com/codematos/pluscoder-repository/-/blob/main/README.md'.center(80)}

{'or type ´/help´ to get started'.center(80)}

{f"PlusCoder version: {__version__}".center(80)}

-------------------------------------------------------------------------------
[/bold green]

"""
    )


def parse_task_list():
    """Parse and validate the task list from JSON string or file."""
    import json

    if not config.task_list:
        return None

    try:
        # Parse JSON content
        if config.task_list.strip().startswith(("{", "[")):
            tasks = json.loads(config.task_list)
            source = "JSON string"
        else:
            with open(config.task_list) as f:
                tasks = json.loads(f.read())
            source = f"file '{config.task_list}'"

        # Validate task structure
        required_fields = ["objective", "details", "restrictions", "outcome", "agent"]

        if not isinstance(tasks, list):
            raise ValueError("Task list must be an array of tasks")

        for task in tasks:
            if not isinstance(task, dict):
                raise ValueError("Each task must be a dictionary")

            # Validate required fields
            missing = [field for field in required_fields if field not in task]
            if missing:
                msg = f"Task missing required fields: {', '.join(missing)}"
                raise ValueError(msg)

            # Validate agent exists
            if task["agent"] not in ["domain_stakeholder", "domain_expert", "developer", "planning", "orchestrator"]:
                msg = f"Invalid agent '{task['agent']}' in task '{task['objective']}'"
                raise ValueError(msg)

            # Add default values like in setup.py
            task.setdefault("completed", False)
            task.setdefault("is_finished", False)

        io.event(f"> Loaded {len(tasks)} tasks from {source}")
        return tasks

    except (json.JSONDecodeError, IOError, ValueError) as e:
        io.print(f"Error parsing task list: {e}", style="bold red")
        sys.exit(1)


def run_silent_checks():
    """Run tests and linter silently and return any warnings."""
    repo = Repository(io)
    warnings = []

    test_result = repo.run_test()
    if test_result:
        warnings.append("Tests are failing. This may lead to issues when editing files.")

    lint_result = repo.run_lint()
    if lint_result:
        warnings.append("Linter checks are failing. This may lead to issues when editing files.")
    return warnings


def ask_index_confirmation(tracked_files: int) -> bool:
    io.print("")
    io.event("> Embedding model detected.")
    io.print("Indexing your repository will optimize the performance of Pluscoder agents.")
    io.print(
        "This process may take a few minutes.\n\n"
        "Use '--skip_repo_index' flag to start immediately without indexing.\n"
    )
    return io.confirm(f"Would you like to index the repository now? ({tracked_files} files to index)")


async def initialize_search_engine():
    """Initialize the search engine with appropriate algorithm."""
    from pluscoder.agents.event.config import event_emitter
    from pluscoder.search.algorithms import DenseSearch
    from pluscoder.search.algorithms import HybridSearch
    from pluscoder.search.algorithms import SparseSearch
    from pluscoder.search.chunking import TokenBasedChunking
    from pluscoder.search.embeddings import LiteLLMEmbedding
    from pluscoder.search.engine import SearchEngine

    try:
        io.live.start("indexing")
        storage_dir = Path(".pluscoder") / "search_index"
        chunking = TokenBasedChunking(chunk_size=512, overlap=64)

        # Configure search algorithm and embedding model based on config
        embedding_model = None
        algorithm = SparseSearch()

        if config.embedding_model:
            embedding_model = LiteLLMEmbedding(model_name=config.embedding_model)
            dense = DenseSearch(embedding_model)
            sparse = SparseSearch()
            algorithm = HybridSearch([dense, sparse])

        # Create engine with final configuration
        engine = await SearchEngine.create(
            chunking_strategy=chunking,
            search_algorithm=algorithm,
            storage_dir=storage_dir,
            embedding_model=embedding_model,
        )
        # Connect to global event emitter
        engine.events = event_emitter

        # Get tracked files
        repo = Repository(io)
        files = [Path(f) for f in repo.get_tracked_files()]

        # Check if reindexing needed and ask confirmation
        if config.embedding_model:
            # hybrid search engine being used
            files_to_reindex = engine.index_manager.reindex_needed(files)
            if files_to_reindex and not config.skip_repo_index and ask_index_confirmation(len(files_to_reindex)):
                await engine.build_index(files, reindex=True)
            elif files_to_reindex:
                await engine.build_index(files, reindex=False)
            else:
                await engine.build_index(files, reindex=True)
        else:
            await engine.build_index(files, reindex=True)

        io.live.stop("indexing")

    except Exception as e:
        io.print(f"Error: Failed to initialize search engine: {e}", style="bold red")
        raise


def display_initial_messages():
    """Display initial message with the number of files detected by git, excluded files, and model information."""
    from pluscoder.model import get_inferred_provider
    from pluscoder.model import get_model_token_info
    from pluscoder.model import get_model_validation_message

    banner()

    repo = Repository(io)

    # Get all tracked files (including those in the index) and untracked files
    all_files = set(
        repo.repo.git.ls_files().splitlines() + repo.repo.git.ls_files(others=True, exclude_standard=True).splitlines()
    )

    # Get tracked files after applying exclusion patterns
    tracked_files = repo.get_tracked_files()

    # Calculate the number of excluded files
    excluded_files_count = len(all_files) - len(tracked_files)

    io.event(f"> Files detected by git: {len(tracked_files)} (excluded: {excluded_files_count})")

    # Get model and provider information
    main_provider = get_inferred_provider()
    orchestrator_model = config.orchestrator_model if config.orchestrator_model else config.model
    orchestrator_provider = config.orchestrator_model_provider or main_provider
    weak_model = config.weak_model or config.model
    weak_provider = config.weak_model_provider or main_provider

    # Construct model information string
    model_info = f"main: [green]{config.model}[/green]"
    if orchestrator_model != config.model:
        model_info += f", orchestrator: [green]{orchestrator_model}[/green]"
    if weak_model != config.model:
        model_info += f", weak: [green]{weak_model}[/green]"

    # Add provider information
    provider_info = f"provider: [green]{main_provider}[/green]"
    if orchestrator_provider != main_provider:
        provider_info += f", orchestrator: {orchestrator_provider}"
    if weak_provider != main_provider:
        provider_info += f", weak: {weak_provider}"

    io.event(f"> Using models: {model_info} with {provider_info}")

    # Model validation
    error_msg = get_model_validation_message(main_provider)
    if error_msg:
        io.print(error_msg, style="bold red")

    if config.read_only:
        io.event("> Running on 'read-only' mode")

    if config.task_list:
        io.event("> Running in task list execution mode")

    # Warns token cost
    if not get_model_token_info(config.model):
        io.print(
            f"Token usage info not available for model `{config.model}`. Cost calculation can be unaccurate.",
            style="bold dark_goldenrod",
        )


# Run the workflow
def choose_chat_agent_node(agents: dict):
    """Allows the user to choose which agent to chat with or uses the default agent if specified."""
    if config.default_agent:
        if config.default_agent.isdigit():
            agent_index = int(config.default_agent)
            agent = list(agents)[agent_index - 1]
        else:
            agent = config.default_agent
        io.event(f"> Using default agent: [green]{agent}[/green]")
        return agent

    display_agent_list(agents)

    choice = Prompt.ask(
        "Select an agent", choices=[str(i) for i in range(1, len(agents) + 1)], default="1", console=io.console
    )

    chosen_agent = list(agents)[int(choice) - 1]
    io.event(f"> Starting chat with {chosen_agent} agent.")

    # Display suggestions for chosen agent
    agent = agents[chosen_agent]
    if hasattr(agent, "suggestions"):
        io.print("\n[dark_goldenrod]Example requests:[/dark_goldenrod]")
        for suggestion in agent.suggestions or []:
            io.print(f"   > {suggestion}")

    return chosen_agent


def display_agent_list(agents: dict):
    """Display the list of available agents with their indices."""
    io.print("\n[bold green]Available agents:[/bold green]")
    for i, (_agent_id, agent) in enumerate(agents.items(), 1):
        agent_type = "[cyan]Custom[/cyan]" if agent.is_custom else "[yellow]Predefined[/yellow]"
        io.print(f"{i}. {display_agent(agent, agent_type)}")


def explain_default_agent_usage():
    """Explain how to use the --default_agent option."""
    io.print(
        "\n[bold]How to use --default_agent:[/bold]"
        "\n1. Use the agent name: --default_agent=orchestrator"
        "\n2. Use the agent index: --default_agent=1"
        "\nExample: python -m pluscoder --default_agent=orchestrator"
    )


def validate_run_requirements():
    git_dir = Path(".git")
    if not git_dir.is_dir():
        io.event("> .git directory not found. Make sure you're in a Git repository.")
        sys.exit(1)
    if config.model is None:
        io.print("Model is empty. Configure a model to run Pluscoder.", style="bold red")
        io.print(
            "Use [green]--model <your-model>[/green], the [green].pluscoder-config.yml[/green] config file or env vars to configure"
        )
        sys.exit(1)


def main() -> None:
    """
    Main entry point for the Pluscoder application.
    """
    try:
        # Check for new command-line arguments
        if config.version:
            io.print(f"{__version__}")
            return

        from pluscoder.commands import show_config
        from pluscoder.commands import show_repo

        if config.show_repo:
            show_repo()
            return

        if config.show_config:
            show_config()
            return

        from pluscoder.setup import setup

        if not setup():
            return

        load_dotenv()
        load_dotenv(dotenv_path=get_global_env_filepath())

        validate_run_requirements()
        display_initial_messages()

        # Initialize search engine
        asyncio.run(initialize_search_engine())

        # Check if the default_agent is valid
        from pluscoder.type import TokenUsage
        from pluscoder.workflow import build_agents
        from pluscoder.workflow import build_workflow
        from pluscoder.workflow import run_workflow

        agent_dict = build_agents(provider=config.provider, model=config.model)
        if config.default_agent and (
            # Check if valid number
            config.default_agent.isdigit()
            and (int(config.default_agent) < 1 or int(config.default_agent) > len(agent_dict))
            # Check if valid name
            or not config.default_agent.isdigit()
            and config.default_agent not in agent_dict
        ):
            display_agent_list(agent_dict)
            io.print(f"Error: Invalid agent: {config.default_agent}", style="bold red")
            sys.exit(1)

        warnings = run_silent_checks()
        for warning in warnings:
            io.print(f"Warning: {warning}", style="bold dark_goldenrod")
            if not io.confirm("Proceed anyways?"):
                sys.exit(0)
    except Exception as err:
        if config.debug:
            io.print(traceback.format_exc(), style="bold red")
        io.event(f"An error occurred. {err}")
        return
    try:
        # Parse task list first
        task_list = parse_task_list()

        # In task list mode, force orchestrator agent like in setup.py
        if task_list:
            chat_agent = "orchestrator"
            io.event("> Using orchestrator agent for task list execution")
        else:
            chat_agent = choose_chat_agent_node(agent_dict)

        state = {
            "agents_configs": agent_dict,
            "chat_agent": agent_dict[chat_agent],
            "current_iterations": 0,
            "max_iterations": 100,
            "return_to_user": False,
            "messages": [],
            "context_files": [],
            "accumulated_token_usage": TokenUsage.default(),
            "token_usage": None,
            "current_agent_deflections": 0,
            "max_agent_deflections": 3,
            "is_task_list_workflow": bool(task_list),
            "status": "active",
        }

        # Add task list data if present
        if task_list:
            from pluscoder.tools import delegate_tasks
            from pluscoder.type import AgentInstructions

            tool_data = {}
            tool_data[delegate_tasks.name] = AgentInstructions(
                general_objective="Execute predefined task list",
                task_list=task_list,
                resources=[],
            ).dict()
            state["tool_data"] = tool_data

        app = build_workflow(agent_dict)
        asyncio.run(run_workflow(app, state))
    except KeyboardInterrupt:
        io.event("\nProgram interrupted. Exiting gracefully...")
        return
    except Exception as err:
        if config.debug:
            io.print(traceback.format_exc(), style="bold red")
        io.event(f"An error occurred. {err} during workflow run.")
        return


if __name__ == "__main__":
    main()
