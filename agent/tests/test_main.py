"""Tests for main entry point.

Tests the main() function and entry point behavior.
"""

import signal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from main import main


class TestMain:
    """Tests for main entry point."""

    @pytest.mark.asyncio
    async def test_creates_agent(self):
        """Should create Agent instance."""
        mock_agent = MagicMock()
        mock_agent.run = AsyncMock()
        mock_agent.shutdown = AsyncMock()

        with patch("main.Agent", return_value=mock_agent):
            with patch("asyncio.get_event_loop") as mock_loop:
                mock_loop.return_value = MagicMock()
                await main()

        mock_agent.run.assert_called_once()

    @pytest.mark.asyncio
    async def test_runs_agent(self):
        """Should run the agent."""
        mock_agent = MagicMock()
        mock_agent.run = AsyncMock()
        mock_agent.shutdown = AsyncMock()

        with patch("main.Agent", return_value=mock_agent):
            with patch("asyncio.get_event_loop") as mock_loop:
                mock_loop.return_value = MagicMock()
                await main()

        mock_agent.run.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_sets_up_signal_handlers(self):
        """Should set up signal handlers for SIGTERM and SIGINT."""
        mock_agent = MagicMock()
        mock_agent.run = AsyncMock()
        mock_agent.shutdown = AsyncMock()
        mock_loop = MagicMock()

        with patch("main.Agent", return_value=mock_agent):
            with patch("asyncio.get_event_loop", return_value=mock_loop):
                await main()

        # Should have called add_signal_handler twice (SIGTERM and SIGINT)
        assert mock_loop.add_signal_handler.call_count == 2

        # Check that both signals are handled
        signal_calls = mock_loop.add_signal_handler.call_args_list
        signals_handled = [call[0][0] for call in signal_calls]
        assert signal.SIGTERM in signals_handled
        assert signal.SIGINT in signals_handled

    @pytest.mark.asyncio
    async def test_logs_startup(self):
        """Should log startup message."""
        mock_agent = MagicMock()
        mock_agent.run = AsyncMock()
        mock_agent.shutdown = AsyncMock()

        with patch("main.Agent", return_value=mock_agent):
            with patch("asyncio.get_event_loop") as mock_loop:
                mock_loop.return_value = MagicMock()
                with patch("main.logger") as mock_logger:
                    await main()

                    # Should log both startup and stop
                    assert mock_logger.info.call_count >= 2

    @pytest.mark.asyncio
    async def test_logs_shutdown(self):
        """Should log shutdown message."""
        mock_agent = MagicMock()
        mock_agent.run = AsyncMock()
        mock_agent.shutdown = AsyncMock()

        with patch("main.Agent", return_value=mock_agent):
            with patch("asyncio.get_event_loop") as mock_loop:
                mock_loop.return_value = MagicMock()
                with patch("main.logger") as mock_logger:
                    await main()

                    # Check that "stopped" was logged
                    log_messages = [
                        str(call) for call in mock_logger.info.call_args_list
                    ]
                    assert any("stopped" in msg.lower() for msg in log_messages)
