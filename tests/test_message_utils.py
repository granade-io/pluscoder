import pytest
from langchain_core.messages import HumanMessage

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
