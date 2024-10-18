import json
import logging
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from PIL import ImageGrab
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from rich.console import Console, ConsoleRenderable, Group, RichCast
from rich.live import Live
from rich.progress import Progress
from rich.prompt import Confirm
from rich.rule import Rule
from rich.text import Text

from pluscoder.config import config
from pluscoder.display_utils import display_file_diff
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
        self.commands = [
            "/agent",
            "/clear",
            "/diff",
            "/config",
            "/help",
            "/undo",
            "/run",
            "/init",
            "/show_repo",
            "/show_repomap",
            "/show_config",
            "/custom",
        ]

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        if text.startswith("/"):
            words = text.split()
            if len(words) == 1:
                # Complete command names
                for command in self.commands:
                    if command.startswith(text):
                        yield Completion(command, start_position=-len(text))
            elif len(words) == 2 and words[0] == "/custom":
                # Complete custom prompt names
                prompt_name = words[1]
                for prompt in config.custom_prompt_commands:
                    if (
                        prompt["prompt_name"].startswith(prompt_name)
                        and prompt_name != prompt["prompt_name"]
                    ):
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
                    for completion in self.file_completer.get_completions(
                        document, complete_event
                    )
                )


class FileNameCompleter(Completer):
    def __init__(self):
        super().__init__()
        self.repo = Repository(io=io)

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
            if any(
                part.startswith(last_word)
                for part in directories.split(os.sep) + [filename]
            ):
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

    def get_stream_renderable(self) -> ConsoleRenderable | RichCast | str:
        return Text("".join(self.chunks), style=self.style)

    def get_renderable(self) -> ConsoleRenderable | RichCast | str:
        renderable = Group(
            self.get_stream_renderable(), Rule(), *self.get_renderables()
        )
        return renderable


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
        self.buffer = ""  # Buffer para acumular los pequeños chunks
        self.filepath_buffer = (
            ""  # Buffer to store last 100 characters for filepath detection
        )
        self.in_block = False  # Indicador de si estamos dentro de un bloque
        self.block_content = ""  # Contenido dentro de un bloque
        self.block_type = ""
        self.current_filepath = ""  # New attribute to store the current filepath
        self.buffer_size = 20  # Buffer size to hold before display to look for blocks
        self.valid_blocks = {"thinking", "source"}

    def _check_block_start(self, text):
        return re.match(
            r"^<(thinking|output|source)>", text.strip()
        )  # Detectar inicio de bloque

    def _check_block_end(self, text):
        return re.match(
            f"^</{self.block_type}>", text.strip()
        )  # Detectar fin de bloque

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

    def input(self, string: str, autocomplete=True) -> Union[str, List[Dict[str, Any]]]:
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

        completer = CombinedCompleter() if autocomplete else None

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
        return Confirm.ask(
            f"[green]{message}[/green]", console=self.console, default=True
        )

    def log_to_debug_file(
        self, message: Optional[str] = None, json_data: Optional[dict] = None
    ) -> None:
        if json_data is not None:
            try:
                content = json.dumps(json_data, indent=2)
            except Exception:
                content = message
        elif message is not None:
            content = message
        else:
            raise ValueError("Either message or json_data must be provided")

        # Create the directory if it doesn't exist
        path = Path(self.DEBUG_FILE)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.DEBUG_FILE, "a") as f:
            f.write(f"{content}\n")

    def set_progress(self, progress: Progress | Live) -> None:
        self.progress = progress

    def start_stream(self):
        self.in_block = False
        self.seen_nl = False
        if self.progress and not self.progress.started:
            self.progress.start()

    def stop_stream(self):
        if not self.progress:
            self.console.print(self.buffer, style="blue")
            self.console.print("")
            self.buffer = ""
            self.filepath_buffer = ""
            return
        if self.progress.started:
            self.console.print(self.buffer, style="blue")
            self.buffer = ""
            self.filepath_buffer = ""

            self.console.print(self.progress.get_stream_renderable())
            self.progress.chunks = []
            self.progress.stop()

    def _stream_to_user(self, chunk: str, style=None) -> None:
        style = style or self.get_block_color()
        if not self.progress:
            self.console.print(chunk, style=style, end="")
        else:
            self.progress.stream(chunk, style)

    def get_block_color(self) -> str:
        pass
        return (
            "light_salmon3"
            if self.block_type == "thinking"
            else "blue"
            if self.block_type == "output"
            else "blue"
        )

    def start_block(self, block_type: str) -> None:
        # starts new block
        self.block_type = block_type
        self.in_block = True

        # Display block header
        if block_type == "thinking":
            if self.progress:
                self.progress.flush(self.get_block_color())
            self.console.print(f"::{block_type}::", style=self.get_block_color())

    def end_block(self) -> None:
        if self.block_type == "source":
            self.flush()
            displayed = display_file_diff(
                self.block_content, self.current_filepath, self.console
            )

            # Fall back to display raw code if fails to display diff
            if not displayed and not config.hide_source_blocks:
                self._stream_to_user(self.block_content, style=self.get_block_color())
                self._stream_to_user("\n")

        if self.buffer:
            # Clean leftovers from buffer if external end of blocks are called
            self._stream_to_user(self.buffer, style=self.get_block_color())
            self.buffer = ""
        self.in_block = False
        self.block_type = None
        self.current_filepath = None
        self.block_content = ""

    def stream_block_chunk(self, chunk: str) -> None:
        self.block_content += chunk
        if (
            config.hide_thinking_blocks
            and self.block_type == "thinking"
            or config.hide_output_blocks
            and self.block_type == "output"
            or config.hide_source_blocks
            and self.block_type == "source"
        ):
            return

        self._stream_to_user(chunk, style=self.get_block_color())

    def flush(self):
        pass
        # if self.buffer:
        #     self.console.print(self.buffer, style=self.get_block_color())
        #     self.buffer = ""

    def stream(self, chunk: str):
        self.seen_nl = self.seen_nl or "\n<" in chunk

        if isinstance(chunk, list) and len(chunk) >= 0:
            chunk = "".join([c["text"] for c in chunk if c["type"] == "text"])
        elif isinstance(chunk, str):
            pass
        else:
            raise ValueError("Not chunk type")

        # Update filepath_buffer
        self.filepath_buffer += chunk
        self.filepath_buffer = self.filepath_buffer[
            -100:
        ]  # Keep only last 100 characters

        # Update main buffer
        self.buffer += chunk

        # Look for block start/end with capturing group for block type
        start_match = re.search(
            r"\n<(thinking|output|source)>"
            if self.seen_nl
            else r"\n?<(thinking|output|source)>",
            self.buffer,
        )
        end_match = re.search(r"\n</(thinking|output|source)>", self.buffer)

        if "<" in self.buffer:
            pass

        if self.in_block:
            if end_match and end_match.group(1) == self.block_type:
                # Found matching end of block
                end_pos = end_match.end()

                # Print anything after the block
                self._stream_to_user(self.buffer[end_pos:])
                self.block_content += self.buffer[: end_match.start()]

                # Reset buffer must be before end of block because end of block also prints buffer when be called from
                # other sources
                self.buffer = ""
                self.end_block()
            else:
                # Still in block, add everything except last 20 chars to block_content
                self.stream_block_chunk(self.buffer[: -self.buffer_size])
                self.buffer = self.buffer[-self.buffer_size :]

        elif start_match:
            # Found start of block
            block_type = start_match.group(1)
            if block_type in self.valid_blocks:
                # Check for filepath pattern in filepath_buffer
                filepath_match = re.search(
                    r"`([^`\n]+):?`\n{1,2}^<source>", self.buffer, re.MULTILINE
                )
                if filepath_match:
                    self.current_filepath = filepath_match.group(1)
                    self.filepath_buffer = self.filepath_buffer.replace(
                        filepath_match.group(0), "<source>"
                    )

                start_pos = start_match.start()
                self._stream_to_user(self.buffer[:start_pos])
                self.start_block(block_type)
                self.block_content = self.buffer[start_match.end() :]
                self.buffer = ""
            else:
                self._stream_to_user(self.buffer[: -self.buffer_size])
                self.buffer = self.buffer[-self.buffer_size :]
        elif len(self.buffer) > self.buffer_size:
            self._stream_to_user(self.buffer[: -self.buffer_size])
            self.buffer = self.buffer[-self.buffer_size :]


io = IO()
