import difflib
import re
from typing import Optional
from typing import Set

from pluscoder.display_utils import display_diff
from pluscoder.io_utils import IO


class TagHandler:
    updated_files = set()

    def __init__(self):
        self.handled_tags: Set[str] = set()

    def handle(self, tag, content, attributes) -> None:
        if tag in self.handled_tags:
            self.process(tag, attributes, content)

    def clear_updated_files(self):
        self.updated_files = set()

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
            style = "green"
            self.io.console.print(f"\n`{file}`", style=style)

            # get contents
            pattern = re.compile(r"%%original%%(.*?)<\/original>[\s\n]*%%new%%(.*?)<\/new>", re.DOTALL)
            match = re.search(pattern, content)
            if match:
                old_content = match.group(1).strip().splitlines()
                new_content = match.group(2).strip().splitlines()

                # Generate unified diff
                diff = difflib.unified_diff(old_content, new_content, fromfile=file, tofile=file, lineterm="")

                # Convert diff to a single string
                diff_text = "\n".join(diff)

                # Display using rich syntax highlighting
                display_diff(diff_text, file, self.io.console)
            else:
                self.io.console.print(content, style=style)
            return
        self.io.console.print(content, style=style)
