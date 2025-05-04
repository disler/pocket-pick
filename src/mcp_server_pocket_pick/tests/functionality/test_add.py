import pytest
import tempfile
import os
from pathlib import Path
import json
import sqlite3
from ...modules.data_types import AddCommand, PocketItem
from ...modules.functionality.add import add

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

def test_add_simple(temp_db_path):
    # Create a command to add a simple item
    command = AddCommand(
        id="test-item-1",
        text="This is a test item",
        tags=["test", "example"],
        db_path=temp_db_path
    )
    
    # Add the item
    result = add(command)
    
    # Verify result is a PocketItem
    assert isinstance(result, PocketItem)
    assert result.text == "This is a test item"
    assert result.tags == ["test", "example"]
    assert result.id == "test-item-1"
    
    # Verify item was added to the database
    db = sqlite3.connect(temp_db_path)
    cursor = db.execute("SELECT id, text, tags FROM POCKET_PICK")
    row = cursor.fetchone()
    
    assert row is not None
    assert row[0] == "test-item-1"
    assert row[1] == "This is a test item"
    
    # Verify tags were stored as JSON
    stored_tags = json.loads(row[2])
    assert stored_tags == ["test", "example"]
    
    # Verify no more rows exist
    assert cursor.fetchone() is None
    
    db.close()

def test_add_with_tag_normalization(temp_db_path):
    # Create a command with tags that need normalization
    command = AddCommand(
        id="test-normalize",
        text="Item with tags to normalize",
        tags=["TAG", "with space", "under_score"],
        db_path=temp_db_path
    )
    
    # Add the item
    result = add(command)
    
    # Verify tags were normalized
    assert result.tags == ["tag", "with-space", "under-score"]
    assert result.id == "test-normalize"
    
    # Verify in database
    db = sqlite3.connect(temp_db_path)
    cursor = db.execute("SELECT id, tags FROM POCKET_PICK")
    row = cursor.fetchone()
    
    assert row[0] == "test-normalize"
    stored_tags = json.loads(row[1])
    assert stored_tags == ["tag", "with-space", "under-score"]
    
    db.close()

def test_add_duplicate_id(temp_db_path):
    # Create first item
    command1 = AddCommand(
        id="duplicate-id",
        text="First item with this ID",
        tags=["test"],
        db_path=temp_db_path
    )
    
    # Add the first item successfully
    result = add(command1)
    assert result.id == "duplicate-id"
    
    # Create second item with same ID
    command2 = AddCommand(
        id="duplicate-id",
        text="Second item with same ID",
        tags=["test"],
        db_path=temp_db_path
    )
    
    # Attempt to add with the same ID should raise IntegrityError
    with pytest.raises(sqlite3.IntegrityError):
        add(command2)
        
    # Verify only the first item exists in the database
    db = sqlite3.connect(temp_db_path)
    cursor = db.execute("SELECT COUNT(*) FROM POCKET_PICK")
    count = cursor.fetchone()[0]
    assert count == 1
    
    cursor = db.execute("SELECT text FROM POCKET_PICK WHERE id = ?", ("duplicate-id",))
    text = cursor.fetchone()[0]
    assert text == "First item with this ID"
    
    db.close()