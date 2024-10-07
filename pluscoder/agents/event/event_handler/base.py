import asyncio
from enum import Enum
from typing import List

from pluscoder.type import AgentTask


class AgentEvent(Enum):
    NEW_AGENT_INSTRUCTIONS = "on_new_agent_instructions"
    TASK_DELEGATED = "on_task_delegated"
    TASK_VALIDATION_START = "on_task_validation_start"
    TASK_COMPLETED = "on_task_completed"
    TASK_LIST_COMPLETED = "on_task_list_completed"
    FILES_UPDATED = "on_files_updated"


class AgentEventBaseHandler:
    async def on_new_agent_instructions(self, task_list: List[AgentTask]):
        pass

    async def on_task_delegated(self, task):
        pass

    async def on_task_validation_start(self, task):
        pass

    async def on_task_completed(self, task):
        pass

    async def on_task_list_completed(self, task_list):
        pass

    async def on_files_updated(self, updated_files):
        pass


class EventEmitter:
    def __init__(self):
        self.handlers = []

    def add_handler(self, handler):
        if isinstance(handler, AgentEventBaseHandler):
            self.handlers.append(handler)
        else:
            raise TypeError("Handler must be an instance of AgentEventBaseHandler")

    def remove_handler(self, handler):
        if handler in self.handlers:
            self.handlers.remove(handler)

    async def emit(self, event, *args, **kwargs):
        method_name = f"on_{event}"
        for handler in self.handlers:
            method = getattr(handler, method_name, None)
            if method and asyncio.iscoroutinefunction(method):
                await method(*args, **kwargs)
            elif method:
                method(*args, **kwargs)
