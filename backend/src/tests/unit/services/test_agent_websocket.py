"""
Unit tests for services/agent_websocket.py

Tests WebSocket handler for agent registration and authentication.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from starlette.websockets import WebSocketDisconnect

from services.agent_websocket import (
    WS_AUTH_TIMEOUT_SECONDS,
    WS_CLOSE_AUTH_FAILED,
    WS_CLOSE_NORMAL,
    AgentWebSocketHandler,
)


@pytest.fixture
def mock_agent_service():
    """Create mock agent service."""
    return MagicMock()


@pytest.fixture
def mock_agent_manager():
    """Create mock agent manager."""
    manager = MagicMock()
    manager.register_connection = AsyncMock()
    manager.unregister_connection = AsyncMock()
    return manager


@pytest.fixture
def mock_websocket():
    """Create mock WebSocket."""
    ws = AsyncMock()
    ws.accept = AsyncMock()
    ws.receive_json = AsyncMock()
    ws.send_json = AsyncMock()
    ws.close = AsyncMock()
    ws.client = MagicMock(host="127.0.0.1", port=12345)
    return ws


@pytest.fixture
def handler(mock_agent_service, mock_agent_manager):
    """Create AgentWebSocketHandler instance."""
    return AgentWebSocketHandler(mock_agent_service, mock_agent_manager)


class TestAgentWebSocketHandlerInit:
    """Tests for AgentWebSocketHandler initialization."""

    def test_init_stores_agent_service(self, mock_agent_service, mock_agent_manager):
        """Handler should store agent service reference."""
        handler = AgentWebSocketHandler(mock_agent_service, mock_agent_manager)
        assert handler._agent_service is mock_agent_service

    def test_init_stores_agent_manager(self, mock_agent_service, mock_agent_manager):
        """Handler should store agent manager reference."""
        handler = AgentWebSocketHandler(mock_agent_service, mock_agent_manager)
        assert handler._agent_manager is mock_agent_manager


class TestConstants:
    """Tests for module constants."""

    def test_ws_close_auth_failed_value(self):
        """WS_CLOSE_AUTH_FAILED should be 4001."""
        assert WS_CLOSE_AUTH_FAILED == 4001

    def test_ws_close_normal_value(self):
        """WS_CLOSE_NORMAL should be 1000."""
        assert WS_CLOSE_NORMAL == 1000

    def test_ws_auth_timeout_seconds(self):
        """WS_AUTH_TIMEOUT_SECONDS should be 30."""
        assert WS_AUTH_TIMEOUT_SECONDS == 30.0


class TestHandleConnection:
    """Tests for handle_connection method."""

    @pytest.mark.asyncio
    async def test_handle_connection_accepts_websocket(
        self, handler, mock_websocket, mock_agent_service, mock_agent_manager
    ):
        """handle_connection should accept the WebSocket."""
        mock_websocket.receive_json.side_effect = WebSocketDisconnect()

        with (
            patch("services.agent_websocket.get_client_info", return_value={}),
            patch("services.agent_websocket.ws_rate_limiter") as mock_limiter,
            patch("services.agent_websocket.close_websocket", new_callable=AsyncMock),
            patch("services.agent_websocket.logger"),
        ):
            mock_limiter.is_allowed.return_value = True
            await handler.handle_connection(mock_websocket)

        mock_websocket.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_connection_rate_limited(self, handler, mock_websocket):
        """handle_connection should reject rate-limited connections."""
        with (
            patch(
                "services.agent_websocket.get_client_info",
                return_value={"client_host": "1.2.3.4"},
            ),
            patch("services.agent_websocket.ws_rate_limiter") as mock_limiter,
            patch(
                "services.agent_websocket.send_error", new_callable=AsyncMock
            ) as mock_send_error,
            patch(
                "services.agent_websocket.close_websocket", new_callable=AsyncMock
            ) as mock_close,
            patch("services.agent_websocket.logger"),
        ):
            mock_limiter.is_allowed.return_value = False

            await handler.handle_connection(mock_websocket)

            mock_send_error.assert_called_once()
            mock_close.assert_called_once_with(mock_websocket, WS_CLOSE_AUTH_FAILED)

    @pytest.mark.asyncio
    async def test_handle_connection_auth_failed(
        self, handler, mock_websocket, mock_agent_manager
    ):
        """handle_connection should record failure on auth failure."""
        with (
            patch(
                "services.agent_websocket.get_client_info",
                return_value={"client_host": "1.2.3.4"},
            ),
            patch("services.agent_websocket.ws_rate_limiter") as mock_limiter,
            patch("services.agent_websocket.close_websocket", new_callable=AsyncMock),
            patch("services.agent_websocket.send_error", new_callable=AsyncMock),
            patch("services.agent_websocket.logger"),
        ):
            mock_limiter.is_allowed.return_value = True
            mock_websocket.receive_json.side_effect = TimeoutError()

            await handler.handle_connection(mock_websocket)

            mock_limiter.record_failure.assert_called_once_with("1.2.3.4")
            mock_agent_manager.register_connection.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_connection_auth_success(
        self, handler, mock_websocket, mock_agent_service, mock_agent_manager
    ):
        """handle_connection should register connection on auth success."""
        mock_websocket.receive_json.return_value = {
            "type": "authenticate",
            "token": "test-token",
        }
        mock_agent_service.authenticate_agent = AsyncMock(
            return_value=("agent-123", {"config": "data"}, "server-456")
        )

        with (
            patch(
                "services.agent_websocket.get_client_info",
                return_value={"client_host": "1.2.3.4"},
            ),
            patch("services.agent_websocket.ws_rate_limiter") as mock_limiter,
            patch("services.agent_websocket.close_websocket", new_callable=AsyncMock),
            patch(
                "services.agent_websocket.send_authenticated", new_callable=AsyncMock
            ),
            patch("services.agent_websocket.message_loop", new_callable=AsyncMock),
            patch("services.agent_websocket.log_event", new_callable=AsyncMock),
            patch("services.agent_websocket.logger"),
        ):
            mock_limiter.is_allowed.return_value = True

            await handler.handle_connection(mock_websocket)

            mock_limiter.record_success.assert_called_once_with("1.2.3.4")
            mock_agent_manager.register_connection.assert_called_once_with(
                "agent-123", mock_websocket, "server-456"
            )

    @pytest.mark.asyncio
    async def test_handle_connection_websocket_disconnect(
        self, handler, mock_websocket, mock_agent_service, mock_agent_manager
    ):
        """handle_connection should handle WebSocketDisconnect."""
        mock_websocket.receive_json.return_value = {
            "type": "authenticate",
            "token": "test-token",
        }
        mock_agent_service.authenticate_agent = AsyncMock(
            return_value=("agent-123", {}, "server-456")
        )

        with (
            patch("services.agent_websocket.get_client_info", return_value={}),
            patch("services.agent_websocket.ws_rate_limiter") as mock_limiter,
            patch("services.agent_websocket.close_websocket", new_callable=AsyncMock),
            patch(
                "services.agent_websocket.send_authenticated", new_callable=AsyncMock
            ),
            patch(
                "services.agent_websocket.message_loop", new_callable=AsyncMock
            ) as mock_loop,
            patch("services.agent_websocket.log_event", new_callable=AsyncMock),
            patch("services.agent_websocket.logger"),
        ):
            mock_limiter.is_allowed.return_value = True
            mock_loop.side_effect = WebSocketDisconnect()

            await handler.handle_connection(mock_websocket)

            mock_agent_manager.unregister_connection.assert_called_once_with(
                "agent-123"
            )

    @pytest.mark.asyncio
    async def test_handle_connection_unregisters_on_error(
        self, handler, mock_websocket, mock_agent_service, mock_agent_manager
    ):
        """handle_connection should unregister connection on error."""
        mock_websocket.receive_json.return_value = {
            "type": "authenticate",
            "token": "test-token",
        }
        mock_agent_service.authenticate_agent = AsyncMock(
            return_value=("agent-123", {}, "server-456")
        )

        with (
            patch("services.agent_websocket.get_client_info", return_value={}),
            patch("services.agent_websocket.ws_rate_limiter") as mock_limiter,
            patch("services.agent_websocket.close_websocket", new_callable=AsyncMock),
            patch(
                "services.agent_websocket.send_authenticated", new_callable=AsyncMock
            ),
            patch(
                "services.agent_websocket.message_loop", new_callable=AsyncMock
            ) as mock_loop,
            patch("services.agent_websocket.log_event", new_callable=AsyncMock),
            patch("services.agent_websocket.logger"),
        ):
            mock_limiter.is_allowed.return_value = True
            mock_loop.side_effect = Exception("Connection error")

            await handler.handle_connection(mock_websocket)

            mock_agent_manager.unregister_connection.assert_called_once_with(
                "agent-123"
            )


class TestAuthenticateConnection:
    """Tests for _authenticate_connection method."""

    @pytest.mark.asyncio
    async def test_authenticate_timeout(self, handler, mock_websocket):
        """_authenticate_connection should handle timeout."""
        mock_websocket.receive_json.side_effect = TimeoutError()

        with (
            patch(
                "services.agent_websocket.send_error", new_callable=AsyncMock
            ) as mock_error,
            patch(
                "services.agent_websocket.close_websocket", new_callable=AsyncMock
            ) as mock_close,
            patch("services.agent_websocket.logger"),
        ):
            result = await handler._authenticate_connection(mock_websocket)

            assert result is None
            mock_error.assert_called_once()
            mock_close.assert_called_once_with(mock_websocket, WS_CLOSE_AUTH_FAILED)

    @pytest.mark.asyncio
    async def test_authenticate_invalid_message(self, handler, mock_websocket):
        """_authenticate_connection should handle invalid message."""
        mock_websocket.receive_json.side_effect = ValueError("Invalid JSON")

        with (
            patch(
                "services.agent_websocket.send_error", new_callable=AsyncMock
            ) as mock_error,
            patch("services.agent_websocket.close_websocket", new_callable=AsyncMock),
            patch("services.agent_websocket.logger"),
        ):
            result = await handler._authenticate_connection(mock_websocket)

            assert result is None
            mock_error.assert_called_once()

    @pytest.mark.asyncio
    async def test_authenticate_unknown_type(self, handler, mock_websocket):
        """_authenticate_connection should reject unknown message type."""
        mock_websocket.receive_json.return_value = {"type": "unknown"}

        with (
            patch("services.agent_websocket.send_error", new_callable=AsyncMock),
            patch("services.agent_websocket.close_websocket", new_callable=AsyncMock),
            patch("services.agent_websocket.logger"),
        ):
            result = await handler._authenticate_connection(mock_websocket)

            assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_register_type(
        self, handler, mock_websocket, mock_agent_service
    ):
        """_authenticate_connection should handle register type."""
        mock_websocket.receive_json.return_value = {
            "type": "register",
            "code": "reg-code-123",
            "version": "1.0.0",
        }
        mock_agent_service.register_agent = AsyncMock(
            return_value=("agent-1", "token-1", {}, "server-1")
        )

        with (
            patch("services.agent_websocket.send_registered", new_callable=AsyncMock),
            patch("services.agent_websocket.logger"),
        ):
            result = await handler._authenticate_connection(mock_websocket)

            assert result == ("agent-1", "server-1")

    @pytest.mark.asyncio
    async def test_authenticate_authenticate_type(
        self, handler, mock_websocket, mock_agent_service
    ):
        """_authenticate_connection should handle authenticate type."""
        mock_websocket.receive_json.return_value = {
            "type": "authenticate",
            "token": "auth-token",
        }
        mock_agent_service.authenticate_agent = AsyncMock(
            return_value=("agent-1", {}, "server-1")
        )

        with (
            patch(
                "services.agent_websocket.send_authenticated", new_callable=AsyncMock
            ),
            patch("services.agent_websocket.log_event", new_callable=AsyncMock),
            patch("services.agent_websocket.logger"),
        ):
            result = await handler._authenticate_connection(mock_websocket)

            assert result == ("agent-1", "server-1")


class TestHandleRegistration:
    """Tests for _handle_registration method."""

    @pytest.mark.asyncio
    async def test_registration_no_code(self, handler, mock_websocket):
        """_handle_registration should reject missing code."""
        msg = {"type": "register"}

        with (
            patch("services.agent_websocket.send_error", new_callable=AsyncMock),
            patch("services.agent_websocket.close_websocket", new_callable=AsyncMock),
            patch("services.agent_websocket.logger"),
        ):
            result = await handler._handle_registration(mock_websocket, msg)

            assert result is None

    @pytest.mark.asyncio
    async def test_registration_failed(
        self, handler, mock_websocket, mock_agent_service
    ):
        """_handle_registration should handle failed registration."""
        msg = {"type": "register", "code": "invalid-code"}
        mock_agent_service.register_agent = AsyncMock(return_value=None)

        with (
            patch("services.agent_websocket.send_error", new_callable=AsyncMock),
            patch("services.agent_websocket.close_websocket", new_callable=AsyncMock),
            patch("services.agent_websocket.logger"),
        ):
            result = await handler._handle_registration(mock_websocket, msg)

            assert result is None

    @pytest.mark.asyncio
    async def test_registration_success(
        self, handler, mock_websocket, mock_agent_service
    ):
        """_handle_registration should return agent_id and server_id on success."""
        msg = {"type": "register", "code": "valid-code", "version": "1.0.0"}
        mock_agent_service.register_agent = AsyncMock(
            return_value=("agent-123", "token-abc", {"key": "config"}, "server-456")
        )

        with (
            patch(
                "services.agent_websocket.send_registered", new_callable=AsyncMock
            ) as mock_send,
            patch("services.agent_websocket.logger"),
        ):
            result = await handler._handle_registration(mock_websocket, msg)

            assert result == ("agent-123", "server-456")
            mock_send.assert_called_once_with(
                mock_websocket, "agent-123", "token-abc", {"key": "config"}
            )


class TestHandleAuthentication:
    """Tests for _handle_authentication method."""

    @pytest.mark.asyncio
    async def test_authentication_no_token(self, handler, mock_websocket):
        """_handle_authentication should reject missing token."""
        msg = {"type": "authenticate"}

        with (
            patch("services.agent_websocket.send_error", new_callable=AsyncMock),
            patch("services.agent_websocket.close_websocket", new_callable=AsyncMock),
            patch("services.agent_websocket.logger"),
        ):
            result = await handler._handle_authentication(mock_websocket, msg)

            assert result is None

    @pytest.mark.asyncio
    async def test_authentication_failed(
        self, handler, mock_websocket, mock_agent_service
    ):
        """_handle_authentication should handle failed authentication."""
        msg = {"type": "authenticate", "token": "invalid-token"}
        mock_agent_service.authenticate_agent = AsyncMock(return_value=None)

        with (
            patch("services.agent_websocket.send_error", new_callable=AsyncMock),
            patch("services.agent_websocket.close_websocket", new_callable=AsyncMock),
            patch("services.agent_websocket.logger"),
        ):
            result = await handler._handle_authentication(mock_websocket, msg)

            assert result is None

    @pytest.mark.asyncio
    async def test_authentication_success(
        self, handler, mock_websocket, mock_agent_service
    ):
        """_handle_authentication should return agent_id and server_id on success."""
        msg = {"type": "authenticate", "token": "valid-token", "version": "1.0.0"}
        mock_agent_service.authenticate_agent = AsyncMock(
            return_value=("agent-123", {"config": "data"}, "server-456")
        )

        with (
            patch(
                "services.agent_websocket.send_authenticated", new_callable=AsyncMock
            ) as mock_send,
            patch("services.agent_websocket.log_event", new_callable=AsyncMock),
            patch("services.agent_websocket.logger"),
        ):
            result = await handler._handle_authentication(mock_websocket, msg)

            assert result == ("agent-123", "server-456")
            mock_send.assert_called_once_with(
                mock_websocket, "agent-123", {"config": "data"}
            )

    @pytest.mark.asyncio
    async def test_authentication_logs_event(
        self, handler, mock_websocket, mock_agent_service
    ):
        """_handle_authentication should log agent connected event."""
        msg = {"type": "authenticate", "token": "valid-token"}
        mock_agent_service.authenticate_agent = AsyncMock(
            return_value=("agent-123", {}, "server-456")
        )

        with (
            patch(
                "services.agent_websocket.send_authenticated", new_callable=AsyncMock
            ),
            patch(
                "services.agent_websocket.log_event", new_callable=AsyncMock
            ) as mock_log,
            patch("services.agent_websocket.logger"),
        ):
            await handler._handle_authentication(mock_websocket, msg)

            mock_log.assert_called_once()
            call_args = mock_log.call_args
            assert call_args[0][0] == "agent"
            assert "AGENT_CONNECTED" in str(call_args[0][4])


class TestCloseWithError:
    """Tests for _close_with_error method."""

    @pytest.mark.asyncio
    async def test_close_with_error_sends_error(self, handler, mock_websocket):
        """_close_with_error should send error message."""
        with (
            patch(
                "services.agent_websocket.send_error", new_callable=AsyncMock
            ) as mock_send,
            patch("services.agent_websocket.close_websocket", new_callable=AsyncMock),
        ):
            await handler._close_with_error(mock_websocket, "Test error")

            mock_send.assert_called_once_with(mock_websocket, "Test error")

    @pytest.mark.asyncio
    async def test_close_with_error_closes_connection(self, handler, mock_websocket):
        """_close_with_error should close with auth failed code."""
        with (
            patch("services.agent_websocket.send_error", new_callable=AsyncMock),
            patch(
                "services.agent_websocket.close_websocket", new_callable=AsyncMock
            ) as mock_close,
        ):
            await handler._close_with_error(mock_websocket, "Test error")

            mock_close.assert_called_once_with(mock_websocket, WS_CLOSE_AUTH_FAILED)
