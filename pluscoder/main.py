#!/usr/bin/env python3
import asyncio
from pluscoder.setup import setup
from pluscoder.type import AgentState, TokenUsage
from pluscoder.workflow import run_workflow
from pluscoder.io_utils import io
from pluscoder.config import config
from pluscoder.commands import show_repo, show_repomap, show_config

# Run the workflow

def choose_chat_agent_node():
    """Allows the user to choose which agent to chat with."""
    io.console.print("[bold green]Choose an agent to chat with:[/bold green]")
    io.console.print("1. Orchestrator: Break down the problem into a list of tasks and delegates it to others agents.")
    io.console.print("2. Domain Stakeholder: For discussing project details, maintaining the project overview, roadmap, and brainstorming.")
    io.console.print("3. Planning: For creating detailed, actionable plans for software development tasks.")
    io.console.print("4. Developer: For implementing code to solve complex software development requirements.")
    io.console.print("5. Domain Expert: For validating tasks and ensuring alignment with project vision.")
    io.console.print()
    choice = io.input("Enter your choice (1-5): ")
    
    if choice not in ["1", "2", "3", "4", "5"]:
        raise ValueError("Invalid choice. Please enter a number between 1 and 5.")
    
    # Map user input to agent IDs
    agent_map = {
        "1": "orchestrator",
        "2": "domain_stakeholder",
        "3": "planning",
        "4": "developer",
        "5": "domain_expert"
    }
    
    chosen_agent = agent_map.get(choice, "orchestrator")
    io.event(f"> Starting chat with {chosen_agent} agent.")
    return chosen_agent

def main():
    """
    Main entry point for the Pluscoder application.
    """
    if not setup():
        return
    
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

if __name__ == "__main__":
    main()
