# Coding Guidelines

This document outlines the coding guidelines, standards, conventions, and reusable patterns identified in the PlusCoder project. Following these guidelines will help maintain consistency, improve code quality, and enhance reusability across the project.

## Coding Standards and Conventions

### Code Structure and File Organization

- Organize code into modules based on functionality (e.g., `config.py`, `workflow.py`, `main.py`).
- Use classes to encapsulate related functionality (e.g., `Config`, `Agent`).
- Keep files focused on a single responsibility or closely related set of responsibilities.

### Printing and console display

Always use the `io` object from `pluscoder.io_utils` for console interactions:

```python
from pluscoder.io_utils import io

# Normal output
io.console.print("Normal message")

# Error output
io.console.print("Error message", style="bold red")

# Event output
io.event("Event occurred")

# File logging
io.log_to_debug_file("Debug message")

# User input
user_input = io.input("Enter command: ")

# Confirmation
if io.confirm("Proceed?"):
    # Action
``` 


### Commenting and Documentation

- Use docstrings for classes, methods, and functions to describe their purpose, parameters, and return values.
- Example:
  ```python
  def get_context_files(self, state):
      """
      Get the list of context files for the current state.
      
      Args:
          state (dict): The current state dictionary.
      
      Returns:
          list: A list of file paths to be used as context.
      """
      # Function implementation
  ```
- Use inline comments to explain complex logic or non-obvious code.


### Type Hinting
- Use type hints for function parameters and return values.
- For complex types, use the `typing` module.
- Example:
  ```python
  from typing import List, Dict

  def process_data(data: List[Dict[str, Any]]) -> None:
      # Function implementation
  ```

### Agents Capabilities
- LLM Agents perform almost any natural language task automatically
- They proactively can use tools; like read files, browse internet, update files, make summaries, analisys, coding, etc, all of that just giving him a naturale language text prompt. 
- In PlusCoder they care of many things; and there are tools agents can call where they decide which arguments to use when calling them.

### Testing

- Write unit tests for critical functions and classes.
- Place test files in the `tests/` directory, mirroring the structure of the `pluscoder/` directory.
- Use meaningful test names that describe the behavior being tested.

## Reusable Patterns

### Global Configuration Management & Environment Variable and Argument Parsing

The project uses a centralized configuration management approach, implemented in `pluscoder/config.py`. This pattern allows for easy configuration updates and access throughout the project. Config singleton automatically parses and read all command-line argument and env vars.

**Usage example:**
```python
from pluscoder.config import config

if config.streaming:
    # Do something with streaming enabled
```

### Singleton Pattern for Configuration

The `Config` class in `pluscoder/config.py` uses the Singleton pattern to ensure only one instance of the configuration is created and used throughout the application.

**Singleton Implementation:**
```python
class Config:
    def __new__(cls):
        if not hasattr(cls, '_instance'):
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
```

### Tool Registration and Usage

The project uses a consistent pattern for registering and using tools across different agents.

**Files where used:**
- `pluscoder/tools.py`
- `pluscoder/agents/base.py`
- `pluscoder/agents/core.py`
- `pluscoder/agents/orchestrator.py`

**Usage example:**
```python
from langchain_core.tools import tool

@tool
def read_files(
    file_paths: Annotated[List[str], "The paths to the files you want to read."]
) -> str:
    """Read the contents of multiple files at once"""
    # Implementation
```

### Agent State Management

The project uses a consistent pattern for managing agent states, including token usage and message history.

**Files where used:**
- `pluscoder/type.py`
- `pluscoder/agents/base.py`
- `pluscoder/agents/orchestrator.py`

**Usage example:**
```python
class AgentState(TypedDict, total=False):
    token_usage: TokenUsage
    messages: Annotated[List[AnyMessage], add_messages]
    agent_messages: List[AnyMessage]
    tool_data: dict
    status: Literal["active", "delegating", "summarizing"]
```

### Event Emitter Pattern

The project uses an event emitter pattern for handling various events across the application.

**Files where used:**
- `pluscoder/agents/event/base.py`
- `pluscoder/agents/event/config.py`

**Usage example:**
```python
class EventEmitter:
    def __init__(self):
        self.handlers = {}

    async def emit(self, event, *args, **kwargs):
        if event in self.handlers:
            for handler in self.handlers[event]:
                await handler(*args, **kwargs)
```

By following these reusable patterns and guidelines, developers can maintain consistency and improve code quality across the PlusCoder project.
