"""
Unit tests for services/database_service.py - App/Installation method delegation.

Tests installation-related methods that delegate to AppDatabaseService.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from models.app_catalog import InstalledApp


@pytest.fixture
def mock_app_service():
    """Create mock AppDatabaseService."""
    return MagicMock()


@pytest.fixture
def db_service_with_app_mock(mock_app_service):
    """Create DatabaseService with mocked app service."""
    with patch("services.database_service.DatabaseConnection"), \
         patch("services.database_service.UserDatabaseService"), \
         patch("services.database_service.ServerDatabaseService"), \
         patch("services.database_service.SessionDatabaseService"), \
         patch("services.database_service.AppDatabaseService") as MockApp, \
         patch("services.database_service.MetricsDatabaseService"), \
         patch("services.database_service.SystemDatabaseService"), \
         patch("services.database_service.ExportDatabaseService"), \
         patch("services.database_service.SchemaInitializer"):
        from services.database_service import DatabaseService
        MockApp.return_value = mock_app_service
        return DatabaseService()


@pytest.fixture
def sample_installed_app():
    """Create sample InstalledApp."""
    from models.app_catalog import InstallationStatus
    return InstalledApp(
        id="install-123",
        server_id="srv-123",
        app_id="app-456",
        container_name="my-app",
        status=InstallationStatus.RUNNING,
        config={"port": 8080},
        installed_at="2024-01-15T10:00:00Z",
    )


class TestCreateInstallation:
    """Tests for create_installation method."""

    @pytest.mark.asyncio
    async def test_create_installation_success(
        self, db_service_with_app_mock, mock_app_service, sample_installed_app
    ):
        """create_installation should delegate to app service."""
        mock_app_service.create_installation = AsyncMock(
            return_value=sample_installed_app
        )

        result = await db_service_with_app_mock.create_installation(
            id="install-123",
            server_id="srv-123",
            app_id="app-456",
            container_name="my-app",
            status="running",
            config={"port": 8080},
            installed_at="2024-01-15T10:00:00Z",
        )

        mock_app_service.create_installation.assert_awaited_once_with(
            "install-123",
            "srv-123",
            "app-456",
            "my-app",
            "running",
            {"port": 8080},
            "2024-01-15T10:00:00Z",
        )
        assert result == sample_installed_app

    @pytest.mark.asyncio
    async def test_create_installation_failure(
        self, db_service_with_app_mock, mock_app_service
    ):
        """create_installation should return None on failure."""
        mock_app_service.create_installation = AsyncMock(return_value=None)

        result = await db_service_with_app_mock.create_installation(
            id="install-123",
            server_id="srv-123",
            app_id="app-456",
            container_name="my-app",
            status="pending",
            config={},
            installed_at="2024-01-15T10:00:00Z",
        )

        assert result is None


class TestUpdateInstallation:
    """Tests for update_installation method."""

    @pytest.mark.asyncio
    async def test_update_installation_success(
        self, db_service_with_app_mock, mock_app_service
    ):
        """update_installation should delegate kwargs to app service."""
        mock_app_service.update_installation = AsyncMock(return_value=True)

        result = await db_service_with_app_mock.update_installation(
            "install-123", status="stopped", container_id="abc123"
        )

        mock_app_service.update_installation.assert_awaited_once_with(
            "install-123", status="stopped", container_id="abc123"
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_update_installation_single_field(
        self, db_service_with_app_mock, mock_app_service
    ):
        """update_installation should handle single field update."""
        mock_app_service.update_installation = AsyncMock(return_value=True)

        result = await db_service_with_app_mock.update_installation(
            "install-123", status="error"
        )

        mock_app_service.update_installation.assert_awaited_once_with(
            "install-123", status="error"
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_update_installation_failure(
        self, db_service_with_app_mock, mock_app_service
    ):
        """update_installation should return False on failure."""
        mock_app_service.update_installation = AsyncMock(return_value=False)

        result = await db_service_with_app_mock.update_installation(
            "nonexistent", status="running"
        )

        assert result is False


class TestGetInstallation:
    """Tests for get_installation method."""

    @pytest.mark.asyncio
    async def test_get_installation_found(
        self, db_service_with_app_mock, mock_app_service, sample_installed_app
    ):
        """get_installation should return installation when found."""
        mock_app_service.get_installation = AsyncMock(return_value=sample_installed_app)

        result = await db_service_with_app_mock.get_installation(
            server_id="srv-123", app_id="app-456"
        )

        mock_app_service.get_installation.assert_awaited_once_with("srv-123", "app-456")
        assert result == sample_installed_app

    @pytest.mark.asyncio
    async def test_get_installation_not_found(
        self, db_service_with_app_mock, mock_app_service
    ):
        """get_installation should return None when not found."""
        mock_app_service.get_installation = AsyncMock(return_value=None)

        result = await db_service_with_app_mock.get_installation(
            server_id="unknown", app_id="unknown"
        )

        assert result is None


class TestGetInstallationById:
    """Tests for get_installation_by_id method."""

    @pytest.mark.asyncio
    async def test_get_installation_by_id_found(
        self, db_service_with_app_mock, mock_app_service, sample_installed_app
    ):
        """get_installation_by_id should return installation when found."""
        mock_app_service.get_installation_by_id = AsyncMock(
            return_value=sample_installed_app
        )

        result = await db_service_with_app_mock.get_installation_by_id("install-123")

        mock_app_service.get_installation_by_id.assert_awaited_once_with("install-123")
        assert result == sample_installed_app

    @pytest.mark.asyncio
    async def test_get_installation_by_id_not_found(
        self, db_service_with_app_mock, mock_app_service
    ):
        """get_installation_by_id should return None when not found."""
        mock_app_service.get_installation_by_id = AsyncMock(return_value=None)

        result = await db_service_with_app_mock.get_installation_by_id("nonexistent")

        assert result is None


class TestGetInstallations:
    """Tests for get_installations method."""

    @pytest.mark.asyncio
    async def test_get_installations_returns_list(
        self, db_service_with_app_mock, mock_app_service, sample_installed_app
    ):
        """get_installations should return list of installations."""
        mock_app_service.get_installations = AsyncMock(
            return_value=[sample_installed_app]
        )

        result = await db_service_with_app_mock.get_installations("srv-123")

        mock_app_service.get_installations.assert_awaited_once_with("srv-123")
        assert result == [sample_installed_app]

    @pytest.mark.asyncio
    async def test_get_installations_empty(
        self, db_service_with_app_mock, mock_app_service
    ):
        """get_installations should return empty list when none."""
        mock_app_service.get_installations = AsyncMock(return_value=[])

        result = await db_service_with_app_mock.get_installations("srv-123")

        assert result == []


class TestGetAllInstallations:
    """Tests for get_all_installations method."""

    @pytest.mark.asyncio
    async def test_get_all_installations_returns_list(
        self, db_service_with_app_mock, mock_app_service, sample_installed_app
    ):
        """get_all_installations should return all installations."""
        mock_app_service.get_all_installations = AsyncMock(
            return_value=[sample_installed_app]
        )

        result = await db_service_with_app_mock.get_all_installations()

        mock_app_service.get_all_installations.assert_awaited_once()
        assert result == [sample_installed_app]

    @pytest.mark.asyncio
    async def test_get_all_installations_empty(
        self, db_service_with_app_mock, mock_app_service
    ):
        """get_all_installations should return empty list when none."""
        mock_app_service.get_all_installations = AsyncMock(return_value=[])

        result = await db_service_with_app_mock.get_all_installations()

        assert result == []


class TestDeleteInstallation:
    """Tests for delete_installation method."""

    @pytest.mark.asyncio
    async def test_delete_installation_success(
        self, db_service_with_app_mock, mock_app_service
    ):
        """delete_installation should delegate to app service."""
        mock_app_service.delete_installation = AsyncMock(return_value=True)

        result = await db_service_with_app_mock.delete_installation(
            server_id="srv-123", app_id="app-456"
        )

        mock_app_service.delete_installation.assert_awaited_once_with(
            "srv-123", "app-456"
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_installation_failure(
        self, db_service_with_app_mock, mock_app_service
    ):
        """delete_installation should return False on failure."""
        mock_app_service.delete_installation = AsyncMock(return_value=False)

        result = await db_service_with_app_mock.delete_installation(
            server_id="unknown", app_id="unknown"
        )

        assert result is False
