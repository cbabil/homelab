"""
Unit tests for services/agent_lifecycle.py.

Tests AgentLifecycleManager - heartbeat tracking, version management,
shutdown handling, and stale agent detection.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.agent import (
    Agent,
    AgentConfig,
    AgentHeartbeat,
    AgentShutdownRequest,
    AgentStatus,
)
from services.agent_lifecycle import CURRENT_AGENT_VERSION, AgentLifecycleManager


@pytest.fixture
def mock_agent_db():
    """Create mock agent database service."""
    db = MagicMock()
    db.update_agent = AsyncMock()
    return db


@pytest.fixture
def default_config():
    """Create default agent config."""
    return AgentConfig(heartbeat_interval=30, heartbeat_timeout=90)


@pytest.fixture
def lifecycle_manager(mock_agent_db, default_config):
    """Create AgentLifecycleManager with mocked dependencies."""
    with patch("services.agent_lifecycle.logger"):
        return AgentLifecycleManager(mock_agent_db, default_config)


class TestAgentLifecycleManagerInit:
    """Tests for AgentLifecycleManager initialization."""

    def test_init_stores_db_service(self, mock_agent_db):
        """Init should store agent_db reference."""
        with patch("services.agent_lifecycle.logger"):
            manager = AgentLifecycleManager(mock_agent_db)
        assert manager._agent_db is mock_agent_db

    def test_init_uses_default_config(self, mock_agent_db):
        """Init should use default config if none provided."""
        with patch("services.agent_lifecycle.logger"):
            manager = AgentLifecycleManager(mock_agent_db)
        assert manager._config.heartbeat_interval == 30  # AgentConfig default

    def test_init_uses_provided_config(self, mock_agent_db, default_config):
        """Init should use provided config."""
        custom_config = AgentConfig(heartbeat_interval=60, heartbeat_timeout=180)
        with patch("services.agent_lifecycle.logger"):
            manager = AgentLifecycleManager(mock_agent_db, custom_config)
        assert manager._config.heartbeat_interval == 60

    def test_init_state(self, mock_agent_db):
        """Init should set proper initial state."""
        with patch("services.agent_lifecycle.logger"):
            manager = AgentLifecycleManager(mock_agent_db)
        assert manager._heartbeat_task is None
        assert manager._shutdown_handlers == []
        assert manager._last_heartbeats == {}
        assert manager._running is False


class TestSetConfig:
    """Tests for set_config method."""

    def test_set_config_updates_and_logs(self, lifecycle_manager):
        """set_config should update configuration and log."""
        new_config = AgentConfig(heartbeat_interval=45, heartbeat_timeout=120)
        with patch("services.agent_lifecycle.logger") as mock_logger:
            lifecycle_manager.set_config(new_config)
        assert lifecycle_manager._config.heartbeat_interval == 45
        assert lifecycle_manager._config.heartbeat_timeout == 120
        mock_logger.debug.assert_called()


class TestRegisterShutdownHandler:
    """Tests for register_shutdown_handler method."""

    def test_register_handlers(self, lifecycle_manager):
        """register_shutdown_handler should add handlers to list."""
        handler1, handler2 = AsyncMock(), AsyncMock()
        with patch("services.agent_lifecycle.logger"):
            lifecycle_manager.register_shutdown_handler(handler1)
            lifecycle_manager.register_shutdown_handler(handler2)
        assert handler1 in lifecycle_manager._shutdown_handlers
        assert len(lifecycle_manager._shutdown_handlers) == 2


class TestStartStop:
    """Tests for start and stop methods."""

    @pytest.mark.asyncio
    async def test_start_creates_task(self, lifecycle_manager):
        """start should create heartbeat task."""
        with patch("services.agent_lifecycle.logger"):
            await lifecycle_manager.start()
        try:
            assert lifecycle_manager._running is True
            assert lifecycle_manager._heartbeat_task is not None
        finally:
            await lifecycle_manager.stop()

    @pytest.mark.asyncio
    async def test_start_already_running(self, lifecycle_manager):
        """start should warn if already running."""
        with patch("services.agent_lifecycle.logger") as mock_logger:
            await lifecycle_manager.start()
            await lifecycle_manager.start()  # Second call
            mock_logger.warning.assert_called()
        await lifecycle_manager.stop()

    @pytest.mark.asyncio
    async def test_stop_cleans_up(self, lifecycle_manager):
        """stop should cleanup state."""
        lifecycle_manager._last_heartbeats["agent-1"] = datetime.now(UTC)
        with patch("services.agent_lifecycle.logger"):
            await lifecycle_manager.start()
            await lifecycle_manager.stop()
        assert lifecycle_manager._running is False
        assert lifecycle_manager._heartbeat_task is None
        assert lifecycle_manager._last_heartbeats == {}

    @pytest.mark.asyncio
    async def test_stop_without_start(self, lifecycle_manager):
        """stop should handle being called without start."""
        with patch("services.agent_lifecycle.logger"):
            await lifecycle_manager.stop()
        assert lifecycle_manager._running is False


class TestRecordHeartbeat:
    """Tests for record_heartbeat method."""

    @pytest.mark.asyncio
    async def test_record_heartbeat_success(self, lifecycle_manager, mock_agent_db):
        """record_heartbeat should update tracking and database."""
        now = datetime.now(UTC)
        heartbeat = AgentHeartbeat(
            agent_id="agent-123",
            timestamp=now,
            cpu_percent=50.0,
            memory_percent=60.0,
        )

        with patch("services.agent_lifecycle.logger"):
            await lifecycle_manager.record_heartbeat(heartbeat)

        assert "agent-123" in lifecycle_manager._last_heartbeats
        assert lifecycle_manager._last_heartbeats["agent-123"] == now
        mock_agent_db.update_agent.assert_called_once()

    @pytest.mark.asyncio
    async def test_record_heartbeat_updates_existing(
        self, lifecycle_manager, mock_agent_db
    ):
        """record_heartbeat should update existing agent timestamp."""
        old_time = datetime.now(UTC) - timedelta(minutes=5)
        new_time = datetime.now(UTC)
        lifecycle_manager._last_heartbeats["agent-123"] = old_time

        heartbeat = AgentHeartbeat(agent_id="agent-123", timestamp=new_time)

        with patch("services.agent_lifecycle.logger"):
            await lifecycle_manager.record_heartbeat(heartbeat)

        assert lifecycle_manager._last_heartbeats["agent-123"] == new_time


class TestHandleShutdown:
    """Tests for handle_shutdown method."""

    @pytest.mark.asyncio
    async def test_handle_shutdown_disconnected(self, lifecycle_manager, mock_agent_db):
        """handle_shutdown should set status to disconnected."""
        mock_agent_db.update_agent = AsyncMock()
        lifecycle_manager._last_heartbeats["agent-123"] = datetime.now(UTC)

        request = AgentShutdownRequest(
            agent_id="agent-123",
            reason="maintenance",
            restart=False,
        )

        with patch("services.agent_lifecycle.logger"):
            await lifecycle_manager.handle_shutdown(request)

        call_args = mock_agent_db.update_agent.call_args
        assert call_args[0][0] == "agent-123"
        update = call_args[0][1]
        assert update.status == AgentStatus.DISCONNECTED
        assert "agent-123" not in lifecycle_manager._last_heartbeats

    @pytest.mark.asyncio
    async def test_handle_shutdown_restart_pending(
        self, lifecycle_manager, mock_agent_db
    ):
        """handle_shutdown with restart should set status to pending."""
        mock_agent_db.update_agent = AsyncMock()

        request = AgentShutdownRequest(
            agent_id="agent-123",
            reason="update",
            restart=True,
        )

        with patch("services.agent_lifecycle.logger"):
            await lifecycle_manager.handle_shutdown(request)

        call_args = mock_agent_db.update_agent.call_args
        update = call_args[0][1]
        assert update.status == AgentStatus.PENDING

    @pytest.mark.asyncio
    async def test_handle_shutdown_calls_handlers(
        self, lifecycle_manager, mock_agent_db
    ):
        """handle_shutdown should notify all handlers."""
        handler1 = AsyncMock()
        handler2 = AsyncMock()
        lifecycle_manager._shutdown_handlers = [handler1, handler2]
        mock_agent_db.update_agent = AsyncMock()

        request = AgentShutdownRequest(agent_id="agent-123", reason="test")

        with patch("services.agent_lifecycle.logger"):
            await lifecycle_manager.handle_shutdown(request)

        handler1.assert_called_once_with("agent-123", "test", False)
        handler2.assert_called_once_with("agent-123", "test", False)

    @pytest.mark.asyncio
    async def test_handle_shutdown_handler_error(
        self, lifecycle_manager, mock_agent_db
    ):
        """handle_shutdown should continue if handler errors."""
        handler1 = AsyncMock(side_effect=Exception("Handler error"))
        handler2 = AsyncMock()
        lifecycle_manager._shutdown_handlers = [handler1, handler2]
        mock_agent_db.update_agent = AsyncMock()

        request = AgentShutdownRequest(agent_id="agent-123", reason="test")

        with patch("services.agent_lifecycle.logger"):
            await lifecycle_manager.handle_shutdown(request)

        handler2.assert_called_once()


class TestCheckVersion:
    """Tests for check_version method."""

    def test_check_version_current(self, lifecycle_manager):
        """check_version should return no update for current version."""
        with patch("services.agent_lifecycle.logger"):
            result = lifecycle_manager.check_version(CURRENT_AGENT_VERSION)
        assert result.update_available is False
        assert result.current_version == CURRENT_AGENT_VERSION
        assert result.latest_version == CURRENT_AGENT_VERSION

    def test_check_version_older(self, lifecycle_manager):
        """check_version should return update available for older version."""
        with patch("services.agent_lifecycle.logger"):
            result = lifecycle_manager.check_version("0.9.0")
        assert result.update_available is True
        assert result.release_notes is not None
        assert result.update_url is not None

    def test_check_version_newer(self, lifecycle_manager):
        """check_version should return no update for newer version."""
        with patch("services.agent_lifecycle.logger"):
            result = lifecycle_manager.check_version("99.0.0")
        assert result.update_available is False


class TestTriggerUpdate:
    """Tests for trigger_update method."""

    @pytest.mark.asyncio
    async def test_trigger_update_success(self, lifecycle_manager, mock_agent_db):
        """trigger_update should mark agent for update."""
        mock_agent = Agent(
            id="agent-123", server_id="srv-1", status=AgentStatus.CONNECTED
        )
        mock_agent_db.update_agent = AsyncMock(return_value=mock_agent)

        with (
            patch("services.agent_lifecycle.logger"),
            patch("services.agent_lifecycle.log_event", new_callable=AsyncMock),
        ):
            result = await lifecycle_manager.trigger_update("agent-123")

        assert result is True
        call_args = mock_agent_db.update_agent.call_args
        assert call_args[0][1].status == AgentStatus.UPDATING

    @pytest.mark.asyncio
    async def test_trigger_update_not_found(self, lifecycle_manager, mock_agent_db):
        """trigger_update should return False if agent not found."""
        mock_agent_db.update_agent = AsyncMock(return_value=None)

        with patch("services.agent_lifecycle.logger"):
            result = await lifecycle_manager.trigger_update("nonexistent")

        assert result is False


class TestGetStaleAgents:
    """Tests for get_stale_agents method."""

    @pytest.mark.asyncio
    async def test_get_stale_agents_none(self, lifecycle_manager):
        """get_stale_agents should return empty list when none stale."""
        lifecycle_manager._last_heartbeats["agent-1"] = datetime.now(UTC)

        with patch("services.agent_lifecycle.logger"):
            result = await lifecycle_manager.get_stale_agents()

        assert result == []

    @pytest.mark.asyncio
    async def test_get_stale_agents_some(self, lifecycle_manager):
        """get_stale_agents should return stale agent IDs."""
        now = datetime.now(UTC)
        lifecycle_manager._last_heartbeats["agent-1"] = now
        lifecycle_manager._last_heartbeats["agent-2"] = now - timedelta(seconds=120)

        with patch("services.agent_lifecycle.logger"):
            result = await lifecycle_manager.get_stale_agents()

        assert "agent-2" in result
        assert "agent-1" not in result


class TestIsAgentStale:
    """Tests for is_agent_stale method."""

    def test_is_agent_stale_unknown(self, lifecycle_manager):
        """is_agent_stale should return True for unknown agent."""
        with patch("services.agent_lifecycle.logger"):
            result = lifecycle_manager.is_agent_stale("unknown-agent")
        assert result is True

    def test_is_agent_stale_active(self, lifecycle_manager):
        """is_agent_stale should return False for recently active agent."""
        lifecycle_manager._last_heartbeats["agent-1"] = datetime.now(UTC)

        with patch("services.agent_lifecycle.logger"):
            result = lifecycle_manager.is_agent_stale("agent-1")

        assert result is False

    def test_is_agent_stale_timeout(self, lifecycle_manager):
        """is_agent_stale should return True for timed out agent."""
        old_time = datetime.now(UTC) - timedelta(seconds=120)
        lifecycle_manager._last_heartbeats["agent-1"] = old_time

        with patch("services.agent_lifecycle.logger"):
            result = lifecycle_manager.is_agent_stale("agent-1")

        assert result is True


class TestRegisterUnregisterConnection:
    """Tests for register/unregister agent connection."""

    def test_register_and_unregister(self, lifecycle_manager):
        """register/unregister should add/remove agent from tracking."""
        with patch("services.agent_lifecycle.logger"):
            lifecycle_manager.register_agent_connection("agent-123")
            assert "agent-123" in lifecycle_manager._last_heartbeats
            lifecycle_manager.unregister_agent_connection("agent-123")
            assert "agent-123" not in lifecycle_manager._last_heartbeats
            lifecycle_manager.unregister_agent_connection(
                "nonexistent"
            )  # Should not raise


class TestCompareVersions:
    """Tests for _compare_versions method."""

    def test_compare_versions_newer(self, lifecycle_manager):
        """_compare_versions should return True when latest > current."""
        assert lifecycle_manager._compare_versions("1.0.0", "1.1.0") is True
        assert lifecycle_manager._compare_versions("1.0.0", "2.0.0") is True
        assert lifecycle_manager._compare_versions("1.0.0", "1.0.1") is True

    def test_compare_versions_same(self, lifecycle_manager):
        """_compare_versions should return False when equal."""
        assert lifecycle_manager._compare_versions("1.0.0", "1.0.0") is False

    def test_compare_versions_older(self, lifecycle_manager):
        """_compare_versions should return False when latest < current."""
        assert lifecycle_manager._compare_versions("2.0.0", "1.0.0") is False

    def test_compare_versions_different_lengths(self, lifecycle_manager):
        """_compare_versions should handle different version lengths."""
        assert lifecycle_manager._compare_versions("1.0", "1.0.1") is True
        assert lifecycle_manager._compare_versions("1.0.0", "1.1") is True

    def test_compare_versions_invalid(self, lifecycle_manager):
        """_compare_versions should return False for invalid versions."""
        with patch("services.agent_lifecycle.logger"):
            assert lifecycle_manager._compare_versions("invalid", "1.0.0") is False
            assert lifecycle_manager._compare_versions("1.0.0", "invalid") is False


class TestHelperMethods:
    """Tests for helper methods."""

    def test_get_release_notes(self, lifecycle_manager):
        """_get_release_notes should return release notes string."""
        notes = lifecycle_manager._get_release_notes()
        assert CURRENT_AGENT_VERSION in notes

    def test_get_update_url(self, lifecycle_manager):
        """_get_update_url should return download URL."""
        url = lifecycle_manager._get_update_url()
        assert CURRENT_AGENT_VERSION in url
        assert "github" in url


class TestCheckStaleAgents:
    """Tests for _check_stale_agents method."""

    @pytest.mark.asyncio
    async def test_check_stale_agents_updates_status(
        self, lifecycle_manager, mock_agent_db
    ):
        """_check_stale_agents should update stale agent status."""
        old_time = datetime.now(UTC) - timedelta(seconds=120)
        lifecycle_manager._last_heartbeats["agent-1"] = old_time
        mock_agent_db.update_agent = AsyncMock()

        with patch("services.agent_lifecycle.logger"):
            await lifecycle_manager._check_stale_agents()

        mock_agent_db.update_agent.assert_called()
        call_args = mock_agent_db.update_agent.call_args
        assert call_args[0][1].status == AgentStatus.DISCONNECTED
        assert "agent-1" not in lifecycle_manager._last_heartbeats


class TestHeartbeatMonitorLoop:
    """Tests for _heartbeat_monitor_loop method."""

    @pytest.mark.asyncio
    async def test_heartbeat_loop_runs(self, lifecycle_manager):
        """_heartbeat_monitor_loop should run until stopped."""
        lifecycle_manager._config.heartbeat_interval = 0.1  # Fast for testing
        lifecycle_manager._running = True

        check_count = [0]

        async def mock_check():
            check_count[0] += 1
            if check_count[0] >= 2:
                lifecycle_manager._running = False

        lifecycle_manager._check_stale_agents = mock_check

        with patch("services.agent_lifecycle.logger"):
            await lifecycle_manager._heartbeat_monitor_loop()

        assert check_count[0] >= 2

    @pytest.mark.asyncio
    async def test_heartbeat_loop_handles_error(self, lifecycle_manager):
        """_heartbeat_monitor_loop should continue on error."""
        lifecycle_manager._config.heartbeat_interval = 0.1
        lifecycle_manager._running = True

        call_count = [0]

        async def mock_check():
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("Test error")
            lifecycle_manager._running = False

        lifecycle_manager._check_stale_agents = mock_check

        with patch("services.agent_lifecycle.logger"):
            await lifecycle_manager._heartbeat_monitor_loop()

    @pytest.mark.asyncio
    async def test_heartbeat_loop_handles_cancelled(self, lifecycle_manager):
        """_heartbeat_monitor_loop should exit on CancelledError."""
        import asyncio

        lifecycle_manager._config.heartbeat_interval = 0.1
        lifecycle_manager._running = True

        async def mock_check():
            raise asyncio.CancelledError()

        lifecycle_manager._check_stale_agents = mock_check

        with patch("services.agent_lifecycle.logger"):
            await lifecycle_manager._heartbeat_monitor_loop()
        # Should exit cleanly without raising
