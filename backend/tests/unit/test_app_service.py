"""
Unit tests for services/app_service.py

Tests for application marketplace service.
"""

from contextlib import asynccontextmanager
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import services.app_service as app_module
from models.app import (
    App,
    AppCategory,
    AppFilter,
    AppRequirements,
    AppStatus,
)
from services.app_service import AppService


@pytest.fixture
def mock_db_manager():
    """Create mock database manager."""
    return MagicMock()


@pytest.fixture
def sample_category():
    """Create sample app category."""
    return AppCategory(
        id="utilities",
        name="Utilities",
        description="Utility applications",
        icon="Wrench",
        color="text-blue-500",
    )


@pytest.fixture
def sample_app(sample_category):
    """Create sample application."""
    return App(
        id="app-1",
        name="Test App",
        description="A test application",
        long_description="Detailed description",
        version="1.0.0",
        category=sample_category,
        tags=["test", "utility"],
        icon="TestIcon",
        screenshots=[],
        author="Test Author",
        repository="https://github.com/test/app",
        documentation="https://docs.test.app",
        license="MIT",
        requirements=AppRequirements(
            min_ram="512MB",
            min_storage="1GB",
            supported_architectures=["amd64", "arm64"],
        ),
        status=AppStatus.AVAILABLE,
        install_count=100,
        rating=4.5,
        featured=True,
        created_at=datetime.now(UTC).isoformat(),
        updated_at=datetime.now(UTC).isoformat(),
    )


@pytest.fixture
def sample_app_2(sample_category):
    """Create second sample application."""
    return App(
        id="app-2",
        name="Another App",
        description="A secondary utility program",
        long_description=None,
        version="2.0.0",
        category=sample_category,
        tags=["test"],
        icon=None,
        screenshots=None,
        author="Another Author",
        repository=None,
        documentation=None,
        license="Apache-2.0",
        requirements=AppRequirements(
            min_ram=None,
            min_storage=None,
            supported_architectures=[],
        ),
        status=AppStatus.INSTALLED,
        install_count=50,
        rating=3.5,
        featured=False,
        created_at="2024-01-01T00:00:00Z",
        updated_at="2024-06-01T00:00:00Z",
    )


@pytest.fixture
def app_service():
    """Create app service with mocked dependencies."""
    with patch.object(app_module, "logger"):
        return AppService()


class TestAppServiceInit:
    """Tests for AppService initialization."""

    def test_init_sets_defaults(self):
        """Should initialize with default values."""
        with patch.object(app_module, "logger"):
            service = AppService()

            assert service._initialized is False
            assert service.installations == {}


class TestEnsureInitialized:
    """Tests for _ensure_initialized method."""

    @pytest.mark.asyncio
    async def test_ensure_initialized_initializes_once(self, app_service):
        """Should initialize database only once."""
        with patch.object(
            app_module, "initialize_app_database", new_callable=AsyncMock
        ) as mock_init:
            await app_service._ensure_initialized()
            await app_service._ensure_initialized()

            assert mock_init.call_count == 1
            assert app_service._initialized is True

    @pytest.mark.asyncio
    async def test_ensure_initialized_skips_if_already_init(self, app_service):
        """Should skip initialization if already initialized."""
        app_service._initialized = True

        with patch.object(
            app_module, "initialize_app_database", new_callable=AsyncMock
        ) as mock_init:
            await app_service._ensure_initialized()

            mock_init.assert_not_called()


class TestApplyFilters:
    """Tests for _apply_filters static method."""

    def test_apply_filters_no_filters(self, sample_app, sample_app_2):
        """Should return all apps when no filters."""
        apps = [sample_app, sample_app_2]
        filters = AppFilter()

        result = AppService._apply_filters(apps, filters)

        assert len(result) == 2

    def test_apply_filters_by_category(self, sample_app, sample_app_2):
        """Should filter by category."""
        apps = [sample_app, sample_app_2]
        filters = AppFilter(category="utilities")

        result = AppService._apply_filters(apps, filters)

        assert len(result) == 2

    def test_apply_filters_by_category_no_match(self, sample_app):
        """Should exclude apps with different category."""
        apps = [sample_app]
        filters = AppFilter(category="media")

        result = AppService._apply_filters(apps, filters)

        assert len(result) == 0

    def test_apply_filters_by_status(self, sample_app, sample_app_2):
        """Should filter by status."""
        apps = [sample_app, sample_app_2]
        filters = AppFilter(status=AppStatus.AVAILABLE)

        result = AppService._apply_filters(apps, filters)

        assert len(result) == 1
        assert result[0].id == "app-1"

    def test_apply_filters_by_featured(self, sample_app, sample_app_2):
        """Should filter by featured flag."""
        apps = [sample_app, sample_app_2]
        filters = AppFilter(featured=True)

        result = AppService._apply_filters(apps, filters)

        assert len(result) == 1
        assert result[0].id == "app-1"

    def test_apply_filters_by_tags(self, sample_app, sample_app_2):
        """Should filter by tags."""
        apps = [sample_app, sample_app_2]
        filters = AppFilter(tags=["utility"])

        result = AppService._apply_filters(apps, filters)

        assert len(result) == 1
        assert result[0].id == "app-1"

    def test_apply_filters_by_search_name(self, sample_app, sample_app_2):
        """Should filter by search term in name."""
        apps = [sample_app, sample_app_2]
        # Use "Test App" to match only the first app's name
        filters = AppFilter(search="Test App")

        result = AppService._apply_filters(apps, filters)

        assert len(result) == 1
        assert result[0].id == "app-1"

    def test_apply_filters_by_search_description(self, sample_app, sample_app_2):
        """Should filter by search term in description."""
        apps = [sample_app, sample_app_2]
        filters = AppFilter(search="Another")

        result = AppService._apply_filters(apps, filters)

        assert len(result) == 1
        assert result[0].id == "app-2"

    def test_apply_filters_combined(self, sample_app, sample_app_2):
        """Should apply multiple filters."""
        apps = [sample_app, sample_app_2]
        filters = AppFilter(
            status=AppStatus.AVAILABLE,
            featured=True,
            tags=["test"],
        )

        result = AppService._apply_filters(apps, filters)

        assert len(result) == 1
        assert result[0].id == "app-1"


class TestApplySorting:
    """Tests for _apply_sorting static method."""

    def test_apply_sorting_by_name_asc(self, sample_app, sample_app_2):
        """Should sort by name ascending."""
        apps = [sample_app, sample_app_2]
        filters = AppFilter(sort_by="name", sort_order="asc")

        AppService._apply_sorting(apps, filters)

        assert apps[0].id == "app-2"  # "Another App" comes before "Test App"
        assert apps[1].id == "app-1"

    def test_apply_sorting_by_name_desc(self, sample_app, sample_app_2):
        """Should sort by name descending."""
        apps = [sample_app, sample_app_2]
        filters = AppFilter(sort_by="name", sort_order="desc")

        AppService._apply_sorting(apps, filters)

        assert apps[0].id == "app-1"  # "Test App" comes first descending
        assert apps[1].id == "app-2"

    def test_apply_sorting_by_rating(self, sample_app, sample_app_2):
        """Should sort by rating."""
        apps = [sample_app, sample_app_2]
        filters = AppFilter(sort_by="rating", sort_order="desc")

        AppService._apply_sorting(apps, filters)

        assert apps[0].id == "app-1"  # Higher rating first

    def test_apply_sorting_by_popularity(self, sample_app, sample_app_2):
        """Should sort by popularity (install_count)."""
        apps = [sample_app, sample_app_2]
        filters = AppFilter(sort_by="popularity", sort_order="desc")

        AppService._apply_sorting(apps, filters)

        assert apps[0].id == "app-1"  # More installs first

    def test_apply_sorting_by_install_count(self, sample_app, sample_app_2):
        """Should sort by install_count."""
        apps = [sample_app, sample_app_2]
        filters = AppFilter(sort_by="install_count", sort_order="asc")

        AppService._apply_sorting(apps, filters)

        assert apps[0].id == "app-2"  # Fewer installs first

    def test_apply_sorting_by_updated(self, sample_app, sample_app_2):
        """Should sort by updated_at."""
        apps = [sample_app, sample_app_2]
        filters = AppFilter(sort_by="updated", sort_order="asc")

        AppService._apply_sorting(apps, filters)

        # app_2 has earlier updated_at (2024-06-01)
        assert apps[0].id == "app-2"

    def test_apply_sorting_unknown_key_defaults_to_name(self, sample_app, sample_app_2):
        """Should default to name sorting for unknown key."""
        apps = [sample_app, sample_app_2]
        filters = AppFilter(sort_by="unknown", sort_order="asc")

        with patch.object(app_module, "logger"):
            AppService._apply_sorting(apps, filters)

        assert apps[0].id == "app-2"  # Alphabetical by name

    def test_apply_sorting_none_rating(self, sample_app):
        """Should handle None rating values."""
        app_no_rating = MagicMock()
        app_no_rating.rating = None
        app_no_rating.name = MagicMock()
        app_no_rating.name.lower.return_value = "aaa"

        apps = [sample_app, app_no_rating]
        filters = AppFilter(sort_by="rating", sort_order="desc")

        AppService._apply_sorting(apps, filters)

        assert apps[0] == sample_app  # App with rating comes first


class TestIsoToDatetime:
    """Tests for _iso_to_datetime static method."""

    def test_iso_to_datetime_standard_format(self):
        """Should parse standard ISO format."""
        result = AppService._iso_to_datetime("2024-01-15T10:30:00+00:00")

        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_iso_to_datetime_z_suffix(self):
        """Should handle Z suffix."""
        result = AppService._iso_to_datetime("2024-01-15T10:30:00Z")

        assert result.year == 2024
        assert result.month == 1


class TestFetchAllApps:
    """Tests for _fetch_all_apps method."""

    @pytest.mark.asyncio
    async def test_fetch_all_apps_returns_apps(self, app_service):
        """Should fetch and return all apps."""
        mock_app_row = MagicMock()
        mock_cat_row = MagicMock()

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = [(mock_app_row, mock_cat_row)]
        mock_session.execute.return_value = mock_result

        @asynccontextmanager
        async def mock_get_session():
            yield mock_session

        mock_app = MagicMock()

        with (
            patch.object(
                app_module, "initialize_app_database", new_callable=AsyncMock
            ),
            patch.object(app_module, "db_manager") as mock_db,
            patch.object(app_module.App, "from_table", return_value=mock_app),
            patch.object(app_module, "logger"),
        ):
            mock_db.get_session = mock_get_session

            result = await app_service._fetch_all_apps()

            assert len(result) == 1
            assert result[0] == mock_app


class TestSearchApps:
    """Tests for search_apps method."""

    @pytest.mark.asyncio
    async def test_search_apps_returns_results(self, app_service, sample_app):
        """Should return search results."""
        filters = AppFilter()

        with (
            patch.object(
                app_service, "_fetch_all_apps", new_callable=AsyncMock
            ) as mock_fetch,
            patch.object(app_module, "logger"),
        ):
            mock_fetch.return_value = [sample_app]

            result = await app_service.search_apps(filters)

            assert result.total == 1
            assert len(result.apps) == 1
            assert result.page == 1

    @pytest.mark.asyncio
    async def test_search_apps_empty_logs(self, app_service):
        """Should log when no results found."""
        filters = AppFilter(search="nonexistent")

        with (
            patch.object(
                app_service, "_fetch_all_apps", new_callable=AsyncMock
            ) as mock_fetch,
            patch.object(app_module, "log_service") as mock_log_service,
            patch.object(app_module, "logger"),
            patch.object(app_module, "build_empty_search_log") as mock_build_log,
        ):
            mock_fetch.return_value = []
            mock_log_service.create_log_entry = AsyncMock()
            mock_build_log.return_value = {"type": "empty_search"}

            result = await app_service.search_apps(filters)

            assert result.total == 0
            mock_log_service.create_log_entry.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_apps_log_error_handled(self, app_service):
        """Should handle log write errors gracefully."""
        filters = AppFilter(search="nonexistent")

        with (
            patch.object(
                app_service, "_fetch_all_apps", new_callable=AsyncMock
            ) as mock_fetch,
            patch.object(app_module, "log_service") as mock_log_service,
            patch.object(app_module, "logger") as mock_logger,
            patch.object(app_module, "build_empty_search_log"),
        ):
            mock_fetch.return_value = []
            mock_log_service.create_log_entry = AsyncMock(
                side_effect=RuntimeError("Log error")
            )

            result = await app_service.search_apps(filters)

            assert result.total == 0
            mock_logger.warning.assert_called()


class TestGetAppById:
    """Tests for get_app_by_id method."""

    @pytest.mark.asyncio
    async def test_get_app_by_id_found(self, app_service):
        """Should return app when found."""
        mock_app_row = MagicMock()
        mock_cat_row = MagicMock()

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.first.return_value = (mock_app_row, mock_cat_row)
        mock_session.execute.return_value = mock_result

        @asynccontextmanager
        async def mock_get_session():
            yield mock_session

        mock_app = MagicMock()

        with (
            patch.object(
                app_module, "initialize_app_database", new_callable=AsyncMock
            ),
            patch.object(app_module, "db_manager") as mock_db,
            patch.object(app_module.App, "from_table", return_value=mock_app),
            patch.object(app_module, "logger"),
        ):
            mock_db.get_session = mock_get_session

            result = await app_service.get_app_by_id("app-1")

            assert result == mock_app

    @pytest.mark.asyncio
    async def test_get_app_by_id_not_found(self, app_service):
        """Should return None when not found."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.execute.return_value = mock_result

        @asynccontextmanager
        async def mock_get_session():
            yield mock_session

        with (
            patch.object(
                app_module, "initialize_app_database", new_callable=AsyncMock
            ),
            patch.object(app_module, "db_manager") as mock_db,
            patch.object(app_module, "logger") as mock_logger,
        ):
            mock_db.get_session = mock_get_session

            result = await app_service.get_app_by_id("nonexistent")

            assert result is None
            mock_logger.warning.assert_called()


class TestAddApp:
    """Tests for add_app method."""

    @pytest.mark.asyncio
    async def test_add_app_success(self, app_service, sample_category):
        """Should add app successfully."""
        app_data = {
            "id": "new-app",
            "name": "New App",
            "description": "A new application",
            "version": "1.0.0",
            "category_id": "utilities",
            "author": "Test Author",
            "license": "MIT",
        }

        mock_session = AsyncMock()

        # First execute: check existing app
        mock_existing_result = MagicMock()
        mock_existing_result.first.return_value = None

        # Second execute: get category
        mock_cat_row = MagicMock()
        mock_cat_result = MagicMock()
        mock_cat_result.first.return_value = (mock_cat_row,)

        mock_session.execute.side_effect = [mock_existing_result, mock_cat_result]
        mock_session.add = MagicMock()

        @asynccontextmanager
        async def mock_get_session():
            yield mock_session

        with (
            patch.object(
                app_module, "initialize_app_database", new_callable=AsyncMock
            ),
            patch.object(app_module, "db_manager") as mock_db,
            patch.object(
                app_module.AppCategory, "from_table", return_value=sample_category
            ),
            patch.object(app_module, "logger"),
        ):
            mock_db.get_session = mock_get_session

            result = await app_service.add_app(app_data)

            assert result.id == "new-app"
            assert result.name == "New App"
            mock_session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_app_already_exists(self, app_service):
        """Should raise error if app already exists."""
        app_data = {
            "id": "existing-app",
            "name": "Existing App",
            "description": "Already exists",
            "version": "1.0.0",
            "category_id": "utilities",
            "author": "Test Author",
            "license": "MIT",
        }

        mock_session = AsyncMock()
        mock_existing_result = MagicMock()
        mock_existing_result.first.return_value = MagicMock()  # App exists
        mock_session.execute.return_value = mock_existing_result

        @asynccontextmanager
        async def mock_get_session():
            yield mock_session

        with (
            patch.object(
                app_module, "initialize_app_database", new_callable=AsyncMock
            ),
            patch.object(app_module, "db_manager") as mock_db,
            patch.object(app_module, "logger"),
        ):
            mock_db.get_session = mock_get_session

            with pytest.raises(ValueError, match="already exists"):
                await app_service.add_app(app_data)

    @pytest.mark.asyncio
    async def test_add_app_creates_category(self, app_service):
        """Should create category if not exists."""
        app_data = {
            "id": "new-app",
            "name": "New App",
            "description": "A new application",
            "version": "1.0.0",
            "category": "newcategory",
            "author": "Test Author",
            "license": "MIT",
        }

        mock_session = AsyncMock()

        # First: check existing app
        mock_existing_result = MagicMock()
        mock_existing_result.first.return_value = None

        # Second: get category (not found)
        mock_cat_result = MagicMock()
        mock_cat_result.first.return_value = None

        mock_session.execute.side_effect = [mock_existing_result, mock_cat_result]
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()

        @asynccontextmanager
        async def mock_get_session():
            yield mock_session

        # Create a proper category for the newly created category
        new_category = AppCategory(
            id="newcategory",
            name="Newcategory",
            description="Applications in the newcategory category",
            icon="Package",
            color="text-primary",
        )

        with (
            patch.object(
                app_module, "initialize_app_database", new_callable=AsyncMock
            ),
            patch.object(app_module, "db_manager") as mock_db,
            patch.object(
                app_module.AppCategory, "from_table", return_value=new_category
            ),
            patch.object(app_module, "logger"),
        ):
            mock_db.get_session = mock_get_session

            result = await app_service.add_app(app_data)

            assert result.id == "new-app"
            # Session.add called twice: once for category, once for app
            assert mock_session.add.call_count == 2


class TestRemoveApp:
    """Tests for remove_app method."""

    @pytest.mark.asyncio
    async def test_remove_app_success(self, app_service):
        """Should remove app successfully."""
        mock_session = AsyncMock()

        mock_app = MagicMock()
        mock_app.status = "available"

        mock_result = MagicMock()
        mock_result.first.return_value = (mock_app,)
        mock_session.execute.return_value = mock_result

        @asynccontextmanager
        async def mock_get_session():
            yield mock_session

        with (
            patch.object(
                app_module, "initialize_app_database", new_callable=AsyncMock
            ),
            patch.object(app_module, "db_manager") as mock_db,
            patch.object(app_module, "logger"),
        ):
            mock_db.get_session = mock_get_session

            result = await app_service.remove_app("app-1")

            assert result is True

    @pytest.mark.asyncio
    async def test_remove_app_not_found(self, app_service):
        """Should return False if app not found."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.execute.return_value = mock_result

        @asynccontextmanager
        async def mock_get_session():
            yield mock_session

        with (
            patch.object(
                app_module, "initialize_app_database", new_callable=AsyncMock
            ),
            patch.object(app_module, "db_manager") as mock_db,
            patch.object(app_module, "logger"),
        ):
            mock_db.get_session = mock_get_session

            result = await app_service.remove_app("nonexistent")

            assert result is False

    @pytest.mark.asyncio
    async def test_remove_app_installed_raises(self, app_service):
        """Should raise error if app is installed."""
        mock_session = AsyncMock()

        mock_app = MagicMock()
        mock_app.status = "installed"

        mock_result = MagicMock()
        mock_result.first.return_value = (mock_app,)
        mock_session.execute.return_value = mock_result

        @asynccontextmanager
        async def mock_get_session():
            yield mock_session

        with (
            patch.object(
                app_module, "initialize_app_database", new_callable=AsyncMock
            ),
            patch.object(app_module, "db_manager") as mock_db,
            patch.object(app_module, "logger"),
        ):
            mock_db.get_session = mock_get_session

            with pytest.raises(ValueError, match="Cannot remove installed app"):
                await app_service.remove_app("installed-app")


class TestRemoveAppsBulk:
    """Tests for remove_apps_bulk method."""

    @pytest.mark.asyncio
    async def test_remove_apps_bulk_success(self, app_service):
        """Should remove multiple apps."""
        with patch.object(
            app_service, "remove_app", new_callable=AsyncMock
        ) as mock_remove:
            mock_remove.return_value = True

            result = await app_service.remove_apps_bulk(["app-1", "app-2"])

            assert result["removed_count"] == 2
            assert result["skipped_count"] == 0

    @pytest.mark.asyncio
    async def test_remove_apps_bulk_partial(self, app_service):
        """Should handle partial success."""
        with patch.object(
            app_service, "remove_app", new_callable=AsyncMock
        ) as mock_remove:
            mock_remove.side_effect = [True, False]  # First succeeds, second not found

            result = await app_service.remove_apps_bulk(["app-1", "app-2"])

            assert result["removed_count"] == 1
            assert result["skipped_count"] == 1
            assert result["skipped"][0]["reason"] == "not found"

    @pytest.mark.asyncio
    async def test_remove_apps_bulk_with_errors(self, app_service):
        """Should handle errors gracefully."""
        with patch.object(
            app_service, "remove_app", new_callable=AsyncMock
        ) as mock_remove:
            mock_remove.side_effect = [True, ValueError("Cannot remove")]

            result = await app_service.remove_apps_bulk(["app-1", "app-2"])

            assert result["removed_count"] == 1
            assert result["skipped_count"] == 1
            assert "Cannot remove" in result["skipped"][0]["reason"]


class TestGetAppIds:
    """Tests for get_app_ids method."""

    @pytest.mark.asyncio
    async def test_get_app_ids_returns_ids(self, app_service):
        """Should return all app IDs."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = [("app-1",), ("app-2",), ("app-3",)]
        mock_session.execute.return_value = mock_result

        @asynccontextmanager
        async def mock_get_session():
            yield mock_session

        with (
            patch.object(
                app_module, "initialize_app_database", new_callable=AsyncMock
            ),
            patch.object(app_module, "db_manager") as mock_db,
        ):
            mock_db.get_session = mock_get_session

            result = await app_service.get_app_ids()

            assert result == ["app-1", "app-2", "app-3"]


class TestMarkAppUninstalled:
    """Tests for mark_app_uninstalled method."""

    @pytest.mark.asyncio
    async def test_mark_app_uninstalled_success(self, app_service):
        """Should mark app as uninstalled."""
        mock_session = AsyncMock()
        mock_app = MagicMock()

        mock_result = MagicMock()
        mock_result.first.return_value = (mock_app,)
        mock_session.execute.return_value = mock_result

        @asynccontextmanager
        async def mock_get_session():
            yield mock_session

        with (
            patch.object(
                app_module, "initialize_app_database", new_callable=AsyncMock
            ),
            patch.object(app_module, "db_manager") as mock_db,
            patch.object(app_module, "logger"),
        ):
            mock_db.get_session = mock_get_session

            result = await app_service.mark_app_uninstalled("app-1")

            assert result is True
            assert mock_app.status == "available"
            assert mock_app.connected_server_id is None

    @pytest.mark.asyncio
    async def test_mark_app_uninstalled_not_found(self, app_service):
        """Should return False if app not found."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.execute.return_value = mock_result

        @asynccontextmanager
        async def mock_get_session():
            yield mock_session

        with (
            patch.object(
                app_module, "initialize_app_database", new_callable=AsyncMock
            ),
            patch.object(app_module, "db_manager") as mock_db,
        ):
            mock_db.get_session = mock_get_session

            result = await app_service.mark_app_uninstalled("nonexistent")

            assert result is False


class TestMarkAppInstalled:
    """Tests for mark_app_installed method."""

    @pytest.mark.asyncio
    async def test_mark_app_installed_success(self, app_service):
        """Should mark app as installed."""
        mock_session = AsyncMock()
        mock_app = MagicMock()
        mock_app.id = "app-1"

        mock_result = MagicMock()
        mock_result.first.return_value = (mock_app,)
        mock_session.execute.return_value = mock_result

        @asynccontextmanager
        async def mock_get_session():
            yield mock_session

        with (
            patch.object(
                app_module, "initialize_app_database", new_callable=AsyncMock
            ),
            patch.object(app_module, "db_manager") as mock_db,
            patch.object(app_module, "logger"),
        ):
            mock_db.get_session = mock_get_session

            result = await app_service.mark_app_installed("app-1", "server-1")

            assert result is True
            assert mock_app.status == "installed"
            assert mock_app.connected_server_id == "server-1"

    @pytest.mark.asyncio
    async def test_mark_app_installed_with_prefix(self, app_service):
        """Should find app by removing casaos- prefix."""
        mock_session = AsyncMock()
        mock_app = MagicMock()
        mock_app.id = "myapp"

        # First query returns None, second returns app
        mock_result_none = MagicMock()
        mock_result_none.first.return_value = None

        mock_result_found = MagicMock()
        mock_result_found.first.return_value = (mock_app,)

        mock_session.execute.side_effect = [mock_result_none, mock_result_found]

        @asynccontextmanager
        async def mock_get_session():
            yield mock_session

        with (
            patch.object(
                app_module, "initialize_app_database", new_callable=AsyncMock
            ),
            patch.object(app_module, "db_manager") as mock_db,
            patch.object(app_module, "logger"),
        ):
            mock_db.get_session = mock_get_session

            result = await app_service.mark_app_installed("casaos-myapp", "server-1")

            assert result is True
            assert mock_app.status == "installed"

    @pytest.mark.asyncio
    async def test_mark_app_installed_not_found(self, app_service):
        """Should return False if app not found."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.execute.return_value = mock_result

        @asynccontextmanager
        async def mock_get_session():
            yield mock_session

        with (
            patch.object(
                app_module, "initialize_app_database", new_callable=AsyncMock
            ),
            patch.object(app_module, "db_manager") as mock_db,
            patch.object(app_module, "logger") as mock_logger,
        ):
            mock_db.get_session = mock_get_session

            result = await app_service.mark_app_installed("nonexistent", "server-1")

            assert result is False
            mock_logger.warning.assert_called()


class TestMarkAppsUninstalledBulk:
    """Tests for mark_apps_uninstalled_bulk method."""

    @pytest.mark.asyncio
    async def test_mark_apps_uninstalled_bulk_success(self, app_service):
        """Should uninstall multiple apps."""
        with patch.object(
            app_service, "mark_app_uninstalled", new_callable=AsyncMock
        ) as mock_uninstall:
            mock_uninstall.return_value = True

            result = await app_service.mark_apps_uninstalled_bulk(["app-1", "app-2"])

            assert result["uninstalled_count"] == 2
            assert result["skipped_count"] == 0

    @pytest.mark.asyncio
    async def test_mark_apps_uninstalled_bulk_partial(self, app_service):
        """Should handle partial success."""
        with patch.object(
            app_service, "mark_app_uninstalled", new_callable=AsyncMock
        ) as mock_uninstall:
            mock_uninstall.side_effect = [True, False]

            result = await app_service.mark_apps_uninstalled_bulk(["app-1", "app-2"])

            assert result["uninstalled_count"] == 1
            assert result["skipped_count"] == 1

    @pytest.mark.asyncio
    async def test_mark_apps_uninstalled_bulk_with_errors(self, app_service):
        """Should handle errors gracefully."""
        with patch.object(
            app_service, "mark_app_uninstalled", new_callable=AsyncMock
        ) as mock_uninstall:
            mock_uninstall.side_effect = [True, RuntimeError("Error")]

            result = await app_service.mark_apps_uninstalled_bulk(["app-1", "app-2"])

            assert result["uninstalled_count"] == 1
            assert result["skipped_count"] == 1
            assert "Error" in result["skipped"][0]["reason"]


class TestInstallApp:
    """Tests for install_app method."""

    @pytest.mark.asyncio
    async def test_install_app_success(self, app_service, sample_app):
        """Should create installation record."""
        with (
            patch.object(
                app_service, "get_app_by_id", new_callable=AsyncMock
            ) as mock_get,
            patch.object(app_module, "logger"),
        ):
            mock_get.return_value = sample_app

            result = await app_service.install_app("app-1", {"port": 8080})

            assert result.app_id == "app-1"
            assert result.status == AppStatus.INSTALLING
            assert result.config == {"port": 8080}
            assert "app-1" in app_service.installations

    @pytest.mark.asyncio
    async def test_install_app_not_found(self, app_service):
        """Should raise error if app not found."""
        with patch.object(
            app_service, "get_app_by_id", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = None

            with pytest.raises(ValueError, match="not found"):
                await app_service.install_app("nonexistent")

    @pytest.mark.asyncio
    async def test_install_app_default_config(self, app_service, sample_app):
        """Should use empty config by default."""
        with (
            patch.object(
                app_service, "get_app_by_id", new_callable=AsyncMock
            ) as mock_get,
            patch.object(app_module, "logger"),
        ):
            mock_get.return_value = sample_app

            result = await app_service.install_app("app-1")

            assert result.config == {}
