import pytest
import tempfile
import os
from pathlib import Path
import sqlite3
from ...modules.data_types import AddCommand, RemoveCommand, GetCommand
from ...modules.functionality.add import add
from ...modules.functionality.remove import remove
from ...modules.functionality.get import get

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
def item_id(temp_db_path):
    # Add a test item and return its ID
    command = AddCommand(
        id="test-get-remove",
        text="Test item for get and remove",
        tags=["test", "example"],
        db_path=temp_db_path
    )
    
    result = add(command)
    return result.id, temp_db_path

def test_get_item(item_id):
    id, db_path = item_id
    
    # Get the item by ID
    command = GetCommand(
        id=id,
        db_path=db_path
    )
    
    result = get(command)
    
    # Verify item properties
    assert result is not None
    assert result.id == id
    assert result.text == "Test item for get and remove"
    assert set(result.tags) == set(["test", "example"])

def test_get_nonexistent_item(temp_db_path):
    # Try to get a nonexistent item
    command = GetCommand(
        id="nonexistent-id",
        db_path=temp_db_path
    )
    
    result = get(command)
    
    # Should return None
    assert result is None

def test_remove_item(item_id):
    id, db_path = item_id
    
    # Remove the item
    command = RemoveCommand(
        id=id,
        db_path=db_path
    )
    
    result = remove(command)
    
    # Should return True indicating success
    assert result is True
    
    # Verify item is no longer in the database
    db = sqlite3.connect(db_path)
    cursor = db.execute("SELECT COUNT(*) FROM POCKET_PICK WHERE id = ?", (id,))
    count = cursor.fetchone()[0]
    db.close()
    
    assert count == 0
    
    # Trying to get the removed item should return None
    get_command = GetCommand(
        id=id,
        db_path=db_path
    )
    get_result = get(get_command)
    assert get_result is None

def test_remove_nonexistent_item(temp_db_path):
    # Try to remove a nonexistent item
    command = RemoveCommand(
        id="nonexistent-id",
        db_path=temp_db_path
    )
    
    result = remove(command)
    
    # Should return False indicating failure
    assert result is False