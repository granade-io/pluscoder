# Event handlers
from pluscoder.agents.event.base import EventEmitter
from pluscoder.agents.event.event_handler.console_event_handler import ConsoleAgentEventHandler
from pluscoder.agents.event.event_handler.git_event_handler import GitEventHandler
from pluscoder.io_utils import io

# Create a single instance of the EventEmitter
event_emitter = EventEmitter()

# Console event handler
console_agent_event_handler = ConsoleAgentEventHandler(io=io)
event_emitter.add_handler(console_agent_event_handler)

# Git event handler
git_event_handler = GitEventHandler()
event_emitter.add_handler(git_event_handler)
