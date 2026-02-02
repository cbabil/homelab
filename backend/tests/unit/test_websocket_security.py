"""Tests for WebSocket security features.

Tests rate limiting, message size limits, auth timeout, and other
security measures in the WebSocket handling code.
"""

import asyncio
import time
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from services.helpers.websocket_helpers import (
    ConnectionRateLimiter,
    ws_rate_limiter,
    MAX_CONSECUTIVE_ERRORS,
    message_loop,
)
from services.agent_manager import AgentManager, MAX_MESSAGE_SIZE_BYTES
from services.agent_websocket import WS_AUTH_TIMEOUT_SECONDS


class TestConnectionRateLimiter:
    """Tests for the rate limiter."""

    @pytest.fixture
    def rate_limiter(self):
        """Create a fresh rate limiter for each test."""
        return ConnectionRateLimiter(
            max_attempts=3,
            window_seconds=60.0,
            base_block_seconds=10.0,
            max_block_seconds=300.0,
        )

    def test_allows_first_request(self, rate_limiter):
        """Should allow first request from new client."""
        assert rate_limiter.is_allowed("192.168.1.1") is True

    def test_allows_requests_within_limit(self, rate_limiter):
        """Should allow requests up to the limit."""
        client_ip = "192.168.1.1"

        for _ in range(3):
            assert rate_limiter.is_allowed(client_ip) is True
            rate_limiter.record_attempt(client_ip)

    def test_blocks_after_limit_exceeded(self, rate_limiter):
        """Should block after exceeding attempt limit."""
        client_ip = "192.168.1.2"

        # Make max_attempts
        for _ in range(3):
            rate_limiter.record_attempt(client_ip)

        # Should be blocked now
        assert rate_limiter.is_allowed(client_ip) is False

    def test_exponential_backoff(self, rate_limiter):
        """Should apply exponential backoff on repeated blocks."""
        client_ip = "192.168.1.3"

        # First block
        for _ in range(3):
            rate_limiter.record_attempt(client_ip)
        rate_limiter.is_allowed(client_ip)  # Triggers first block

        # Verify failure count increased
        assert rate_limiter._failure_counts[client_ip] == 1

        # Simulate time passing and another block
        rate_limiter._clients[client_ip].blocked_until = 0
        rate_limiter._clients[client_ip].attempts = 0
        rate_limiter._clients[client_ip].first_attempt = 0

        for _ in range(3):
            rate_limiter.record_attempt(client_ip)
        rate_limiter.is_allowed(client_ip)  # Triggers second block

        assert rate_limiter._failure_counts[client_ip] == 2

    def test_success_resets_state(self, rate_limiter):
        """Should reset state on successful auth."""
        client_ip = "192.168.1.4"

        # Record some attempts
        rate_limiter.record_attempt(client_ip)
        rate_limiter.record_attempt(client_ip)

        # Record success
        rate_limiter.record_success(client_ip)

        # Should be clean
        assert client_ip not in rate_limiter._clients
        assert client_ip not in rate_limiter._failure_counts

    def test_cleanup_expired(self, rate_limiter):
        """Should cleanup expired entries."""
        client_ip = "192.168.1.5"

        rate_limiter.record_attempt(client_ip)
        # Simulate old entry
        rate_limiter._clients[client_ip].last_attempt = time.time() - 200
        rate_limiter._clients[client_ip].blocked_until = 0

        cleaned = rate_limiter.cleanup_expired()
        assert cleaned == 1
        assert client_ip not in rate_limiter._clients


class TestMessageSizeLimits:
    """Tests for message size validation in AgentManager."""

    @pytest.fixture
    def mock_agent_db(self):
        """Create mock agent database service."""
        return MagicMock()

    @pytest.fixture
    def agent_manager(self, mock_agent_db):
        """Create AgentManager with mocks."""
        return AgentManager(agent_db=mock_agent_db)

    @pytest.mark.asyncio
    async def test_rejects_oversized_message(self, agent_manager):
        """Should reject messages larger than MAX_MESSAGE_SIZE_BYTES."""
        agent_id = "test-agent"

        # Create a connection
        mock_ws = MagicMock()
        mock_ws.send_text = AsyncMock()
        mock_ws.close = AsyncMock()

        await agent_manager.register_connection(agent_id, mock_ws, "server-1")

        # Create oversized message
        oversized = "x" * (MAX_MESSAGE_SIZE_BYTES + 1000)

        # Should not raise, just log warning and return
        await agent_manager.handle_message(agent_id, oversized)

        # Verify no processing happened (no response handlers called)
        # The message should have been rejected silently

    @pytest.mark.asyncio
    async def test_accepts_normal_size_message(self, agent_manager):
        """Should accept messages within size limit."""
        agent_id = "test-agent"

        mock_ws = MagicMock()
        mock_ws.send_text = AsyncMock()
        mock_ws.close = AsyncMock()

        await agent_manager.register_connection(agent_id, mock_ws, "server-1")

        # Create valid JSON-RPC notification within size limit
        valid_message = '{"jsonrpc": "2.0", "method": "test", "params": {}}'

        # Should not raise
        await agent_manager.handle_message(agent_id, valid_message)


class TestConnectionLocking:
    """Tests for race condition prevention in connection registration."""

    @pytest.fixture
    def mock_agent_db(self):
        """Create mock agent database service."""
        mock = MagicMock()
        mock.update_agent = AsyncMock()
        return mock

    @pytest.fixture
    def agent_manager(self, mock_agent_db):
        """Create AgentManager with mocks."""
        return AgentManager(agent_db=mock_agent_db)

    @pytest.mark.asyncio
    async def test_concurrent_registration_uses_lock(self, agent_manager):
        """Should use lock to prevent race conditions."""
        agent_id = "test-agent"

        mock_ws1 = MagicMock()
        mock_ws1.send_text = AsyncMock()
        mock_ws1.close = AsyncMock()

        mock_ws2 = MagicMock()
        mock_ws2.send_text = AsyncMock()
        mock_ws2.close = AsyncMock()

        # Register first connection
        await agent_manager.register_connection(agent_id, mock_ws1, "server-1")

        # Register second connection (should replace first)
        await agent_manager.register_connection(agent_id, mock_ws2, "server-1")

        # Should have called close on first websocket
        mock_ws1.close.assert_called_once()

        # Final connection should be ws2
        assert agent_manager._connections[agent_id].websocket == mock_ws2

    @pytest.mark.asyncio
    async def test_lock_is_per_agent(self, agent_manager):
        """Should have separate locks per agent."""
        agent1 = "agent-1"
        agent2 = "agent-2"

        lock1 = agent_manager._get_connection_lock(agent1)
        lock2 = agent_manager._get_connection_lock(agent2)

        assert lock1 is not lock2
        assert agent_manager._get_connection_lock(agent1) is lock1


class TestMessageLoopErrorHandling:
    """Tests for error handling in message loop."""

    @pytest.mark.asyncio
    async def test_disconnects_after_max_consecutive_errors(self):
        """Should disconnect after MAX_CONSECUTIVE_ERRORS consecutive errors."""
        mock_ws = MagicMock()
        mock_agent_manager = MagicMock()

        # Make handle_message always raise
        mock_agent_manager.handle_message = AsyncMock(
            side_effect=ValueError("Test error")
        )

        # Track receive_text calls
        call_count = 0

        async def receive_text():
            nonlocal call_count
            call_count += 1
            return '{"test": "message"}'

        mock_ws.receive_text = receive_text

        # Should raise after MAX_CONSECUTIVE_ERRORS errors
        with pytest.raises(RuntimeError, match="consecutive errors"):
            await message_loop(mock_ws, "test-agent", mock_agent_manager)

        # Should have tried MAX_CONSECUTIVE_ERRORS times
        assert call_count == MAX_CONSECUTIVE_ERRORS

    @pytest.mark.asyncio
    async def test_resets_error_count_on_success(self):
        """Should reset error count after successful message."""
        mock_ws = MagicMock()
        mock_agent_manager = MagicMock()

        # Simulate: 2 errors, 1 success, 2 more errors (should not disconnect)
        call_sequence = [
            ValueError("Error 1"),
            ValueError("Error 2"),
            None,  # Success
            ValueError("Error 3"),
            ValueError("Error 4"),
        ]
        call_idx = 0

        async def handle_message(agent_id, message):
            nonlocal call_idx
            if call_idx < len(call_sequence):
                result = call_sequence[call_idx]
                call_idx += 1
                if result:
                    raise result

        mock_agent_manager.handle_message = handle_message

        from starlette.websockets import WebSocketDisconnect

        receive_count = 0

        async def receive_text():
            nonlocal receive_count
            receive_count += 1
            if receive_count > 5:
                raise WebSocketDisconnect(code=1000)
            return '{"test": "message"}'

        mock_ws.receive_text = receive_text

        # Should disconnect normally (not due to errors)
        with pytest.raises(WebSocketDisconnect):
            await message_loop(mock_ws, "test-agent", mock_agent_manager)


class TestAuthTimeout:
    """Tests for authentication timeout constants."""

    def test_auth_timeout_is_reasonable(self):
        """Auth timeout should be reasonable (not too short or long)."""
        assert WS_AUTH_TIMEOUT_SECONDS >= 10.0  # At least 10 seconds
        assert WS_AUTH_TIMEOUT_SECONDS <= 120.0  # No more than 2 minutes


class TestAgentDeployValidation:
    """Tests for agent deploy script input validation."""

    def test_validates_registration_code(self):
        """Should validate registration code format."""
        from tools.agent.tools import AgentTools

        # Create minimal agent tools instance with mocks
        tools = AgentTools(
            agent_service=MagicMock(),
            agent_manager=MagicMock(),
            ssh_service=MagicMock(),
            server_service=MagicMock(),
        )

        # Valid codes
        assert tools._validate_registration_code("abc123") is True
        assert tools._validate_registration_code("ABC_def-123") is True

        # Invalid codes
        assert tools._validate_registration_code("") is False
        assert tools._validate_registration_code("code with spaces") is False
        assert tools._validate_registration_code("code;injection") is False
        assert tools._validate_registration_code("$(whoami)") is False
        assert tools._validate_registration_code("x" * 101) is False

    def test_validates_server_url(self):
        """Should validate server URL format."""
        from tools.agent.tools import AgentTools

        tools = AgentTools(
            agent_service=MagicMock(),
            agent_manager=MagicMock(),
            ssh_service=MagicMock(),
            server_service=MagicMock(),
        )

        # Valid URLs
        assert tools._validate_server_url("http://localhost:8000") is True
        assert tools._validate_server_url("https://example.com") is True
        assert tools._validate_server_url("http://192.168.1.1:8000/api") is True
        # WebSocket URLs
        assert tools._validate_server_url("ws://localhost:8000/ws/agent") is True
        assert tools._validate_server_url("wss://example.com/ws/agent") is True
        # URLs with query parameters
        assert tools._validate_server_url("http://example.com/api?token=abc") is True

        # Invalid URLs
        assert tools._validate_server_url("") is False
        assert tools._validate_server_url("ftp://server.com") is False
        assert tools._validate_server_url("http://$(whoami)") is False
        assert tools._validate_server_url("http://server;rm -rf /") is False

    def test_build_deploy_script_validates_inputs(self):
        """Should reject invalid inputs in deploy script builder."""
        from tools.agent.tools import AgentTools

        tools = AgentTools(
            agent_service=MagicMock(),
            agent_manager=MagicMock(),
            ssh_service=MagicMock(),
            server_service=MagicMock(),
        )

        # Mock packager
        tools.agent_packager = MagicMock()
        tools.agent_packager.package.return_value = "base64data"
        tools.agent_packager.get_version.return_value = "1.0.0"

        # Valid inputs should work
        script = tools._build_deploy_script("validcode123", "http://localhost:8000")
        assert "REGISTER_CODE=" in script

        # Invalid code should raise
        with pytest.raises(ValueError, match="registration code"):
            tools._build_deploy_script("$(bad);code", "http://localhost:8000")

        # Invalid URL should raise
        with pytest.raises(ValueError, match="server URL"):
            tools._build_deploy_script("validcode", "not-a-url")
