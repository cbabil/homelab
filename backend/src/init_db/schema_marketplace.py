"""Marketplace database schema management."""

from __future__ import annotations

import structlog
from sqlalchemy import text

from database.connection import Base, db_manager

logger = structlog.get_logger("schema_marketplace")


async def create_marketplace_schema() -> None:
    """Create the marketplace schema."""

    await db_manager.initialize()
    async with db_manager.engine.begin() as conn:  # type: ignore[union-attr]
        # Use checkfirst=True to avoid errors if tables already exist
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn, checkfirst=True))
    logger.info("Marketplace schema created")


async def check_marketplace_schema_exists() -> bool:
    """Return True if the marketplace_repos table already exists."""

    await db_manager.initialize()
    async with db_manager.engine.begin() as conn:  # type: ignore[union-attr]
        result = await conn.run_sync(
            lambda sync_conn: sync_conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='marketplace_repos'")
            ).fetchone()
        )
    exists = result is not None
    logger.debug("Marketplace repos table existence check", exists=exists)
    return exists


async def migrate_marketplace_schema() -> None:
    """Apply any needed schema migrations."""

    await db_manager.initialize()
    async with db_manager.engine.begin() as conn:
        # Check if maintainers column exists
        result = await conn.run_sync(
            lambda sync_conn: sync_conn.execute(
                text("PRAGMA table_info(marketplace_apps)")
            ).fetchall()
        )
        columns = [row[1] for row in result]

        if "maintainers" not in columns:
            logger.info("Adding maintainers column to marketplace_apps")
            await conn.run_sync(
                lambda sync_conn: sync_conn.execute(
                    text("ALTER TABLE marketplace_apps ADD COLUMN maintainers TEXT")
                )
            )


async def initialize_marketplace_database() -> None:
    """Ensure the marketplace schema exists."""

    schema_exists = await check_marketplace_schema_exists()
    if not schema_exists:
        await create_marketplace_schema()
    else:
        # Run migrations for existing schema
        await migrate_marketplace_schema()

    logger.info("Marketplace database initialized")
