"""
Agent Tools Unit Tests - Lifecycle and Management

Tests for trigger_agent_update, list_stale_agents, list_agents, reset_agent_status.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.agent import AgentStatus
from tools.agent.tools import AgentTools


class TestTriggerAgentUpdate:
    """Tests for trigger_agent_update method."""

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
    async def test_trigger_update_no_lifecycle(self, mock_services):
        """Test trigger_agent_update when lifecycle unavailable."""
        with patch("tools.agent.tools.logger"):
            tools = AgentTools(
                mock_services["agent_service"],
                mock_services["agent_manager"],
                mock_services["ssh_service"],
                mock_services["server_service"],
            )

        result = await tools.trigger_agent_update("server-123")

        assert result["success"] is False
        assert result["error"] == "LIFECYCLE_UNAVAILABLE"

    @pytest.mark.asyncio
    async def test_trigger_update_no_agent(self, agent_tools, mock_services):
        """Test trigger_agent_update when no agent exists."""
        mock_services["agent_service"].get_agent_by_server = AsyncMock(
            return_value=None
        )

        result = await agent_tools.trigger_agent_update("server-123")

        assert result["success"] is False
        assert result["error"] == "AGENT_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_trigger_update_not_connected(self, agent_tools, mock_services):
        """Test trigger_agent_update when agent not connected."""
        agent = MagicMock()
        agent.id = "agent-123"
        mock_services["agent_service"].get_agent_by_server = AsyncMock(
            return_value=agent
        )
        mock_services["agent_manager"].is_connected.return_value = False

        result = await agent_tools.trigger_agent_update("server-123")

        assert result["success"] is False
        assert result["error"] == "AGENT_NOT_CONNECTED"

    @pytest.mark.asyncio
    async def test_trigger_update_already_latest(self, agent_tools, mock_services):
        """Test trigger_agent_update when already at latest version."""
        agent = MagicMock()
        agent.id = "agent-123"
        agent.version = "1.1.0"
        mock_services["agent_service"].get_agent_by_server = AsyncMock(
            return_value=agent
        )
        mock_services["agent_manager"].is_connected.return_value = True

        version_info = MagicMock()
        version_info.update_available = False
        mock_services["lifecycle"].check_version.return_value = version_info

        result = await agent_tools.trigger_agent_update("server-123")

        assert result["success"] is False
        assert result["error"] == "ALREADY_LATEST"

    @pytest.mark.asyncio
    async def test_trigger_update_mark_failed(self, agent_tools, mock_services):
        """Test trigger_agent_update when marking for update fails."""
        agent = MagicMock()
        agent.id = "agent-123"
        agent.version = "1.0.0"
        mock_services["agent_service"].get_agent_by_server = AsyncMock(
            return_value=agent
        )
        mock_services["agent_manager"].is_connected.return_value = True

        version_info = MagicMock()
        version_info.update_available = True
        mock_services["lifecycle"].check_version.return_value = version_info
        mock_services["lifecycle"].trigger_update = AsyncMock(return_value=False)

        result = await agent_tools.trigger_agent_update("server-123")

        assert result["success"] is False
        assert result["error"] == "UPDATE_TRIGGER_FAILED"

    @pytest.mark.asyncio
    async def test_trigger_update_success(self, agent_tools, mock_services):
        """Test successful update trigger."""
        agent = MagicMock()
        agent.id = "agent-123"
        agent.version = "1.0.0"
        mock_services["agent_service"].get_agent_by_server = AsyncMock(
            return_value=agent
        )
        mock_services["agent_manager"].is_connected.return_value = True
        mock_services["agent_manager"].send_command = AsyncMock()

        version_info = MagicMock()
        version_info.update_available = True
        version_info.latest_version = "1.1.0"
        mock_services["lifecycle"].check_version.return_value = version_info
        mock_services["lifecycle"].trigger_update = AsyncMock(return_value=True)

        with patch("tools.agent.tools.log_event", new_callable=AsyncMock):
            result = await agent_tools.trigger_agent_update("server-123")

        assert result["success"] is True
        assert result["data"]["status"] == AgentStatus.UPDATING.value

    @pytest.mark.asyncio
    async def test_trigger_update_command_fails(self, agent_tools, mock_services):
        """Test update trigger continues even if command fails."""
        agent = MagicMock()
        agent.id = "agent-123"
        agent.version = "1.0.0"
        mock_services["agent_service"].get_agent_by_server = AsyncMock(
            return_value=agent
        )
        mock_services["agent_manager"].is_connected.return_value = True
        mock_services["agent_manager"].send_command = AsyncMock(
            side_effect=Exception("Command failed")
        )

        version_info = MagicMock()
        version_info.update_available = True
        version_info.latest_version = "1.1.0"
        mock_services["lifecycle"].check_version.return_value = version_info
        mock_services["lifecycle"].trigger_update = AsyncMock(return_value=True)

        with patch("tools.agent.tools.log_event", new_callable=AsyncMock):
            result = await agent_tools.trigger_agent_update("server-123")

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_trigger_update_no_version(self, agent_tools, mock_services):
        """Test trigger_agent_update when agent version is None."""
        agent = MagicMock()
        agent.id = "agent-123"
        agent.version = None
        mock_services["agent_service"].get_agent_by_server = AsyncMock(
            return_value=agent
        )
        mock_services["agent_manager"].is_connected.return_value = True
        mock_services["agent_manager"].send_command = AsyncMock()

        version_info = MagicMock()
        version_info.latest_version = "1.1.0"
        mock_services["lifecycle"].check_version.return_value = version_info
        mock_services["lifecycle"].trigger_update = AsyncMock(return_value=True)

        with patch("tools.agent.tools.log_event", new_callable=AsyncMock):
            result = await agent_tools.trigger_agent_update("server-123")

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_trigger_update_exception(self, agent_tools, mock_services):
        """Test trigger_agent_update handles exceptions."""
        mock_services["agent_service"].get_agent_by_server = AsyncMock(
            side_effect=Exception("Error")
        )

        result = await agent_tools.trigger_agent_update("server-123")

        assert result["success"] is False
        assert result["error"] == "TRIGGER_UPDATE_ERROR"


class TestListStaleAgents:
    """Tests for list_stale_agents method."""

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
    async def test_list_stale_no_lifecycle(self, mock_services):
        """Test list_stale_agents when lifecycle unavailable."""
        with patch("tools.agent.tools.logger"):
            tools = AgentTools(
                mock_services["agent_service"],
                mock_services["agent_manager"],
                mock_services["ssh_service"],
                mock_services["server_service"],
            )

        result = await tools.list_stale_agents()

        assert result["success"] is False
        assert result["error"] == "LIFECYCLE_UNAVAILABLE"

    @pytest.mark.asyncio
    async def test_list_stale_empty(self, agent_tools, mock_services):
        """Test list_stale_agents with no stale agents."""
        mock_services["lifecycle"].get_stale_agents = AsyncMock(return_value=[])

        result = await agent_tools.list_stale_agents()

        assert result["success"] is True
        assert result["data"]["stale_count"] == 0
        assert result["data"]["agents"] == []

    @pytest.mark.asyncio
    async def test_list_stale_with_agents(self, agent_tools, mock_services):
        """Test list_stale_agents with stale agents."""
        mock_services["lifecycle"].get_stale_agents = AsyncMock(
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
    async def test_list_stale_missing_connection_info(self, agent_tools, mock_services):
        """Test list_stale_agents when connection info missing."""
        mock_services["lifecycle"].get_stale_agents = AsyncMock(
            return_value=["agent-1", "agent-2"]
        )
        mock_services["agent_manager"].get_connection_info.side_effect = [
            {"agent_id": "agent-1", "server_id": "server-1"},
            None,
        ]

        result = await agent_tools.list_stale_agents()

        assert result["success"] is True
        assert result["data"]["stale_count"] == 1

    @pytest.mark.asyncio
    async def test_list_stale_exception(self, agent_tools, mock_services):
        """Test list_stale_agents handles exceptions."""
        mock_services["lifecycle"].get_stale_agents = AsyncMock(
            side_effect=Exception("Error")
        )

        result = await agent_tools.list_stale_agents()

        assert result["success"] is False
        assert result["error"] == "LIST_STALE_ERROR"


class TestListAgents:
    """Tests for list_agents method."""

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
    async def test_list_agents_empty(self, agent_tools, mock_services):
        """Test list_agents with no agents."""
        mock_services["agent_service"].list_all_agents = AsyncMock(return_value=[])

        result = await agent_tools.list_agents()

        assert result["success"] is True
        assert result["data"]["count"] == 0
        assert result["data"]["agents"] == []

    @pytest.mark.asyncio
    async def test_list_agents_with_agents(self, agent_tools, mock_services):
        """Test list_agents with multiple agents."""
        agent1 = MagicMock()
        agent1.id = "agent-1"
        agent1.server_id = "server-1"
        agent1.status = AgentStatus.CONNECTED
        agent1.version = "1.0.0"
        agent1.last_seen = datetime.now(UTC)
        agent1.registered_at = datetime.now(UTC)

        agent2 = MagicMock()
        agent2.id = "agent-2"
        agent2.server_id = "server-2"
        agent2.status = AgentStatus.DISCONNECTED
        agent2.version = "1.0.0"
        agent2.last_seen = None
        agent2.registered_at = datetime.now(UTC)

        mock_services["agent_service"].list_all_agents = AsyncMock(
            return_value=[agent1, agent2]
        )

        result = await agent_tools.list_agents()

        assert result["success"] is True
        assert result["data"]["count"] == 2
        assert len(result["data"]["agents"]) == 2
        assert result["data"]["agents"][0]["id"] == "agent-1"
        assert result["data"]["agents"][1]["last_seen"] is None

    @pytest.mark.asyncio
    async def test_list_agents_exception(self, agent_tools, mock_services):
        """Test list_agents handles exceptions."""
        mock_services["agent_service"].list_all_agents = AsyncMock(
            side_effect=Exception("Database error")
        )

        result = await agent_tools.list_agents()

        assert result["success"] is False
        assert result["error"] == "LIST_AGENTS_ERROR"


class TestResetAgentStatus:
    """Tests for reset_agent_status method."""

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
    async def test_reset_status_specific_agent_not_found(
        self, agent_tools, mock_services
    ):
        """Test reset_agent_status when specific agent not found."""
        mock_services["agent_service"].get_agent_by_server = AsyncMock(
            return_value=None
        )

        result = await agent_tools.reset_agent_status("server-123")

        assert result["success"] is False
        assert result["error"] == "AGENT_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_reset_status_agent_connected(self, agent_tools, mock_services):
        """Test reset_agent_status when agent is connected."""
        agent = MagicMock()
        agent.id = "agent-123"
        mock_services["agent_service"].get_agent_by_server = AsyncMock(
            return_value=agent
        )
        mock_services["agent_manager"].is_connected.return_value = True

        result = await agent_tools.reset_agent_status("server-123")

        assert result["success"] is False
        assert result["error"] == "AGENT_CONNECTED"

    @pytest.mark.asyncio
    async def test_reset_status_specific_agent_success(
        self, agent_tools, mock_services
    ):
        """Test successful status reset for specific agent."""
        agent = MagicMock()
        agent.id = "agent-123"
        mock_services["agent_service"].get_agent_by_server = AsyncMock(
            return_value=agent
        )
        mock_services["agent_manager"].is_connected.return_value = False

        mock_agent_db = MagicMock()
        mock_agent_db.update_agent = AsyncMock()
        mock_services["agent_service"]._get_agent_db.return_value = mock_agent_db

        with patch("tools.agent.tools.log_event", new_callable=AsyncMock):
            result = await agent_tools.reset_agent_status("server-123")

        assert result["success"] is True
        assert result["data"]["agent_id"] == "agent-123"
        assert result["data"]["reset_count"] == 1

    @pytest.mark.asyncio
    async def test_reset_status_all_agents(self, agent_tools, mock_services):
        """Test resetting all stale agent statuses."""
        mock_services["agent_service"].reset_stale_agent_statuses = AsyncMock(
            return_value=5
        )

        with patch("tools.agent.tools.log_event", new_callable=AsyncMock):
            result = await agent_tools.reset_agent_status()

        assert result["success"] is True
        assert result["data"]["reset_count"] == 5

    @pytest.mark.asyncio
    async def test_reset_status_all_agents_none_stale(self, agent_tools, mock_services):
        """Test resetting when no stale agents exist."""
        mock_services["agent_service"].reset_stale_agent_statuses = AsyncMock(
            return_value=0
        )

        with patch("tools.agent.tools.log_event", new_callable=AsyncMock):
            result = await agent_tools.reset_agent_status()

        assert result["success"] is True
        assert result["data"]["reset_count"] == 0

    @pytest.mark.asyncio
    async def test_reset_status_exception(self, agent_tools, mock_services):
        """Test reset_agent_status handles exceptions."""
        mock_services["agent_service"].get_agent_by_server = AsyncMock(
            side_effect=Exception("DB error")
        )

        result = await agent_tools.reset_agent_status("server-123")

        assert result["success"] is False
        assert result["error"] == "RESET_STATUS_ERROR"
