import base64
import os
import re
from typing import Any, Dict, List, Union
from urllib.parse import urlparse

from langchain_core.messages import AnyMessage
from langchain_core.messages import HumanMessage as LangChainHumanMessage


def get_message_content_str(message: AnyMessage) -> str:
    if type(message.content) is str:
        return message.content
    # check type list for content
    elif type(message.content) is list:
        for item in message.content:
            if isinstance(item, dict) and "text" in item:
                return item["text"]
    return str(message.content)


def convert_image_paths_to_base64(input_text: str) -> Union[str, List[Dict[str, Any]]]:
    """Convert images in the input into base64-encoded strings or keep URLs as is, converting the input text into a list of entries suitable for LLM calls"""

    def image_to_base64(path):
        try:
            if os.path.isfile(path):
                with open(path, "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
                file_extension = os.path.splitext(path)[1].lower()
                mime_type = (
                    f"image/{file_extension[1:]}"
                    if file_extension in [".png", ".jpg", ".jpeg", ".gif"]
                    else "image/png"
                )
                return f"data:{mime_type};base64,{encoded_string}"
            else:
                return None
        except Exception as e:
            print(f"Error converting image to base64: {e}")
            return None

    # Updated regex pattern to match both file paths and URLs
    pattern = r"img::(?:(?:https?://)?(?:[a-zA-Z0-9.-]+(?:\.[a-zA-Z]{2,})+)(?:/[^\s]*)?|(?:[a-zA-Z]:)?(?:[\/][a-zA-Z0-9_.-]+)+\.(?:png|jpg|jpeg|gif))"

    parts = re.split(pattern, input_text)
    matches = re.findall(pattern, input_text)

    if not matches:
        return input_text

    result = []
    for i, part in enumerate(parts):
        if part.strip():
            result.append({"type": "text", "text": part.strip()})
        if i < len(matches):
            image_path_or_url = matches[i][5:]  # Remove the 'img::' prefix
            if urlparse(image_path_or_url).scheme in ["http", "https"]:
                result.append({"type": "text", "text": matches[i]})
                result.append(
                    {"type": "image_url", "image_url": {"url": image_path_or_url}}
                )
            else:
                image_data = image_to_base64(image_path_or_url)
                if image_data:
                    result.append({"type": "text", "text": matches[i]})
                    result.append(
                        {"type": "image_url", "image_url": {"url": image_data}}
                    )
                else:
                    # Image doesn't exist or couldn't be processed, keep the original text
                    result.append({"type": "text", "text": matches[i]})

    return result if any(item["type"] == "image_url" for item in result) else input_text


class HumanMessage(LangChainHumanMessage):
    def __init__(self, content: Union[str, List[Dict[str, Any]]], **kwargs):
        if isinstance(content, str):
            content = convert_image_paths_to_base64(content)
        super().__init__(content=content, **kwargs)
