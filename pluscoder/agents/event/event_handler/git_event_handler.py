from pluscoder.agents.event.base import AgentEventBaseHandler
from pluscoder.type import AgentInstructions
from pluscoder.repo import Repository
from pluscoder.io_utils import io
from pluscoder.config import config


class GitEventHandler(AgentEventBaseHandler):
    def __init__(self):
        super().__init__()
        self.repo = Repository(io=io)

    async def on_new_agent_instructions(
        self, agent_instructions: AgentInstructions = None
    ):
        pass

    async def on_task_delegated(self, agent_instructions: AgentInstructions):
        pass

    async def on_task_validation_start(self, agent_instructions: AgentInstructions):
        pass

    async def on_task_completed(self, agent_instructions: AgentInstructions = None):
        pass

    async def on_task_list_completed(
        self, agent_instructions: AgentInstructions = None
    ):
        pass

    async def on_files_updated(self, updated_files):
        if updated_files and config.auto_commits:
            files_str = ", ".join(updated_files)
            commit_message = f"Updated files: {files_str}"
            self.repo.commit(commit_message)
