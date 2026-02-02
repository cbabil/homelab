"""
Unit tests for services/agent_manager.py - Built-in notification handlers.

Tests heartbeat and shutdown notification handlers.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from services.agent_manager import AgentManager
from models.agent import AgentHeartbeat, AgentShutdownRequest


@pytest.fixture
def mock_agent_db():
    """Create mock agent database service."""
    db = MagicMock()
    db.update_agent = AsyncMock()
    return db


@pytest.fixture
def mock_lifecycle_manager():
    """Create mock lifecycle manager."""
    lifecycle = MagicMock()
    lifecycle.register_agent_connection = MagicMock()
    lifecycle.unregister_agent_connection = MagicMock()
    lifecycle.record_heartbeat = AsyncMock()
    lifecycle.handle_shutdown = AsyncMock()
    return lifecycle


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


@pytest.fixture
def agent_manager_with_lifecycle(mock_agent_db, mock_lifecycle_manager):
    """Create AgentManager with lifecycle manager."""
    with patch("services.agent_manager.logger"):
        return AgentManager(mock_agent_db, mock_lifecycle_manager)


class TestHandleHeartbeat:
    """Tests for _handle_heartbeat method."""

    @pytest.mark.asyncio
    async def test_handle_heartbeat_no_lifecycle(
        self, agent_manager, mock_websocket, mock_agent_db
    ):
        """_handle_heartbeat should do nothing without lifecycle manager."""
        with patch("services.agent_manager.logger"):
            await agent_manager.register_connection(
                "agent-123", mock_websocket, "server-456"
            )

        notification = json.dumps({
            "jsonrpc": "2.0",
            "method": "agent.heartbeat",
            "params": {
                "cpu_percent": 50.0,
                "memory_percent": 60.0,
                "uptime_seconds": 3600,
            },
        })

        with patch("services.agent_manager.logger") as mock_logger:
            await agent_manager.handle_message("agent-123", notification)
            mock_logger.debug.assert_called()

    @pytest.mark.asyncio
    async def test_handle_heartbeat_with_lifecycle(
        self,
        agent_manager_with_lifecycle,
        mock_websocket,
        mock_lifecycle_manager,
        mock_agent_db,
    ):
        """_handle_heartbeat should record heartbeat with lifecycle manager."""
        with patch("services.agent_manager.logger"):
            await agent_manager_with_lifecycle.register_connection(
                "agent-123", mock_websocket, "server-456"
            )

        notification = json.dumps({
            "jsonrpc": "2.0",
            "method": "agent.heartbeat",
            "params": {
                "cpu_percent": 50.0,
                "memory_percent": 60.0,
                "uptime_seconds": 3600,
            },
        })

        with patch("services.agent_manager.logger"):
            await agent_manager_with_lifecycle.handle_message("agent-123", notification)

        mock_lifecycle_manager.record_heartbeat.assert_called_once()
        call_args = mock_lifecycle_manager.record_heartbeat.call_args
        heartbeat = call_args[0][0]
        assert isinstance(heartbeat, AgentHeartbeat)
        assert heartbeat.agent_id == "agent-123"
        assert heartbeat.cpu_percent == 50.0
        assert heartbeat.memory_percent == 60.0
        assert heartbeat.uptime_seconds == 3600

    @pytest.mark.asyncio
    async def test_handle_heartbeat_partial_params(
        self,
        agent_manager_with_lifecycle,
        mock_websocket,
        mock_lifecycle_manager,
        mock_agent_db,
    ):
        """_handle_heartbeat should handle partial heartbeat params."""
        with patch("services.agent_manager.logger"):
            await agent_manager_with_lifecycle.register_connection(
                "agent-123", mock_websocket, "server-456"
            )

        # Only cpu_percent provided
        notification = json.dumps({
            "jsonrpc": "2.0",
            "method": "agent.heartbeat",
            "params": {"cpu_percent": 75.0},
        })

        with patch("services.agent_manager.logger"):
            await agent_manager_with_lifecycle.handle_message("agent-123", notification)

        mock_lifecycle_manager.record_heartbeat.assert_called_once()
        call_args = mock_lifecycle_manager.record_heartbeat.call_args
        heartbeat = call_args[0][0]
        assert heartbeat.cpu_percent == 75.0
        assert heartbeat.memory_percent is None
        assert heartbeat.uptime_seconds is None

    @pytest.mark.asyncio
    async def test_handle_heartbeat_empty_params(
        self,
        agent_manager_with_lifecycle,
        mock_websocket,
        mock_lifecycle_manager,
        mock_agent_db,
    ):
        """_handle_heartbeat should handle empty params."""
        with patch("services.agent_manager.logger"):
            await agent_manager_with_lifecycle.register_connection(
                "agent-123", mock_websocket, "server-456"
            )

        notification = json.dumps({
            "jsonrpc": "2.0",
            "method": "agent.heartbeat",
        })

        with patch("services.agent_manager.logger"):
            await agent_manager_with_lifecycle.handle_message("agent-123", notification)

        mock_lifecycle_manager.record_heartbeat.assert_called_once()


class TestHandleShutdown:
    """Tests for _handle_shutdown method."""

    @pytest.mark.asyncio
    async def test_handle_shutdown_no_lifecycle(
        self, agent_manager, mock_websocket, mock_agent_db
    ):
        """_handle_shutdown should do nothing without lifecycle manager."""
        with patch("services.agent_manager.logger"):
            await agent_manager.register_connection(
                "agent-123", mock_websocket, "server-456"
            )

        notification = json.dumps({
            "jsonrpc": "2.0",
            "method": "agent.shutdown",
            "params": {"reason": "maintenance", "restart": False},
        })

        with patch("services.agent_manager.logger") as mock_logger:
            await agent_manager.handle_message("agent-123", notification)
            mock_logger.debug.assert_called()

    @pytest.mark.asyncio
    async def test_handle_shutdown_with_lifecycle(
        self,
        agent_manager_with_lifecycle,
        mock_websocket,
        mock_lifecycle_manager,
        mock_agent_db,
    ):
        """_handle_shutdown should notify lifecycle and unregister connection."""
        with patch("services.agent_manager.logger"):
            await agent_manager_with_lifecycle.register_connection(
                "agent-123", mock_websocket, "server-456"
            )

        notification = json.dumps({
            "jsonrpc": "2.0",
            "method": "agent.shutdown",
            "params": {"reason": "maintenance", "restart": False},
        })

        with patch("services.agent_manager.logger"):
            await agent_manager_with_lifecycle.handle_message("agent-123", notification)

        # Lifecycle manager should be notified
        mock_lifecycle_manager.handle_shutdown.assert_called_once()
        call_args = mock_lifecycle_manager.handle_shutdown.call_args
        request = call_args[0][0]
        assert isinstance(request, AgentShutdownRequest)
        assert request.agent_id == "agent-123"
        assert request.reason == "maintenance"
        assert request.restart is False

        # Connection should be unregistered
        assert "agent-123" not in agent_manager_with_lifecycle._connections

    @pytest.mark.asyncio
    async def test_handle_shutdown_with_restart(
        self,
        agent_manager_with_lifecycle,
        mock_websocket,
        mock_lifecycle_manager,
        mock_agent_db,
    ):
        """_handle_shutdown should handle restart=True."""
        with patch("services.agent_manager.logger"):
            await agent_manager_with_lifecycle.register_connection(
                "agent-123", mock_websocket, "server-456"
            )

        notification = json.dumps({
            "jsonrpc": "2.0",
            "method": "agent.shutdown",
            "params": {"reason": "update", "restart": True},
        })

        with patch("services.agent_manager.logger"):
            await agent_manager_with_lifecycle.handle_message("agent-123", notification)

        call_args = mock_lifecycle_manager.handle_shutdown.call_args
        request = call_args[0][0]
        assert request.restart is True

    @pytest.mark.asyncio
    async def test_handle_shutdown_default_params(
        self,
        agent_manager_with_lifecycle,
        mock_websocket,
        mock_lifecycle_manager,
        mock_agent_db,
    ):
        """_handle_shutdown should use defaults for missing params."""
        with patch("services.agent_manager.logger"):
            await agent_manager_with_lifecycle.register_connection(
                "agent-123", mock_websocket, "server-456"
            )

        notification = json.dumps({
            "jsonrpc": "2.0",
            "method": "agent.shutdown",
            "params": {},
        })

        with patch("services.agent_manager.logger"):
            await agent_manager_with_lifecycle.handle_message("agent-123", notification)

        call_args = mock_lifecycle_manager.handle_shutdown.call_args
        request = call_args[0][0]
        assert request.reason == "unknown"
        assert request.restart is False

    @pytest.mark.asyncio
    async def test_handle_shutdown_empty_params(
        self,
        agent_manager_with_lifecycle,
        mock_websocket,
        mock_lifecycle_manager,
        mock_agent_db,
    ):
        """_handle_shutdown should handle no params."""
        with patch("services.agent_manager.logger"):
            await agent_manager_with_lifecycle.register_connection(
                "agent-123", mock_websocket, "server-456"
            )

        notification = json.dumps({
            "jsonrpc": "2.0",
            "method": "agent.shutdown",
        })

        with patch("services.agent_manager.logger"):
            await agent_manager_with_lifecycle.handle_message("agent-123", notification)

        mock_lifecycle_manager.handle_shutdown.assert_called_once()


class TestBuiltinHandlerRegistration:
    """Tests for built-in handler registration."""

    def test_heartbeat_handler_registered(self, agent_manager):
        """Heartbeat handler should be registered on init."""
        assert "agent.heartbeat" in agent_manager._notification_handlers
        handler = agent_manager._notification_handlers["agent.heartbeat"]
        assert handler == agent_manager._handle_heartbeat

    def test_shutdown_handler_registered(self, agent_manager):
        """Shutdown handler should be registered on init."""
        assert "agent.shutdown" in agent_manager._notification_handlers
        handler = agent_manager._notification_handlers["agent.shutdown"]
        assert handler == agent_manager._handle_shutdown


class TestNotificationHandlerIntegration:
    """Integration tests for notification handling flow."""

    @pytest.mark.asyncio
    async def test_notification_flow_end_to_end(
        self,
        agent_manager_with_lifecycle,
        mock_websocket,
        mock_lifecycle_manager,
        mock_agent_db,
    ):
        """Test complete notification handling flow."""
        # Register connection
        with patch("services.agent_manager.logger"):
            await agent_manager_with_lifecycle.register_connection(
                "agent-123", mock_websocket, "server-456"
            )

        # Send heartbeat
        heartbeat_msg = json.dumps({
            "jsonrpc": "2.0",
            "method": "agent.heartbeat",
            "params": {"cpu_percent": 25.0},
        })

        with patch("services.agent_manager.logger"):
            await agent_manager_with_lifecycle.handle_message("agent-123", heartbeat_msg)

        assert mock_lifecycle_manager.record_heartbeat.call_count == 1

        # Send shutdown
        shutdown_msg = json.dumps({
            "jsonrpc": "2.0",
            "method": "agent.shutdown",
            "params": {"reason": "test"},
        })

        with patch("services.agent_manager.logger"):
            await agent_manager_with_lifecycle.handle_message("agent-123", shutdown_msg)

        assert mock_lifecycle_manager.handle_shutdown.call_count == 1
        assert "agent-123" not in agent_manager_with_lifecycle._connections

    @pytest.mark.asyncio
    async def test_custom_handler_with_builtin(
        self, agent_manager_with_lifecycle, mock_websocket, mock_agent_db
    ):
        """Test that custom handlers work alongside built-in handlers."""
        custom_handler = AsyncMock()

        with patch("services.agent_manager.logger"):
            await agent_manager_with_lifecycle.register_connection(
                "agent-123", mock_websocket, "server-456"
            )
            agent_manager_with_lifecycle.register_notification_handler(
                "custom.event", custom_handler
            )

        # Custom notification
        custom_msg = json.dumps({
            "jsonrpc": "2.0",
            "method": "custom.event",
            "params": {"data": "test"},
        })

        with patch("services.agent_manager.logger"):
            await agent_manager_with_lifecycle.handle_message("agent-123", custom_msg)

        custom_handler.assert_called_once_with("agent-123", {"data": "test"})

        # Built-in handlers should still work
        assert "agent.heartbeat" in agent_manager_with_lifecycle._notification_handlers
        assert "agent.shutdown" in agent_manager_with_lifecycle._notification_handlers
