"""
Unit tests for services/database_service.py - Export/Import method delegation.

Tests export and import methods that delegate to ExportDatabaseService.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def mock_export_service():
    """Create mock ExportDatabaseService."""
    return MagicMock()


@pytest.fixture
def db_service_with_export_mock(mock_export_service):
    """Create DatabaseService with mocked export service."""
    with (
        patch("services.database_service.DatabaseConnection"),
        patch("services.database_service.UserDatabaseService"),
        patch("services.database_service.ServerDatabaseService"),
        patch("services.database_service.SessionDatabaseService"),
        patch("services.database_service.AppDatabaseService"),
        patch("services.database_service.MetricsDatabaseService"),
        patch("services.database_service.SystemDatabaseService"),
        patch("services.database_service.ExportDatabaseService") as MockExport,
        patch("services.database_service.SchemaInitializer"),
    ):
        from services.database_service import DatabaseService

        MockExport.return_value = mock_export_service
        return DatabaseService()


@pytest.fixture
def sample_user_export():
    """Create sample exported user data."""
    return [
        {
            "id": "user-123",
            "username": "admin",
            "email": "admin@example.com",
            "role": "admin",
        },
        {
            "id": "user-456",
            "username": "user1",
            "email": "user1@example.com",
            "role": "user",
        },
    ]


@pytest.fixture
def sample_server_export():
    """Create sample exported server data."""
    return [
        {
            "id": "srv-123",
            "name": "Server 1",
            "host": "192.168.1.100",
            "port": 22,
        },
        {
            "id": "srv-456",
            "name": "Server 2",
            "host": "192.168.1.101",
            "port": 22,
        },
    ]


@pytest.fixture
def sample_settings_export():
    """Create sample exported settings data."""
    return {
        "general": {"app_name": "Tomo", "timezone": "UTC"},
        "security": {"session_timeout": 3600, "max_login_attempts": 5},
    }


class TestExportUsers:
    """Tests for export_users method."""

    @pytest.mark.asyncio
    async def test_export_users_returns_list(
        self, db_service_with_export_mock, mock_export_service, sample_user_export
    ):
        """export_users should return list of user dicts."""
        mock_export_service.export_users = AsyncMock(return_value=sample_user_export)

        result = await db_service_with_export_mock.export_users()

        mock_export_service.export_users.assert_awaited_once()
        assert result == sample_user_export

    @pytest.mark.asyncio
    async def test_export_users_empty(
        self, db_service_with_export_mock, mock_export_service
    ):
        """export_users should return empty list when no users."""
        mock_export_service.export_users = AsyncMock(return_value=[])

        result = await db_service_with_export_mock.export_users()

        assert result == []


class TestExportServers:
    """Tests for export_servers method."""

    @pytest.mark.asyncio
    async def test_export_servers_returns_list(
        self, db_service_with_export_mock, mock_export_service, sample_server_export
    ):
        """export_servers should return list of server dicts."""
        mock_export_service.export_servers = AsyncMock(
            return_value=sample_server_export
        )

        result = await db_service_with_export_mock.export_servers()

        mock_export_service.export_servers.assert_awaited_once()
        assert result == sample_server_export

    @pytest.mark.asyncio
    async def test_export_servers_empty(
        self, db_service_with_export_mock, mock_export_service
    ):
        """export_servers should return empty list when no servers."""
        mock_export_service.export_servers = AsyncMock(return_value=[])

        result = await db_service_with_export_mock.export_servers()

        assert result == []


class TestExportSettings:
    """Tests for export_settings method."""

    @pytest.mark.asyncio
    async def test_export_settings_returns_dict(
        self, db_service_with_export_mock, mock_export_service, sample_settings_export
    ):
        """export_settings should return settings dict."""
        mock_export_service.export_settings = AsyncMock(
            return_value=sample_settings_export
        )

        result = await db_service_with_export_mock.export_settings()

        mock_export_service.export_settings.assert_awaited_once()
        assert result == sample_settings_export

    @pytest.mark.asyncio
    async def test_export_settings_empty(
        self, db_service_with_export_mock, mock_export_service
    ):
        """export_settings should return empty dict when no settings."""
        mock_export_service.export_settings = AsyncMock(return_value={})

        result = await db_service_with_export_mock.export_settings()

        assert result == {}


class TestImportUsers:
    """Tests for import_users method."""

    @pytest.mark.asyncio
    async def test_import_users_default(
        self, db_service_with_export_mock, mock_export_service, sample_user_export
    ):
        """import_users should use default overwrite=False."""
        mock_export_service.import_users = AsyncMock(return_value=None)

        result = await db_service_with_export_mock.import_users(sample_user_export)

        mock_export_service.import_users.assert_awaited_once_with(
            sample_user_export, False
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_import_users_overwrite(
        self, db_service_with_export_mock, mock_export_service, sample_user_export
    ):
        """import_users should pass overwrite=True."""
        mock_export_service.import_users = AsyncMock(return_value=None)

        await db_service_with_export_mock.import_users(
            sample_user_export, overwrite=True
        )

        mock_export_service.import_users.assert_awaited_once_with(
            sample_user_export, True
        )

    @pytest.mark.asyncio
    async def test_import_users_empty_list(
        self, db_service_with_export_mock, mock_export_service
    ):
        """import_users should handle empty list."""
        mock_export_service.import_users = AsyncMock(return_value=None)

        await db_service_with_export_mock.import_users([])

        mock_export_service.import_users.assert_awaited_once_with([], False)


class TestImportServers:
    """Tests for import_servers method."""

    @pytest.mark.asyncio
    async def test_import_servers_default(
        self, db_service_with_export_mock, mock_export_service, sample_server_export
    ):
        """import_servers should use default overwrite=False."""
        mock_export_service.import_servers = AsyncMock(return_value=None)

        result = await db_service_with_export_mock.import_servers(sample_server_export)

        mock_export_service.import_servers.assert_awaited_once_with(
            sample_server_export, False
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_import_servers_overwrite(
        self, db_service_with_export_mock, mock_export_service, sample_server_export
    ):
        """import_servers should pass overwrite=True."""
        mock_export_service.import_servers = AsyncMock(return_value=None)

        await db_service_with_export_mock.import_servers(
            sample_server_export, overwrite=True
        )

        mock_export_service.import_servers.assert_awaited_once_with(
            sample_server_export, True
        )

    @pytest.mark.asyncio
    async def test_import_servers_empty_list(
        self, db_service_with_export_mock, mock_export_service
    ):
        """import_servers should handle empty list."""
        mock_export_service.import_servers = AsyncMock(return_value=None)

        await db_service_with_export_mock.import_servers([])

        mock_export_service.import_servers.assert_awaited_once_with([], False)


class TestImportSettings:
    """Tests for import_settings method."""

    @pytest.mark.asyncio
    async def test_import_settings_default(
        self, db_service_with_export_mock, mock_export_service, sample_settings_export
    ):
        """import_settings should use default overwrite=False."""
        mock_export_service.import_settings = AsyncMock(return_value=None)

        result = await db_service_with_export_mock.import_settings(
            sample_settings_export
        )

        mock_export_service.import_settings.assert_awaited_once_with(
            sample_settings_export, False
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_import_settings_overwrite(
        self, db_service_with_export_mock, mock_export_service, sample_settings_export
    ):
        """import_settings should pass overwrite=True."""
        mock_export_service.import_settings = AsyncMock(return_value=None)

        await db_service_with_export_mock.import_settings(
            sample_settings_export, overwrite=True
        )

        mock_export_service.import_settings.assert_awaited_once_with(
            sample_settings_export, True
        )

    @pytest.mark.asyncio
    async def test_import_settings_empty_dict(
        self, db_service_with_export_mock, mock_export_service
    ):
        """import_settings should handle empty dict."""
        mock_export_service.import_settings = AsyncMock(return_value=None)

        await db_service_with_export_mock.import_settings({})

        mock_export_service.import_settings.assert_awaited_once_with({}, False)
