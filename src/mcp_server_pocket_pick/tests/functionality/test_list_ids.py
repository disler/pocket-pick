import pytest
import tempfile
import os
from pathlib import Path
from ...modules.data_types import AddCommand, ListIdsCommand
from ...modules.functionality.add import add
from ...modules.functionality.list_ids import list_ids

@pytest.fixture
def temp_db_path():
    fd, path = tempfile.mkstemp()
    os.close(fd)
    yield Path(path)
    if os.path.exists(path):
        os.unlink(path)

@pytest.fixture
def populated_db(temp_db_path):
    items = [
        {"id": "python-1", "text": "Python programming is fun", "tags": ["python", "programming", "fun"]},
        {"id": "sql-1", "text": "SQL databases are powerful", "tags": ["sql", "database", "programming"]},
        {"id": "testing-1", "text": "Testing code is important", "tags": ["testing", "code", "programming"]},
        {"id": "regex-1", "text": "Regular expressions can be complex", "tags": ["regex", "programming", "advanced"]},
        {"id": "learning-1", "text": "Learning new technologies is exciting", "tags": ["learning", "technology", "fun"]},
    ]

    for item in items:
        command = AddCommand(
            id=item["id"],
            text=item["text"],
            tags=item["tags"],
            db_path=temp_db_path,
        )
        add(command)

    return temp_db_path

def test_list_ids_all(populated_db):
    command = ListIdsCommand(
        limit=10,
        db_path=populated_db,
    )

    results = list_ids(command)

    assert len(results) == 5
    for expected in [
        "python-1",
        "sql-1",
        "testing-1",
        "regex-1",
        "learning-1",
    ]:
        assert expected in results

def test_list_ids_with_tags(populated_db):
    command = ListIdsCommand(
        tags=["programming"],
        limit=10,
        db_path=populated_db,
    )

    results = list_ids(command)

    assert len(results) == 4
    for expected in ["python-1", "sql-1", "testing-1", "regex-1"]:
        assert expected in results

def test_list_ids_limit(populated_db):
    command = ListIdsCommand(
        limit=2,
        db_path=populated_db,
    )

    results = list_ids(command)

    assert len(results) == 2

def test_list_ids_empty_db(temp_db_path):
    command = ListIdsCommand(
        db_path=temp_db_path,
    )

    results = list_ids(command)

    assert len(results) == 0
