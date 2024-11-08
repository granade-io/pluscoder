class AgentException(Exception):
    def __init__(self, message: str):
        self.message = message


class NotGitRepositoryException(Exception):
    def __init__(self, folder: str):
        super().__init__(f"{folder} is not a git repository")


class TokenValidationException(Exception):
    def __init__(self, message: str):
        super().__init__(f"Token error: {message}")
