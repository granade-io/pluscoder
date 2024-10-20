from unittest.mock import Mock
from unittest.mock import patch

import pytest
import requests

from pluscoder.tools import convert_to_raw_url
from pluscoder.tools import file_detection_with_confirmation
from pluscoder.tools import move_files
from pluscoder.tools import read_file_from_url
from pluscoder.tools import read_files
from pluscoder.tools import update_file


@pytest.fixture
def temp_file(tmp_path):
    file_path = tmp_path / "test_file.txt"
    with open(file_path, "w") as f:
        f.write("Initial content")
    return file_path


def test_read_file(temp_file):
    content = read_files.run({"file_paths": [str(temp_file)]})
    assert "Initial content" in content
    assert str(temp_file) in content


def test_read_file_nonexistent():
    result = read_files.run({"file_paths": ["nonexistent_file.txt"]})
    assert "Error reading file" in result


def test_update_file(temp_file):
    result = update_file.run({"file_path": str(temp_file), "content": "New content"})
    assert "File updated successfully" in result
    assert temp_file.read_text() == "New content"


def test_update_file_nonexistent(tmp_path):
    nonexistent = tmp_path / "nonexistent.txt"
    result = update_file.run({"file_path": str(nonexistent), "content": "New content"})
    assert "File updated successfully" in result
    assert nonexistent.read_text() == "New content"


def test_file_detection_with_confirmation(temp_file):
    content = f"""
{temp_file}
```python
New file content
with multiple lines
```
"""
    result = file_detection_with_confirmation.run(
        {"file_path": str(temp_file), "content": content, "confirmation": "YES"}
    )
    assert "File updated successfully" in result
    assert temp_file.read_text() == "New file content\nwith multiple lines"


def test_file_detection_with_confirmation_no_match(temp_file):
    content = "Some content without file blocks"
    result = file_detection_with_confirmation.run(
        {"file_path": str(temp_file), "content": content, "confirmation": "YES"}
    )
    assert "No file blocks detected in the content." in result


def test_file_detection_with_confirmation_not_confirmed(temp_file):
    content = f"""
{temp_file}
```python
New file content
```
"""
    result = file_detection_with_confirmation.run(
        {"file_path": str(temp_file), "content": content, "confirmation": "n"}
    )
    assert "Update for" in result
    assert "was not confirmed" in result


def test_move_files_all_successful(tmp_path):
    # Create two temporary files
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    file1.write_text("Content of file1")
    file2.write_text("Content of file2")

    # Create destination directory
    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()

    # Define file paths for moving
    file_paths = [
        {"from": str(file1), "to": str(dest_dir / "file1.txt")},
        {"from": str(file2), "to": str(dest_dir / "file2.txt")},
    ]

    # Run the move_files tool
    result = move_files.run({"file_paths": file_paths})

    # Assert the results
    assert "Moved 2 file(s) successfully. 0 file(s) failed to move." in result
    assert "Successfully moved" in result
    assert (dest_dir / "file1.txt").exists()
    assert (dest_dir / "file2.txt").exists()
    assert not file1.exists()
    assert not file2.exists()


def test_move_files_one_failed(tmp_path):
    # Create one temporary file
    file1 = tmp_path / "file1.txt"
    file1.write_text("Content of file1")

    # Create destination directory
    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()

    # Define file paths for moving (including a non-existent file)
    file_paths = [
        {"from": str(file1), "to": str(dest_dir / "file1.txt")},
        {
            "from": str(tmp_path / "nonexistent.txt"),
            "to": str(dest_dir / "nonexistent.txt"),
        },
    ]

    # Run the move_files tool
    result = move_files.run({"file_paths": file_paths})

    # Assert the results
    assert "Moved 1 file(s) successfully. 1 file(s) failed to move." in result
    assert "Successfully moved" in result
    assert "Failed to move" in result
    assert (dest_dir / "file1.txt").exists()
    assert not file1.exists()
    assert not (dest_dir / "nonexistent.txt").exists()


def test_convert_to_raw_url():
    # Test GitHub repository URL
    github_url = "https://github.com/user/repo/blob/main/file.txt"
    expected_github_raw = "https://raw.githubusercontent.com/user/repo/main/file.txt"
    assert convert_to_raw_url(github_url) == expected_github_raw

    # Test GitLab repository URL
    gitlab_url = "https://gitlab.com/user/repo/-/blob/main/file.txt"
    expected_gitlab_raw = "https://gitlab.com/user/repo/-/raw/main/file.txt"
    assert convert_to_raw_url(gitlab_url) == expected_gitlab_raw

    # Test Bitbucket repository URL
    # bitbucket_url = "https://bitbucket.org/user/repo/src/main/file.txt"
    # expected_bitbucket_raw = "https://bitbucket.org/user/repo/raw/main/file.txt"
    # assert convert_to_raw_url(bitbucket_url) == expected_bitbucket_raw

    # # Test Azure DevOps repository URL
    # azure_url = "https://dev.azure.com/org/project/_git/repo/blob/main/file.txt"
    # expected_azure_raw = "https://dev.azure.com/org/project/_apis/git/repositories/repo/items?path=/main/file.txt&api-version=6.0"
    # assert convert_to_raw_url(azure_url) == expected_azure_raw

    # Test non-repository URL
    other_url = "https://example.com/file.txt"
    assert convert_to_raw_url(other_url) == other_url


@patch("requests.get")
def test_read_file_from_url(mock_get):
    # Mock the requests.get method
    mock_response = Mock()
    mock_response.text = "File content"
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    # Test with a regular URL
    result = read_file_from_url.run({"url": "https://example.com/file.txt"})
    assert "File content" in result
    mock_get.assert_called_with("https://example.com/file.txt")

    # Test with a GitHub repository URL
    github_url = "https://github.com/user/repo/blob/main/file.txt"
    result = read_file_from_url.run({"url": github_url})
    assert "File content" in result
    mock_get.assert_called_with("https://raw.githubusercontent.com/user/repo/main/file.txt")


@patch("requests.get")
def test_read_file_from_url_error(mock_get):
    # Mock the requests.get method to raise an exception
    mock_get.side_effect = requests.RequestException("Error")

    result = read_file_from_url.run({"url": "https://example.com/file.txt"})
    assert "Error downloading file" in result
