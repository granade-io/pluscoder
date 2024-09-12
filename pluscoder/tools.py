import os
from typing import Annotated, Dict, List, Literal
from langchain_core.tools import tool
import re
from pluscoder.fs import get_formatted_file_content
from pluscoder.io_utils import io
from pluscoder.type import AgentTask

@tool
def select_agent(
    agent_node: Annotated[Literal["domain_stakeholder", "planning", "developer", "domain_expert"], "The type of agent to select for the next task."],
    task: Annotated[str, "The specific task to be handled by the selected agent."]
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
    content: Annotated[str, "The entire content including file blocks to be processed."],
    confirmation: Annotated[str, "Confirmation status ('YES' or any other value)."]
) -> str:
    """
    Extract file blocks from content and update the file if confirmed.
    """
    file_blocks = re.findall(r'(\S+)\n```[\w-]*\n(.*?)\n```', content, re.DOTALL)
    
    if not file_blocks:
        return "No file blocks detected in the content."
    
    for file_name, file_content in file_blocks:
        if file_name == file_path:
            if confirmation == "YES":
                return update_file.run({"file_path": file_path, "content": file_content.strip()})
            else:
                return f"Update for {file_path} was not confirmed."
    
    return f"No matching file block found for {file_path}."

@tool
def read_files(
    file_paths: Annotated[List[str], "The paths to the files you want to read."]
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
            errors.append(f"Error reading file {file_path}. Maybe the path is wrong or the file never existed: {str(e)}")
    
    if errors:
        result += "\n\nErrors:\n" + "\n".join(errors)
    
    io.event(f"> Added files: {", ".join(loaded_files)}")
    
    return result.strip()

@tool
def move_file(
    source_path: Annotated[str, "The current path of the file."],
    destination_path: Annotated[str, "The new path where you want to move the file."]
) -> str:
    """Move a file from one location to another."""
    try:
        os.rename(source_path, destination_path)
        return f"File moved successfully from {source_path} to {destination_path}"
    except Exception as e:
        return f"Error moving file: {str(e)}"

@tool
def update_file(
    file_path: Annotated[str, "The path to the file you want to update/create."],
    content: Annotated[str, "New entire content to put in the file."]
) -> str:
    """Replace the entire content of an existing file or create a new file."""
    try:
        with open(file_path, 'w') as file:
            file.write(content)
        return f"File updated successfully at {file_path}"
    except Exception as e:
        return f"Error updating file: {str(e)}"

@tool
def ask_confirmation(
    message: Annotated[str, "The message to display for confirmation."]
) -> str:
    """Ask for user confirmation with a custom message."""
    response = io.console.input(f"[bold green]{message} (y/n): [/bold green]")
    if response.lower() == 'y':
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
    task_list: Annotated[List[AgentTask], "List of tasks, each task being a dictionary with 'objective', 'details', 'agent', 'is_finished', 'restrictions', and 'outcome' keys."]
) -> Dict[str, List[AgentTask]]:
    """
    Delegates tasks to other agents to execute/complete them. Each task in the task_list must be a dict with 6 values: (objective, details, agent, is_finished, restrictions, outcome).
    The 'agent' value must be one of: "domain_stakeholder", "planning", "developer", or "domain_expert".
    The 'is_finished' value is a boolean indicating whether the task has been completed.
    The 'restrictions' value is a string describing any limitations or constraints for the task.
    The 'outcome' value is a string describing the expected result of the task.
    """
    return f"Task '{general_objective}' about to be delegated. \n\n{task_list}"

@tool
def is_task_completed(
    completed: Annotated[bool, "Boolean indicating whether the task is completed."],
    feedback: Annotated[str, "Feedback from the agent regarding the task completion."]
) -> Dict[str, bool]:
    """
    Extract a boolean indicating whether specified task was completed successfully or not
    """
    return {"completed": completed, "feedback": feedback}
