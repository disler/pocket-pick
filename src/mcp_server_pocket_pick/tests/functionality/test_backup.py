import pytest
import tempfile
import os
import sqlite3
from pathlib import Path
from ...modules.data_types import AddCommand, BackupCommand
from ...modules.functionality.add import add
from ...modules.functionality.backup import backup

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
def temp_backup_path():
    # Create a temporary file path for backup
    fd, path = tempfile.mkstemp()
    os.close(fd)
    os.unlink(path)  # Remove the file so backup can create it
    
    # Return the path as a Path object
    yield Path(path)
    
    # Clean up the temp file after test
    if os.path.exists(path):
        os.unlink(path)

@pytest.fixture
def populated_db(temp_db_path):
    # Add a test item to the database
    command = AddCommand(
        id="test-backup-item",
        text="Test item for backup",
        tags=["test", "backup"],
        db_path=temp_db_path
    )
    
    add(command)
    return temp_db_path

def test_backup_success(populated_db, temp_backup_path):
    # Backup the database
    command = BackupCommand(
        backup_path=temp_backup_path,
        db_path=populated_db
    )
    
    result = backup(command)
    
    # Should return True indicating success
    assert result is True
    
    # Verify backup file exists
    assert temp_backup_path.exists()
    
    # Verify backup contains the same data as original
    original_db = sqlite3.connect(populated_db)
    original_cursor = original_db.execute("SELECT id, text, tags FROM POCKET_PICK")
    original_row = original_cursor.fetchone()
    original_db.close()
    
    backup_db = sqlite3.connect(temp_backup_path)
    backup_cursor = backup_db.execute("SELECT id, text, tags FROM POCKET_PICK")
    backup_row = backup_cursor.fetchone()
    backup_db.close()
    
    assert backup_row is not None
    assert backup_row[0] == original_row[0]  # ID
    assert backup_row[1] == original_row[1]  # text
    assert backup_row[2] == original_row[2]  # tags

def test_backup_nested_directory_creation(populated_db):
    # Create a backup path in a nested directory that doesn't exist
    with tempfile.TemporaryDirectory() as temp_dir:
        nested_dir = Path(temp_dir) / "nested" / "dirs"
        backup_path = nested_dir / "backup.db"
        
        # Backup the database
        command = BackupCommand(
            backup_path=backup_path,
            db_path=populated_db
        )
        
        result = backup(command)
        
        # Should return True indicating success
        assert result is True
        
        # Verify backup file exists
        assert backup_path.exists()

def test_backup_from_nonexistent_db(temp_db_path, temp_backup_path):
    # Try to backup from a nonexistent database
    # (temp_db_path fixture exists but is empty)
    command = BackupCommand(
        backup_path=temp_backup_path,
        db_path=temp_db_path
    )
    
    result = backup(command)
    
    # Should return True indicating success (empty database created and backed up)
    assert result is True
    assert temp_backup_path.exists()