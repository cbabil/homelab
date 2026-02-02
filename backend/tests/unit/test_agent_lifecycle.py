"""
Unit tests for services/agent_lifecycle.py

Tests for agent health monitoring, version management, and shutdown coordination.
"""

import asyncio
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import services.agent_lifecycle as lifecycle_module
from services.agent_lifecycle import AgentLifecycleManager, CURRENT_AGENT_VERSION


@pytest.fixture
def mock_agent_db():
    """Create mock AgentDatabaseService."""
    return AsyncMock()


@pytest.fixture
def lifecycle_manager(mock_agent_db):
    """Create lifecycle manager with mocked database."""
    with patch.object(lifecycle_module, "logger"):
        return AgentLifecycleManager(agent_db=mock_agent_db)


class TestAgentLifecycleManagerInit:
    """Tests for initialization."""

    def test_init_with_default_config(self, mock_agent_db):
        """Should initialize with default config."""
        with patch.object(lifecycle_module, "logger"):
            manager = AgentLifecycleManager(agent_db=mock_agent_db)

            assert manager._agent_db is mock_agent_db
            assert manager._config is not None
            assert manager._running is False

    def test_init_with_custom_config(self, mock_agent_db):
        """Should use provided config."""
        mock_config = MagicMock()
        mock_config.heartbeat_interval = 30
        mock_config.heartbeat_timeout = 90

        with patch.object(lifecycle_module, "logger"):
            manager = AgentLifecycleManager(
                agent_db=mock_agent_db, default_config=mock_config
            )

            assert manager._config is mock_config


class TestSetConfig:
    """Tests for set_config method."""

    def test_set_config_updates_config(self, lifecycle_manager):
        """Should update configuration."""
        mock_config = MagicMock()
        mock_config.heartbeat_interval = 60
        mock_config.heartbeat_timeout = 180

        lifecycle_manager.set_config(mock_config)

        assert lifecycle_manager._config is mock_config


class TestRegisterShutdownHandler:
    """Tests for register_shutdown_handler method."""

    def test_register_shutdown_handler_adds_handler(self, lifecycle_manager):
        """Should add handler to list."""
        handler = MagicMock()

        lifecycle_manager.register_shutdown_handler(handler)

        assert handler in lifecycle_manager._shutdown_handlers

    def test_register_multiple_handlers(self, lifecycle_manager):
        """Should allow multiple handlers."""
        handler1 = MagicMock()
        handler2 = MagicMock()

        lifecycle_manager.register_shutdown_handler(handler1)
        lifecycle_manager.register_shutdown_handler(handler2)

        assert len(lifecycle_manager._shutdown_handlers) == 2


class TestStartStop:
    """Tests for start and stop methods."""

    @pytest.mark.asyncio
    async def test_start_sets_running(self, lifecycle_manager):
        """Should set running flag and create task."""
        with patch.object(
            lifecycle_manager, "_heartbeat_monitor_loop", new_callable=AsyncMock
        ):
            await lifecycle_manager.start()

            assert lifecycle_manager._running is True
            assert lifecycle_manager._heartbeat_task is not None

            # Cleanup
            await lifecycle_manager.stop()

    @pytest.mark.asyncio
    async def test_start_already_running(self, lifecycle_manager):
        """Should do nothing if already running."""
        lifecycle_manager._running = True

        with patch.object(lifecycle_module, "logger") as mock_logger:
            await lifecycle_manager.start()

            mock_logger.warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_clears_state(self, lifecycle_manager):
        """Should clear state on stop."""
        lifecycle_manager._running = True
        lifecycle_manager._last_heartbeats = {"agent-1": datetime.now(UTC)}
        lifecycle_manager._heartbeat_task = asyncio.create_task(asyncio.sleep(10))

        await lifecycle_manager.stop()

        assert lifecycle_manager._running is False
        assert lifecycle_manager._heartbeat_task is None
        assert len(lifecycle_manager._last_heartbeats) == 0


class TestRecordHeartbeat:
    """Tests for record_heartbeat method."""

    @pytest.mark.asyncio
    async def test_record_heartbeat_updates_timestamp(
        self, lifecycle_manager, mock_agent_db
    ):
        """Should record heartbeat timestamp."""
        mock_heartbeat = MagicMock()
        mock_heartbeat.agent_id = "agent-1"
        mock_heartbeat.timestamp = datetime.now(UTC)
        mock_heartbeat.cpu_percent = 50.0
        mock_heartbeat.memory_percent = 60.0

        await lifecycle_manager.record_heartbeat(mock_heartbeat)

        assert "agent-1" in lifecycle_manager._last_heartbeats
        mock_agent_db.update_agent.assert_called_once()


class TestHandleShutdown:
    """Tests for handle_shutdown method."""

    @pytest.mark.asyncio
    async def test_handle_shutdown_sets_disconnected(
        self, lifecycle_manager, mock_agent_db
    ):
        """Should set status to disconnected."""
        mock_request = MagicMock()
        mock_request.agent_id = "agent-1"
        mock_request.reason = "User requested"
        mock_request.restart = False

        await lifecycle_manager.handle_shutdown(mock_request)

        mock_agent_db.update_agent.assert_called_once()
        call_args = mock_agent_db.update_agent.call_args
        assert call_args[0][0] == "agent-1"

    @pytest.mark.asyncio
    async def test_handle_shutdown_sets_pending_on_restart(
        self, lifecycle_manager, mock_agent_db
    ):
        """Should set status to pending if restarting."""
        mock_request = MagicMock()
        mock_request.agent_id = "agent-1"
        mock_request.reason = "Update"
        mock_request.restart = True

        await lifecycle_manager.handle_shutdown(mock_request)

        mock_agent_db.update_agent.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_shutdown_removes_from_tracking(
        self, lifecycle_manager, mock_agent_db
    ):
        """Should remove from heartbeat tracking."""
        lifecycle_manager._last_heartbeats["agent-1"] = datetime.now(UTC)

        mock_request = MagicMock()
        mock_request.agent_id = "agent-1"
        mock_request.reason = "Shutdown"
        mock_request.restart = False

        await lifecycle_manager.handle_shutdown(mock_request)

        assert "agent-1" not in lifecycle_manager._last_heartbeats

    @pytest.mark.asyncio
    async def test_handle_shutdown_calls_handlers(
        self, lifecycle_manager, mock_agent_db
    ):
        """Should call registered shutdown handlers."""
        handler = AsyncMock()
        lifecycle_manager._shutdown_handlers.append(handler)

        mock_request = MagicMock()
        mock_request.agent_id = "agent-1"
        mock_request.reason = "Test"
        mock_request.restart = False

        await lifecycle_manager.handle_shutdown(mock_request)

        handler.assert_called_once_with("agent-1", "Test", False)

    @pytest.mark.asyncio
    async def test_handle_shutdown_handles_handler_error(
        self, lifecycle_manager, mock_agent_db
    ):
        """Should handle errors in shutdown handlers."""
        handler = AsyncMock(side_effect=RuntimeError("Handler error"))
        lifecycle_manager._shutdown_handlers.append(handler)

        mock_request = MagicMock()
        mock_request.agent_id = "agent-1"
        mock_request.reason = "Test"
        mock_request.restart = False

        # Should not raise
        await lifecycle_manager.handle_shutdown(mock_request)


class TestCheckVersion:
    """Tests for check_version method."""

    def test_check_version_no_update_needed(self, lifecycle_manager):
        """Should return no update when version matches."""
        result = lifecycle_manager.check_version(CURRENT_AGENT_VERSION)

        assert result.update_available is False
        assert result.current_version == CURRENT_AGENT_VERSION

    def test_check_version_update_available(self, lifecycle_manager):
        """Should detect when update is available."""
        result = lifecycle_manager.check_version("0.9.0")

        assert result.update_available is True
        assert result.latest_version == CURRENT_AGENT_VERSION
        assert result.release_notes is not None
        assert result.update_url is not None

    def test_check_version_newer_than_latest(self, lifecycle_manager):
        """Should handle newer version than current."""
        result = lifecycle_manager.check_version("99.0.0")

        assert result.update_available is False


class TestTriggerUpdate:
    """Tests for trigger_update method."""

    @pytest.mark.asyncio
    async def test_trigger_update_success(self, lifecycle_manager, mock_agent_db):
        """Should mark agent for update."""
        mock_agent = MagicMock()
        mock_agent.server_id = "server-1"
        mock_agent_db.update_agent.return_value = mock_agent

        with patch.object(lifecycle_module, "log_event", new_callable=AsyncMock):
            result = await lifecycle_manager.trigger_update("agent-1")

            assert result is True
            mock_agent_db.update_agent.assert_called_once()

    @pytest.mark.asyncio
    async def test_trigger_update_failure(self, lifecycle_manager, mock_agent_db):
        """Should return False on failure."""
        mock_agent_db.update_agent.return_value = None

        result = await lifecycle_manager.trigger_update("agent-1")

        assert result is False


class TestGetStaleAgents:
    """Tests for get_stale_agents method."""

    @pytest.mark.asyncio
    async def test_get_stale_agents_returns_stale(self, lifecycle_manager):
        """Should return stale agent IDs."""
        # Set up stale agent (old timestamp)
        old_time = datetime.now(UTC) - timedelta(hours=1)
        lifecycle_manager._last_heartbeats["stale-agent"] = old_time

        # Set up fresh agent
        lifecycle_manager._last_heartbeats["fresh-agent"] = datetime.now(UTC)

        result = await lifecycle_manager.get_stale_agents()

        assert "stale-agent" in result
        assert "fresh-agent" not in result

    @pytest.mark.asyncio
    async def test_get_stale_agents_empty(self, lifecycle_manager):
        """Should return empty list when no stale agents."""
        lifecycle_manager._last_heartbeats["agent-1"] = datetime.now(UTC)

        result = await lifecycle_manager.get_stale_agents()

        assert len(result) == 0


class TestIsAgentStale:
    """Tests for is_agent_stale method."""

    def test_is_agent_stale_unknown(self, lifecycle_manager):
        """Should return True for unknown agent."""
        result = lifecycle_manager.is_agent_stale("unknown-agent")

        assert result is True

    def test_is_agent_stale_fresh(self, lifecycle_manager):
        """Should return False for fresh agent."""
        lifecycle_manager._last_heartbeats["agent-1"] = datetime.now(UTC)

        result = lifecycle_manager.is_agent_stale("agent-1")

        assert result is False

    def test_is_agent_stale_stale(self, lifecycle_manager):
        """Should return True for stale agent."""
        old_time = datetime.now(UTC) - timedelta(hours=1)
        lifecycle_manager._last_heartbeats["agent-1"] = old_time

        result = lifecycle_manager.is_agent_stale("agent-1")

        assert result is True


class TestRegisterUnregisterAgentConnection:
    """Tests for agent connection registration."""

    def test_register_agent_connection(self, lifecycle_manager):
        """Should add agent to tracking."""
        lifecycle_manager.register_agent_connection("agent-1")

        assert "agent-1" in lifecycle_manager._last_heartbeats

    def test_unregister_agent_connection(self, lifecycle_manager):
        """Should remove agent from tracking."""
        lifecycle_manager._last_heartbeats["agent-1"] = datetime.now(UTC)

        lifecycle_manager.unregister_agent_connection("agent-1")

        assert "agent-1" not in lifecycle_manager._last_heartbeats

    def test_unregister_unknown_agent(self, lifecycle_manager):
        """Should not error for unknown agent."""
        # Should not raise
        lifecycle_manager.unregister_agent_connection("unknown")


class TestHeartbeatMonitorLoop:
    """Tests for _heartbeat_monitor_loop method."""

    @pytest.mark.asyncio
    async def test_heartbeat_monitor_loop_runs(self, lifecycle_manager):
        """Should run monitoring loop."""
        lifecycle_manager._running = True
        lifecycle_manager._config.heartbeat_interval = 0.01

        with patch.object(
            lifecycle_manager, "_check_stale_agents", new_callable=AsyncMock
        ) as mock_check:
            # Run loop briefly then stop
            task = asyncio.create_task(lifecycle_manager._heartbeat_monitor_loop())
            await asyncio.sleep(0.05)
            lifecycle_manager._running = False
            await asyncio.sleep(0.02)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

            assert mock_check.call_count > 0

    @pytest.mark.asyncio
    async def test_heartbeat_monitor_loop_handles_error(self, lifecycle_manager):
        """Should handle errors in loop."""
        lifecycle_manager._running = True
        lifecycle_manager._config.heartbeat_interval = 0.01

        call_count = 0

        async def failing_check():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise RuntimeError("Check error")

        with patch.object(
            lifecycle_manager, "_check_stale_agents", side_effect=failing_check
        ):
            task = asyncio.create_task(lifecycle_manager._heartbeat_monitor_loop())
            await asyncio.sleep(0.1)
            lifecycle_manager._running = False
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass


class TestCheckStaleAgents:
    """Tests for _check_stale_agents method."""

    @pytest.mark.asyncio
    async def test_check_stale_agents_updates_status(
        self, lifecycle_manager, mock_agent_db
    ):
        """Should update status of stale agents."""
        old_time = datetime.now(UTC) - timedelta(hours=1)
        lifecycle_manager._last_heartbeats["stale-agent"] = old_time

        await lifecycle_manager._check_stale_agents()

        mock_agent_db.update_agent.assert_called_once()
        assert "stale-agent" not in lifecycle_manager._last_heartbeats


class TestCompareVersions:
    """Tests for _compare_versions method."""

    def test_compare_versions_latest_greater(self, lifecycle_manager):
        """Should return True when latest > current."""
        assert lifecycle_manager._compare_versions("1.0.0", "1.1.0") is True
        assert lifecycle_manager._compare_versions("1.0.0", "2.0.0") is True
        assert lifecycle_manager._compare_versions("1.0.0", "1.0.1") is True

    def test_compare_versions_equal(self, lifecycle_manager):
        """Should return False when versions equal."""
        assert lifecycle_manager._compare_versions("1.0.0", "1.0.0") is False

    def test_compare_versions_current_greater(self, lifecycle_manager):
        """Should return False when current > latest."""
        assert lifecycle_manager._compare_versions("2.0.0", "1.0.0") is False
        assert lifecycle_manager._compare_versions("1.1.0", "1.0.0") is False

    def test_compare_versions_different_lengths(self, lifecycle_manager):
        """Should handle versions with different segment counts."""
        assert lifecycle_manager._compare_versions("1.0", "1.0.1") is True
        assert lifecycle_manager._compare_versions("1.0.0.0", "1.0.1") is True

    def test_compare_versions_invalid_format(self, lifecycle_manager):
        """Should return False for invalid version formats."""
        assert lifecycle_manager._compare_versions("invalid", "1.0.0") is False
        assert lifecycle_manager._compare_versions("1.0.0", "invalid") is False


class TestGetReleaseNotes:
    """Tests for _get_release_notes method."""

    def test_get_release_notes_returns_string(self, lifecycle_manager):
        """Should return release notes string."""
        result = lifecycle_manager._get_release_notes()

        assert isinstance(result, str)
        assert CURRENT_AGENT_VERSION in result


class TestGetUpdateUrl:
    """Tests for _get_update_url method."""

    def test_get_update_url_returns_url(self, lifecycle_manager):
        """Should return update URL."""
        result = lifecycle_manager._get_update_url()

        assert isinstance(result, str)
        assert CURRENT_AGENT_VERSION in result
        assert "http" in result
