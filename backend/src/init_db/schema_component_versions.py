"""
Component Versions Schema

Defines the component_versions table for tracking versions of
backend, frontend, and mcp components.
"""

import structlog

from database.connection import DatabaseManager

logger = structlog.get_logger("schema_component_versions")

COMPONENT_VERSIONS_SCHEMA = """
-- Component Versions Table
-- Tracks installed versions of each application component
CREATE TABLE IF NOT EXISTS component_versions (
    component TEXT PRIMARY KEY CHECK (component IN ('backend', 'frontend', 'api')),
    version TEXT NOT NULL DEFAULT '1.0.0',
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Initialize default versions for all components
INSERT OR IGNORE INTO component_versions (component, version) VALUES
    ('backend', '1.0.0'),
    ('frontend', '1.0.0'),
    ('api', '1.0.0');

-- Trigger to update updated_at on version change
CREATE TRIGGER IF NOT EXISTS component_versions_updated_at
AFTER UPDATE ON component_versions
BEGIN
    UPDATE component_versions SET updated_at = datetime('now') WHERE component = NEW.component;
END;
"""


async def initialize_component_versions_schema(
    db_manager: DatabaseManager = None,
) -> bool:
    """Initialize the component_versions table schema.

    Args:
        db_manager: Optional DatabaseManager instance. If not provided, creates one.

    Returns:
        True if successful, False otherwise.
    """
    try:
        if db_manager is None:
            db_manager = DatabaseManager()

        async with db_manager.get_connection() as conn:
            await conn.executescript(COMPONENT_VERSIONS_SCHEMA)
            await conn.commit()

        logger.info("Component versions schema initialized successfully")
        return True

    except Exception as e:
        logger.error("Failed to initialize component versions schema", error=str(e))
        return False


async def check_component_versions_exists(db_manager: DatabaseManager = None) -> bool:
    """Check if component_versions table exists.

    Args:
        db_manager: Optional DatabaseManager instance.

    Returns:
        True if table exists, False otherwise.
    """
    try:
        if db_manager is None:
            db_manager = DatabaseManager()

        async with db_manager.get_connection() as conn:
            cursor = await conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='component_versions'"
            )
            row = await cursor.fetchone()
            return row is not None

    except Exception as e:
        logger.error("Failed to check component_versions existence", error=str(e))
        return False
