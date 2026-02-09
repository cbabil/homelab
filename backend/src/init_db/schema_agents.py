"""
Agents Schema

Defines the agents and agent_registration_codes tables for WebSocket-based
agent management. Agents replace SSH for server communication.
"""

import structlog

from services.database_service import DatabaseService

logger = structlog.get_logger("schema_agents")

AGENTS_SCHEMA = """
-- Agents Table
-- Stores agent information for WebSocket-based server management
CREATE TABLE IF NOT EXISTS agents (
    id TEXT PRIMARY KEY,
    server_id TEXT NOT NULL UNIQUE,
    token_hash TEXT,
    version TEXT,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'active', 'disconnected', 'error')),
    last_seen TEXT,
    registered_at TEXT,
    config TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE
);

-- Agent Registration Codes Table
-- Stores one-time registration codes for agent authentication
CREATE TABLE IF NOT EXISTS agent_registration_codes (
    id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    code TEXT NOT NULL UNIQUE,
    expires_at TEXT NOT NULL,
    used INTEGER NOT NULL DEFAULT 0 CHECK (used IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_agents_server_id ON agents(server_id);
CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);
CREATE INDEX IF NOT EXISTS idx_agent_registration_codes_code
    ON agent_registration_codes(code);
CREATE INDEX IF NOT EXISTS idx_agent_registration_codes_agent_id
    ON agent_registration_codes(agent_id);
"""


async def migrate_token_rotation_fields(db_manager: DatabaseService) -> bool:
    """Add token rotation fields to agents table.

    Migration adds:
    - pending_token_hash: For dual-token rotation
    - token_issued_at: When current token was created
    - token_expires_at: When token should be rotated

    Args:
        db_manager: DatabaseService instance.

    Returns:
        True if successful, False otherwise.
    """
    try:
        async with db_manager.get_connection() as conn:
            # Get existing columns
            cursor = await conn.execute("PRAGMA table_info(agents)")
            rows = await cursor.fetchall()
            columns = {row[1] for row in rows}

            # Add pending_token_hash if not exists
            if "pending_token_hash" not in columns:
                await conn.execute(
                    "ALTER TABLE agents ADD COLUMN pending_token_hash TEXT"
                )
                logger.info("Added pending_token_hash column to agents table")

            # Add token_issued_at if not exists
            if "token_issued_at" not in columns:
                await conn.execute("ALTER TABLE agents ADD COLUMN token_issued_at TEXT")
                logger.info("Added token_issued_at column to agents table")

            # Add token_expires_at if not exists
            if "token_expires_at" not in columns:
                await conn.execute(
                    "ALTER TABLE agents ADD COLUMN token_expires_at TEXT"
                )
                logger.info("Added token_expires_at column to agents table")

            await conn.commit()

        logger.info("Token rotation migration completed successfully")
        return True

    except Exception as e:
        logger.error("Failed to migrate token rotation fields", error=str(e))
        return False


async def initialize_agents_schema(db_manager: DatabaseService = None) -> bool:
    """Initialize the agents and agent_registration_codes table schemas.

    Args:
        db_manager: Optional DatabaseService instance. If not provided, creates one.

    Returns:
        True if successful, False otherwise.
    """
    try:
        if db_manager is None:
            db_manager = DatabaseService()

        async with db_manager.get_connection() as conn:
            await conn.executescript(AGENTS_SCHEMA)
            await conn.commit()

        # Run token rotation migration
        await migrate_token_rotation_fields(db_manager)

        logger.info("Agents schema initialized successfully")
        return True

    except Exception as e:
        logger.error("Failed to initialize agents schema", error=str(e))
        return False
