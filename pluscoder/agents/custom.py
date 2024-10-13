from pluscoder import tools
from pluscoder.agents.base import Agent
from pluscoder.agents.prompts import (
    BASE_PROMPT,
    FILE_OPERATIONS_PROMPT,
    OUTPUT_STRUCTURE_PROMPT_READ_ONLY,
    OUTPUT_STRUCTURE_PROMPT_WRITE,
    READONLY_MODE_PROMPT,
    REMINDER_PREFILL_FILE_OPERATIONS_PROMPT,
    REMINDER_PREFILL_PROMP,
    combine_prompts,
)
from pluscoder.config import config
from pluscoder.type import AgentState


class CustomAgent(Agent):
    def __init__(
        self,
        name: str,
        prompt: str,
        read_only: bool,
        description: str,
        tools=[tools.read_files, tools.move_files, tools.read_file_from_url],
        default_context_files=["PROJECT_OVERVIEW.md", "CODING_GUIDELINES.md"],
    ):
        self.id = name.lower()
        self.custom_prompt = prompt
        self.read_only = read_only
        self.description = description
        system_message = self._get_system_message()
        super().__init__(
            system_message,
            name,
            tools=tools,
            default_context_files=default_context_files,
        )

    def _get_system_message(self):
        return combine_prompts(
            BASE_PROMPT,
            self.custom_prompt,
            OUTPUT_STRUCTURE_PROMPT_READ_ONLY
            if config.read_only
            else OUTPUT_STRUCTURE_PROMPT_WRITE,
            FILE_OPERATIONS_PROMPT
            if not self.read_only and not config.read_only
            else READONLY_MODE_PROMPT,
        )

    def process_agent_response(self, state, response):
        if self.read_only:
            return {}
        return super().process_agent_response(state, response)

    def get_reminder_prefill(self, state: AgentState) -> str:
        return combine_prompts(
            REMINDER_PREFILL_PROMP,
            REMINDER_PREFILL_FILE_OPERATIONS_PROMPT
            if not config.read_only and not self.read_only
            else "",
        )
