"""Tests for app MCP tools."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from tools.app_tools import AppTools
from models.app_catalog import AppDefinition, AppCategory, InstallationStatus


@pytest.fixture
def mock_catalog_service():
    """Create mock catalog service."""
    svc = MagicMock()
    svc.list_apps = MagicMock(return_value=[
        AppDefinition(
            id="portainer",
            name="Portainer",
            description="Docker management",
            category=AppCategory.UTILITY,
            image="portainer/portainer-ce:latest",
            ports=[], volumes=[], env_vars=[]
        )
    ])
    svc.get_app = MagicMock(return_value=AppDefinition(
        id="portainer",
        name="Portainer",
        description="Docker management",
        category=AppCategory.UTILITY,
        image="portainer/portainer-ce:latest",
        ports=[], volumes=[], env_vars=[]
    ))
    return svc


@pytest.fixture
def mock_deployment_service():
    """Create mock deployment service."""
    svc = MagicMock()
    svc.install_app = AsyncMock()
    svc.uninstall_app = AsyncMock()
    svc.start_app = AsyncMock()
    svc.stop_app = AsyncMock()
    svc.get_installed_apps = AsyncMock(return_value=[])
    svc.get_app_status = AsyncMock()
    return svc


@pytest.fixture
def app_tools(mock_catalog_service, mock_deployment_service):
    """Create app tools with mocks."""
    return AppTools(mock_catalog_service, mock_deployment_service)


class TestListCatalog:
    """Tests for list_catalog tool."""

    @pytest.mark.asyncio
    async def test_list_catalog_success(self, app_tools):
        """Should list all apps."""
        result = await app_tools.list_catalog()

        assert result["success"] is True
        assert len(result["data"]["apps"]) == 1

    @pytest.mark.asyncio
    async def test_list_catalog_with_category(self, app_tools, mock_catalog_service):
        """Should filter by category."""
        mock_catalog_service.list_apps.return_value = []

        result = await app_tools.list_catalog(category="storage")

        mock_catalog_service.list_apps.assert_called_with(category="storage")


class TestGetAppDefinition:
    """Tests for get_app_definition tool."""

    @pytest.mark.asyncio
    async def test_get_app_success(self, app_tools):
        """Should return app definition."""
        result = await app_tools.get_app_definition(app_id="portainer")

        assert result["success"] is True
        assert result["data"]["id"] == "portainer"

    @pytest.mark.asyncio
    async def test_get_app_not_found(self, app_tools, mock_catalog_service):
        """Should return error for unknown app."""
        mock_catalog_service.get_app.return_value = None

        result = await app_tools.get_app_definition(app_id="unknown")

        assert result["success"] is False
        assert result["error"] == "APP_NOT_FOUND"


class TestInstallApp:
    """Tests for install_app tool."""

    @pytest.mark.asyncio
    async def test_install_success(self, app_tools, mock_deployment_service):
        """Should install app successfully."""
        mock_deployment_service.install_app.return_value = MagicMock(id="inst-123")

        result = await app_tools.install_app(
            server_id="server-456",
            app_id="portainer",
            config={}
        )

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_install_failure(self, app_tools, mock_deployment_service):
        """Should handle install failure."""
        mock_deployment_service.install_app.return_value = None

        result = await app_tools.install_app(
            server_id="server-456",
            app_id="portainer",
            config={}
        )

        assert result["success"] is False


class TestUninstallApp:
    """Tests for uninstall_app tool."""

    @pytest.mark.asyncio
    async def test_uninstall_success(self, app_tools, mock_deployment_service):
        """Should uninstall app successfully."""
        mock_deployment_service.uninstall_app.return_value = True

        result = await app_tools.uninstall_app(
            server_id="server-456",
            app_id="portainer"
        )

        assert result["success"] is True
