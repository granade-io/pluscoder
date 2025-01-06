import subprocess
import traceback
from functools import wraps
from typing import Callable
from typing import Dict
from typing import Union

from pydantic import ValidationError
from rich.panel import Panel
from rich.prompt import Prompt
from rich.rule import Rule
from rich.syntax import Syntax
from rich.table import Table
from rich.tree import Tree

from pluscoder import tools
from pluscoder.config import config
from pluscoder.config.utils import append_custom_agent_to_config
from pluscoder.config.utils import get_config_paths
from pluscoder.display_utils import display_agent
from pluscoder.io_utils import io
from pluscoder.message_utils import HumanMessage
from pluscoder.message_utils import delete_messages
from pluscoder.message_utils import filter_messages
from pluscoder.message_utils import tag_messages
from pluscoder.repo import Repository
from pluscoder.type import AgentConfig
from pluscoder.type import OrchestrationState


class CommandRegistry:
    def __init__(self):
        self.commands: Dict[str, Callable] = {}

    def register(self, name: str):
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            self.commands[name] = wrapper
            io.register_command(name, func.__doc__)
            return wrapper

        return decorator

    def get(self, name: str) -> Union[Callable, None]:
        return self.commands.get(name)


command_registry = CommandRegistry()


def _clear(state: OrchestrationState):
    """Clear entire chat history"""
    return {**state, "messages": delete_messages(state["messages"], include_tags=[state["chat_agent"].id])}


@command_registry.register("clear")
def clear(state: OrchestrationState):
    """Clear the entire chat history"""

    cleared_state = _clear(state)
    io.event(Rule("Chat history cleared."))
    return cleared_state


@command_registry.register("diff")
def diff(state: OrchestrationState):
    """Show last commit diff"""
    repo = Repository(io=io)
    diff = repo.diff()
    if diff:
        syntax = Syntax(diff, "diff", theme="monokai", line_numbers=True)
        io.print(syntax)
    else:
        io.print("No changes in the last commit.")
    return state


@command_registry.register("config")
def config_command(state: OrchestrationState, key: str, value: str, *args):
    """Override any pluscoder configuration. e.g: `/config auto_commits false`"""
    if key not in config.__dict__:
        io.print(f"Error: '{key}' is not a valid configuration option.", style="bold red")
        return state
    old_value = getattr(config, key)
    try:
        config.__init__(**{key: value})
        io.print(f"Config updated: {key} = {getattr(config, key)} (was: {old_value})")
    except ValidationError:
        io.print("Invalid value.", style="bold red")

    return state


@command_registry.register("undo")
def undo(state: OrchestrationState):
    """Revert last commit and remove message from history until last user message is removed"""
    repo = Repository(io=io)
    if repo.undo():
        messages = state.get("messages", [])
        # Find last HumanMessage
        last_human_idx = next(
            (i for i in range(len(messages) - 1, -1, -1) if isinstance(messages[i], HumanMessage)), -1
        )

        if last_human_idx == -1:
            io.event("> Last commit reverted. No chat messages to remove.")
            return state

        # Get all message IDs from last human message to end
        message_ids = [msg.id for msg in messages[last_human_idx:]]

        io.event("> Last commit reverted and messages removed from chat history.")
        return {**state, "messages": delete_messages(state["messages"], include_ids=message_ids)}
    io.print("Failed to revert last commit.", style="bold red")
    return state


@command_registry.register("agent")
def select_agent(state: OrchestrationState, *args):
    """Start a new conversation with another agent"""
    from pluscoder.workflow import build_agents

    agent_dict = build_agents(provider=config.provider, model=config.model)
    chosen_agent = " ".join(args).strip()

    if chosen_agent not in agent_dict:
        # chose an agent interactively
        io.print("[bold green]Choose an agent to chat with:[/bold green]")

        for i, (_agent_id, agent) in enumerate(agent_dict.items(), 1):
            agent_type = "[cyan]Custom[/cyan]" if agent.is_custom else "[yellow]Predefined[/yellow]"
            io.print(f"{i}. {display_agent(agent, agent_type)}")

        choice = Prompt.ask(
            "Select an agent",
            choices=[str(i) for i in range(1, len(agent_dict) + 1)],
            default="1",
            console=io.console,
        )

        chosen_agent = list(agent_dict.keys())[int(choice) - 1]

    preserve_chat = io.confirm("Preserve that story with new agent?")

    if not preserve_chat:
        io.event(f"> Starting chat with {chosen_agent} agent. Chat history was cleared.")
        return {**_clear(state), "chat_agent": agent_dict[chosen_agent]}

    # Preserve history by adding new agent tag
    current_messages = filter_messages(state["messages"], include_tags=[state["chat_agent"].id])
    tagged_messages = tag_messages(current_messages, tags=[agent_dict[chosen_agent].id])

    io.event(f"> Starting chat with {chosen_agent} agent. Chat history preserved.")
    return {**state, "messages": tagged_messages, "chat_agent": agent_dict[chosen_agent]}


@command_registry.register("help")
def help_command(state: OrchestrationState):
    """Display help information for available commands"""
    table = Table(title="Available Commands")
    table.add_column("Command", style="cyan")
    table.add_column("Description", style="green")

    for cmd_name, cmd_func in command_registry.commands.items():
        table.add_row(f"/{cmd_name}", cmd_func.__doc__ or "No description available")

    io.print(table)
    return state


@command_registry.register("run")
def run_command(state: OrchestrationState, *args) -> OrchestrationState:
    """Execute a system command and displays its output"""
    command = " ".join(args)
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True,
        )
        output = result.stdout
        io.print(f"Command executed successfully:\n{output}")
        state["command_output"] = output
    except subprocess.CalledProcessError as e:
        error_message = f"Command execution failed:\nError: {e}\nOutput: {e.output}\nError output: {e.stderr}"
        io.print(error_message, style="bold red")
        state["command_output"] = error_message
    except Exception as e:
        error_message = f"An unexpected error occurred: {e!s}"
        io.print(error_message, style="bold red")
        state["command_output"] = error_message

    return state


@command_registry.register("show_repo")
def show_repo(state: OrchestrationState = None):
    """Display repository files tree in the context"""
    repo = Repository(io=io)
    tracked_files = repo.get_tracked_files()

    tree = Tree("Repository Structure")
    for file in tracked_files:
        tree.add(file)

    io.print(Panel(tree, title="Repository Files", expand=False))
    return state


@command_registry.register("show_repomap")
def show_repomap(state: OrchestrationState = None):
    """Display the repository map"""
    repo = Repository(io=io)
    repomap = repo.generate_repomap()

    if repomap:
        io.print(Panel(repomap, title="Repository Map", expand=False))
    else:
        io.print("Repomap is not enabled or could not be generated.")
    return state


@command_registry.register("show_config")
def show_config(state: OrchestrationState = None):
    """Display Pluscoder configuration and config file locations"""

    # Show current values
    io.print("")
    table = Table(title="Current Configuration Values")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="magenta")

    for key, value in vars(config).items():
        if key.startswith("_"):  # Skip private attributes
            continue
        table.add_row(key, str(value))

    io.print(table)

    # Show config locations
    paths = get_config_paths()
    locations = Table(title="Configuration File Locations")
    locations.add_column("Scope", style="cyan")
    locations.add_column("Path", style="green")
    locations.add_row("Local (Repository)", paths.local)
    locations.add_row("User Global", paths.global_config)
    locations.add_row("User Global Env vars", paths.global_env)
    io.print(locations)
    return state


@command_registry.register("agent_create")
def create_agent(state: OrchestrationState, *args):
    """Creates a persistent specialized Agent to chat with."""
    from pluscoder.agents.utils import generate_agent

    io.event("> Started new agent creation")

    io.print(Rule("Agent Personalization"))
    # Repository interaction
    io.print(
        "WARN: Disabling code-base interaction will cause the agent to know nothing about the repository or its files",
        style="bold dark_goldenrod",
    )
    repository_interaction = bool(io.confirm("Enable code-base interaction for this agent?"))

    # Read only config
    read_only = not (repository_interaction and io.confirm("Allow this agent to edit files?"))

    io.print("Describe the problem you want to solve or an agent to create")
    io.print("Example: 'I need a ReactJs frontend with MaterialUI and Swagger APIs connections'")
    io.print("Example: 'An Agent to refactor my Python code with Design Patterns'")
    description = io.input("Describe your problem or agent:\n")

    try:
        new_agent = generate_agent(description, repository_interaction)
        io.print(Rule("Generated Agent"))
        io.print(f"[bold green]{new_agent['name']}[/bold green]: {new_agent['description']}\n")
        io.print(new_agent["prompt"], style="bold green")
        io.print(Rule())
        if not io.confirm("Do you to proceed with this agent?"):
            io.event("\n> Agent was discarded. Run /agent_create again with better indications")
            return {}

        # Extends agent with personalization values
        new_agent["read_only"] = read_only
        new_agent["repository_interaction"] = repository_interaction
        new_agent["default_context_files"] = []

        # Naming
        name = Prompt.ask(
            "Name your agent (use it as [yellow]--default_agent <name>[/yellow])", default=new_agent["name"]
        )

        if name != new_agent["name"]:
            new_agent["name"] = name.lower().replace(" ", "")

        # Adds agent to config
        io.event(f"> Agent '{new_agent['name']}' saved to .pluscoder-config.yml")
        append_custom_agent_to_config(new_agent)

        # Reloads config to apply changes
        config.__init__(**{})

        # New agent config
        new_agent_id = new_agent["name"].lower().replace(" ", "")
        new_agent_config = AgentConfig(
            is_custom=True,
            id=new_agent_id,
            name=new_agent["name"],
            description=new_agent["description"],
            prompt=new_agent["prompt"],
            reminder=new_agent.get("reminder", ""),
            tools=[tool.name for tool in tools.base_tools],
            default_context_files=[],
            read_only=new_agent["read_only"],
            repository_interaction=new_agent["repository_interaction"],
            provider=config.provider,
            model=config.model,
        )

        return select_agent(
            {**state, "agents_configs": {**state["agents_configs"], new_agent_id: new_agent_config}}, new_agent["name"]
        )
    except Exception:
        if config.debug:
            io.print(traceback.format_exc(), style="bold red")
        io.print("Error generating agent: Please run command again", style="bold red")

    return state


@command_registry.register("custom")
def custom_command(state: OrchestrationState, prompt_name: str = "", *args):
    """Execute a custom prompt command"""
    if not prompt_name:
        io.print("Error: Custom prompt name is required.", style="bold red")
        io.print("Usage: /custom <prompt_name> <additional instructions>")
        return state

    custom_prompt = next(
        (prompt for prompt in config.custom_prompt_commands if prompt["prompt_name"] == prompt_name),
        None,
    )
    if not custom_prompt:
        io.print(f"Error: Custom prompt '{prompt_name}' not found.", style="bold red")
        return state

    user_input = " ".join(args)
    combined_prompt = f"{user_input} {custom_prompt['prompt']}"

    current_agent = state["chat_agent"]

    io.print(f"Custom prompt '{prompt_name}' executed and added to {current_agent.name}'s message history.")
    return {
        # Add the combined prompt as a HumanMessage to the current agent's message history
        "messages": [HumanMessage(content=combined_prompt, tags=[state["chat_agent"].id])],
        # Do not return to the user to execute agent with the added human message
        "return_to_user": False,
    }


def is_command(command: Union[str, dict]) -> bool:
    if isinstance(command, str):
        return command.strip().startswith("/")
    return bool(isinstance(command, dict) and "type" in command and command["type"] == "command")


def parse_command(command: str) -> Union[str, dict, None]:
    # Parse input for commands
    command_parts = command.strip().strip("/").split()
    args = command_parts[1:]
    return {"type": "command", "command": command_parts[0], "args": args}


def handle_command(command: str, state: OrchestrationState = None) -> bool:
    """Handle command execution and return True if a command was executed, False otherwise."""

    parsed_command = parse_command(command)

    if parsed_command["type"] == "command":
        cmd_func = command_registry.get(parsed_command["command"])
        if cmd_func:
            # updated state
            return cmd_func(
                {
                    **state,
                    # All commands return to the user by default, can be overridden by each command
                    "return_to_user": True,
                },
                *parsed_command["args"],
            )

    return state
