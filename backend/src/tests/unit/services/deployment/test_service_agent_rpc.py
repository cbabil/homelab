"""
Unit tests for services/deployment/service.py - Agent RPC Methods

Tests for agent Docker RPC methods like pull, run, stop, etc.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


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
    # Setup connected agent by default
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


class TestAgentPullImage:
    """Tests for _agent_pull_image method."""

    @pytest.mark.asyncio
    async def test_returns_error_when_agent_not_connected(
        self, deployment_service, mock_services
    ):
        """Should return error when agent not connected."""
        mock_services["agent_service"].get_agent_by_server.return_value = None

        result = await deployment_service._agent_pull_image("server-1", "nginx:latest")

        assert result["success"] is False
        assert "Agent not connected" in result["error"]

    @pytest.mark.asyncio
    async def test_pulls_image_with_tag(self, deployment_service, mock_services):
        """Should pull image with specified tag."""
        mock_services["agent_manager"].send_command.return_value = {"id": "sha256:abc"}

        result = await deployment_service._agent_pull_image("server-1", "nginx:1.21")

        assert result["success"] is True
        call_kwargs = mock_services["agent_manager"].send_command.call_args[1]
        assert call_kwargs["params"]["image"] == "nginx"
        assert call_kwargs["params"]["tag"] == "1.21"

    @pytest.mark.asyncio
    async def test_defaults_to_latest_tag(self, deployment_service, mock_services):
        """Should default to 'latest' tag when not specified."""
        mock_services["agent_manager"].send_command.return_value = {}

        await deployment_service._agent_pull_image("server-1", "nginx")

        call_kwargs = mock_services["agent_manager"].send_command.call_args[1]
        assert call_kwargs["params"]["tag"] == "latest"

    @pytest.mark.asyncio
    async def test_handles_pull_exception(self, deployment_service, mock_services):
        """Should handle exception during pull."""
        mock_services["agent_manager"].send_command.side_effect = Exception(
            "Pull failed"
        )

        result = await deployment_service._agent_pull_image("server-1", "nginx:latest")

        assert result["success"] is False
        assert "Pull failed" in result["error"]


class TestAgentRunContainer:
    """Tests for _agent_run_container method."""

    @pytest.mark.asyncio
    async def test_returns_error_when_agent_not_connected(
        self, deployment_service, mock_services
    ):
        """Should return error when agent not connected."""
        mock_services["agent_service"].get_agent_by_server.return_value = None

        result = await deployment_service._agent_run_container(
            "server-1", "nginx:latest", "my-nginx"
        )

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_creates_container_with_basic_params(
        self, deployment_service, mock_services
    ):
        """Should create container with basic parameters."""
        mock_services["agent_manager"].send_command.return_value = {
            "container_id": "abc123"
        }

        result = await deployment_service._agent_run_container(
            "server-1", "nginx:latest", "my-nginx"
        )

        assert result["success"] is True
        call_kwargs = mock_services["agent_manager"].send_command.call_args[1]
        assert call_kwargs["method"] == "docker.containers.run"
        assert call_kwargs["params"]["image"] == "nginx:latest"
        assert call_kwargs["params"]["name"] == "my-nginx"

    @pytest.mark.asyncio
    async def test_creates_container_with_all_params(
        self, deployment_service, mock_services
    ):
        """Should create container with all parameters."""
        mock_services["agent_manager"].send_command.return_value = {}

        await deployment_service._agent_run_container(
            server_id="server-1",
            image="nginx:latest",
            name="my-nginx",
            ports={"8080": "80/tcp"},
            env={"DEBUG": "true"},
            volumes=[{"host": "/data", "container": "/data", "mode": "rw"}],
            restart_policy="unless-stopped",
            network_mode="bridge",
            privileged=True,
            capabilities=["NET_ADMIN"],
        )

        call_kwargs = mock_services["agent_manager"].send_command.call_args[1]
        params = call_kwargs["params"]
        assert params["ports"] == {"8080": "80/tcp"}
        assert params["env"] == {"DEBUG": "true"}
        assert params["privileged"] is True
        assert params["capabilities"] == ["NET_ADMIN"]

    @pytest.mark.asyncio
    async def test_handles_run_exception(self, deployment_service, mock_services):
        """Should handle exception during container run."""
        mock_services["agent_manager"].send_command.side_effect = Exception(
            "Run failed"
        )

        result = await deployment_service._agent_run_container(
            "server-1", "nginx:latest", "my-nginx"
        )

        assert result["success"] is False
        assert "Run failed" in result["error"]


class TestAgentStopContainer:
    """Tests for _agent_stop_container method."""

    @pytest.mark.asyncio
    async def test_returns_error_when_agent_not_connected(
        self, deployment_service, mock_services
    ):
        """Should return error when agent not connected."""
        mock_services["agent_service"].get_agent_by_server.return_value = None

        result = await deployment_service._agent_stop_container(
            "server-1", "my-container"
        )

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_stops_container(self, deployment_service, mock_services):
        """Should stop container via agent."""
        mock_services["agent_manager"].send_command.return_value = {}

        result = await deployment_service._agent_stop_container(
            "server-1", "my-container"
        )

        assert result["success"] is True
        call_kwargs = mock_services["agent_manager"].send_command.call_args[1]
        assert call_kwargs["method"] == "docker.containers.stop"
        assert call_kwargs["params"]["container"] == "my-container"

    @pytest.mark.asyncio
    async def test_handles_stop_exception(self, deployment_service, mock_services):
        """Should handle exception during stop."""
        mock_services["agent_manager"].send_command.side_effect = Exception(
            "Stop failed"
        )

        result = await deployment_service._agent_stop_container(
            "server-1", "my-container"
        )

        assert result["success"] is False


class TestAgentRemoveContainer:
    """Tests for _agent_remove_container method."""

    @pytest.mark.asyncio
    async def test_returns_error_when_agent_not_connected(
        self, deployment_service, mock_services
    ):
        """Should return error when agent not connected."""
        mock_services["agent_service"].get_agent_by_server.return_value = None

        result = await deployment_service._agent_remove_container(
            "server-1", "my-container"
        )

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_removes_container(self, deployment_service, mock_services):
        """Should remove container via agent."""
        mock_services["agent_manager"].send_command.return_value = {}

        result = await deployment_service._agent_remove_container(
            "server-1", "my-container"
        )

        assert result["success"] is True
        call_kwargs = mock_services["agent_manager"].send_command.call_args[1]
        assert call_kwargs["method"] == "docker.containers.remove"

    @pytest.mark.asyncio
    async def test_removes_container_with_force(
        self, deployment_service, mock_services
    ):
        """Should remove container with force flag."""
        mock_services["agent_manager"].send_command.return_value = {}

        await deployment_service._agent_remove_container(
            "server-1", "my-container", force=True
        )

        call_kwargs = mock_services["agent_manager"].send_command.call_args[1]
        assert call_kwargs["params"]["force"] is True

    @pytest.mark.asyncio
    async def test_handles_remove_exception(self, deployment_service, mock_services):
        """Should handle exception during remove."""
        mock_services["agent_manager"].send_command.side_effect = Exception(
            "Remove failed"
        )

        result = await deployment_service._agent_remove_container(
            "server-1", "my-container"
        )

        assert result["success"] is False


class TestAgentUpdateRestartPolicy:
    """Tests for _agent_update_restart_policy method."""

    @pytest.mark.asyncio
    async def test_returns_error_when_agent_not_connected(
        self, deployment_service, mock_services
    ):
        """Should return error when agent not connected."""
        mock_services["agent_service"].get_agent_by_server.return_value = None

        result = await deployment_service._agent_update_restart_policy(
            "server-1", "my-container", "always"
        )

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_updates_restart_policy(self, deployment_service, mock_services):
        """Should update restart policy via agent."""
        mock_services["agent_manager"].send_command.return_value = {}

        result = await deployment_service._agent_update_restart_policy(
            "server-1", "my-container", "unless-stopped"
        )

        assert result["success"] is True
        call_kwargs = mock_services["agent_manager"].send_command.call_args[1]
        assert call_kwargs["method"] == "docker.containers.update"
        assert call_kwargs["params"]["restart_policy"] == "unless-stopped"

    @pytest.mark.asyncio
    async def test_handles_update_exception(self, deployment_service, mock_services):
        """Should handle exception during update."""
        mock_services["agent_manager"].send_command.side_effect = Exception(
            "Update failed"
        )

        result = await deployment_service._agent_update_restart_policy(
            "server-1", "my-container", "always"
        )

        assert result["success"] is False


class TestAgentInspectContainer:
    """Tests for _agent_inspect_container method."""

    @pytest.mark.asyncio
    async def test_returns_error_when_agent_not_connected(
        self, deployment_service, mock_services
    ):
        """Should return error when agent not connected."""
        mock_services["agent_service"].get_agent_by_server.return_value = None

        result = await deployment_service._agent_inspect_container(
            "server-1", "my-container"
        )

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_inspects_container(self, deployment_service, mock_services):
        """Should inspect container via agent."""
        mock_services["agent_manager"].send_command.return_value = {
            "State": {"Status": "running"}
        }

        result = await deployment_service._agent_inspect_container(
            "server-1", "my-container"
        )

        assert result["success"] is True
        assert result["data"]["State"]["Status"] == "running"

    @pytest.mark.asyncio
    async def test_handles_inspect_exception(self, deployment_service, mock_services):
        """Should handle exception during inspect."""
        mock_services["agent_manager"].send_command.side_effect = Exception(
            "Inspect failed"
        )

        result = await deployment_service._agent_inspect_container(
            "server-1", "my-container"
        )

        assert result["success"] is False


class TestAgentGetContainerStatus:
    """Tests for _agent_get_container_status method."""

    @pytest.mark.asyncio
    async def test_returns_error_when_agent_not_connected(
        self, deployment_service, mock_services
    ):
        """Should return error when agent not connected."""
        mock_services["agent_service"].get_agent_by_server.return_value = None

        result = await deployment_service._agent_get_container_status(
            "server-1", "container-123"
        )

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_gets_container_status(self, deployment_service, mock_services):
        """Should get container status via agent."""
        mock_services["agent_manager"].send_command.return_value = {
            "status": "running",
            "health": "healthy",
        }

        result = await deployment_service._agent_get_container_status(
            "server-1", "container-123"
        )

        assert result["success"] is True
        call_kwargs = mock_services["agent_manager"].send_command.call_args[1]
        assert call_kwargs["method"] == "docker.containers.status"
        assert call_kwargs["params"]["include_logs"] is True

    @pytest.mark.asyncio
    async def test_handles_status_exception(self, deployment_service, mock_services):
        """Should handle exception during status check."""
        mock_services["agent_manager"].send_command.side_effect = Exception(
            "Status failed"
        )

        result = await deployment_service._agent_get_container_status(
            "server-1", "container-123"
        )

        assert result["success"] is False


class TestAgentGetContainerLogs:
    """Tests for _agent_get_container_logs method."""

    @pytest.mark.asyncio
    async def test_returns_error_when_agent_not_connected(
        self, deployment_service, mock_services
    ):
        """Should return error when agent not connected."""
        mock_services["agent_service"].get_agent_by_server.return_value = None

        result = await deployment_service._agent_get_container_logs(
            "server-1", "my-container"
        )

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_gets_container_logs(self, deployment_service, mock_services):
        """Should get container logs via agent."""
        mock_services["agent_manager"].send_command.return_value = {
            "logs": "log line 1\nlog line 2"
        }

        result = await deployment_service._agent_get_container_logs(
            "server-1", "my-container", tail=100
        )

        assert result["success"] is True
        call_kwargs = mock_services["agent_manager"].send_command.call_args[1]
        assert call_kwargs["method"] == "docker.containers.logs"
        assert call_kwargs["params"]["tail"] == 100

    @pytest.mark.asyncio
    async def test_handles_logs_exception(self, deployment_service, mock_services):
        """Should handle exception during logs retrieval."""
        mock_services["agent_manager"].send_command.side_effect = Exception(
            "Logs failed"
        )

        result = await deployment_service._agent_get_container_logs(
            "server-1", "my-container"
        )

        assert result["success"] is False


class TestAgentPreflightCheck:
    """Tests for _agent_preflight_check method."""

    @pytest.mark.asyncio
    async def test_returns_error_when_agent_not_connected(
        self, deployment_service, mock_services
    ):
        """Should return error when agent not connected."""
        mock_services["agent_service"].get_agent_by_server.return_value = None

        result = await deployment_service._agent_preflight_check("server-1")

        assert result["success"] is False
        assert "Agent not connected" in result["errors"]

    @pytest.mark.asyncio
    async def test_runs_preflight_check(self, deployment_service, mock_services):
        """Should run preflight check via agent."""
        mock_services["agent_manager"].send_command.return_value = {
            "success": True,
            "disk_ok": True,
            "memory_ok": True,
        }

        result = await deployment_service._agent_preflight_check(
            "server-1", min_disk_gb=5, min_memory_mb=512
        )

        assert result["success"] is True
        call_kwargs = mock_services["agent_manager"].send_command.call_args[1]
        assert call_kwargs["method"] == "system.preflight_check"
        assert call_kwargs["params"]["min_disk_gb"] == 5
        assert call_kwargs["params"]["min_memory_mb"] == 512

    @pytest.mark.asyncio
    async def test_handles_preflight_exception(self, deployment_service, mock_services):
        """Should handle exception during preflight check."""
        mock_services["agent_manager"].send_command.side_effect = Exception(
            "Preflight failed"
        )

        result = await deployment_service._agent_preflight_check("server-1")

        assert result["success"] is False
        assert "Preflight failed" in result["errors"]


class TestAgentPrepareVolumes:
    """Tests for _agent_prepare_volumes method."""

    @pytest.mark.asyncio
    async def test_returns_error_when_agent_not_connected(
        self, deployment_service, mock_services
    ):
        """Should return error when agent not connected."""
        mock_services["agent_service"].get_agent_by_server.return_value = None

        result = await deployment_service._agent_prepare_volumes(
            "server-1", [{"host": "/data"}]
        )

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_prepares_volumes(self, deployment_service, mock_services):
        """Should prepare volume directories via agent."""
        mock_services["agent_manager"].send_command.return_value = {"success": True}

        result = await deployment_service._agent_prepare_volumes(
            "server-1",
            [{"host": "/data/app", "uid": 1000, "gid": 1000}],
            default_uid=1000,
            default_gid=1000,
        )

        assert result["success"] is True
        call_kwargs = mock_services["agent_manager"].send_command.call_args[1]
        assert call_kwargs["method"] == "system.prepare_volumes"

    @pytest.mark.asyncio
    async def test_skips_non_absolute_paths(self, deployment_service, mock_services):
        """Should skip volumes without absolute paths."""
        mock_services["agent_manager"].send_command.return_value = {"success": True}

        result = await deployment_service._agent_prepare_volumes(
            "server-1", [{"host": "relative/path"}]
        )

        assert result["success"] is True
        assert "No bind mounts to prepare" in result["message"]

    @pytest.mark.asyncio
    async def test_returns_success_for_empty_volumes(
        self, deployment_service, mock_services
    ):
        """Should return success for empty volume list."""
        result = await deployment_service._agent_prepare_volumes("server-1", [])

        assert result["success"] is True
        assert "No bind mounts to prepare" in result["message"]

    @pytest.mark.asyncio
    async def test_handles_prepare_exception(self, deployment_service, mock_services):
        """Should handle exception during volume preparation."""
        mock_services["agent_manager"].send_command.side_effect = Exception(
            "Prepare failed"
        )

        result = await deployment_service._agent_prepare_volumes(
            "server-1", [{"host": "/data"}]
        )

        assert result["success"] is False
