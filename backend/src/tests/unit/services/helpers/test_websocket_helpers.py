"""
Unit tests for services/helpers/websocket_helpers.py

Tests WebSocket helper functions and rate limiting for agent connections.
"""

import time
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from starlette.websockets import WebSocketDisconnect, WebSocketState

from services.helpers.websocket_helpers import (
    ConnectionRateLimiter,
    RateLimitEntry,
    close_websocket,
    get_client_info,
    message_loop,
    send_authenticated,
    send_error,
    send_registered,
    ws_rate_limiter,
    MAX_CONSECUTIVE_ERRORS,
)


class TestRateLimitEntry:
    """Tests for RateLimitEntry dataclass."""

    def test_default_values(self):
        """RateLimitEntry should have correct default values."""
        entry = RateLimitEntry()
        assert entry.attempts == 0
        assert entry.first_attempt == 0.0
        assert entry.last_attempt == 0.0
        assert entry.blocked_until == 0.0

    def test_custom_values(self):
        """RateLimitEntry should accept custom values."""
        entry = RateLimitEntry(
            attempts=5, first_attempt=100.0, last_attempt=150.0, blocked_until=200.0
        )
        assert entry.attempts == 5
        assert entry.first_attempt == 100.0
        assert entry.last_attempt == 150.0
        assert entry.blocked_until == 200.0


class TestConnectionRateLimiterInit:
    """Tests for ConnectionRateLimiter initialization."""

    def test_default_values(self):
        """ConnectionRateLimiter should use correct default values."""
        limiter = ConnectionRateLimiter()
        assert limiter._max_attempts == 5
        assert limiter._window_seconds == 60.0
        assert limiter._base_block_seconds == 30.0
        assert limiter._max_block_seconds == 3600.0

    def test_custom_values(self):
        """ConnectionRateLimiter should accept custom values."""
        limiter = ConnectionRateLimiter(
            max_attempts=10,
            window_seconds=120.0,
            base_block_seconds=60.0,
            max_block_seconds=7200.0,
        )
        assert limiter._max_attempts == 10
        assert limiter._window_seconds == 120.0
        assert limiter._base_block_seconds == 60.0
        assert limiter._max_block_seconds == 7200.0

    def test_empty_clients_dict(self):
        """ConnectionRateLimiter should start with empty clients dict."""
        limiter = ConnectionRateLimiter()
        assert len(limiter._clients) == 0
        assert len(limiter._failure_counts) == 0


class TestConnectionRateLimiterIsAllowed:
    """Tests for ConnectionRateLimiter.is_allowed method."""

    def test_new_client_allowed(self):
        """is_allowed should return True for new client."""
        limiter = ConnectionRateLimiter()
        assert limiter.is_allowed("192.168.1.1") is True

    def test_blocked_client_not_allowed(self):
        """is_allowed should return False for blocked client."""
        limiter = ConnectionRateLimiter()
        client_ip = "192.168.1.1"
        # Manually block the client
        limiter._clients[client_ip].blocked_until = time.time() + 100

        with patch("services.helpers.websocket_helpers.logger"):
            assert limiter.is_allowed(client_ip) is False

    def test_block_expired_allowed(self):
        """is_allowed should return True when block has expired."""
        limiter = ConnectionRateLimiter()
        client_ip = "192.168.1.1"
        # Set block that has expired
        limiter._clients[client_ip].blocked_until = time.time() - 10
        limiter._clients[client_ip].first_attempt = time.time()

        assert limiter.is_allowed(client_ip) is True

    def test_window_reset(self):
        """is_allowed should reset attempts when window expires."""
        limiter = ConnectionRateLimiter(window_seconds=60.0)
        client_ip = "192.168.1.1"

        # Set up attempts from old window
        limiter._clients[client_ip].attempts = 4
        limiter._clients[client_ip].first_attempt = time.time() - 120  # 2 minutes ago

        result = limiter.is_allowed(client_ip)

        assert result is True
        assert limiter._clients[client_ip].attempts == 0

    def test_max_attempts_exceeded(self):
        """is_allowed should block client when max attempts exceeded."""
        limiter = ConnectionRateLimiter(max_attempts=5, base_block_seconds=30.0)
        client_ip = "192.168.1.1"

        limiter._clients[client_ip].attempts = 5
        limiter._clients[client_ip].first_attempt = time.time()

        with patch("services.helpers.websocket_helpers.logger"):
            result = limiter.is_allowed(client_ip)

        assert result is False
        assert limiter._clients[client_ip].blocked_until > time.time()

    def test_exponential_backoff(self):
        """is_allowed should apply exponential backoff on repeated failures."""
        limiter = ConnectionRateLimiter(
            max_attempts=5, base_block_seconds=30.0, max_block_seconds=3600.0
        )
        client_ip = "192.168.1.1"

        # First block: 30 seconds
        limiter._clients[client_ip].attempts = 5
        limiter._clients[client_ip].first_attempt = time.time()

        with patch("services.helpers.websocket_helpers.logger"):
            limiter.is_allowed(client_ip)

        assert limiter._failure_counts[client_ip] == 1

        # Reset for second violation
        limiter._clients[client_ip].blocked_until = 0
        limiter._clients[client_ip].attempts = 5
        limiter._clients[client_ip].first_attempt = time.time()

        with patch("services.helpers.websocket_helpers.logger"):
            limiter.is_allowed(client_ip)

        assert limiter._failure_counts[client_ip] == 2

    def test_max_block_duration_cap(self):
        """is_allowed should cap block duration at max_block_seconds."""
        limiter = ConnectionRateLimiter(
            max_attempts=5, base_block_seconds=1000.0, max_block_seconds=100.0
        )
        client_ip = "192.168.1.1"

        limiter._failure_counts[client_ip] = 10  # Would be 1000 * 2^10 without cap
        limiter._clients[client_ip].attempts = 5
        limiter._clients[client_ip].first_attempt = time.time()

        now = time.time()
        with patch("services.helpers.websocket_helpers.logger"):
            limiter.is_allowed(client_ip)

        # Block should be capped at ~100 seconds (allow small timing tolerance)
        block_duration = limiter._clients[client_ip].blocked_until - now
        assert block_duration <= 100.1

    def test_logs_warning_when_blocked(self):
        """is_allowed should log warning when client is blocked."""
        limiter = ConnectionRateLimiter()
        client_ip = "192.168.1.1"
        limiter._clients[client_ip].blocked_until = time.time() + 100

        with patch("services.helpers.websocket_helpers.logger") as mock_logger:
            limiter.is_allowed(client_ip)
            mock_logger.warning.assert_called()

    def test_logs_warning_when_rate_limited(self):
        """is_allowed should log warning when client is rate limited."""
        limiter = ConnectionRateLimiter(max_attempts=5)
        client_ip = "192.168.1.1"
        limiter._clients[client_ip].attempts = 5
        limiter._clients[client_ip].first_attempt = time.time()

        with patch("services.helpers.websocket_helpers.logger") as mock_logger:
            limiter.is_allowed(client_ip)
            mock_logger.warning.assert_called()


class TestConnectionRateLimiterRecordAttempt:
    """Tests for ConnectionRateLimiter.record_attempt method."""

    def test_first_attempt_sets_time(self):
        """record_attempt should set first_attempt on first attempt."""
        limiter = ConnectionRateLimiter()
        client_ip = "192.168.1.1"

        before = time.time()
        limiter.record_attempt(client_ip)
        after = time.time()

        assert before <= limiter._clients[client_ip].first_attempt <= after
        assert limiter._clients[client_ip].attempts == 1

    def test_subsequent_attempt_no_reset(self):
        """record_attempt should not reset first_attempt on subsequent attempts."""
        limiter = ConnectionRateLimiter()
        client_ip = "192.168.1.1"

        initial_time = time.time() - 30
        limiter._clients[client_ip].first_attempt = initial_time

        limiter.record_attempt(client_ip)

        assert limiter._clients[client_ip].first_attempt == initial_time

    def test_increments_attempts(self):
        """record_attempt should increment attempt count."""
        limiter = ConnectionRateLimiter()
        client_ip = "192.168.1.1"

        limiter.record_attempt(client_ip)
        assert limiter._clients[client_ip].attempts == 1

        limiter.record_attempt(client_ip)
        assert limiter._clients[client_ip].attempts == 2

    def test_updates_last_attempt(self):
        """record_attempt should update last_attempt time."""
        limiter = ConnectionRateLimiter()
        client_ip = "192.168.1.1"

        before = time.time()
        limiter.record_attempt(client_ip)
        after = time.time()

        assert before <= limiter._clients[client_ip].last_attempt <= after


class TestConnectionRateLimiterRecordSuccess:
    """Tests for ConnectionRateLimiter.record_success method."""

    def test_clears_failure_count(self):
        """record_success should clear failure count."""
        limiter = ConnectionRateLimiter()
        client_ip = "192.168.1.1"

        limiter._failure_counts[client_ip] = 5

        limiter.record_success(client_ip)

        assert client_ip not in limiter._failure_counts

    def test_clears_client_entry(self):
        """record_success should clear client entry."""
        limiter = ConnectionRateLimiter()
        client_ip = "192.168.1.1"

        limiter._clients[client_ip].attempts = 3
        limiter._clients[client_ip].first_attempt = time.time()

        limiter.record_success(client_ip)

        assert client_ip not in limiter._clients

    def test_handles_unknown_client(self):
        """record_success should handle unknown client gracefully."""
        limiter = ConnectionRateLimiter()
        # Should not raise exception
        limiter.record_success("unknown-ip")


class TestConnectionRateLimiterRecordFailure:
    """Tests for ConnectionRateLimiter.record_failure method."""

    def test_calls_record_attempt(self):
        """record_failure should call record_attempt."""
        limiter = ConnectionRateLimiter()
        client_ip = "192.168.1.1"

        limiter.record_failure(client_ip)

        assert limiter._clients[client_ip].attempts == 1


class TestConnectionRateLimiterCleanupExpired:
    """Tests for ConnectionRateLimiter.cleanup_expired method."""

    def test_removes_expired_entries(self):
        """cleanup_expired should remove expired entries."""
        limiter = ConnectionRateLimiter(window_seconds=60.0)
        client_ip = "192.168.1.1"

        # Set up an expired entry
        limiter._clients[client_ip].blocked_until = time.time() - 10
        limiter._clients[client_ip].last_attempt = time.time() - 200  # Past 2x window
        limiter._failure_counts[client_ip] = 1

        count = limiter.cleanup_expired()

        assert count == 1
        assert client_ip not in limiter._clients
        assert client_ip not in limiter._failure_counts

    def test_keeps_active_entries(self):
        """cleanup_expired should keep active entries."""
        limiter = ConnectionRateLimiter(window_seconds=60.0)
        client_ip = "192.168.1.1"

        # Set up an active entry
        limiter._clients[client_ip].blocked_until = 0
        limiter._clients[client_ip].last_attempt = time.time()  # Recent

        count = limiter.cleanup_expired()

        assert count == 0
        assert client_ip in limiter._clients

    def test_keeps_blocked_entries(self):
        """cleanup_expired should keep currently blocked entries."""
        limiter = ConnectionRateLimiter()
        client_ip = "192.168.1.1"

        # Set up a blocked entry
        limiter._clients[client_ip].blocked_until = time.time() + 100
        limiter._clients[client_ip].last_attempt = time.time() - 200

        count = limiter.cleanup_expired()

        assert count == 0
        assert client_ip in limiter._clients

    def test_returns_cleanup_count(self):
        """cleanup_expired should return count of cleaned entries."""
        limiter = ConnectionRateLimiter(window_seconds=60.0)

        # Add multiple expired entries
        for i in range(3):
            ip = f"192.168.1.{i}"
            limiter._clients[ip].blocked_until = time.time() - 10
            limiter._clients[ip].last_attempt = time.time() - 200

        count = limiter.cleanup_expired()

        assert count == 3


class TestGlobalRateLimiter:
    """Tests for global ws_rate_limiter instance."""

    def test_ws_rate_limiter_exists(self):
        """ws_rate_limiter should be a ConnectionRateLimiter instance."""
        assert isinstance(ws_rate_limiter, ConnectionRateLimiter)


class TestMaxConsecutiveErrors:
    """Tests for MAX_CONSECUTIVE_ERRORS constant."""

    def test_max_consecutive_errors_value(self):
        """MAX_CONSECUTIVE_ERRORS should be 5."""
        assert MAX_CONSECUTIVE_ERRORS == 5


class TestMessageLoop:
    """Tests for message_loop function."""

    @pytest.fixture
    def mock_websocket(self):
        """Create mock WebSocket."""
        ws = AsyncMock()
        ws.receive_text = AsyncMock()
        return ws

    @pytest.fixture
    def mock_agent_manager(self):
        """Create mock AgentManager."""
        manager = MagicMock()
        manager.handle_message = AsyncMock()
        return manager

    @pytest.mark.asyncio
    async def test_processes_messages(self, mock_websocket, mock_agent_manager):
        """message_loop should process messages from websocket."""
        mock_websocket.receive_text.side_effect = [
            "message1",
            "message2",
            WebSocketDisconnect(),
        ]

        with pytest.raises(WebSocketDisconnect):
            await message_loop(mock_websocket, "agent-123", mock_agent_manager)

        assert mock_agent_manager.handle_message.call_count == 2
        mock_agent_manager.handle_message.assert_any_call("agent-123", "message1")
        mock_agent_manager.handle_message.assert_any_call("agent-123", "message2")

    @pytest.mark.asyncio
    async def test_reraises_websocket_disconnect(
        self, mock_websocket, mock_agent_manager
    ):
        """message_loop should reraise WebSocketDisconnect."""
        mock_websocket.receive_text.side_effect = WebSocketDisconnect()

        with pytest.raises(WebSocketDisconnect):
            await message_loop(mock_websocket, "agent-123", mock_agent_manager)

    @pytest.mark.asyncio
    async def test_handles_processing_error(self, mock_websocket, mock_agent_manager):
        """message_loop should handle message processing error."""
        mock_websocket.receive_text.side_effect = [
            "message1",
            WebSocketDisconnect(),
        ]
        mock_agent_manager.handle_message.side_effect = [
            Exception("Processing error"),
            None,
        ]

        with patch("services.helpers.websocket_helpers.logger"):
            with pytest.raises(WebSocketDisconnect):
                await message_loop(mock_websocket, "agent-123", mock_agent_manager)

    @pytest.mark.asyncio
    async def test_resets_error_count_on_success(
        self, mock_websocket, mock_agent_manager
    ):
        """message_loop should reset error count on success."""
        error_sequence = [
            Exception("Error 1"),
            Exception("Error 2"),
            None,  # Success
            Exception("Error 3"),
            WebSocketDisconnect(),
        ]
        mock_websocket.receive_text.side_effect = [
            "msg1",
            "msg2",
            "msg3",
            "msg4",
            WebSocketDisconnect(),
        ]
        mock_agent_manager.handle_message.side_effect = error_sequence

        with patch("services.helpers.websocket_helpers.logger"):
            with pytest.raises(WebSocketDisconnect):
                await message_loop(mock_websocket, "agent-123", mock_agent_manager)

    @pytest.mark.asyncio
    async def test_disconnects_after_max_errors(
        self, mock_websocket, mock_agent_manager
    ):
        """message_loop should disconnect after MAX_CONSECUTIVE_ERRORS."""
        mock_websocket.receive_text.return_value = "message"
        mock_agent_manager.handle_message.side_effect = Exception("Recurring error")

        with patch("services.helpers.websocket_helpers.logger"):
            with pytest.raises(RuntimeError) as exc_info:
                await message_loop(mock_websocket, "agent-123", mock_agent_manager)

        assert "consecutive errors" in str(exc_info.value)
        assert mock_agent_manager.handle_message.call_count == MAX_CONSECUTIVE_ERRORS

    @pytest.mark.asyncio
    async def test_logs_warning_on_error(self, mock_websocket, mock_agent_manager):
        """message_loop should log warning on message processing error."""
        mock_websocket.receive_text.side_effect = [
            "message",
            WebSocketDisconnect(),
        ]
        mock_agent_manager.handle_message.side_effect = [Exception("Error"), None]

        with patch("services.helpers.websocket_helpers.logger") as mock_logger:
            with pytest.raises(WebSocketDisconnect):
                await message_loop(mock_websocket, "agent-123", mock_agent_manager)

            mock_logger.warning.assert_called()

    @pytest.mark.asyncio
    async def test_logs_error_on_disconnect(self, mock_websocket, mock_agent_manager):
        """message_loop should log error when disconnecting due to errors."""
        mock_websocket.receive_text.return_value = "message"
        mock_agent_manager.handle_message.side_effect = Exception("Error")

        with patch("services.helpers.websocket_helpers.logger") as mock_logger:
            with pytest.raises(RuntimeError):
                await message_loop(mock_websocket, "agent-123", mock_agent_manager)

            mock_logger.error.assert_called()


class TestSendError:
    """Tests for send_error function."""

    @pytest.fixture
    def mock_websocket(self):
        """Create mock WebSocket."""
        ws = AsyncMock()
        ws.send_json = AsyncMock()
        ws.client_state = WebSocketState.CONNECTED
        return ws

    @pytest.mark.asyncio
    async def test_sends_error_json(self, mock_websocket):
        """send_error should send error as JSON."""
        await send_error(mock_websocket, "Test error message")

        mock_websocket.send_json.assert_called_once_with(
            {"error": "Test error message"}
        )

    @pytest.mark.asyncio
    async def test_checks_connection_state(self, mock_websocket):
        """send_error should check connection state before sending."""
        mock_websocket.client_state = WebSocketState.DISCONNECTED

        await send_error(mock_websocket, "Test error")

        mock_websocket.send_json.assert_not_called()

    @pytest.mark.asyncio
    async def test_handles_send_failure(self, mock_websocket):
        """send_error should handle send failure gracefully."""
        mock_websocket.send_json.side_effect = Exception("Send failed")

        with patch("services.helpers.websocket_helpers.logger") as mock_logger:
            # Should not raise exception
            await send_error(mock_websocket, "Test error")
            mock_logger.debug.assert_called()


class TestSendRegistered:
    """Tests for send_registered function."""

    @pytest.fixture
    def mock_websocket(self):
        """Create mock WebSocket."""
        ws = AsyncMock()
        ws.send_json = AsyncMock()
        return ws

    @pytest.mark.asyncio
    async def test_sends_registered_response(self, mock_websocket):
        """send_registered should send registration response."""
        config = {"key": "value"}

        await send_registered(mock_websocket, "agent-123", "token-abc", config)

        mock_websocket.send_json.assert_called_once_with(
            {
                "type": "registered",
                "agent_id": "agent-123",
                "token": "token-abc",
                "config": {"key": "value"},
            }
        )

    @pytest.mark.asyncio
    async def test_handles_pydantic_model(self, mock_websocket):
        """send_registered should handle pydantic model config."""
        mock_config = MagicMock()
        mock_config.model_dump.return_value = {"setting": "data"}

        await send_registered(mock_websocket, "agent-1", "token-1", mock_config)

        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["config"] == {"setting": "data"}

    @pytest.mark.asyncio
    async def test_handles_dict_config(self, mock_websocket):
        """send_registered should handle dict config."""
        config = {"direct": "dict"}

        await send_registered(mock_websocket, "agent-1", "token-1", config)

        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["config"] == {"direct": "dict"}


class TestSendAuthenticated:
    """Tests for send_authenticated function."""

    @pytest.fixture
    def mock_websocket(self):
        """Create mock WebSocket."""
        ws = AsyncMock()
        ws.send_json = AsyncMock()
        return ws

    @pytest.mark.asyncio
    async def test_sends_authenticated_response(self, mock_websocket):
        """send_authenticated should send authentication response."""
        config = {"key": "value"}

        await send_authenticated(mock_websocket, "agent-123", config)

        mock_websocket.send_json.assert_called_once_with(
            {
                "type": "authenticated",
                "agent_id": "agent-123",
                "config": {"key": "value"},
            }
        )

    @pytest.mark.asyncio
    async def test_handles_pydantic_model(self, mock_websocket):
        """send_authenticated should handle pydantic model config."""
        mock_config = MagicMock()
        mock_config.model_dump.return_value = {"auth": "config"}

        await send_authenticated(mock_websocket, "agent-1", mock_config)

        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["config"] == {"auth": "config"}

    @pytest.mark.asyncio
    async def test_handles_dict_config(self, mock_websocket):
        """send_authenticated should handle dict config."""
        config = {"direct": "dict"}

        await send_authenticated(mock_websocket, "agent-1", config)

        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["config"] == {"direct": "dict"}


class TestCloseWebsocket:
    """Tests for close_websocket function."""

    @pytest.fixture
    def mock_websocket(self):
        """Create mock WebSocket."""
        ws = AsyncMock()
        ws.close = AsyncMock()
        ws.client_state = WebSocketState.CONNECTED
        return ws

    @pytest.mark.asyncio
    async def test_closes_connected_websocket(self, mock_websocket):
        """close_websocket should close connected websocket."""
        await close_websocket(mock_websocket, 1000)

        mock_websocket.close.assert_called_once_with(code=1000)

    @pytest.mark.asyncio
    async def test_skips_disconnected_websocket(self, mock_websocket):
        """close_websocket should skip already disconnected websocket."""
        mock_websocket.client_state = WebSocketState.DISCONNECTED

        await close_websocket(mock_websocket, 1000)

        mock_websocket.close.assert_not_called()

    @pytest.mark.asyncio
    async def test_handles_close_failure(self, mock_websocket):
        """close_websocket should handle close failure gracefully."""
        mock_websocket.close.side_effect = Exception("Close failed")

        with patch("services.helpers.websocket_helpers.logger") as mock_logger:
            # Should not raise exception
            await close_websocket(mock_websocket, 1000)
            mock_logger.debug.assert_called()

    @pytest.mark.asyncio
    async def test_uses_custom_code(self, mock_websocket):
        """close_websocket should use provided close code."""
        await close_websocket(mock_websocket, 4001)

        mock_websocket.close.assert_called_once_with(code=4001)


class TestGetClientInfo:
    """Tests for get_client_info function."""

    def test_returns_client_host_and_port(self):
        """get_client_info should return client host and port."""
        mock_ws = MagicMock()
        mock_ws.client = MagicMock(host="192.168.1.100", port=54321)

        result = get_client_info(mock_ws)

        assert result == {"client_host": "192.168.1.100", "client_port": 54321}

    def test_handles_none_client(self):
        """get_client_info should handle None client."""
        mock_ws = MagicMock()
        mock_ws.client = None

        result = get_client_info(mock_ws)

        assert result == {"client_host": "unknown", "client_port": 0}

    def test_returns_dict(self):
        """get_client_info should return a dictionary."""
        mock_ws = MagicMock()
        mock_ws.client = MagicMock(host="localhost", port=8080)

        result = get_client_info(mock_ws)

        assert isinstance(result, dict)
        assert "client_host" in result
        assert "client_port" in result
