from pluscoder import tools
from pluscoder.agents.base import Agent
from pluscoder.agents.prompts import (
    BASE_PROMPT,
    FILE_OPERATIONS_PROMPT,
    READONLY_MODE_PROMPT,
    combine_prompts,
)
from pluscoder.config import config


class CustomAgent(Agent):
    def __init__(
        self,
        llm,
        name: str,
        prompt: str,
        read_only: bool,
        description: str,
        tools=[tools.read_files, tools.move_files, tools.download_file],
        default_context_files=["PROJECT_OVERVIEW.md", "CODING_GUIDELINES.md"],
    ):
        self.id = name.lower()
        self.custom_prompt = prompt
        self.read_only = read_only
        self.description = description
        system_message = self._get_system_message()
        super().__init__(
            llm,
            system_message,
            name,
            tools=tools,
            default_context_files=default_context_files,
        )

    def _get_system_message(self):
        prompts = [BASE_PROMPT, self.custom_prompt]
        if not self.read_only and not config.read_only:
            prompts.append(FILE_OPERATIONS_PROMPT)
        else:
            prompts.append(READONLY_MODE_PROMPT)
        return combine_prompts(*prompts)

    def process_agent_response(self, state, response):
        if self.read_only:
            return {}
        return super().process_agent_response(state, response)
