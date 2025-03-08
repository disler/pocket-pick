import logging
from pathlib import Path
from typing import Sequence, List
from mcp.server import Server
from mcp.server.session import ServerSession
from mcp.server.stdio import stdio_server
from mcp.types import (
    ClientCapabilities,
    TextContent,
    Tool,
    ListRootsResult,
    RootsCapability,
)
from enum import Enum
from pydantic import BaseModel

from .modules.data_types import (
    AddCommand,
    FindCommand, 
    ListCommand,
    ListTagsCommand,
    RemoveCommand,
    GetCommand,
    BackupCommand,
)
from .modules.functionality.add import add
from .modules.functionality.find import find
from .modules.functionality.list import list_items
from .modules.functionality.list_tags import list_tags
from .modules.functionality.remove import remove
from .modules.functionality.get import get
from .modules.functionality.backup import backup
from .modules.constants import DEFAULT_SQLITE_DATABASE_PATH

logger = logging.getLogger(__name__)

class PocketAdd(BaseModel):
    text: str
    tags: List[str] = []
    db: str = str(DEFAULT_SQLITE_DATABASE_PATH)

class PocketFind(BaseModel):
    text: str
    mode: str = "substr"
    limit: int = 5
    info: bool = False
    tags: List[str] = []
    db: str = str(DEFAULT_SQLITE_DATABASE_PATH)

class PocketList(BaseModel):
    tags: List[str] = []
    limit: int = 100
    db: str = str(DEFAULT_SQLITE_DATABASE_PATH)

class PocketListTags(BaseModel):
    limit: int = 1000
    db: str = str(DEFAULT_SQLITE_DATABASE_PATH)

class PocketRemove(BaseModel):
    id: str
    db: str = str(DEFAULT_SQLITE_DATABASE_PATH)

class PocketGet(BaseModel):
    id: str
    db: str = str(DEFAULT_SQLITE_DATABASE_PATH)

class PocketBackup(BaseModel):
    backup_path: str
    db: str = str(DEFAULT_SQLITE_DATABASE_PATH)

class PocketTools(str, Enum):
    ADD = "pocket_add"
    FIND = "pocket_find"
    LIST = "pocket_list"
    LIST_TAGS = "pocket_list_tags"
    REMOVE = "pocket_remove"
    GET = "pocket_get"
    BACKUP = "pocket_backup"

async def serve(sqlite_database: Path | None = None) -> None:
    logger.info(f"Starting Pocket Pick MCP server")
    
    if sqlite_database is not None:
        logger.info(f"Using database at {sqlite_database}")
    else:
        logger.info(f"Using default database at {DEFAULT_SQLITE_DATABASE_PATH}")
    
    server = Server("pocket-pick")
    
    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name=PocketTools.ADD,
                description="Add a new item to your pocket pick database",
                inputSchema=PocketAdd.schema(),
            ),
            Tool(
                name=PocketTools.FIND,
                description="Find items in your pocket pick database by text and tags",
                inputSchema=PocketFind.schema(),
            ),
            Tool(
                name=PocketTools.LIST,
                description="List items in your pocket pick database, optionally filtered by tags",
                inputSchema=PocketList.schema(),
            ),
            Tool(
                name=PocketTools.LIST_TAGS,
                description="List all tags in your pocket pick database with their counts",
                inputSchema=PocketListTags.schema(),
            ),
            Tool(
                name=PocketTools.REMOVE,
                description="Remove an item from your pocket pick database by ID",
                inputSchema=PocketRemove.schema(),
            ),
            Tool(
                name=PocketTools.GET,
                description="Get an item from your pocket pick database by ID",
                inputSchema=PocketGet.schema(),
            ),
            Tool(
                name=PocketTools.BACKUP,
                description="Backup your pocket pick database to a specified location",
                inputSchema=PocketBackup.schema(),
            ),
        ]
    
    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        # Override db_path if provided via command line
        if sqlite_database is not None:
            arguments["db"] = str(sqlite_database)
        
        db_path = Path(arguments["db"])
        
        match name:
            case PocketTools.ADD:
                command = AddCommand(
                    text=arguments["text"],
                    tags=arguments.get("tags", []),
                    db_path=db_path
                )
                result = add(command)
                return [TextContent(
                    type="text",
                    text=f"Added item with ID: {result.id}\nText: {result.text}\nTags: {', '.join(result.tags)}"
                )]
            
            case PocketTools.FIND:
                command = FindCommand(
                    text=arguments["text"],
                    mode=arguments.get("mode", "substr"),
                    limit=arguments.get("limit", 5),
                    info=arguments.get("info", False),
                    tags=arguments.get("tags", []),
                    db_path=db_path
                )
                results = find(command)
                
                if not results:
                    return [TextContent(
                        type="text",
                        text="No items found matching your search criteria."
                    )]
                
                output = []
                for item in results:
                    if command.info:
                        output.append(f"ID: {item.id}")
                        output.append(f"Created: {item.created.isoformat()}")
                        output.append(f"Tags: {', '.join(item.tags)}")
                        output.append(f"Text: {item.text}")
                        output.append("")
                    else:
                        output.append(item.text)
                        output.append("")
                
                return [TextContent(
                    type="text",
                    text="\n".join(output).strip()
                )]
            
            case PocketTools.LIST:
                command = ListCommand(
                    tags=arguments.get("tags", []),
                    limit=arguments.get("limit", 100),
                    db_path=db_path
                )
                results = list_items(command)
                
                if not results:
                    return [TextContent(
                        type="text",
                        text="No items found."
                    )]
                
                output = []
                for item in results:
                    output.append(f"ID: {item.id}")
                    output.append(f"Created: {item.created.isoformat()}")
                    output.append(f"Tags: {', '.join(item.tags)}")
                    output.append(f"Text: {item.text}")
                    output.append("")
                
                return [TextContent(
                    type="text",
                    text="\n".join(output).strip()
                )]
            
            case PocketTools.LIST_TAGS:
                command = ListTagsCommand(
                    limit=arguments.get("limit", 1000),
                    db_path=db_path
                )
                results = list_tags(command)
                
                if not results:
                    return [TextContent(
                        type="text",
                        text="No tags found."
                    )]
                
                output = ["Tags:"]
                for item in results:
                    output.append(f"{item['tag']} ({item['count']})")
                
                return [TextContent(
                    type="text",
                    text="\n".join(output)
                )]
            
            case PocketTools.REMOVE:
                command = RemoveCommand(
                    id=arguments["id"],
                    db_path=db_path
                )
                result = remove(command)
                
                if result:
                    return [TextContent(
                        type="text",
                        text=f"Item {command.id} removed successfully."
                    )]
                else:
                    return [TextContent(
                        type="text",
                        text=f"Item {command.id} not found."
                    )]
            
            case PocketTools.GET:
                command = GetCommand(
                    id=arguments["id"],
                    db_path=db_path
                )
                result = get(command)
                
                if result:
                    return [TextContent(
                        type="text",
                        text=f"ID: {result.id}\nCreated: {result.created.isoformat()}\nTags: {', '.join(result.tags)}\nText: {result.text}"
                    )]
                else:
                    return [TextContent(
                        type="text",
                        text=f"Item {command.id} not found."
                    )]
            
            case PocketTools.BACKUP:
                command = BackupCommand(
                    backup_path=Path(arguments["backup_path"]),
                    db_path=db_path
                )
                result = backup(command)
                
                if result:
                    return [TextContent(
                        type="text",
                        text=f"Database backed up successfully to {command.backup_path}"
                    )]
                else:
                    return [TextContent(
                        type="text",
                        text=f"Failed to backup database to {command.backup_path}"
                    )]
            
            case _:
                raise ValueError(f"Unknown tool: {name}")
    
    options = server.create_initialization_options()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, options, raise_exceptions=True)