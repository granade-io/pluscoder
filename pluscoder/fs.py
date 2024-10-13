import re
from pathlib import Path
from typing import List

from pluscoder.io_utils import io

BLOCK_FORMAT = """
`<relative_file_path>`
<source>
>>> FIND
1st line of context
2nd line of context
(lines of content to be replaced)
3nd line of context
4th line of context
===
1st line of context
2nd line of context
(lines of new content to put in file)
3nd line of context
4th line of context
<<< REPLACE
</source>
"""
MSG_WRONG_FORMAT = f"""Invalid file update format when updating '%s' file. Please use the format:
{BLOCK_FORMAT}
"""
MSG_FIND_NOT_FOUND = f"""Couldn't replace some changes at file `{{file_path}}`.

Remember to use the format:
{BLOCK_FORMAT}

Read the `{{file_path}}` file again, identify content that was not replaced properly and add them performing exact content match for replacements using the format above.
"""


def apply_block_update(file_path: str, block_content: str):
    """Applies a block update to a file using the provided block content. Returns error message"""
    path = Path(file_path)

    # Check if the block content matches the specific format using regex
    block_pattern = re.compile(
        r">>> FIND\n(.*?\n|\n{0})===\n(.*?)\n<<< REPLACE", re.DOTALL
    )
    matches = list(block_pattern.finditer(block_content))
    original_content = ""

    if matches:
        # debug log
        io.log_to_debug_file(f"FOUND BLOCK FOR {file_path}\n")
        io.log_to_debug_file(
            f"{"<-- START OF WHOLE BLOCK -->"}\n{block_content}\n{"<-- END OF WHOLE BLOCK -->"}\n\n"
        )

        # Read the current file content
        if path.exists():
            current_content = path.read_text()
            original_content = current_content
        else:
            current_content = ""

        # Process all block updates
        for match in matches:
            # debug log
            io.log_to_debug_file(f"APPLYING BLOCK CHUNK TO {file_path}\n")
            io.log_to_debug_file(
                f"{"<-- START OF BLOCK CHUNK -->"}{block_content}\n{"<-- END OF BLOCK CHUNK -->"}\n\n"
            )

            find_content = match.group(1).strip()
            replace_content = match.group(2).strip()

            if not current_content:
                # If writing to empty file, always write even if find_content is not found
                current_content = replace_content
                continue

            # Apply the replacement, make it fail raising an error if find_content is not found or trying to replace entire file
            if find_content not in current_content or (
                not find_content and current_content
            ):
                return MSG_FIND_NOT_FOUND.format(file_path=file_path)

            current_content = current_content.replace(find_content, replace_content)

        new_content = current_content
    else:
        # debug log
        io.log_to_debug_file(f"FOUND FULL FILE BLOCK FOR {file_path}\n")
        io.log_to_debug_file(
            f"{"<-- START OF FULL FILE WHOLE BLOCK -->"}\n{block_content}\n{"<-- END OF FULL FILE WHOLE BLOCK -->"}\n\n"
        )

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

    if new_content != original_content:
        # Write the updated content back to the file
        path.write_text(new_content)
        io.console.print(f"`{file_path}` file updated. ", style="green")

    # False means no error
    return False


def get_formatted_file_content(file_path: str) -> str:
    """Return a formatted string with the content of a single file."""
    file_content = Path(file_path).read_text()
    formatted_content = f"{file_content}"
    return f"\n--- start of `{file_path}`---\n{formatted_content}\n"


def get_formatted_files_content(files: List[str]) -> str:
    """Return a formatted string with the content of each file ready to be used in llm prompts"""
    content = ""
    for file_path in files:
        content += get_formatted_file_content(file_path)
    return content.strip()
