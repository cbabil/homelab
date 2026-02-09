"""Application Service.

Provides data access and business logic for the application marketplace."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

import structlog

from exceptions import ApplicationLogWriteError
from logs import build_empty_search_log
from models.app import (
    App,
    AppCategory,
    AppFilter,
    AppInstallation,
    AppRequirements,
    AppSearchResult,
    AppStatus,
)
from services.database.base import DatabaseConnection
from services.service_log import LogService

logger = structlog.get_logger("app_service")

# SQL for fetching apps with their categories via JOIN
_APP_JOIN_SQL = """
    SELECT a.*, c.id AS cat_id, c.name AS cat_name, c.description AS cat_desc,
           c.icon AS cat_icon, c.color AS cat_color
    FROM applications a
    JOIN app_categories c ON a.category_id = c.id
"""


class AppService:
    """Service for managing applications and installations."""

    def __init__(
        self,
        connection: DatabaseConnection,
        log_service: LogService,
    ) -> None:
        self._conn = connection
        self._log_service = log_service
        self.installations: dict[str, AppInstallation] = {}
        logger.info("Application service initialized")

    async def _fetch_all_apps(self) -> list[App]:
        """Fetch all applications with their categories from the database."""
        async with self._conn.get_connection() as conn:
            cursor = await conn.execute(_APP_JOIN_SQL)
            rows = await cursor.fetchall()

        apps = [App.from_row(row) for row in rows]
        logger.debug("Fetched applications from database", count=len(apps))
        return apps

    @staticmethod
    def _apply_filters(apps: list[App], filters: AppFilter) -> list[App]:
        """Apply in-memory filtering to the application list."""
        filtered: list[App] = []
        search_term = filters.search.lower() if filters.search else None
        required_tags = set(tag.lower() for tag in filters.tags or [])

        for app in apps:
            if filters.category and app.category.id != filters.category:
                continue
            if filters.status and app.status != filters.status:
                continue
            if filters.featured is not None and bool(app.featured) != filters.featured:
                continue
            if required_tags and not required_tags.issubset(
                {tag.lower() for tag in app.tags}
            ):
                continue
            if (
                search_term
                and search_term not in app.name.lower()
                and search_term not in app.description.lower()
            ):
                continue
            filtered.append(app)

        return filtered

    @staticmethod
    def _apply_sorting(apps: list[App], filters: AppFilter) -> None:
        """Sort applications in-place based on filter configuration."""
        reverse = (filters.sort_order or "asc").lower() == "desc"
        sort_key = (filters.sort_by or "name").lower()

        if sort_key == "name":
            apps.sort(key=lambda app: app.name.lower(), reverse=reverse)
        elif sort_key == "rating":
            apps.sort(key=lambda app: app.rating or 0, reverse=reverse)
        elif sort_key in {"popularity", "install_count"}:
            apps.sort(key=lambda app: app.install_count or 0, reverse=reverse)
        elif sort_key == "updated":
            apps.sort(
                key=lambda app: AppService._iso_to_datetime(app.updated_at),
                reverse=reverse,
            )
        else:
            logger.debug("Unknown sort key, defaulting to name", sort_key=sort_key)
            apps.sort(key=lambda app: app.name.lower(), reverse=reverse)

    @staticmethod
    def _iso_to_datetime(value: str) -> datetime:
        """Convert ISO formatted string to datetime for sorting."""
        if value.lower().endswith("z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)

    async def search_apps(self, filters: AppFilter) -> AppSearchResult:
        """Search applications with filters and return a result set."""
        apps = await self._fetch_all_apps()
        filtered_apps = self._apply_filters(apps, filters)
        self._apply_sorting(filtered_apps, filters)

        total = len(filtered_apps)

        if total == 0:
            metadata_filters = filters.model_dump(exclude_none=True, mode="json")
            try:
                await self._log_service.create_log_entry(
                    build_empty_search_log(metadata_filters)
                )
            except Exception as exc:  # pylint: disable=broad-except
                error = ApplicationLogWriteError(metadata_filters, exc)
                logger.warning(str(error))

        result = AppSearchResult(
            apps=filtered_apps,
            total=total,
            page=1,
            limit=total or len(apps),
            filters=filters,
        )
        logger.info("Application search completed", total=total)
        return result

    async def get_app_by_id(self, app_id: str) -> App | None:
        """Retrieve a single application by identifier."""
        async with self._conn.get_connection() as conn:
            cursor = await conn.execute(
                _APP_JOIN_SQL + " WHERE a.id = ?", (app_id,)
            )
            row = await cursor.fetchone()

        if not row:
            logger.warning("Application not found", app_id=app_id)
            return None

        app = App.from_row(row)
        logger.debug("Retrieved application", app_id=app_id)
        return app

    async def add_app(self, app_data: dict[str, Any]) -> App:
        """Add an application to the catalog from marketplace import."""
        category_id = app_data.get("category_id") or app_data.get("category")

        async with self._conn.get_connection() as conn:
            # Check if app already exists
            cursor = await conn.execute(
                "SELECT id FROM applications WHERE id = ?", (app_data["id"],)
            )
            if await cursor.fetchone():
                raise ValueError(f"Application {app_data['id']} already exists")

            # Get or create category
            cursor = await conn.execute(
                "SELECT * FROM app_categories WHERE id = ?", (category_id,)
            )
            cat_row = await cursor.fetchone()

            if not cat_row:
                await conn.execute(
                    """INSERT INTO app_categories (id, name, description, icon, color)
                       VALUES (?, ?, ?, ?, ?)""",
                    (
                        category_id,
                        category_id.title(),
                        f"Applications in the {category_id} category",
                        "Package",
                        "text-primary",
                    ),
                )
                cursor = await conn.execute(
                    "SELECT * FROM app_categories WHERE id = ?", (category_id,)
                )
                cat_row = await cursor.fetchone()

            category = AppCategory.from_row(cat_row)

            req_data = app_data.get("requirements", {})
            requirements = AppRequirements(
                min_ram=req_data.get("min_ram"),
                min_storage=req_data.get("min_storage"),
                supported_architectures=req_data.get("architectures", []),
            )

            now = datetime.now(UTC).isoformat()

            app = App(
                id=app_data["id"],
                name=app_data["name"],
                description=app_data["description"],
                long_description=app_data.get("long_description"),
                version=app_data["version"],
                category=category,
                tags=app_data.get("tags", []),
                icon=app_data.get("icon"),
                screenshots=app_data.get("screenshots"),
                author=app_data["author"],
                repository=app_data.get("repository"),
                documentation=app_data.get("documentation"),
                license=app_data["license"],
                requirements=requirements,
                status=AppStatus.AVAILABLE,
                install_count=0,
                rating=app_data.get("avg_rating"),
                featured=app_data.get("featured", False),
                created_at=now,
                updated_at=now,
            )

            params = app.to_insert_params()
            cols = ", ".join(params.keys())
            placeholders = ", ".join(["?"] * len(params))
            await conn.execute(
                f"INSERT INTO applications ({cols}) VALUES ({placeholders})",
                tuple(params.values()),
            )
            await conn.commit()
            logger.info("Application created from import", app_id=app.id, name=app.name)

        return app

    async def remove_app(self, app_id: str) -> bool:
        """Remove an application from the catalog."""
        async with self._conn.get_connection() as conn:
            cursor = await conn.execute(
                "SELECT status FROM applications WHERE id = ?", (app_id,)
            )
            row = await cursor.fetchone()

            if not row:
                return False

            if row["status"] == "installed":
                raise ValueError(
                    f"Cannot remove installed app '{app_id}'. Uninstall it first."
                )

            await conn.execute("DELETE FROM applications WHERE id = ?", (app_id,))
            await conn.commit()
            logger.info("Application removed from catalog", app_id=app_id)

        return True

    async def remove_apps_bulk(self, app_ids: list[str]) -> dict[str, Any]:
        """Remove multiple applications from the catalog."""
        removed = []
        skipped = []

        for app_id in app_ids:
            try:
                success = await self.remove_app(app_id)
                if success:
                    removed.append(app_id)
                else:
                    skipped.append({"id": app_id, "reason": "not found"})
            except ValueError as e:
                skipped.append({"id": app_id, "reason": str(e)})

        return {
            "removed": removed,
            "removed_count": len(removed),
            "skipped": skipped,
            "skipped_count": len(skipped),
        }

    async def get_app_ids(self) -> list[str]:
        """Get all application IDs in the catalog."""
        async with self._conn.get_connection() as conn:
            cursor = await conn.execute("SELECT id FROM applications")
            rows = await cursor.fetchall()
            return [row["id"] for row in rows]

    async def mark_app_uninstalled(self, app_id: str) -> bool:
        """Mark an application as uninstalled (update status to available)."""
        async with self._conn.get_connection() as conn:
            cursor = await conn.execute(
                "SELECT id FROM applications WHERE id = ?", (app_id,)
            )
            if not await cursor.fetchone():
                return False

            await conn.execute(
                "UPDATE applications SET status = ?, connected_server_id = NULL WHERE id = ?",
                ("available", app_id),
            )
            await conn.commit()
            logger.info("Application marked as uninstalled", app_id=app_id)

        return True

    async def mark_app_installed(self, app_id: str, server_id: str) -> bool:
        """Mark an application as installed on a server."""
        async with self._conn.get_connection() as conn:
            cursor = await conn.execute(
                "SELECT id FROM applications WHERE id = ?", (app_id,)
            )
            row = await cursor.fetchone()

            if not row and app_id.startswith("casaos-"):
                base_id = app_id[7:]
                cursor = await conn.execute(
                    "SELECT id FROM applications WHERE id = ?", (base_id,)
                )
                row = await cursor.fetchone()

            if not row:
                logger.warning(
                    "Application not found for marking installed", app_id=app_id
                )
                return False

            actual_id = row["id"]
            await conn.execute(
                "UPDATE applications SET status = ?, connected_server_id = ? WHERE id = ?",
                ("installed", server_id, actual_id),
            )
            await conn.commit()
            logger.info(
                "Application marked as installed",
                app_id=actual_id,
                server_id=server_id,
            )

        return True

    async def mark_apps_uninstalled_bulk(self, app_ids: list[str]) -> dict[str, Any]:
        """Mark multiple applications as uninstalled."""
        uninstalled = []
        skipped = []

        for app_id in app_ids:
            try:
                success = await self.mark_app_uninstalled(app_id)
                if success:
                    uninstalled.append(app_id)
                else:
                    skipped.append({"id": app_id, "reason": "not found"})
            except Exception as e:
                skipped.append({"id": app_id, "reason": str(e)})

        return {
            "uninstalled": uninstalled,
            "uninstalled_count": len(uninstalled),
            "skipped": skipped,
            "skipped_count": len(skipped),
        }

    async def install_app(
        self, app_id: str, config: dict[str, Any] | None = None
    ) -> AppInstallation:
        """Simulate application installation and track status in memory."""
        app = await self.get_app_by_id(app_id)
        if not app:
            raise ValueError(f"Application {app_id} not found")

        installation = AppInstallation(
            app_id=app_id,
            status=AppStatus.INSTALLING,
            version=app.version,
            installed_at=datetime.now(UTC).isoformat(),
            config=config or {},
        )

        self.installations = {**self.installations, app_id: installation}
        logger.info("Application marked as installing", app_id=app_id)
        return installation
