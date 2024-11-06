from typing import Optional
from typing import Set

from lxml import etree

from pluscoder.io_utils import IO


class TagHandler:
    def __init__(self):
        self.handled_tags: Set[str] = set()

    def handle(self, element) -> None:
        if element.tag in self.handled_tags:
            content = (
                etree.tostring(element, encoding="unicode")
                .replace(f"<{element.tag}>", "")
                .replace(f"</{element.tag}>", "")
            )
            self.process(element.tag, element.attrib, content)

    def process(self, tag: str, attributes: dict, content: str) -> None:
        raise NotImplementedError


class ConsoleDisplayHandler(TagHandler):
    def __init__(self, io: Optional[IO] = None):
        self.handled_tags = {"pc_content", "pc_thinking", "pc_action"}
        self.io = io

    def process(self, tag: str, attributes: dict, content: str) -> None:
        style = "green"
        if tag == "pc_thinking":
            content = "::thinking::\n"
            style = "light_salmon3"
        elif tag == "pc_content":
            style = "blue"
        elif tag == "pc_action":
            file = attributes.get("file")
            content = f"`{file}`"
            style = "green"
        self.io.stream(content, style=style)
