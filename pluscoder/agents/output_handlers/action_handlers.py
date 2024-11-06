from pluscoder.agents.output_handlers.tag_handlers import TagHandler


class ActionStrategy:
    """Abstract strategy for handling different types of actions"""

    def execute(self, params: dict, content: str) -> None:
        raise NotImplementedError


class FileActionHandler(ActionStrategy):
    """Handles file-related actions like create, replace, diff"""

    def execute(self, params: dict, content: str) -> None:
        action = params["action"]
        filepath = params["filepath"]
        action_type = action.replace("file_", "")

        print(f"[FileAction] Would {action_type} file: {filepath}")
        # Mock implementations
        if action_type == "create":
            print(f"[FileAction] Creating new file {filepath}")
        elif action_type == "replace":
            print(f"[FileAction] Replacing content in {filepath}")
        elif action_type == "diff":
            print(f"[FileAction] Generating diff for {filepath}")


class BashActionHandler(ActionStrategy):
    """Handles bash command execution actions"""

    def execute(self, params: dict, content: str) -> None:
        command = content
        print(f"[BashAction] Would execute: {command}")
        # Mock implementation
        print("[BashAction] Command execution simulated")


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

    def process(self, tag, attributes, content) -> None:
        try:
            action = attributes["action"]
            if action in self.handlers:
                self.handlers[action].execute(attributes, content)
            else:
                print(f"Unknown action type: {action}")
        except KeyError as e:
            print(f"Missing required attribute: {e}")
