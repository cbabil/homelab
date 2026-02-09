"""
Unit tests for services/marketplace_service.py - App discovery and conversion.

Tests get_app, get_featured_apps, get_trending_apps, get_categories,
and _app_from_row methods.
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


class TestGetApp:
    """Tests for get_app method."""

    @pytest.mark.asyncio
    async def test_get_app_returns_app(self, mock_db_conn):
        """get_app should return app when found."""
        mock_conn, mock_aiosqlite = mock_db_conn
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = make_app_row()
        mock_aiosqlite.execute.return_value = mock_cursor

        with patch("services.marketplace_service.logger"):
            service = MarketplaceService(connection=mock_conn)
            service._initialized = True

            result = await service.get_app("test-app")

            assert result is not None
            assert result.id == "test-app"
            assert result.name == "Test App"

    @pytest.mark.asyncio
    async def test_get_app_returns_none_when_not_found(self, mock_db_conn):
        """get_app should return None when app not found."""
        mock_conn, mock_aiosqlite = mock_db_conn
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = None
        mock_aiosqlite.execute.return_value = mock_cursor

        with patch("services.marketplace_service.logger"):
            service = MarketplaceService(connection=mock_conn)
            service._initialized = True

            result = await service.get_app("nonexistent")

            assert result is None


class TestGetFeaturedApps:
    """Tests for get_featured_apps method."""

    @pytest.mark.asyncio
    async def test_get_featured_apps_calls_search_apps(self, mock_db_conn):
        """get_featured_apps should call search_apps with featured=True."""
        mock_conn, _ = mock_db_conn

        with patch("services.marketplace_service.logger"):
            service = MarketplaceService(connection=mock_conn)
            service._initialized = True

            with patch.object(
                service, "search_apps", new_callable=AsyncMock
            ) as mock_search:
                mock_search.return_value = []
                await service.get_featured_apps(limit=5)
                mock_search.assert_called_once_with(featured=True, limit=5)


class TestGetTrendingApps:
    """Tests for get_trending_apps method."""

    @pytest.mark.asyncio
    async def test_get_trending_apps_calls_search_apps(self, mock_db_conn):
        """get_trending_apps should call search_apps sorted by popularity."""
        mock_conn, _ = mock_db_conn

        with patch("services.marketplace_service.logger"):
            service = MarketplaceService(connection=mock_conn)
            service._initialized = True

            with patch.object(
                service, "search_apps", new_callable=AsyncMock
            ) as mock_search:
                mock_search.return_value = []
                await service.get_trending_apps(limit=5)
                mock_search.assert_called_once_with(
                    sort_by="popularity", sort_order="desc", limit=5
                )


class TestGetCategories:
    """Tests for get_categories method."""

    @pytest.mark.asyncio
    async def test_get_categories_returns_category_counts(self, mock_db_conn):
        """get_categories should return categories with app counts."""
        mock_conn, mock_aiosqlite = mock_db_conn
        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = [
            {"category": "utility"},
            {"category": "utility"},
            {"category": "media"},
            {"category": "networking"},
        ]
        mock_aiosqlite.execute.return_value = mock_cursor

        with patch("services.marketplace_service.logger"):
            service = MarketplaceService(connection=mock_conn)
            service._initialized = True

            result = await service.get_categories()

            assert len(result) == 3
            # Categories should be sorted alphabetically
            assert result[0]["id"] == "media"
            assert result[0]["count"] == 1
            assert result[1]["id"] == "networking"
            assert result[1]["count"] == 1
            assert result[2]["id"] == "utility"
            assert result[2]["count"] == 2

    @pytest.mark.asyncio
    async def test_get_categories_returns_empty_list(self, mock_db_conn):
        """get_categories should return empty list when no apps."""
        mock_conn, mock_aiosqlite = mock_db_conn
        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = []
        mock_aiosqlite.execute.return_value = mock_cursor

        with patch("services.marketplace_service.logger"):
            service = MarketplaceService(connection=mock_conn)
            service._initialized = True

            result = await service.get_categories()

            assert result == []


class TestSearchAppsPagination:
    """Tests for search_apps pagination functionality."""

    @pytest.mark.asyncio
    async def test_pagination(self, mock_db_conn):
        """search_apps should support pagination with limit and offset."""
        mock_conn, mock_aiosqlite = mock_db_conn

        base_docker = json.dumps(
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
        )
        base_reqs = json.dumps({"architectures": ["amd64", "arm64"]})

        rows = []
        for i in range(5):
            rows.append(
                make_app_row(
                    id=f"app-{i}",
                    name=f"App {i}",
                    description="Description",
                    long_description=None,
                    icon=None,
                    author="Author",
                    maintainers="[]",
                    repository=None,
                    documentation=None,
                    tags="[]",
                    docker_config=base_docker,
                    requirements=base_reqs,
                    install_count=i * 10,
                    avg_rating=3.0,
                    rating_count=1,
                    featured=0,
                    created_at="2024-01-01T00:00:00",
                    updated_at="2024-01-01T00:00:00",
                )
            )

        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = rows
        mock_aiosqlite.execute.return_value = mock_cursor

        with patch("services.marketplace_service.logger"):
            service = MarketplaceService(connection=mock_conn)
            service._initialized = True

            # Get first 2
            result = await service.search_apps(limit=2, offset=0)
            assert len(result) == 2

            # Get next 2
            result = await service.search_apps(limit=2, offset=2)
            assert len(result) == 2

            # Get last 1
            result = await service.search_apps(limit=2, offset=4)
            assert len(result) == 1


class TestAppFromRow:
    """Tests for _app_from_row static method."""

    def test_converts_app_row_to_model(self):
        """_app_from_row should convert dict row to model."""
        row = make_app_row()
        result = MarketplaceService._app_from_row(row)

        assert result.id == "test-app"
        assert result.name == "Test App"
        assert result.description == "A test application"
        assert result.version == "1.0.0"
        assert result.category == "utility"
        assert result.tags == ["test", "sample"]
        assert result.author == "Test Author"
        assert result.install_count == 100
        assert result.avg_rating == 4.5
        assert result.featured is True

    def test_handles_null_requirements(self):
        """_app_from_row should handle null requirements with defaults."""
        row = make_app_row(requirements=None)
        result = MarketplaceService._app_from_row(row)

        assert result.requirements.architectures == ["amd64", "arm64"]

    def test_handles_empty_tags(self):
        """_app_from_row should handle empty tags."""
        row = make_app_row(tags=None)
        result = MarketplaceService._app_from_row(row)

        assert result.tags == []

    def test_handles_null_optional_fields(self):
        """_app_from_row should handle null optional fields."""
        row = make_app_row(
            install_count=None,
            avg_rating=None,
            rating_count=None,
            featured=None,
        )
        result = MarketplaceService._app_from_row(row)

        assert result.install_count == 0
        assert result.avg_rating == 0.0
        assert result.rating_count == 0
        assert result.featured is False
