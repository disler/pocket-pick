import pytest
import tempfile
import os
from pathlib import Path
import json
import sqlite3
from ...modules.data_types import AddCommand, ToFileByIdCommand, PocketItem
from ...modules.functionality.add import add
from ...modules.functionality.to_file_by_id import to_file_by_id

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
def sample_item(temp_db_path):
    # Add a sample item to the database and return it
    command = AddCommand(
        id="test-file-output",
        text="This is sample content for testing to_file_by_id function",
        tags=["test", "sample"],
        db_path=temp_db_path
    )
    
    return add(command)

def test_to_file_by_id_successful(temp_db_path, sample_item):
    # Create a temporary output file path
    fd, output_path = tempfile.mkstemp()
    os.close(fd)
    os.unlink(output_path)  # Remove the file so we can test creation
    
    try:
        # Create command to write content to file
        command = ToFileByIdCommand(
            id=sample_item.id,
            output_file_path_abs=output_path,
            db_path=temp_db_path
        )
        
        # Write content to file
        result = to_file_by_id(command)
        
        # Verify result is True
        assert result is True
        
        # Verify file was created with correct content
        assert os.path.exists(output_path)
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert content == sample_item.text
    finally:
        # Clean up the temp file
        if os.path.exists(output_path):
            os.unlink(output_path)

def test_to_file_by_id_nonexistent_id(temp_db_path):
    # Create a temporary output file path
    fd, output_path = tempfile.mkstemp()
    os.close(fd)
    os.unlink(output_path)  # Remove the file so we can test creation
    
    try:
        # Create command with non-existent ID
        command = ToFileByIdCommand(
            id="nonexistent-id",
            output_file_path_abs=output_path,
            db_path=temp_db_path
        )
        
        # Attempt to write content to file
        result = to_file_by_id(command)
        
        # Verify result is False
        assert result is False
        
        # Verify file was not created
        assert not os.path.exists(output_path)
    finally:
        # Clean up the temp file if it was created
        if os.path.exists(output_path):
            os.unlink(output_path)

def test_to_file_by_id_creates_directories(temp_db_path, sample_item):
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()
    try:
        # Create a path with nested directories that don't exist
        output_path = os.path.join(temp_dir, "nested", "dirs", "output.txt")
        
        # Create command to write content to file
        command = ToFileByIdCommand(
            id=sample_item.id,
            output_file_path_abs=output_path,
            db_path=temp_db_path
        )
        
        # Write content to file
        result = to_file_by_id(command)
        
        # Verify result is True
        assert result is True
        
        # Verify file was created with correct content
        assert os.path.exists(output_path)
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert content == sample_item.text
    finally:
        # Clean up the temp dir
        import shutil
        shutil.rmtree(temp_dir)

def test_to_file_by_id_handles_errors(temp_db_path, sample_item, monkeypatch):
    # Mock the open function to raise a PermissionError
    def mock_open_with_permission_error(*args, **kwargs):
        raise PermissionError("Permission denied")
    
    # Create a temporary output file path
    fd, output_path = tempfile.mkstemp()
    os.close(fd)
    os.unlink(output_path)
    
    try:
        # Create command to write content to file
        command = ToFileByIdCommand(
            id=sample_item.id,
            output_file_path_abs=output_path,
            db_path=temp_db_path
        )
        
        # Monkeypatch the built-in open function
        monkeypatch.setattr("builtins.open", mock_open_with_permission_error)
        
        # Attempt to write content to file
        result = to_file_by_id(command)
        
        # Verify result is False because of permission error
        assert result is False
    finally:
        # Clean up the temp file if it was created
        if os.path.exists(output_path):
            os.unlink(output_path)