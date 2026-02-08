"""
Users Schema

Defines the users table for authentication and user management.
"""

import structlog

from database.connection import DatabaseManager

logger = structlog.get_logger("schema_users")

USERS_SCHEMA = """
-- Users Table
-- Stores user accounts for authentication
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    email TEXT DEFAULT '',
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('admin', 'user', 'readonly')),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    last_login TEXT,
    password_changed_at TEXT DEFAULT (datetime('now')),
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    preferences_json TEXT DEFAULT '{}',
    avatar TEXT DEFAULT NULL
);

-- Indexes per documentation (docs/database/diagrams/users-settings.md)
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);
"""


async def _migrate_add_password_changed_at(conn) -> None:
    """Add password_changed_at column if it doesn't exist (migration for existing DBs)."""
    try:
        # Check if column exists
        cursor = await conn.execute("PRAGMA table_info(users)")
        columns = await cursor.fetchall()
        column_names = [col[1] for col in columns]

        if "password_changed_at" not in column_names:
            # Add the column
            await conn.execute(
                "ALTER TABLE users ADD COLUMN password_changed_at TEXT DEFAULT (datetime('now'))"
            )
            # Set existing users' password_changed_at to their created_at
            await conn.execute(
                "UPDATE users SET password_changed_at = created_at WHERE password_changed_at IS NULL"
            )
            logger.info("Added password_changed_at column to users table")
    except Exception as e:
        logger.warning(
            "Migration for password_changed_at failed (may already exist)", error=str(e)
        )


async def initialize_users_schema(db_manager: DatabaseManager = None) -> bool:
    """Initialize the users table schema.

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
            await conn.executescript(USERS_SCHEMA)
            await conn.commit()

            # Run migrations for existing databases
            await _migrate_add_password_changed_at(conn)
            await conn.commit()

        logger.info("Users schema initialized successfully")
        return True

    except Exception as e:
        logger.error("Failed to initialize users schema", error=str(e))
        return False
