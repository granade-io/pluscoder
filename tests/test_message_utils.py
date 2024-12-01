import pytest
from langchain_core.messages import AIMessage
from langchain_core.messages import HumanMessage
from langchain_core.messages import ToolMessage

from pluscoder import fs
from pluscoder.message_utils import mask_stale_file_messages
from pluscoder.message_utils import tag_messages


@pytest.fixture
def mock_messages():
    return [
        HumanMessage(content="Message 1", tags=[]),
        HumanMessage(content="Message 2", tags=["existing_tag"]),
        HumanMessage(content="Message 3", tags=[]),
    ]


def test_tag_messages(mock_messages):
    tags_to_add = ["new_tag", "another_tag"]
    updated_messages = tag_messages(mock_messages, tags_to_add)

    assert tags_to_add[0] in updated_messages[0].tags
    assert tags_to_add[1] in updated_messages[0].tags
    assert "existing_tag" in updated_messages[1].tags  # existing tag should remain
    assert tags_to_add[0] in updated_messages[1].tags  # new tags should be added
    assert tags_to_add[1] in updated_messages[1].tags
    assert tags_to_add[0] in updated_messages[2].tags
    assert tags_to_add[1] in updated_messages[2].tags


def test_tag_messages_exclude_tagged(mock_messages):
    tags_to_add = ["new_tag", "another_tag"]
    updated_messages = tag_messages(mock_messages, tags_to_add, exclude_tagged=True)

    assert tags_to_add[0] in updated_messages[0].tags
    assert tags_to_add[1] in updated_messages[0].tags
    assert "existing_tag" in updated_messages[1].tags  # existing tagged message should not have new tags
    assert tags_to_add[0] not in updated_messages[1].tags
    assert tags_to_add[1] not in updated_messages[1].tags
    assert tags_to_add[0] in updated_messages[2].tags
    assert tags_to_add[1] in updated_messages[2].tags


@pytest.fixture(autouse=True)
def mock_get_formatted_file_content(monkeypatch):
    def mock_format(file_path: str) -> str:
        contents = {
            "file1.txt": "file1.txt content",
            "file2.txt": "file2.txt content",
            "file3.txt": "file3.txt content",
        }
        return f"\n--- start of `{file_path}`---\n{contents.get(file_path, '')}\n"

    monkeypatch.setattr(fs, "get_formatted_file_content", mock_format)


def test_basic_file_staleness():
    # Setup messages: read_files followed by file edition
    messages = [
        # First read operation
        AIMessage(
            content="Reading files...",
            tool_calls=[
                {
                    "id": "1",
                    "type": "function",
                    "name": "read_files",
                    "args": {"file_paths": ["file1.txt", "file2.txt"]},
                }
            ],
        ),
        ToolMessage(content="Content of files:\nfile1.txt content\nfile2.txt content", tool_call_id="1"),
        # File edition
        AIMessage(content="Editing file...", metadata={"file_editions": ["file1.txt"]}),
    ]

    # Process messages
    result = mask_stale_file_messages(messages)

    # Verify file1.txt is marked as stale but file2.txt keeps original content
    assert "Content is stale" in result[1].content
    assert "file1.txt" in result[1].content
    assert "file2.txt content" in result[1].content


def test_multiple_file_edits_partial_staleness():
    messages = [
        # First read operation
        AIMessage(
            content="Reading files...",
            tool_calls=[
                {
                    "id": "1",
                    "type": "function",
                    "name": "read_files",
                    "args": {"file_paths": ["file1.txt", "file2.txt"]},
                }
            ],
        ),
        ToolMessage(content="Content of files:\nfile1.txt content\nfile2.txt content", tool_call_id="1"),
        # Edit file1
        AIMessage(content="Editing file1...", metadata={"file_editions": ["file1.txt"]}),
        # Second read operation
        AIMessage(
            content="Reading more files...",
            tool_calls=[
                {
                    "id": "2",
                    "type": "function",
                    "name": "read_files",
                    "args": {"file_paths": ["file2.txt", "file3.txt"]},
                }
            ],
        ),
        ToolMessage(content="Content of files:\nfile2.txt new content\nfile3.txt content", tool_call_id="2"),
        # Edit file2
        AIMessage(content="Editing file2...", metadata={"file_editions": ["file2.txt"]}),
    ]

    # Process messages
    result = mask_stale_file_messages(messages)

    # First read: file1 should be stale, file2 should be stale
    assert "Content is stale" in result[1].content
    assert "`file1.txt`: Content is stale" in result[1].content
    assert "`file2.txt`: Content is stale" in result[1].content

    # Second read: file2 should be stale, file3 original
    assert "Content is stale" in result[4].content
    assert "`file2.txt`: Content is stale" in result[4].content
    assert "file3.txt content" in result[4].content
