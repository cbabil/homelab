"""
Unit tests for services/agent_manager.py - Core functionality.

Tests AgentManager initialization, connection management, and basic operations.
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.agent import AgentStatus
from services.agent_manager import (
    MAX_MESSAGE_SIZE_BYTES,
    AgentConnection,
    AgentManager,
)


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


class TestAgentManagerInit:
    """Tests for AgentManager initialization."""

    def test_init_stores_db_service(self, mock_agent_db):
        """Init should store agent_db reference."""
        with patch("services.agent_manager.logger"):
            manager = AgentManager(mock_agent_db)
        assert manager._agent_db is mock_agent_db

    def test_init_stores_lifecycle_manager(self, mock_agent_db, mock_lifecycle_manager):
        """Init should store lifecycle manager reference."""
        with patch("services.agent_manager.logger"):
            manager = AgentManager(mock_agent_db, mock_lifecycle_manager)
        assert manager._lifecycle is mock_lifecycle_manager

    def test_init_empty_connections(self, mock_agent_db):
        """Init should have empty connections dict."""
        with patch("services.agent_manager.logger"):
            manager = AgentManager(mock_agent_db)
        assert manager._connections == {}

    def test_init_registers_builtin_handlers(self, mock_agent_db):
        """Init should register heartbeat and shutdown handlers."""
        with patch("services.agent_manager.logger"):
            manager = AgentManager(mock_agent_db)
        assert "agent.heartbeat" in manager._notification_handlers
        assert "agent.shutdown" in manager._notification_handlers


class TestSetLifecycleManager:
    """Tests for set_lifecycle_manager method."""

    def test_set_lifecycle_manager(self, agent_manager, mock_lifecycle_manager):
        """set_lifecycle_manager should store the manager."""
        with patch("services.agent_manager.logger"):
            agent_manager.set_lifecycle_manager(mock_lifecycle_manager)
        assert agent_manager._lifecycle is mock_lifecycle_manager


class TestRegisterNotificationHandler:
    """Tests for register_notification_handler method."""

    def test_register_handler(self, agent_manager):
        """register_notification_handler should add handler to dict."""
        handler = AsyncMock()
        with patch("services.agent_manager.logger"):
            agent_manager.register_notification_handler("test.method", handler)
        assert "test.method" in agent_manager._notification_handlers
        assert agent_manager._notification_handlers["test.method"] is handler

    def test_register_multiple_handlers(self, agent_manager):
        """register_notification_handler should allow multiple handlers."""
        handler1 = AsyncMock()
        handler2 = AsyncMock()
        with patch("services.agent_manager.logger"):
            agent_manager.register_notification_handler("method1", handler1)
            agent_manager.register_notification_handler("method2", handler2)
        assert len(agent_manager._notification_handlers) >= 4  # 2 builtin + 2 custom


class TestGetConnectionLock:
    """Tests for _get_connection_lock method."""

    def test_creates_new_lock(self, agent_manager):
        """_get_connection_lock should create lock for new agent."""
        lock = agent_manager._get_connection_lock("agent-123")
        assert isinstance(lock, asyncio.Lock)
        assert "agent-123" in agent_manager._connection_locks

    def test_returns_existing_lock(self, agent_manager):
        """_get_connection_lock should return existing lock."""
        lock1 = agent_manager._get_connection_lock("agent-123")
        lock2 = agent_manager._get_connection_lock("agent-123")
        assert lock1 is lock2


class TestRegisterConnection:
    """Tests for register_connection method."""

    @pytest.mark.asyncio
    async def test_register_new_connection(
        self, agent_manager, mock_websocket, mock_agent_db
    ):
        """register_connection should add new connection."""
        with patch("services.agent_manager.logger"):
            conn = await agent_manager.register_connection(
                "agent-123", mock_websocket, "server-456"
            )

        assert conn.agent_id == "agent-123"
        assert conn.server_id == "server-456"
        assert conn.websocket is mock_websocket
        assert "agent-123" in agent_manager._connections

    @pytest.mark.asyncio
    async def test_register_updates_database(
        self, agent_manager, mock_websocket, mock_agent_db
    ):
        """register_connection should update agent status in database."""
        with patch("services.agent_manager.logger"):
            await agent_manager.register_connection(
                "agent-123", mock_websocket, "server-456"
            )

        mock_agent_db.update_agent.assert_called_once()
        call_args = mock_agent_db.update_agent.call_args
        assert call_args[0][0] == "agent-123"
        assert call_args[0][1].status == AgentStatus.CONNECTED

    @pytest.mark.asyncio
    async def test_register_with_lifecycle(
        self, agent_manager_with_lifecycle, mock_websocket, mock_lifecycle_manager
    ):
        """register_connection should notify lifecycle manager."""
        with patch("services.agent_manager.logger"):
            await agent_manager_with_lifecycle.register_connection(
                "agent-123", mock_websocket, "server-456"
            )

        mock_lifecycle_manager.register_agent_connection.assert_called_once_with(
            "agent-123"
        )

    @pytest.mark.asyncio
    async def test_register_replaces_existing(
        self, agent_manager, mock_websocket, mock_agent_db
    ):
        """register_connection should close and replace existing connection."""
        old_ws = AsyncMock()
        old_ws.close = AsyncMock()

        with patch("services.agent_manager.logger"):
            # Register first connection
            await agent_manager.register_connection("agent-123", old_ws, "server-456")
            # Register second connection for same agent
            await agent_manager.register_connection(
                "agent-123", mock_websocket, "server-456"
            )

        # Old websocket should be closed
        old_ws.close.assert_called()
        # New connection should be stored
        assert agent_manager._connections["agent-123"].websocket is mock_websocket


class TestUnregisterConnection:
    """Tests for unregister_connection method."""

    @pytest.mark.asyncio
    async def test_unregister_existing_connection(
        self, agent_manager, mock_websocket, mock_agent_db
    ):
        """unregister_connection should remove connection."""
        with patch("services.agent_manager.logger"):
            await agent_manager.register_connection(
                "agent-123", mock_websocket, "server-456"
            )
            await agent_manager.unregister_connection("agent-123")

        assert "agent-123" not in agent_manager._connections
        mock_websocket.close.assert_called()

    @pytest.mark.asyncio
    async def test_unregister_nonexistent(self, agent_manager):
        """unregister_connection should warn for unknown agent."""
        with patch("services.agent_manager.logger") as mock_logger:
            await agent_manager.unregister_connection("nonexistent")
            mock_logger.warning.assert_called()

    @pytest.mark.asyncio
    async def test_unregister_cancels_pending_requests(
        self, agent_manager, mock_websocket
    ):
        """unregister_connection should cancel pending futures."""
        with patch("services.agent_manager.logger"):
            await agent_manager.register_connection(
                "agent-123", mock_websocket, "server-456"
            )

        # Add a pending request
        future = asyncio.get_running_loop().create_future()
        agent_manager._connections["agent-123"].pending_requests["req-1"] = future

        with patch("services.agent_manager.logger"):
            await agent_manager.unregister_connection("agent-123")

        assert future.cancelled()

    @pytest.mark.asyncio
    async def test_unregister_updates_database(
        self, agent_manager, mock_websocket, mock_agent_db
    ):
        """unregister_connection should set status to disconnected."""
        with patch("services.agent_manager.logger"):
            await agent_manager.register_connection(
                "agent-123", mock_websocket, "server-456"
            )
            mock_agent_db.update_agent.reset_mock()
            await agent_manager.unregister_connection("agent-123")

        mock_agent_db.update_agent.assert_called_once()
        call_args = mock_agent_db.update_agent.call_args
        assert call_args[0][1].status == AgentStatus.DISCONNECTED

    @pytest.mark.asyncio
    async def test_unregister_with_lifecycle(
        self, agent_manager_with_lifecycle, mock_websocket, mock_lifecycle_manager
    ):
        """unregister_connection should notify lifecycle manager."""
        with patch("services.agent_manager.logger"):
            await agent_manager_with_lifecycle.register_connection(
                "agent-123", mock_websocket, "server-456"
            )
            await agent_manager_with_lifecycle.unregister_connection("agent-123")

        mock_lifecycle_manager.unregister_agent_connection.assert_called_once_with(
            "agent-123"
        )

    @pytest.mark.asyncio
    async def test_unregister_handles_websocket_close_error(
        self, agent_manager, mock_agent_db
    ):
        """unregister_connection should handle WebSocket close errors gracefully."""
        ws = AsyncMock()
        ws.close = AsyncMock(side_effect=Exception("Close error"))

        with patch("services.agent_manager.logger"):
            await agent_manager.register_connection("agent-123", ws, "server-456")
            # Should not raise
            await agent_manager.unregister_connection("agent-123")

        assert "agent-123" not in agent_manager._connections


class TestIsConnected:
    """Tests for is_connected method."""

    @pytest.mark.asyncio
    async def test_is_connected_true(self, agent_manager, mock_websocket):
        """is_connected should return True for connected agent."""
        with patch("services.agent_manager.logger"):
            await agent_manager.register_connection(
                "agent-123", mock_websocket, "server-456"
            )

        assert agent_manager.is_connected("agent-123") is True

    def test_is_connected_false(self, agent_manager):
        """is_connected should return False for unknown agent."""
        assert agent_manager.is_connected("unknown") is False


class TestGetConnectionByServer:
    """Tests for get_connection_by_server method."""

    @pytest.mark.asyncio
    async def test_get_connection_by_server_found(self, agent_manager, mock_websocket):
        """get_connection_by_server should return matching connection."""
        with patch("services.agent_manager.logger"):
            await agent_manager.register_connection(
                "agent-123", mock_websocket, "server-456"
            )

        conn = agent_manager.get_connection_by_server("server-456")
        assert conn is not None
        assert conn.agent_id == "agent-123"

    def test_get_connection_by_server_not_found(self, agent_manager):
        """get_connection_by_server should return None if not found."""
        conn = agent_manager.get_connection_by_server("unknown")
        assert conn is None


class TestGetConnectedAgentIds:
    """Tests for get_connected_agent_ids method."""

    @pytest.mark.asyncio
    async def test_get_connected_agent_ids(self, agent_manager, mock_websocket):
        """get_connected_agent_ids should return list of agent IDs."""
        with patch("services.agent_manager.logger"):
            await agent_manager.register_connection(
                "agent-1", mock_websocket, "server-1"
            )
            ws2 = AsyncMock()
            await agent_manager.register_connection("agent-2", ws2, "server-2")

        ids = agent_manager.get_connected_agent_ids()
        assert set(ids) == {"agent-1", "agent-2"}

    def test_get_connected_agent_ids_empty(self, agent_manager):
        """get_connected_agent_ids should return empty list if no connections."""
        ids = agent_manager.get_connected_agent_ids()
        assert ids == []


class TestGetConnectionInfo:
    """Tests for get_connection_info method."""

    @pytest.mark.asyncio
    async def test_get_connection_info_found(self, agent_manager, mock_websocket):
        """get_connection_info should return info dict for connected agent."""
        with patch("services.agent_manager.logger"):
            await agent_manager.register_connection(
                "agent-123", mock_websocket, "server-456"
            )

        info = agent_manager.get_connection_info("agent-123")
        assert info is not None
        assert info["agent_id"] == "agent-123"
        assert info["server_id"] == "server-456"
        assert "connected_at" in info
        assert info["pending_requests"] == 0

    def test_get_connection_info_not_found(self, agent_manager):
        """get_connection_info should return None for unknown agent."""
        info = agent_manager.get_connection_info("unknown")
        assert info is None


class TestAgentConnection:
    """Tests for AgentConnection dataclass."""

    def test_agent_connection_defaults(self, mock_websocket):
        """AgentConnection should have proper defaults."""
        conn = AgentConnection(
            agent_id="agent-123",
            websocket=mock_websocket,
            server_id="server-456",
        )
        assert conn.agent_id == "agent-123"
        assert conn.server_id == "server-456"
        assert conn.pending_requests == {}
        assert isinstance(conn.connected_at, datetime)


class TestMaxMessageSize:
    """Tests for MAX_MESSAGE_SIZE_BYTES constant."""

    def test_max_message_size_value(self):
        """MAX_MESSAGE_SIZE_BYTES should be 1MB."""
        assert MAX_MESSAGE_SIZE_BYTES == 1024 * 1024
