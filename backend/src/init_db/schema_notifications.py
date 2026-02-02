"""
Notifications Schema

Defines the notifications table for persistent notification storage.
"""

import structlog
from database.connection import DatabaseManager

logger = structlog.get_logger("schema_notifications")

NOTIFICATIONS_SCHEMA = """
-- Notifications Table
-- Stores user notifications for alerts, events, and system messages
CREATE TABLE IF NOT EXISTS notifications (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('info', 'success', 'warning', 'error')),
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    read INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    read_at TEXT,
    dismissed_at TEXT,
    expires_at TEXT,
    source TEXT,
    metadata TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(read);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at);
CREATE INDEX IF NOT EXISTS idx_notifications_type ON notifications(type);
CREATE INDEX IF NOT EXISTS idx_notifications_user_read ON notifications(user_id, read);
"""


async def initialize_notifications_schema(db_manager: DatabaseManager = None) -> bool:
    """Initialize the notifications table schema.

    Args:
        db_manager: Optional DatabaseManager instance. If not provided, creates one.

    Returns:
        True if successful, False otherwise.
    """
    try:
        if db_manager is None:
            db_manager = DatabaseManager()

        async with db_manager.get_connection() as conn:
            await conn.executescript(NOTIFICATIONS_SCHEMA)
            await conn.commit()

        logger.info("Notifications schema initialized successfully")
        return True

    except Exception as e:
        logger.error("Failed to initialize notifications schema", error=str(e))
        return False
