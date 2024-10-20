from datetime import datetime
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from langchain.schema import AIMessage
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import BaseMessage

# TODO: Move this to config
llm_log_file = ".pluscoder/llm_history.txt"


class FileCallbackHandler(BaseCallbackHandler):
    def on_chat_model_start(
        self,
        serialized: Dict[str, Any],
        messages: List[List[BaseMessage]],
        **kwargs: Any,
    ) -> Any:
        chat_log = ""
        for message in messages:
            for m in message:
                if not hasattr(m, "content"):
                    continue
                # check type str for content
                # if isinstance(m.content, str):
                if type(m.content) is str:
                    chat_log += "\n".join(f"{m.type}: {line}" for line in m.content.split("\n")) + "\n"
                # check type list for content
                # elif isinstance(m.content, list):
                elif type(m.content) is list:
                    for item in m.content:
                        if isinstance(item, dict) and "text" in item:
                            chat_log += "\n".join(f"{m.type}: {line}" for line in item["text"].split("\n")) + "\n"
                        else:
                            chat_log += f"{m.type}: {item!s}\n"

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
        chat_log = "\n".join(f"OUTPUT: {line}" for line in response.generations[0][0].text.split("\n")) + "\n"
        log_entry = f"[{timestamp}] LLM OUTPUT:\n{chat_log}\n---\n\n"

        with Path(llm_log_file).open("a") as f:
            f.write(log_entry)


file_callback = FileCallbackHandler()


def log_llm(
    prompt: Optional[str] = None,
    output: AIMessage = None,
    log_file: Path = Path(llm_log_file),
):
    """Log the prompt and/or LLM response to a file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with log_file.open("a") as f:
        if prompt:
            f.write(f"[{timestamp}] Prompt:\n{prompt}\n\n")

        if output:
            content = output.content
            if isinstance(content, list):
                content = "\n".join(item.get("text", str(item)) for item in content)
            f.write(f"[{timestamp}] AGENT:\n{content}\n\n")

        f.write("---\n\n")
