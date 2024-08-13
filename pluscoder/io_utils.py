import os
import logging
from typing import List, Union
from prompt_toolkit import PromptSession
from rich.console import Console, Group, ConsoleRenderable, RichCast
from rich.live import Live
from rich.text import Text
from rich.rule import Rule
from rich.progress import Progress
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.completion import Completer, Completion, WordCompleter
import sys

from pluscoder.repo import Repository

import logging
logging.getLogger().setLevel(logging.ERROR) # hide warning log

class CommandCompleter(Completer):
    def __init__(self):
        super().__init__()
        self.commands = ['/agent', '/clear', '/diff', '/config', '/help', '/undo', '/run']

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        if text.startswith('/'):
            prefix = text[1:]  # Remove the leading '/'
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
        self.chunks.append(chunk)
        
    def get_stream_renderable(self) -> ConsoleRenderable | RichCast | str:
        return Text(''.join(self.chunks), style="dark_blue")
        
    def get_renderable(self) -> ConsoleRenderable | RichCast | str:
        
        renderable = Group(self.get_stream_renderable(), Rule(), *self.get_renderables())
        return renderable

class IO:
    def __init__(self, log_level=logging.INFO):
        self.console = Console()
        self.error_console = Console(stderr=True, style="bold red")
        self.file_console = Console(file=".plus_coderlog.txt", style="cyan")
        self.progress = None
        self.ctrl_c_count = 0
        self.last_input = ""
        
    def event(self, string: str):
        return self.console.print(string, style="yellow")
    
    def confirm(self, message: str) -> bool:
        return input(f'{message} (y/n):').lower().strip() == 'y'
    
    def input(self, string: str, autocomplete=True) -> Union[str, dict]:
        kb = KeyBindings()

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
            completer=completer
        )
        
        try:
            user_input = session.prompt(string)
            self.ctrl_c_count = 0  # Reset the counter when input is successfully received
            self.last_input = user_input
            return user_input
        except KeyboardInterrupt:
            sys.exit(0)
    
    
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
            io.console.print(self.progress.get_stream_renderable())
            self.progress.chunks = []
            # self.progress.stop()
        
        
    def stream(self, chunk: str) -> None:
        if not self.progress:
            self.console.print(chunk, style="dark_blue", end="")
            return
        
        self.progress.stream(chunk)

        
        
io = IO()