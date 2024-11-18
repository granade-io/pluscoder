import os
import re
from pathlib import Path
from typing import Dict
from typing import List
from typing import NamedTuple
from typing import Tuple
from typing import Union

CONFIG_FILEPATH = ".pluscoder-config.yml"


class ConfigPaths(NamedTuple):
    local: str  # Repository local config
    global_config: str  # User global config
    global_env: str  # User global env file


def get_config_paths() -> ConfigPaths:
    """Get all possible configuration file paths for pluscoder.

    Returns:
        ConfigPaths: Named tuple containing paths for local and global configs
    """
    local = CONFIG_FILEPATH
    home = str(Path.home())

    if os.name == "nt":  # Windows
        global_config = os.path.join(home, "AppData", "Local", "pluscoder", "config.yml")
        global_env = os.path.join(home, "AppData", "Roaming", "pluscoder", "vars.env")
    else:  # Unix-like
        global_config = os.path.join(home, ".config", "pluscoder", "config.yml")
        global_env = os.path.join(home, ".config", "pluscoder", "vars.env")

    return ConfigPaths(local, global_config, global_env)


def get_local_config() -> str:
    """Get local repository config file path.

    Returns:
        str: Path to local config file
    """
    return get_config_paths().local


def get_global_config() -> str:
    """Get global user config file path.

    Returns:
        str: Path to global config file
    """
    return get_config_paths().global_config


def get_global_env_filepath():
    return get_config_paths().global_env


def read_yaml_file(file_path: str) -> List[str]:
    """
    Read YAML file and return its contents as a list of lines.

    Args:
        file_path (str): Path to the YAML file

    Returns:
        List[str]: List of lines from the file
    """
    with open(file_path, "r") as file:
        return file.readlines()


def find_custom_agents_section(lines: List[str]) -> int:
    """
    Find the index where custom_agents section starts.

    Args:
        lines (List[str]): List of lines from YAML file

    Returns:
        int: Index of custom_agents section, or -1 if not found
    """
    for i, line in enumerate(lines):
        if re.match(r"^custom_agents\s*:", line):
            return i
    return -1


def format_agent_dict(agent: Dict[str, Union[str, bool]], indent: int = 2) -> List[str]:
    """
    Format a single agent dictionary into YAML lines with proper indentation.

    Args:
        agent (Dict): Dictionary containing agent details
        indent (int): Number of spaces for indentation

    Returns:
        List[str]: Formatted lines for the agent
    """
    base_indent = " " * indent
    lines = [f'{base_indent}- name: {agent["name"]}\n']

    # Add other fields with proper indentation
    for key, value in agent.items():
        if key != "name":  # Skip name as it's already added
            if isinstance(value, bool):
                lines.append(f"{base_indent}  {key}: {str(value).lower()}\n")
            elif isinstance(value, list):
                lines.append(f"{base_indent}  {key}: {value}\n")
            else:
                # check if multiline value
                if "\n" in value:
                    # then appends an aditional indent plus '|' multiline string yaml symbol
                    value = "|\n" + base_indent * 3 + value.replace("\n", "\n" + base_indent * 3)  # noqa: PLW2901
                lines.append(f'{base_indent}  {key}: "{value}"\n')

    return lines


def find_insertion_point(lines: List[str], start_index: int) -> int:
    """
    Find the correct insertion point for a new agent by detecting the end of the custom_agents section.

    Args:
        lines (List[str]): List of lines from YAML file
        start_index (int): Index where custom_agents section starts

    Returns:
        int: Index where new agent should be inserted
    """
    last_agent_index = start_index
    in_agents_section = False

    # Check if the section is empty or contains []
    next_line_idx = start_index + 1
    if next_line_idx < len(lines):
        next_line = lines[next_line_idx].strip()
        if next_line == "[]" or not next_line or next_line.startswith("#"):
            return next_line_idx

    for i in range(start_index + 1, len(lines)):
        raw_line = lines[i]
        line = raw_line.strip()

        # Skip empty lines
        if not line:
            continue

        # If we find a list item at the correct indentation, update last_agent_index
        if line.startswith("- "):
            last_agent_index = i
            in_agents_section = True
            continue

        # If we're in the agents section and find a property (indented line)
        if raw_line.startswith("  ") and in_agents_section:
            last_agent_index = i
            continue

        # If we find a new top-level key (no indentation), we've gone too far
        if not raw_line.startswith(" "):
            break

        # Update last_agent_index to include the current line if we're still in an agent's properties
        if in_agents_section and (line.startswith(("  ", "- "))):
            last_agent_index = i

    # Return the index after the last agent
    return last_agent_index + 1


def create_custom_agents_section(lines: List[str]) -> Tuple[List[str], int]:
    """
    Create a new custom_agents section if it doesn't exist.

    Args:
        lines (List[str]): Current file lines

    Returns:
        Tuple[List[str], int]: Updated lines and index where to insert new agent
    """
    # Try to find a suitable location - after comments at the top
    insert_index = 0
    for i, line in enumerate(lines):
        if line.strip() and not line.strip().startswith("#"):
            insert_index = i
            break

    # Add a newline before if there's content
    if insert_index > 0 and lines[insert_index - 1].strip():
        lines.insert(insert_index, "\n")
        insert_index += 1

    # Add the custom_agents section
    lines.insert(insert_index, "custom_agents:\n")

    return lines, insert_index


def append_custom_agent_to_config(new_agent: Dict[str, Union[str, bool]]) -> None:
    """
    Append a new agent to the custom_agents section in the YAML file.
    Creates the section if it doesn't exist.

    Args:
        new_agent (Dict): Dictionary containing the new agent's details
    """
    # Read the file
    lines = read_yaml_file(CONFIG_FILEPATH)

    # Find or create custom_agents section
    custom_agents_index = find_custom_agents_section(lines)
    if custom_agents_index == -1:
        lines, custom_agents_index = create_custom_agents_section(lines)
    elif "[]" in lines[custom_agents_index]:
        lines[custom_agents_index] = lines[custom_agents_index].replace("[]", "").strip() + "\n"

    # Find where to insert the new agent
    insert_index = find_insertion_point(lines, custom_agents_index)

    # If the section is empty with [], remove it
    if insert_index < len(lines) and lines[insert_index].strip() == "[]":
        lines.pop(insert_index)

    # Format and insert the new agent
    new_agent_lines = format_agent_dict(new_agent)

    # If inserting outside the file, add a new line
    if insert_index == len(lines):
        new_agent_lines = ["\n"] + new_agent_lines
    lines[insert_index:insert_index] = new_agent_lines

    # Write back to file
    with open(CONFIG_FILEPATH, "w") as file:
        file.writelines(lines)
