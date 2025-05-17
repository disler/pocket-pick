import sqlite3
from typing import List
import logging
from ..data_types import ListIdsCommand
from ..init_db import init_db, normalize_tags

logger = logging.getLogger(__name__)

def list_ids(command: ListIdsCommand) -> List[str]:
    """List all item IDs in the database, optionally filtered by tags."""
    normalized_tags = normalize_tags(command.tags) if command.tags else []

    db = init_db(command.db_path)

    try:
        if normalized_tags:
            placeholders = ', '.join(['?'] * len(normalized_tags))
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
            params = [*normalized_tags, len(normalized_tags), command.limit]
        else:
            query = """
                SELECT id
                FROM POCKET_PICK
                ORDER BY created DESC
                LIMIT ?
            """
            params = [command.limit]

        cursor = db.execute(query, params)
        results = [row[0] for row in cursor.fetchall()]
        return results
    except Exception as e:
        logger.error(f"Error listing ids: {e}")
        raise
    finally:
        db.close()
