#!/usr/bin/env python3
import asyncio
import sys
import traceback

from rich.prompt import Prompt

from pluscoder.commands import show_config
from pluscoder.commands import show_repo
from pluscoder.commands import show_repomap
from pluscoder.config import config
from pluscoder.display_utils import display_agent
from pluscoder.io_utils import io
from pluscoder.model import get_inferred_provider
from pluscoder.model import get_model_validation_message
from pluscoder.repo import Repository
from pluscoder.setup import setup
from pluscoder.type import TokenUsage
from pluscoder.workflow import build_agents
from pluscoder.workflow import build_workflow
from pluscoder.workflow import run_workflow


def banner() -> None:
    """Display the Pluscoder banner."""
    io.console.print(
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

{'or type ´help´ to get started'.center(80)}

-------------------------------------------------------------------------------
[/bold green]

"""
    )


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


def display_initial_messages():
    """Display initial message with the number of files detected by git, excluded files, and model information."""
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
        io.console.print(error_msg, style="bold red")

    if config.read_only:
        io.event("> Running on 'read-only' mode")


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
        "Select an agent",
        choices=[str(i) for i in range(1, len(agents) + 1)],
        default="1",
    )

    chosen_agent = list(agents)[int(choice) - 1]
    io.event(f"> Starting chat with {chosen_agent} agent.")
    return chosen_agent


def display_agent_list(agents: dict):
    """Display the list of available agents with their indices."""
    io.console.print("\n[bold green]Available agents:[/bold green]")
    for i, (_agent_id, agent) in enumerate(agents.items(), 1):
        agent_type = "[cyan]Custom[/cyan]" if agent.is_custom else "[yellow]Predefined[/yellow]"
        io.console.print(f"{i}. {display_agent(agent, agent_type)}")


def explain_default_agent_usage():
    """Explain how to use the --default_agent option."""
    io.console.print(
        "\n[bold]How to use --default_agent:[/bold]"
        "\n1. Use the agent name: --default_agent=orchestrator"
        "\n2. Use the agent index: --default_agent=1"
        "\nExample: python -m pluscoder --default_agent=orchestrator"
    )


def main() -> None:
    """
    Main entry point for the Pluscoder application.
    """
    try:
        # Check for new command-line arguments
        if config.show_repo:
            show_repo()
            return

        if config.show_repomap:
            show_repomap()
            return

        if config.show_config:
            show_config()
            return

        if not setup():
            return

        display_initial_messages()

        # Check if the default_agent is valid
        agent_dict = build_agents()
        if config.default_agent and (
            # Check if valid number
            config.default_agent.isdigit()
            and (int(config.default_agent) < 1 or int(config.default_agent) > len(agent_dict))
            # Check if valid name
            or not config.default_agent.isdigit()
            and config.default_agent not in agent_dict
        ):
            display_agent_list(agent_dict)
            io.console.print(f"Error: Invalid agent: {config.default_agent}", style="bold red")
            sys.exit(1)

        warnings = run_silent_checks()
        for warning in warnings:
            io.console.print(f"Warning: {warning}", style="bold dark_goldenrod")
            if not io.confirm("Proceed anyways?"):
                sys.exit(0)
    except Exception as err:
        if config.debug:
            io.console.print(traceback.format_exc(), style="bold red")
        io.event(f"An error occurred. {err}")
        return
    try:
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
            "is_task_list_workflow": False,
            "status": "active",
        }

        app = build_workflow(agent_dict)
        asyncio.run(run_workflow(app, state))
    except Exception as err:
        if config.debug:
            io.console.print(traceback.format_exc(), style="bold red")
        io.event(f"An error occurred. {err} during workflow run.")
        return
    except KeyboardInterrupt:
        io.event("\nProgram interrupted. Exiting gracefully...")
        return


if __name__ == "__main__":
    main()
