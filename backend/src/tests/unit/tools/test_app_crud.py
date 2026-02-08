"""
App Tools Unit Tests - Add and Delete Operations

Tests for add_app and delete_app methods.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.deployment import DeploymentError
from tools.app.tools import AppTools


class TestAddApp:
    """Tests for add_app method."""

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
    async def test_add_app_missing_app_id(self, app_tools):
        """Test add_app without app_id or app_ids."""
        result = await app_tools.add_app(server_id="server-123")

        assert result["success"] is False
        assert result["error"] == "MISSING_APP_ID"

    @pytest.mark.asyncio
    async def test_add_app_single_success(self, app_tools, mock_services):
        """Test successful single app deployment."""
        installation = MagicMock()
        installation.id = "install-123"
        mock_services["deployment_service"].install_app = AsyncMock(
            return_value=installation
        )
        mock_services["app_service"].mark_app_installed = AsyncMock()

        with patch("tools.app.tools.log_event", new_callable=AsyncMock):
            result = await app_tools.add_app(
                server_id="server-123",
                app_id="nginx",
                config={"port": 8080},
            )

        assert result["success"] is True
        assert result["data"]["installation_id"] == "install-123"
        assert result["data"]["app_id"] == "nginx"

    @pytest.mark.asyncio
    async def test_add_app_bulk_success(self, app_tools, mock_services):
        """Test successful bulk app deployment."""
        installation1 = MagicMock()
        installation1.id = "install-1"
        installation2 = MagicMock()
        installation2.id = "install-2"

        mock_services["deployment_service"].install_app = AsyncMock(
            side_effect=[installation1, installation2]
        )
        mock_services["app_service"].mark_app_installed = AsyncMock()

        with patch("tools.app.tools.log_event", new_callable=AsyncMock):
            result = await app_tools.add_app(
                server_id="server-123",
                app_ids=["nginx", "redis"],
            )

        assert result["success"] is True
        assert result["data"]["succeeded"] == 2
        assert result["data"]["total"] == 2

    @pytest.mark.asyncio
    async def test_add_app_bulk_partial_failure(self, app_tools, mock_services):
        """Test bulk deployment with partial failure."""
        installation1 = MagicMock()
        installation1.id = "install-1"

        mock_services["deployment_service"].install_app = AsyncMock(
            side_effect=[installation1, Exception("Install failed")]
        )
        mock_services["app_service"].mark_app_installed = AsyncMock()

        with patch("tools.app.tools.log_event", new_callable=AsyncMock):
            result = await app_tools.add_app(
                server_id="server-123",
                app_ids=["nginx", "redis"],
            )

        assert result["success"] is True
        assert result["data"]["succeeded"] == 1
        assert result["data"]["total"] == 2

    @pytest.mark.asyncio
    async def test_add_app_deployment_error(self, app_tools, mock_services):
        """Test add_app handles DeploymentError."""
        server = MagicMock()
        server.name = "my-server"
        mock_services["deployment_service"].server_service.get_server = AsyncMock(
            return_value=server
        )
        mock_services["deployment_service"].install_app = AsyncMock(
            side_effect=DeploymentError("Docker not running")
        )

        with patch("tools.app.tools.log_event", new_callable=AsyncMock):
            result = await app_tools.add_app(
                server_id="server-123",
                app_id="nginx",
            )

        assert result["success"] is False
        assert result["error"] == "DEPLOYMENT_FAILED"
        assert "my-server" in result["message"]

    @pytest.mark.asyncio
    async def test_add_app_exception(self, app_tools, mock_services):
        """Test add_app handles general exceptions."""
        server = MagicMock()
        server.name = "my-server"
        mock_services["deployment_service"].server_service.get_server = AsyncMock(
            return_value=server
        )
        mock_services["deployment_service"].install_app = AsyncMock(
            side_effect=Exception("Unexpected error")
        )

        with patch("tools.app.tools.log_event", new_callable=AsyncMock):
            result = await app_tools.add_app(
                server_id="server-123",
                app_id="nginx",
            )

        assert result["success"] is False
        assert result["error"] == "ADD_APP_ERROR"


class TestDeleteApp:
    """Tests for delete_app method."""

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
    async def test_delete_app_missing_app_id(self, app_tools):
        """Test delete_app without app_id or app_ids."""
        result = await app_tools.delete_app(server_id="server-123")

        assert result["success"] is False
        assert result["error"] == "MISSING_APP_ID"

    @pytest.mark.asyncio
    async def test_delete_app_single_success(self, app_tools, mock_services):
        """Test successful single app deletion."""
        mock_services["deployment_service"].uninstall_app = AsyncMock(return_value=True)
        mock_services["app_service"].mark_app_uninstalled = AsyncMock()

        with patch("tools.app.tools.log_event", new_callable=AsyncMock):
            result = await app_tools.delete_app(
                server_id="server-123",
                app_id="nginx",
                remove_data=True,
            )

        assert result["success"] is True
        assert result["data"]["app_id"] == "nginx"

    @pytest.mark.asyncio
    async def test_delete_app_single_failure(self, app_tools, mock_services):
        """Test single app deletion failure."""
        mock_services["deployment_service"].uninstall_app = AsyncMock(
            return_value=False
        )

        with patch("tools.app.tools.log_event", new_callable=AsyncMock):
            result = await app_tools.delete_app(
                server_id="server-123",
                app_id="nginx",
            )

        assert result["success"] is False
        assert result["error"] == "DELETE_FAILED"

    @pytest.mark.asyncio
    async def test_delete_app_bulk_success(self, app_tools, mock_services):
        """Test successful bulk app deletion."""
        mock_services["deployment_service"].uninstall_app = AsyncMock(return_value=True)
        mock_services["app_service"].mark_app_uninstalled = AsyncMock()

        with patch("tools.app.tools.log_event", new_callable=AsyncMock):
            result = await app_tools.delete_app(
                server_id="server-123",
                app_ids=["nginx", "redis"],
            )

        assert result["success"] is True
        assert result["data"]["succeeded"] == 2
        assert result["data"]["total"] == 2

    @pytest.mark.asyncio
    async def test_delete_app_bulk_partial_failure(self, app_tools, mock_services):
        """Test bulk deletion with partial failure."""
        mock_services["deployment_service"].uninstall_app = AsyncMock(
            side_effect=[True, Exception("Uninstall failed")]
        )
        mock_services["app_service"].mark_app_uninstalled = AsyncMock()

        with patch("tools.app.tools.log_event", new_callable=AsyncMock):
            result = await app_tools.delete_app(
                server_id="server-123",
                app_ids=["nginx", "redis"],
            )

        assert result["success"] is True
        assert result["data"]["succeeded"] == 1

    @pytest.mark.asyncio
    async def test_delete_app_bulk_uninstall_returns_false(
        self, app_tools, mock_services
    ):
        """Test bulk deletion when uninstall_app returns False."""
        mock_services["deployment_service"].uninstall_app = AsyncMock(
            side_effect=[True, False]
        )
        mock_services["app_service"].mark_app_uninstalled = AsyncMock()

        with patch("tools.app.tools.log_event", new_callable=AsyncMock):
            result = await app_tools.delete_app(
                server_id="server-123",
                app_ids=["nginx", "redis"],
            )

        assert result["success"] is True
        assert result["data"]["succeeded"] == 1

    @pytest.mark.asyncio
    async def test_delete_app_exception(self, app_tools, mock_services):
        """Test delete_app handles exceptions."""
        mock_services["deployment_service"].uninstall_app = AsyncMock(
            side_effect=Exception("DB error")
        )

        with patch("tools.app.tools.log_event", new_callable=AsyncMock):
            result = await app_tools.delete_app(
                server_id="server-123",
                app_id="nginx",
            )

        assert result["success"] is False
        assert result["error"] == "DELETE_APP_ERROR"
