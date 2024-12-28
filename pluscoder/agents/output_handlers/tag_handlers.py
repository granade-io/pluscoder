import difflib
import re
from pathlib import Path
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
            self.validate_tag(attributes, content)
            self.process(tag, attributes, content)

    def validate_tag(self, attributes: dict, content: str):
        pass

    def clear_updated_files(self):
        self.updated_files = set()

    def process(self, tag: str, attributes: dict, content: str) -> None:
        raise NotImplementedError


class ConsoleDisplayHandler(TagHandler):
    def __init__(self, io: Optional[IO] = None):
        self.handled_tags = {"pc_content", "pc_thinking", "pc_action"}
        self.io = io

    def display_file_action(self, action: str, attributes: dict, content: str):
        file = attributes.get("file")
        style = "green"
        diff_text = None

        if file:
            self.io.print(f"\n`{file}`", style=style)

        if action == "file_diff":
            pattern = re.compile(r"<original>(.*?)<\/original>[\s\n]*<new>(.*?)<\/new>", re.DOTALL)
            match = re.search(pattern, content)
            if match:
                old_content = match.group(1).strip().splitlines()
                new_content = match.group(2).strip().splitlines()

                # Generate unified diff
                diff = difflib.unified_diff(old_content, new_content, fromfile=file, tofile=file, lineterm="")

                # Convert diff to a single string
                diff_text = "\n".join(diff)

        elif action == "file_create":
            diff_text = content
        elif action == "file_replace":
            filepath = Path(file)
            if filepath.exists():
                old_content = filepath.read_text().splitlines()
                new_content = content.splitlines()
                diff = difflib.unified_diff(old_content, new_content, fromfile=file, tofile=file, lineterm="")
                diff_text = "\n".join(diff)
            else:
                diff_text = content
        # Any errors encountered will be handler and reported by another handler

        if diff_text:
            # Display using rich syntax highlighting
            display_diff(diff_text, file, self.io)

    def process(self, tag: str, attributes: dict, content: str) -> None:
        style = "green"
        if tag == "pc_thinking":
            content = "::thinking::\n"
            style = "light_salmon3"
        elif tag == "pc_content":
            style = "blue"
            content = "\n\n" + content
        elif tag == "pc_action":
            self.display_file_action(attributes["action"], attributes, content)
            return
        self.io.print(content, style=style)
