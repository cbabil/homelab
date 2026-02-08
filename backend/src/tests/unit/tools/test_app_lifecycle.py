"""
App Tools Unit Tests - Update, Start, Stop Operations

Tests for update_app, start_app, and stop_app methods.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tools.app.tools import AppTools


class TestUpdateApp:
    """Tests for update_app method."""

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
    async def test_update_app_missing_app_id(self, app_tools):
        """Test update_app without app_id or app_ids."""
        result = await app_tools.update_app(server_id="server-123")

        assert result["success"] is False
        assert result["error"] == "MISSING_APP_ID"

    @pytest.mark.asyncio
    async def test_update_app_not_installed(self, app_tools, mock_services):
        """Test update_app when app not installed."""
        mock_services["deployment_service"].get_installed_apps = AsyncMock(
            return_value=[]
        )

        result = await app_tools.update_app(
            server_id="server-123",
            app_id="nginx",
        )

        assert result["success"] is False
        assert result["error"] == "APP_NOT_INSTALLED"

    @pytest.mark.asyncio
    async def test_update_app_single_success(self, app_tools, mock_services):
        """Test successful single app update."""
        mock_services["deployment_service"].get_installed_apps = AsyncMock(
            return_value=[{"app_id": "nginx", "config": {"port": 80}}]
        )
        mock_services["deployment_service"].uninstall_app = AsyncMock(return_value=True)
        installation = MagicMock()
        installation.id = "install-new"
        mock_services["deployment_service"].install_app = AsyncMock(
            return_value=installation
        )

        with patch("tools.app.tools.log_event", new_callable=AsyncMock):
            result = await app_tools.update_app(
                server_id="server-123",
                app_id="nginx",
                version="2.0.0",
            )

        assert result["success"] is True
        assert result["data"]["installation_id"] == "install-new"
        assert result["data"]["version"] == "2.0.0"

    @pytest.mark.asyncio
    async def test_update_app_single_no_version(self, app_tools, mock_services):
        """Test update app without specifying version."""
        mock_services["deployment_service"].get_installed_apps = AsyncMock(
            return_value=[{"app_id": "nginx", "config": {}}]
        )
        mock_services["deployment_service"].uninstall_app = AsyncMock(return_value=True)
        installation = MagicMock()
        installation.id = "install-new"
        mock_services["deployment_service"].install_app = AsyncMock(
            return_value=installation
        )

        with patch("tools.app.tools.log_event", new_callable=AsyncMock):
            result = await app_tools.update_app(
                server_id="server-123",
                app_id="nginx",
            )

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_update_app_bulk_success(self, app_tools, mock_services):
        """Test successful bulk app update."""
        mock_services["deployment_service"].get_installed_apps = AsyncMock(
            return_value=[
                {"app_id": "nginx", "config": {}},
                {"app_id": "redis", "config": {}},
            ]
        )
        mock_services["deployment_service"].uninstall_app = AsyncMock(return_value=True)
        installation = MagicMock()
        installation.id = "install-new"
        mock_services["deployment_service"].install_app = AsyncMock(
            return_value=installation
        )

        with patch("tools.app.tools.log_event", new_callable=AsyncMock):
            result = await app_tools.update_app(
                server_id="server-123",
                app_ids=["nginx", "redis"],
                version="2.0.0",
            )

        assert result["success"] is True
        assert result["data"]["succeeded"] == 2
        assert result["data"]["total"] == 2

    @pytest.mark.asyncio
    async def test_update_app_bulk_not_installed(self, app_tools, mock_services):
        """Test bulk update when app not installed."""
        mock_services["deployment_service"].get_installed_apps = AsyncMock(
            return_value=[{"app_id": "nginx", "config": {}}]
        )
        mock_services["deployment_service"].uninstall_app = AsyncMock(return_value=True)
        installation = MagicMock()
        installation.id = "install-new"
        mock_services["deployment_service"].install_app = AsyncMock(
            return_value=installation
        )

        with patch("tools.app.tools.log_event", new_callable=AsyncMock):
            result = await app_tools.update_app(
                server_id="server-123",
                app_ids=["nginx", "redis"],
            )

        assert result["success"] is True
        assert result["data"]["succeeded"] == 1

    @pytest.mark.asyncio
    async def test_update_app_bulk_exception(self, app_tools, mock_services):
        """Test bulk update with exception on one app."""
        mock_services["deployment_service"].get_installed_apps = AsyncMock(
            return_value=[
                {"app_id": "nginx", "config": {}},
                {"app_id": "redis", "config": {}},
            ]
        )
        mock_services["deployment_service"].uninstall_app = AsyncMock(
            side_effect=[True, Exception("Uninstall error")]
        )
        installation = MagicMock()
        installation.id = "install-new"
        mock_services["deployment_service"].install_app = AsyncMock(
            return_value=installation
        )

        with patch("tools.app.tools.log_event", new_callable=AsyncMock):
            result = await app_tools.update_app(
                server_id="server-123",
                app_ids=["nginx", "redis"],
            )

        assert result["success"] is True
        assert result["data"]["succeeded"] == 1

    @pytest.mark.asyncio
    async def test_update_app_exception(self, app_tools, mock_services):
        """Test update_app handles exceptions."""
        mock_services["deployment_service"].get_installed_apps = AsyncMock(
            side_effect=Exception("DB error")
        )

        with patch("tools.app.tools.log_event", new_callable=AsyncMock):
            result = await app_tools.update_app(
                server_id="server-123",
                app_id="nginx",
            )

        assert result["success"] is False
        assert result["error"] == "UPDATE_APP_ERROR"


class TestStartApp:
    """Tests for start_app method."""

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
    async def test_start_app_success(self, app_tools, mock_services):
        """Test successful app start."""
        mock_services["deployment_service"].start_app = AsyncMock(return_value=True)

        with patch("tools.app.tools.log_event", new_callable=AsyncMock):
            result = await app_tools.start_app(
                server_id="server-123",
                app_id="nginx",
            )

        assert result["success"] is True
        assert result["data"]["app_id"] == "nginx"

    @pytest.mark.asyncio
    async def test_start_app_failure(self, app_tools, mock_services):
        """Test app start failure."""
        mock_services["deployment_service"].start_app = AsyncMock(return_value=False)

        with patch("tools.app.tools.log_event", new_callable=AsyncMock):
            result = await app_tools.start_app(
                server_id="server-123",
                app_id="nginx",
            )

        assert result["success"] is False
        assert result["error"] == "START_FAILED"

    @pytest.mark.asyncio
    async def test_start_app_exception(self, app_tools, mock_services):
        """Test start_app handles exceptions."""
        mock_services["deployment_service"].start_app = AsyncMock(
            side_effect=Exception("Docker error")
        )

        with patch("tools.app.tools.log_event", new_callable=AsyncMock):
            result = await app_tools.start_app(
                server_id="server-123",
                app_id="nginx",
            )

        assert result["success"] is False
        assert result["error"] == "START_ERROR"


class TestStopApp:
    """Tests for stop_app method."""

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
    async def test_stop_app_success(self, app_tools, mock_services):
        """Test successful app stop."""
        mock_services["deployment_service"].stop_app = AsyncMock(return_value=True)

        with patch("tools.app.tools.log_event", new_callable=AsyncMock):
            result = await app_tools.stop_app(
                server_id="server-123",
                app_id="nginx",
            )

        assert result["success"] is True
        assert result["data"]["app_id"] == "nginx"

    @pytest.mark.asyncio
    async def test_stop_app_failure(self, app_tools, mock_services):
        """Test app stop failure."""
        mock_services["deployment_service"].stop_app = AsyncMock(return_value=False)

        with patch("tools.app.tools.log_event", new_callable=AsyncMock):
            result = await app_tools.stop_app(
                server_id="server-123",
                app_id="nginx",
            )

        assert result["success"] is False
        assert result["error"] == "STOP_FAILED"

    @pytest.mark.asyncio
    async def test_stop_app_exception(self, app_tools, mock_services):
        """Test stop_app handles exceptions."""
        mock_services["deployment_service"].stop_app = AsyncMock(
            side_effect=Exception("Docker error")
        )

        with patch("tools.app.tools.log_event", new_callable=AsyncMock):
            result = await app_tools.stop_app(
                server_id="server-123",
                app_id="nginx",
            )

        assert result["success"] is False
        assert result["error"] == "STOP_ERROR"
