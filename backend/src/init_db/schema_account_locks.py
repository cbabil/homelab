"""
Account Locks Schema

Defines the account_locks table for tracking failed login attempts
and locking accounts/IPs to prevent brute force attacks.
"""

import structlog

from services.database_service import DatabaseService

logger = structlog.get_logger("schema_account_locks")

ACCOUNT_LOCKS_SCHEMA = """
-- Account Locks Table
-- Tracks failed login attempts and locks accounts/IPs to prevent brute force attacks
CREATE TABLE IF NOT EXISTS account_locks (
    id TEXT PRIMARY KEY,
    identifier TEXT NOT NULL,
    identifier_type TEXT NOT NULL CHECK (identifier_type IN ('username', 'ip')),
    attempt_count INTEGER NOT NULL DEFAULT 1,
    first_attempt_at TEXT NOT NULL DEFAULT (datetime('now')),
    last_attempt_at TEXT NOT NULL DEFAULT (datetime('now')),
    locked_at TEXT,
    lock_expires_at TEXT,
    ip_address TEXT,
    user_agent TEXT,
    reason TEXT DEFAULT 'too_many_attempts',
    unlocked_at TEXT,
    unlocked_by TEXT,
    notes TEXT,
    UNIQUE(identifier, identifier_type)
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_account_locks_identifier ON account_locks(identifier);
CREATE INDEX IF NOT EXISTS idx_account_locks_identifier_type ON account_locks(identifier_type);
CREATE INDEX IF NOT EXISTS idx_account_locks_locked_at ON account_locks(locked_at);
CREATE INDEX IF NOT EXISTS idx_account_locks_lock_expires_at ON account_locks(lock_expires_at);
CREATE INDEX IF NOT EXISTS idx_account_locks_ip_address ON account_locks(ip_address);
"""


async def initialize_account_locks_schema(db_manager: DatabaseService = None) -> bool:
    """Initialize the account_locks table schema.

    Args:
        db_manager: Optional DatabaseService instance. If not provided, creates one.

    Returns:
        True if successful, False otherwise.
    """
    try:
        if db_manager is None:
            db_manager = DatabaseService()

        async with db_manager.get_connection() as conn:
            await conn.executescript(ACCOUNT_LOCKS_SCHEMA)
            await conn.commit()

        logger.info("Account locks schema initialized successfully")
        return True

    except Exception as e:
        logger.error("Failed to initialize account locks schema", error=str(e))
        return False
