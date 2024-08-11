import pytest
from unittest.mock import patch, mock_open
from pathlib import Path
from pluscoder.exceptions import AgentException
from pluscoder.fs import apply_block_update

@patch('pluscoder.fs.Path')
def test_apply_block_update_multiple_updates(mock_path):
    # Test multiple updates in the same block
    mock_file = mock_open(read_data="print('Hello')\nx = 5\n")
    mock_path.return_value.exists.return_value = True
    mock_path.return_value.read_text.side_effect = mock_file().read
    mock_path.return_value.write_text.side_effect = mock_file().write

    block_content = """
>>> FIND
print('Hello')
===
print('Hello, World!')
<<< REPLACE

>>> FIND
x = 5
===
x = 10
<<< REPLACE
"""

    apply_block_update("test.py", block_content)

    mock_path.assert_called_once_with("test.py")
    mock_path.return_value.exists.assert_called_once()
    mock_path.return_value.read_text.assert_called_once()
    mock_path.return_value.write_text.assert_called_once_with("print('Hello, World!')\nx = 10\n")
    
@patch('pluscoder.fs.Path')
def test_apply_block_update_entire_file_raise(mock_path):
    mock_file = mock_open(read_data="print('Hello')\nx = 5\n")
    mock_path.return_value.exists.return_value = True
    mock_path.return_value.read_text.side_effect = mock_file().read
    mock_path.return_value.write_text.side_effect = mock_file().write

    block_content = """
print('Hello, World!')
x = 10
"""

    error_msg = apply_block_update("test.py", block_content)
    
    assert "Couldn't replace previous content at file `test.py`" in str(error_msg)
   

@patch('pluscoder.fs.Path')
def test_apply_block_update_new_file_block(mock_path):
    # Test create a new file from proper block
    mock_file = mock_open(read_data="")
    mock_path.return_value.exists.return_value = False
    # mock_path.return_value.read_text.side_effect = mock_file().read
    mock_path.return_value.write_text.side_effect = mock_file().write
    block_content = """
>>> FIND
===
import os
from dotenv import load_dotenv
<<< REPLACE
"""
    apply_block_update("test.py", block_content)

    mock_path.assert_called_once_with("test.py")
    mock_path.return_value.exists.assert_called_once()
    mock_path.return_value.read_text.assert_not_called()
    mock_path.return_value.write_text.assert_called_once_with("import os\nfrom dotenv import load_dotenv")
    