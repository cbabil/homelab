"""Tests for collectors (health and metrics).

Tests health reporting and metrics collection.
"""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from collectors.health import HealthReporter
from collectors.metrics import MetricsCollector


def create_mock_callbacks(interval=1, websocket=None):
    """Create mock callbacks for collectors."""
    return {
        "get_interval": lambda: interval,
        "get_websocket": lambda: websocket,
    }


class TestHealthReporterInit:
    """Tests for HealthReporter initialization."""

    def test_initializes_with_callbacks(self):
        """Should initialize with callback functions."""
        callbacks = create_mock_callbacks()
        reporter = HealthReporter(**callbacks)

        assert reporter._get_interval() == 1
        assert reporter._get_websocket() is None
        assert reporter._task is None


class TestHealthReporterStart:
    """Tests for HealthReporter.start()."""

    @pytest.mark.asyncio
    async def test_start_creates_task(self):
        """Should create background task on start."""
        callbacks = create_mock_callbacks()
        reporter = HealthReporter(**callbacks)

        await reporter.start()

        assert reporter._task is not None
        assert not reporter._task.done()

        # Cleanup
        await reporter.stop()

    @pytest.mark.asyncio
    async def test_start_logs_message(self):
        """Should log start message."""
        callbacks = create_mock_callbacks()
        reporter = HealthReporter(**callbacks)

        with patch("collectors.health.logger") as mock_logger:
            await reporter.start()
            mock_logger.info.assert_called_with("Health reporter started")

        await reporter.stop()


class TestHealthReporterStop:
    """Tests for HealthReporter.stop()."""

    @pytest.mark.asyncio
    async def test_stop_cancels_task(self):
        """Should cancel task on stop."""
        callbacks = create_mock_callbacks()
        reporter = HealthReporter(**callbacks)

        await reporter.start()
        task = reporter._task

        await reporter.stop()

        assert task.cancelled() or task.done()

    @pytest.mark.asyncio
    async def test_stop_without_task(self):
        """Should handle stop when no task exists."""
        callbacks = create_mock_callbacks()
        reporter = HealthReporter(**callbacks)

        # Should not raise
        await reporter.stop()

    @pytest.mark.asyncio
    async def test_stop_logs_message(self):
        """Should log stop message."""
        callbacks = create_mock_callbacks()
        reporter = HealthReporter(**callbacks)

        with patch("collectors.health.logger") as mock_logger:
            await reporter.stop()
            mock_logger.info.assert_called_with("Health reporter stopped")


class TestHealthReporterLoop:
    """Tests for HealthReporter._report_loop()."""

    @pytest.mark.asyncio
    async def test_skips_when_no_websocket(self):
        """Should skip reporting when websocket is None."""
        callbacks = create_mock_callbacks(websocket=None)
        reporter = HealthReporter(**callbacks)

        await reporter.start()
        await asyncio.sleep(0.05)
        await reporter.stop()

        # No websocket send should have been called

    @pytest.mark.asyncio
    async def test_sends_health_notification(self):
        """Should send health notification when websocket exists."""
        mock_websocket = AsyncMock()
        callbacks = create_mock_callbacks(websocket=mock_websocket)

        reporter = HealthReporter(**callbacks)

        # Mock asyncio.sleep to return immediately after first call
        call_count = 0
        original_sleep = asyncio.sleep

        async def quick_sleep(interval):
            nonlocal call_count
            call_count += 1
            if call_count > 1:
                raise asyncio.CancelledError()
            await original_sleep(0)

        with patch.object(asyncio, "sleep", side_effect=quick_sleep):
            try:
                await reporter._report_loop()
            except asyncio.CancelledError:
                pass

        # Verify send was called
        assert mock_websocket.send.called

        # Verify message format
        call_args = mock_websocket.send.call_args[0][0]
        message = json.loads(call_args)
        assert message["jsonrpc"] == "2.0"
        assert message["method"] == "health.status"
        assert "status" in message["params"]
        assert "uptime" in message["params"]
        assert "version" in message["params"]

    @pytest.mark.asyncio
    async def test_handles_send_error(self):
        """Should handle errors during send."""
        mock_websocket = AsyncMock()
        mock_websocket.send.side_effect = Exception("Connection lost")
        callbacks = create_mock_callbacks(websocket=mock_websocket)

        reporter = HealthReporter(**callbacks)

        call_count = 0
        original_sleep = asyncio.sleep

        async def quick_sleep(interval):
            nonlocal call_count
            call_count += 1
            if call_count > 1:
                raise asyncio.CancelledError()
            await original_sleep(0)

        with patch("collectors.health.logger") as mock_logger:
            with patch.object(asyncio, "sleep", side_effect=quick_sleep):
                try:
                    await reporter._report_loop()
                except asyncio.CancelledError:
                    pass

            # Should log error but not crash
            assert mock_logger.error.called


class TestMetricsCollectorInit:
    """Tests for MetricsCollector initialization."""

    def test_initializes_with_callbacks(self):
        """Should initialize with callback functions."""
        callbacks = create_mock_callbacks()
        collector = MetricsCollector(**callbacks)

        assert collector._get_interval() == 1
        assert collector._get_websocket() is None
        assert collector._task is None


class TestMetricsCollectorStart:
    """Tests for MetricsCollector.start()."""

    @pytest.mark.asyncio
    async def test_start_creates_task(self):
        """Should create background task on start."""
        callbacks = create_mock_callbacks()
        collector = MetricsCollector(**callbacks)

        with patch("rpc.methods.system.SystemMethods"):
            await collector.start()

            assert collector._task is not None
            assert not collector._task.done()

            await collector.stop()

    @pytest.mark.asyncio
    async def test_start_logs_message(self):
        """Should log start message."""
        callbacks = create_mock_callbacks()
        collector = MetricsCollector(**callbacks)

        with patch("collectors.metrics.logger") as mock_logger:
            with patch("rpc.methods.system.SystemMethods"):
                await collector.start()
                mock_logger.info.assert_called_with("Metrics collector started")
                await collector.stop()


class TestMetricsCollectorStop:
    """Tests for MetricsCollector.stop()."""

    @pytest.mark.asyncio
    async def test_stop_cancels_task(self):
        """Should cancel task on stop."""
        callbacks = create_mock_callbacks()
        collector = MetricsCollector(**callbacks)

        with patch("rpc.methods.system.SystemMethods"):
            await collector.start()
            task = collector._task

            await collector.stop()

            assert task.cancelled() or task.done()

    @pytest.mark.asyncio
    async def test_stop_without_task(self):
        """Should handle stop when no task exists."""
        callbacks = create_mock_callbacks()
        collector = MetricsCollector(**callbacks)

        await collector.stop()

    @pytest.mark.asyncio
    async def test_stop_logs_message(self):
        """Should log stop message."""
        callbacks = create_mock_callbacks()
        collector = MetricsCollector(**callbacks)

        with patch("collectors.metrics.logger") as mock_logger:
            await collector.stop()
            mock_logger.info.assert_called_with("Metrics collector stopped")


class TestMetricsCollectorLoop:
    """Tests for MetricsCollector._collection_loop()."""

    @pytest.mark.asyncio
    async def test_skips_when_no_websocket(self):
        """Should skip collection when websocket is None."""
        callbacks = create_mock_callbacks(websocket=None)
        collector = MetricsCollector(**callbacks)

        with patch("rpc.methods.system.SystemMethods"):
            await collector.start()
            await asyncio.sleep(0.05)
            await collector.stop()

    @pytest.mark.asyncio
    async def test_sends_metrics_notification(self):
        """Should send metrics notification when websocket exists."""
        mock_websocket = AsyncMock()

        mock_system = MagicMock()
        mock_system.get_metrics.return_value = {
            "cpu": 25.5,
            "memory": {"used": 1024, "total": 4096},
        }

        callbacks = create_mock_callbacks(websocket=mock_websocket)
        collector = MetricsCollector(**callbacks)

        call_count = 0
        original_sleep = asyncio.sleep

        async def quick_sleep(interval):
            nonlocal call_count
            call_count += 1
            if call_count > 1:
                raise asyncio.CancelledError()
            await original_sleep(0)

        with patch("rpc.methods.system.SystemMethods", return_value=mock_system):
            with patch.object(asyncio, "sleep", side_effect=quick_sleep):
                try:
                    await collector._collection_loop()
                except asyncio.CancelledError:
                    pass

        assert mock_websocket.send.called

        call_args = mock_websocket.send.call_args[0][0]
        message = json.loads(call_args)
        assert message["jsonrpc"] == "2.0"
        assert message["method"] == "metrics.update"
        assert message["params"]["cpu"] == 25.5

    @pytest.mark.asyncio
    async def test_handles_collection_error(self):
        """Should handle errors during collection."""
        mock_websocket = AsyncMock()

        mock_system = MagicMock()
        mock_system.get_metrics.side_effect = Exception("Docker unavailable")

        callbacks = create_mock_callbacks(websocket=mock_websocket)
        collector = MetricsCollector(**callbacks)

        call_count = 0
        original_sleep = asyncio.sleep

        async def quick_sleep(interval):
            nonlocal call_count
            call_count += 1
            if call_count > 1:
                raise asyncio.CancelledError()
            await original_sleep(0)

        with patch("rpc.methods.system.SystemMethods", return_value=mock_system):
            with patch("collectors.metrics.logger") as mock_logger:
                with patch.object(asyncio, "sleep", side_effect=quick_sleep):
                    try:
                        await collector._collection_loop()
                    except asyncio.CancelledError:
                        pass

                assert mock_logger.error.called
