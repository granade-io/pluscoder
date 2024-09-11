
# Global Configuration variables

- All pluscoder configuration, environment variables and command line argument, are loaded and stored in the singleton config at config.py
- Add any custom config to that singleton class

**Usage**:

    ```python
    from pluscoder.config import config
    config.my_custom_variable
    ```

# Printing and console display

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

# Docstrings
- Use multi-line docstrings for functions and classes.
- Include clear descriptions of function purposes, parameters, and return values.
- Example:
  ```python
  def function_name(param1: Type1, param2: Type2) -> ReturnType:
      """
      Brief description of the function.

      Args:
          param1 (Type1): Description of param1.
          param2 (Type2): Description of param2.

      Returns:
          ReturnType: Description of the return value.
      """
  ```

# Type Hinting
- Use type hints for function parameters and return values.
- For complex types, use the `typing` module.
- Example:
  ```python
  from typing import List, Dict

  def process_data(data: List[Dict[str, Any]]) -> None:
      # Function implementation
  ```

# Agents Capabilities
- LLM Agents perform almost any natural language task automatically
- They proactively can use tools; like read files, browse internet, update files, make summaries, analisys, coding, etc, all of that just giving him a naturale language text prompt. 
- In PlusCoder they care of many things; and there are tools agents can call where they decide which arguments to use when calling them.

## Agents Tools
- Implement tools as functions and register them with agents.
- Use the `@tool` decorator for defining tools.
- Example:
  ```python
  @tool
  def custom_tool(arg1: str, arg2: int) -> str:
      """Tool description"""
      # Tool implementation
  ```

# Code Organization
- Organize code into modules with clear responsibilities.
- Use meaningful file and directory names.
- Example directory structure:
  ```
  pluscoder/
  ├── agents/
  ├── config.py
  ├── io_utils.py
  ├── model.py
  ├── repo.py
  └── workflow.py
  ```

# Testing
- `tests/` folder constains tests and mirrors `pluscoder/` folder structure 
- Example:
  ```python
  def test_function():
      assert function_to_test() == expected_result
  ```

## Git Integration and repository related logic
- Use the custom `Repository` class to add repository related operations.
- Example:
  ```python
  from pluscoder.repo import Repository

  repo = Repository()
  ```

# Commenting
- Use inline comments sparingly, preferring self-documenting code.
- Use comments to explain complex logic or reasoning behind implementation choices.

# Naming Conventions
- Use snake_case for function and variable names.
- Use PascalCase for class names.
- Use UPPER_CASE for constants.

# File Operations
- Use the functions in `pluscoder/fs.py` for file reading and writing operations.
- Handle file operations with appropriate error checking.

Remember to follow these guidelines when contributing to the PlusCoder project. Consistency in coding style and practices helps maintain code quality and readability across the project.