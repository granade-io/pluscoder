import traceback
import xml.etree.ElementTree as ET
from itertools import chain
from typing import TYPE_CHECKING
from typing import List
from typing import Optional

from pluscoder.config import config
from pluscoder.exceptions import AgentException
from pluscoder.io_utils import IO

if TYPE_CHECKING:
    from pluscoder.agents.output_handlers.tag_handlers import TagHandler


class XMLStreamParser:
    def __init__(self, io: Optional[IO] = None):
        self.select_tags = ["pc_action", "pc_content", "pc_thinking"]
        self.subscribers: List[TagHandler] = []
        self.agent_errors = []
        self.io = io

    def subscribe(self, callback):
        """Subscribe a callback function to handle tag end events"""
        self.subscribers.append(callback)

    def on_tag_end(self, tag, content, attributes):
        """Notify all subscribers when a tag ends"""
        for subscriber in self.subscribers:
            try:
                subscriber.handle(tag, content, attributes)
            except AgentException as e:
                self.agent_errors.append(e.message)
            except Exception:
                if config.debug:
                    self.io.print(traceback.format_exc(), style="bold red")

    def start_stream(self):
        self.agent_errors = []
        self.buffer = ""
        for subscriber in self.subscribers:
            subscriber.clear_updated_files()

    def close_stream(self):
        pass

    def stream(self, chunk: str):
        """Process incoming data chunk by chunk."""
        if isinstance(chunk, list) and len(chunk) >= 0:
            chunk = "".join([c["text"] for c in chunk if c["type"] == "text"])
        elif isinstance(chunk, str):
            pass
        self.buffer += chunk
        self.process_buffer()

    def process_buffer(self):
        """Process the buffer to find and handle complete desired tags."""
        while True:
            tag_found = False
            for tag in self.select_tags:
                opening_tag_pattern = f"<{tag}"
                # Search for opening tag
                open_pos = self.buffer.find(opening_tag_pattern)
                if open_pos == -1:
                    continue
                # Find end of opening tag '>'
                open_tag_end = self.buffer.find(">", open_pos)
                if open_tag_end == -1:
                    continue  # Incomplete opening tag
                open_tag_end += 1
                # Find matching closing tag
                close_pos = self.find_matching_closing_tag(self.buffer, tag, open_tag_end)
                if close_pos == -1:
                    continue  # Closing tag not found yet
                # Extract the tag content
                tag_content = self.buffer[open_pos:close_pos]
                # Parse the tag content
                try:
                    # Wrap content to make it a well-formed XML
                    wrapped_content = f"<root>{tag_content.split('>', 1)[0] + '>' + f'</{tag}>'}</root>"
                    root = ET.fromstring(wrapped_content)  # noqa: S314
                    element = root.find(tag)
                    if element is None:
                        continue
                    attributes = element.attrib
                    inner_content = tag_content.split(">", 1)[1].replace(f"</{tag}>", "")
                    self.on_tag_end(tag, inner_content, attributes)
                except ET.ParseError:
                    continue  # Wait for more data
                # Remove processed data from buffer to avoid duplicate events
                self.buffer = self.buffer[:open_pos] + self.buffer[close_pos:]
                tag_found = True
                break  # Restart the search after processing a tag
            if not tag_found:
                break

    def find_matching_closing_tag(self, buffer, tag, start_pos):
        """Find the position of the matching closing tag, accounting for nested tags."""
        pos = start_pos
        nesting_level = 1  # Start after the first opening tag
        opening_tag_pattern = f"<{tag}"
        closing_tag_pattern = f"</{tag}>"
        while pos < len(buffer):
            next_open_pos = buffer.find(opening_tag_pattern, pos)
            next_close_pos = buffer.find(closing_tag_pattern, pos)
            if next_close_pos == -1:
                return -1  # Closing tag not found yet
            if next_open_pos != -1 and next_open_pos < next_close_pos:
                nesting_level += 1
                pos = next_open_pos + len(opening_tag_pattern)
            else:
                nesting_level -= 1
                pos = next_close_pos + len(closing_tag_pattern)
                if nesting_level == 0:
                    return pos
        return -1

    def get_updated_files(self):
        return set(chain(*[sub.updated_files for sub in self.subscribers if sub.updated_files]))

    def pop_updated_files(self):
        updated_files = set(chain(*[sub.updated_files for sub in self.subscribers if sub.updated_files]))
        for sub in self.subscribers:
            sub.updated_files.clear()
        return updated_files

    def pop_agent_errors(self):
        errors = self.agent_errors
        self.agent_errors = []
        return errors
