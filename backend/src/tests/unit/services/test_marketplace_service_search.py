"""
Unit tests for services/marketplace_service.py - Search operations.

Tests search_apps method with various filters, sorting, and pagination.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.marketplace_service import MarketplaceService


@pytest.fixture
def mock_db_conn():
    """Create mock DatabaseConnection with async context manager."""
    mock_aiosqlite_conn = AsyncMock()
    mock_connection = MagicMock()
    ctx = AsyncMock()
    ctx.__aenter__.return_value = mock_aiosqlite_conn
    ctx.__aexit__.return_value = None
    mock_connection.get_connection.return_value = ctx
    return mock_connection, mock_aiosqlite_conn


def make_app_row(**overrides):
    """Create a dict row for marketplace app."""
    row = {
        "id": "test-app",
        "name": "Test App",
        "description": "A test application",
        "long_description": "A longer description",
        "version": "1.0.0",
        "category": "utility",
        "tags": '["test", "sample"]',
        "icon": "https://example.com/icon.png",
        "author": "Test Author",
        "license": "MIT",
        "maintainers": '["maintainer@example.com"]',
        "repository": "https://github.com/test/app",
        "documentation": "https://docs.example.com",
        "repo_id": "test-repo",
        "docker_config": json.dumps(
            {
                "image": "test/app:latest",
                "ports": [],
                "volumes": [],
                "environment": [],
                "restartPolicy": "unless-stopped",
                "networkMode": None,
                "privileged": False,
                "capabilities": [],
            }
        ),
        "requirements": json.dumps(
            {"architectures": ["amd64", "arm64"]}
        ),
        "install_count": 100,
        "avg_rating": 4.5,
        "rating_count": 10,
        "featured": 1,
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-06-01T00:00:00",
    }
    row.update(overrides)
    return row


class TestSearchApps:
    """Tests for search_apps method."""

    @pytest.mark.asyncio
    async def test_search_apps_returns_all_from_enabled_repos(
        self, mock_db_conn
    ):
        """search_apps should return apps only from enabled repositories."""
        mock_conn, mock_aiosqlite = mock_db_conn
        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = [make_app_row()]
        mock_aiosqlite.execute.return_value = mock_cursor

        with patch("services.marketplace_service.logger"):
            service = MarketplaceService(connection=mock_conn)
            service._initialized = True

            result = await service.search_apps()

            assert len(result) == 1
            assert result[0].id == "test-app"

    @pytest.mark.asyncio
    async def test_search_apps_filters_by_search_term(self, mock_db_conn):
        """search_apps should filter by search term in name or description."""
        mock_conn, mock_aiosqlite = mock_db_conn
        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = [make_app_row()]
        mock_aiosqlite.execute.return_value = mock_cursor

        with patch("services.marketplace_service.logger"):
            service = MarketplaceService(connection=mock_conn)
            service._initialized = True

            # Search matching name
            result = await service.search_apps(search="Test")
            assert len(result) == 1

            # Search matching description
            result = await service.search_apps(search="application")
            assert len(result) == 1

            # Search not matching
            result = await service.search_apps(search="nonexistent")
            assert len(result) == 0

    @pytest.mark.asyncio
    async def test_search_apps_case_insensitive(self, mock_db_conn):
        """search_apps should be case insensitive."""
        mock_conn, mock_aiosqlite = mock_db_conn
        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = [make_app_row()]
        mock_aiosqlite.execute.return_value = mock_cursor

        with patch("services.marketplace_service.logger"):
            service = MarketplaceService(connection=mock_conn)
            service._initialized = True

            result = await service.search_apps(search="TEST APP")
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_search_apps_filters_by_tags(self, mock_db_conn):
        """search_apps should filter by tags (all must match)."""
        mock_conn, mock_aiosqlite = mock_db_conn
        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = [make_app_row()]
        mock_aiosqlite.execute.return_value = mock_cursor

        with patch("services.marketplace_service.logger"):
            service = MarketplaceService(connection=mock_conn)
            service._initialized = True

            # Single tag match
            result = await service.search_apps(tags=["test"])
            assert len(result) == 1

            # Multiple tags match
            result = await service.search_apps(tags=["test", "sample"])
            assert len(result) == 1

            # Tag not matching
            result = await service.search_apps(tags=["nonexistent"])
            assert len(result) == 0


class TestSearchAppsSorting:
    """Tests for search_apps sorting functionality."""

    @pytest.mark.asyncio
    async def test_sorts_by_name(self, mock_db_conn):
        """search_apps should sort by name."""
        mock_conn, mock_aiosqlite = mock_db_conn

        app2 = make_app_row(
            id="another-app",
            name="Another App",
            description="Another test app",
            long_description=None,
            icon=None,
            author="Author",
            maintainers="[]",
            repository=None,
            documentation=None,
            tags="[]",
            install_count=50,
            avg_rating=3.0,
            rating_count=5,
            featured=0,
            created_at="2024-01-01T00:00:00",
            updated_at="2024-03-01T00:00:00",
        )

        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = [make_app_row(), app2]
        mock_aiosqlite.execute.return_value = mock_cursor

        with patch("services.marketplace_service.logger"):
            service = MarketplaceService(connection=mock_conn)
            service._initialized = True

            # Sort by name ascending
            result = await service.search_apps(
                sort_by="name", sort_order="asc"
            )
            assert result[0].name == "Another App"
            assert result[1].name == "Test App"

            # Sort by name descending
            result = await service.search_apps(
                sort_by="name", sort_order="desc"
            )
            assert result[0].name == "Test App"
            assert result[1].name == "Another App"

    @pytest.mark.asyncio
    async def test_sorts_by_rating(self, mock_db_conn):
        """search_apps should sort by rating."""
        mock_conn, mock_aiosqlite = mock_db_conn

        app2 = make_app_row(
            id="low-rated",
            name="Low Rated App",
            description="A low rated app",
            long_description=None,
            icon=None,
            author="Author",
            maintainers="[]",
            repository=None,
            documentation=None,
            tags="[]",
            install_count=10,
            avg_rating=2.0,
            rating_count=3,
            featured=0,
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
        )

        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = [app2, make_app_row()]
        mock_aiosqlite.execute.return_value = mock_cursor

        with patch("services.marketplace_service.logger"):
            service = MarketplaceService(connection=mock_conn)
            service._initialized = True

            result = await service.search_apps(
                sort_by="rating", sort_order="desc"
            )
            assert result[0].avg_rating == 4.5
            assert result[1].avg_rating == 2.0

    @pytest.mark.asyncio
    async def test_sorts_by_popularity(self, mock_db_conn):
        """search_apps should sort by install_count for popularity."""
        mock_conn, mock_aiosqlite = mock_db_conn
        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = [make_app_row()]
        mock_aiosqlite.execute.return_value = mock_cursor

        with patch("services.marketplace_service.logger"):
            service = MarketplaceService(connection=mock_conn)
            service._initialized = True

            result = await service.search_apps(
                sort_by="popularity", sort_order="desc"
            )
            assert len(result) == 1
            assert result[0].install_count == 100

    @pytest.mark.asyncio
    async def test_sorts_by_updated(self, mock_db_conn):
        """search_apps should sort by updated_at."""
        mock_conn, mock_aiosqlite = mock_db_conn

        app2 = make_app_row(
            id="old-app",
            name="Old App",
            description="An old app",
            long_description=None,
            icon=None,
            author="Author",
            maintainers="[]",
            repository=None,
            documentation=None,
            tags="[]",
            install_count=10,
            avg_rating=3.0,
            rating_count=3,
            featured=0,
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
        )

        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = [app2, make_app_row()]
        mock_aiosqlite.execute.return_value = mock_cursor

        with patch("services.marketplace_service.logger"):
            service = MarketplaceService(connection=mock_conn)
            service._initialized = True

            result = await service.search_apps(
                sort_by="updated", sort_order="desc"
            )
            # make_app_row() has updated_at 2024-06-01, app2 has 2024-01-01
            assert result[0].id == "test-app"
            assert result[1].id == "old-app"


class TestSearchAppsFilters:
    """Tests for search_apps database filter functionality."""

    @pytest.mark.asyncio
    async def test_filters_by_category(self, mock_db_conn):
        """search_apps should filter by category database query."""
        mock_conn, mock_aiosqlite = mock_db_conn
        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = [make_app_row()]
        mock_aiosqlite.execute.return_value = mock_cursor

        with patch("services.marketplace_service.logger"):
            service = MarketplaceService(connection=mock_conn)
            service._initialized = True

            result = await service.search_apps(category="utility")

            assert len(result) == 1
            mock_aiosqlite.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_filters_by_repo_id(self, mock_db_conn):
        """search_apps should filter by repo_id database query."""
        mock_conn, mock_aiosqlite = mock_db_conn
        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = [make_app_row()]
        mock_aiosqlite.execute.return_value = mock_cursor

        with patch("services.marketplace_service.logger"):
            service = MarketplaceService(connection=mock_conn)
            service._initialized = True

            result = await service.search_apps(repo_id="test-repo")

            assert len(result) == 1
            mock_aiosqlite.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_filters_by_featured(self, mock_db_conn):
        """search_apps should filter by featured flag database query."""
        mock_conn, mock_aiosqlite = mock_db_conn
        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = [make_app_row()]
        mock_aiosqlite.execute.return_value = mock_cursor

        with patch("services.marketplace_service.logger"):
            service = MarketplaceService(connection=mock_conn)
            service._initialized = True

            result = await service.search_apps(featured=True)

            assert len(result) == 1
            mock_aiosqlite.execute.assert_called_once()
