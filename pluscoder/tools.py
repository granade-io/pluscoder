import re
import shutil
from typing import Annotated, Dict, List, Literal

import requests
from langchain_core.tools import tool

from pluscoder.fs import get_formatted_file_content
from pluscoder.io_utils import io
from pluscoder.type import AgentTask


@tool
def read_file_from_url(url: Annotated[str, "The URL of the file to read."]) -> str:
    """Reads the content of a file given its URL."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        content = response.text
        return f"Here is the content of the file:\n\n{content}"
    except requests.RequestException as e:
        return f"Error downloading file: {e!s}"


@tool
def move_files(
    file_paths: Annotated[
        List[Dict[str, str]],
        "List of dictionaries, each containing 'from' and 'to' keys for the source and destination paths of each file to be moved.",
    ],
) -> str:
    """Move multiple files from their current locations to new locations."""
    results = []
    for file_path in file_paths:
        from_path = file_path["from"]
        to_path = file_path["to"]
        try:
            shutil.move(from_path, to_path)
            results.append(f"Successfully moved {from_path} to {to_path}")
        except Exception as e:
            results.append(f"Failed to move {from_path} to {to_path}: {e!s}")

    success_count = sum(1 for result in results if result.startswith("Successfully"))
    failure_count = len(results) - success_count

    summary = f"Moved {success_count} file(s) successfully. {failure_count} file(s) failed to move."
    details = "\n".join(results)

    return f"{summary}\n\nDetails:\n{details}"


@tool
def select_agent(
    agent_node: Annotated[
        Literal["domain_stakeholder", "planning", "developer", "domain_expert"],
        "The type of agent to select for the next task.",
    ],
    task: Annotated[str, "The specific task to be handled by the selected agent."],
) -> str:
    """
    Select the best suitable and appropriate agent for handling the specific task.
    """
    # This tool doesn't need real logic
    # LLM response fills this tool with all values we define here for future use
    return f"{agent_node}:{task}"


@tool
def file_detection_with_confirmation(
    file_path: Annotated[str, "The path to the file you want to update."],
    content: Annotated[
        str, "The entire content including file blocks to be processed."
    ],
    confirmation: Annotated[str, "Confirmation status ('YES' or any other value)."],
) -> str:
    """
    Extract file blocks from content and update the file if confirmed.
    """
    file_blocks = re.findall(r"(\S+)\n```[\w-]*\n(.*?)\n```", content, re.DOTALL)

    if not file_blocks:
        return "No file blocks detected in the content."

    for file_name, file_content in file_blocks:
        if file_name == file_path:
            if confirmation == "YES":
                return update_file.run(
                    {"file_path": file_path, "content": file_content.strip()}
                )
            else:
                return f"Update for {file_path} was not confirmed."

    return f"No matching file block found for {file_path}."


@tool
def read_files(
    file_paths: Annotated[List[str], "The paths to the files you want to read."],
) -> str:
    """Read the contents of multiple files at once"""
    result = ""
    errors = []
    loaded_files = []

    for file_path in file_paths:
        try:
            result += get_formatted_file_content(file_path)
            loaded_files.append(file_path)
        except Exception as e:
            errors.append(
                f"Error reading file {file_path}. Maybe the path is wrong or the file never existed: {e!s}"
            )

    if errors:
        result += "\n\nErrors:\n" + "\n".join(errors)

    io.event(f"> Added files: {", ".join(loaded_files)}")

    return "Here are the files content:\n\n" + result.strip()


@tool
def update_file(
    file_path: Annotated[str, "The path to the file you want to update/create."],
    content: Annotated[str, "New entire content to put in the file."],
) -> str:
    """Replace the entire content of an existing file or create a new file."""
    try:
        with open(file_path, "w") as file:
            file.write(content)
        return f"File updated successfully at {file_path}"
    except Exception as e:
        return f"Error updating file: {e!s}"


@tool
def ask_confirmation(
    message: Annotated[str, "The message to display for confirmation."],
) -> str:
    """Ask for user confirmation with a custom message."""
    response = io.console.input(f"[bold green]{message} (y/n): [/bold green]")
    if response.lower() == "y":
        return "Confirmed"
    else:
        return response


@tool
def extract_files(
    mentioned_files: Annotated[str, "Entire list of filenames of file mentions."],
) -> Dict[str, List[Dict[str, str]]]:
    """
    Detect and extract all files mentioned with their full paths.
    """
    io.console.print(mentioned_files)
    return mentioned_files


@tool
def delegate_tasks(
    general_objective: Annotated[str, "The general objective for all tasks."],
    task_list: Annotated[
        List[AgentTask],
        "List of tasks, each task being a dictionary with 'objective', 'details', 'agent', 'is_finished', 'restrictions', and 'outcome' keys.",
    ],
    resources: Annotated[
        List[str],
        "List of resources specified by the user external to the repository. (url/links/local files)",
    ],
) -> Dict[str, List[AgentTask]]:
    """
    Delegates tasks to other agents to execute/complete them. Each task in the task_list must be a dict with 6 values: (objective, details, agent, is_finished, restrictions, outcome).
    The 'agent' value must be one of: "developer".
    The 'is_finished' value is a boolean indicating whether the task has been completed.
    The 'restrictions' value is a string describing any limitations or constraints for the task.
    The 'outcome' value is a string describing the expected result of the task.
    The 'resources' value contains the list of resources the same exact format the user passed it. Including 'img::' if present.
    """
    return f"Task '{general_objective}' about to be delegated. \n\n{task_list}"


@tool
def is_task_completed(
    completed: Annotated[bool, "Boolean indicating whether the task is completed."],
    feedback: Annotated[str, "Feedback from the agent regarding the task completion."],
) -> Dict[str, bool]:
    """
    Extract a boolean indicating whether specified task was completed successfully or not
    """
    return {"completed": completed, "feedback": feedback}
