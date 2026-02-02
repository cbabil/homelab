"""Tests for connection module.

Tests WebSocket connection management, SSL context creation, and message handling.
"""

import asyncio
import json
import os
import ssl
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from connection import (
    create_ssl_context,
    establish_connection,
    run_message_loop,
    close_websocket,
    _handle_message,
)
from config import AgentConfig, AgentState
from rpc.handler import RPCHandler


class TestCreateSSLContext:
    """Tests for SSL context creation."""

    def test_development_mode_disables_verification(self):
        """Should disable certificate verification in dev mode."""
        with patch.dict(os.environ, {"TOMO_DEV": "1"}):
            ctx = create_ssl_context()

            assert ctx.check_hostname is False
            assert ctx.verify_mode == ssl.CERT_NONE

    def test_production_mode_enables_verification(self):
        """Should enable strict certificate verification in production."""
        import certifi

        _ = certifi.where()  # Verify certifi is available

        with patch.dict(os.environ, {}, clear=True):
            ctx = create_ssl_context()

            assert ctx.check_hostname is True
            assert ctx.verify_mode == ssl.CERT_REQUIRED
            assert ctx.minimum_version == ssl.TLSVersion.TLSv1_2


class TestEstablishConnection:
    """Tests for establish_connection function."""

    @pytest.mark.asyncio
    async def test_returns_none_when_no_server_url(self):
        """Should return None when no server URL is configured."""
        config = AgentConfig(server_url="")

        with patch("connection.load_state", return_value=None):
            ws, agent_id, updated_config = await establish_connection(config)

            assert ws is None
            assert agent_id is None
            assert updated_config is None

    @pytest.mark.asyncio
    async def test_uses_state_server_url(self):
        """Should use server URL from state if available."""
        config = AgentConfig(server_url="ws://config-server")
        state = AgentState(
            agent_id="test",
            token="token",
            server_url="ws://state-server",
            registered_at="2024-01-01T00:00:00Z",
        )

        with patch("connection.load_state", return_value=state):
            with patch(
                "connection.websockets.connect", new_callable=AsyncMock
            ) as mock_connect:
                mock_ws = AsyncMock()
                mock_connect.return_value = mock_ws

                with patch("connection.authenticate", return_value=(None, None)):
                    await establish_connection(config)

                    # Should use state URL, not config URL
                    mock_connect.assert_called_once()
                    call_args = mock_connect.call_args
                    assert call_args[0][0] == "ws://state-server"

    @pytest.mark.asyncio
    async def test_successful_connection(self):
        """Should return websocket and agent_id on success."""
        config = AgentConfig(server_url="ws://test-server")

        mock_ws = AsyncMock()
        updated_config = AgentConfig(metrics_interval=45)

        with patch("connection.load_state", return_value=None):
            with patch(
                "connection.websockets.connect", new_callable=AsyncMock
            ) as mock_connect:
                mock_connect.return_value = mock_ws
                with patch(
                    "connection.authenticate",
                    return_value=("agent-123", updated_config),
                ):
                    with patch("connection.update_config", return_value=updated_config):
                        ws, agent_id, cfg = await establish_connection(config)

                        assert ws == mock_ws
                        assert agent_id == "agent-123"
                        assert cfg == updated_config

    @pytest.mark.asyncio
    async def test_closes_websocket_on_auth_failure(self):
        """Should close websocket if authentication fails."""
        config = AgentConfig(server_url="ws://test-server")

        mock_ws = AsyncMock()

        with patch("connection.load_state", return_value=None):
            with patch(
                "connection.websockets.connect", new_callable=AsyncMock
            ) as mock_connect:
                mock_connect.return_value = mock_ws
                with patch("connection.authenticate", return_value=(None, None)):
                    ws, agent_id, cfg = await establish_connection(config)

                    assert ws is None
                    assert agent_id is None

    @pytest.mark.asyncio
    async def test_uses_ssl_for_wss_url(self):
        """Should use SSL context for wss:// URLs."""
        config = AgentConfig(server_url="wss://secure-server")

        with patch("connection.load_state", return_value=None):
            with patch(
                "connection.websockets.connect", new_callable=AsyncMock
            ) as mock_connect:
                mock_ws = AsyncMock()
                mock_connect.return_value = mock_ws
                with patch("connection.authenticate", return_value=(None, None)):
                    with patch("connection.create_ssl_context") as mock_ssl:
                        mock_ssl.return_value = MagicMock()
                        await establish_connection(config)

                        mock_ssl.assert_called_once()
                        assert mock_connect.call_args[1]["ssl"] is not None


class TestRunMessageLoop:
    """Tests for run_message_loop function."""

    @pytest.mark.asyncio
    async def test_processes_messages(self):
        """Should process incoming messages."""
        mock_ws = AsyncMock()
        mock_handler = MagicMock()
        mock_handler.handle = AsyncMock(return_value={"result": "ok"})

        # Simulate receiving one message then closing
        async def message_generator():
            yield json.dumps({"method": "test", "id": 1})
            raise StopAsyncIteration

        mock_ws.__aiter__ = lambda self: message_generator()

        with patch("connection._handle_message", new_callable=AsyncMock) as mock_handle:
            await run_message_loop(mock_ws, mock_handler)

            mock_handle.assert_called()


class TestHandleMessage:
    """Tests for _handle_message function."""

    @pytest.mark.asyncio
    async def test_handles_valid_json_request(self):
        """Should handle valid JSON-RPC request."""
        mock_ws = AsyncMock()
        handler = RPCHandler()

        def test_method():
            return {"status": "ok"}

        handler.register("test.method", test_method)

        message = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "test.method",
                "params": {},
                "id": 1,
            }
        )

        await _handle_message(message, mock_ws, handler)

        mock_ws.send.assert_called_once()
        sent_response = json.loads(mock_ws.send.call_args[0][0])
        assert sent_response["result"] == {"status": "ok"}

    @pytest.mark.asyncio
    async def test_handles_invalid_json(self):
        """Should handle invalid JSON gracefully."""
        mock_ws = AsyncMock()
        handler = RPCHandler()

        message = "not valid json {{"

        # Should not raise
        await _handle_message(message, mock_ws, handler)

        # Should not send response for invalid JSON
        mock_ws.send.assert_not_called()

    @pytest.mark.asyncio
    async def test_validates_message_freshness(self):
        """Should validate message freshness when timestamp/nonce present."""
        mock_ws = AsyncMock()
        handler = RPCHandler()

        message = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "test.method",
                "params": {},
                "id": 1,
                "timestamp": 1000,  # Very old timestamp
                "nonce": "test-nonce",
            }
        )

        with patch(
            "connection.validate_message_freshness",
            return_value=(False, "Message too old"),
        ):
            await _handle_message(message, mock_ws, handler)

            # Should send error response
            mock_ws.send.assert_called_once()
            sent_response = json.loads(mock_ws.send.call_args[0][0])
            assert "error" in sent_response
            assert sent_response["error"]["message"] == "Message too old"

    @pytest.mark.asyncio
    async def test_notification_no_response(self):
        """Should not send response for notification."""
        mock_ws = AsyncMock()
        handler = RPCHandler()

        def test_method():
            pass

        handler.register("notify.method", test_method)

        message = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "notify.method",
                "params": {},
                # No id - notification
            }
        )

        await _handle_message(message, mock_ws, handler)

        # Should not send response for notification
        mock_ws.send.assert_not_called()


class TestCloseWebsocket:
    """Tests for close_websocket function."""

    @pytest.mark.asyncio
    async def test_closes_websocket(self):
        """Should close the websocket."""
        mock_ws = AsyncMock()

        await close_websocket(mock_ws)

        mock_ws.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_handles_none_websocket(self):
        """Should handle None websocket gracefully."""
        # Should not raise
        await close_websocket(None)

    @pytest.mark.asyncio
    async def test_handles_timeout(self):
        """Should handle close timeout."""
        mock_ws = AsyncMock()

        async def slow_close():
            await asyncio.sleep(10)

        mock_ws.close = slow_close

        # Should not hang - timeout should apply
        # Note: We can't easily test the timeout in unit tests
        # but we verify it doesn't crash
        with patch("asyncio.wait_for", side_effect=asyncio.TimeoutError):
            await close_websocket(mock_ws)

    @pytest.mark.asyncio
    async def test_handles_close_error(self):
        """Should handle errors during close."""
        mock_ws = AsyncMock()
        mock_ws.close.side_effect = Exception("Close failed")

        # Should not raise
        await close_websocket(mock_ws)
