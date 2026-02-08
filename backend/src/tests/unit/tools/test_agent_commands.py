"""
Agent Tools Unit Tests - Commands and Health

Tests for send_agent_command, check_agent_health, ping_agent,
check_agent_version, trigger_agent_update, list_stale_agents,
list_agents, reset_agent_status.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.agent import AgentStatus
from tools.agent.tools import AgentTools


class TestSendAgentCommand:
    """Tests for send_agent_command method."""

    @pytest.fixture
    def mock_services(self):
        """Create mock services."""
        return {
            "agent_service": MagicMock(),
            "agent_manager": MagicMock(),
            "ssh_service": MagicMock(),
            "server_service": MagicMock(),
        }

    @pytest.fixture
    def agent_tools(self, mock_services):
        """Create AgentTools instance."""
        with patch("tools.agent.tools.logger"):
            return AgentTools(
                mock_services["agent_service"],
                mock_services["agent_manager"],
                mock_services["ssh_service"],
                mock_services["server_service"],
            )

    @pytest.mark.asyncio
    async def test_send_command_no_agent(self, agent_tools, mock_services):
        """Test send_agent_command when no agent exists."""
        mock_services["agent_service"].get_agent_by_server = AsyncMock(
            return_value=None
        )

        result = await agent_tools.send_agent_command("server-123", "docker.list")

        assert result["success"] is False
        assert result["error"] == "AGENT_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_send_command_not_connected(self, agent_tools, mock_services):
        """Test send_agent_command when agent not connected."""
        agent = MagicMock()
        agent.id = "agent-123"
        mock_services["agent_service"].get_agent_by_server = AsyncMock(
            return_value=agent
        )
        mock_services["agent_manager"].is_connected.return_value = False

        result = await agent_tools.send_agent_command("server-123", "docker.list")

        assert result["success"] is False
        assert result["error"] == "AGENT_NOT_CONNECTED"

    @pytest.mark.asyncio
    async def test_send_command_success(self, agent_tools, mock_services):
        """Test successful command execution."""
        agent = MagicMock()
        agent.id = "agent-123"
        mock_services["agent_service"].get_agent_by_server = AsyncMock(
            return_value=agent
        )
        mock_services["agent_manager"].is_connected.return_value = True
        mock_services["agent_manager"].send_command = AsyncMock(
            return_value={"containers": []}
        )

        result = await agent_tools.send_agent_command(
            "server-123", "docker.list", {"filter": "running"}
        )

        assert result["success"] is True
        assert result["data"] == {"containers": []}
        mock_services["agent_manager"].send_command.assert_called_once_with(
            agent_id="agent-123", method="docker.list", params={"filter": "running"}
        )

    @pytest.mark.asyncio
    async def test_send_command_timeout(self, agent_tools, mock_services):
        """Test send_agent_command handles timeout."""
        agent = MagicMock()
        agent.id = "agent-123"
        mock_services["agent_service"].get_agent_by_server = AsyncMock(
            return_value=agent
        )
        mock_services["agent_manager"].is_connected.return_value = True
        mock_services["agent_manager"].send_command = AsyncMock(
            side_effect=TimeoutError("Command timed out")
        )

        result = await agent_tools.send_agent_command("server-123", "docker.list")

        assert result["success"] is False
        assert result["error"] == "COMMAND_TIMEOUT"

    @pytest.mark.asyncio
    async def test_send_command_runtime_error(self, agent_tools, mock_services):
        """Test send_agent_command handles agent error response."""
        agent = MagicMock()
        agent.id = "agent-123"
        mock_services["agent_service"].get_agent_by_server = AsyncMock(
            return_value=agent
        )
        mock_services["agent_manager"].is_connected.return_value = True
        mock_services["agent_manager"].send_command = AsyncMock(
            side_effect=RuntimeError("Invalid command")
        )

        result = await agent_tools.send_agent_command("server-123", "invalid.command")

        assert result["success"] is False
        assert result["error"] == "AGENT_COMMAND_ERROR"

    @pytest.mark.asyncio
    async def test_send_command_exception(self, agent_tools, mock_services):
        """Test send_agent_command handles general exceptions."""
        mock_services["agent_service"].get_agent_by_server = AsyncMock(
            side_effect=Exception("Network error")
        )

        result = await agent_tools.send_agent_command("server-123", "docker.list")

        assert result["success"] is False
        assert result["error"] == "SEND_COMMAND_ERROR"


class TestCheckAgentHealth:
    """Tests for check_agent_health method."""

    @pytest.fixture
    def mock_services(self):
        """Create mock services."""
        return {
            "agent_service": MagicMock(),
            "agent_manager": MagicMock(),
            "ssh_service": MagicMock(),
            "server_service": MagicMock(),
            "lifecycle": MagicMock(),
        }

    @pytest.fixture
    def agent_tools(self, mock_services):
        """Create AgentTools instance."""
        with patch("tools.agent.tools.logger"):
            return AgentTools(
                mock_services["agent_service"],
                mock_services["agent_manager"],
                mock_services["ssh_service"],
                mock_services["server_service"],
                agent_lifecycle=mock_services["lifecycle"],
            )

    @pytest.mark.asyncio
    async def test_check_health_no_agent(self, agent_tools, mock_services):
        """Test check_agent_health when no agent exists."""
        mock_services["agent_service"].get_agent_by_server = AsyncMock(
            return_value=None
        )

        result = await agent_tools.check_agent_health("server-123")

        assert result["success"] is False
        assert result["error"] == "AGENT_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_check_health_healthy(self, agent_tools, mock_services):
        """Test check_agent_health when agent is healthy."""
        agent = MagicMock()
        agent.id = "agent-123"
        agent.server_id = "server-123"
        agent.status = AgentStatus.CONNECTED
        agent.version = "1.0.0"
        agent.last_seen = datetime.now(UTC)
        agent.registered_at = datetime.now(UTC)

        mock_services["agent_service"].get_agent_by_server = AsyncMock(
            return_value=agent
        )
        mock_services["agent_manager"].is_connected.return_value = True
        mock_services["lifecycle"].is_agent_stale.return_value = False

        result = await agent_tools.check_agent_health("server-123")

        assert result["success"] is True
        assert result["data"]["health"] == "healthy"
        assert result["data"]["is_connected"] is True
        assert result["data"]["is_stale"] is False

    @pytest.mark.asyncio
    async def test_check_health_degraded(self, agent_tools, mock_services):
        """Test check_agent_health when agent is stale."""
        agent = MagicMock()
        agent.id = "agent-123"
        agent.server_id = "server-123"
        agent.status = AgentStatus.CONNECTED
        agent.version = "1.0.0"
        agent.last_seen = datetime.now(UTC)
        agent.registered_at = datetime.now(UTC)

        mock_services["agent_service"].get_agent_by_server = AsyncMock(
            return_value=agent
        )
        mock_services["agent_manager"].is_connected.return_value = True
        mock_services["lifecycle"].is_agent_stale.return_value = True

        result = await agent_tools.check_agent_health("server-123")

        assert result["success"] is True
        assert result["data"]["health"] == "degraded"
        assert result["data"]["is_stale"] is True

    @pytest.mark.asyncio
    async def test_check_health_offline(self, agent_tools, mock_services):
        """Test check_agent_health when agent is offline."""
        agent = MagicMock()
        agent.id = "agent-123"
        agent.server_id = "server-123"
        agent.status = AgentStatus.DISCONNECTED
        agent.version = "1.0.0"
        agent.last_seen = None
        agent.registered_at = datetime.now(UTC)

        mock_services["agent_service"].get_agent_by_server = AsyncMock(
            return_value=agent
        )
        mock_services["agent_manager"].is_connected.return_value = False

        result = await agent_tools.check_agent_health("server-123")

        assert result["success"] is True
        assert result["data"]["health"] == "offline"
        assert result["data"]["is_connected"] is False

    @pytest.mark.asyncio
    async def test_check_health_no_lifecycle(self, mock_services):
        """Test check_agent_health when lifecycle manager unavailable."""
        with patch("tools.agent.tools.logger"):
            tools = AgentTools(
                mock_services["agent_service"],
                mock_services["agent_manager"],
                mock_services["ssh_service"],
                mock_services["server_service"],
            )

        agent = MagicMock()
        agent.id = "agent-123"
        agent.server_id = "server-123"
        agent.status = AgentStatus.CONNECTED
        agent.version = "1.0.0"
        agent.last_seen = datetime.now(UTC)
        agent.registered_at = datetime.now(UTC)

        mock_services["agent_service"].get_agent_by_server = AsyncMock(
            return_value=agent
        )
        mock_services["agent_manager"].is_connected.return_value = True

        result = await tools.check_agent_health("server-123")

        assert result["success"] is True
        assert result["data"]["is_stale"] is True

    @pytest.mark.asyncio
    async def test_check_health_exception(self, agent_tools, mock_services):
        """Test check_agent_health handles exceptions."""
        mock_services["agent_service"].get_agent_by_server = AsyncMock(
            side_effect=Exception("DB error")
        )

        result = await agent_tools.check_agent_health("server-123")

        assert result["success"] is False
        assert result["error"] == "CHECK_HEALTH_ERROR"


class TestPingAgent:
    """Tests for ping_agent method."""

    @pytest.fixture
    def mock_services(self):
        """Create mock services."""
        return {
            "agent_service": MagicMock(),
            "agent_manager": MagicMock(),
            "ssh_service": MagicMock(),
            "server_service": MagicMock(),
        }

    @pytest.fixture
    def agent_tools(self, mock_services):
        """Create AgentTools instance."""
        with patch("tools.agent.tools.logger"):
            return AgentTools(
                mock_services["agent_service"],
                mock_services["agent_manager"],
                mock_services["ssh_service"],
                mock_services["server_service"],
            )

    @pytest.mark.asyncio
    async def test_ping_no_agent(self, agent_tools, mock_services):
        """Test ping_agent when no agent exists."""
        mock_services["agent_service"].get_agent_by_server = AsyncMock(
            return_value=None
        )

        result = await agent_tools.ping_agent("server-123")

        assert result["success"] is False
        assert result["error"] == "AGENT_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_ping_not_connected(self, agent_tools, mock_services):
        """Test ping_agent when agent not connected."""
        agent = MagicMock()
        agent.id = "agent-123"
        mock_services["agent_service"].get_agent_by_server = AsyncMock(
            return_value=agent
        )
        mock_services["agent_manager"].is_connected.return_value = False

        result = await agent_tools.ping_agent("server-123")

        assert result["success"] is False
        assert result["error"] == "AGENT_NOT_CONNECTED"

    @pytest.mark.asyncio
    async def test_ping_success(self, agent_tools, mock_services):
        """Test successful ping."""
        agent = MagicMock()
        agent.id = "agent-123"
        mock_services["agent_service"].get_agent_by_server = AsyncMock(
            return_value=agent
        )
        mock_services["agent_manager"].is_connected.return_value = True
        mock_services["agent_manager"].ping_agent = AsyncMock(return_value=True)

        result = await agent_tools.ping_agent("server-123", timeout=10.0)

        assert result["success"] is True
        assert result["data"]["responsive"] is True
        assert result["data"]["latency_ms"] is not None
        assert "Pong" in result["message"]

    @pytest.mark.asyncio
    async def test_ping_no_response(self, agent_tools, mock_services):
        """Test ping when agent doesn't respond."""
        agent = MagicMock()
        agent.id = "agent-123"
        mock_services["agent_service"].get_agent_by_server = AsyncMock(
            return_value=agent
        )
        mock_services["agent_manager"].is_connected.return_value = True
        mock_services["agent_manager"].ping_agent = AsyncMock(return_value=False)

        result = await agent_tools.ping_agent("server-123")

        assert result["success"] is False
        assert result["data"]["responsive"] is False
        assert result["data"]["latency_ms"] is None

    @pytest.mark.asyncio
    async def test_ping_exception(self, agent_tools, mock_services):
        """Test ping_agent handles exceptions."""
        mock_services["agent_service"].get_agent_by_server = AsyncMock(
            side_effect=Exception("Network error")
        )

        result = await agent_tools.ping_agent("server-123")

        assert result["success"] is False
        assert result["error"] == "PING_ERROR"


class TestCheckAgentVersion:
    """Tests for check_agent_version method."""

    @pytest.fixture
    def mock_services(self):
        """Create mock services."""
        return {
            "agent_service": MagicMock(),
            "agent_manager": MagicMock(),
            "ssh_service": MagicMock(),
            "server_service": MagicMock(),
            "lifecycle": MagicMock(),
        }

    @pytest.fixture
    def agent_tools(self, mock_services):
        """Create AgentTools instance."""
        with patch("tools.agent.tools.logger"):
            return AgentTools(
                mock_services["agent_service"],
                mock_services["agent_manager"],
                mock_services["ssh_service"],
                mock_services["server_service"],
                agent_lifecycle=mock_services["lifecycle"],
            )

    @pytest.mark.asyncio
    async def test_check_version_no_lifecycle(self, mock_services):
        """Test check_agent_version when lifecycle unavailable."""
        with patch("tools.agent.tools.logger"):
            tools = AgentTools(
                mock_services["agent_service"],
                mock_services["agent_manager"],
                mock_services["ssh_service"],
                mock_services["server_service"],
            )

        result = await tools.check_agent_version("server-123")

        assert result["success"] is False
        assert result["error"] == "LIFECYCLE_UNAVAILABLE"

    @pytest.mark.asyncio
    async def test_check_version_no_agent(self, agent_tools, mock_services):
        """Test check_agent_version when no agent exists."""
        mock_services["agent_service"].get_agent_by_server = AsyncMock(
            return_value=None
        )

        result = await agent_tools.check_agent_version("server-123")

        assert result["success"] is False
        assert result["error"] == "AGENT_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_check_version_unknown(self, agent_tools, mock_services):
        """Test check_agent_version when version unknown."""
        agent = MagicMock()
        agent.id = "agent-123"
        agent.version = None
        mock_services["agent_service"].get_agent_by_server = AsyncMock(
            return_value=agent
        )

        result = await agent_tools.check_agent_version("server-123")

        assert result["success"] is False
        assert result["error"] == "VERSION_UNKNOWN"

    @pytest.mark.asyncio
    async def test_check_version_update_available(self, agent_tools, mock_services):
        """Test check_agent_version when update available."""
        agent = MagicMock()
        agent.id = "agent-123"
        agent.version = "1.0.0"
        mock_services["agent_service"].get_agent_by_server = AsyncMock(
            return_value=agent
        )

        version_info = MagicMock()
        version_info.update_available = True
        version_info.model_dump.return_value = {
            "current_version": "1.0.0",
            "latest_version": "1.1.0",
            "update_available": True,
        }
        mock_services["lifecycle"].check_version.return_value = version_info

        result = await agent_tools.check_agent_version("server-123")

        assert result["success"] is True
        assert result["data"]["update_available"] is True
        assert "Update available" in result["message"]

    @pytest.mark.asyncio
    async def test_check_version_up_to_date(self, agent_tools, mock_services):
        """Test check_agent_version when up to date."""
        agent = MagicMock()
        agent.id = "agent-123"
        agent.version = "1.1.0"
        mock_services["agent_service"].get_agent_by_server = AsyncMock(
            return_value=agent
        )

        version_info = MagicMock()
        version_info.update_available = False
        version_info.model_dump.return_value = {
            "current_version": "1.1.0",
            "latest_version": "1.1.0",
            "update_available": False,
        }
        mock_services["lifecycle"].check_version.return_value = version_info

        result = await agent_tools.check_agent_version("server-123")

        assert result["success"] is True
        assert result["data"]["update_available"] is False
        assert "up to date" in result["message"]

    @pytest.mark.asyncio
    async def test_check_version_exception(self, agent_tools, mock_services):
        """Test check_agent_version handles exceptions."""
        mock_services["agent_service"].get_agent_by_server = AsyncMock(
            side_effect=Exception("Error")
        )

        result = await agent_tools.check_agent_version("server-123")

        assert result["success"] is False
        assert result["error"] == "CHECK_VERSION_ERROR"
