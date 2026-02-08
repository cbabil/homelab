"""
Agent Tools Unit Tests - Token Rotation

Tests for rotate_agent_token MCP tool.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.agent import Agent, AgentStatus
from tools.agent.tools import AgentTools


class TestRotateAgentToken:
    """Tests for rotate_agent_token method."""

    @pytest.fixture
    def mock_services(self):
        """Create mock services."""
        return {
            "agent_service": MagicMock(),
            "agent_manager": MagicMock(),
            "ssh_service": MagicMock(),
            "server_service": MagicMock(),
            "packager": MagicMock(),
        }

    @pytest.fixture
    def agent_tools(self, mock_services):
        """Create AgentTools instance."""
        mock_services["packager"].package.return_value = "BASE64=="
        mock_services["packager"].get_version.return_value = "1.0.0"

        with patch("tools.agent.tools.logger"):
            return AgentTools(
                mock_services["agent_service"],
                mock_services["agent_manager"],
                mock_services["ssh_service"],
                mock_services["server_service"],
                mock_services["packager"],
            )

    @pytest.mark.asyncio
    async def test_rotate_token_agent_not_found(self, agent_tools, mock_services):
        """Test rotate fails when no agent for server."""
        mock_services["agent_service"].get_agent_by_server = AsyncMock(
            return_value=None
        )

        result = await agent_tools.rotate_agent_token("server-123")

        assert result["success"] is False
        assert result["error"] == "AGENT_NOT_FOUND"
        assert "No agent found" in result["message"]

    @pytest.mark.asyncio
    async def test_rotate_token_agent_not_connected(self, agent_tools, mock_services):
        """Test rotate fails when agent is not connected."""
        agent = Agent(
            id="agent-123",
            server_id="server-1",
            token_hash="hash",
            status=AgentStatus.DISCONNECTED,
        )
        mock_services["agent_service"].get_agent_by_server = AsyncMock(
            return_value=agent
        )
        mock_services["agent_manager"].is_connected = MagicMock(return_value=False)

        result = await agent_tools.rotate_agent_token("server-1")

        assert result["success"] is False
        assert result["error"] == "AGENT_NOT_CONNECTED"
        assert "must be connected" in result["message"]

    @pytest.mark.asyncio
    async def test_rotate_token_success(self, agent_tools, mock_services):
        """Test successful token rotation."""
        agent = Agent(
            id="agent-123",
            server_id="server-1",
            token_hash="hash",
            status=AgentStatus.CONNECTED,
        )
        mock_services["agent_service"].get_agent_by_server = AsyncMock(
            return_value=agent
        )
        mock_services["agent_manager"].is_connected = MagicMock(return_value=True)
        mock_services["agent_service"].initiate_rotation = AsyncMock(
            return_value="new-token-123"
        )
        mock_services["agent_service"]._get_token_rotation_settings = AsyncMock(
            return_value=(7, 5)  # 7 days rotation, 5 minutes grace
        )
        mock_services["agent_manager"].send_command = AsyncMock(
            return_value={"status": "ok"}
        )

        with patch("tools.agent.tools.log_event", new_callable=AsyncMock):
            result = await agent_tools.rotate_agent_token("server-1")

        assert result["success"] is True
        assert "rotation" in result["message"].lower()
        assert result["data"]["agent_id"] == "agent-123"
        assert result["data"]["grace_period_seconds"] == 300  # 5 * 60
        mock_services["agent_manager"].send_command.assert_called_once()
        call_args = mock_services["agent_manager"].send_command.call_args
        assert call_args[0][1] == "agent.rotate_token"
        assert call_args[0][2]["new_token"] == "new-token-123"

    @pytest.mark.asyncio
    async def test_rotate_token_initiate_fails(self, agent_tools, mock_services):
        """Test rotate fails when initiate_rotation returns None."""
        agent = Agent(
            id="agent-123",
            server_id="server-1",
            token_hash="hash",
            status=AgentStatus.CONNECTED,
        )
        mock_services["agent_service"].get_agent_by_server = AsyncMock(
            return_value=agent
        )
        mock_services["agent_manager"].is_connected = MagicMock(return_value=True)
        mock_services["agent_service"].initiate_rotation = AsyncMock(return_value=None)

        result = await agent_tools.rotate_agent_token("server-1")

        assert result["success"] is False
        assert result["error"] == "ROTATION_INIT_FAILED"

    @pytest.mark.asyncio
    async def test_rotate_token_websocket_send_failure(
        self, agent_tools, mock_services
    ):
        """Test rotate cancels when WebSocket send fails."""
        agent = Agent(
            id="agent-123",
            server_id="server-1",
            token_hash="hash",
            status=AgentStatus.CONNECTED,
        )
        mock_services["agent_service"].get_agent_by_server = AsyncMock(
            return_value=agent
        )
        mock_services["agent_manager"].is_connected = MagicMock(return_value=True)
        mock_services["agent_service"].initiate_rotation = AsyncMock(
            return_value="new-token-123"
        )
        mock_services["agent_service"]._get_token_rotation_settings = AsyncMock(
            return_value=(7, 5)
        )
        mock_services["agent_manager"].send_command = AsyncMock(
            side_effect=TimeoutError("Connection timed out")
        )
        mock_services["agent_service"].cancel_rotation = AsyncMock(return_value=True)

        result = await agent_tools.rotate_agent_token("server-1")

        assert result["success"] is False
        assert result["error"] == "ROTATION_SEND_FAILED"
        # Verify rotation was cancelled
        mock_services["agent_service"].cancel_rotation.assert_called_once_with(
            "agent-123"
        )

    @pytest.mark.asyncio
    async def test_rotate_token_includes_server_id(self, agent_tools, mock_services):
        """Test successful rotation includes server_id in response data."""
        agent = Agent(
            id="agent-xyz-789",
            server_id="server-1",
            token_hash="hash",
            status=AgentStatus.CONNECTED,
        )
        mock_services["agent_service"].get_agent_by_server = AsyncMock(
            return_value=agent
        )
        mock_services["agent_manager"].is_connected = MagicMock(return_value=True)
        mock_services["agent_service"].initiate_rotation = AsyncMock(
            return_value="new-token"
        )
        mock_services["agent_service"]._get_token_rotation_settings = AsyncMock(
            return_value=(7, 5)
        )
        mock_services["agent_manager"].send_command = AsyncMock(
            return_value={"status": "ok"}
        )

        with patch("tools.agent.tools.log_event", new_callable=AsyncMock):
            result = await agent_tools.rotate_agent_token("server-1")

        assert result["success"] is True
        assert result["data"]["agent_id"] == "agent-xyz-789"
        assert result["data"]["server_id"] == "server-1"
