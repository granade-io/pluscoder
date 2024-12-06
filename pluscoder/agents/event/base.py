# event_emitter.py

import asyncio
from enum import Enum


class AgentEvent(Enum):
    NEW_AGENT_INSTRUCTIONS = "on_new_agent_instructions"
    TASK_DELEGATED = "on_task_delegated"
    TASK_VALIDATION_START = "on_task_validation_start"
    TASK_COMPLETED = "on_task_completed"
    TASK_LIST_COMPLETED = "on_task_list_completed"
    FILES_UPDATED = "on_files_updated"
    INDEXING_STARTED = "on_indexing_started"
    INDEXING_COMPLETED = "on_indexing_completed"


class AgentEventBaseHandler:
    """Base class for all event handlers"""

    async def on_new_agent_instructions(self, agent_instructions=None):
        pass

    async def on_task_delegated(self, agent_instructions=None):
        pass

    async def on_task_validation_start(self, agent_instructions=None):
        pass

    async def on_task_completed(self, agent_instructions=None):
        pass

    async def on_task_list_completed(self, agent_instructions=None):
        pass

    async def on_files_updated(self, updated_files):
        pass

    async def on_indexing_started(self, files):
        pass

    async def on_indexing_completed(self):
        pass


class EventEmitter:
    def __init__(self):
        self.handlers = []

    def add_handler(self, handler):
        if isinstance(handler, AgentEventBaseHandler):
            self.handlers.append(handler)
        else:
            msg = "Handler must be an instance of AgentEventBaseHandler"
            raise TypeError(msg)

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

    def emit_sync(self, event, *args, **kwargs):
        method_name = f"on_{event}"
        for handler in self.handlers:
            method = getattr(handler, method_name, None)
            if method:
                method(*args, **kwargs)
