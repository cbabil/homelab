"""
Unit tests for services/database_service.py - System and schema method delegation.

Tests system info, component versions, and schema initialization methods.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_system_service():
    """Create mock SystemDatabaseService."""
    return MagicMock()


@pytest.fixture
def mock_schema_service():
    """Create mock SchemaInitializer."""
    return MagicMock()


@pytest.fixture
def db_service_with_system_mock(mock_system_service, mock_schema_service):
    """Create DatabaseService with mocked system and schema services."""
    with patch("services.database_service.DatabaseConnection"), \
         patch("services.database_service.UserDatabaseService"), \
         patch("services.database_service.ServerDatabaseService"), \
         patch("services.database_service.SessionDatabaseService"), \
         patch("services.database_service.AppDatabaseService"), \
         patch("services.database_service.MetricsDatabaseService"), \
         patch("services.database_service.SystemDatabaseService") as MockSystem, \
         patch("services.database_service.ExportDatabaseService"), \
         patch("services.database_service.SchemaInitializer") as MockSchema:
        from services.database_service import DatabaseService
        MockSystem.return_value = mock_system_service
        MockSchema.return_value = mock_schema_service
        return DatabaseService()


class TestGetSystemInfo:
    """Tests for get_system_info method."""

    @pytest.mark.asyncio
    async def test_get_system_info_found(
        self, db_service_with_system_mock, mock_system_service
    ):
        """get_system_info should return system info dict."""
        system_info = {
            "app_name": "Tomo",
            "is_setup": True,
            "setup_completed_at": "2024-01-15T10:00:00Z",
        }
        mock_system_service.get_system_info = AsyncMock(return_value=system_info)

        result = await db_service_with_system_mock.get_system_info()

        mock_system_service.get_system_info.assert_awaited_once()
        assert result == system_info

    @pytest.mark.asyncio
    async def test_get_system_info_none(
        self, db_service_with_system_mock, mock_system_service
    ):
        """get_system_info should return None when not found."""
        mock_system_service.get_system_info = AsyncMock(return_value=None)

        result = await db_service_with_system_mock.get_system_info()

        assert result is None


class TestIsSystemSetup:
    """Tests for is_system_setup method."""

    @pytest.mark.asyncio
    async def test_is_system_setup_true(
        self, db_service_with_system_mock, mock_system_service
    ):
        """is_system_setup should return True when setup complete."""
        mock_system_service.is_system_setup = AsyncMock(return_value=True)

        result = await db_service_with_system_mock.is_system_setup()

        mock_system_service.is_system_setup.assert_awaited_once()
        assert result is True

    @pytest.mark.asyncio
    async def test_is_system_setup_false(
        self, db_service_with_system_mock, mock_system_service
    ):
        """is_system_setup should return False when not setup."""
        mock_system_service.is_system_setup = AsyncMock(return_value=False)

        result = await db_service_with_system_mock.is_system_setup()

        assert result is False


class TestMarkSystemSetupComplete:
    """Tests for mark_system_setup_complete method."""

    @pytest.mark.asyncio
    async def test_mark_system_setup_complete_success(
        self, db_service_with_system_mock, mock_system_service
    ):
        """mark_system_setup_complete should delegate to system service."""
        mock_system_service.mark_system_setup_complete = AsyncMock(return_value=True)

        result = await db_service_with_system_mock.mark_system_setup_complete(
            "user-123"
        )

        mock_system_service.mark_system_setup_complete.assert_awaited_once_with(
            "user-123"
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_mark_system_setup_complete_failure(
        self, db_service_with_system_mock, mock_system_service
    ):
        """mark_system_setup_complete should return False on failure."""
        mock_system_service.mark_system_setup_complete = AsyncMock(return_value=False)

        result = await db_service_with_system_mock.mark_system_setup_complete(
            "user-123"
        )

        assert result is False


class TestUpdateSystemInfo:
    """Tests for update_system_info method."""

    @pytest.mark.asyncio
    async def test_update_system_info_success(
        self, db_service_with_system_mock, mock_system_service
    ):
        """update_system_info should delegate kwargs to system service."""
        mock_system_service.update_system_info = AsyncMock(return_value=True)

        result = await db_service_with_system_mock.update_system_info(
            app_name="New Name", license_type="pro"
        )

        mock_system_service.update_system_info.assert_awaited_once_with(
            app_name="New Name", license_type="pro"
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_update_system_info_failure(
        self, db_service_with_system_mock, mock_system_service
    ):
        """update_system_info should return False on failure."""
        mock_system_service.update_system_info = AsyncMock(return_value=False)

        result = await db_service_with_system_mock.update_system_info(app_name="X")

        assert result is False


class TestVerifyDatabaseConnection:
    """Tests for verify_database_connection method."""

    @pytest.mark.asyncio
    async def test_verify_database_connection_success(
        self, db_service_with_system_mock, mock_system_service
    ):
        """verify_database_connection should return True when valid."""
        mock_system_service.verify_database_connection = AsyncMock(return_value=True)

        result = await db_service_with_system_mock.verify_database_connection()

        mock_system_service.verify_database_connection.assert_awaited_once()
        assert result is True

    @pytest.mark.asyncio
    async def test_verify_database_connection_failure(
        self, db_service_with_system_mock, mock_system_service
    ):
        """verify_database_connection should return False on failure."""
        mock_system_service.verify_database_connection = AsyncMock(return_value=False)

        result = await db_service_with_system_mock.verify_database_connection()

        assert result is False


class TestComponentVersions:
    """Tests for component version methods."""

    @pytest.mark.asyncio
    async def test_initialize_component_versions_table(
        self, db_service_with_system_mock, mock_schema_service
    ):
        """initialize_component_versions_table should delegate to schema."""
        mock_schema_service.initialize_component_versions_table = AsyncMock(
            return_value=True
        )

        result = await db_service_with_system_mock.initialize_component_versions_table()

        mock_schema_service.initialize_component_versions_table.assert_awaited_once()
        assert result is True

    @pytest.mark.asyncio
    async def test_get_component_versions(
        self, db_service_with_system_mock, mock_system_service
    ):
        """get_component_versions should return list of versions."""
        versions = [
            {"component": "backend", "version": "1.0.0"},
            {"component": "frontend", "version": "1.0.0"},
        ]
        mock_system_service.get_component_versions = AsyncMock(return_value=versions)

        result = await db_service_with_system_mock.get_component_versions()

        mock_system_service.get_component_versions.assert_awaited_once()
        assert result == versions

    @pytest.mark.asyncio
    async def test_get_component_version_found(
        self, db_service_with_system_mock, mock_system_service
    ):
        """get_component_version should return version dict when found."""
        version = {"component": "backend", "version": "1.0.0"}
        mock_system_service.get_component_version = AsyncMock(return_value=version)

        result = await db_service_with_system_mock.get_component_version("backend")

        mock_system_service.get_component_version.assert_awaited_once_with("backend")
        assert result == version

    @pytest.mark.asyncio
    async def test_get_component_version_not_found(
        self, db_service_with_system_mock, mock_system_service
    ):
        """get_component_version should return None when not found."""
        mock_system_service.get_component_version = AsyncMock(return_value=None)

        result = await db_service_with_system_mock.get_component_version("unknown")

        assert result is None

    @pytest.mark.asyncio
    async def test_update_component_version_success(
        self, db_service_with_system_mock, mock_system_service
    ):
        """update_component_version should delegate to system service."""
        mock_system_service.update_component_version = AsyncMock(return_value=True)

        result = await db_service_with_system_mock.update_component_version(
            "backend", "1.1.0"
        )

        mock_system_service.update_component_version.assert_awaited_once_with(
            "backend", "1.1.0"
        )
        assert result is True


class TestSchemaInitialization:
    """Tests for schema initialization methods."""

    @pytest.mark.asyncio
    async def test_initialize_system_info_table(
        self, db_service_with_system_mock, mock_schema_service
    ):
        """initialize_system_info_table should delegate to schema."""
        mock_schema_service.initialize_system_info_table = AsyncMock(return_value=True)

        result = await db_service_with_system_mock.initialize_system_info_table()

        mock_schema_service.initialize_system_info_table.assert_awaited_once()
        assert result is True

    @pytest.mark.asyncio
    async def test_initialize_users_table(
        self, db_service_with_system_mock, mock_schema_service
    ):
        """initialize_users_table should delegate to schema."""
        mock_schema_service.initialize_users_table = AsyncMock(return_value=True)

        result = await db_service_with_system_mock.initialize_users_table()

        mock_schema_service.initialize_users_table.assert_awaited_once()
        assert result is True

    @pytest.mark.asyncio
    async def test_initialize_sessions_table(
        self, db_service_with_system_mock, mock_schema_service
    ):
        """initialize_sessions_table should delegate to schema."""
        mock_schema_service.initialize_sessions_table = AsyncMock(return_value=True)

        result = await db_service_with_system_mock.initialize_sessions_table()

        mock_schema_service.initialize_sessions_table.assert_awaited_once()
        assert result is True

    @pytest.mark.asyncio
    async def test_initialize_account_locks_table(
        self, db_service_with_system_mock, mock_schema_service
    ):
        """initialize_account_locks_table should delegate to schema."""
        mock_schema_service.initialize_account_locks_table = AsyncMock(
            return_value=True
        )

        result = await db_service_with_system_mock.initialize_account_locks_table()

        mock_schema_service.initialize_account_locks_table.assert_awaited_once()
        assert result is True

    @pytest.mark.asyncio
    async def test_initialize_notifications_table(
        self, db_service_with_system_mock, mock_schema_service
    ):
        """initialize_notifications_table should delegate to schema."""
        mock_schema_service.initialize_notifications_table = AsyncMock(
            return_value=True
        )

        result = await db_service_with_system_mock.initialize_notifications_table()

        mock_schema_service.initialize_notifications_table.assert_awaited_once()
        assert result is True

    @pytest.mark.asyncio
    async def test_initialize_retention_settings_table(
        self, db_service_with_system_mock, mock_schema_service
    ):
        """initialize_retention_settings_table should delegate to schema."""
        mock_schema_service.initialize_retention_settings_table = AsyncMock(
            return_value=True
        )

        result = await db_service_with_system_mock.initialize_retention_settings_table()

        mock_schema_service.initialize_retention_settings_table.assert_awaited_once()
        assert result is True

    @pytest.mark.asyncio
    async def test_initialize_servers_table(
        self, db_service_with_system_mock, mock_schema_service
    ):
        """initialize_servers_table should delegate to schema."""
        mock_schema_service.initialize_servers_table = AsyncMock(return_value=True)

        result = await db_service_with_system_mock.initialize_servers_table()

        mock_schema_service.initialize_servers_table.assert_awaited_once()
        assert result is True

    @pytest.mark.asyncio
    async def test_initialize_agents_table(
        self, db_service_with_system_mock, mock_schema_service
    ):
        """initialize_agents_table should delegate to schema."""
        mock_schema_service.initialize_agents_table = AsyncMock(return_value=True)

        result = await db_service_with_system_mock.initialize_agents_table()

        mock_schema_service.initialize_agents_table.assert_awaited_once()
        assert result is True

    @pytest.mark.asyncio
    async def test_initialize_installed_apps_table(
        self, db_service_with_system_mock, mock_schema_service
    ):
        """initialize_installed_apps_table should delegate to schema."""
        mock_schema_service.initialize_installed_apps_table = AsyncMock(
            return_value=True
        )

        result = await db_service_with_system_mock.initialize_installed_apps_table()

        mock_schema_service.initialize_installed_apps_table.assert_awaited_once()
        assert result is True

    @pytest.mark.asyncio
    async def test_initialize_metrics_tables(
        self, db_service_with_system_mock, mock_schema_service
    ):
        """initialize_metrics_tables should delegate to schema."""
        mock_schema_service.initialize_metrics_tables = AsyncMock(return_value=True)

        result = await db_service_with_system_mock.initialize_metrics_tables()

        mock_schema_service.initialize_metrics_tables.assert_awaited_once()
        assert result is True


class TestMigrations:
    """Tests for migration methods."""

    @pytest.mark.asyncio
    async def test_run_installed_apps_migrations(
        self, db_service_with_system_mock, mock_schema_service
    ):
        """run_installed_apps_migrations should delegate to schema."""
        mock_schema_service.run_installed_apps_migrations = AsyncMock(return_value=None)

        result = await db_service_with_system_mock.run_installed_apps_migrations()

        mock_schema_service.run_installed_apps_migrations.assert_awaited_once()
        assert result is None

    @pytest.mark.asyncio
    async def test_run_users_migrations(
        self, db_service_with_system_mock, mock_schema_service
    ):
        """run_users_migrations should delegate to schema."""
        mock_schema_service.run_users_migrations = AsyncMock(return_value=None)

        result = await db_service_with_system_mock.run_users_migrations()

        mock_schema_service.run_users_migrations.assert_awaited_once()
        assert result is None
