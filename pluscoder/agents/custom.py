from pluscoder import tools
from pluscoder.agents.base import Agent
from pluscoder.agents.prompts import REMINDER_PREFILL_FILE_OPERATIONS_PROMPT
from pluscoder.agents.prompts import REMINDER_PREFILL_PROMPT
from pluscoder.agents.prompts import combine_prompts
from pluscoder.config import config
from pluscoder.type import AgentState


class CustomAgent(Agent):
    def __init__(self, name: str, prompt: str, **kwargs):
        self.id = name.lower()
        super().__init__(prompt, name, tools=[tools.read_files, tools.move_files, tools.read_file_from_url], **kwargs)

    def get_reminder_prefill(self, state: AgentState) -> str:
        return combine_prompts(
            REMINDER_PREFILL_PROMPT if self.repository_interaction else "",
            REMINDER_PREFILL_FILE_OPERATIONS_PROMPT
            if not config.read_only and not self.read_only and self.repository_interaction
            else "",
            self.reminder,
        )
