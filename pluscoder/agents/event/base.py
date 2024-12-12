# event_emitter.py

import asyncio
from enum import Enum
from typing import Any


class AgentEvent(Enum):
    NEW_AGENT_INSTRUCTIONS = "on_new_agent_instructions"
    TASK_DELEGATED = "on_task_delegated"
    TASK_VALIDATION_START = "on_task_validation_start"
    TASK_COMPLETED = "on_task_completed"
    TASK_LIST_COMPLETED = "on_task_list_completed"
    FILES_UPDATED = "on_files_updated"
    INDEXING_STARTED = "on_indexing_started"
    INDEXING_COMPLETED = "on_indexing_completed"
    COST_UPDATE = "on_cost_update"
    LIVE_DISPLAY_UPDATE = "on_live_display_update"
    AGENT_STATE_UPDATE = "on_agent_state_update"


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

    async def on_indexing_started(self, chunks=0):
        pass

    async def on_indexing_progress(self, data=None):
        pass

    async def on_indexing_completed(self):
        pass

    async def on_cost_update(self, token_usage=None):
        """Handle token usage updates."""

    async def on_live_display_update(self, component_name: str, data: Any) -> None:
        """Handle updates to live display components.
        Args:
            component_name: Name of component to update
            data: New data for the component
        """

    async def on_agent_state_update(self, agent_state=None):
        """Handle agent state updates."""


class EventEmitter:
    def __init__(self):
        self.handlers = []

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            cls._instance = super().__new__(cls)
        return cls._instance

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
            if method:
                if asyncio.iscoroutinefunction(method):
                    await method(*args, **kwargs)
                else:
                    method(*args, **kwargs)

    def emit_sync(self, event, *args, **kwargs):
        """Emit event synchronously, handling both sync and async methods."""
        method_name = f"on_{event}"
        for handler in self.handlers:
            method = getattr(handler, method_name, None)
            if not method:
                continue

            try:
                # For sync methods just call directly
                if not asyncio.iscoroutinefunction(method):
                    method(*args, **kwargs)
                # For async methods in sync context
                else:
                    try:
                        loop = asyncio.get_running_loop()
                        task = asyncio.create_task(method(*args, **kwargs))
                        # Ensure task reference is maintained
                        _ = task
                    except RuntimeError:
                        # No loop running, create new one
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(method(*args, **kwargs))
            except Exception as e:
                # Log error but continue execution
                print(f"Error in event handler {method_name}: {e}")
