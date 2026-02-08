"""Application Service

Provides data access and business logic for the application marketplace."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import structlog
from sqlalchemy import select

from database.connection import db_manager
from exceptions import ApplicationLogWriteError
from init_db.schema_apps import initialize_app_database
from logs import build_empty_search_log
from models.app import (
    App,
    AppCategory,
    AppCategoryTable,
    AppFilter,
    AppInstallation,
    ApplicationTable,
    AppRequirements,
    AppSearchResult,
    AppStatus,
)
from services.service_log import log_service

logger = structlog.get_logger("app_service")


class AppService:
    """Service for managing applications and installations."""

    def __init__(self) -> None:
        self._initialized = False
        self.installations: dict[str, AppInstallation] = {}
        logger.info("Application service initialized")

    async def _ensure_initialized(self) -> None:
        if not self._initialized:
            await initialize_app_database()
            self._initialized = True

    async def _fetch_all_apps(self) -> list[App]:
        """Fetch all applications with their categories from the database."""

        await self._ensure_initialized()

        async with db_manager.get_session() as session:
            result = await session.execute(
                select(ApplicationTable, AppCategoryTable).join(
                    AppCategoryTable,
                    ApplicationTable.category_id == AppCategoryTable.id,
                )
            )
            rows = result.all()

        apps: list[App] = [
            App.from_table(app_row, category_row) for app_row, category_row in rows
        ]
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
                await log_service.create_log_entry(
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

        await self._ensure_initialized()

        async with db_manager.get_session() as session:
            result = await session.execute(
                select(ApplicationTable, AppCategoryTable)
                .join(
                    AppCategoryTable,
                    ApplicationTable.category_id == AppCategoryTable.id,
                )
                .where(ApplicationTable.id == app_id)
            )
            row = result.first()

        if not row:
            logger.warning("Application not found", app_id=app_id)
            return None

        app = App.from_table(row[0], row[1])
        logger.debug("Retrieved application", app_id=app_id)
        return app

    async def add_app(self, app_data: dict[str, Any]) -> App:
        """Add an application to the catalog from marketplace import.

        Args:
            app_data: Dictionary with app fields (from marketplace import)

        Returns:
            Created App instance
        """
        await self._ensure_initialized()

        # Get or create category
        category_id = app_data.get("category_id") or app_data.get("category")

        async with db_manager.get_session() as session:
            # Check if app already exists
            existing = await session.execute(
                select(ApplicationTable).where(ApplicationTable.id == app_data["id"])
            )
            if existing.first():
                raise ValueError(f"Application {app_data['id']} already exists")

            # Get the category
            cat_result = await session.execute(
                select(AppCategoryTable).where(AppCategoryTable.id == category_id)
            )
            cat_row = cat_result.first()

            if not cat_row:
                # Create a simple category if it doesn't exist
                new_cat = AppCategoryTable(
                    id=category_id,
                    name=category_id.title(),
                    description=f"Applications in the {category_id} category",
                    icon="Package",
                    color="text-primary",
                )
                session.add(new_cat)
                await session.flush()
                cat_row = (new_cat,)

            category = AppCategory.from_table(cat_row[0])

            # Build requirements
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

            session.add(app.to_table_model())
            logger.info("Application created from import", app_id=app.id, name=app.name)

        return app

    async def remove_app(self, app_id: str) -> bool:
        """Remove an application from the catalog.

        Only allows removing apps that are not installed.

        Args:
            app_id: Application ID to remove

        Returns:
            True if removed, False if not found

        Raises:
            ValueError: If app is installed
        """
        await self._ensure_initialized()

        async with db_manager.get_session() as session:
            # Check if app exists and get its status
            result = await session.execute(
                select(ApplicationTable).where(ApplicationTable.id == app_id)
            )
            app_row = result.first()

            if not app_row:
                return False

            app = app_row[0]
            if app.status == "installed":
                raise ValueError(
                    f"Cannot remove installed app '{app_id}'. Uninstall it first."
                )

            await session.execute(
                ApplicationTable.__table__.delete().where(ApplicationTable.id == app_id)
            )
            logger.info("Application removed from catalog", app_id=app_id)

        return True

    async def remove_apps_bulk(self, app_ids: list[str]) -> dict[str, Any]:
        """Remove multiple applications from the catalog.

        Only removes apps that are not installed. Skips installed apps.

        Args:
            app_ids: List of application IDs to remove

        Returns:
            Dict with removed count, skipped count, and details
        """
        await self._ensure_initialized()

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
        """Get all application IDs in the catalog.

        Returns:
            List of application IDs
        """
        await self._ensure_initialized()

        async with db_manager.get_session() as session:
            result = await session.execute(select(ApplicationTable.id))
            return [row[0] for row in result.all()]

    async def mark_app_uninstalled(self, app_id: str) -> bool:
        """Mark an application as uninstalled (update status to available).

        Args:
            app_id: Application ID to update

        Returns:
            True if updated, False if not found
        """
        await self._ensure_initialized()

        async with db_manager.get_session() as session:
            result = await session.execute(
                select(ApplicationTable).where(ApplicationTable.id == app_id)
            )
            app_row = result.first()

            if not app_row:
                return False

            app = app_row[0]
            app.status = "available"
            app.connected_server_id = None
            logger.info("Application marked as uninstalled", app_id=app_id)

        return True

    async def mark_app_installed(self, app_id: str, server_id: str) -> bool:
        """Mark an application as installed on a server.

        Args:
            app_id: Application ID to update (may be prefixed with 'casaos-')
            server_id: Server ID where the app is installed

        Returns:
            True if updated, False if not found
        """
        await self._ensure_initialized()

        async with db_manager.get_session() as session:
            # Try finding by exact ID first
            result = await session.execute(
                select(ApplicationTable).where(ApplicationTable.id == app_id)
            )
            app_row = result.first()

            # If not found and ID has prefix, try without prefix
            if not app_row and app_id.startswith("casaos-"):
                base_id = app_id[7:]  # Remove 'casaos-' prefix
                result = await session.execute(
                    select(ApplicationTable).where(ApplicationTable.id == base_id)
                )
                app_row = result.first()

            if not app_row:
                logger.warning(
                    "Application not found for marking installed", app_id=app_id
                )
                return False

            app = app_row[0]
            app.status = "installed"
            app.connected_server_id = server_id
            logger.info(
                "Application marked as installed", app_id=app.id, server_id=server_id
            )

        return True

    async def mark_apps_uninstalled_bulk(self, app_ids: list[str]) -> dict[str, Any]:
        """Mark multiple applications as uninstalled.

        Args:
            app_ids: List of application IDs to uninstall

        Returns:
            Dict with uninstalled count and details
        """
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

        self.installations[app_id] = installation
        logger.info("Application marked as installing", app_id=app_id)
        return installation
