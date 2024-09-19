import pytest
from pluscoder.tools import file_detection_with_confirmation, read_files, update_file, move_files

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
        {"from": str(file2), "to": str(dest_dir / "file2.txt")}
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
        {"from": str(tmp_path / "nonexistent.txt"), "to": str(dest_dir / "nonexistent.txt")}
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
