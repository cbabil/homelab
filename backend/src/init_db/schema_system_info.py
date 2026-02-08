"""
System Info Schema

Defines the system_info table for tracking application metadata,
setup status, and installation information.
"""

import structlog

from database.connection import DatabaseManager

logger = structlog.get_logger("schema_system_info")

SYSTEM_INFO_SCHEMA = """
-- System Info Table
-- Single row table (enforced by CHECK constraint) for application metadata
-- Component versions are tracked separately in component_versions table
CREATE TABLE IF NOT EXISTS system_info (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    app_name TEXT NOT NULL DEFAULT 'Tomo',
    is_setup INTEGER NOT NULL DEFAULT 0 CHECK (is_setup IN (0, 1)),
    setup_completed_at TEXT,
    setup_by_user_id TEXT,
    installation_id TEXT NOT NULL,
    license_type TEXT DEFAULT 'community' CHECK (license_type IN ('community', 'pro', 'enterprise')),
    license_key TEXT,
    license_expires_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Ensure single row exists with auto-generated installation ID
INSERT OR IGNORE INTO system_info (id, installation_id)
VALUES (1, lower(hex(randomblob(16))));

-- Trigger to auto-update updated_at timestamp
CREATE TRIGGER IF NOT EXISTS system_info_updated_at
AFTER UPDATE ON system_info
BEGIN
    UPDATE system_info SET updated_at = datetime('now') WHERE id = 1;
END;

-- Index on is_setup for fast lookup
CREATE INDEX IF NOT EXISTS idx_system_info_is_setup ON system_info(is_setup);
"""


async def initialize_system_info_schema(db_manager: DatabaseManager = None) -> bool:
    """Initialize the system_info table schema.

    Args:
        db_manager: Optional DatabaseManager instance. If not provided, creates one.

    Returns:
        True if successful, False otherwise.
    """
    try:
        if db_manager is None:
            db_manager = DatabaseManager()

        async with db_manager.get_connection() as conn:
            # Execute schema creation
            await conn.executescript(SYSTEM_INFO_SCHEMA)
            await conn.commit()

        logger.info("System info schema initialized successfully")
        return True

    except Exception as e:
        logger.error("Failed to initialize system info schema", error=str(e))
        return False


async def check_system_info_exists(db_manager: DatabaseManager = None) -> bool:
    """Check if system_info table exists and has data.

    Args:
        db_manager: Optional DatabaseManager instance.

    Returns:
        True if table exists and has data, False otherwise.
    """
    try:
        if db_manager is None:
            db_manager = DatabaseManager()

        async with db_manager.get_connection() as conn:
            cursor = await conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='system_info'"
            )
            row = await cursor.fetchone()
            return row is not None

    except Exception as e:
        logger.error("Failed to check system_info existence", error=str(e))
        return False
