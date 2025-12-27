"""Marketplace database schema management."""

from __future__ import annotations

import structlog
from sqlalchemy import text

from database.connection import Base, db_manager
from models.marketplace import (
    MarketplaceRepoTable,
    MarketplaceAppTable,
    AppRatingTable,
)

logger = structlog.get_logger("schema_marketplace")


async def create_marketplace_schema() -> None:
    """Create the marketplace schema."""

    await db_manager.initialize()
    async with db_manager.engine.begin() as conn:  # type: ignore[union-attr]
        await conn.run_sync(Base.metadata.create_all)
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


async def initialize_marketplace_database() -> None:
    """Ensure the marketplace schema exists."""

    schema_exists = await check_marketplace_schema_exists()
    if not schema_exists:
        await create_marketplace_schema()

    logger.info("Marketplace database initialized")
