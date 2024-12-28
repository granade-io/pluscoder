import difflib
import re

from rich.console import Console
from rich.syntax import Syntax


def display_diff(diff_text, filepath, io):
    # Display using rich syntax highlighting
    # print(Text(f"`{filepath}`", style="bold"))
    syntax = Syntax(diff_text, "diff", theme="monokai", line_numbers=False)
    io.print(syntax)


def display_file_diff(content: str, filepath: str, console=None) -> None:
    """
    Find FIND/REPLACE blocks in the given content and display a git-like diff
    using rich Syntax for each found block.

    Args:
        content (str): The content containing FIND/REPLACE blocks.
        filepath (str): The filepath associated with the content.
    """
    # Initialize console for rich output
    console = console if console else Console()

    if not filepath:
        filepath = "a"

    # Define the regex pattern to match FIND/REPLACE blocks
    pattern = r">>> FIND\n(.*?)\n===\n(.*?)\n<<< REPLACE"

    # Find all matches of FIND/REPLACE blocks
    matches = re.findall(pattern, content, re.DOTALL)

    if not matches:
        # Generate unified diff
        replace_lines = content.splitlines()
        diff = difflib.unified_diff("", replace_lines, fromfile=filepath, tofile=filepath, lineterm="")

        # Convert diff to a single string
        diff_text = "\n".join(diff)
        display_diff(diff_text, filepath, console)
        return True

    # For each match, generate a diff and display
    for _index, (find_block, replace_block) in enumerate(matches):
        find_lines = find_block.splitlines()
        replace_lines = replace_block.splitlines()

        # Generate unified diff
        diff = difflib.unified_diff(find_lines, replace_lines, fromfile=filepath, tofile=filepath, lineterm="")

        # Convert diff to a single string
        diff_text = "\n".join(diff)

        # Display using rich syntax highlighting
        display_diff(diff_text, filepath, console)
    return True


def get_cost_usage_display(token_usage):
    if not token_usage:
        text_content = "Tokens: ↑:0 ↓:0 T:0 $0"
    else:
        text_content = f"Tokens: ↑:{token_usage['prompt_tokens']} ↓:{token_usage['completion_tokens']} T:{token_usage['total_tokens']} ${token_usage['total_cost']:.3f}"
    return text_content


def render_task(task):
    """Render a single task with status indicator."""
    status = "✓" if task.is_finished else "⋯"
    return f"{status} {task.objective}"


def display_agent(agent, agent_type: str):
    description = agent.description if hasattr(agent, "description") else "No description available"
    return f"[bold green]{agent.name}[/bold green] ({agent_type}): {description}"


if __name__ == "__main__":
    # Example usage
    content = """
>>> FIND
This is the new text.
It has been replaced.
===
This is the new text.
It has been replaced.
<<< REPLACE
    """

    filepath = "example.txt"
    display_file_diff(content, filepath)
