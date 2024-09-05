import pytest
from unittest.mock import patch, mock_open
from pluscoder.repomap import generate_tree
from pluscoder.io_utils import io

@pytest.fixture
def mock_file_content():
    return b"""
class ExampleClass:
    \"\"\"This is an example class.\"\"\"

    def example_method(self):
        \"\"\"This is an example method.\"\"\"
        pass
"""

@patch('pluscoder.repomap.os.walk')
@patch('pluscoder.repomap.open', new_callable=mock_open)
@patch('pluscoder.repomap.should_include_file')
def test_generate_tree(mock_should_include, mock_file_open, mock_walk, mock_file_content):
    # Mock os.walk to return one Python file
    mock_walk.return_value = [
        ('/repo_root', [], ['example.py'])
    ]

    # Mock should_include_file to return True for our file
    mock_should_include.return_value = True

    # Mock file open to return our example content
    mock_file_open.return_value.read.return_value = mock_file_content

    # Call generate_tree
    result = generate_tree(
        repo_path='/repo_root',
        include_patterns=['*.py'],
        exclude_patterns=[],
        level=2,
        tracked_files=['example.py'],
        io=io
    )

    # Define expected output
    expected_output = """
example.py
==========
class ExampleClass:
    This is an example class.
    def example_method(self):
        This is an example method.
==========
"""

    # Assert the result matches the expected output
    assert result.strip() == expected_output.strip()

    # Verify that the mocks were called correctly
    mock_walk.assert_called_once_with('/repo_root')
    mock_should_include.assert_called_once_with('/repo_root/example.py', ['example.py'], ['*.py'], [], '/repo_root')
    mock_file_open.assert_called_once_with('/repo_root/example.py', 'rb')