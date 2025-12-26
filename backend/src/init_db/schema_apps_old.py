"""Application database schema management and seeding."""

from __future__ import annotations

import structlog
from sqlalchemy import select, func, text

from database.connection import Base, db_manager
from models.app import (
    App,
    AppCategory,
    AppCategoryTable,
    AppRequirements,
    AppStatus,
    ApplicationTable,
)
from data.application_seed_data import APPLICATIONS, CATEGORIES

logger = structlog.get_logger("schema_apps")


async def create_app_schema() -> None:
    """Create the application catalog schema."""

    await db_manager.initialize()
    async with db_manager.engine.begin() as conn:  # type: ignore[union-attr]
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Application schema created")


async def check_app_schema_exists() -> bool:
    """Return True if the applications table already exists."""

    await db_manager.initialize()
    async with db_manager.engine.begin() as conn:  # type: ignore[union-attr]
        result = await conn.run_sync(
            lambda sync_conn: sync_conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='applications'")
            ).fetchone()
        )
    exists = result is not None
    logger.debug("Applications table existence check", exists=exists)
    return exists


async def seed_application_data() -> None:
    """Populate the application catalog with initial data if empty."""

    await db_manager.initialize()
    async with db_manager.get_session() as session:
        count_result = await session.execute(select(func.count()).select_from(ApplicationTable))
        if count_result.scalar_one() > 0:
            logger.info("Application catalog already seeded")
            return

        # Seed categories (skip existing ones)
        category_models = {
            category["id"]: AppCategory(**category)
            for category in CATEGORIES
        }

        existing_categories = await session.execute(select(AppCategoryTable.id))
        existing_ids = {row[0] for row in existing_categories.all()}

        new_categories = [
            category_model.to_table_model()
            for category_model in category_models.values()
            if category_model.id not in existing_ids
        ]

        if new_categories:
            session.add_all(new_categories)

        # Seed applications
        for app_payload in APPLICATIONS:
            category = category_models[app_payload["category_id"]]
            requirements = app_payload.get("requirements", {})

            app_model = App(
                id=app_payload["id"],
                name=app_payload["name"],
                description=app_payload["description"],
                long_description=app_payload.get("long_description"),
                version=app_payload["version"],
                category=category,
                tags=app_payload.get("tags", []),
                icon=app_payload.get("icon"),
                screenshots=app_payload.get("screenshots"),
                author=app_payload["author"],
                repository=app_payload.get("repository"),
                documentation=app_payload.get("documentation"),
                license=app_payload["license"],
                requirements=AppRequirements(**requirements) if requirements else AppRequirements(),
                status=AppStatus(app_payload["status"]),
                install_count=app_payload.get("install_count"),
                rating=app_payload.get("rating"),
                featured=app_payload.get("featured", False),
                created_at=app_payload["created_at"],
                updated_at=app_payload["updated_at"],
                connected_server_id=app_payload.get("connected_server_id"),
            )

            session.add(app_model.to_table_model())

        logger.info(
            "Seeded application catalog",
            category_count=len(new_categories),
            application_count=len(APPLICATIONS),
        )


async def initialize_app_database() -> None:
    """Ensure the application schema exists and is seeded."""

    schema_exists = await check_app_schema_exists()
    if not schema_exists:
        await create_app_schema()

    await seed_application_data()
    logger.info("Application database initialized")
