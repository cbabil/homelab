"""Tests for the main Agent class.

Tests agent initialization, connection, run loop, and shutdown.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent import Agent
from config import AgentConfig


class TestAgentInit:
    """Tests for Agent initialization."""

    def test_initializes_with_defaults(self):
        """Should initialize with default configuration."""
        with patch("agent.load_config") as mock_load:
            mock_load.return_value = AgentConfig()
            with patch("agent.setup_all_handlers"):
                agent = Agent()

                assert agent.running is True
                assert agent.agent_id is None
                assert agent.websocket is None
                assert agent.rpc_handler is not None

    def test_loads_config_on_init(self):
        """Should load configuration on initialization."""
        with patch("agent.load_config") as mock_load:
            mock_load.return_value = AgentConfig(server_url="wss://test.com")
            with patch("agent.setup_all_handlers"):
                agent = Agent()

                mock_load.assert_called_once()
                assert agent.config.server_url == "wss://test.com"

    def test_sets_up_handlers(self):
        """Should set up RPC handlers on initialization."""
        with patch("agent.load_config") as mock_load:
            mock_load.return_value = AgentConfig()
            with patch("agent.setup_all_handlers") as mock_setup:
                Agent()  # Create agent to trigger setup

                mock_setup.assert_called_once()


class TestAgentConfig:
    """Tests for Agent config property."""

    def test_config_getter(self):
        """Should return current config."""
        with patch("agent.load_config") as mock_load:
            expected_config = AgentConfig(metrics_interval=45)
            mock_load.return_value = expected_config
            with patch("agent.setup_all_handlers"):
                agent = Agent()

                assert agent.config == expected_config

    def test_config_setter(self):
        """Should update config."""
        with patch("agent.load_config") as mock_load:
            mock_load.return_value = AgentConfig()
            with patch("agent.setup_all_handlers"):
                agent = Agent()

                new_config = AgentConfig(metrics_interval=90)
                agent.config = new_config

                assert agent.config.metrics_interval == 90


class TestAgentConnect:
    """Tests for Agent.connect method."""

    @pytest.mark.asyncio
    async def test_successful_connection(self):
        """Should connect and update state on success."""
        with patch("agent.load_config") as mock_load:
            mock_load.return_value = AgentConfig()
            with patch("agent.setup_all_handlers"):
                agent = Agent()

                mock_ws = AsyncMock()
                updated_config = AgentConfig(metrics_interval=60)

                with patch("agent.establish_connection") as mock_conn:
                    mock_conn.return_value = (mock_ws, "agent-123", updated_config)

                    result = await agent.connect()

                    assert result is True
                    assert agent.websocket == mock_ws
                    assert agent.agent_id == "agent-123"
                    assert agent.config.metrics_interval == 60

    @pytest.mark.asyncio
    async def test_failed_connection(self):
        """Should return False on connection failure."""
        with patch("agent.load_config") as mock_load:
            mock_load.return_value = AgentConfig()
            with patch("agent.setup_all_handlers"):
                agent = Agent()

                with patch("agent.establish_connection") as mock_conn:
                    mock_conn.return_value = (None, None, None)

                    result = await agent.connect()

                    assert result is False
                    assert agent.websocket is None
                    assert agent.agent_id is None

    @pytest.mark.asyncio
    async def test_connection_without_config_update(self):
        """Should keep original config if no update provided."""
        with patch("agent.load_config") as mock_load:
            original_config = AgentConfig(metrics_interval=30)
            mock_load.return_value = original_config
            with patch("agent.setup_all_handlers"):
                agent = Agent()

                mock_ws = AsyncMock()

                with patch("agent.establish_connection") as mock_conn:
                    mock_conn.return_value = (mock_ws, "agent-456", None)

                    await agent.connect()

                    assert agent.config.metrics_interval == 30


class TestAgentRun:
    """Tests for Agent.run method."""

    @pytest.mark.asyncio
    async def test_run_connects_and_runs_loop(self):
        """Should connect and run message loop."""
        with patch("agent.load_config") as mock_load:
            mock_load.return_value = AgentConfig()
            with patch("agent.setup_all_handlers"):
                agent = Agent()

                mock_ws = AsyncMock()
                connect_count = 0

                async def mock_connect():
                    nonlocal connect_count
                    connect_count += 1
                    if connect_count == 1:
                        agent.websocket = mock_ws
                        agent.agent_id = "test"
                        return True
                    agent.running = False
                    return False

                agent.connect = mock_connect

                with patch(
                    "agent.run_message_loop", new_callable=AsyncMock
                ) as mock_loop:
                    with patch.object(
                        agent, "_start_collectors", new_callable=AsyncMock
                    ):
                        with patch.object(
                            agent, "_stop_collectors", new_callable=AsyncMock
                        ):
                            await agent.run()

                            mock_loop.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_exits_when_not_running(self):
        """Should exit loop when running is False."""
        with patch("agent.load_config") as mock_load:
            mock_load.return_value = AgentConfig()
            with patch("agent.setup_all_handlers"):
                agent = Agent()
                agent.running = False

                # Should exit immediately
                await agent.run()


class TestAgentCollectors:
    """Tests for Agent collector management."""

    @pytest.mark.asyncio
    async def test_start_collectors(self):
        """Should start metrics and health collectors."""
        with patch("agent.load_config") as mock_load:
            mock_load.return_value = AgentConfig()
            with patch("agent.setup_all_handlers"):
                agent = Agent()
                agent.websocket = AsyncMock()

                with patch("agent.MetricsCollector") as mock_metrics:
                    with patch("agent.HealthReporter") as mock_health:
                        mock_metrics_instance = MagicMock()
                        mock_metrics_instance.start = AsyncMock()
                        mock_metrics.return_value = mock_metrics_instance

                        mock_health_instance = MagicMock()
                        mock_health_instance.start = AsyncMock()
                        mock_health.return_value = mock_health_instance

                        await agent._start_collectors()

                        mock_metrics_instance.start.assert_called_once()
                        mock_health_instance.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_collectors(self):
        """Should stop collectors if running."""
        with patch("agent.load_config") as mock_load:
            mock_load.return_value = AgentConfig()
            with patch("agent.setup_all_handlers"):
                agent = Agent()

                mock_metrics = MagicMock()
                mock_metrics.stop = AsyncMock()
                mock_health = MagicMock()
                mock_health.stop = AsyncMock()

                agent._metrics_collector = mock_metrics
                agent._health_reporter = mock_health

                await agent._stop_collectors()

                mock_metrics.stop.assert_called_once()
                mock_health.stop.assert_called_once()
                assert agent._metrics_collector is None
                assert agent._health_reporter is None

    @pytest.mark.asyncio
    async def test_stop_collectors_when_none(self):
        """Should handle None collectors gracefully."""
        with patch("agent.load_config") as mock_load:
            mock_load.return_value = AgentConfig()
            with patch("agent.setup_all_handlers"):
                agent = Agent()

                # Should not raise
                await agent._stop_collectors()


class TestAgentShutdown:
    """Tests for Agent.shutdown method."""

    @pytest.mark.asyncio
    async def test_shutdown_stops_running(self):
        """Should set running to False."""
        with patch("agent.load_config") as mock_load:
            mock_load.return_value = AgentConfig()
            with patch("agent.setup_all_handlers"):
                agent = Agent()
                assert agent.running is True

                with patch("agent.close_websocket", new_callable=AsyncMock):
                    with patch.object(
                        agent, "_stop_collectors", new_callable=AsyncMock
                    ):
                        await agent.shutdown()

                        assert agent.running is False

    @pytest.mark.asyncio
    async def test_shutdown_stops_collectors(self):
        """Should stop collectors on shutdown."""
        with patch("agent.load_config") as mock_load:
            mock_load.return_value = AgentConfig()
            with patch("agent.setup_all_handlers"):
                agent = Agent()

                with patch("agent.close_websocket", new_callable=AsyncMock):
                    with patch.object(
                        agent, "_stop_collectors", new_callable=AsyncMock
                    ) as mock_stop:
                        await agent.shutdown()

                        mock_stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_shutdown_closes_websocket(self):
        """Should close websocket on shutdown."""
        with patch("agent.load_config") as mock_load:
            mock_load.return_value = AgentConfig()
            with patch("agent.setup_all_handlers"):
                agent = Agent()
                agent.websocket = AsyncMock()

                with patch(
                    "agent.close_websocket", new_callable=AsyncMock
                ) as mock_close:
                    with patch.object(
                        agent, "_stop_collectors", new_callable=AsyncMock
                    ):
                        await agent.shutdown()

                        mock_close.assert_called_once_with(agent.websocket)
