# Feature Specification: Require ID for Adding Items

## High Level Objective
Currently, when users add items to the Pocket Pick database using the `pocket_add` and `pocket_add_file` tools, IDs are automatically generated. This feature will modify these tools to require users to provide an ID as a mandatory parameter when adding items, giving them more control over item identification and enabling custom ID schemes.

Benefits:
- Allows users to create meaningful, custom IDs instead of auto-generated UUIDs
- Enables semantic naming for easier item recall
- Provides consistency with other commands that require IDs
- Maintains backward compatibility with existing database records

## Type Changes

### Data Types Module
**File**: `src/mcp_server_pocket_pick/modules/data_types.py`

1. Update `AddCommand` class:
   ```python
   class AddCommand(BaseModel):
       id: str  # New required field
       text: str
       tags: List[str] = []
       db_path: Path = DEFAULT_SQLITE_DATABASE_PATH
   ```

2. Update `AddFileCommand` class:
   ```python
   class AddFileCommand(BaseModel):
       id: str  # New required field
       file_path: str
       tags: List[str] = []
       db_path: Path = DEFAULT_SQLITE_DATABASE_PATH
   ```

### Server Module
**File**: `src/mcp_server_pocket_pick/server.py`

1. Update `PocketAdd` class:
   ```python
   class PocketAdd(BaseModel):
       id: str  # New required field
       text: str
       tags: List[str] = []
       db: str = str(DEFAULT_SQLITE_DATABASE_PATH)
   ```

2. Update `PocketAddFile` class:
   ```python
   class PocketAddFile(BaseModel):
       id: str  # New required field
       file_path: str
       tags: List[str] = []
       db: str = str(DEFAULT_SQLITE_DATABASE_PATH)
   ```

## Method Changes

### Add Functionality Module
**File**: `src/mcp_server_pocket_pick/modules/functionality/add.py`

1. Modify the `add` function:
   - Remove UUID generation code
   - Use the provided ID from `command.id`
   - Add error handling for duplicate IDs
   - Return a clear error message if the ID already exists

### Add File Functionality Module
**File**: `src/mcp_server_pocket_pick/modules/functionality/add_file.py`

1. Similar changes to the `add_file` function:
   - Remove UUID generation code
   - Use the provided ID from `command.id`
   - Add error handling for duplicate IDs
   - Return a clear error message if the ID already exists

### Server Implementation
**File**: `src/mcp_server_pocket_pick/server.py`

1. Update the `call_tool` function to pass the ID from arguments:
   ```python
   # In PocketTools.ADD case:
   command = AddCommand(
       id=arguments["id"],  # Pass the ID from arguments
       text=arguments["text"],
       tags=arguments.get("tags", []),
       db_path=db_path
   )
   
   # In PocketTools.ADD_FILE case:
   command = AddFileCommand(
       id=arguments["id"],  # Pass the ID from arguments
       file_path=arguments["file_path"],
       tags=arguments.get("tags", []),
       db_path=db_path
   )
   ```

2. Add error handling for duplicate IDs in both cases

## Test Changes

### Add Tests
**File**: `src/mcp_server_pocket_pick/tests/functionality/test_add.py`

1. Update existing tests to include an ID parameter
2. Add new test cases:
   - Test successful addition with a custom ID
   - Test error case when adding an item with a duplicate ID
   - Test with different ID formats and edge cases

### Add File Tests
**File**: `src/mcp_server_pocket_pick/tests/functionality/test_add_file.py`

1. Update existing tests to include an ID parameter
2. Add new test cases:
   - Test successful addition with a custom ID
   - Test error case when adding an item with a duplicate ID
   - Test with different ID formats and edge cases

Check the other tests to see if they're using any add functions and update them to use the new ID parameter.
   file: `src/mcp_server_pocket_pick/tests/functionality/*`

## Self Validation

1. **Manual Testing**:
   - Add an item with a custom ID
   - Verify it was added correctly
   - Try to add another item with the same ID and verify the error
   - Get, list, and remove the item using the custom ID

2. **Automated Testing**:
   - Run all tests with `uv run pytest -v`
   - Verify all tests pass

## README Update
**File**: `README.md`

1. Update tool descriptions in the "Pocket Pick MCP Tools" section:
   - `pocket_add`: "Add a new item with a specified ID to your knowledge base"
   - `pocket_add_file`: "Add a file's content with a specified ID to your knowledge base"

2. Update examples in the "Using with Claude" section to include IDs:
   ```
   Add "claude mcp list" as a pocket pick item with ID "claude-mcp-list". tags: mcp, claude, code
   ```

3. Add a new section on ID management:
   ```markdown
   ## ID Management
   
   When adding items to Pocket Pick, you must now provide a unique ID:
   
   - IDs must be unique across your database
   - Choose descriptive IDs that help you identify the content
   - If you attempt to add an item with an ID that already exists, you'll receive an error
   