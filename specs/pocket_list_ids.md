# Pocket Pick List IDs Feature

## Overview
The `pocket_list_ids` command will provide a simple way to retrieve just the IDs of all items stored in the Pocket Pick database. This lightweight command is useful for quickly checking what IDs exist without having to retrieve the full content of each item.

## Command Details

### Name
`pocket_list_ids`

### Description
List all item IDs in your pocket pick database, optionally filtered by tags

### Parameters
- `tags` (optional): List of strings - Filter results to only include items with these tags
- `limit` (optional): Integer - Maximum number of IDs to return (default: 100)
- `db` (optional): String - Path to the database file (defaults to "~/.pocket_pick.db")

### Response Format
The command will return a simple list of strings, with each string representing an item ID.

Example response:
```
python-sort-algorithm
css-flexbox-cheatsheet
docker-cheat-sheet
api-design-patterns
git-workflow
```

## Implementation Plan

### 1. Data Model
Create a `ListIdsCommand` model in `data_types.py`:
```python
class ListIdsCommand(BaseModel):
    tags: List[str] = []
    limit: int = 100
    db_path: Path = DEFAULT_SQLITE_DATABASE_PATH
```

### 2. Tool Definition
Add a new tool to the `PocketTools` enum in `server.py`:
```python
class PocketTools(str, Enum):
    ...
    LIST_IDS = "pocket_list_ids"
    ...
```

### 3. Functionality
Create a new file `list_ids.py` in the functionality directory:
```python
from typing import List
import sqlite3
import json
from ..data_types import ListIdsCommand

def list_ids(command: ListIdsCommand) -> List[str]:
    """List all item IDs in the database, optionally filtered by tags."""
    connection = sqlite3.connect(command.db_path)
    cursor = connection.cursor()
    
    if command.tags:
        # If tags are provided, filter by them
        placeholders = ', '.join(['?'] * len(command.tags))
        query = f"""
            SELECT id 
            FROM POCKET_PICK
            WHERE id IN (
                SELECT id 
                FROM POCKET_PICK 
                WHERE (
                    SELECT COUNT(*) 
                    FROM json_each(tags) 
                    WHERE json_each.value IN ({placeholders})
                ) = ?
            )
            ORDER BY created DESC
            LIMIT ?
        """
        params = [*command.tags, len(command.tags), command.limit]
    else:
        # If no tags provided, get all IDs
        query = """
            SELECT id
            FROM POCKET_PICK
            ORDER BY created DESC
            LIMIT ?
        """
        params = [command.limit]
    
    cursor.execute(query, params)
    results = [row[0] for row in cursor.fetchall()]
    
    cursor.close()
    connection.close()
    
    return results
```

### 4. Server Integration
Add the tool to the server's `list_tools()` method:
```python
Tool(
    name=PocketTools.LIST_IDS,
    description="List all item IDs in your pocket pick database, optionally filtered by tags",
    inputSchema=PocketListIds.schema(),
),
```

### 5. Handler Implementation
Add a case to the `call_tool()` method:
```python
case PocketTools.LIST_IDS:
    command = ListIdsCommand(
        tags=arguments.get("tags", []),
        limit=arguments.get("limit", 100),
        db_path=db_path
    )
    results = list_ids(command)
    
    if not results:
        return [TextContent(
            type="text",
            text="No item IDs found."
        )]
    
    return [TextContent(
        type="text",
        text="\n".join(results)
    )]
```

## Benefits
1. Provides a lightweight way to see all available IDs
2. Useful for checking if an ID exists before adding a new item
3. Can be used to generate reports or lists of available knowledge
4. Supports the same tag filtering as other list commands for consistency

## Testing
Testing should verify that:
1. All IDs are correctly returned when no filters are applied
2. Tag filtering correctly limits the IDs returned
3. The limit parameter correctly restricts the number of results
4. Results are ordered by creation date (newest first)
5. The response format is a simple list of strings