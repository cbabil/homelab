"""
Unit tests for services/agent_manager.py

Tests for AgentManager WebSocket connection management and message routing.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.agent_manager import AgentManager


@pytest.fixture
def mock_agent_db():
    """Create mock AgentDatabaseService."""
    return AsyncMock()


@pytest.fixture
def mock_lifecycle():
    """Create mock AgentLifecycleManager."""
    lifecycle = MagicMock()
    lifecycle.register_agent_connection = MagicMock()
    lifecycle.unregister_agent_connection = MagicMock()
    lifecycle.record_heartbeat = AsyncMock()
    lifecycle.handle_shutdown = AsyncMock()
    return lifecycle


@pytest.fixture
def agent_manager(mock_agent_db, mock_lifecycle):
    """Create AgentManager with mocked dependencies."""
    manager = AgentManager(mock_agent_db, mock_lifecycle)
    return manager


@pytest.fixture
def mock_websocket():
    """Create mock WebSocket."""
    ws = AsyncMock()
    ws.send_text = AsyncMock()
    ws.close = AsyncMock()
    return ws


class TestAgentManagerInit:
    """Tests for AgentManager initialization."""

    def test_init_stores_db_service(self, mock_agent_db):
        """Should store database service reference."""
        manager = AgentManager(mock_agent_db)
        assert manager._agent_db is mock_agent_db

    def test_init_registers_builtin_handlers(self, mock_agent_db):
        """Should register built-in notification handlers."""
        manager = AgentManager(mock_agent_db)

        assert "agent.heartbeat" in manager._notification_handlers
        assert "agent.shutdown" in manager._notification_handlers
        assert "agent.rotation_complete" in manager._notification_handlers
        assert "agent.rotation_failed" in manager._notification_handlers


class TestRegisterConnection:
    """Tests for register_connection method."""

    @pytest.mark.asyncio
    async def test_register_creates_connection(
        self, agent_manager, mock_websocket, mock_agent_db
    ):
        """Should create and store connection."""
        connection = await agent_manager.register_connection(
            "agent-1", mock_websocket, "server-1"
        )

        assert connection.agent_id == "agent-1"
        assert connection.server_id == "server-1"
        assert "agent-1" in agent_manager._connections

    @pytest.mark.asyncio
    async def test_register_updates_status(
        self, agent_manager, mock_websocket, mock_agent_db
    ):
        """Should update agent status in database."""
        await agent_manager.register_connection("agent-1", mock_websocket, "server-1")

        mock_agent_db.update_agent.assert_called()


class TestSendCommand:
    """Tests for send_command method."""

    @pytest.mark.asyncio
    async def test_send_command_to_unconnected_agent(self, agent_manager):
        """Should raise ValueError for unconnected agent."""
        with pytest.raises(ValueError, match="not connected"):
            await agent_manager.send_command("unknown-agent", "test.method")

    @pytest.mark.asyncio
    async def test_send_command_sends_json_rpc(
        self, agent_manager, mock_websocket, mock_agent_db
    ):
        """Should send JSON-RPC formatted message."""
        await agent_manager.register_connection("agent-1", mock_websocket, "server-1")

        # Create a future that will be resolved
        async def mock_send(data):
            msg = json.loads(data)
            # Resolve the pending request
            connection = agent_manager._connections["agent-1"]
            future = connection.pending_requests.get(msg["id"])
            if future:
                future.set_result({"status": "ok"})

        mock_websocket.send_text = mock_send

        result = await agent_manager.send_command("agent-1", "test.method", timeout=1.0)

        assert result == {"status": "ok"}


class TestSendRotationRequest:
    """Tests for send_rotation_request method."""

    @pytest.mark.asyncio
    async def test_send_rotation_to_unconnected_agent(self, agent_manager):
        """Should return False for unconnected agent."""
        result = await agent_manager.send_rotation_request(
            "unknown-agent", "new-token", 300
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_send_rotation_request_success(
        self, agent_manager, mock_websocket, mock_agent_db
    ):
        """Should send rotation request and return True on success."""
        await agent_manager.register_connection("agent-1", mock_websocket, "server-1")

        # Mock send_command to return success
        with patch.object(
            agent_manager,
            "send_command",
            new_callable=AsyncMock,
            return_value={"status": "ok"},
        ):
            result = await agent_manager.send_rotation_request(
                "agent-1", "new-token-123", 300
            )

        assert result is True

    @pytest.mark.asyncio
    async def test_send_rotation_request_includes_params(
        self, agent_manager, mock_websocket, mock_agent_db
    ):
        """Should include new_token and grace_period in params."""
        await agent_manager.register_connection("agent-1", mock_websocket, "server-1")

        with patch.object(
            agent_manager,
            "send_command",
            new_callable=AsyncMock,
            return_value={"status": "ok"},
        ) as mock_cmd:
            await agent_manager.send_rotation_request("agent-1", "secret-token", 600)

        mock_cmd.assert_called_once_with(
            "agent-1",
            "agent.rotate_token",
            {"new_token": "secret-token", "grace_period_seconds": 600},
            timeout=30.0,
        )

    @pytest.mark.asyncio
    async def test_send_rotation_request_timeout(
        self, agent_manager, mock_websocket, mock_agent_db
    ):
        """Should return False on timeout."""
        await agent_manager.register_connection("agent-1", mock_websocket, "server-1")

        with patch.object(
            agent_manager,
            "send_command",
            new_callable=AsyncMock,
            side_effect=TimeoutError("Timeout"),
        ):
            result = await agent_manager.send_rotation_request(
                "agent-1", "new-token", 300
            )

        assert result is False

    @pytest.mark.asyncio
    async def test_send_rotation_request_error(
        self, agent_manager, mock_websocket, mock_agent_db
    ):
        """Should return False on error response."""
        await agent_manager.register_connection("agent-1", mock_websocket, "server-1")

        with patch.object(
            agent_manager,
            "send_command",
            new_callable=AsyncMock,
            return_value={"status": "error"},
        ):
            result = await agent_manager.send_rotation_request(
                "agent-1", "new-token", 300
            )

        assert result is False


class TestHandleRotationComplete:
    """Tests for _handle_rotation_complete notification handler."""

    @pytest.mark.asyncio
    async def test_handles_rotation_complete(self, agent_manager):
        """Should handle rotation complete notification without error."""
        # Should not raise
        await agent_manager._handle_rotation_complete(
            "agent-1", {"rotated_at": "2024-01-01T00:00:00Z"}
        )


class TestHandleRotationFailed:
    """Tests for _handle_rotation_failed notification handler."""

    @pytest.mark.asyncio
    async def test_handles_rotation_failed(self, agent_manager):
        """Should handle rotation failed notification without error."""
        # Should not raise
        await agent_manager._handle_rotation_failed("agent-1", {"error": "Disk full"})

    @pytest.mark.asyncio
    async def test_handles_rotation_failed_no_error(self, agent_manager):
        """Should handle rotation failed with no error message."""
        # Should not raise
        await agent_manager._handle_rotation_failed("agent-1", {})


class TestHandleNotification:
    """Tests for _handle_notification method."""

    @pytest.mark.asyncio
    async def test_routes_rotation_complete(
        self, agent_manager, mock_websocket, mock_agent_db
    ):
        """Should route rotation_complete to handler."""
        await agent_manager.register_connection("agent-1", mock_websocket, "server-1")

        # Replace handler in the dictionary
        mock_handler = AsyncMock()
        agent_manager._notification_handlers["agent.rotation_complete"] = mock_handler

        await agent_manager._handle_notification(
            "agent-1", {"method": "agent.rotation_complete", "params": {"ts": "now"}}
        )

        mock_handler.assert_called_once_with("agent-1", {"ts": "now"})

    @pytest.mark.asyncio
    async def test_routes_rotation_failed(
        self, agent_manager, mock_websocket, mock_agent_db
    ):
        """Should route rotation_failed to handler."""
        await agent_manager.register_connection("agent-1", mock_websocket, "server-1")

        # Replace handler in the dictionary
        mock_handler = AsyncMock()
        agent_manager._notification_handlers["agent.rotation_failed"] = mock_handler

        await agent_manager._handle_notification(
            "agent-1", {"method": "agent.rotation_failed", "params": {"error": "oops"}}
        )

        mock_handler.assert_called_once_with("agent-1", {"error": "oops"})


class TestPingAgent:
    """Tests for ping_agent method."""

    @pytest.mark.asyncio
    async def test_ping_unconnected_agent(self, agent_manager):
        """Should return False for unconnected agent."""
        result = await agent_manager.ping_agent("unknown-agent")
        assert result is False

    @pytest.mark.asyncio
    async def test_ping_successful(self, agent_manager, mock_websocket, mock_agent_db):
        """Should return True on successful ping."""
        await agent_manager.register_connection("agent-1", mock_websocket, "server-1")

        with patch.object(
            agent_manager, "send_command", new_callable=AsyncMock, return_value="pong"
        ):
            result = await agent_manager.ping_agent("agent-1")

        assert result is True

    @pytest.mark.asyncio
    async def test_ping_timeout(self, agent_manager, mock_websocket, mock_agent_db):
        """Should return False on timeout."""
        await agent_manager.register_connection("agent-1", mock_websocket, "server-1")

        with patch.object(
            agent_manager,
            "send_command",
            new_callable=AsyncMock,
            side_effect=TimeoutError(),
        ):
            result = await agent_manager.ping_agent("agent-1")

        assert result is False


class TestIsConnected:
    """Tests for is_connected method."""

    def test_is_connected_false_for_unknown(self, agent_manager):
        """Should return False for unknown agent."""
        assert agent_manager.is_connected("unknown") is False

    @pytest.mark.asyncio
    async def test_is_connected_true_after_register(
        self, agent_manager, mock_websocket, mock_agent_db
    ):
        """Should return True after registration."""
        await agent_manager.register_connection("agent-1", mock_websocket, "server-1")
        assert agent_manager.is_connected("agent-1") is True


class TestGetConnectedAgentIds:
    """Tests for get_connected_agent_ids method."""

    def test_empty_when_no_connections(self, agent_manager):
        """Should return empty list when no agents connected."""
        assert agent_manager.get_connected_agent_ids() == []

    @pytest.mark.asyncio
    async def test_returns_connected_ids(
        self, agent_manager, mock_websocket, mock_agent_db
    ):
        """Should return list of connected agent IDs."""
        await agent_manager.register_connection("agent-1", mock_websocket, "server-1")
        await agent_manager.register_connection("agent-2", mock_websocket, "server-2")

        ids = agent_manager.get_connected_agent_ids()

        assert "agent-1" in ids
        assert "agent-2" in ids
        assert len(ids) == 2
