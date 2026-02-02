"""
Unit tests for services/agent_websocket.py

Tests for WebSocket handler for agent registration and authentication.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from starlette.websockets import WebSocketDisconnect

import services.agent_websocket as ws_module
from services.agent_websocket import AgentWebSocketHandler


@pytest.fixture
def mock_agent_service():
    """Create mock AgentService."""
    return AsyncMock()


@pytest.fixture
def mock_agent_manager():
    """Create mock AgentManager."""
    return AsyncMock()


@pytest.fixture
def handler(mock_agent_service, mock_agent_manager):
    """Create AgentWebSocketHandler with mocked dependencies."""
    return AgentWebSocketHandler(mock_agent_service, mock_agent_manager)


@pytest.fixture
def mock_websocket():
    """Create mock WebSocket."""
    ws = AsyncMock()
    ws.client = MagicMock()
    ws.client.host = "127.0.0.1"
    ws.client.port = 12345
    return ws


class TestAgentWebSocketHandlerInit:
    """Tests for handler initialization."""

    def test_init_stores_services(self, mock_agent_service, mock_agent_manager):
        """Should store service references."""
        handler = AgentWebSocketHandler(mock_agent_service, mock_agent_manager)

        assert handler._agent_service is mock_agent_service
        assert handler._agent_manager is mock_agent_manager


class TestHandleConnection:
    """Tests for handle_connection method."""

    @pytest.mark.asyncio
    async def test_handle_connection_accepts_websocket(
        self, handler, mock_websocket
    ):
        """Should accept the WebSocket connection."""
        mock_rate_limiter = MagicMock()
        mock_rate_limiter.is_allowed.return_value = False

        with (
            patch.object(ws_module, "get_client_info", return_value={"client_host": "127.0.0.1"}),
            patch.object(ws_module, "ws_rate_limiter", mock_rate_limiter),
            patch.object(ws_module, "send_error", new_callable=AsyncMock),
            patch.object(ws_module, "close_websocket", new_callable=AsyncMock),
        ):
            await handler.handle_connection(mock_websocket)

            mock_websocket.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_connection_rejects_rate_limited(
        self, handler, mock_websocket
    ):
        """Should reject rate-limited connections."""
        mock_rate_limiter = MagicMock()
        mock_rate_limiter.is_allowed.return_value = False

        with (
            patch.object(ws_module, "get_client_info", return_value={"client_host": "127.0.0.1"}),
            patch.object(ws_module, "ws_rate_limiter", mock_rate_limiter),
            patch.object(ws_module, "send_error", new_callable=AsyncMock) as mock_send_error,
            patch.object(ws_module, "close_websocket", new_callable=AsyncMock) as mock_close,
        ):
            await handler.handle_connection(mock_websocket)

            mock_send_error.assert_called_once()
            mock_close.assert_called_once_with(mock_websocket, ws_module.WS_CLOSE_AUTH_FAILED)

    @pytest.mark.asyncio
    async def test_handle_connection_auth_failure_records_rate_limit(
        self, handler, mock_websocket, mock_agent_manager
    ):
        """Should record rate limit failure on auth failure."""
        mock_rate_limiter = MagicMock()
        mock_rate_limiter.is_allowed.return_value = True

        with (
            patch.object(ws_module, "get_client_info", return_value={"client_host": "127.0.0.1"}),
            patch.object(ws_module, "ws_rate_limiter", mock_rate_limiter),
            patch.object(handler, "_authenticate_connection", new_callable=AsyncMock, return_value=None),
            patch.object(ws_module, "close_websocket", new_callable=AsyncMock),
        ):
            await handler.handle_connection(mock_websocket)

            mock_rate_limiter.record_failure.assert_called_once_with("127.0.0.1")

    @pytest.mark.asyncio
    async def test_handle_connection_auth_success_records_success(
        self, handler, mock_websocket, mock_agent_manager
    ):
        """Should record rate limit success and register connection."""
        mock_rate_limiter = MagicMock()
        mock_rate_limiter.is_allowed.return_value = True

        with (
            patch.object(ws_module, "get_client_info", return_value={"client_host": "127.0.0.1"}),
            patch.object(ws_module, "ws_rate_limiter", mock_rate_limiter),
            patch.object(
                handler, "_authenticate_connection",
                new_callable=AsyncMock, return_value=("agent-1", "server-1")
            ),
            patch.object(ws_module, "message_loop", new_callable=AsyncMock),
            patch.object(ws_module, "close_websocket", new_callable=AsyncMock),
            patch.object(ws_module, "log_event", new_callable=AsyncMock),
        ):
            await handler.handle_connection(mock_websocket)

            mock_rate_limiter.record_success.assert_called_once_with("127.0.0.1")
            mock_agent_manager.register_connection.assert_called_once_with(
                "agent-1", mock_websocket, "server-1"
            )

    @pytest.mark.asyncio
    async def test_handle_connection_calls_message_loop(
        self, handler, mock_websocket, mock_agent_manager
    ):
        """Should call message_loop after successful auth."""
        mock_rate_limiter = MagicMock()
        mock_rate_limiter.is_allowed.return_value = True

        with (
            patch.object(ws_module, "get_client_info", return_value={"client_host": "127.0.0.1"}),
            patch.object(ws_module, "ws_rate_limiter", mock_rate_limiter),
            patch.object(
                handler, "_authenticate_connection",
                new_callable=AsyncMock, return_value=("agent-1", "server-1")
            ),
            patch.object(ws_module, "message_loop", new_callable=AsyncMock) as mock_loop,
            patch.object(ws_module, "close_websocket", new_callable=AsyncMock),
            patch.object(ws_module, "log_event", new_callable=AsyncMock),
        ):
            await handler.handle_connection(mock_websocket)

            mock_loop.assert_called_once_with(mock_websocket, "agent-1", mock_agent_manager)

    @pytest.mark.asyncio
    async def test_handle_connection_handles_disconnect(
        self, handler, mock_websocket, mock_agent_manager
    ):
        """Should handle WebSocketDisconnect gracefully."""
        mock_rate_limiter = MagicMock()
        mock_rate_limiter.is_allowed.return_value = True

        with (
            patch.object(ws_module, "get_client_info", return_value={"client_host": "127.0.0.1"}),
            patch.object(ws_module, "ws_rate_limiter", mock_rate_limiter),
            patch.object(
                handler, "_authenticate_connection",
                new_callable=AsyncMock, return_value=("agent-1", "server-1")
            ),
            patch.object(
                ws_module, "message_loop",
                new_callable=AsyncMock, side_effect=WebSocketDisconnect()
            ),
            patch.object(ws_module, "close_websocket", new_callable=AsyncMock),
            patch.object(ws_module, "log_event", new_callable=AsyncMock),
        ):
            # Should not raise
            await handler.handle_connection(mock_websocket)

    @pytest.mark.asyncio
    async def test_handle_connection_handles_exception(
        self, handler, mock_websocket, mock_agent_manager
    ):
        """Should handle exceptions gracefully."""
        mock_rate_limiter = MagicMock()
        mock_rate_limiter.is_allowed.return_value = True

        with (
            patch.object(ws_module, "get_client_info", return_value={"client_host": "127.0.0.1"}),
            patch.object(ws_module, "ws_rate_limiter", mock_rate_limiter),
            patch.object(
                handler, "_authenticate_connection",
                new_callable=AsyncMock, return_value=("agent-1", "server-1")
            ),
            patch.object(
                ws_module, "message_loop",
                new_callable=AsyncMock, side_effect=RuntimeError("Test error")
            ),
            patch.object(ws_module, "close_websocket", new_callable=AsyncMock),
            patch.object(ws_module, "log_event", new_callable=AsyncMock),
        ):
            # Should not raise
            await handler.handle_connection(mock_websocket)

    @pytest.mark.asyncio
    async def test_handle_connection_unregisters_on_exit(
        self, handler, mock_websocket, mock_agent_manager
    ):
        """Should unregister connection in finally block."""
        mock_rate_limiter = MagicMock()
        mock_rate_limiter.is_allowed.return_value = True

        with (
            patch.object(ws_module, "get_client_info", return_value={"client_host": "127.0.0.1"}),
            patch.object(ws_module, "ws_rate_limiter", mock_rate_limiter),
            patch.object(
                handler, "_authenticate_connection",
                new_callable=AsyncMock, return_value=("agent-1", "server-1")
            ),
            patch.object(ws_module, "message_loop", new_callable=AsyncMock),
            patch.object(ws_module, "close_websocket", new_callable=AsyncMock),
            patch.object(ws_module, "log_event", new_callable=AsyncMock),
        ):
            await handler.handle_connection(mock_websocket)

            mock_agent_manager.unregister_connection.assert_called_once_with("agent-1")


class TestAuthenticateConnection:
    """Tests for _authenticate_connection method."""

    @pytest.mark.asyncio
    async def test_authenticate_timeout(self, handler, mock_websocket):
        """Should return None on timeout."""
        mock_websocket.receive_json.side_effect = asyncio.TimeoutError()

        with (
            patch.object(ws_module, "send_error", new_callable=AsyncMock),
            patch.object(ws_module, "close_websocket", new_callable=AsyncMock),
        ):
            result = await handler._authenticate_connection(mock_websocket)

            assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_receive_error(self, handler, mock_websocket):
        """Should return None on receive error."""
        mock_websocket.receive_json.side_effect = RuntimeError("Connection error")

        with (
            patch.object(ws_module, "send_error", new_callable=AsyncMock),
            patch.object(ws_module, "close_websocket", new_callable=AsyncMock),
        ):
            result = await handler._authenticate_connection(mock_websocket)

            assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_register_message(self, handler, mock_websocket):
        """Should handle register message type."""
        mock_websocket.receive_json.return_value = {"type": "register", "code": "abc123"}

        with patch.object(
            handler, "_handle_registration",
            new_callable=AsyncMock, return_value=("agent-1", "server-1")
        ) as mock_register:
            result = await handler._authenticate_connection(mock_websocket)

            mock_register.assert_called_once()
            assert result == ("agent-1", "server-1")

    @pytest.mark.asyncio
    async def test_authenticate_authenticate_message(self, handler, mock_websocket):
        """Should handle authenticate message type."""
        mock_websocket.receive_json.return_value = {"type": "authenticate", "token": "token123"}

        with patch.object(
            handler, "_handle_authentication",
            new_callable=AsyncMock, return_value=("agent-1", "server-1")
        ) as mock_auth:
            result = await handler._authenticate_connection(mock_websocket)

            mock_auth.assert_called_once()
            assert result == ("agent-1", "server-1")

    @pytest.mark.asyncio
    async def test_authenticate_unknown_message_type(self, handler, mock_websocket):
        """Should return None on unknown message type."""
        mock_websocket.receive_json.return_value = {"type": "unknown"}

        with patch.object(
            handler, "_close_with_error", new_callable=AsyncMock
        ) as mock_close:
            result = await handler._authenticate_connection(mock_websocket)

            assert result is None
            mock_close.assert_called_once()


class TestHandleRegistration:
    """Tests for _handle_registration method."""

    @pytest.mark.asyncio
    async def test_registration_without_code(
        self, handler, mock_websocket, mock_agent_service
    ):
        """Should reject registration without code."""
        with patch.object(
            handler, "_close_with_error", new_callable=AsyncMock
        ) as mock_close:
            result = await handler._handle_registration(mock_websocket, {})

            assert result is None
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_registration_service_failure(
        self, handler, mock_websocket, mock_agent_service
    ):
        """Should handle service registration failure."""
        mock_agent_service.register_agent.return_value = None

        with patch.object(
            handler, "_close_with_error", new_callable=AsyncMock
        ) as mock_close:
            result = await handler._handle_registration(
                mock_websocket, {"code": "abc123", "version": "1.0.0"}
            )

            assert result is None
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_registration_success(
        self, handler, mock_websocket, mock_agent_service
    ):
        """Should return agent_id and server_id on success."""
        mock_agent_service.register_agent.return_value = (
            "agent-1", "token123", {"config": "data"}, "server-1"
        )

        with patch.object(ws_module, "send_registered", new_callable=AsyncMock) as mock_send:
            result = await handler._handle_registration(
                mock_websocket, {"code": "abc123", "version": "1.0.0"}
            )

            assert result == ("agent-1", "server-1")
            mock_send.assert_called_once_with(
                mock_websocket, "agent-1", "token123", {"config": "data"}
            )


class TestHandleAuthentication:
    """Tests for _handle_authentication method."""

    @pytest.mark.asyncio
    async def test_authentication_without_token(
        self, handler, mock_websocket, mock_agent_service
    ):
        """Should reject authentication without token."""
        with patch.object(
            handler, "_close_with_error", new_callable=AsyncMock
        ) as mock_close:
            result = await handler._handle_authentication(mock_websocket, {})

            assert result is None
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_authentication_service_failure(
        self, handler, mock_websocket, mock_agent_service
    ):
        """Should handle service authentication failure."""
        mock_agent_service.authenticate_agent.return_value = None

        with patch.object(
            handler, "_close_with_error", new_callable=AsyncMock
        ) as mock_close:
            result = await handler._handle_authentication(
                mock_websocket, {"token": "token123", "version": "1.0.0"}
            )

            assert result is None
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_authentication_success(
        self, handler, mock_websocket, mock_agent_service
    ):
        """Should return agent_id and server_id on success."""
        mock_agent_service.authenticate_agent.return_value = (
            "agent-1", {"config": "data"}, "server-1"
        )

        with (
            patch.object(ws_module, "send_authenticated", new_callable=AsyncMock) as mock_send,
            patch.object(ws_module, "log_event", new_callable=AsyncMock),
        ):
            result = await handler._handle_authentication(
                mock_websocket, {"token": "token123", "version": "1.0.0"}
            )

            assert result == ("agent-1", "server-1")
            mock_send.assert_called_once_with(
                mock_websocket, "agent-1", {"config": "data"}
            )


class TestCloseWithError:
    """Tests for _close_with_error method."""

    @pytest.mark.asyncio
    async def test_close_with_error_sends_and_closes(self, handler, mock_websocket):
        """Should send error and close connection."""
        with (
            patch.object(ws_module, "send_error", new_callable=AsyncMock) as mock_send,
            patch.object(ws_module, "close_websocket", new_callable=AsyncMock) as mock_close,
        ):
            await handler._close_with_error(mock_websocket, "Test error")

            mock_send.assert_called_once_with(mock_websocket, "Test error")
            mock_close.assert_called_once_with(
                mock_websocket, ws_module.WS_CLOSE_AUTH_FAILED
            )
