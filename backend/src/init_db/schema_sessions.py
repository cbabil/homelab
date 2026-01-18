"""
Sessions Schema

Defines the sessions table for persistent session management.
"""

import structlog
from database.connection import DatabaseManager

logger = structlog.get_logger("schema_sessions")

SESSIONS_SCHEMA = """
-- Sessions Table
-- Stores user sessions for authentication tracking
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    ip_address TEXT,
    user_agent TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    expires_at TEXT NOT NULL,
    last_activity TEXT NOT NULL DEFAULT (datetime('now')),
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'idle', 'expired', 'terminated')),
    terminated_at TEXT,
    terminated_by TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_sessions_last_activity ON sessions(last_activity);
"""


async def initialize_sessions_schema(db_manager: DatabaseManager = None) -> bool:
    """Initialize the sessions table schema.

    Args:
        db_manager: Optional DatabaseManager instance. If not provided, creates one.

    Returns:
        True if successful, False otherwise.
    """
    try:
        if db_manager is None:
            db_manager = DatabaseManager()

        async with db_manager.get_connection() as conn:
            await conn.executescript(SESSIONS_SCHEMA)
            await conn.commit()

        logger.info("Sessions schema initialized successfully")
        return True

    except Exception as e:
        logger.error("Failed to initialize sessions schema", error=str(e))
        return False
