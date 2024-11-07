import traceback
from itertools import chain
from typing import TYPE_CHECKING
from typing import List
from typing import Optional

from lxml import etree

from pluscoder.config import config
from pluscoder.exceptions import AgentException
from pluscoder.io_utils import IO

if TYPE_CHECKING:
    from pluscoder.agents.output_handlers.tag_handlers import TagHandler


class XMLStreamParser:
    def __init__(self, io: Optional[IO] = None):
        self.parser = etree.XMLPullParser(events=("start", "end"), recover=True)
        self.select_tags = ["pc_action", "pc_content", "pc_thinking"]
        self.subscribers: List[TagHandler] = []
        self.agent_errors = []
        self.io = io

    def subscribe(self, callback):
        """Subscribe a callback function to handle tag end events"""
        self.subscribers.append(callback)

    def on_tag_end(self, element):
        """Notify all subscribers when a tag ends"""
        for subscriber in self.subscribers:
            try:
                subscriber.handle(element)
            except AgentException as e:
                self.agent_errors.append(e.message)
            except Exception:
                if config.debug:
                    self.io.console.print(traceback.format_exc(), style="bold red")

    def process_parse_events(self):
        for action, element in self.parser.read_events():
            if element.tag not in self.select_tags:
                continue
            if action == "end":
                self.on_tag_end(element)

    def start_stream(self):
        self.parser = etree.XMLPullParser(events=("start", "end"), recover=True)
        self.agent_errors = []
        for subscriber in self.subscribers:
            subscriber.clear_updated_files()

    def close_stream(self):
        self.parser.close()

    def stream(self, chunk: str):
        if isinstance(chunk, list) and len(chunk) >= 0:
            chunk = "".join([c["text"] for c in chunk if c["type"] == "text"])
        elif isinstance(chunk, str):
            pass
        else:
            error = "Not chunk type"
            raise ValueError(error)

        self.parser.feed(chunk)
        self.process_parse_events()

    def get_updated_files(self):
        return set(chain(*[sub.updated_files for sub in self.subscribers if sub.updated_files]))
