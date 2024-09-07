import re
from pathlib import Path
from typing import List
from pluscoder.io_utils import io

BLOCK_FORMAT = """
>>> FIND
<old_content>
===
<new_content>
<<< REPLACE
"""
MSG_WRONG_FORMAT = f"""Invalid file update format when updating '%s' file. Please use the format: 
{BLOCK_FORMAT}
"""
MSG_FIND_NOT_FOUND = f"""Couldn't replace previous content at file `{{file_path}}`.

Remember to use the format:
{BLOCK_FORMAT}

Remember to read `{{file_path}}` file content before editing.
"""

def apply_block_update(file_path: str, block_content: str):
    """ Applies a block update to a file using the provided block content. Returns error message"""
    path = Path(file_path)
    
    # Check if the block content matches the specific format using regex
    block_pattern = re.compile(r'>>> FIND\n(.*?)\n?===\n(.*?)\n<<< REPLACE', re.DOTALL)
    matches = list(block_pattern.finditer(block_content))

    if matches:
        # debug log
        io.log_to_debug_file(f"Found blocks to update {file_path}")
        io.log_to_debug_file(f"Whole block: {block_content}")
        
        # Read the current file content
        if path.exists():
            current_content = path.read_text()
        else:
            current_content = ""

        # Process all block updates
        for match in matches:
            # debug log
            io.log_to_debug_file.print(f"Applying block to {file_path}")
            io.log_to_debug_file.print(f"Block: {block_content}")
            
            find_content = match.group(1).strip()
            replace_content = match.group(2).strip()
            
            if not current_content:
                # If writing to empty file, always write even if find_content is not found
                current_content = replace_content
                continue
                
            # Apply the replacement, make it fail raising an error if find_content is not found or trying to replace entire file
            if find_content not in current_content or (not find_content and current_content):
                return MSG_FIND_NOT_FOUND.format(file_path=file_path)
            
            current_content = current_content.replace(find_content, replace_content)

        new_content = current_content
    else:
        # Treat as a full content update
        new_content = block_content.strip()
        
        # Check if there is already content in the file to force block update
        if path.exists():
            current_content = path.read_text()
            if current_content:
                # If there are content, force block update format
                return MSG_FIND_NOT_FOUND.format(file_path=file_path)
    
    # Create the directory if it doesn't exist
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write the updated content back to the file
    path.write_text(new_content)
    io.console.print(f"`{file_path}` file updated. ", style="yellow")
    
    # False means no error
    return False

    
def get_formatted_file_content(file_path: str) -> str:
    """Return a formatted string with the content of a single file."""
    file_content = Path(file_path).read_text()
    formatted_content = f"\n<source>\n{file_content}\n</source> ---\n"
    return f"\n{file_path}:\n{formatted_content}\n"

def get_formatted_files_content(files: List[str]) -> str:
    """Return a formatted string with the content of each file ready to be used in llm prompts"""
    content = ""
    for file_path in files:
        content += get_formatted_file_content(file_path)
    return content.strip()