"""Application database schema seeding.

Schema creation is handled by SchemaInitializer.initialize_applications_tables().
This module only provides the seed_application_data() helper.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

import structlog

from data.application_seed_data import APPLICATIONS, CATEGORIES
from services.database.base import DatabaseConnection

logger = structlog.get_logger("schema_apps")


async def seed_application_data(connection: DatabaseConnection) -> None:
    """Populate the application catalog with initial data if empty."""
    async with connection.get_connection() as conn:
        cursor = await conn.execute("SELECT COUNT(*) FROM applications")
        row = await cursor.fetchone()
        if row and row[0] > 0:
            logger.info("Application catalog already seeded")
            return

        # Seed categories
        for cat in CATEGORIES:
            await conn.execute(
                """INSERT OR IGNORE INTO app_categories
                   (id, name, description, icon, color)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    cat["id"],
                    cat["name"],
                    cat["description"],
                    cat.get("icon", "Package"),
                    cat.get("color", "text-primary"),
                ),
            )

        # Seed applications
        now = datetime.now(UTC).isoformat()
        for app in APPLICATIONS:
            req = app.get("requirements", {})
            await conn.execute(
                """INSERT OR IGNORE INTO applications
                   (id, name, description, long_description, version,
                    category_id, tags, icon, screenshots, author,
                    repository, documentation, license, requirements,
                    status, install_count, rating, featured,
                    created_at, updated_at, connected_server_id)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    app["id"],
                    app["name"],
                    app["description"],
                    app.get("long_description"),
                    app["version"],
                    app.get("category_id", app.get("category")),
                    json.dumps(app.get("tags", [])),
                    app.get("icon"),
                    json.dumps(app.get("screenshots")) if app.get("screenshots") else None,
                    app["author"],
                    app.get("repository"),
                    app.get("documentation"),
                    app["license"],
                    json.dumps(req) if req else None,
                    app.get("status", "available"),
                    app.get("install_count", 0),
                    app.get("rating"),
                    1 if app.get("featured") else 0,
                    app.get("created_at", now),
                    app.get("updated_at", now),
                    app.get("connected_server_id"),
                ),
            )

        await conn.commit()
        logger.info(
            "Seeded application catalog",
            category_count=len(CATEGORIES),
            application_count=len(APPLICATIONS),
        )
