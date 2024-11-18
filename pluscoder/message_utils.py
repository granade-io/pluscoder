import base64
import os
import re
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Sequence
from typing import Union
from urllib.parse import urlparse

from langchain_core.messages import AnyMessage
from langchain_core.messages import BaseMessage
from langchain_core.messages import HumanMessage as LangChainHumanMessage
from langchain_core.messages import RemoveMessage
from langchain_core.messages import convert_to_messages


def get_message_content_str(message: AnyMessage) -> str:
    if type(message.content) is str:
        return message.content
    # check type list for content
    if type(message.content) is list:
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
                result.append({"type": "image_url", "image_url": {"url": image_path_or_url}})
            else:
                image_data = image_to_base64(image_path_or_url)
                if image_data:
                    result.append({"type": "text", "text": matches[i]})
                    result.append({"type": "image_url", "image_url": {"url": image_data}})
                else:
                    # Image doesn't exist or couldn't be processed, keep the original text
                    result.append({"type": "text", "text": matches[i]})

    return result if any(item["type"] == "image_url" for item in result) else input_text


class HumanMessage(LangChainHumanMessage):
    def __init__(self, content: Union[str, List[Dict[str, Any]]], **kwargs):
        if isinstance(content, str):
            content = convert_image_paths_to_base64(content)
        super().__init__(content=content, **kwargs)


def filter_messages(
    messages: List[BaseMessage],
    *,
    include_types: Optional[Sequence[str]] = None,
    include_tags: Optional[Sequence[str]] = None,
    include_no_tags: Optional[bool] = None,
) -> List[BaseMessage]:
    messages = convert_to_messages(messages)
    filtered: List[BaseMessage] = []
    for msg in messages:
        if include_tags and hasattr(msg, "tags") and any(tag in include_tags for tag in msg.tags):
            filtered.append(msg)

        if include_no_tags and (not hasattr(msg, "tags") or not msg.tags):
            filtered.append(msg)

        if include_types and msg.type in include_types:
            filtered.append(msg)

    return filtered


def delete_messages(
    messages: List[BaseMessage],
    include_tags: Optional[Sequence[str]] = None,
    include_ids: Optional[Sequence[str]] = None,
) -> List[BaseMessage]:
    messages = convert_to_messages(messages)
    messages_to_delete: List[BaseMessage] = []
    for msg in messages:
        if include_tags and hasattr(msg, "tags") and any(tag in include_tags for tag in msg.tags):
            messages_to_delete.append(RemoveMessage(id=msg.id))
        if include_ids and msg.id in include_ids:
            messages_to_delete.append(RemoveMessage(id=msg.id))

    return messages_to_delete


def tag_messages(messages: List[BaseMessage], tags: List[str], exclude_tagged: bool = False) -> List[BaseMessage]:
    """
    Add tags to all messages in the list. Optionally exclude messages that are already tagged.

    :param messages: List of messages to tag.
    :param tags: List of tags to add.
    :param exclude_tagged: If True, do not add tags to messages that already have tags.
    :return: List of messages with added tags.
    """
    tagged_messages = []
    for msg in messages:
        if exclude_tagged and hasattr(msg, "tags") and msg.tags:
            tagged_messages.append(msg)
        elif hasattr(msg, "tags"):
            msg.tags.extend(t for t in tags if t not in msg.tags)
            tagged_messages.append(msg)
        else:
            msg.tags = [t for t in tags]
            tagged_messages.append(msg)
    return tagged_messages
