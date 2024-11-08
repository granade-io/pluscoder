from unittest.mock import patch

import pytest

from pluscoder.agents.output_handlers.action_handlers import FileActionHandler
from pluscoder.exceptions import AgentException


@pytest.fixture
def file_handler():
    return FileActionHandler()


@pytest.fixture
def sample_content():
    return "test content\nline 2\nline 3"


@patch("pluscoder.io_utils.io")
def test_file_create(mock_io, tmp_path, file_handler, sample_content):
    # Test file creation
    test_file = tmp_path / "subdir" / "test.txt"
    params = {"action": "file_create", "file": str(test_file)}

    result = file_handler.execute(params, sample_content)

    assert test_file.exists()
    assert test_file.read_text() == sample_content
    assert test_file.parent.is_dir()
    assert str(test_file) in result["updated_files"]
    mock_io.event.assert_called_once_with(f"> `{test_file}` file created.")


@patch("pluscoder.io_utils.io")
def test_file_replace(mock_io, tmp_path, file_handler, sample_content):
    # Test file content replacement
    test_file = tmp_path / "test.txt"
    test_file.write_text("original content")

    params = {"action": "file_replace", "file": str(test_file)}

    result = file_handler.execute(params, sample_content)

    assert test_file.read_text() == sample_content
    assert str(test_file) in result["updated_files"]
    mock_io.event.assert_called_once_with(f"> `{test_file}` file updated.")


@patch("pluscoder.io_utils.io")
def test_file_replace_nonexistent(mock_io, tmp_path, file_handler, sample_content):
    # Test replacing non-existent file
    test_file = tmp_path / "nonexistent.txt"

    params = {"action": "file_replace", "file": str(test_file)}

    with pytest.raises(AgentException):
        file_handler.execute(params, sample_content)


@patch("pluscoder.io_utils.io")
def test_file_diff_nonexistent(mock_io, tmp_path, file_handler):
    # Test diff on non-existent file
    test_file = tmp_path / "nonexistent.txt"

    params = {"action": "file_diff", "file": str(test_file)}

    with pytest.raises(AgentException):
        file_handler.execute(params, "some diff content")
