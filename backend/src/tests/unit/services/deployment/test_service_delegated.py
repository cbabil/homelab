"""
Unit tests for services/deployment/service.py - Delegated and Advanced Methods

Tests for delegated methods, refresh_installation_status, check_container_health,
get_container_logs, and _wait_for_container.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def mock_services():
    """Create mock services for DeploymentService."""
    services = {
        "ssh": MagicMock(),
        "server": MagicMock(),
        "marketplace": MagicMock(),
        "db": MagicMock(),
        "agent_manager": MagicMock(),
        "agent_service": MagicMock(),
    }
    agent = MagicMock()
    agent.id = "agent-123"
    services["agent_service"].get_agent_by_server = AsyncMock(return_value=agent)
    services["agent_manager"].is_connected.return_value = True
    services["agent_manager"].send_command = AsyncMock(return_value={})
    return services


@pytest.fixture
def deployment_service(mock_services):
    """Create DeploymentService instance."""
    from services.deployment.service import DeploymentService

    with patch("services.deployment.service.logger"):
        return DeploymentService(
            ssh_service=mock_services["ssh"],
            server_service=mock_services["server"],
            marketplace_service=mock_services["marketplace"],
            db_service=mock_services["db"],
            agent_manager=mock_services["agent_manager"],
            agent_service=mock_services["agent_service"],
        )


class TestDelegatedMethods:
    """Tests for methods delegated to sub-components."""

    @pytest.mark.asyncio
    async def test_validate_deployment_config(self, deployment_service):
        """Should delegate to validator."""
        deployment_service.validator.validate_config = AsyncMock(
            return_value={"valid": True}
        )

        result = await deployment_service.validate_deployment_config(
            "app-1", {"port": 8080}
        )

        assert result["valid"] is True
        deployment_service.validator.validate_config.assert_called_once_with(
            "app-1", {"port": 8080}
        )

    @pytest.mark.asyncio
    async def test_run_preflight_checks(self, deployment_service):
        """Should delegate to validator."""
        deployment_service.validator.run_preflight_checks = AsyncMock(
            return_value={"success": True}
        )

        result = await deployment_service.run_preflight_checks(
            "server-1", "app-1", {"config": "value"}
        )

        assert result["success"] is True
        deployment_service.validator.run_preflight_checks.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_app_status(self, deployment_service):
        """Should delegate to status_manager."""
        deployment_service.status_manager.get_app_status = AsyncMock(
            return_value={"status": "running"}
        )

        result = await deployment_service.get_app_status("server-1", "app-1")

        assert result["status"] == "running"

    @pytest.mark.asyncio
    async def test_get_installed_apps(self, deployment_service):
        """Should delegate to status_manager."""
        deployment_service.status_manager.get_installed_apps = AsyncMock(
            return_value=[{"app_id": "app-1"}]
        )

        result = await deployment_service.get_installed_apps("server-1")

        assert len(result) == 1
        assert result[0]["app_id"] == "app-1"

    @pytest.mark.asyncio
    async def test_get_installation_status_by_id(self, deployment_service):
        """Should delegate to status_manager."""
        deployment_service.status_manager.get_installation_status_by_id = AsyncMock(
            return_value={"id": "inst-123", "status": "running"}
        )

        result = await deployment_service.get_installation_status_by_id("inst-123")

        assert result["id"] == "inst-123"

    @pytest.mark.asyncio
    async def test_get_all_installations_with_details(self, deployment_service):
        """Should delegate to status_manager."""
        deployment_service.status_manager.get_all_installations_with_details = (
            AsyncMock(return_value=[{"id": "inst-1"}, {"id": "inst-2"}])
        )

        result = await deployment_service.get_all_installations_with_details()

        assert len(result) == 2


class TestRefreshInstallationStatus:
    """Tests for refresh_installation_status method."""

    @pytest.fixture
    def sample_installation(self):
        """Create sample installation."""
        inst = MagicMock()
        inst.id = "inst-123"
        inst.server_id = "server-1"
        inst.container_name = "my-container"
        inst.status = "running"
        return inst

    @pytest.mark.asyncio
    async def test_returns_none_when_installation_not_found(
        self, deployment_service, mock_services
    ):
        """Should return None when installation not found."""
        mock_services["db"].get_installation_by_id = AsyncMock(return_value=None)

        result = await deployment_service.refresh_installation_status("inst-123")

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_status_when_no_container_name(
        self, deployment_service, mock_services, sample_installation
    ):
        """Should return status without Docker check when no container."""
        sample_installation.container_name = None
        mock_services["db"].get_installation_by_id = AsyncMock(
            return_value=sample_installation
        )

        result = await deployment_service.refresh_installation_status("inst-123")

        assert result["status"] == "running"

    @pytest.mark.asyncio
    async def test_returns_stopped_when_inspect_fails(
        self, deployment_service, mock_services, sample_installation
    ):
        """Should return stopped when container inspect fails."""
        mock_services["db"].get_installation_by_id = AsyncMock(
            return_value=sample_installation
        )
        mock_services["db"].update_installation = AsyncMock()
        mock_services["agent_service"].get_agent_by_server.return_value = None

        result = await deployment_service.refresh_installation_status("inst-123")

        assert result["status"] == "stopped"

    @pytest.mark.asyncio
    async def test_parses_running_status(
        self, deployment_service, mock_services, sample_installation
    ):
        """Should parse running status correctly."""
        mock_services["db"].get_installation_by_id = AsyncMock(
            return_value=sample_installation
        )
        mock_services["db"].update_installation = AsyncMock()
        mock_services["agent_manager"].send_command.return_value = {
            "State": {"Status": "running"},
            "NetworkSettings": {"Networks": {"bridge": {}}},
            "Mounts": [],
        }

        result = await deployment_service.refresh_installation_status("inst-123")

        assert result["status"] == "running"
        assert "bridge" in result["networks"]

    @pytest.mark.asyncio
    async def test_parses_exited_status(
        self, deployment_service, mock_services, sample_installation
    ):
        """Should parse exited status as stopped."""
        mock_services["db"].get_installation_by_id = AsyncMock(
            return_value=sample_installation
        )
        mock_services["db"].update_installation = AsyncMock()
        mock_services["agent_manager"].send_command.return_value = {
            "State": {"Status": "exited"},
            "NetworkSettings": {"Networks": {}},
            "Mounts": [],
        }

        result = await deployment_service.refresh_installation_status("inst-123")

        assert result["status"] == "stopped"

    @pytest.mark.asyncio
    async def test_parses_restarting_status(
        self, deployment_service, mock_services, sample_installation
    ):
        """Should parse restarting status as error."""
        mock_services["db"].get_installation_by_id = AsyncMock(
            return_value=sample_installation
        )
        mock_services["db"].update_installation = AsyncMock()
        mock_services["agent_manager"].send_command.return_value = {
            "State": {"Status": "restarting"},
            "NetworkSettings": {"Networks": {}},
            "Mounts": [],
        }

        result = await deployment_service.refresh_installation_status("inst-123")

        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_parses_mounts(
        self, deployment_service, mock_services, sample_installation
    ):
        """Should parse mount information."""
        mock_services["db"].get_installation_by_id = AsyncMock(
            return_value=sample_installation
        )
        mock_services["db"].update_installation = AsyncMock()
        mock_services["agent_manager"].send_command.return_value = {
            "State": {"Status": "running"},
            "NetworkSettings": {"Networks": {}},
            "Mounts": [
                {
                    "Type": "volume",
                    "Name": "vol-1",
                    "Destination": "/data",
                    "Mode": "rw",
                },
                {
                    "Type": "bind",
                    "Source": "/host",
                    "Destination": "/cont",
                    "Mode": "ro",
                },
            ],
        }

        result = await deployment_service.refresh_installation_status("inst-123")

        assert len(result["named_volumes"]) == 1
        assert len(result["bind_mounts"]) == 1

    @pytest.mark.asyncio
    async def test_handles_exception(self, deployment_service, mock_services):
        """Should return None on exception."""
        mock_services["db"].get_installation_by_id = AsyncMock(
            side_effect=Exception("DB error")
        )

        result = await deployment_service.refresh_installation_status("inst-123")

        assert result is None


class TestCheckContainerHealth:
    """Tests for check_container_health method."""

    @pytest.mark.asyncio
    async def test_returns_health_dict(self, deployment_service, mock_services):
        """Should return health dictionary."""
        mock_services["agent_manager"].send_command.side_effect = [
            {"running": True, "status": "running", "restart_count": 0},
            {"NetworkSettings": {"Ports": {"80/tcp": {}}}},
        ]

        result = await deployment_service.check_container_health(
            "server-1", "my-container"
        )

        assert "container_running" in result
        assert "healthy" in result

    @pytest.mark.asyncio
    async def test_parses_status_result(self, deployment_service, mock_services):
        """Should parse status result from agent."""
        mock_services["agent_manager"].send_command.side_effect = [
            {
                "running": True,
                "status": "running",
                "restart_count": 1,
                "logs": "line1\nline2",
            },
            {"NetworkSettings": {"Ports": {}}},
        ]

        result = await deployment_service.check_container_health(
            "server-1", "my-container"
        )

        assert result["container_running"] is True
        assert result["restart_count"] == 1
        assert len(result["recent_logs"]) == 2

    @pytest.mark.asyncio
    async def test_extracts_ports(self, deployment_service, mock_services):
        """Should extract port information."""
        mock_services["agent_manager"].send_command.side_effect = [
            {"running": True, "status": "running", "restart_count": 0},
            {"NetworkSettings": {"Ports": {"80/tcp": {}, "443/tcp": {}}}},
        ]

        result = await deployment_service.check_container_health(
            "server-1", "my-container"
        )

        assert "80/tcp" in result["ports_listening"]
        assert "443/tcp" in result["ports_listening"]

    @pytest.mark.asyncio
    async def test_healthy_when_running_low_restarts(
        self, deployment_service, mock_services
    ):
        """Should be healthy when running with low restarts."""
        mock_services["agent_manager"].send_command.side_effect = [
            {"running": True, "status": "running", "restart_count": 2},
            {"NetworkSettings": {"Ports": {}}},
        ]

        result = await deployment_service.check_container_health(
            "server-1", "my-container"
        )

        assert result["healthy"] is True

    @pytest.mark.asyncio
    async def test_unhealthy_when_high_restarts(
        self, deployment_service, mock_services
    ):
        """Should be unhealthy when restart count >= 3."""
        mock_services["agent_manager"].send_command.side_effect = [
            {"running": True, "status": "running", "restart_count": 3},
            {"NetworkSettings": {"Ports": {}}},
        ]

        result = await deployment_service.check_container_health(
            "server-1", "my-container"
        )

        assert result["healthy"] is False

    @pytest.mark.asyncio
    async def test_handles_exception(self, deployment_service, mock_services):
        """Should return error on exception."""
        mock_services["agent_service"].get_agent_by_server.side_effect = Exception(
            "Connection failed"
        )

        result = await deployment_service.check_container_health(
            "server-1", "my-container"
        )

        assert result["healthy"] is False
        assert "error" in result


class TestGetContainerLogs:
    """Tests for get_container_logs method."""

    @pytest.mark.asyncio
    async def test_returns_error_when_agent_not_connected(
        self, deployment_service, mock_services
    ):
        """Should return error when agent not connected."""
        mock_services["agent_service"].get_agent_by_server.return_value = None

        result = await deployment_service.get_container_logs("server-1", "my-container")

        assert result["logs"] == []
        assert "Agent not connected" in result["error"]

    @pytest.mark.asyncio
    async def test_gets_logs(self, deployment_service, mock_services):
        """Should get container logs."""
        mock_services["agent_manager"].send_command.return_value = {
            "logs": "line1\nline2\nline3"
        }

        result = await deployment_service.get_container_logs(
            "server-1", "my-container", tail=50
        )

        assert len(result["logs"]) == 3
        assert result["container_name"] == "my-container"
        assert result["line_count"] == 3

    @pytest.mark.asyncio
    async def test_formats_log_lines(self, deployment_service, mock_services):
        """Should format log lines with timestamp placeholder."""
        mock_services["agent_manager"].send_command.return_value = {
            "logs": "log message"
        }

        result = await deployment_service.get_container_logs("server-1", "my-container")

        assert result["logs"][0]["message"] == "log message"
        assert result["logs"][0]["timestamp"] is None

    @pytest.mark.asyncio
    async def test_handles_exception(self, deployment_service, mock_services):
        """Should return error on exception."""
        mock_services["agent_manager"].send_command.side_effect = Exception(
            "Logs failed"
        )

        result = await deployment_service.get_container_logs("server-1", "my-container")

        assert result["logs"] == []
        assert "Logs failed" in result["error"]


class TestHandleInstallError:
    """Tests for _handle_install_error helper method."""

    @pytest.mark.asyncio
    async def test_updates_installation_status(self, deployment_service, mock_services):
        """Should update installation to error status."""
        mock_services["db"].update_installation = AsyncMock()

        await deployment_service._handle_install_error(
            "inst-123",
            "Something went wrong",
            50,
            "Test App",
            "server-1",
            "app-1",
        )

        mock_services["db"].update_installation.assert_called_once()
        call_args = mock_services["db"].update_installation.call_args
        assert call_args[0][0] == "inst-123"
        assert call_args[1]["status"] == "error"
        assert call_args[1]["error_message"] == "Something went wrong"
        assert call_args[1]["progress"] == 50
