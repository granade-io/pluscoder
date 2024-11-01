from unittest.mock import mock_open
from unittest.mock import patch

import pytest

from pluscoder.config.utils import append_custom_agent_to_config
from pluscoder.config.utils import create_custom_agents_section
from pluscoder.config.utils import find_custom_agents_section
from pluscoder.config.utils import find_insertion_point
from pluscoder.config.utils import format_agent_dict
from pluscoder.config.utils import read_yaml_file


@pytest.fixture
def sample_yaml_content():
    return [
        "# Some comments\n",
        "model: gpt-4\n",
        "\n",
        "custom_agents:\n",
        "  - name: test_agent\n",
        "    description: test description\n",
        "    enabled: true\n",
        "\n",
        "other_key: value\n",
    ]


@pytest.fixture
def empty_yaml_content():
    return ["# Some comments\n", "model: gpt-4\n", "custom_agents: []\n", "other_key: value\n"]


def test_read_yaml_file():
    content = "key: value\n"
    with patch("builtins.open", mock_open(read_data=content)):
        result = read_yaml_file("dummy.yml")
        assert result == ["key: value\n"]


def test_find_custom_agents_section(sample_yaml_content, empty_yaml_content):
    assert find_custom_agents_section(sample_yaml_content) == 3
    assert find_custom_agents_section(empty_yaml_content) == 2
    assert find_custom_agents_section(["no_section: true"]) == -1


def test_format_agent_dict():
    agent = {
        "name": "test_agent",
        "description": "test description",
        "enabled": True,
        "multiline": "line1\nline2\nline3",
    }

    expected = [
        "  - name: test_agent\n",
        '    description: "test description"\n',
        "    enabled: true\n",
        '    multiline: "|\n      line1\n      line2\n      line3"\n',
    ]

    result = format_agent_dict(agent)
    assert result == expected


def test_find_insertion_point(sample_yaml_content, empty_yaml_content):
    # Test with existing agents
    assert find_insertion_point(sample_yaml_content, 3) == 7

    # Test with empty agents section
    assert find_insertion_point(empty_yaml_content, 2) == 3


def test_create_custom_agents_section():
    lines = ["# Comments\n", "key: value\n", "other: data\n"]

    expected = ["# Comments\n", "\n", "custom_agents:\n", "key: value\n", "other: data\n"]

    result, index = create_custom_agents_section(lines)
    assert result == expected
    assert index == 2


@patch("pluscoder.config.utils.read_yaml_file")
@patch("builtins.open", new_callable=mock_open)
def test_append_custom_agent_to_config(mock_file, mock_read, sample_yaml_content):
    mock_read.return_value = sample_yaml_content

    new_agent = {"name": "new_agent", "description": "new description", "enabled": True}

    append_custom_agent_to_config(new_agent)

    # Verify file was written
    mock_file.assert_called_once_with(".pluscoder-config.yml", "w")
    handle = mock_file()

    # Capture writelines calls
    calls = handle.writelines.call_args_list
    if not calls:
        calls = [call[0] for call in handle.write.call_args_list]

    # Convert all writes to a single string for easier assertion
    written_content = "".join(str(arg) for call in calls for arg in call[0])

    # Verify content
    assert "new_agent" in written_content
    assert "new description" in written_content
    assert "enabled: true" in written_content


@patch("pluscoder.config.utils.read_yaml_file")
@patch("builtins.open", new_callable=mock_open)
def test_append_custom_agent_to_empty_config(mock_file, mock_read, empty_yaml_content):
    mock_read.return_value = empty_yaml_content

    new_agent = {"name": "new_agent", "description": "new description", "enabled": True}

    append_custom_agent_to_config(new_agent)

    # Verify file was written
    mock_file.assert_called_once_with(".pluscoder-config.yml", "w")
    handle = mock_file()

    # Capture writelines calls
    calls = handle.writelines.call_args_list
    if not calls:
        calls = [call[0] for call in handle.write.call_args_list]

    # Convert all writes to a single string for easier assertion
    written_content = "".join(str(arg) for call in calls for arg in call[0])

    # Verify content
    assert "custom_agents: []" not in written_content
    assert "new_agent" in written_content
    assert "new description" in written_content
    assert "enabled: true" in written_content
