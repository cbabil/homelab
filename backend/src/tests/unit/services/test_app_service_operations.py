"""
Unit tests for services/app_service.py - Search Operations

Tests search_apps and get_app_by_id methods.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.app import (
    App,
    AppCategory,
    AppFilter,
    AppRequirements,
    AppStatus,
)
from services.app_service import AppService


@pytest.fixture
def mock_db_conn():
    """Create mock DatabaseConnection with get_connection context manager."""
    mock_aiosqlite_conn = AsyncMock()
    mock_connection = MagicMock()
    ctx = AsyncMock()
    ctx.__aenter__.return_value = mock_aiosqlite_conn
    ctx.__aexit__.return_value = None
    mock_connection.get_connection.return_value = ctx
    return mock_connection, mock_aiosqlite_conn


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
def sample_app_row():
    """Create dict-like row as returned by aiosqlite JOIN query."""
    return {
        "id": "plex",
        "name": "Plex",
        "description": "Media server",
        "long_description": None,
        "version": "1.0.0",
        "category_id": "media",
        "tags": '["media", "streaming"]',
        "icon": None,
        "screenshots": None,
        "author": "Plex Inc",
        "repository": None,
        "documentation": None,
        "license": "MIT",
        "requirements": None,
        "status": "available",
        "install_count": 100,
        "rating": 4.5,
        "featured": 1,
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-06-01T00:00:00",
        "connected_server_id": None,
        "cat_id": "media",
        "cat_name": "Media",
        "cat_desc": "Media applications",
        "cat_icon": "Video",
        "cat_color": "text-blue-500",
    }


class TestSearchApps:
    """Tests for search_apps method."""

    @pytest.mark.asyncio
    async def test_search_apps_returns_result(
        self, mock_db_conn, sample_app_row
    ):
        """search_apps should return AppSearchResult."""
        mock_conn, mock_aiosqlite = mock_db_conn

        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = [sample_app_row]
        mock_aiosqlite.execute.return_value = mock_cursor

        mock_log = MagicMock()
        with patch("services.app_service.logger"):
            service = AppService(connection=mock_conn, log_service=mock_log)
            result = await service.search_apps(AppFilter())

            assert result.total == 1
            assert len(result.apps) == 1
            assert result.page == 1

    @pytest.mark.asyncio
    async def test_search_apps_logs_success(
        self, mock_db_conn, sample_app_row
    ):
        """search_apps should log completion."""
        mock_conn, mock_aiosqlite = mock_db_conn

        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = [sample_app_row]
        mock_aiosqlite.execute.return_value = mock_cursor

        mock_log = MagicMock()
        with patch("services.app_service.logger") as mock_logger:
            service = AppService(connection=mock_conn, log_service=mock_log)
            await service.search_apps(AppFilter())

            mock_logger.info.assert_any_call(
                "Application search completed", total=1
            )

    @pytest.mark.asyncio
    async def test_search_apps_empty_logs_entry(self, mock_db_conn):
        """search_apps should log entry when no results found."""
        mock_conn, mock_aiosqlite = mock_db_conn

        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = []
        mock_aiosqlite.execute.return_value = mock_cursor

        mock_log = MagicMock()
        mock_log.create_log_entry = AsyncMock()

        with patch("services.app_service.logger"):
            service = AppService(connection=mock_conn, log_service=mock_log)
            result = await service.search_apps(
                AppFilter(search="nonexistent")
            )

            assert result.total == 0
            mock_log.create_log_entry.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_apps_log_entry_error(self, mock_db_conn):
        """search_apps should warn on log entry error."""
        mock_conn, mock_aiosqlite = mock_db_conn

        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = []
        mock_aiosqlite.execute.return_value = mock_cursor

        mock_log = MagicMock()
        mock_log.create_log_entry = AsyncMock(
            side_effect=Exception("Log error")
        )

        with patch("services.app_service.logger") as mock_logger:
            service = AppService(connection=mock_conn, log_service=mock_log)
            await service.search_apps(AppFilter())

            mock_logger.warning.assert_called()

    @pytest.mark.asyncio
    async def test_search_apps_with_filters(
        self, mock_db_conn, sample_app_row
    ):
        """search_apps should apply filters correctly."""
        mock_conn, mock_aiosqlite = mock_db_conn

        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = [sample_app_row]
        mock_aiosqlite.execute.return_value = mock_cursor

        mock_log = MagicMock()
        with patch("services.app_service.logger"):
            service = AppService(connection=mock_conn, log_service=mock_log)
            result = await service.search_apps(
                AppFilter(category="media", featured=True)
            )

            assert result.total == 1
            assert result.filters.category == "media"

    @pytest.mark.asyncio
    async def test_search_apps_limit_handling(
        self, mock_db_conn, sample_app_row
    ):
        """search_apps should set correct limit in result."""
        mock_conn, mock_aiosqlite = mock_db_conn

        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = [sample_app_row]
        mock_aiosqlite.execute.return_value = mock_cursor

        mock_log = MagicMock()
        with patch("services.app_service.logger"):
            service = AppService(connection=mock_conn, log_service=mock_log)
            result = await service.search_apps(AppFilter())

            assert result.limit == 1


class TestGetAppById:
    """Tests for get_app_by_id method."""

    @pytest.mark.asyncio
    async def test_get_app_by_id_found(self, mock_db_conn, sample_app_row):
        """get_app_by_id should return app when found."""
        mock_conn, mock_aiosqlite = mock_db_conn

        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = sample_app_row
        mock_aiosqlite.execute.return_value = mock_cursor

        mock_log = MagicMock()
        with patch("services.app_service.logger"):
            service = AppService(connection=mock_conn, log_service=mock_log)
            result = await service.get_app_by_id("plex")

            assert result is not None
            assert result.id == "plex"

    @pytest.mark.asyncio
    async def test_get_app_by_id_not_found(self, mock_db_conn):
        """get_app_by_id should return None when not found."""
        mock_conn, mock_aiosqlite = mock_db_conn

        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = None
        mock_aiosqlite.execute.return_value = mock_cursor

        mock_log = MagicMock()
        with patch("services.app_service.logger") as mock_logger:
            service = AppService(connection=mock_conn, log_service=mock_log)
            result = await service.get_app_by_id("nonexistent")

            assert result is None
            mock_logger.warning.assert_called_with(
                "Application not found", app_id="nonexistent"
            )

    @pytest.mark.asyncio
    async def test_get_app_by_id_logs_success(
        self, mock_db_conn, sample_app_row
    ):
        """get_app_by_id should log retrieval."""
        mock_conn, mock_aiosqlite = mock_db_conn

        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = sample_app_row
        mock_aiosqlite.execute.return_value = mock_cursor

        mock_log = MagicMock()
        with patch("services.app_service.logger") as mock_logger:
            service = AppService(connection=mock_conn, log_service=mock_log)
            await service.get_app_by_id("plex")

            mock_logger.debug.assert_called_with(
                "Retrieved application", app_id="plex"
            )
