"""
Unit tests for services/marketplace_service.py - Search operations.

Tests search_apps method with various filters, sorting, and pagination.
"""

import json
import pytest
from datetime import datetime, UTC
from unittest.mock import AsyncMock, MagicMock, patch

from services.marketplace_service import MarketplaceService
from models.marketplace import (
    MarketplaceAppTable,
    MarketplaceRepoTable,
)


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
    app.docker_config = json.dumps({
        "image": "test/app:latest",
        "ports": [],
        "volumes": [],
        "environment": [],
        "restartPolicy": "unless-stopped",
        "networkMode": None,
        "privileged": False,
        "capabilities": [],
    })
    app.requirements = json.dumps({
        "architectures": ["amd64", "arm64"],
    })
    app.install_count = 100
    app.avg_rating = 4.5
    app.rating_count = 10
    app.featured = True
    app.created_at = datetime(2024, 1, 1, tzinfo=UTC)
    app.updated_at = datetime(2024, 6, 1, tzinfo=UTC)
    return app


@pytest.fixture
def mock_repo_table():
    """Create mock MarketplaceRepoTable row."""
    repo = MagicMock(spec=MarketplaceRepoTable)
    repo.id = "test-repo"
    repo.enabled = True
    return repo


class TestSearchApps:
    """Tests for search_apps method."""

    @pytest.mark.asyncio
    async def test_search_apps_returns_all_from_enabled_repos(
        self, mock_db_session, mock_app_table, mock_repo_table
    ):
        """search_apps should return apps only from enabled repositories."""
        session, context_manager = mock_db_session
        mock_result = MagicMock()
        mock_result.all.return_value = [(mock_app_table, mock_repo_table)]
        session.execute = AsyncMock(return_value=mock_result)

        with (
            patch("services.marketplace_service.logger"),
            patch("services.marketplace_service.db_manager") as mock_db,
            patch("services.marketplace_service.initialize_marketplace_database"),
        ):
            mock_db.get_session.return_value = context_manager
            service = MarketplaceService()
            service._initialized = True

            result = await service.search_apps()

            assert len(result) == 1
            assert result[0].id == "test-app"

    @pytest.mark.asyncio
    async def test_search_apps_filters_by_search_term(
        self, mock_db_session, mock_app_table, mock_repo_table
    ):
        """search_apps should filter by search term in name or description."""
        session, context_manager = mock_db_session
        mock_result = MagicMock()
        mock_result.all.return_value = [(mock_app_table, mock_repo_table)]
        session.execute = AsyncMock(return_value=mock_result)

        with (
            patch("services.marketplace_service.logger"),
            patch("services.marketplace_service.db_manager") as mock_db,
            patch("services.marketplace_service.initialize_marketplace_database"),
        ):
            mock_db.get_session.return_value = context_manager
            service = MarketplaceService()
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
    async def test_search_apps_case_insensitive(
        self, mock_db_session, mock_app_table, mock_repo_table
    ):
        """search_apps should be case insensitive."""
        session, context_manager = mock_db_session
        mock_result = MagicMock()
        mock_result.all.return_value = [(mock_app_table, mock_repo_table)]
        session.execute = AsyncMock(return_value=mock_result)

        with (
            patch("services.marketplace_service.logger"),
            patch("services.marketplace_service.db_manager") as mock_db,
            patch("services.marketplace_service.initialize_marketplace_database"),
        ):
            mock_db.get_session.return_value = context_manager
            service = MarketplaceService()
            service._initialized = True

            result = await service.search_apps(search="TEST APP")
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_search_apps_filters_by_tags(
        self, mock_db_session, mock_app_table, mock_repo_table
    ):
        """search_apps should filter by tags (all must match)."""
        session, context_manager = mock_db_session
        mock_result = MagicMock()
        mock_result.all.return_value = [(mock_app_table, mock_repo_table)]
        session.execute = AsyncMock(return_value=mock_result)

        with (
            patch("services.marketplace_service.logger"),
            patch("services.marketplace_service.db_manager") as mock_db,
            patch("services.marketplace_service.initialize_marketplace_database"),
        ):
            mock_db.get_session.return_value = context_manager
            service = MarketplaceService()
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
    async def test_sorts_by_name(
        self, mock_db_session, mock_app_table, mock_repo_table
    ):
        """search_apps should sort by name."""
        session, context_manager = mock_db_session

        app2 = MagicMock(spec=MarketplaceAppTable)
        app2.id = "another-app"
        app2.name = "Another App"
        app2.description = "Another test app"
        app2.long_description = None
        app2.version = "1.0.0"
        app2.category = "utility"
        app2.tags = "[]"
        app2.icon = None
        app2.author = "Author"
        app2.license = "MIT"
        app2.maintainers = "[]"
        app2.repository = None
        app2.documentation = None
        app2.repo_id = "test-repo"
        app2.docker_config = mock_app_table.docker_config
        app2.requirements = mock_app_table.requirements
        app2.install_count = 50
        app2.avg_rating = 3.0
        app2.rating_count = 5
        app2.featured = False
        app2.created_at = datetime(2024, 1, 1, tzinfo=UTC)
        app2.updated_at = datetime(2024, 3, 1, tzinfo=UTC)

        mock_result = MagicMock()
        mock_result.all.return_value = [
            (mock_app_table, mock_repo_table),
            (app2, mock_repo_table),
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

            # Sort by name ascending
            result = await service.search_apps(sort_by="name", sort_order="asc")
            assert result[0].name == "Another App"
            assert result[1].name == "Test App"

            # Sort by name descending
            result = await service.search_apps(sort_by="name", sort_order="desc")
            assert result[0].name == "Test App"
            assert result[1].name == "Another App"

    @pytest.mark.asyncio
    async def test_sorts_by_rating(
        self, mock_db_session, mock_app_table, mock_repo_table
    ):
        """search_apps should sort by rating."""
        session, context_manager = mock_db_session

        app2 = MagicMock(spec=MarketplaceAppTable)
        app2.id = "low-rated"
        app2.name = "Low Rated App"
        app2.description = "A low rated app"
        app2.long_description = None
        app2.version = "1.0.0"
        app2.category = "utility"
        app2.tags = "[]"
        app2.icon = None
        app2.author = "Author"
        app2.license = "MIT"
        app2.maintainers = "[]"
        app2.repository = None
        app2.documentation = None
        app2.repo_id = "test-repo"
        app2.docker_config = mock_app_table.docker_config
        app2.requirements = mock_app_table.requirements
        app2.install_count = 10
        app2.avg_rating = 2.0
        app2.rating_count = 3
        app2.featured = False
        app2.created_at = datetime(2024, 1, 1, tzinfo=UTC)
        app2.updated_at = datetime(2024, 1, 1, tzinfo=UTC)

        mock_result = MagicMock()
        mock_result.all.return_value = [
            (app2, mock_repo_table),
            (mock_app_table, mock_repo_table),
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

            result = await service.search_apps(sort_by="rating", sort_order="desc")
            assert result[0].avg_rating == 4.5
            assert result[1].avg_rating == 2.0

    @pytest.mark.asyncio
    async def test_sorts_by_popularity(
        self, mock_db_session, mock_app_table, mock_repo_table
    ):
        """search_apps should sort by install_count for popularity."""
        session, context_manager = mock_db_session
        mock_result = MagicMock()
        mock_result.all.return_value = [(mock_app_table, mock_repo_table)]
        session.execute = AsyncMock(return_value=mock_result)

        with (
            patch("services.marketplace_service.logger"),
            patch("services.marketplace_service.db_manager") as mock_db,
            patch("services.marketplace_service.initialize_marketplace_database"),
        ):
            mock_db.get_session.return_value = context_manager
            service = MarketplaceService()
            service._initialized = True

            result = await service.search_apps(sort_by="popularity", sort_order="desc")
            assert len(result) == 1
            assert result[0].install_count == 100

    @pytest.mark.asyncio
    async def test_sorts_by_updated(
        self, mock_db_session, mock_app_table, mock_repo_table
    ):
        """search_apps should sort by updated_at."""
        session, context_manager = mock_db_session

        app2 = MagicMock(spec=MarketplaceAppTable)
        app2.id = "old-app"
        app2.name = "Old App"
        app2.description = "An old app"
        app2.long_description = None
        app2.version = "1.0.0"
        app2.category = "utility"
        app2.tags = "[]"
        app2.icon = None
        app2.author = "Author"
        app2.license = "MIT"
        app2.maintainers = "[]"
        app2.repository = None
        app2.documentation = None
        app2.repo_id = "test-repo"
        app2.docker_config = mock_app_table.docker_config
        app2.requirements = mock_app_table.requirements
        app2.install_count = 10
        app2.avg_rating = 3.0
        app2.rating_count = 3
        app2.featured = False
        app2.created_at = datetime(2024, 1, 1, tzinfo=UTC)
        app2.updated_at = datetime(2024, 1, 1, tzinfo=UTC)

        mock_result = MagicMock()
        mock_result.all.return_value = [
            (app2, mock_repo_table),
            (mock_app_table, mock_repo_table),
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

            result = await service.search_apps(sort_by="updated", sort_order="desc")
            # mock_app_table has updated_at of 2024-06-01, app2 has 2024-01-01
            assert result[0].id == "test-app"
            assert result[1].id == "old-app"


class TestSearchAppsFilters:
    """Tests for search_apps database filter functionality."""

    @pytest.mark.asyncio
    async def test_filters_by_category(
        self, mock_db_session, mock_app_table, mock_repo_table
    ):
        """search_apps should filter by category database query."""
        session, context_manager = mock_db_session
        mock_result = MagicMock()
        mock_result.all.return_value = [(mock_app_table, mock_repo_table)]
        session.execute = AsyncMock(return_value=mock_result)

        with (
            patch("services.marketplace_service.logger"),
            patch("services.marketplace_service.db_manager") as mock_db,
            patch("services.marketplace_service.initialize_marketplace_database"),
        ):
            mock_db.get_session.return_value = context_manager
            service = MarketplaceService()
            service._initialized = True

            result = await service.search_apps(category="utility")

            assert len(result) == 1
            session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_filters_by_repo_id(
        self, mock_db_session, mock_app_table, mock_repo_table
    ):
        """search_apps should filter by repo_id database query."""
        session, context_manager = mock_db_session
        mock_result = MagicMock()
        mock_result.all.return_value = [(mock_app_table, mock_repo_table)]
        session.execute = AsyncMock(return_value=mock_result)

        with (
            patch("services.marketplace_service.logger"),
            patch("services.marketplace_service.db_manager") as mock_db,
            patch("services.marketplace_service.initialize_marketplace_database"),
        ):
            mock_db.get_session.return_value = context_manager
            service = MarketplaceService()
            service._initialized = True

            result = await service.search_apps(repo_id="test-repo")

            assert len(result) == 1
            session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_filters_by_featured(
        self, mock_db_session, mock_app_table, mock_repo_table
    ):
        """search_apps should filter by featured flag database query."""
        session, context_manager = mock_db_session
        mock_result = MagicMock()
        mock_result.all.return_value = [(mock_app_table, mock_repo_table)]
        session.execute = AsyncMock(return_value=mock_result)

        with (
            patch("services.marketplace_service.logger"),
            patch("services.marketplace_service.db_manager") as mock_db,
            patch("services.marketplace_service.initialize_marketplace_database"),
        ):
            mock_db.get_session.return_value = context_manager
            service = MarketplaceService()
            service._initialized = True

            result = await service.search_apps(featured=True)

            assert len(result) == 1
            session.execute.assert_called_once()
