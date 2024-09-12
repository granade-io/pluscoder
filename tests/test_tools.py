import pytest
from pluscoder.tools import file_detection_with_confirmation, read_files, move_file, update_file

@pytest.fixture
def temp_file(tmp_path):
    file_path = tmp_path / "test_file.txt"
    with open(file_path, 'w') as f:
        f.write("Initial content")
    return file_path

def test_read_file(temp_file):
    content = read_files.run({"file_paths": [str(temp_file)]})
    assert "Initial content" in content
    assert str(temp_file) in content

def test_read_file_nonexistent():
    result = read_files.run({"file_paths": ["nonexistent_file.txt"]})
    assert "Error reading file" in result

def test_move_file(tmp_path):
    source = tmp_path / "source.txt"
    source.write_text("Move me")
    destination = tmp_path / "destination.txt"
    
    result = move_file.run({"source_path": str(source), "destination_path": str(destination)})
    assert "File moved successfully" in result
    assert not source.exists()
    assert destination.exists()
    assert destination.read_text() == "Move me"

def test_move_file_nonexistent(tmp_path):
    source = tmp_path / "nonexistent.txt"
    destination = tmp_path / "destination.txt"
    
    result = move_file.run({"source_path": str(source), "destination_path": str(destination)})
    assert "Error moving file" in result

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
    result = file_detection_with_confirmation.run({"file_path": str(temp_file), "content": content, "confirmation": "YES"})
    assert "File updated successfully" in result
    assert temp_file.read_text() == "New file content\nwith multiple lines"

def test_file_detection_with_confirmation_no_match(temp_file):
    content = "Some content without file blocks"
    result = file_detection_with_confirmation.run({"file_path": str(temp_file), "content": content, "confirmation": "YES"})
    assert "No file blocks detected in the content." in result

def test_file_detection_with_confirmation_not_confirmed(temp_file):
    content = f"""
{temp_file}
```python
New file content
```
"""
    result = file_detection_with_confirmation.run({"file_path": str(temp_file), "content": content, "confirmation": "n"})
    assert "Update for" in result and "was not confirmed" in result
