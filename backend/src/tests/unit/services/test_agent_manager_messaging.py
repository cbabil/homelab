"""
Unit tests for services/agent_manager.py - Messaging functionality.

Tests send_command, handle_message, broadcast, and notification handling.
"""

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from services.agent_manager import AgentManager, MAX_MESSAGE_SIZE_BYTES
from models.agent import AgentConfig, AgentStatus


@pytest.fixture
def mock_agent_db():
    """Create mock agent database service."""
    db = MagicMock()
    db.update_agent = AsyncMock()
    return db


@pytest.fixture
def mock_websocket():
    """Create mock WebSocket."""
    ws = AsyncMock()
    ws.send_text = AsyncMock()
    ws.close = AsyncMock()
    return ws


@pytest.fixture
def agent_manager(mock_agent_db):
    """Create AgentManager with mocked dependencies."""
    with patch("services.agent_manager.logger"):
        return AgentManager(mock_agent_db)


async def resolve_pending_requests(agent_manager, agent_id, result="ok"):
    """Helper to resolve pending requests for an agent."""
    await asyncio.sleep(0.01)
    conn = agent_manager._connections.get(agent_id)
    if conn:
        for req_id, future in list(conn.pending_requests.items()):
            if not future.done():
                future.set_result(result)


class TestSendCommand:
    """Tests for send_command method."""

    @pytest.mark.asyncio
    async def test_send_command_not_connected(self, agent_manager):
        """send_command should raise ValueError if agent not connected."""
        with pytest.raises(ValueError, match="not connected"):
            await agent_manager.send_command("unknown-agent", "test.method")

    @pytest.mark.asyncio
    async def test_send_command_sends_json_rpc(self, agent_manager, mock_websocket):
        """send_command should send properly formatted JSON-RPC request."""
        with patch("services.agent_manager.logger"):
            await agent_manager.register_connection("agent-123", mock_websocket, "srv")
            task = asyncio.create_task(
                resolve_pending_requests(agent_manager, "agent-123", {"success": True})
            )
            await agent_manager.send_command(
                "agent-123", "test.method", {"param": "value"}, timeout=1.0
            )
            await task

        sent_data = json.loads(mock_websocket.send_text.call_args[0][0])
        assert sent_data["jsonrpc"] == "2.0"
        assert "id" in sent_data
        assert sent_data["method"] == "test.method"
        assert sent_data["params"] == {"param": "value"}

    @pytest.mark.asyncio
    async def test_send_command_no_params(self, agent_manager, mock_websocket):
        """send_command should not include params if None."""
        with patch("services.agent_manager.logger"):
            await agent_manager.register_connection("agent-123", mock_websocket, "srv")
            task = asyncio.create_task(
                resolve_pending_requests(agent_manager, "agent-123")
            )
            await agent_manager.send_command("agent-123", "test.method", timeout=1.0)
            await task

        sent_data = json.loads(mock_websocket.send_text.call_args[0][0])
        assert "params" not in sent_data

    @pytest.mark.asyncio
    async def test_send_command_timeout(self, agent_manager, mock_websocket):
        """send_command should raise TimeoutError on timeout."""
        with patch("services.agent_manager.logger"):
            await agent_manager.register_connection("agent-123", mock_websocket, "srv")

        with pytest.raises(TimeoutError, match="did not respond"):
            with patch("services.agent_manager.logger"):
                await agent_manager.send_command("agent-123", "test.method", timeout=0.01)

    @pytest.mark.asyncio
    async def test_send_command_cleans_up_on_timeout(self, agent_manager, mock_websocket):
        """send_command should cleanup pending request on timeout."""
        with patch("services.agent_manager.logger"):
            await agent_manager.register_connection("agent-123", mock_websocket, "srv")

        try:
            with patch("services.agent_manager.logger"):
                await agent_manager.send_command("agent-123", "test.method", timeout=0.01)
        except TimeoutError:
            pass

        assert len(agent_manager._connections["agent-123"].pending_requests) == 0


class TestHandleMessage:
    """Tests for handle_message method."""

    @pytest.mark.asyncio
    async def test_handle_message_oversized(self, agent_manager, mock_websocket):
        """handle_message should reject oversized messages."""
        with patch("services.agent_manager.logger"):
            await agent_manager.register_connection("agent-123", mock_websocket, "srv")

        oversized = "x" * (MAX_MESSAGE_SIZE_BYTES + 1)
        with patch("services.agent_manager.logger") as mock_logger:
            await agent_manager.handle_message("agent-123", oversized)
            mock_logger.warning.assert_called()

    @pytest.mark.asyncio
    async def test_handle_message_unknown_agent(self, agent_manager):
        """handle_message should warn for unknown agent."""
        with patch("services.agent_manager.logger") as mock_logger:
            await agent_manager.handle_message("unknown", '{"id": "1"}')
            mock_logger.warning.assert_called()

    @pytest.mark.asyncio
    async def test_handle_message_invalid_json(self, agent_manager, mock_websocket):
        """handle_message should log error for invalid JSON."""
        with patch("services.agent_manager.logger"):
            await agent_manager.register_connection("agent-123", mock_websocket, "srv")

        with patch("services.agent_manager.logger") as mock_logger:
            await agent_manager.handle_message("agent-123", "not json")
            mock_logger.error.assert_called()


class TestHandleResponse:
    """Tests for _handle_response method."""

    @pytest.mark.asyncio
    async def test_handle_response_success(self, agent_manager, mock_websocket):
        """_handle_response should resolve future with result."""
        with patch("services.agent_manager.logger"):
            await agent_manager.register_connection("agent-123", mock_websocket, "srv")

        future = asyncio.get_running_loop().create_future()
        agent_manager._connections["agent-123"].pending_requests["req-1"] = future
        response = json.dumps({"jsonrpc": "2.0", "id": "req-1", "result": "success"})

        with patch("services.agent_manager.logger"):
            await agent_manager.handle_message("agent-123", response)

        assert future.done() and future.result() == "success"

    @pytest.mark.asyncio
    async def test_handle_response_error(self, agent_manager, mock_websocket):
        """_handle_response should set exception for error response."""
        with patch("services.agent_manager.logger"):
            await agent_manager.register_connection("agent-123", mock_websocket, "srv")

        future = asyncio.get_running_loop().create_future()
        agent_manager._connections["agent-123"].pending_requests["req-1"] = future
        response = json.dumps({
            "jsonrpc": "2.0", "id": "req-1",
            "error": {"code": -32600, "message": "Invalid Request"},
        })

        with patch("services.agent_manager.logger"):
            await agent_manager.handle_message("agent-123", response)

        assert future.done()
        with pytest.raises(RuntimeError, match="Invalid Request"):
            future.result()

    @pytest.mark.asyncio
    async def test_handle_response_unknown_request(self, agent_manager, mock_websocket):
        """_handle_response should warn for unknown request ID."""
        with patch("services.agent_manager.logger"):
            await agent_manager.register_connection("agent-123", mock_websocket, "srv")

        response = json.dumps({"jsonrpc": "2.0", "id": "unknown-req", "result": "ok"})
        with patch("services.agent_manager.logger") as mock_logger:
            await agent_manager.handle_message("agent-123", response)
            mock_logger.warning.assert_called()


class TestHandleNotification:
    """Tests for _handle_notification method."""

    @pytest.mark.asyncio
    async def test_handle_notification_calls_handler(self, agent_manager, mock_websocket):
        """_handle_notification should call registered handler."""
        handler = AsyncMock()
        with patch("services.agent_manager.logger"):
            await agent_manager.register_connection("agent-123", mock_websocket, "srv")
            agent_manager.register_notification_handler("test.notify", handler)

        notification = json.dumps({
            "jsonrpc": "2.0", "method": "test.notify", "params": {"key": "value"},
        })

        with patch("services.agent_manager.logger"):
            await agent_manager.handle_message("agent-123", notification)

        handler.assert_called_once_with("agent-123", {"key": "value"})

    @pytest.mark.asyncio
    async def test_handle_notification_no_method(self, agent_manager, mock_websocket):
        """_handle_notification should warn if no method in notification."""
        with patch("services.agent_manager.logger"):
            await agent_manager.register_connection("agent-123", mock_websocket, "srv")

        notification = json.dumps({"jsonrpc": "2.0", "params": {}})
        with patch("services.agent_manager.logger") as mock_logger:
            await agent_manager.handle_message("agent-123", notification)
            mock_logger.warning.assert_called()

    @pytest.mark.asyncio
    async def test_handle_notification_no_handler(self, agent_manager, mock_websocket):
        """_handle_notification should log debug if no handler registered."""
        with patch("services.agent_manager.logger"):
            await agent_manager.register_connection("agent-123", mock_websocket, "srv")

        notification = json.dumps({"jsonrpc": "2.0", "method": "unhandled.notification"})
        with patch("services.agent_manager.logger") as mock_logger:
            await agent_manager.handle_message("agent-123", notification)
            mock_logger.debug.assert_called()

    @pytest.mark.asyncio
    async def test_handle_notification_handler_error(self, agent_manager, mock_websocket):
        """_handle_notification should log error if handler raises."""
        handler = AsyncMock(side_effect=Exception("Handler error"))
        with patch("services.agent_manager.logger"):
            await agent_manager.register_connection("agent-123", mock_websocket, "srv")
            agent_manager.register_notification_handler("test.notify", handler)

        notification = json.dumps({"jsonrpc": "2.0", "method": "test.notify"})
        with patch("services.agent_manager.logger") as mock_logger:
            await agent_manager.handle_message("agent-123", notification)
            mock_logger.error.assert_called()


class TestBroadcastConfigUpdate:
    """Tests for broadcast_config_update method."""

    @pytest.mark.asyncio
    async def test_broadcast_no_connections(self, agent_manager):
        """broadcast_config_update should do nothing with no connections."""
        config = AgentConfig()
        with patch("services.agent_manager.logger") as mock_logger:
            await agent_manager.broadcast_config_update(config)
            mock_logger.debug.assert_called()

    @pytest.mark.asyncio
    async def test_broadcast_to_all_agents(self, agent_manager):
        """broadcast_config_update should send to all connected agents."""
        ws1, ws2 = AsyncMock(), AsyncMock()
        ws1.send_text, ws1.close = AsyncMock(), AsyncMock()
        ws2.send_text, ws2.close = AsyncMock(), AsyncMock()

        with patch("services.agent_manager.logger"):
            await agent_manager.register_connection("agent-1", ws1, "server-1")
            await agent_manager.register_connection("agent-2", ws2, "server-2")

        config = AgentConfig(heartbeat_interval=60)

        async def resolve_all():
            await asyncio.sleep(0.01)
            for aid in ["agent-1", "agent-2"]:
                conn = agent_manager._connections.get(aid)
                if conn:
                    for _, future in list(conn.pending_requests.items()):
                        if not future.done():
                            future.set_result(True)

        with patch("services.agent_manager.logger"):
            task = asyncio.create_task(resolve_all())
            await agent_manager.broadcast_config_update(config)
            await task

        ws1.send_text.assert_called()
        ws2.send_text.assert_called()


class TestSendConfigUpdate:
    """Tests for _send_config_update method."""

    @pytest.mark.asyncio
    async def test_send_config_update_success(self, agent_manager, mock_websocket):
        """_send_config_update should return True on success."""
        with patch("services.agent_manager.logger"):
            await agent_manager.register_connection("agent-123", mock_websocket, "srv")
            task = asyncio.create_task(
                resolve_pending_requests(agent_manager, "agent-123", True)
            )
            result = await agent_manager._send_config_update(
                "agent-123", {"heartbeat_interval": 60}
            )
            await task

        assert result is True

    @pytest.mark.asyncio
    async def test_send_config_update_failure(self, agent_manager, mock_websocket):
        """_send_config_update should return False on failure."""
        with patch("services.agent_manager.logger"):
            await agent_manager.register_connection("agent-123", mock_websocket, "srv")
            result = await agent_manager._send_config_update(
                "agent-123", {"heartbeat_interval": 60}
            )

        assert result is False


class TestUpdateAgentStatus:
    """Tests for _update_agent_status method."""

    @pytest.mark.asyncio
    async def test_update_agent_status_success(self, agent_manager, mock_agent_db):
        """_update_agent_status should call database service."""
        with patch("services.agent_manager.logger"):
            await agent_manager._update_agent_status("agent-123", AgentStatus.CONNECTED)

        mock_agent_db.update_agent.assert_called_once()
        call_args = mock_agent_db.update_agent.call_args
        assert call_args[0][0] == "agent-123"
        assert call_args[0][1].status == AgentStatus.CONNECTED

    @pytest.mark.asyncio
    async def test_update_agent_status_handles_error(self, agent_manager, mock_agent_db):
        """_update_agent_status should log error on database failure."""
        mock_agent_db.update_agent.side_effect = Exception("Database error")

        with patch("services.agent_manager.logger") as mock_logger:
            await agent_manager._update_agent_status("agent-123", AgentStatus.CONNECTED)
            mock_logger.error.assert_called()


class TestPingAgent:
    """Tests for ping_agent method."""

    @pytest.mark.asyncio
    async def test_ping_agent_success(self, agent_manager, mock_websocket):
        """ping_agent should return True if agent responds with pong."""
        with patch("services.agent_manager.logger"):
            await agent_manager.register_connection("agent-123", mock_websocket, "srv")
            task = asyncio.create_task(
                resolve_pending_requests(agent_manager, "agent-123", "pong")
            )
            result = await agent_manager.ping_agent("agent-123", timeout=1.0)
            await task

        assert result is True

    @pytest.mark.asyncio
    async def test_ping_agent_wrong_response(self, agent_manager, mock_websocket):
        """ping_agent should return False if agent responds with wrong value."""
        with patch("services.agent_manager.logger"):
            await agent_manager.register_connection("agent-123", mock_websocket, "srv")
            task = asyncio.create_task(
                resolve_pending_requests(agent_manager, "agent-123", "wrong")
            )
            result = await agent_manager.ping_agent("agent-123", timeout=1.0)
            await task

        assert result is False

    @pytest.mark.asyncio
    async def test_ping_agent_not_connected(self, agent_manager):
        """ping_agent should return False if agent not connected."""
        with patch("services.agent_manager.logger"):
            result = await agent_manager.ping_agent("unknown")
        assert result is False

    @pytest.mark.asyncio
    async def test_ping_agent_timeout(self, agent_manager, mock_websocket):
        """ping_agent should return False on timeout."""
        with patch("services.agent_manager.logger"):
            await agent_manager.register_connection("agent-123", mock_websocket, "srv")
            result = await agent_manager.ping_agent("agent-123", timeout=0.01)

        assert result is False
