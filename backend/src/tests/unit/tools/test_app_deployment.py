"""
App Tools Unit Tests - Deployment Pipeline Operations

Tests for installation status, validation, preflight checks, health, logs, cleanup.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tools.app.tools import AppTools


class TestGetInstallationStatus:
    """Tests for get_installation_status method."""

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
    async def test_get_installation_status_success(self, app_tools, mock_services):
        """Test successful installation status retrieval."""
        mock_services["deployment_service"].get_installation_status_by_id = AsyncMock(
            return_value={"status": "running", "progress": 100}
        )

        result = await app_tools.get_installation_status("install-123")

        assert result["success"] is True
        assert result["data"]["status"] == "running"

    @pytest.mark.asyncio
    async def test_get_installation_status_not_found(self, app_tools, mock_services):
        """Test installation status when not found."""
        mock_services["deployment_service"].get_installation_status_by_id = AsyncMock(
            return_value=None
        )

        result = await app_tools.get_installation_status("install-123")

        assert result["success"] is False
        assert result["error"] == "INSTALLATION_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_get_installation_status_exception(self, app_tools, mock_services):
        """Test get_installation_status handles exceptions."""
        mock_services["deployment_service"].get_installation_status_by_id = AsyncMock(
            side_effect=Exception("DB error")
        )

        result = await app_tools.get_installation_status("install-123")

        assert result["success"] is False
        assert result["error"] == "STATUS_ERROR"


class TestRefreshInstallationStatus:
    """Tests for refresh_installation_status method."""

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
    async def test_refresh_installation_status_success(self, app_tools, mock_services):
        """Test successful status refresh."""
        mock_services["deployment_service"].refresh_installation_status = AsyncMock(
            return_value={"status": "running", "container_id": "abc123"}
        )

        result = await app_tools.refresh_installation_status("install-123")

        assert result["success"] is True
        assert result["data"]["container_id"] == "abc123"

    @pytest.mark.asyncio
    async def test_refresh_installation_status_not_found(
        self, app_tools, mock_services
    ):
        """Test refresh status when not found."""
        mock_services["deployment_service"].refresh_installation_status = AsyncMock(
            return_value=None
        )

        result = await app_tools.refresh_installation_status("install-123")

        assert result["success"] is False
        assert result["error"] == "INSTALLATION_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_refresh_installation_status_exception(
        self, app_tools, mock_services
    ):
        """Test refresh_installation_status handles exceptions."""
        mock_services["deployment_service"].refresh_installation_status = AsyncMock(
            side_effect=Exception("Docker error")
        )

        result = await app_tools.refresh_installation_status("install-123")

        assert result["success"] is False
        assert result["error"] == "REFRESH_ERROR"


class TestValidateDeploymentConfig:
    """Tests for validate_deployment_config method."""

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
    async def test_validate_config_valid(self, app_tools, mock_services):
        """Test successful config validation."""
        mock_services["deployment_service"].validate_deployment_config = AsyncMock(
            return_value={"valid": True, "errors": []}
        )

        result = await app_tools.validate_deployment_config(
            app_id="nginx",
            config={"port": 8080},
        )

        assert result["success"] is True
        assert "Valid" in result["message"]

    @pytest.mark.asyncio
    async def test_validate_config_invalid(self, app_tools, mock_services):
        """Test config validation with errors."""
        mock_services["deployment_service"].validate_deployment_config = AsyncMock(
            return_value={"valid": False, "errors": ["Port out of range"]}
        )

        result = await app_tools.validate_deployment_config(
            app_id="nginx",
            config={"port": 99999},
        )

        assert result["success"] is True
        assert "1 errors" in result["message"]

    @pytest.mark.asyncio
    async def test_validate_config_no_config(self, app_tools, mock_services):
        """Test validation with no config provided."""
        mock_services["deployment_service"].validate_deployment_config = AsyncMock(
            return_value={"valid": True, "errors": []}
        )

        result = await app_tools.validate_deployment_config(app_id="nginx")

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_validate_config_exception(self, app_tools, mock_services):
        """Test validate_deployment_config handles exceptions."""
        mock_services["deployment_service"].validate_deployment_config = AsyncMock(
            side_effect=Exception("Validation error")
        )

        result = await app_tools.validate_deployment_config(
            app_id="nginx",
            config={"port": 8080},
        )

        assert result["success"] is False
        assert result["error"] == "VALIDATION_ERROR"


class TestRunPreflightChecks:
    """Tests for run_preflight_checks method."""

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
    async def test_preflight_checks_passed(self, app_tools, mock_services):
        """Test successful preflight checks."""
        mock_services["deployment_service"].run_preflight_checks = AsyncMock(
            return_value={
                "passed": True,
                "checks": [
                    {"name": "docker", "passed": True},
                    {"name": "disk_space", "passed": True},
                ],
            }
        )

        result = await app_tools.run_preflight_checks(
            server_id="server-123",
            app_id="nginx",
            config={"port": 8080},
        )

        assert result["success"] is True
        assert "passed" in result["message"]

    @pytest.mark.asyncio
    async def test_preflight_checks_failed(self, app_tools, mock_services):
        """Test failed preflight checks."""
        mock_services["deployment_service"].run_preflight_checks = AsyncMock(
            return_value={
                "passed": False,
                "checks": [
                    {"name": "docker", "passed": False, "error": "Docker not running"},
                ],
            }
        )

        result = await app_tools.run_preflight_checks(
            server_id="server-123",
            app_id="nginx",
        )

        assert result["success"] is True
        assert "failed" in result["message"]

    @pytest.mark.asyncio
    async def test_preflight_checks_exception(self, app_tools, mock_services):
        """Test run_preflight_checks handles exceptions."""
        mock_services["deployment_service"].run_preflight_checks = AsyncMock(
            side_effect=Exception("SSH error")
        )

        with patch("tools.app.tools.log_event", new_callable=AsyncMock):
            result = await app_tools.run_preflight_checks(
                server_id="server-123",
                app_id="nginx",
            )

        assert result["success"] is False
        assert result["error"] == "PREFLIGHT_ERROR"


class TestCheckContainerHealth:
    """Tests for check_container_health method."""

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
    async def test_container_health_healthy(self, app_tools, mock_services):
        """Test healthy container."""
        mock_services["deployment_service"].check_container_health = AsyncMock(
            return_value={"healthy": True, "status": "running"}
        )

        result = await app_tools.check_container_health(
            server_id="server-123",
            container_name="nginx",
        )

        assert result["success"] is True
        assert "healthy" in result["message"]

    @pytest.mark.asyncio
    async def test_container_health_unhealthy(self, app_tools, mock_services):
        """Test unhealthy container."""
        mock_services["deployment_service"].check_container_health = AsyncMock(
            return_value={"healthy": False, "status": "restarting"}
        )

        result = await app_tools.check_container_health(
            server_id="server-123",
            container_name="nginx",
        )

        assert result["success"] is True
        assert "unhealthy" in result["message"]

    @pytest.mark.asyncio
    async def test_container_health_exception(self, app_tools, mock_services):
        """Test check_container_health handles exceptions."""
        mock_services["deployment_service"].check_container_health = AsyncMock(
            side_effect=Exception("Docker error")
        )

        result = await app_tools.check_container_health(
            server_id="server-123",
            container_name="nginx",
        )

        assert result["success"] is False
        assert result["error"] == "HEALTH_CHECK_ERROR"


class TestGetContainerLogs:
    """Tests for get_container_logs method."""

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
    async def test_get_container_logs_success(self, app_tools, mock_services):
        """Test successful log retrieval."""
        mock_services["deployment_service"].get_container_logs = AsyncMock(
            return_value={"logs": ["line1", "line2", "line3"]}
        )

        result = await app_tools.get_container_logs(
            server_id="server-123",
            container_name="nginx",
            tail=50,
        )

        assert result["success"] is True
        assert "3 log lines" in result["message"]

    @pytest.mark.asyncio
    async def test_get_container_logs_default_tail(self, app_tools, mock_services):
        """Test log retrieval with default tail."""
        mock_services["deployment_service"].get_container_logs = AsyncMock(
            return_value={"logs": []}
        )

        result = await app_tools.get_container_logs(
            server_id="server-123",
            container_name="nginx",
        )

        assert result["success"] is True
        mock_services["deployment_service"].get_container_logs.assert_called_with(
            server_id="server-123", container_name="nginx", tail=100
        )

    @pytest.mark.asyncio
    async def test_get_container_logs_exception(self, app_tools, mock_services):
        """Test get_container_logs handles exceptions."""
        mock_services["deployment_service"].get_container_logs = AsyncMock(
            side_effect=Exception("Container not found")
        )

        result = await app_tools.get_container_logs(
            server_id="server-123",
            container_name="nginx",
        )

        assert result["success"] is False
        assert result["error"] == "LOGS_ERROR"


class TestCleanupFailedDeployment:
    """Tests for cleanup_failed_deployment method."""

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
    async def test_cleanup_success(self, app_tools, mock_services):
        """Test successful cleanup."""
        mock_services["deployment_service"].cleanup_failed_deployment = AsyncMock(
            return_value={
                "message": "Cleanup complete",
                "removed": ["container", "image"],
            }
        )

        with patch("tools.app.tools.log_event", new_callable=AsyncMock):
            result = await app_tools.cleanup_failed_deployment(
                server_id="server-123",
                installation_id="install-123",
            )

        assert result["success"] is True
        assert "Cleanup complete" in result["message"]

    @pytest.mark.asyncio
    async def test_cleanup_exception(self, app_tools, mock_services):
        """Test cleanup_failed_deployment handles exceptions."""
        mock_services["deployment_service"].cleanup_failed_deployment = AsyncMock(
            side_effect=Exception("Cleanup error")
        )

        with patch("tools.app.tools.log_event", new_callable=AsyncMock):
            result = await app_tools.cleanup_failed_deployment(
                server_id="server-123",
                installation_id="install-123",
            )

        assert result["success"] is False
        assert result["error"] == "CLEANUP_ERROR"
