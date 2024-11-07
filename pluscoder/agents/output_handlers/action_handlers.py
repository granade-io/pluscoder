import re

from pluscoder.agents.output_handlers.tag_handlers import TagHandler
from pluscoder.exceptions import AgentException
from pluscoder.fs import apply_diff_edition


class ActionStrategy:
    """Abstract strategy for handling different types of actions"""

    def execute(self, params: dict, content: str) -> None:
        raise NotImplementedError


def normalize_diff(diff_text):
    # Split the input text into lines
    lines = diff_text.lstrip().splitlines()

    # Find the minimum leading whitespace on lines starting with + or -
    min_leading_spaces = min(
        (len(re.match(r"^ *", line).group()) for line in lines if line.lstrip().startswith(("+", "-"))), default=0
    )

    # Remove min_leading_spaces from all lines
    normalized_lines = [re.sub(f"^ {{{min_leading_spaces}}}", "", line) for line in lines]

    return "\n".join(normalized_lines).strip("\n")


class FileActionHandler(ActionStrategy):
    """Handles file-related actions like create, replace, diff"""

    def execute(self, params: dict, content: str) -> None:
        from pathlib import Path

        from pluscoder.io_utils import io

        action = params["action"]
        filepath = params["file"]
        action_type = action.replace("file_", "")
        path = Path(filepath)

        if action_type == "create":
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
            io.event(f"> `{filepath}` file created.")
            return {"updated_files": filepath}

        if action_type == "replace":
            if not path.exists():
                msg = f"The file {filepath} were not found in the repository to edit its contents."
                raise AgentException(msg)
            path.write_text(content)
            io.event(f"> `{filepath}` file updated.")
            return {"updated_files": filepath}

        if action_type == "diff":
            if not path.exists():
                msg = f"The file {filepath} were not found in the repository to edit its contents."
                raise AgentException(msg)

            pattern = re.compile(r"<original>(.*?)<\/original>[\s\n]*<new>(.*?)<\/new>", re.DOTALL)
            match = re.search(pattern, content)
            if match:
                old_content = match.group(1).strip()
                new_content = match.group(2).strip()
                _, error = apply_diff_edition(filepath, old_content, new_content, None)
                if error:
                    raise AgentException(error)
                io.event(f"> `{filepath}` file updated. ")
                return {"updated_files": filepath}
        return {}


class BashActionHandler(ActionStrategy):
    """Handles bash command execution actions"""

    def execute(self, params: dict, content: str) -> None:
        command = content
        print(f"[BashAction] Would execute: {command}")
        # Mock implementation
        print("[BashAction] Command execution simulated")
        return {}


class ActionProcessHandler(TagHandler):
    def __init__(self):
        self.handled_tags = {"pc_action"}

        # Single instances for each handler type
        self.file_handler = FileActionHandler()
        self.bash_handler = BashActionHandler()

        # Map action types to handlers
        self.handlers = {
            "file_create": self.file_handler,
            "file_replace": self.file_handler,
            "file_diff": self.file_handler,
            "bash_cmd": self.bash_handler,
        }

    def validate_tag(self, attributes: dict, content: str):
        required_attributes = ["action", "file"]
        missing_attributes = [attr for attr in required_attributes if attr not in attributes]
        if missing_attributes:
            msg = f"One of the actions has missing attributes: {', '.join(missing_attributes)}. Please ensure that all necessary attributes are provided when writing an action tag."
            raise AgentException(msg)

        valid_actions = ["file_create", "file_replace", "file_diff", "bash_cmd"]
        action = attributes.get("action")
        if action not in valid_actions:
            msg = f"Invalid tag action '{action}'. Valid actions are: {', '.join(valid_actions)}. Please use a valid action. Remember to provider proper attributes."
            raise AgentException(msg)

        # Add additional content validation if necessary

    def process(self, tag, attributes, content) -> None:
        self.validate_tag(attributes, content)
        action = attributes["action"]
        if action in self.handlers:
            result = self.handlers[action].execute(attributes, content)
            self.updated_files.add(result.get("updated_files"))
        else:
            print(f"Unknown action type: {action}")
