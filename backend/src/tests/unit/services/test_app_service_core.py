"""
Unit tests for services/app_service.py - Core functionality

Tests initialization, fetch, filtering, and sorting.
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


class TestAppServiceInit:
    """Tests for AppService initialization."""

    def test_init_sets_not_initialized(self):
        """AppService should start uninitialized."""
        with patch("services.app_service.logger"):
            service = AppService()
            assert service._initialized is False

    def test_init_creates_empty_installations(self):
        """AppService should initialize empty installations dict."""
        with patch("services.app_service.logger"):
            service = AppService()
            assert service.installations == {}

    def test_init_logs_message(self):
        """AppService should log initialization."""
        with patch("services.app_service.logger") as mock_logger:
            AppService()
            mock_logger.info.assert_called_once_with("Application service initialized")


class TestEnsureInitialized:
    """Tests for _ensure_initialized method."""

    @pytest.mark.asyncio
    async def test_ensure_initialized_calls_init_db(self):
        """_ensure_initialized should call initialize_app_database."""
        with (
            patch("services.app_service.logger"),
            patch("services.app_service.initialize_app_database") as mock_init,
        ):
            mock_init.return_value = None
            service = AppService()
            await service._ensure_initialized()
            mock_init.assert_called_once()

    @pytest.mark.asyncio
    async def test_ensure_initialized_sets_flag(self):
        """_ensure_initialized should set _initialized to True."""
        with (
            patch("services.app_service.logger"),
            patch("services.app_service.initialize_app_database"),
        ):
            service = AppService()
            await service._ensure_initialized()
            assert service._initialized is True

    @pytest.mark.asyncio
    async def test_ensure_initialized_skips_if_already_initialized(self):
        """_ensure_initialized should skip if already initialized."""
        with (
            patch("services.app_service.logger"),
            patch("services.app_service.initialize_app_database") as mock_init,
        ):
            service = AppService()
            service._initialized = True
            await service._ensure_initialized()
            mock_init.assert_not_called()


class TestFetchAllApps:
    """Tests for _fetch_all_apps method."""

    @pytest.mark.asyncio
    async def test_fetch_all_apps_returns_apps(
        self, mock_db_session, sample_app_table, sample_category_table
    ):
        """_fetch_all_apps should return list of App instances."""
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
            apps = await service._fetch_all_apps()

            assert len(apps) == 1
            assert apps[0].id == "plex"
            assert apps[0].name == "Plex"

    @pytest.mark.asyncio
    async def test_fetch_all_apps_logs_count(
        self, mock_db_session, sample_app_table, sample_category_table
    ):
        """_fetch_all_apps should log fetched count."""
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
            await service._fetch_all_apps()

            mock_logger.debug.assert_called_with(
                "Fetched applications from database", count=1
            )


class TestApplyFilters:
    """Tests for _apply_filters static method."""

    def test_filter_by_category(self, sample_app):
        """_apply_filters should filter by category."""
        filters = AppFilter(category="media")
        result = AppService._apply_filters([sample_app], filters)
        assert len(result) == 1

        filters = AppFilter(category="networking")
        result = AppService._apply_filters([sample_app], filters)
        assert len(result) == 0

    def test_filter_by_status(self, sample_app):
        """_apply_filters should filter by status."""
        filters = AppFilter(status=AppStatus.AVAILABLE)
        result = AppService._apply_filters([sample_app], filters)
        assert len(result) == 1

        filters = AppFilter(status=AppStatus.INSTALLED)
        result = AppService._apply_filters([sample_app], filters)
        assert len(result) == 0

    def test_filter_by_featured(self, sample_app):
        """_apply_filters should filter by featured flag."""
        filters = AppFilter(featured=True)
        result = AppService._apply_filters([sample_app], filters)
        assert len(result) == 1

        filters = AppFilter(featured=False)
        result = AppService._apply_filters([sample_app], filters)
        assert len(result) == 0

    def test_filter_by_tags(self, sample_app):
        """_apply_filters should filter by tags."""
        filters = AppFilter(tags=["media"])
        result = AppService._apply_filters([sample_app], filters)
        assert len(result) == 1

        filters = AppFilter(tags=["media", "streaming"])
        result = AppService._apply_filters([sample_app], filters)
        assert len(result) == 1

        filters = AppFilter(tags=["nonexistent"])
        result = AppService._apply_filters([sample_app], filters)
        assert len(result) == 0

    def test_filter_by_search_name(self, sample_app):
        """_apply_filters should search in name."""
        filters = AppFilter(search="plex")
        result = AppService._apply_filters([sample_app], filters)
        assert len(result) == 1

        filters = AppFilter(search="PLEX")  # Case insensitive
        result = AppService._apply_filters([sample_app], filters)
        assert len(result) == 1

    def test_filter_by_search_description(self, sample_app):
        """_apply_filters should search in description."""
        filters = AppFilter(search="media server")
        result = AppService._apply_filters([sample_app], filters)
        assert len(result) == 1

    def test_filter_no_match(self, sample_app):
        """_apply_filters should return empty for no match."""
        filters = AppFilter(search="nonexistent")
        result = AppService._apply_filters([sample_app], filters)
        assert len(result) == 0

    def test_filter_empty_filters(self, sample_app):
        """_apply_filters should return all apps with empty filters."""
        filters = AppFilter()
        result = AppService._apply_filters([sample_app], filters)
        assert len(result) == 1


class TestApplySorting:
    """Tests for _apply_sorting static method."""

    def test_sort_by_name_asc(self, sample_category):
        """_apply_sorting should sort by name ascending."""
        app1 = App(
            id="a",
            name="Zebra",
            description="Z",
            version="1.0",
            category=sample_category,
            author="test",
            license="MIT",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
        )
        app2 = App(
            id="b",
            name="Alpha",
            description="A",
            version="1.0",
            category=sample_category,
            author="test",
            license="MIT",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
        )
        apps = [app1, app2]
        filters = AppFilter(sort_by="name", sort_order="asc")
        AppService._apply_sorting(apps, filters)
        assert apps[0].name == "Alpha"
        assert apps[1].name == "Zebra"

    def test_sort_by_name_desc(self, sample_category):
        """_apply_sorting should sort by name descending."""
        app1 = App(
            id="a",
            name="Alpha",
            description="A",
            version="1.0",
            category=sample_category,
            author="test",
            license="MIT",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
        )
        app2 = App(
            id="b",
            name="Zebra",
            description="Z",
            version="1.0",
            category=sample_category,
            author="test",
            license="MIT",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
        )
        apps = [app1, app2]
        filters = AppFilter(sort_by="name", sort_order="desc")
        AppService._apply_sorting(apps, filters)
        assert apps[0].name == "Zebra"
        assert apps[1].name == "Alpha"

    def test_sort_by_rating(self, sample_category):
        """_apply_sorting should sort by rating."""
        app1 = App(
            id="a",
            name="A",
            description="A",
            version="1.0",
            category=sample_category,
            author="test",
            license="MIT",
            rating=3.0,
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
        )
        app2 = App(
            id="b",
            name="B",
            description="B",
            version="1.0",
            category=sample_category,
            author="test",
            license="MIT",
            rating=5.0,
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
        )
        apps = [app1, app2]
        filters = AppFilter(sort_by="rating", sort_order="desc")
        AppService._apply_sorting(apps, filters)
        assert apps[0].rating == 5.0

    def test_sort_by_popularity(self, sample_category):
        """_apply_sorting should sort by install_count for popularity."""
        app1 = App(
            id="a",
            name="A",
            description="A",
            version="1.0",
            category=sample_category,
            author="test",
            license="MIT",
            install_count=10,
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
        )
        app2 = App(
            id="b",
            name="B",
            description="B",
            version="1.0",
            category=sample_category,
            author="test",
            license="MIT",
            install_count=100,
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
        )
        apps = [app1, app2]
        filters = AppFilter(sort_by="popularity", sort_order="desc")
        AppService._apply_sorting(apps, filters)
        assert apps[0].install_count == 100

    def test_sort_by_install_count(self, sample_category):
        """_apply_sorting should handle install_count sort key."""
        app1 = App(
            id="a",
            name="A",
            description="A",
            version="1.0",
            category=sample_category,
            author="test",
            license="MIT",
            install_count=50,
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
        )
        app2 = App(
            id="b",
            name="B",
            description="B",
            version="1.0",
            category=sample_category,
            author="test",
            license="MIT",
            install_count=200,
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
        )
        apps = [app1, app2]
        filters = AppFilter(sort_by="install_count", sort_order="desc")
        AppService._apply_sorting(apps, filters)
        assert apps[0].install_count == 200

    def test_sort_by_updated(self, sample_category):
        """_apply_sorting should sort by updated_at."""
        app1 = App(
            id="a",
            name="A",
            description="A",
            version="1.0",
            category=sample_category,
            author="test",
            license="MIT",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
        )
        app2 = App(
            id="b",
            name="B",
            description="B",
            version="1.0",
            category=sample_category,
            author="test",
            license="MIT",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-06-01T00:00:00Z",
        )
        apps = [app1, app2]
        filters = AppFilter(sort_by="updated", sort_order="desc")
        AppService._apply_sorting(apps, filters)
        assert apps[0].id == "b"

    def test_sort_by_unknown_key(self, sample_category):
        """_apply_sorting should default to name for unknown key."""
        app1 = App(
            id="a",
            name="Zebra",
            description="Z",
            version="1.0",
            category=sample_category,
            author="test",
            license="MIT",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
        )
        app2 = App(
            id="b",
            name="Alpha",
            description="A",
            version="1.0",
            category=sample_category,
            author="test",
            license="MIT",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
        )
        apps = [app1, app2]
        filters = AppFilter(sort_by="unknown", sort_order="asc")

        with patch("services.app_service.logger") as mock_logger:
            AppService._apply_sorting(apps, filters)
            mock_logger.debug.assert_called()

        assert apps[0].name == "Alpha"


class TestIsoToDatetime:
    """Tests for _iso_to_datetime static method."""

    def test_iso_to_datetime_z_suffix(self):
        """_iso_to_datetime should handle Z suffix."""
        result = AppService._iso_to_datetime("2024-01-01T00:00:00Z")
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 1

    def test_iso_to_datetime_offset(self):
        """_iso_to_datetime should handle timezone offset."""
        result = AppService._iso_to_datetime("2024-06-15T12:30:00+00:00")
        assert result.year == 2024
        assert result.month == 6
        assert result.hour == 12

    def test_iso_to_datetime_no_tz(self):
        """_iso_to_datetime should handle no timezone."""
        result = AppService._iso_to_datetime("2024-03-20T15:45:30")
        assert result.year == 2024
        assert result.minute == 45
