
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


