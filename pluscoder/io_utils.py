import json
import logging
import os
import sys
import tempfile
from pathlib import Path
from typing import Optional

from PIL import ImageGrab
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer
from prompt_toolkit.completion import Completion
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from rich.console import Console
from rich.console import ConsoleRenderable
from rich.console import Group
from rich.progress import Progress
from rich.prompt import Confirm
from rich.rule import Rule
from rich.text import Text

from pluscoder.config import config
from pluscoder.repo import Repository

logging.getLogger().setLevel(logging.ERROR)  # hide warning log

# TODO: move this to config?
INPUT_HISTORY_FILEPATH = ".pluscoder/input_history.txt"


class CustomConsole(Console):
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            cls._instance = super().__new__(cls)
        return cls._instance


class CommandCompleter(Completer):
    def __init__(self, file_completer):
        super().__init__()
        self.file_completer = file_completer
        self.commands = []

    def register_command(self, command_name: str, command_description: str):
        """Register a new command for autocompletion"""
        if not command_name.startswith("/"):
            command_name = f"/{command_name}"
        if command_name not in self.commands:
            self.commands.append(
                {
                    "name": command_name,
                    "description": command_description,
                }
            )

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        if text.startswith("/"):
            words = text.split()
            if len(words) == 1 and not text.endswith(" "):
                # Complete command names
                for command in self.commands:
                    if command["name"].startswith(text):
                        yield Completion(
                            command["name"], start_position=-len(text), display_meta=command["description"]
                        )
            elif words[0] == "/custom" and (len(words) == 2 or len(words) == 1 and text.endswith(" ")):
                # Complete custom prompt names
                prompt_name = words[1] if len(words) == 2 else ""
                for prompt in config.custom_prompt_commands:
                    if prompt["prompt_name"].startswith(prompt_name) and prompt_name != prompt["prompt_name"]:
                        yield Completion(
                            prompt["prompt_name"],
                            start_position=-len(prompt_name),
                            display_meta=prompt["description"],
                        )
            else:
                yield from (
                    Completion(
                        completion.text,
                        completion.start_position,
                        display=completion.display,
                    )
                    for completion in self.file_completer.get_completions(document, complete_event)
                )


class FileNameCompleter(Completer):
    def __init__(self):
        super().__init__()
        self.repo = Repository()

    def get_completions(self, document, complete_event):
        text_before_cursor = document.text_before_cursor
        words = text_before_cursor.split()
        if not words:
            return

        last_word = words[-1]

        # Get git tracked files in project
        repo_files = self.repo.get_tracked_files()

        for filepath in repo_files:
            # splits filepath into directories and filename
            directories, filename = os.path.split(filepath)
            if any(part.startswith(last_word) for part in directories.split(os.sep) + [filename]):
                yield Completion(filepath, start_position=-len(last_word))


class CombinedCompleter(Completer):
    def __init__(self):
        self.file_completer = FileNameCompleter()
        self.command_completer = CommandCompleter(file_completer=self.file_completer)

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        if text.startswith("/"):
            yield from self.command_completer.get_completions(document, complete_event)
        else:
            yield from self.file_completer.get_completions(document, complete_event)


class CustomProgress(Progress):
    started = False
    chunks = []
    style = "blue"

    def start(self) -> None:
        self.chunks = []
        self.started = True
        return super().start()

    def stop(self) -> None:
        self.started = False
        return super().stop()

    def flush(self, style):
        # Combine all previous chunks with the first part of the new chunk
        full_text = "".join(self.chunks)

        # Print the full text
        self.console.print(full_text, style=style)

        # Clear the chunks list and add only the remainder (if any)
        self.chunks.clear()

    def stream(self, chunk: str, style: str = "blue") -> None:
        if "\n" in chunk:
            # Split the chunk by the last newline
            parts = chunk.rsplit("\n", 1)

            # Combine all previous chunks with the first part of the new chunk
            full_text = "".join(self.chunks) + parts[0]

            # Print the full text
            self.console.print(full_text, style=style)

            # Clear the chunks list and add only the remainder (if any)
            self.chunks.clear()
            if len(parts) > 1:
                self.chunks.append(parts[1])
        else:
            self.chunks.append(chunk)
        self.style = style

    def get_stream_renderable(self) -> ConsoleRenderable:
        return Text("".join(self.chunks), style=self.style)

    def get_renderable(self) -> ConsoleRenderable:
        return Group(self.get_stream_renderable(), Rule(), *self.get_renderables())


class IO:
    # TODO: move to config
    DEBUG_FILE = ".pluscoder/debug.txt"

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, log_level=logging.INFO):
        self.console = CustomConsole()
        self.progress = None
        self.ctrl_c_count = 0
        self.last_input = ""
        self.completer = CombinedCompleter()

    def register_command(self, command_name: str, command_description: str):
        """Register a new command for autocompletion"""
        if self.completer.command_completer:
            self.completer.command_completer.register_command(command_name, command_description)

    def event(self, string: str):
        return self.console.print(string, style="yellow")

    def handle_clipboard_image(self):
        try:
            image = ImageGrab.grabclipboard()
            if image:
                fd, path = tempfile.mkstemp(suffix=".png")
                image.save(path, "PNG")
                os.close(fd)
                return path
        except Exception as e:
            self.console.print(f"Error handling clipboard image: {e}", style="bold red")
        return None

    def input(self, string: str, autocomplete=True) -> str:
        kb = KeyBindings()

        # Create the directory if it doesn't exist
        path = Path(INPUT_HISTORY_FILEPATH)
        path.parent.mkdir(parents=True, exist_ok=True)
        history = FileHistory(".pluscoder/input_history.txt")

        @kb.add("escape", "c-m", eager=True)
        def _(event):
            event.current_buffer.insert_text("\n")

        @kb.add("c-c")
        def _(event):
            buf = event.current_buffer
            if not buf.text:
                self.ctrl_c_count += 1
                if self.ctrl_c_count == 2:
                    event.app.exit(exception=KeyboardInterrupt)
                else:
                    self.console.print("\nPress Ctrl+C again to exit.")
            else:
                self.ctrl_c_count = 0
                buf.text = ""
                buf.cursor_position = 0

        @kb.add("c-v")
        def _(event):
            image_path = self.handle_clipboard_image()
            if image_path:
                event.current_buffer.insert_text("img::" + image_path)

        completer = self.completer if autocomplete else None

        session = PromptSession(key_bindings=kb, completer=completer, history=history)

        try:
            user_input = session.prompt(string)
            self.ctrl_c_count = 0
            self.last_input = user_input
            return user_input
        except KeyboardInterrupt:
            sys.exit(0)

    def confirm(self, message: str) -> bool:
        if config.auto_confirm:
            io.event("> Auto-confirming...")
            return True
        return Confirm.ask(f"[green]{message}[/green]", console=self.console, default=True)

    def log_to_debug_file(
        self,
        message: Optional[str] = None,
        json_data: Optional[dict] = None,
        indent: int = 0,
    ) -> None:
        if json_data is not None:
            try:
                content = json.dumps(json_data, indent=2)
            except Exception:
                content = message
        elif message is not None:
            content = message
        else:
            msg = "Either message or json_data must be provided"
            raise ValueError(msg)

        # Create the directory if it doesn't exist
        path = Path(self.DEBUG_FILE)
        path.parent.mkdir(parents=True, exist_ok=True)

        # Apply indentation
        indented_content = "\n".join(" " * indent + line for line in content.split("\n"))

        with open(self.DEBUG_FILE, "a") as f:
            f.write(f"{indented_content}\n")

    def set_progress(self, progress: Progress) -> None:
        self.progress = progress

    def stream(self, chunk: str, style=None) -> None:
        if not self.progress:
            self.console.print(chunk, style=style, end="")
        else:
            self.progress.stream(chunk, style)


io = IO()
