#!/usr/bin/env python3
import asyncio
from pluscoder.model import get_inferred_provider
from pluscoder.setup import setup
from pluscoder.type import AgentState, TokenUsage
from pluscoder.workflow import run_workflow
from pluscoder.io_utils import io
from pluscoder.config import config
from pluscoder.commands import show_repo, show_repomap, show_config
from pluscoder.repo import Repository
from rich.prompt import Prompt

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
    repo = Repository(io)
    
    # Get all tracked files (including those in the index) and untracked files
    all_files = set(repo.repo.git.ls_files().splitlines() +
                    repo.repo.git.ls_files(others=True, exclude_standard=True).splitlines())
    
    # Get tracked files after applying exclusion patterns
    tracked_files = repo.get_tracked_files()
    
    # Calculate the number of excluded files
    excluded_files_count = len(all_files) - len(tracked_files)
    
    io.event(f"> Files detected by git: {len(tracked_files)} (excluded: {excluded_files_count})")
    
    # Get model and provider information
    main_provider = get_inferred_provider()
    orchestrator_model = config.orchestrator_model if config.orchestrator_model else config.model
    orchestrator_provider = config.orchestrator_model_provider or main_provider
    weak_model = config.weak_model if config.weak_model else config.model
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
    
    if config.read_only:
        io.event("> Running on 'read-only' mode")
    
    io.console.print("Look at https://gitlab.com/codematos/pluscoder/-/blob/main/README.md for more documentation.")

# Run the workflow

def choose_chat_agent_node():
    """Allows the user to choose which agent to chat with."""
    
    agent_options = [
        "Orchestrator: Break down the problem into a list of tasks and delegates it to other agents",
        "Domain Stakeholder: Discuss project details, maintain project overview, roadmap, and brainstorm",
        "Planning: Create detailed, actionable plans for software development tasks",
        "Developer: Implement code to solve complex software development requirements",
        "Domain Expert: Validate tasks and ensure alignment with project vision"
    ]
    io.console.print("[bold green]Choose an agent to chat with:[/bold green]")
    io.console.print("1. [bold green]Orchestrator[/bold green]: Break down the problem into a list of tasks and delegates it to others agents.")
    io.console.print("2. [bold green]Domain Stakeholder[/bold green]: For discussing project details, maintaining the project overview, roadmap, and brainstorming.")
    io.console.print("3. [bold green]Planning[/bold green]: For creating detailed, actionable plans for software development tasks.")
    io.console.print("4. [bold green]Developer[/bold green]: For implementing code to solve complex software development requirements.")
    io.console.print("5. [bold green]Domain Expert[/bold green]: For validating tasks and ensuring alignment with project vision.")
    
    choice = Prompt.ask(
        "Select an agent",
        choices=[str(i) for i in range(1, len(agent_options) + 1)],
        default="1"
    )
    
    # Map user input to agent IDs
    agent_map = {
        "1": "orchestrator",
        "2": "domain_stakeholder",
        "3": "planning",
        "4": "developer",
        "5": "domain_expert"
    }
    
    chosen_agent = agent_map[choice]
    io.event(f"> Starting chat with {chosen_agent} agent.")
    return chosen_agent

def main():
    """
    Main entry point for the Pluscoder application.
    """
    try:
        if not setup():
            return
        
        warnings = run_silent_checks()
        for warning in warnings:
            io.console.print(f"Warning: {warning}", style="bold dark_goldenrod")
        
        display_initial_messages()
        
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
        
        state = {
            "return_to_user": False,
            "messages": [], 
            "context_files": [],
            "orchestrator_state": AgentState.default(),
            "domain_stakeholder_state": AgentState.default(),
            "planning_state": AgentState.default(),
            "developer_state": AgentState.default(),
            "domain_expert_state": AgentState.default(),
            "accumulated_token_usage": TokenUsage.default(),
            "current_agent_deflections": 0,
            "max_agent_deflections": 3,
            "chat_agent": choose_chat_agent_node(),
            "is_task_list_workflow": False
            }
        
        asyncio.run(run_workflow(state))
    except KeyboardInterrupt:
        io.event("\nProgram interrupted. Exiting gracefully...")
        return

if __name__ == "__main__":
    main()
