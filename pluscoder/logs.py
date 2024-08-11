from datetime import datetime
from typing import Any, Dict, List
from langchain.schema import AIMessage
from pathlib import Path
from langchain_core.callbacks import BaseCallbackHandler, StdOutCallbackHandler
from langchain_core.messages import BaseMessage

llm_log_file = ".plus_coder_llm.history"

class FileCallbackHandler(BaseCallbackHandler):
    def on_chat_model_start(
        self,
        serialized: Dict[str, Any],
        messages: List[List[BaseMessage]],
        **kwargs: Any
    ) -> Any:
        chat_log = ""
        for message in messages:
            for m in message:
                if hasattr(m, 'content'):
                    # check type str for content
                    if type(m.content) == str:
                        chat_log += "\n".join(f"{m.type}: {line}" for line in m.content.split('\n')) + "\n"
                    # check type list for content
                    elif type(m.content) == list:
                        for item in m.content:
                            if isinstance(item, dict) and 'text' in item:
                                chat_log += "\n".join(f"{m.type}: {line}" for line in item['text'].split('\n')) + "\n"
                            else:
                                chat_log += f"{m.type}: {str(item)}\n"

                    
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] LLM INPUT:\n{chat_log}\n---\n\n"
        
        with Path(llm_log_file).open("a") as f:
            f.write(log_entry)

    def on_llm_end(
        self,
        response: Any,
        **kwargs: Any,
    ) -> None: 
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        chat_log = "\n".join(f"OUTPUT: {line}" for line in response.generations[0][0].text.split('\n')) + "\n"
        log_entry = f"[{timestamp}] LLM OUTPUT:\n{chat_log}\n---\n\n"
        
        with Path(llm_log_file).open("a") as f:
            f.write(log_entry)
        
file_callback = FileCallbackHandler()

def fs_log(message: str, log_file: Path = Path(".plus_coder.log")):
    """Log a simple text message to a file with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}\n"
    
    with log_file.open("a") as f:
        f.write(log_entry)
        
def log_llm(prompt: str = None, output: AIMessage = None, log_file: Path = Path(llm_log_file)):
    """Log the prompt and/or LLM response to a file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with log_file.open("a") as f:
        if prompt:
            f.write(f"[{timestamp}] Prompt:\n{prompt}\n\n")
        
        if output:
            content = output.content
            if isinstance(content, list):
                content = "\n".join(item.get('text', str(item)) for item in content)
            f.write(f"[{timestamp}] AGENT:\n{content}\n\n")
        
        f.write("---\n\n")

