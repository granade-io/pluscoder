from pathlib import Path
from typing import List

BLOCK_FORMAT = """
    <pc_action action="file_diff" file="app/router.js">
    <original>... lines of context ...\n content to replace \n... lines of context ...</original>
    <new>... lines of context ...\n new content \n... lines of context ..</new>
    </pc_action>
"""
MSG_WRONG_FORMAT = f"""Invalid file update format when updating '%s' file. Please use the format:
{BLOCK_FORMAT}
"""
MSG_FIND_NOT_FOUND = f"""{{content}}

The previous content was not found in the file `{{file_path}}` to be replaced. Please try again this file operation.


Remember, when using action tags you must exactly match content to replace, line by line, character by character:
{BLOCK_FORMAT}

Read the `{{file_path}}` file again, identify content that was not replaced properly and them perform exact content match for replacements.
"""

MSG_WHOLE_FILE_REPLACEMENT = f"""Couldn't replace some changes at file `{{file_path}}`. You are trying to replace the entire file but it already have a content.

Remember, when using action tags you must exactly match content to replace, line by line, character by character:
{BLOCK_FORMAT}

Read the `{{file_path}}` file again, identify content that was not replaced properly and the perform exact content match for replacements.
"""


def apply_diff_edition(file_path, find_content, replace_content, current_content=None):
    path = Path(file_path)

    # Read the current file content
    current_content = path.read_text() if path.exists() else ""

    # Apply the replacement, make it fail raising an error if find_content is not found or trying to replace entire file
    if find_content not in current_content:
        return None, MSG_FIND_NOT_FOUND.format(file_path=file_path, content=find_content)
    if not find_content and current_content:
        return None, MSG_WHOLE_FILE_REPLACEMENT.format(file_path=file_path)

    new_content = current_content.replace(find_content, replace_content)
    path.write_text(new_content)
    return new_content, None


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
