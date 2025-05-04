import pytest
import tempfile
import os
from pathlib import Path
import json
import sqlite3
from ...modules.data_types import AddFileCommand, PocketItem
from ...modules.functionality.add_file import add_file

@pytest.fixture
def temp_db_path():
    # Create a temporary file path
    fd, path = tempfile.mkstemp()
    os.close(fd)
    
    # Return the path as a Path object
    yield Path(path)
    
    # Clean up the temp file after test
    if os.path.exists(path):
        os.unlink(path)

@pytest.fixture
def temp_file_with_content():
    # Create a temporary file with content
    fd, path = tempfile.mkstemp()
    with os.fdopen(fd, 'w') as file:
        file.write("This is test content from a file")
    
    # Return the path as a string
    yield path
    
    # Clean up the temp file after test
    if os.path.exists(path):
        os.unlink(path)

def test_add_file_simple(temp_db_path, temp_file_with_content):
    # Create a command to add a file content
    command = AddFileCommand(
        id="test-file-1",
        file_path=temp_file_with_content,
        tags=["test", "file"],
        db_path=temp_db_path
    )
    
    # Add the item
    result = add_file(command)
    
    # Verify result is a PocketItem
    assert isinstance(result, PocketItem)
    assert result.text == "This is test content from a file"
    assert result.tags == ["test", "file"]
    assert result.id == "test-file-1"
    
    # Verify item was added to the database
    db = sqlite3.connect(temp_db_path)
    cursor = db.execute("SELECT id, text, tags FROM POCKET_PICK")
    row = cursor.fetchone()
    
    assert row is not None
    assert row[0] == "test-file-1"
    assert row[1] == "This is test content from a file"
    
    # Verify tags were stored as JSON
    stored_tags = json.loads(row[2])
    assert stored_tags == ["test", "file"]
    
    # Verify no more rows exist
    assert cursor.fetchone() is None
    
    db.close()

def test_add_file_with_tag_normalization(temp_db_path, temp_file_with_content):
    # Create a command with tags that need normalization
    command = AddFileCommand(
        id="test-file-normalize",
        file_path=temp_file_with_content,
        tags=["FILE", "with space", "under_score"],
        db_path=temp_db_path
    )
    
    # Add the item
    result = add_file(command)
    
    # Verify tags were normalized
    assert result.tags == ["file", "with-space", "under-score"]
    assert result.id == "test-file-normalize"
    
    # Verify in database
    db = sqlite3.connect(temp_db_path)
    cursor = db.execute("SELECT id, tags FROM POCKET_PICK")
    row = cursor.fetchone()
    
    assert row[0] == "test-file-normalize"
    stored_tags = json.loads(row[1])
    assert stored_tags == ["file", "with-space", "under-score"]
    
    db.close()

def test_add_file_nonexistent(temp_db_path):
    # Create a command with a nonexistent file
    command = AddFileCommand(
        id="test-nonexistent",
        file_path="/nonexistent/file/path.txt",
        tags=["test"],
        db_path=temp_db_path
    )
    
    # Expect FileNotFoundError when adding
    with pytest.raises(FileNotFoundError):
        add_file(command)
        
def test_add_file_duplicate_id(temp_db_path, temp_file_with_content):
    # Create first file item
    command1 = AddFileCommand(
        id="duplicate-file-id",
        file_path=temp_file_with_content,
        tags=["test"],
        db_path=temp_db_path
    )
    
    # Add the first item successfully
    result = add_file(command1)
    assert result.id == "duplicate-file-id"
    
    # Create second item with same ID
    command2 = AddFileCommand(
        id="duplicate-file-id",
        file_path=temp_file_with_content,
        tags=["different"],
        db_path=temp_db_path
    )
    
    # Attempt to add with the same ID should raise IntegrityError
    with pytest.raises(sqlite3.IntegrityError):
        add_file(command2)
        
    # Verify only the first item exists in the database
    db = sqlite3.connect(temp_db_path)
    cursor = db.execute("SELECT COUNT(*) FROM POCKET_PICK")
    count = cursor.fetchone()[0]
    assert count == 1
    
    cursor = db.execute("SELECT tags FROM POCKET_PICK WHERE id = ?", ("duplicate-file-id",))
    tags = json.loads(cursor.fetchone()[0])
    assert tags == ["test"]  # Original tags are preserved
    
    db.close()