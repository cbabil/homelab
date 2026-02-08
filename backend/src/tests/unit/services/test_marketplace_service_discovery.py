"""
Unit tests for services/marketplace_service.py - App discovery and conversion.

Tests get_app, get_featured_apps, get_trending_apps, get_categories,
and _app_from_table methods.
"""

import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.marketplace import (
    MarketplaceAppTable,
    MarketplaceRepoTable,
)
from services.marketplace_service import MarketplaceService


@pytest.fixture
def mock_db_session():
    """Create mock database session with async context manager."""
    session = AsyncMock()
    context_manager = AsyncMock()
    context_manager.__aenter__.return_value = session
    context_manager.__aexit__.return_value = None
    return session, context_manager


@pytest.fixture
def mock_app_table():
    """Create mock MarketplaceAppTable row."""
    app = MagicMock(spec=MarketplaceAppTable)
    app.id = "test-app"
    app.name = "Test App"
    app.description = "A test application"
    app.long_description = "A longer description"
    app.version = "1.0.0"
    app.category = "utility"
    app.tags = '["test", "sample"]'
    app.icon = "https://example.com/icon.png"
    app.author = "Test Author"
    app.license = "MIT"
    app.maintainers = '["maintainer@example.com"]'
    app.repository = "https://github.com/test/app"
    app.documentation = "https://docs.example.com"
    app.repo_id = "test-repo"
    app.docker_config = json.dumps(
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
    app.requirements = json.dumps(
        {
            "architectures": ["amd64", "arm64"],
        }
    )
    app.install_count = 100
    app.avg_rating = 4.5
    app.rating_count = 10
    app.featured = True
    app.created_at = datetime(2024, 1, 1, tzinfo=UTC)
    app.updated_at = datetime(2024, 6, 1, tzinfo=UTC)
    return app


class TestGetApp:
    """Tests for get_app method."""

    @pytest.mark.asyncio
    async def test_get_app_returns_app(self, mock_db_session, mock_app_table):
        """get_app should return app when found."""
        session, context_manager = mock_db_session
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_app_table
        session.execute = AsyncMock(return_value=mock_result)

        with (
            patch("services.marketplace_service.logger"),
            patch("services.marketplace_service.db_manager") as mock_db,
            patch("services.marketplace_service.initialize_marketplace_database"),
        ):
            mock_db.get_session.return_value = context_manager
            service = MarketplaceService()
            service._initialized = True

            result = await service.get_app("test-app")

            assert result is not None
            assert result.id == "test-app"
            assert result.name == "Test App"

    @pytest.mark.asyncio
    async def test_get_app_returns_none_when_not_found(self, mock_db_session):
        """get_app should return None when app not found."""
        session, context_manager = mock_db_session
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute = AsyncMock(return_value=mock_result)

        with (
            patch("services.marketplace_service.logger"),
            patch("services.marketplace_service.db_manager") as mock_db,
            patch("services.marketplace_service.initialize_marketplace_database"),
        ):
            mock_db.get_session.return_value = context_manager
            service = MarketplaceService()
            service._initialized = True

            result = await service.get_app("nonexistent")

            assert result is None


class TestGetFeaturedApps:
    """Tests for get_featured_apps method."""

    @pytest.mark.asyncio
    async def test_get_featured_apps_calls_search_apps(self, mock_db_session):
        """get_featured_apps should call search_apps with featured=True."""
        session, context_manager = mock_db_session
        mock_result = MagicMock()
        mock_result.all.return_value = []
        session.execute = AsyncMock(return_value=mock_result)

        with (
            patch("services.marketplace_service.logger"),
            patch("services.marketplace_service.db_manager") as mock_db,
            patch("services.marketplace_service.initialize_marketplace_database"),
        ):
            mock_db.get_session.return_value = context_manager
            service = MarketplaceService()
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
    async def test_get_trending_apps_calls_search_apps(self, mock_db_session):
        """get_trending_apps should call search_apps sorted by popularity."""
        session, context_manager = mock_db_session
        mock_result = MagicMock()
        mock_result.all.return_value = []
        session.execute = AsyncMock(return_value=mock_result)

        with (
            patch("services.marketplace_service.logger"),
            patch("services.marketplace_service.db_manager") as mock_db,
            patch("services.marketplace_service.initialize_marketplace_database"),
        ):
            mock_db.get_session.return_value = context_manager
            service = MarketplaceService()
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
    async def test_get_categories_returns_category_counts(self, mock_db_session):
        """get_categories should return categories with app counts."""
        session, context_manager = mock_db_session
        mock_result = MagicMock()
        mock_result.all.return_value = [
            ("utility",),
            ("utility",),
            ("media",),
            ("networking",),
        ]
        session.execute = AsyncMock(return_value=mock_result)

        with (
            patch("services.marketplace_service.logger"),
            patch("services.marketplace_service.db_manager") as mock_db,
            patch("services.marketplace_service.initialize_marketplace_database"),
        ):
            mock_db.get_session.return_value = context_manager
            service = MarketplaceService()
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
    async def test_get_categories_returns_empty_list(self, mock_db_session):
        """get_categories should return empty list when no apps."""
        session, context_manager = mock_db_session
        mock_result = MagicMock()
        mock_result.all.return_value = []
        session.execute = AsyncMock(return_value=mock_result)

        with (
            patch("services.marketplace_service.logger"),
            patch("services.marketplace_service.db_manager") as mock_db,
            patch("services.marketplace_service.initialize_marketplace_database"),
        ):
            mock_db.get_session.return_value = context_manager
            service = MarketplaceService()
            service._initialized = True

            result = await service.get_categories()

            assert result == []


class TestSearchAppsPagination:
    """Tests for search_apps pagination functionality."""

    @pytest.mark.asyncio
    async def test_pagination(self, mock_db_session, mock_app_table):
        """search_apps should support pagination with limit and offset."""
        session, context_manager = mock_db_session

        mock_repo = MagicMock(spec=MarketplaceRepoTable)
        mock_repo.id = "test-repo"
        mock_repo.enabled = True

        # Create multiple apps
        apps = []
        for i in range(5):
            app = MagicMock(spec=MarketplaceAppTable)
            app.id = f"app-{i}"
            app.name = f"App {i}"
            app.description = "Description"
            app.long_description = None
            app.version = "1.0.0"
            app.category = "utility"
            app.tags = "[]"
            app.icon = None
            app.author = "Author"
            app.license = "MIT"
            app.maintainers = "[]"
            app.repository = None
            app.documentation = None
            app.repo_id = "test-repo"
            app.docker_config = mock_app_table.docker_config
            app.requirements = mock_app_table.requirements
            app.install_count = i * 10
            app.avg_rating = 3.0
            app.rating_count = 1
            app.featured = False
            app.created_at = datetime(2024, 1, 1, tzinfo=UTC)
            app.updated_at = datetime(2024, 1, 1, tzinfo=UTC)
            apps.append((app, mock_repo))

        mock_result = MagicMock()
        mock_result.all.return_value = apps
        session.execute = AsyncMock(return_value=mock_result)

        with (
            patch("services.marketplace_service.logger"),
            patch("services.marketplace_service.db_manager") as mock_db,
            patch("services.marketplace_service.initialize_marketplace_database"),
        ):
            mock_db.get_session.return_value = context_manager
            service = MarketplaceService()
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


class TestAppFromTable:
    """Tests for _app_from_table static method."""

    def test_converts_app_table_to_model(self, mock_app_table):
        """_app_from_table should convert table row to model."""
        result = MarketplaceService._app_from_table(mock_app_table)

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

    def test_handles_null_requirements(self, mock_app_table):
        """_app_from_table should handle null requirements with defaults."""
        mock_app_table.requirements = None

        result = MarketplaceService._app_from_table(mock_app_table)

        assert result.requirements.architectures == ["amd64", "arm64"]

    def test_handles_empty_tags(self, mock_app_table):
        """_app_from_table should handle empty tags."""
        mock_app_table.tags = None

        result = MarketplaceService._app_from_table(mock_app_table)

        assert result.tags == []

    def test_handles_null_optional_fields(self, mock_app_table):
        """_app_from_table should handle null optional fields."""
        mock_app_table.install_count = None
        mock_app_table.avg_rating = None
        mock_app_table.rating_count = None
        mock_app_table.featured = None

        result = MarketplaceService._app_from_table(mock_app_table)

        assert result.install_count == 0
        assert result.avg_rating == 0.0
        assert result.rating_count == 0
        assert result.featured is False
