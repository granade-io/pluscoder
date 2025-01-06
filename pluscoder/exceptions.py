class AgentException(Exception):
    def __init__(self, message: str):
        self.message = message


class WorkflowException(Exception):
    def __init__(self, message: str):
        self.message = message


class NotGitRepositoryException(Exception):
    def __init__(self, folder: str):
        super().__init__(f"{folder} is not a git repository")


class TokenValidationException(Exception):
    def __init__(self, message: str):
        super().__init__(f"Token error: {message}")


class GitCloneException(Exception):
    def __init__(self, url: str, error: str):
        super().__init__(f"Failed to clone repository from {url}: {error}")
