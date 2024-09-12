from typing import Dict, Union, Callable
from functools import wraps
from rich.syntax import Syntax
from pluscoder.config import config
from pluscoder.repo import Repository
from pluscoder.io_utils import io
from pluscoder.type import AgentState, OrchestrationState
from rich.rule import Rule                                                                                                      
from rich.table import Table
import subprocess

class CommandRegistry:
    def __init__(self):
        self.commands: Dict[str, Callable] = {}

    def register(self, name: str):
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            self.commands[name] = wrapper
            return wrapper
        return decorator

    def get(self, name: str) -> Union[Callable, None]:
        return self.commands.get(name)

command_registry = CommandRegistry()

def _clear(state: OrchestrationState):
    """Clear entire chat history"""
    # Filters values from dict where key ends with "_state"                                                                       
    for key, value in state.items():                                                                                              
        if key.endswith("_state"):                                                                                                
            # Reset AgentState to default values                                                                                  
            state[key] = AgentState.default()
    return state

@command_registry.register("clear")
def clear(state: OrchestrationState):
    """Reset entire chat history"""                                                                                               
                                                                                                                                  
    cleared_state = _clear(state)                                                                                             
    io.event("Chat history cleared.")                                                                                             
    io.event(Rule())                                                                                                              
    return cleared_state 

@command_registry.register("diff")
def diff(state: OrchestrationState):
    """Show last commit diff""" 
    repo = Repository(io=io)
    diff = repo.diff()
    if diff:
        syntax = Syntax(diff, "diff", theme="monokai", line_numbers=True)
        io.console.print(syntax)
    else:
        io.console.print("No changes in the last commit.")
    return state

@command_registry.register("config")
def config_command(state: OrchestrationState, key: str, value: str):
    """Override any pluscoder configuration. e.g: `/config auto-commits false`"""
    if key not in config.__dict__:
        io.console.print(f"Error: '{key}' is not a valid configuration option.", style="bold red")
        return state
    old_value = getattr(config, key)
    new_value = config.update_config(key, value)
    io.console.print(f"Config updated: {key} = {new_value} (was: {old_value})")
    return state

@command_registry.register("undo")
def undo(state: OrchestrationState):
    """Revert last commit and remove last message from chat history"""
    repo = Repository(io=io)
    if repo.undo():
        # Filters values from dict where key ends with "_state"                                                                   
        for key, value in state.items():                                                                                          
            if not key.endswith("_state") or len(state[key]["messages"]) < 1:                                                     
                # Skip non-message-containing keys                                                                                
                continue                                                                                                          
                                                                                                                                  
            # Remove last message from chat history                                                                               
            state[key]["messages"] = state[key]["messages"][:-1]                                                                  
        io.event("Last commit reverted and last message removed from chat history.")                                              
        return state  
    else:
        io.console.print("Failed to revert last commit.", style="bold red")                                                       
        return state  

@command_registry.register("agent")
def agent(state: OrchestrationState):
    """Start a conversation with a new agent from scratch"""
    agents = ["orchestrator", "domain_stakeholder", "planning", "developer", "domain_expert"]
    io.console.print("Available agents:")
    for i, agent in enumerate(agents, 1):
        io.console.print(f"{i}. {agent}")
    
    choice = io.input("Enter the number of the agent you want to switch to: ")
    try:
        index = int(choice) - 1
        if 0 <= index < len(agents):
            state["chat_agent"] = agents[index]
            io.event(f"Switched to `{agents[index]}` agent. Chat history was cleared.")
        else:
            io.console.print("Invalid choice. Please enter a number between 1 and 5.", style="bold red")
    except ValueError:
        io.console.print("Invalid input. Please enter a number.", style="bold red")
        
    # Clear chats to start new conversations
    cleared_state = _clear(state)  
    return cleared_state

@command_registry.register("help")                                                                                                
def help_command(state: OrchestrationState):                                                                                      
    """Display help information for available commands"""                                                                         
    table = Table(title="Available Commands")                                                                                     
    table.add_column("Command", style="cyan")                                                                                     
    table.add_column("Description", style="green")                                                                                
                                                                                                                                  
    for cmd_name, cmd_func in command_registry.commands.items():                                                                  
        table.add_row(f"/{cmd_name}", cmd_func.__doc__ or "No description available")                                             
                                                                                                                                  
    io.console.print(table)                                                                                                       
    return state  

@command_registry.register("run")
def run_command(state: OrchestrationState, *args) -> OrchestrationState:
    """Execute a system command and capture its output"""
    command = " ".join(args)
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        output = result.stdout
        io.console.print(f"Command executed successfully:\n{output}")
        state["command_output"] = output
    except subprocess.CalledProcessError as e:
        error_message = f"Command execution failed:\nError: {e}\nOutput: {e.output}\nError output: {e.stderr}"
        io.console.print(error_message, style="bold red")
        state["command_output"] = error_message
    except Exception as e:
        error_message = f"An unexpected error occurred: {str(e)}"
        io.console.print(error_message, style="bold red")
        state["command_output"] = error_message
    
    return state

@command_registry.register("init")
def _init(state: OrchestrationState):
    """Force repository initialization"""
    io.console.print("It takes about 1-2 minutes to analyze the repository for better understanding.")
    if io.confirm("Do you want to initialize it now? (recommended)"):
        from pluscoder.setup import initialize_repository
        initialize_repository()
    else:
        io.console.print("Repository initialization cancelled.")
    return state

def is_command(command: Union[str, dict]) -> bool:
    if isinstance(command, str):
        return command.strip().startswith('/')
    elif isinstance(command, dict) and "type" in command and command["type"] == "command":
        return True
    return False

def parse_command(command: str) -> Union[str, dict, None]:
    # Parse input for commands
    command_parts = command.strip().strip("/").split()
    args = command_parts[1:]
    return {
        'type': 'command',
        'command': command_parts[0],
        'args': args
    }

def handle_command(command: str, state: OrchestrationState=None) -> bool:
    """Handle command execution and return True if a command was executed, False otherwise."""
    
    parsed_command = parse_command(command)
    
    if parsed_command['type'] == 'command':
        cmd_func = command_registry.get(parsed_command['command'])
        if cmd_func:
            updated_sate = cmd_func({
                **state,
                # All commands return to the user by default, can be overridden by each command
                "return_to_user": True,
                }, *parsed_command['args'])
            return updated_sate
    
    return state