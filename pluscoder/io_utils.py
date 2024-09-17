import os
import logging
import re
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
        self.buffer = ""  # Buffer para acumular los pequeños chunks
        self.in_block = False  # Indicador de si estamos dentro de un bloque
        self.block_content = ""  # Contenido dentro de un bloque
        self.block_type = ""
    
    def _check_block_start(self, text):
        return re.match(r'^<(thinking|output|source)>', text.strip())  # Detectar inicio de bloque

    def _check_block_end(self, text):
        return re.match(f'^</{self.block_type}>', text.strip())  # Detectar fin de bloque
        
    def event(self, string: str):
        return self.console.print(string, style="yellow")
    
    def confirm(self, message: str) -> bool:
        if config.auto_confirm:
            io.event("Auto-confirming...")
            return True
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
            
        completer = CombinedCompleter() if autocomplete else None

        session = PromptSession(
            key_bindings=kb,
            completer=completer,
            history=history
        )
        
        try:
            user_input = session.prompt(string)
            self.ctrl_c_count = 0
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
        self.in_block = False
        if self.progress and not self.progress.started:
            self.progress.start()
        
    def stop_stream(self):
        if not self.progress:
            self.console.print(self.buffer, style="blue")
            self.console.print("")
            self.buffer = ""
            return
        if self.progress.started:
            self.console.print(self.buffer, style="blue")
            self.buffer = ""
            
            self.console.print(self.progress.get_stream_renderable())
            self.progress.chunks = []
            self.progress.stop()

    def _stream_to_user(self, chunk: str) -> None:

        if not self.progress:
            
            self.console.print(chunk, style="blue", end="")
        else:
            self.progress.stream(chunk)

    
    def get_block_color(self) -> str:
        return "light_salmon3" if self.block_type == "thinking" else "blue" if self.block_type == "output" else "white"
    
    def set_block_type(self, block_type: str) -> None:
        self.block_type = block_type
        if config.hide_thinking_blocks and self.block_type == "thinking":
            return
        elif config.hide_output_blocks and self.block_type == "output":
            return
        elif config.hide_source_blocks and self.block_type == "source":
            return
        
        io.console.print(f"::{block_type}::", style=self.get_block_color())
        
    def add_block_content(self, content: str) -> None:
        self.block_content += content
        if config.hide_thinking_blocks and self.block_type == "thinking":
            return
        elif config.hide_output_blocks and self.block_type == "output":
            return
        elif config.hide_source_blocks and self.block_type == "source":
            return
        
        io.console.print(content, style=self.get_block_color(), end="")
    
    def stream(self, chunk: str):
        
        self.buffer += chunk  # Añadir el chunk recibido al buffer
        
        display_now = "<" not in self.buffer and not self.buffer.endswith("\n")

        if display_now and not self.in_block:
            self._stream_to_user(self.buffer)  # Imprimir el buffer si no hay bloques abiertos
            self.buffer = ""  # Limpiar el buffer
        elif "\n<" in self.buffer and not self.in_block:
            self._stream_to_user(self.buffer.split("\n<", 1)[0])  # Imprimir el buffer sin bloques abiertos
            self.buffer = "\n<" + self.buffer.split("\n<", 1)[1]
        elif ("<" not in self.buffer and not self.buffer.endswith("\n") and \
            not self.buffer.endswith("\n<") and "\n</" not in self.buffer) and self.in_block:
            self.add_block_content(self.buffer)
            self.buffer = ""
        elif "\n</" in self.buffer and self.in_block:
            self.add_block_content(self.buffer.split("\n</", 1)[0])
            self.buffer = "\n</" + self.buffer.split("\n</", 1)[1]
            
        if re.search(r'<\w+>', self.buffer) and self._check_block_start(self.buffer) and not self.in_block:
            # Detectar y abrir un bloque
            self.set_block_type(self.buffer.split("<", 1)[1].split(">")[0])
            self.in_block = True
            self.block_content =  ""
            self.add_block_content(self.buffer.split("<", 1)[1].split(">")[1])
            self.buffer = ""
        if re.search(r'<\/\w+>', self.buffer):
            if self._check_block_end(self.buffer):
                # Detectar y cerrar un bloque
                self.in_block = False
                #print(self.block_content)
                self.block_content = ""
                self._stream_to_user(self.buffer.split(">", 1)[1])  # Imprimir el resto del buffer
                self.buffer = ""
                self.buffer = ""
            else: 
                self.add_block_content(self.buffer.split(">", 1)[0] + ">")
                self.buffer = self.buffer.split(">", 1)[1]
        
        
io = IO()