"""
App Tools Unit Tests - Get App Operations

Tests for get_app method and initialization.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tools.app.tools import AppTools


class TestAppToolsInit:
    """Tests for AppTools initialization."""

    def test_initialization(self):
        """Test AppTools is initialized correctly."""
        mock_app_service = MagicMock()
        mock_marketplace_service = MagicMock()
        mock_deployment_service = MagicMock()

        with patch("tools.app.tools.logger"):
            tools = AppTools(
                mock_app_service,
                mock_marketplace_service,
                mock_deployment_service,
            )

        assert tools.app_service == mock_app_service
        assert tools.marketplace_service == mock_marketplace_service
        assert tools.deployment_service == mock_deployment_service


class TestGetServerName:
    """Tests for _get_server_name helper."""

    @pytest.fixture
    def mock_services(self):
        """Create mock services."""
        return {
            "app_service": MagicMock(),
            "marketplace_service": MagicMock(),
            "deployment_service": MagicMock(),
        }

    @pytest.fixture
    def app_tools(self, mock_services):
        """Create AppTools instance."""
        with patch("tools.app.tools.logger"):
            return AppTools(
                mock_services["app_service"],
                mock_services["marketplace_service"],
                mock_services["deployment_service"],
            )

    @pytest.mark.asyncio
    async def test_get_server_name_success(self, app_tools, mock_services):
        """Test getting server name successfully."""
        server = MagicMock()
        server.name = "my-server"
        mock_services["deployment_service"].server_service.get_server = AsyncMock(
            return_value=server
        )

        result = await app_tools._get_server_name("server-123")

        assert result == "my-server"

    @pytest.mark.asyncio
    async def test_get_server_name_no_server(self, app_tools, mock_services):
        """Test getting server name when server not found."""
        mock_services["deployment_service"].server_service.get_server = AsyncMock(
            return_value=None
        )

        result = await app_tools._get_server_name("server-123")

        assert result == "server-123"

    @pytest.mark.asyncio
    async def test_get_server_name_exception(self, app_tools, mock_services):
        """Test getting server name handles exceptions."""
        mock_services["deployment_service"].server_service.get_server = AsyncMock(
            side_effect=Exception("DB error")
        )

        result = await app_tools._get_server_name("server-123")

        assert result == "server-123"


class TestGetApp:
    """Tests for get_app method."""

    @pytest.fixture
    def mock_services(self):
        """Create mock services."""
        return {
            "app_service": MagicMock(),
            "marketplace_service": MagicMock(),
            "deployment_service": MagicMock(),
        }

    @pytest.fixture
    def app_tools(self, mock_services):
        """Create AppTools instance."""
        with patch("tools.app.tools.logger"):
            return AppTools(
                mock_services["app_service"],
                mock_services["marketplace_service"],
                mock_services["deployment_service"],
            )

    @pytest.mark.asyncio
    async def test_get_installed_app_single_success(self, app_tools, mock_services):
        """Test getting single installed app."""
        mock_services["deployment_service"].get_installed_apps = AsyncMock(
            return_value=[
                {"app_id": "nginx", "status": "running"},
                {"app_id": "redis", "status": "stopped"},
            ]
        )

        result = await app_tools.get_app(app_id="nginx", server_id="server-123")

        assert result["success"] is True
        assert result["data"]["app_id"] == "nginx"
        assert "Installed app retrieved" in result["message"]

    @pytest.mark.asyncio
    async def test_get_installed_app_not_found(self, app_tools, mock_services):
        """Test getting installed app that doesn't exist."""
        mock_services["deployment_service"].get_installed_apps = AsyncMock(
            return_value=[{"app_id": "nginx", "status": "running"}]
        )

        result = await app_tools.get_app(app_id="postgres", server_id="server-123")

        assert result["success"] is False
        assert result["error"] == "APP_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_get_all_installed_apps_on_server(self, app_tools, mock_services):
        """Test getting all installed apps on server."""
        mock_services["deployment_service"].get_installed_apps = AsyncMock(
            return_value=[
                {"app_id": "nginx", "status": "running"},
                {"app_id": "redis", "status": "stopped"},
            ]
        )

        result = await app_tools.get_app(server_id="server-123")

        assert result["success"] is True
        assert result["data"]["total"] == 2
        assert len(result["data"]["apps"]) == 2

    @pytest.mark.asyncio
    async def test_get_all_installations_across_servers(self, app_tools, mock_services):
        """Test getting all installations without filters."""
        mock_services[
            "deployment_service"
        ].get_all_installations_with_details = AsyncMock(
            return_value=[
                {"app_id": "nginx", "server_id": "server-1"},
                {"app_id": "redis", "server_id": "server-2"},
            ]
        )

        result = await app_tools.get_app()

        assert result["success"] is True
        assert result["data"]["total"] == 2

    @pytest.mark.asyncio
    async def test_get_app_from_marketplace_success(self, app_tools, mock_services):
        """Test getting single app from marketplace."""
        app = MagicMock()
        app.model_dump.return_value = {
            "id": "nginx",
            "name": "Nginx",
            "description": "Web server",
        }
        mock_services["marketplace_service"].get_app = AsyncMock(return_value=app)

        result = await app_tools.get_app(app_id="nginx")

        assert result["success"] is True
        assert result["data"]["id"] == "nginx"

    @pytest.mark.asyncio
    async def test_get_app_from_marketplace_not_found(self, app_tools, mock_services):
        """Test getting app from marketplace that doesn't exist."""
        mock_services["marketplace_service"].get_app = AsyncMock(return_value=None)

        result = await app_tools.get_app(app_id="nonexistent")

        assert result["success"] is False
        assert result["error"] == "APP_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_get_apps_bulk(self, app_tools, mock_services):
        """Test getting multiple apps by IDs."""
        app1 = MagicMock()
        app1.model_dump.return_value = {"id": "nginx", "name": "Nginx"}
        app2 = MagicMock()
        app2.model_dump.return_value = {"id": "redis", "name": "Redis"}

        mock_services["marketplace_service"].get_app = AsyncMock(
            side_effect=[app1, app2, None]
        )

        result = await app_tools.get_app(app_ids=["nginx", "redis", "nonexistent"])

        assert result["success"] is True
        assert result["data"]["total"] == 2

    @pytest.mark.asyncio
    async def test_get_apps_with_filters(self, app_tools, mock_services):
        """Test searching apps with filters."""
        search_result = MagicMock()
        search_result.total = 5
        app = MagicMock()
        app.model_dump.return_value = {"id": "nginx", "category": "web"}
        search_result.apps = [app]

        mock_services["app_service"].search_apps = AsyncMock(return_value=search_result)

        result = await app_tools.get_app(
            filters={
                "category": "web",
                "search": "nginx",
                "featured": True,
                "tags": ["docker"],
                "sort_by": "name",
                "sort_order": "asc",
            }
        )

        assert result["success"] is True
        assert result["data"]["total"] == 5

    @pytest.mark.asyncio
    async def test_get_apps_with_empty_filters(self, app_tools, mock_services):
        """Test searching apps with empty filters falls back to all installations."""
        # Empty dict {} is falsy, so it calls get_all_installations_with_details
        mock_services[
            "deployment_service"
        ].get_all_installations_with_details = AsyncMock(return_value=[])

        result = await app_tools.get_app(filters={})

        assert result["success"] is True
        assert result["data"]["total"] == 0

    @pytest.mark.asyncio
    async def test_get_app_exception(self, app_tools, mock_services):
        """Test get_app handles exceptions."""
        mock_services["marketplace_service"].get_app = AsyncMock(
            side_effect=Exception("Service error")
        )

        result = await app_tools.get_app(app_id="nginx")

        assert result["success"] is False
        assert "Failed to get app" in result["message"]
