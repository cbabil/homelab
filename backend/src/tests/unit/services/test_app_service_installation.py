"""
Unit tests for services/app_service.py - Installation Methods

Tests mark_app_installed, mark_app_uninstalled, install_app,
and bulk installation operations.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.app import (
    App,
    AppCategory,
    AppCategoryTable,
    AppInstallation,
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


class TestMarkAppUninstalled:
    """Tests for mark_app_uninstalled method."""

    @pytest.mark.asyncio
    async def test_mark_app_uninstalled_success(
        self, mock_db_session, sample_app_table
    ):
        """mark_app_uninstalled should update status to available."""
        session, context_manager = mock_db_session
        sample_app_table.status = "installed"
        sample_app_table.connected_server_id = "srv-123"

        result = MagicMock()
        result.first.return_value = (sample_app_table,)
        session.execute = AsyncMock(return_value=result)

        with (
            patch("services.app_service.logger") as mock_logger,
            patch("services.app_service.initialize_app_database"),
            patch("services.app_service.db_manager") as mock_db,
        ):
            mock_db.get_session.return_value = context_manager

            service = AppService()
            success = await service.mark_app_uninstalled("plex")

            assert success is True
            assert sample_app_table.status == "available"
            assert sample_app_table.connected_server_id is None
            mock_logger.info.assert_any_call(
                "Application marked as uninstalled", app_id="plex"
            )

    @pytest.mark.asyncio
    async def test_mark_app_uninstalled_not_found(self, mock_db_session):
        """mark_app_uninstalled should return False when not found."""
        session, context_manager = mock_db_session

        result = MagicMock()
        result.first.return_value = None
        session.execute = AsyncMock(return_value=result)

        with (
            patch("services.app_service.logger"),
            patch("services.app_service.initialize_app_database"),
            patch("services.app_service.db_manager") as mock_db,
        ):
            mock_db.get_session.return_value = context_manager

            service = AppService()
            success = await service.mark_app_uninstalled("nonexistent")

            assert success is False


class TestMarkAppInstalled:
    """Tests for mark_app_installed method."""

    @pytest.mark.asyncio
    async def test_mark_app_installed_success(self, mock_db_session, sample_app_table):
        """mark_app_installed should update status and server_id."""
        session, context_manager = mock_db_session

        result = MagicMock()
        result.first.return_value = (sample_app_table,)
        session.execute = AsyncMock(return_value=result)

        with (
            patch("services.app_service.logger") as mock_logger,
            patch("services.app_service.initialize_app_database"),
            patch("services.app_service.db_manager") as mock_db,
        ):
            mock_db.get_session.return_value = context_manager

            service = AppService()
            success = await service.mark_app_installed("plex", "srv-123")

            assert success is True
            assert sample_app_table.status == "installed"
            assert sample_app_table.connected_server_id == "srv-123"
            mock_logger.info.assert_any_call(
                "Application marked as installed", app_id="plex", server_id="srv-123"
            )

    @pytest.mark.asyncio
    async def test_mark_app_installed_not_found(self, mock_db_session):
        """mark_app_installed should return False when not found."""
        session, context_manager = mock_db_session

        result = MagicMock()
        result.first.return_value = None
        session.execute = AsyncMock(return_value=result)

        with (
            patch("services.app_service.logger") as mock_logger,
            patch("services.app_service.initialize_app_database"),
            patch("services.app_service.db_manager") as mock_db,
        ):
            mock_db.get_session.return_value = context_manager

            service = AppService()
            success = await service.mark_app_installed("nonexistent", "srv-123")

            assert success is False
            mock_logger.warning.assert_called_with(
                "Application not found for marking installed", app_id="nonexistent"
            )

    @pytest.mark.asyncio
    async def test_mark_app_installed_with_casaos_prefix(
        self, mock_db_session, sample_app_table
    ):
        """mark_app_installed should strip casaos- prefix if not found."""
        session, context_manager = mock_db_session
        sample_app_table.id = "plex"

        call_count = [0]

        def execute_side_effect(*args, **kwargs):
            call_count[0] += 1
            result = MagicMock()
            if call_count[0] == 1:
                result.first.return_value = None  # casaos-plex not found
            else:
                result.first.return_value = (sample_app_table,)  # plex found
            return result

        session.execute = AsyncMock(side_effect=execute_side_effect)

        with (
            patch("services.app_service.logger"),
            patch("services.app_service.initialize_app_database"),
            patch("services.app_service.db_manager") as mock_db,
        ):
            mock_db.get_session.return_value = context_manager

            service = AppService()
            success = await service.mark_app_installed("casaos-plex", "srv-123")

            assert success is True
            assert sample_app_table.status == "installed"

    @pytest.mark.asyncio
    async def test_mark_app_installed_with_prefix_not_found(self, mock_db_session):
        """mark_app_installed should return False if prefix stripping fails."""
        session, context_manager = mock_db_session

        result = MagicMock()
        result.first.return_value = None
        session.execute = AsyncMock(return_value=result)

        with (
            patch("services.app_service.logger"),
            patch("services.app_service.initialize_app_database"),
            patch("services.app_service.db_manager") as mock_db,
        ):
            mock_db.get_session.return_value = context_manager

            service = AppService()
            success = await service.mark_app_installed("casaos-unknown", "srv-123")

            assert success is False


class TestMarkAppsUninstalledBulk:
    """Tests for mark_apps_uninstalled_bulk method."""

    @pytest.mark.asyncio
    async def test_mark_apps_uninstalled_bulk_success(
        self, mock_db_session, sample_app_table
    ):
        """mark_apps_uninstalled_bulk should uninstall multiple apps."""
        session, context_manager = mock_db_session
        sample_app_table.status = "installed"

        result = MagicMock()
        result.first.return_value = (sample_app_table,)
        session.execute = AsyncMock(return_value=result)

        with (
            patch("services.app_service.logger"),
            patch("services.app_service.initialize_app_database"),
            patch("services.app_service.db_manager") as mock_db,
        ):
            mock_db.get_session.return_value = context_manager

            service = AppService()
            result = await service.mark_apps_uninstalled_bulk(["plex", "jellyfin"])

            assert result["uninstalled_count"] == 2
            assert len(result["uninstalled"]) == 2

    @pytest.mark.asyncio
    async def test_mark_apps_uninstalled_bulk_partial(
        self, mock_db_session, sample_app_table
    ):
        """mark_apps_uninstalled_bulk should handle partial success."""
        session, context_manager = mock_db_session

        call_count = [0]

        def execute_side_effect(*args, **kwargs):
            call_count[0] += 1
            result = MagicMock()
            if call_count[0] % 2 == 1:
                sample_app_table.status = "installed"
                result.first.return_value = (sample_app_table,)
            else:
                result.first.return_value = None
            return result

        session.execute = AsyncMock(side_effect=execute_side_effect)

        with (
            patch("services.app_service.logger"),
            patch("services.app_service.initialize_app_database"),
            patch("services.app_service.db_manager") as mock_db,
        ):
            mock_db.get_session.return_value = context_manager

            service = AppService()
            result = await service.mark_apps_uninstalled_bulk(["app1", "app2"])

            assert result["uninstalled_count"] == 1
            assert result["skipped_count"] == 1

    @pytest.mark.asyncio
    async def test_mark_apps_uninstalled_bulk_error_handling(self, mock_db_session):
        """mark_apps_uninstalled_bulk should handle exceptions."""
        session, context_manager = mock_db_session

        session.execute = AsyncMock(side_effect=Exception("DB error"))

        with (
            patch("services.app_service.logger"),
            patch("services.app_service.initialize_app_database"),
            patch("services.app_service.db_manager") as mock_db,
        ):
            mock_db.get_session.return_value = context_manager

            service = AppService()
            result = await service.mark_apps_uninstalled_bulk(["app1"])

            assert result["uninstalled_count"] == 0
            assert result["skipped_count"] == 1
            assert "DB error" in result["skipped"][0]["reason"]


class TestInstallApp:
    """Tests for install_app method."""

    @pytest.mark.asyncio
    async def test_install_app_success(
        self, mock_db_session, sample_app_table, sample_category_table
    ):
        """install_app should create installation record."""
        session, context_manager = mock_db_session

        result = MagicMock()
        result.first.return_value = (sample_app_table, sample_category_table)
        session.execute = AsyncMock(return_value=result)

        with (
            patch("services.app_service.logger") as mock_logger,
            patch("services.app_service.initialize_app_database"),
            patch("services.app_service.db_manager") as mock_db,
        ):
            mock_db.get_session.return_value = context_manager

            service = AppService()
            installation = await service.install_app("plex")

            assert isinstance(installation, AppInstallation)
            assert installation.app_id == "plex"
            assert installation.status == AppStatus.INSTALLING
            assert installation.version == "1.0.0"
            assert "plex" in service.installations
            mock_logger.info.assert_any_call(
                "Application marked as installing", app_id="plex"
            )

    @pytest.mark.asyncio
    async def test_install_app_with_config(
        self, mock_db_session, sample_app_table, sample_category_table
    ):
        """install_app should accept configuration."""
        session, context_manager = mock_db_session

        result = MagicMock()
        result.first.return_value = (sample_app_table, sample_category_table)
        session.execute = AsyncMock(return_value=result)

        with (
            patch("services.app_service.logger"),
            patch("services.app_service.initialize_app_database"),
            patch("services.app_service.db_manager") as mock_db,
        ):
            mock_db.get_session.return_value = context_manager

            service = AppService()
            config = {"port": 32400, "transcode": True}
            installation = await service.install_app("plex", config=config)

            assert installation.config == config

    @pytest.mark.asyncio
    async def test_install_app_not_found(self, mock_db_session):
        """install_app should raise ValueError when app not found."""
        session, context_manager = mock_db_session

        result = MagicMock()
        result.first.return_value = None
        session.execute = AsyncMock(return_value=result)

        with (
            patch("services.app_service.logger"),
            patch("services.app_service.initialize_app_database"),
            patch("services.app_service.db_manager") as mock_db,
        ):
            mock_db.get_session.return_value = context_manager

            service = AppService()
            with pytest.raises(ValueError, match="not found"):
                await service.install_app("nonexistent")

    @pytest.mark.asyncio
    async def test_install_app_stores_installation(
        self, mock_db_session, sample_app_table, sample_category_table
    ):
        """install_app should store installation in memory."""
        session, context_manager = mock_db_session

        result = MagicMock()
        result.first.return_value = (sample_app_table, sample_category_table)
        session.execute = AsyncMock(return_value=result)

        with (
            patch("services.app_service.logger"),
            patch("services.app_service.initialize_app_database"),
            patch("services.app_service.db_manager") as mock_db,
        ):
            mock_db.get_session.return_value = context_manager

            service = AppService()
            await service.install_app("plex")

            assert "plex" in service.installations
            assert service.installations["plex"].status == AppStatus.INSTALLING

    @pytest.mark.asyncio
    async def test_install_app_default_config(
        self, mock_db_session, sample_app_table, sample_category_table
    ):
        """install_app should use empty config by default."""
        session, context_manager = mock_db_session

        result = MagicMock()
        result.first.return_value = (sample_app_table, sample_category_table)
        session.execute = AsyncMock(return_value=result)

        with (
            patch("services.app_service.logger"),
            patch("services.app_service.initialize_app_database"),
            patch("services.app_service.db_manager") as mock_db,
        ):
            mock_db.get_session.return_value = context_manager

            service = AppService()
            installation = await service.install_app("plex")

            assert installation.config == {}

    @pytest.mark.asyncio
    async def test_install_app_sets_timestamp(
        self, mock_db_session, sample_app_table, sample_category_table
    ):
        """install_app should set installed_at timestamp."""
        session, context_manager = mock_db_session

        result = MagicMock()
        result.first.return_value = (sample_app_table, sample_category_table)
        session.execute = AsyncMock(return_value=result)

        with (
            patch("services.app_service.logger"),
            patch("services.app_service.initialize_app_database"),
            patch("services.app_service.db_manager") as mock_db,
        ):
            mock_db.get_session.return_value = context_manager

            service = AppService()
            installation = await service.install_app("plex")

            assert installation.installed_at is not None
            # Verify it's a valid ISO timestamp
            datetime.fromisoformat(installation.installed_at.replace("Z", "+00:00"))
