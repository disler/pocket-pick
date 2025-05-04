import pytest
import tempfile
import os
from pathlib import Path
from ...modules.data_types import AddCommand, ListCommand
from ...modules.functionality.add import add
from ...modules.functionality.list import list_items

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
def populated_db(temp_db_path):
    # Create sample items
    items = [
        {"id": "python-1", "text": "Python programming is fun", "tags": ["python", "programming", "fun"]},
        {"id": "sql-1", "text": "SQL databases are powerful", "tags": ["sql", "database", "programming"]},
        {"id": "testing-1", "text": "Testing code is important", "tags": ["testing", "code", "programming"]},
        {"id": "regex-1", "text": "Regular expressions can be complex", "tags": ["regex", "programming", "advanced"]},
        {"id": "learning-1", "text": "Learning new technologies is exciting", "tags": ["learning", "technology", "fun"]}
    ]
    
    # Add items to the database
    for item in items:
        command = AddCommand(
            id=item["id"],
            text=item["text"],
            tags=item["tags"],
            db_path=temp_db_path
        )
        add(command)
    
    return temp_db_path

def test_list_all(populated_db):
    # List all items
    command = ListCommand(
        limit=10,
        db_path=populated_db
    )
    
    results = list_items(command)
    
    # Should return all 5 items
    assert len(results) == 5
    
    # Check that all expected texts are present
    texts = [result.text for result in results]
    expected_texts = [
        "Python programming is fun",
        "SQL databases are powerful",
        "Testing code is important",
        "Regular expressions can be complex",
        "Learning new technologies is exciting"
    ]
    
    for expected in expected_texts:
        assert expected in texts

def test_list_with_tags(populated_db):
    # List items with specific tag
    command = ListCommand(
        tags=["programming"],
        limit=10,
        db_path=populated_db
    )
    
    results = list_items(command)
    
    # Should return items with the "programming" tag (4 items)
    assert len(results) == 4
    
    # Verify the correct items are returned
    texts = [result.text for result in results]
    expected_texts = [
        "Python programming is fun",
        "SQL databases are powerful",
        "Testing code is important",
        "Regular expressions can be complex"
    ]
    
    for expected in expected_texts:
        assert expected in texts

def test_list_with_multiple_tags(populated_db):
    # List items with multiple tags
    command = ListCommand(
        tags=["programming", "fun"],
        limit=10,
        db_path=populated_db
    )
    
    results = list_items(command)
    
    # Should return items with both "programming" and "fun" tags (1 item)
    assert len(results) == 1
    assert results[0].text == "Python programming is fun"

def test_list_limit(populated_db):
    # List with limit
    command = ListCommand(
        limit=2,
        db_path=populated_db
    )
    
    results = list_items(command)
    
    # Should only return 2 items
    assert len(results) == 2