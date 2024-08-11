# event_emitter.py

import asyncio

from pluscoder.agents.event.event_handler.base import AgentEventBaseHandler
from pluscoder.type import AgentTask
    

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
                
    def emit_sync(self, event, *args, **kwargs):
        method_name = f"on_{event}"
        for handler in self.handlers:
            method = getattr(handler, method_name, None)
            if method:
                method(*args, **kwargs)