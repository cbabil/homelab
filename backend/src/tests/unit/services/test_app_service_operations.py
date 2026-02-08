"""
Unit tests for services/app_service.py - Search Operations

Tests search_apps and get_app_by_id methods.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.app import (
    App,
    AppCategory,
    AppCategoryTable,
    AppFilter,
    ApplicationTable,
    AppRequirements,
    AppStatus,
)
from services.app_service import AppService


@pytest.fixture
def mock_db_session():
    """Create mock database session with async context manager."""
    session = AsyncMock()
    context_manager = AsyncMock()
    context_manager.__aenter__.return_value = session
    context_manager.__aexit__.return_value = None
    return session, context_manager


@pytest.fixture
def sample_category():
    """Create sample AppCategory for testing."""
    return AppCategory(
        id="media",
        name="Media",
        description="Media applications",
        icon="Video",
        color="text-blue-500",
    )


@pytest.fixture
def sample_app(sample_category):
    """Create sample App for testing."""
    return App(
        id="plex",
        name="Plex",
        description="Media server",
        version="1.0.0",
        category=sample_category,
        tags=["media", "streaming"],
        author="Plex Inc",
        license="MIT",
        requirements=AppRequirements(),
        status=AppStatus.AVAILABLE,
        install_count=100,
        rating=4.5,
        featured=True,
        created_at="2024-01-01T00:00:00Z",
        updated_at="2024-06-01T00:00:00Z",
    )


@pytest.fixture
def sample_app_table():
    """Create mock ApplicationTable row."""
    app = MagicMock(spec=ApplicationTable)
    app.id = "plex"
    app.name = "Plex"
    app.description = "Media server"
    app.long_description = None
    app.version = "1.0.0"
    app.category_id = "media"
    app.tags = '["media", "streaming"]'
    app.icon = None
    app.screenshots = None
    app.author = "Plex Inc"
    app.repository = None
    app.documentation = None
    app.license = "MIT"
    app.requirements = None
    app.status = "available"
    app.install_count = 100
    app.rating = 4.5
    app.featured = True
    app.created_at = datetime(2024, 1, 1, tzinfo=UTC)
    app.updated_at = datetime(2024, 6, 1, tzinfo=UTC)
    app.connected_server_id = None
    return app


@pytest.fixture
def sample_category_table():
    """Create mock AppCategoryTable row."""
    cat = MagicMock(spec=AppCategoryTable)
    cat.id = "media"
    cat.name = "Media"
    cat.description = "Media applications"
    cat.icon = "Video"
    cat.color = "text-blue-500"
    return cat


class TestSearchApps:
    """Tests for search_apps method."""

    @pytest.mark.asyncio
    async def test_search_apps_returns_result(
        self, mock_db_session, sample_app_table, sample_category_table
    ):
        """search_apps should return AppSearchResult."""
        session, context_manager = mock_db_session
        mock_result = MagicMock()
        mock_result.all.return_value = [(sample_app_table, sample_category_table)]
        session.execute = AsyncMock(return_value=mock_result)

        with (
            patch("services.app_service.logger"),
            patch("services.app_service.initialize_app_database"),
            patch("services.app_service.db_manager") as mock_db,
        ):
            mock_db.get_session.return_value = context_manager

            service = AppService()
            result = await service.search_apps(AppFilter())

            assert result.total == 1
            assert len(result.apps) == 1
            assert result.page == 1

    @pytest.mark.asyncio
    async def test_search_apps_logs_success(
        self, mock_db_session, sample_app_table, sample_category_table
    ):
        """search_apps should log completion."""
        session, context_manager = mock_db_session
        mock_result = MagicMock()
        mock_result.all.return_value = [(sample_app_table, sample_category_table)]
        session.execute = AsyncMock(return_value=mock_result)

        with (
            patch("services.app_service.logger") as mock_logger,
            patch("services.app_service.initialize_app_database"),
            patch("services.app_service.db_manager") as mock_db,
        ):
            mock_db.get_session.return_value = context_manager

            service = AppService()
            await service.search_apps(AppFilter())

            mock_logger.info.assert_any_call("Application search completed", total=1)

    @pytest.mark.asyncio
    async def test_search_apps_empty_logs_entry(self, mock_db_session):
        """search_apps should log entry when no results found."""
        session, context_manager = mock_db_session
        mock_result = MagicMock()
        mock_result.all.return_value = []
        session.execute = AsyncMock(return_value=mock_result)

        with (
            patch("services.app_service.logger"),
            patch("services.app_service.initialize_app_database"),
            patch("services.app_service.db_manager") as mock_db,
            patch("services.app_service.log_service") as mock_log,
        ):
            mock_db.get_session.return_value = context_manager
            mock_log.create_log_entry = AsyncMock()

            service = AppService()
            result = await service.search_apps(AppFilter(search="nonexistent"))

            assert result.total == 0
            mock_log.create_log_entry.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_apps_log_entry_error(self, mock_db_session):
        """search_apps should warn on log entry error."""
        session, context_manager = mock_db_session
        mock_result = MagicMock()
        mock_result.all.return_value = []
        session.execute = AsyncMock(return_value=mock_result)

        with (
            patch("services.app_service.logger") as mock_logger,
            patch("services.app_service.initialize_app_database"),
            patch("services.app_service.db_manager") as mock_db,
            patch("services.app_service.log_service") as mock_log,
        ):
            mock_db.get_session.return_value = context_manager
            mock_log.create_log_entry = AsyncMock(side_effect=Exception("Log error"))

            service = AppService()
            await service.search_apps(AppFilter())

            mock_logger.warning.assert_called()

    @pytest.mark.asyncio
    async def test_search_apps_with_filters(
        self, mock_db_session, sample_app_table, sample_category_table
    ):
        """search_apps should apply filters correctly."""
        session, context_manager = mock_db_session
        mock_result = MagicMock()
        mock_result.all.return_value = [(sample_app_table, sample_category_table)]
        session.execute = AsyncMock(return_value=mock_result)

        with (
            patch("services.app_service.logger"),
            patch("services.app_service.initialize_app_database"),
            patch("services.app_service.db_manager") as mock_db,
        ):
            mock_db.get_session.return_value = context_manager

            service = AppService()
            result = await service.search_apps(
                AppFilter(category="media", featured=True)
            )

            assert result.total == 1
            assert result.filters.category == "media"

    @pytest.mark.asyncio
    async def test_search_apps_limit_handling(
        self, mock_db_session, sample_app_table, sample_category_table
    ):
        """search_apps should set correct limit in result."""
        session, context_manager = mock_db_session
        mock_result = MagicMock()
        mock_result.all.return_value = [(sample_app_table, sample_category_table)]
        session.execute = AsyncMock(return_value=mock_result)

        with (
            patch("services.app_service.logger"),
            patch("services.app_service.initialize_app_database"),
            patch("services.app_service.db_manager") as mock_db,
        ):
            mock_db.get_session.return_value = context_manager

            service = AppService()
            result = await service.search_apps(AppFilter())

            assert result.limit == 1


class TestGetAppById:
    """Tests for get_app_by_id method."""

    @pytest.mark.asyncio
    async def test_get_app_by_id_found(
        self, mock_db_session, sample_app_table, sample_category_table
    ):
        """get_app_by_id should return app when found."""
        session, context_manager = mock_db_session
        mock_result = MagicMock()
        mock_result.first.return_value = (sample_app_table, sample_category_table)
        session.execute = AsyncMock(return_value=mock_result)

        with (
            patch("services.app_service.logger"),
            patch("services.app_service.initialize_app_database"),
            patch("services.app_service.db_manager") as mock_db,
        ):
            mock_db.get_session.return_value = context_manager

            service = AppService()
            result = await service.get_app_by_id("plex")

            assert result is not None
            assert result.id == "plex"

    @pytest.mark.asyncio
    async def test_get_app_by_id_not_found(self, mock_db_session):
        """get_app_by_id should return None when not found."""
        session, context_manager = mock_db_session
        mock_result = MagicMock()
        mock_result.first.return_value = None
        session.execute = AsyncMock(return_value=mock_result)

        with (
            patch("services.app_service.logger") as mock_logger,
            patch("services.app_service.initialize_app_database"),
            patch("services.app_service.db_manager") as mock_db,
        ):
            mock_db.get_session.return_value = context_manager

            service = AppService()
            result = await service.get_app_by_id("nonexistent")

            assert result is None
            mock_logger.warning.assert_called_with(
                "Application not found", app_id="nonexistent"
            )

    @pytest.mark.asyncio
    async def test_get_app_by_id_logs_success(
        self, mock_db_session, sample_app_table, sample_category_table
    ):
        """get_app_by_id should log retrieval."""
        session, context_manager = mock_db_session
        mock_result = MagicMock()
        mock_result.first.return_value = (sample_app_table, sample_category_table)
        session.execute = AsyncMock(return_value=mock_result)

        with (
            patch("services.app_service.logger") as mock_logger,
            patch("services.app_service.initialize_app_database"),
            patch("services.app_service.db_manager") as mock_db,
        ):
            mock_db.get_session.return_value = context_manager

            service = AppService()
            await service.get_app_by_id("plex")

            mock_logger.debug.assert_called_with("Retrieved application", app_id="plex")
