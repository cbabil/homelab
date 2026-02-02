"""Tests for agent MCP tools."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from tools.agent.tools import AgentTools
from models.server import ServerConnection, AuthType, ServerStatus, SystemInfo
from models.agent import Agent, AgentStatus, RegistrationCode
from datetime import datetime, UTC, timedelta


@pytest.fixture
def mock_services():
    """Create mock services for agent tools."""
    agent_service = MagicMock()
    agent_service.create_agent = AsyncMock()
    agent_service.get_agent_by_server = AsyncMock()
    agent_service.revoke_agent = AsyncMock()

    agent_manager = MagicMock()
    agent_manager.is_connected = MagicMock(return_value=False)
    agent_manager.send_command = AsyncMock()
    agent_manager.unregister_connection = AsyncMock()

    ssh_service = MagicMock()
    ssh_service.execute_command = AsyncMock(return_value=(True, "Container started"))

    server_service = MagicMock()
    server_service.get_server = AsyncMock()
    server_service.get_credentials = AsyncMock()

    agent_lifecycle = MagicMock()
    agent_lifecycle.is_agent_stale = MagicMock(return_value=False)

    return {
        "agent_service": agent_service,
        "agent_manager": agent_manager,
        "ssh_service": ssh_service,
        "server_service": server_service,
        "agent_lifecycle": agent_lifecycle,
    }


@pytest.fixture
def agent_tools(mock_services):
    """Create agent tools with mocks."""
    return AgentTools(
        agent_service=mock_services["agent_service"],
        agent_manager=mock_services["agent_manager"],
        ssh_service=mock_services["ssh_service"],
        server_service=mock_services["server_service"],
        agent_lifecycle=mock_services["agent_lifecycle"],
    )


@pytest.fixture
def sample_server_with_docker():
    """Create a sample server with Docker installed."""
    return ServerConnection(
        id="server-123",
        name="Test Server",
        host="192.168.1.100",
        port=22,
        username="admin",
        auth_type=AuthType.PASSWORD,
        status=ServerStatus.CONNECTED,
        created_at="2025-01-01T00:00:00Z",
        system_info=SystemInfo(
            os="Ubuntu 22.04",
            kernel="5.15.0",
            architecture="x86_64",
            docker_version="24.0.5",
        ),
        docker_installed=True,
    )


@pytest.fixture
def sample_server_without_docker():
    """Create a sample server without Docker."""
    return ServerConnection(
        id="server-456",
        name="No Docker Server",
        host="192.168.1.101",
        port=22,
        username="admin",
        auth_type=AuthType.KEY,
        status=ServerStatus.CONNECTED,
        created_at="2025-01-01T00:00:00Z",
        system_info=SystemInfo(
            os="Ubuntu 22.04",
            kernel="5.15.0",
            architecture="x86_64",
            docker_version="Not installed",
        ),
        docker_installed=False,
    )


@pytest.fixture
def sample_agent():
    """Create a sample agent."""
    return Agent(
        id="agent-123",
        server_id="server-123",
        status=AgentStatus.PENDING,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def sample_registration_code():
    """Create a sample registration code."""
    return RegistrationCode(
        id="code-123",
        agent_id="agent-123",
        code="ABC123XYZ",
        expires_at=datetime.now(UTC) + timedelta(minutes=5),
        used=False,
        created_at=datetime.now(UTC),
    )


class TestInstallAgent:
    """Tests for install_agent tool."""

    @pytest.mark.asyncio
    async def test_install_agent_success(
        self,
        agent_tools,
        mock_services,
        sample_server_with_docker,
        sample_agent,
        sample_registration_code,
    ):
        """Should install agent successfully when Docker is available."""
        mock_services["server_service"].get_server.return_value = sample_server_with_docker
        mock_services["server_service"].get_credentials.return_value = {
            "password": "secret123"
        }
        mock_services["agent_service"].create_agent.return_value = (
            sample_agent,
            sample_registration_code,
        )
        mock_services["ssh_service"].execute_command.return_value = (
            True,
            "tomo-agent running",
        )

        result = await agent_tools.install_agent("server-123")

        assert result["success"] is True
        assert result["data"]["agent_id"] == "agent-123"
        assert result["data"]["server_id"] == "server-123"
        assert "deploy_command" in result["data"]

        # Verify SSH was called with correct parameters
        mock_services["ssh_service"].execute_command.assert_called_once()
        call_kwargs = mock_services["ssh_service"].execute_command.call_args.kwargs
        assert call_kwargs["host"] == "192.168.1.100"
        assert call_kwargs["port"] == 22
        assert call_kwargs["username"] == "admin"
        assert call_kwargs["auth_type"] == "password"
        assert call_kwargs["credentials"] == {"password": "secret123"}

    @pytest.mark.asyncio
    async def test_install_agent_server_not_found(self, agent_tools, mock_services):
        """Should fail when server doesn't exist."""
        mock_services["server_service"].get_server.return_value = None

        result = await agent_tools.install_agent("nonexistent-server")

        assert result["success"] is False
        assert result["error"] == "SERVER_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_install_agent_docker_not_installed(
        self, agent_tools, mock_services, sample_server_without_docker
    ):
        """Should fail when Docker is not installed on server."""
        mock_services["server_service"].get_server.return_value = sample_server_without_docker

        result = await agent_tools.install_agent("server-456")

        assert result["success"] is False
        assert result["error"] == "DOCKER_NOT_INSTALLED"
        # SSH should not be called
        mock_services["ssh_service"].execute_command.assert_not_called()

    @pytest.mark.asyncio
    async def test_install_agent_credentials_not_found(
        self, agent_tools, mock_services, sample_server_with_docker
    ):
        """Should fail when credentials cannot be retrieved."""
        mock_services["server_service"].get_server.return_value = sample_server_with_docker
        mock_services["server_service"].get_credentials.return_value = None

        result = await agent_tools.install_agent("server-123")

        assert result["success"] is False
        assert result["error"] == "CREDENTIALS_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_install_agent_ssh_failure(
        self,
        agent_tools,
        mock_services,
        sample_server_with_docker,
        sample_agent,
        sample_registration_code,
    ):
        """Should handle SSH execution failure gracefully."""
        mock_services["server_service"].get_server.return_value = sample_server_with_docker
        mock_services["server_service"].get_credentials.return_value = {
            "password": "secret123"
        }
        mock_services["agent_service"].create_agent.return_value = (
            sample_agent,
            sample_registration_code,
        )
        mock_services["ssh_service"].execute_command.return_value = (
            False,
            "Connection refused",
        )

        result = await agent_tools.install_agent("server-123")

        assert result["success"] is False
        assert result["error"] == "DEPLOY_FAILED"
        assert "Connection refused" in result["message"]

    @pytest.mark.asyncio
    async def test_install_agent_with_key_auth(
        self,
        agent_tools,
        mock_services,
        sample_agent,
        sample_registration_code,
    ):
        """Should work with SSH key authentication."""
        server_with_key = ServerConnection(
            id="server-key",
            name="Key Auth Server",
            host="192.168.1.102",
            port=22,
            username="admin",
            auth_type=AuthType.KEY,
            status=ServerStatus.CONNECTED,
            created_at="2025-01-01T00:00:00Z",
            system_info=SystemInfo(
                os="Ubuntu 22.04",
                kernel="5.15.0",
                architecture="x86_64",
                docker_version="24.0.5",
            ),
            docker_installed=True,
        )
        mock_services["server_service"].get_server.return_value = server_with_key
        mock_services["server_service"].get_credentials.return_value = {
            "private_key": "-----BEGIN OPENSSH PRIVATE KEY-----\n..."
        }
        mock_services["agent_service"].create_agent.return_value = (
            sample_agent,
            sample_registration_code,
        )
        mock_services["ssh_service"].execute_command.return_value = (True, "success")

        result = await agent_tools.install_agent("server-key")

        assert result["success"] is True
        call_kwargs = mock_services["ssh_service"].execute_command.call_args.kwargs
        assert call_kwargs["auth_type"] == "key"
        assert "private_key" in call_kwargs["credentials"]

    @pytest.mark.asyncio
    async def test_install_agent_docker_version_none(self, agent_tools, mock_services):
        """Should fail when system_info exists but docker_version is None."""
        server = ServerConnection(
            id="server-no-docker-version",
            name="No Docker Version",
            host="192.168.1.103",
            port=22,
            username="admin",
            auth_type=AuthType.PASSWORD,
            status=ServerStatus.CONNECTED,
            created_at="2025-01-01T00:00:00Z",
            system_info=SystemInfo(
                os="Ubuntu 22.04",
                kernel="5.15.0",
                architecture="x86_64",
                docker_version=None,
            ),
        )
        mock_services["server_service"].get_server.return_value = server

        result = await agent_tools.install_agent("server-no-docker-version")

        assert result["success"] is False
        assert result["error"] == "DOCKER_NOT_INSTALLED"

    @pytest.mark.asyncio
    async def test_install_agent_no_system_info(self, agent_tools, mock_services):
        """Should fail when server has no system_info."""
        server = ServerConnection(
            id="server-no-sysinfo",
            name="No System Info",
            host="192.168.1.104",
            port=22,
            username="admin",
            auth_type=AuthType.PASSWORD,
            status=ServerStatus.CONNECTED,
            created_at="2025-01-01T00:00:00Z",
            system_info=None,
        )
        mock_services["server_service"].get_server.return_value = server

        result = await agent_tools.install_agent("server-no-sysinfo")

        assert result["success"] is False
        assert result["error"] == "DOCKER_NOT_INSTALLED"


class TestGetAgentStatus:
    """Tests for get_agent_status tool."""

    @pytest.mark.asyncio
    async def test_get_agent_status_found(
        self, agent_tools, mock_services, sample_agent
    ):
        """Should return agent status when agent exists."""
        sample_agent.version = "1.0.0"
        sample_agent.last_seen = datetime.now(UTC)
        mock_services["agent_service"].get_agent_by_server.return_value = sample_agent
        mock_services["agent_manager"].is_connected.return_value = True

        result = await agent_tools.get_agent_status("server-123")

        assert result["success"] is True
        assert result["data"]["id"] == "agent-123"
        assert result["data"]["is_connected"] is True

    @pytest.mark.asyncio
    async def test_get_agent_status_not_found(self, agent_tools, mock_services):
        """Should return None when no agent exists."""
        mock_services["agent_service"].get_agent_by_server.return_value = None

        result = await agent_tools.get_agent_status("server-no-agent")

        assert result["success"] is True
        assert result["data"] is None


class TestRevokeAgent:
    """Tests for revoke_agent tool."""

    @pytest.mark.asyncio
    async def test_revoke_agent_success(
        self, agent_tools, mock_services, sample_agent
    ):
        """Should revoke agent successfully."""
        mock_services["agent_service"].get_agent_by_server.return_value = sample_agent
        mock_services["agent_manager"].is_connected.return_value = True
        mock_services["agent_service"].revoke_agent.return_value = True

        result = await agent_tools.revoke_agent("server-123")

        assert result["success"] is True
        mock_services["agent_manager"].unregister_connection.assert_called_once()

    @pytest.mark.asyncio
    async def test_revoke_agent_not_found(self, agent_tools, mock_services):
        """Should fail when agent doesn't exist."""
        mock_services["agent_service"].get_agent_by_server.return_value = None

        result = await agent_tools.revoke_agent("server-no-agent")

        assert result["success"] is False
        assert result["error"] == "AGENT_NOT_FOUND"


class TestSendAgentCommand:
    """Tests for send_agent_command tool."""

    @pytest.mark.asyncio
    async def test_send_command_success(
        self, agent_tools, mock_services, sample_agent
    ):
        """Should send command successfully when agent is connected."""
        mock_services["agent_service"].get_agent_by_server.return_value = sample_agent
        mock_services["agent_manager"].is_connected.return_value = True
        mock_services["agent_manager"].send_command.return_value = {"result": "ok"}

        result = await agent_tools.send_agent_command(
            "server-123", "docker.list", {"all": True}
        )

        assert result["success"] is True
        assert result["data"] == {"result": "ok"}
        mock_services["agent_manager"].send_command.assert_called_once_with(
            agent_id="agent-123",
            method="docker.list",
            params={"all": True},
        )

    @pytest.mark.asyncio
    async def test_send_command_agent_not_found(self, agent_tools, mock_services):
        """Should fail when agent doesn't exist."""
        mock_services["agent_service"].get_agent_by_server.return_value = None

        result = await agent_tools.send_agent_command("server-123", "docker.list")

        assert result["success"] is False
        assert result["error"] == "AGENT_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_send_command_agent_not_connected(
        self, agent_tools, mock_services, sample_agent
    ):
        """Should fail when agent is not connected."""
        mock_services["agent_service"].get_agent_by_server.return_value = sample_agent
        mock_services["agent_manager"].is_connected.return_value = False

        result = await agent_tools.send_agent_command("server-123", "docker.list")

        assert result["success"] is False
        assert result["error"] == "AGENT_NOT_CONNECTED"

    @pytest.mark.asyncio
    async def test_send_command_timeout(
        self, agent_tools, mock_services, sample_agent
    ):
        """Should handle command timeout."""
        mock_services["agent_service"].get_agent_by_server.return_value = sample_agent
        mock_services["agent_manager"].is_connected.return_value = True
        mock_services["agent_manager"].send_command.side_effect = TimeoutError("Timeout")

        result = await agent_tools.send_agent_command("server-123", "docker.list")

        assert result["success"] is False
        assert result["error"] == "COMMAND_TIMEOUT"


class TestCheckAgentHealth:
    """Tests for check_agent_health tool."""

    @pytest.mark.asyncio
    async def test_check_health_healthy(
        self, agent_tools, mock_services, sample_agent
    ):
        """Should return healthy status when agent is connected and not stale."""
        sample_agent.version = "1.0.0"
        sample_agent.last_seen = datetime.now(UTC)
        mock_services["agent_service"].get_agent_by_server.return_value = sample_agent
        mock_services["agent_manager"].is_connected.return_value = True
        mock_services["agent_lifecycle"].is_agent_stale.return_value = False

        result = await agent_tools.check_agent_health("server-123")

        assert result["success"] is True
        assert result["data"]["health"] == "healthy"
        assert result["data"]["is_connected"] is True
        assert result["data"]["is_stale"] is False

    @pytest.mark.asyncio
    async def test_check_health_degraded(
        self, agent_tools, mock_services, sample_agent
    ):
        """Should return degraded status when agent is stale."""
        sample_agent.version = "1.0.0"
        mock_services["agent_service"].get_agent_by_server.return_value = sample_agent
        mock_services["agent_manager"].is_connected.return_value = True
        mock_services["agent_lifecycle"].is_agent_stale.return_value = True

        result = await agent_tools.check_agent_health("server-123")

        assert result["success"] is True
        assert result["data"]["health"] == "degraded"

    @pytest.mark.asyncio
    async def test_check_health_offline(
        self, agent_tools, mock_services, sample_agent
    ):
        """Should return offline status when agent is not connected."""
        mock_services["agent_service"].get_agent_by_server.return_value = sample_agent
        mock_services["agent_manager"].is_connected.return_value = False

        result = await agent_tools.check_agent_health("server-123")

        assert result["success"] is True
        assert result["data"]["health"] == "offline"

    @pytest.mark.asyncio
    async def test_check_health_agent_not_found(self, agent_tools, mock_services):
        """Should fail when agent doesn't exist."""
        mock_services["agent_service"].get_agent_by_server.return_value = None

        result = await agent_tools.check_agent_health("server-123")

        assert result["success"] is False
        assert result["error"] == "AGENT_NOT_FOUND"


class TestPingAgent:
    """Tests for ping_agent tool."""

    @pytest.mark.asyncio
    async def test_ping_success(self, agent_tools, mock_services, sample_agent):
        """Should return ping result when agent responds."""
        mock_services["agent_service"].get_agent_by_server.return_value = sample_agent
        mock_services["agent_manager"].is_connected.return_value = True
        mock_services["agent_manager"].ping_agent = AsyncMock(return_value=True)

        result = await agent_tools.ping_agent("server-123")

        assert result["success"] is True
        assert result["data"]["responsive"] is True
        assert "latency_ms" in result["data"]

    @pytest.mark.asyncio
    async def test_ping_no_response(self, agent_tools, mock_services, sample_agent):
        """Should handle agent not responding to ping."""
        mock_services["agent_service"].get_agent_by_server.return_value = sample_agent
        mock_services["agent_manager"].is_connected.return_value = True
        mock_services["agent_manager"].ping_agent = AsyncMock(return_value=False)

        result = await agent_tools.ping_agent("server-123")

        assert result["success"] is False
        assert result["data"]["responsive"] is False

    @pytest.mark.asyncio
    async def test_ping_agent_not_connected(
        self, agent_tools, mock_services, sample_agent
    ):
        """Should fail when agent is not connected."""
        mock_services["agent_service"].get_agent_by_server.return_value = sample_agent
        mock_services["agent_manager"].is_connected.return_value = False

        result = await agent_tools.ping_agent("server-123")

        assert result["success"] is False
        assert result["error"] == "AGENT_NOT_CONNECTED"


class TestCheckAgentVersion:
    """Tests for check_agent_version tool."""

    @pytest.mark.asyncio
    async def test_check_version_up_to_date(
        self, agent_tools, mock_services, sample_agent
    ):
        """Should indicate agent is up to date."""
        sample_agent.version = "1.0.0"
        mock_services["agent_service"].get_agent_by_server.return_value = sample_agent

        # Mock version check result
        version_info = MagicMock()
        version_info.update_available = False
        version_info.model_dump.return_value = {
            "current_version": "1.0.0",
            "latest_version": "1.0.0",
            "update_available": False,
        }
        mock_services["agent_lifecycle"].check_version.return_value = version_info

        result = await agent_tools.check_agent_version("server-123")

        assert result["success"] is True
        assert result["data"]["update_available"] is False

    @pytest.mark.asyncio
    async def test_check_version_update_available(
        self, agent_tools, mock_services, sample_agent
    ):
        """Should indicate when update is available."""
        sample_agent.version = "0.9.0"
        mock_services["agent_service"].get_agent_by_server.return_value = sample_agent

        version_info = MagicMock()
        version_info.update_available = True
        version_info.model_dump.return_value = {
            "current_version": "0.9.0",
            "latest_version": "1.0.0",
            "update_available": True,
        }
        mock_services["agent_lifecycle"].check_version.return_value = version_info

        result = await agent_tools.check_agent_version("server-123")

        assert result["success"] is True
        assert result["data"]["update_available"] is True

    @pytest.mark.asyncio
    async def test_check_version_no_lifecycle(self, mock_services):
        """Should fail when lifecycle manager is not available."""
        agent_tools_no_lifecycle = AgentTools(
            agent_service=mock_services["agent_service"],
            agent_manager=mock_services["agent_manager"],
            ssh_service=mock_services["ssh_service"],
            server_service=mock_services["server_service"],
            agent_lifecycle=None,
        )

        result = await agent_tools_no_lifecycle.check_agent_version("server-123")

        assert result["success"] is False
        assert result["error"] == "LIFECYCLE_UNAVAILABLE"


class TestTriggerAgentUpdate:
    """Tests for trigger_agent_update tool."""

    @pytest.mark.asyncio
    async def test_trigger_update_success(
        self, agent_tools, mock_services, sample_agent
    ):
        """Should trigger update successfully."""
        sample_agent.version = "0.9.0"
        mock_services["agent_service"].get_agent_by_server.return_value = sample_agent
        mock_services["agent_manager"].is_connected.return_value = True

        version_info = MagicMock()
        version_info.update_available = True
        version_info.latest_version = "1.0.0"
        mock_services["agent_lifecycle"].check_version.return_value = version_info
        mock_services["agent_lifecycle"].trigger_update = AsyncMock(return_value=True)

        result = await agent_tools.trigger_agent_update("server-123")

        assert result["success"] is True
        mock_services["agent_lifecycle"].trigger_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_trigger_update_already_latest(
        self, agent_tools, mock_services, sample_agent
    ):
        """Should fail when agent is already at latest version."""
        sample_agent.version = "1.0.0"
        mock_services["agent_service"].get_agent_by_server.return_value = sample_agent
        mock_services["agent_manager"].is_connected.return_value = True

        version_info = MagicMock()
        version_info.update_available = False
        mock_services["agent_lifecycle"].check_version.return_value = version_info

        result = await agent_tools.trigger_agent_update("server-123")

        assert result["success"] is False
        assert result["error"] == "ALREADY_LATEST"

    @pytest.mark.asyncio
    async def test_trigger_update_agent_not_connected(
        self, agent_tools, mock_services, sample_agent
    ):
        """Should fail when agent is not connected."""
        mock_services["agent_service"].get_agent_by_server.return_value = sample_agent
        mock_services["agent_manager"].is_connected.return_value = False

        result = await agent_tools.trigger_agent_update("server-123")

        assert result["success"] is False
        assert result["error"] == "AGENT_NOT_CONNECTED"


class TestListStaleAgents:
    """Tests for list_stale_agents tool."""

    @pytest.mark.asyncio
    async def test_list_stale_agents_found(self, agent_tools, mock_services):
        """Should return list of stale agents."""
        mock_services["agent_lifecycle"].get_stale_agents = AsyncMock(
            return_value=["agent-1", "agent-2"]
        )
        mock_services["agent_manager"].get_connection_info.side_effect = [
            {"agent_id": "agent-1", "server_id": "server-1"},
            {"agent_id": "agent-2", "server_id": "server-2"},
        ]

        result = await agent_tools.list_stale_agents()

        assert result["success"] is True
        assert result["data"]["stale_count"] == 2
        assert len(result["data"]["agents"]) == 2

    @pytest.mark.asyncio
    async def test_list_stale_agents_none(self, agent_tools, mock_services):
        """Should return empty list when no stale agents."""
        mock_services["agent_lifecycle"].get_stale_agents = AsyncMock(return_value=[])

        result = await agent_tools.list_stale_agents()

        assert result["success"] is True
        assert result["data"]["stale_count"] == 0
        assert result["data"]["agents"] == []

    @pytest.mark.asyncio
    async def test_list_stale_agents_no_lifecycle(self, mock_services):
        """Should fail when lifecycle manager is not available."""
        agent_tools_no_lifecycle = AgentTools(
            agent_service=mock_services["agent_service"],
            agent_manager=mock_services["agent_manager"],
            ssh_service=mock_services["ssh_service"],
            server_service=mock_services["server_service"],
            agent_lifecycle=None,
        )

        result = await agent_tools_no_lifecycle.list_stale_agents()

        assert result["success"] is False
        assert result["error"] == "LIFECYCLE_UNAVAILABLE"
