import os
import logging
from typing import Union, Optional
import json
from prompt_toolkit import PromptSession
from rich.console import Console, Group, ConsoleRenderable, RichCast
from rich.live import Live
from rich.text import Text
from rich.rule import Rule
from rich.progress import Progress
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.history import FileHistory
import sys

from pluscoder.repo import Repository
from pluscoder.config import config

logging.getLogger().setLevel(logging.ERROR) # hide warning log

class CommandCompleter(Completer):
    def __init__(self):
        super().__init__()
        self.commands = ['/agent', '/clear', '/diff', '/config', '/help', '/undo', '/run', '/init']

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        if text.startswith('/'):
            text[1:]  # Remove the leading '/'
            for command in self.commands:
                if command.startswith(text):
                    yield Completion(command, start_position=-len(text))

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
            if any(part.startswith(last_word) for part in directories.split(os.sep) + [filename]):
                yield Completion(filepath, start_position=-len(last_word))

class CombinedCompleter(Completer):
    def __init__(self):
        self.command_completer = CommandCompleter()
        self.file_completer = FileNameCompleter()

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        if text.startswith('/'):
            yield from self.command_completer.get_completions(document, complete_event)
        else:
            yield from self.file_completer.get_completions(document, complete_event)

class CustomProgress(Progress):
    started = False
    chunks = []
    
    def start(self) -> None:
        self.chunks = []
        self.started = True
        return super().start()
    
    def stop(self) -> None:
        self.started = False
        return super().stop()
    
    def stream(self, chunk: str) -> None:
        if '\n' in chunk:
            # Split the chunk by the last newline
            parts = chunk.rsplit('\n', 1)
            
            # Combine all previous chunks with the first part of the new chunk
            full_text = ''.join(self.chunks) + parts[0]
            
            # Print the full text
            self.console.print(full_text, style="blue")
            
            # Clear the chunks list and add only the remainder (if any)
            self.chunks.clear()
            if len(parts) > 1:
                self.chunks.append(parts[1])
        else:
            self.chunks.append(chunk)
        
    def get_stream_renderable(self) -> ConsoleRenderable | RichCast | str:
        return Text(''.join(self.chunks), style="blue")
        
    def get_renderable(self) -> ConsoleRenderable | RichCast | str:
        
        renderable = Group(self.get_stream_renderable(), Rule(), *self.get_renderables())
        return renderable

class IO:
    DEBUG_FILE = ".plus_coder.debug"
    def __init__(self, log_level=logging.INFO):
        self.console = Console()
        self.error_console = Console(stderr=True, style="bold red")
        self.progress = None
        self.ctrl_c_count = 0
        self.last_input = ""
        
    def event(self, string: str):
        return self.console.print(string, style="yellow")
    
    def confirm(self, message: str) -> bool:
        if config.auto_confirm:
            io.event("Auto-confirming...")
            return True
        # return Confirm.ask(f"{message}", console=self.console)
        return input(f'{message} (y/n):').lower().strip() == 'y'
    
    def input(self, string: str, autocomplete=True) -> Union[str, dict]:
        kb = KeyBindings()
        history = FileHistory('.plus_coder_input_history')

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
            
        # Autocompleter config
        completer = None
        if autocomplete:
            completer = CombinedCompleter()

        session = PromptSession(
            key_bindings=kb,
            completer=completer,
            history=history
        )
        
        try:
            user_input = session.prompt(string)
            self.ctrl_c_count = 0  # Reset the counter when input is successfully received
            self.last_input = user_input
            return user_input
        except KeyboardInterrupt:
            sys.exit(0)
    
    def log_to_debug_file(self, message: Optional[str] = None, json_data: Optional[dict] = None) -> None:
        if json_data is not None:
            try:
                content = json.dumps(json_data, indent=2)
            except Exception:
                content = message
        elif message is not None:
            content = message
        else:
            raise ValueError("Either message or json_data must be provided")

        with open(self.DEBUG_FILE, "a") as f:
            f.write(f"{content}\n")
    
    def set_progress(self, progress: Progress | Live) -> None:
        self.progress = progress
    
    
    def start_stream(self):
        if not self.progress:
            return
        # if not self.progress.started:
            # self.progress.start()
        
    def stop_stream(self):
        if not self.progress:
            self.console.print("")
            return
        if self.progress.started:
            self.console.print(self.progress.get_stream_renderable())
            self.progress.chunks = []
            # self.progress.stop()
        
        
    def stream(self, chunk: str) -> None:
        if not self.progress:
            self.console.print(chunk, style="blue", end="")
            return
        
        self.progress.stream(chunk)

        
        
io = IO()