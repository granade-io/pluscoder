import re
import difflib
from rich.console import Console
from rich.syntax import Syntax


def display_diff(diff_text, filepath, console):
    # Display using rich syntax highlighting
    # console.print(Text(f"`{filepath}`", style="bold"))
    syntax = Syntax(diff_text, "diff", theme="monokai", line_numbers=True)
    console.print(syntax)

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

    # Define the regex pattern to match FIND/REPLACE blocks
    pattern = r'>>> FIND\n(.*?)\n===\n(.*?)\n<<< REPLACE'
    
    # Find all matches of FIND/REPLACE blocks
    matches = re.findall(pattern, content, re.DOTALL)
    
    if not matches:
        
        # Generate unified diff
        replace_lines = content.splitlines()
        diff = difflib.unified_diff("", replace_lines, fromfile=filepath, tofile=filepath, lineterm="")
        
        # Convert diff to a single string
        diff_text = "\n".join(diff)
        display_diff(diff_text, filepath, console)
        return

    # For each match, generate a diff and display
    for index, (find_block, replace_block) in enumerate(matches):
        find_lines = find_block.splitlines()
        replace_lines = replace_block.splitlines()
        
        # Generate unified diff
        diff = difflib.unified_diff(find_lines, replace_lines, fromfile=filepath, tofile=filepath, lineterm="")
        
        # Convert diff to a single string
        diff_text = "\n".join(diff)

        # Display using rich syntax highlighting
        display_diff(diff_text, filepath, console)




if __name__ == "__main__":
    # Example usage
    content = """
>>> FIND
This is the old text.
It needs to be replaced.
===
This is the new text.
It has been replaced.
<<< REPLACE
    """

    filepath = "example.txt"
    display_file_diff(content, filepath)