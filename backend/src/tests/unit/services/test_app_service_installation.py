"""
Unit tests for services/app_service.py - Installation Methods

Tests mark_app_installed, mark_app_uninstalled, install_app,
and bulk installation operations.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.app import (
    App,
    AppCategory,
    AppInstallation,
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


class TestMarkAppUninstalled:
    """Tests for mark_app_uninstalled method."""

    @pytest.mark.asyncio
    async def test_mark_app_uninstalled_success(self, mock_db_conn):
        """mark_app_uninstalled should update status to available."""
        mock_conn, mock_aiosqlite = mock_db_conn

        cursor_select = AsyncMock()
        cursor_select.fetchone.return_value = {"id": "plex"}

        cursor_update = AsyncMock()

        mock_aiosqlite.execute = AsyncMock(
            side_effect=[cursor_select, cursor_update]
        )
        mock_aiosqlite.commit = AsyncMock()

        mock_log = MagicMock()
        with patch("services.app_service.logger") as mock_logger:
            service = AppService(connection=mock_conn, log_service=mock_log)
            success = await service.mark_app_uninstalled("plex")

            assert success is True
            mock_aiosqlite.commit.assert_called_once()
            mock_logger.info.assert_any_call(
                "Application marked as uninstalled", app_id="plex"
            )

    @pytest.mark.asyncio
    async def test_mark_app_uninstalled_not_found(self, mock_db_conn):
        """mark_app_uninstalled should return False when not found."""
        mock_conn, mock_aiosqlite = mock_db_conn

        cursor_select = AsyncMock()
        cursor_select.fetchone.return_value = None
        mock_aiosqlite.execute = AsyncMock(return_value=cursor_select)

        mock_log = MagicMock()
        with patch("services.app_service.logger"):
            service = AppService(connection=mock_conn, log_service=mock_log)
            success = await service.mark_app_uninstalled("nonexistent")

            assert success is False


class TestMarkAppInstalled:
    """Tests for mark_app_installed method."""

    @pytest.mark.asyncio
    async def test_mark_app_installed_success(self, mock_db_conn):
        """mark_app_installed should update status and server_id."""
        mock_conn, mock_aiosqlite = mock_db_conn

        cursor_select = AsyncMock()
        cursor_select.fetchone.return_value = {"id": "plex"}

        cursor_update = AsyncMock()

        mock_aiosqlite.execute = AsyncMock(
            side_effect=[cursor_select, cursor_update]
        )
        mock_aiosqlite.commit = AsyncMock()

        mock_log = MagicMock()
        with patch("services.app_service.logger") as mock_logger:
            service = AppService(connection=mock_conn, log_service=mock_log)
            success = await service.mark_app_installed("plex", "srv-123")

            assert success is True
            mock_aiosqlite.commit.assert_called_once()
            mock_logger.info.assert_any_call(
                "Application marked as installed",
                app_id="plex",
                server_id="srv-123",
            )

    @pytest.mark.asyncio
    async def test_mark_app_installed_not_found(self, mock_db_conn):
        """mark_app_installed should return False when not found."""
        mock_conn, mock_aiosqlite = mock_db_conn

        cursor_select = AsyncMock()
        cursor_select.fetchone.return_value = None
        mock_aiosqlite.execute = AsyncMock(return_value=cursor_select)

        mock_log = MagicMock()
        with patch("services.app_service.logger") as mock_logger:
            service = AppService(connection=mock_conn, log_service=mock_log)
            success = await service.mark_app_installed("nonexistent", "srv-123")

            assert success is False
            mock_logger.warning.assert_called_with(
                "Application not found for marking installed",
                app_id="nonexistent",
            )

    @pytest.mark.asyncio
    async def test_mark_app_installed_with_casaos_prefix(self, mock_db_conn):
        """mark_app_installed should strip casaos- prefix if not found."""
        mock_conn, mock_aiosqlite = mock_db_conn

        call_count = [0]

        def execute_side_effect(*args, **kwargs):
            call_count[0] += 1
            cursor = AsyncMock()
            if call_count[0] == 1:
                # casaos-plex not found
                cursor.fetchone.return_value = None
            elif call_count[0] == 2:
                # plex found after stripping prefix
                cursor.fetchone.return_value = {"id": "plex"}
            else:
                # UPDATE statement
                cursor.fetchone.return_value = None
            return cursor

        mock_aiosqlite.execute = AsyncMock(side_effect=execute_side_effect)
        mock_aiosqlite.commit = AsyncMock()

        mock_log = MagicMock()
        with patch("services.app_service.logger"):
            service = AppService(connection=mock_conn, log_service=mock_log)
            success = await service.mark_app_installed("casaos-plex", "srv-123")

            assert success is True

    @pytest.mark.asyncio
    async def test_mark_app_installed_with_prefix_not_found(self, mock_db_conn):
        """mark_app_installed should return False if prefix stripping fails."""
        mock_conn, mock_aiosqlite = mock_db_conn

        cursor_select = AsyncMock()
        cursor_select.fetchone.return_value = None
        mock_aiosqlite.execute = AsyncMock(return_value=cursor_select)

        mock_log = MagicMock()
        with patch("services.app_service.logger"):
            service = AppService(connection=mock_conn, log_service=mock_log)
            success = await service.mark_app_installed(
                "casaos-unknown", "srv-123"
            )

            assert success is False


class TestMarkAppsUninstalledBulk:
    """Tests for mark_apps_uninstalled_bulk method."""

    @pytest.mark.asyncio
    async def test_mark_apps_uninstalled_bulk_success(self, mock_db_conn):
        """mark_apps_uninstalled_bulk should uninstall multiple apps."""
        mock_conn, mock_aiosqlite = mock_db_conn
        mock_log = MagicMock()

        with patch("services.app_service.logger"):
            service = AppService(connection=mock_conn, log_service=mock_log)

        with patch.object(
            service, "mark_app_uninstalled", new_callable=AsyncMock
        ) as mock_uninstall:
            mock_uninstall.return_value = True
            result = await service.mark_apps_uninstalled_bulk(
                ["plex", "jellyfin"]
            )

            assert result["uninstalled_count"] == 2
            assert len(result["uninstalled"]) == 2

    @pytest.mark.asyncio
    async def test_mark_apps_uninstalled_bulk_partial(self, mock_db_conn):
        """mark_apps_uninstalled_bulk should handle partial success."""
        mock_conn, mock_aiosqlite = mock_db_conn
        mock_log = MagicMock()

        with patch("services.app_service.logger"):
            service = AppService(connection=mock_conn, log_service=mock_log)

        async def uninstall_side_effect(app_id):
            return app_id == "app1"

        with patch.object(
            service, "mark_app_uninstalled", side_effect=uninstall_side_effect
        ):
            result = await service.mark_apps_uninstalled_bulk(["app1", "app2"])

            assert result["uninstalled_count"] == 1
            assert result["skipped_count"] == 1

    @pytest.mark.asyncio
    async def test_mark_apps_uninstalled_bulk_error_handling(
        self, mock_db_conn
    ):
        """mark_apps_uninstalled_bulk should handle exceptions."""
        mock_conn, mock_aiosqlite = mock_db_conn
        mock_log = MagicMock()

        with patch("services.app_service.logger"):
            service = AppService(connection=mock_conn, log_service=mock_log)

        with patch.object(
            service,
            "mark_app_uninstalled",
            new_callable=AsyncMock,
            side_effect=Exception("DB error"),
        ):
            result = await service.mark_apps_uninstalled_bulk(["app1"])

            assert result["uninstalled_count"] == 0
            assert result["skipped_count"] == 1
            assert "DB error" in result["skipped"][0]["reason"]


class TestInstallApp:
    """Tests for install_app method."""

    @pytest.mark.asyncio
    async def test_install_app_success(self, mock_db_conn, sample_app_row):
        """install_app should create installation record."""
        mock_conn, mock_aiosqlite = mock_db_conn

        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = sample_app_row
        mock_aiosqlite.execute.return_value = mock_cursor

        mock_log = MagicMock()
        with patch("services.app_service.logger") as mock_logger:
            service = AppService(connection=mock_conn, log_service=mock_log)
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
    async def test_install_app_with_config(self, mock_db_conn, sample_app_row):
        """install_app should accept configuration."""
        mock_conn, mock_aiosqlite = mock_db_conn

        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = sample_app_row
        mock_aiosqlite.execute.return_value = mock_cursor

        mock_log = MagicMock()
        with patch("services.app_service.logger"):
            service = AppService(connection=mock_conn, log_service=mock_log)
            config = {"port": 32400, "transcode": True}
            installation = await service.install_app("plex", config=config)

            assert installation.config == config

    @pytest.mark.asyncio
    async def test_install_app_not_found(self, mock_db_conn):
        """install_app should raise ValueError when app not found."""
        mock_conn, mock_aiosqlite = mock_db_conn

        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = None
        mock_aiosqlite.execute.return_value = mock_cursor

        mock_log = MagicMock()
        with patch("services.app_service.logger"):
            service = AppService(connection=mock_conn, log_service=mock_log)
            with pytest.raises(ValueError, match="not found"):
                await service.install_app("nonexistent")

    @pytest.mark.asyncio
    async def test_install_app_stores_installation(
        self, mock_db_conn, sample_app_row
    ):
        """install_app should store installation in memory."""
        mock_conn, mock_aiosqlite = mock_db_conn

        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = sample_app_row
        mock_aiosqlite.execute.return_value = mock_cursor

        mock_log = MagicMock()
        with patch("services.app_service.logger"):
            service = AppService(connection=mock_conn, log_service=mock_log)
            await service.install_app("plex")

            assert "plex" in service.installations
            assert service.installations["plex"].status == AppStatus.INSTALLING

    @pytest.mark.asyncio
    async def test_install_app_default_config(
        self, mock_db_conn, sample_app_row
    ):
        """install_app should use empty config by default."""
        mock_conn, mock_aiosqlite = mock_db_conn

        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = sample_app_row
        mock_aiosqlite.execute.return_value = mock_cursor

        mock_log = MagicMock()
        with patch("services.app_service.logger"):
            service = AppService(connection=mock_conn, log_service=mock_log)
            installation = await service.install_app("plex")

            assert installation.config == {}

    @pytest.mark.asyncio
    async def test_install_app_sets_timestamp(
        self, mock_db_conn, sample_app_row
    ):
        """install_app should set installed_at timestamp."""
        mock_conn, mock_aiosqlite = mock_db_conn

        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = sample_app_row
        mock_aiosqlite.execute.return_value = mock_cursor

        mock_log = MagicMock()
        with patch("services.app_service.logger"):
            service = AppService(connection=mock_conn, log_service=mock_log)
            installation = await service.install_app("plex")

            assert installation.installed_at is not None
            # Verify it is a valid ISO timestamp
            datetime.fromisoformat(
                installation.installed_at.replace("Z", "+00:00")
            )
