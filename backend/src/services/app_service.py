"""Application Service

Provides data access and business logic for the application marketplace."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Dict, Any, List, Optional

import structlog
from sqlalchemy import select

from database.connection import db_manager
from init_db.schema_apps import initialize_app_database
from models.app import (
    App,
    AppFilter,
    AppInstallation,
    AppSearchResult,
    AppStatus,
    ApplicationTable,
    AppCategoryTable,
)
from services.service_log import log_service
from exceptions import ApplicationLogWriteError
from app_logging import build_empty_search_log

logger = structlog.get_logger("app_service")


class AppService:
    """Service for managing applications and installations."""

    def __init__(self) -> None:
        self._initialized = False
        self.installations: Dict[str, AppInstallation] = {}
        logger.info("Application service initialized")

    async def _ensure_initialized(self) -> None:
        if not self._initialized:
            await initialize_app_database()
            self._initialized = True

    async def _fetch_all_apps(self) -> List[App]:
        """Fetch all applications with their categories from the database."""

        await self._ensure_initialized()

        async with db_manager.get_session() as session:
            result = await session.execute(
                select(ApplicationTable, AppCategoryTable)
                .join(AppCategoryTable, ApplicationTable.category_id == AppCategoryTable.id)
            )
            rows = result.all()

        apps: List[App] = [App.from_table(app_row, category_row) for app_row, category_row in rows]
        logger.debug("Fetched applications from database", count=len(apps))
        return apps

    @staticmethod
    def _apply_filters(apps: List[App], filters: AppFilter) -> List[App]:
        """Apply in-memory filtering to the application list."""

        filtered: List[App] = []
        search_term = filters.search.lower() if filters.search else None
        required_tags = set(tag.lower() for tag in filters.tags or [])

        for app in apps:
            if filters.category and app.category.id != filters.category:
                continue

            if filters.status and app.status != filters.status:
                continue

            if filters.featured is not None and bool(app.featured) != filters.featured:
                continue

            if required_tags and not required_tags.issubset({tag.lower() for tag in app.tags}):
                continue

            if search_term and search_term not in app.name.lower() and search_term not in app.description.lower():
                continue

            filtered.append(app)

        return filtered

    @staticmethod
    def _apply_sorting(apps: List[App], filters: AppFilter) -> None:
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
            apps.sort(key=lambda app: AppService._iso_to_datetime(app.updated_at), reverse=reverse)
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
            metadata_filters = filters.model_dump(exclude_none=True, mode='json')
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

    async def get_app_by_id(self, app_id: str) -> Optional[App]:
        """Retrieve a single application by identifier."""

        await self._ensure_initialized()

        async with db_manager.get_session() as session:
            result = await session.execute(
                select(ApplicationTable, AppCategoryTable)
                .join(AppCategoryTable, ApplicationTable.category_id == AppCategoryTable.id)
                .where(ApplicationTable.id == app_id)
            )
            row = result.first()

        if not row:
            logger.warning("Application not found", app_id=app_id)
            return None

        app = App.from_table(row[0], row[1])
        logger.debug("Retrieved application", app_id=app_id)
        return app

    async def install_app(self, app_id: str, config: Optional[Dict[str, Any]] = None) -> AppInstallation:
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
