import re
import shutil
import traceback
from typing import Annotated
from typing import Dict
from typing import List
from typing import Literal
from urllib.parse import urlparse

import requests
from langchain_core.tools import tool

from pluscoder.fs import get_formatted_file_content
from pluscoder.io_utils import io
from pluscoder.type import AgentTask


def convert_to_raw_url(url: str) -> str:
    """Convert repository URL to raw file URL."""
    parsed_url = urlparse(url)
    path_parts = parsed_url.path.split("/")

    if parsed_url.netloc == "github.com":
        if len(path_parts) >= 5 and path_parts[3] == "blob":
            return f"https://raw.githubusercontent.com/{path_parts[1]}/{path_parts[2]}/{'/'.join(path_parts[4:])}"
    elif parsed_url.netloc == "gitlab.com" and "/-/blob/" in parsed_url.path:
        return url.replace("/-/blob/", "/-/raw/", 1)
    # elif parsed_url.netloc == "bitbucket.org":
    #     if len(path_parts) >= 5 and path_parts[3] == "src":
    #         return f"https://bitbucket.org/{path_parts[1]}/{path_parts[2]}/raw/{'/'.join(path_parts[4:])}"
    # elif (
    #     parsed_url.netloc == "dev.azure.com"
    #     and len(path_parts) >= 7
    #     and path_parts[5] == "blob"
    # ):
    #     org, project = path_parts[1], path_parts[2]
    #     repo = path_parts[4]
    #     branch_and_file = "/".join(path_parts[6:])
    #     return f"https://dev.azure.com/{org}/{project}/_apis/git/repositories/{repo}/items?path=/{branch_and_file}&api-version=6.0"

    return url  # Return original URL if not a recognized repository link


@tool
def read_file_from_url(url: Annotated[str, "The URL of the file to read."]) -> str:
    """Reads the content of a file given its URL or repository link."""
    try:
        raw_url = convert_to_raw_url(url)
        response = requests.get(raw_url)
        response.raise_for_status()
        content = response.text
        return f"Here is the content of the file:\n\n{content}"
    except requests.RequestException as e:
        return f"Error downloading file: {e!s}. It is possible that the given link is not a valid file or url"


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
    content: Annotated[str, "The entire content including file blocks to be processed."],
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
                return update_file.run({"file_path": file_path, "content": file_content.strip()})
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
            errors.append(f"Error reading file {file_path}. Maybe the path is wrong or the file never existed: {e!s}")

    if errors:
        result += "\n\nErrors:\n" + "\n".join(errors)

    io.event(f"> Added files: {', '.join(loaded_files)}")

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
    return response


@tool
def extract_files(
    mentioned_files: Annotated[str, "Entire list of filenames of file mentions."],
) -> Dict[str, List[Dict[str, str]]]:
    """
    Detect and extract all files mentioned with their full paths.
    """
    io.print(mentioned_files)
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


@tool
def query_repository(
    query: Annotated[
        str, "Natural language query with keywords to find relevant code, content and files in the repository."
    ],
) -> str:
    """
    Search key file snippets and filenames in the repository for better understanding and analysis given a new user request.
    """
    unavailable_message = "Search engine is not available. Just read key files of the repository for better understanding and analysis to handle the user request."
    try:
        from pluscoder.search.engine import SearchEngine

        engine = SearchEngine.get_instance()

        if not engine:
            io.console.print(
                "Warning: Search engine is not available. To improve agents performance please setup the search engine. Check https://granade-io.github.io/pluscoder/documentation/indexing/ for examples.",
                style="bold dark_goldenrod",
            )
            return unavailable_message

        results = engine.search(query, top_k=5)

        if not results:
            return "No matching results found in repository. Just read key files of the repository for better understanding and analysis for handling the user request."

        output = f"Found {len(results)} possible relevant results for query '{query}':\n\n"

        for result in results:
            file_path = result.chunk.file_metadata.file_path
            relevance = f"{result.score:.2%}"
            lines = f"lines {result.start_line}-{result.end_line}"
            snippet = result.chunk.content.strip()

            output += f"📄 {file_path} ({lines}) - Relevance: {relevance}\n"
            output += f"Snippet:\n{snippet}\n\n"

        output += "Given these results analyze which key files to read and if is necessary to perform another search query for handling the user request."

        return output

    except Exception:
        io.print(traceback.format_exc(), style="bold red")
        return unavailable_message


# @tool
# def query_repository(
#     query: Annotated[str, "Query with keywords to find relevant code, content and files in the repository."],
# ) -> str:
#     """
#     Search key file snippets and filenames in the repository for better understanding and analysis given a new user request.
#     """
#     from pluscoder.agents.base import Agent

#     agent = Agent(
#         AgentConfig(
#             id="repo_explorer",
#             name="Explorer",
#             description=RepoExplorerAgent.description,
#             prompt=RepoExplorerAgent.specialization_prompt,
#             reminder="",
#             tools=[tool.name for tool in [read_files, _query_repository]],
#             default_context_files=[],
#             repository_interaction=True,
#             read_only=True,
#             suggestions=RepoExplorerAgent.suggestions,
#         ),
#     )
#     loop = asyncio.get_running_loop()
#     # If exists, run in current loop
#     response = loop.create_task(
#         agent.graph_node(
#             {
#                 "messages": [
#                     HumanMessage(query, tags=["repo_explorer"]),
#                 ],
#             }
#         )
#     )


base_tools = [read_files, move_files, read_file_from_url, query_repository]
