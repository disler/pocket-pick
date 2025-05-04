import pytest
import tempfile
import os
from pathlib import Path
from ...modules.data_types import AddCommand, ListTagsCommand
from ...modules.functionality.add import add
from ...modules.functionality.list_tags import list_tags

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

def test_list_tags_all(populated_db):
    # List all tags
    command = ListTagsCommand(
        db_path=populated_db
    )
    
    results = list_tags(command)
    
    # Verify all expected tags are present
    tags = [result["tag"] for result in results]
    expected_tags = [
        "programming",  # Count: 4
        "fun",          # Count: 2
        "python",       # Count: 1
        "sql",          # Count: 1
        "database",     # Count: 1
        "testing",      # Count: 1
        "code",         # Count: 1
        "regex",        # Count: 1
        "advanced",     # Count: 1
        "learning",     # Count: 1
        "technology"    # Count: 1
    ]
    
    for expected in expected_tags:
        assert expected in tags
    
    # Verify the most common tag is first (sorted by count)
    assert results[0]["tag"] == "programming"
    assert results[0]["count"] == 4
    
    # Verify second most common tag
    assert results[1]["tag"] == "fun"
    assert results[1]["count"] == 2

def test_list_tags_limit(populated_db):
    # List tags with limit
    command = ListTagsCommand(
        limit=3,
        db_path=populated_db
    )
    
    results = list_tags(command)
    
    # Should only return 3 tags
    assert len(results) == 3
    
    # Verify the top 3 tags in order by count
    # (with ties broken alphabetically)
    assert results[0]["tag"] == "programming"
    assert results[1]["tag"] == "fun"
    
    # The third item should be one of the single-count tags
    assert results[2]["count"] == 1

def test_list_tags_empty_db(temp_db_path):
    # List tags in empty database
    command = ListTagsCommand(
        db_path=temp_db_path
    )
    
    results = list_tags(command)
    
    # Should return empty list
    assert len(results) == 0