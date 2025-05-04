import pytest
import tempfile
import os
from pathlib import Path
import json
import sqlite3
from datetime import datetime
from ...modules.data_types import AddCommand, FindCommand, PocketItem
from ...modules.functionality.add import add
from ...modules.functionality.find import find
from ...modules.init_db import init_db

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

def test_find_substr(populated_db):
    # Search for "programming" substring
    command = FindCommand(
        text="programming",
        mode="substr",
        limit=10,
        db_path=populated_db
    )
    
    results = find(command)
    
    # Should match "Python programming is fun"
    assert len(results) == 1
    assert "Python programming is fun" in [r.text for r in results]

def test_find_fts(populated_db):
    # Test basic FTS search with a single word
    command = FindCommand(
        text="SQL",
        mode="fts",
        limit=10,
        db_path=populated_db
    )
    
    results = find(command)
    
    # Should match "SQL databases are powerful"
    assert len(results) == 1
    assert "SQL databases are powerful" in [r.text for r in results]
    
def test_find_fts_phrase(populated_db):
    # Test FTS with a phrase (multiple words in exact order)
    command = FindCommand(
        text="Regular expressions",
        mode="fts",
        limit=10,
        db_path=populated_db
    )
    
    results = find(command)
    
    # Should match "Regular expressions can be complex"
    assert len(results) == 1
    assert "Regular expressions can be complex" in [r.text for r in results]
    
def test_find_fts_multi_term(populated_db):
    # Test FTS with multiple terms (not necessarily in order)
    command = FindCommand(
        text="programming fun",
        mode="fts",
        limit=10,
        db_path=populated_db
    )
    
    results = find(command)
    
    # Should match items containing both "programming" and "fun"
    assert len(results) > 0
    
    # Check that all results contain both "programming" AND "fun"
    for result in results:
        assert "programming" in result.text.lower() and "fun" in result.text.lower()
        
def test_find_fts_with_tags(populated_db):
    # Test FTS with tag filtering
    command = FindCommand(
        text="programming",
        mode="fts",
        tags=["fun"],  # Only items tagged with "fun"
        limit=10,
        db_path=populated_db
    )
    
    results = find(command)
    
    # Should match items containing "programming" AND tagged with "fun"
    assert len(results) == 1
    assert "Python programming is fun" in [r.text for r in results]

def test_find_fts_exact_phrase(populated_db):
    """
    Test exact phrase matching functionality. 
    
    This test is simplified to focus on the core functionality without relying
    on specific matching patterns that might be hard to reproduce with FTS5.
    """
    # First make sure we have a known item with a specific phrase
    command = AddCommand(
        id="test-exact-phrase-1",
        text="This contains programming fun as a phrase",
        tags=["test", "phrase"],
        db_path=populated_db
    )
    result1 = add(command)
    
    # Add an item with same words but in reverse order
    command = AddCommand(
        id="test-exact-phrase-2",
        text="This has fun programming in reverse order",
        tags=["test", "reverse"],
        db_path=populated_db
    )
    result2 = add(command)
    
    # Search using quoted exact phrase matching
    command = FindCommand(
        text='"programming fun"',  # The quotes force exact phrase matching in FTS5
        mode="fts",
        limit=10,
        db_path=populated_db
    )
    
    results = find(command)
    
    # Verify that our item with the exact phrase is found
    # And the item with reversed words is not found
    found_exact = "This contains programming fun as a phrase" in [r.text for r in results]
    found_reverse = "This has fun programming in reverse order" in [r.text for r in results]
    
    assert found_exact, "Should find item with exact phrase"
    assert not found_reverse, "Should not find item with reverse word order"

def test_find_glob(populated_db):
    # Search for text starting with "Test"
    command = FindCommand(
        text="Test*",
        mode="glob",
        limit=10,
        db_path=populated_db
    )
    
    results = find(command)
    
    # Should match "Testing code is important"
    assert len(results) == 1
    assert "Testing code is important" in [r.text for r in results]

def test_find_regex(populated_db):
    # Search for text containing "regular" (case insensitive)
    command = FindCommand(
        text=".*regular.*",
        mode="regex",
        limit=10,
        db_path=populated_db
    )
    
    results = find(command)
    
    # Should match "Regular expressions can be complex"
    assert len(results) == 1
    assert "Regular expressions can be complex" in [r.text for r in results]

def test_find_exact(populated_db):
    # Search for exact match
    command = FindCommand(
        text="Learning new technologies is exciting",
        mode="exact",
        limit=10,
        db_path=populated_db
    )
    
    results = find(command)
    
    # Should match exactly one item
    assert len(results) == 1
    assert results[0].text == "Learning new technologies is exciting"

def test_find_with_tags(populated_db):
    # Search for items with specific tags
    command = FindCommand(
        text="",  # No text search
        tags=["fun"],
        limit=10,
        db_path=populated_db
    )
    
    results = find(command)
    
    # Should match items with the "fun" tag
    assert len(results) == 2
    assert "Python programming is fun" in [r.text for r in results]
    assert "Learning new technologies is exciting" in [r.text for r in results]

def test_find_with_text_and_tags(populated_db):
    # Search for items with specific text and tags
    command = FindCommand(
        text="programming",
        mode="substr",
        tags=["fun"],
        limit=10,
        db_path=populated_db
    )
    
    results = find(command)
    
    # Should match items with "programming" text and "fun" tag
    assert len(results) == 1
    assert "Python programming is fun" in [r.text for r in results]

def test_find_limit(populated_db):
    # Search with limit
    command = FindCommand(
        text="",  # Match all
        limit=2,
        db_path=populated_db
    )
    
    results = find(command)
    
    # Should only return 2 items (due to limit)
    assert len(results) == 2