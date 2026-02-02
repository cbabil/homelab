"""Tests for agent authentication module.

Tests authentication flow, token-based auth, and registration.
"""

import json
from unittest.mock import AsyncMock, patch

import pytest

from auth import authenticate, _authenticate_with_token, _register_with_code
from config import AgentConfig, AgentState


class TestAuthenticate:
    """Tests for the authenticate function."""

    @pytest.mark.asyncio
    async def test_authenticates_with_existing_token(self):
        """Should authenticate using token when state exists."""
        mock_ws = AsyncMock()
        config = AgentConfig(server_url="wss://test.com")

        mock_state = AgentState(
            agent_id="existing-agent",
            token="existing-token",
            server_url="wss://test.com",
            registered_at="2024-01-01T00:00:00Z",
        )

        mock_ws.recv.return_value = json.dumps(
            {
                "type": "authenticated",
                "agent_id": "existing-agent",
                "config": {"metrics_interval": 45},
            }
        )

        with patch("auth.load_state", return_value=mock_state):
            agent_id, updated_config = await authenticate(mock_ws, config)

            assert agent_id == "existing-agent"
            assert updated_config.metrics_interval == 45

    @pytest.mark.asyncio
    async def test_registers_when_no_token_but_code(self):
        """Should register using code when no token exists."""
        mock_ws = AsyncMock()
        config = AgentConfig(
            server_url="wss://test.com",
            register_code="REG-CODE-123",
        )

        mock_ws.recv.return_value = json.dumps(
            {
                "type": "registered",
                "agent_id": "new-agent",
                "token": "new-token",
                "config": {"health_interval": 120},
            }
        )

        with patch("auth.load_state", return_value=None):
            with patch("auth.save_state"):
                agent_id, updated_config = await authenticate(mock_ws, config)

                assert agent_id == "new-agent"
                assert updated_config.health_interval == 120

    @pytest.mark.asyncio
    async def test_returns_none_when_no_token_or_code(self):
        """Should return None when no token or registration code."""
        mock_ws = AsyncMock()
        config = AgentConfig(server_url="wss://test.com")

        with patch("auth.load_state", return_value=None):
            agent_id, updated_config = await authenticate(mock_ws, config)

            assert agent_id is None
            assert updated_config is None


class TestAuthenticateWithToken:
    """Tests for _authenticate_with_token function."""

    @pytest.mark.asyncio
    async def test_successful_token_auth(self):
        """Should authenticate successfully with valid token."""
        mock_ws = AsyncMock()
        state = AgentState(
            agent_id="test-agent",
            token="valid-token",
            server_url="wss://test.com",
            registered_at="2024-01-01T00:00:00Z",
        )

        mock_ws.recv.return_value = json.dumps(
            {
                "type": "authenticated",
                "agent_id": "test-agent",
                "config": {},
            }
        )

        agent_id, updated_config = await _authenticate_with_token(mock_ws, state)

        assert agent_id == "test-agent"
        assert updated_config is not None

        # Verify correct message sent
        sent_data = json.loads(mock_ws.send.call_args[0][0])
        assert sent_data["type"] == "authenticate"
        assert sent_data["token"] == "valid-token"

    @pytest.mark.asyncio
    async def test_failed_token_auth(self):
        """Should return None on auth failure."""
        mock_ws = AsyncMock()
        state = AgentState(
            agent_id="test-agent",
            token="invalid-token",
            server_url="wss://test.com",
            registered_at="2024-01-01T00:00:00Z",
        )

        mock_ws.recv.return_value = json.dumps(
            {
                "type": "error",
                "error": "Invalid token",
            }
        )

        agent_id, updated_config = await _authenticate_with_token(mock_ws, state)

        assert agent_id is None
        assert updated_config is None

    @pytest.mark.asyncio
    async def test_includes_version_in_auth(self):
        """Should include version in authentication request."""
        mock_ws = AsyncMock()
        state = AgentState(
            agent_id="test-agent",
            token="token",
            server_url="wss://test.com",
            registered_at="2024-01-01T00:00:00Z",
        )

        mock_ws.recv.return_value = json.dumps(
            {
                "type": "authenticated",
                "agent_id": "test-agent",
                "config": {},
            }
        )

        with patch("auth.__version__", "1.2.3"):
            await _authenticate_with_token(mock_ws, state)

            sent_data = json.loads(mock_ws.send.call_args[0][0])
            assert sent_data["version"] == "1.2.3"


class TestRegisterWithCode:
    """Tests for _register_with_code function."""

    @pytest.mark.asyncio
    async def test_successful_registration(self):
        """Should register successfully with valid code."""
        mock_ws = AsyncMock()
        config = AgentConfig(
            server_url="wss://test.com",
            register_code="VALID-CODE",
        )

        mock_ws.recv.return_value = json.dumps(
            {
                "type": "registered",
                "agent_id": "new-agent-123",
                "token": "new-token-abc",
                "config": {"metrics_interval": 60},
            }
        )

        with patch("auth.save_state") as mock_save:
            agent_id, updated_config = await _register_with_code(mock_ws, config)

            assert agent_id == "new-agent-123"
            assert updated_config.metrics_interval == 60

            # Verify state was saved
            mock_save.assert_called_once()
            saved_state = mock_save.call_args[0][0]
            assert saved_state.agent_id == "new-agent-123"
            assert saved_state.token == "new-token-abc"
            assert saved_state.server_url == "wss://test.com"

    @pytest.mark.asyncio
    async def test_failed_registration(self):
        """Should return None on registration failure."""
        mock_ws = AsyncMock()
        config = AgentConfig(
            server_url="wss://test.com",
            register_code="INVALID-CODE",
        )

        mock_ws.recv.return_value = json.dumps(
            {
                "type": "error",
                "error": "Invalid registration code",
            }
        )

        agent_id, updated_config = await _register_with_code(mock_ws, config)

        assert agent_id is None
        assert updated_config is None

    @pytest.mark.asyncio
    async def test_sends_correct_register_message(self):
        """Should send correct registration message."""
        mock_ws = AsyncMock()
        config = AgentConfig(
            server_url="wss://test.com",
            register_code="TEST-REG-CODE",
        )

        mock_ws.recv.return_value = json.dumps(
            {
                "type": "registered",
                "agent_id": "agent",
                "token": "token",
                "config": {},
            }
        )

        with patch("auth.save_state"):
            with patch("auth.__version__", "2.0.0"):
                await _register_with_code(mock_ws, config)

                sent_data = json.loads(mock_ws.send.call_args[0][0])
                assert sent_data["type"] == "register"
                assert sent_data["code"] == "TEST-REG-CODE"
                assert sent_data["version"] == "2.0.0"

    @pytest.mark.asyncio
    async def test_registration_includes_timestamp(self):
        """Should include registration timestamp in saved state."""
        mock_ws = AsyncMock()
        config = AgentConfig(
            server_url="wss://test.com",
            register_code="CODE",
        )

        mock_ws.recv.return_value = json.dumps(
            {
                "type": "registered",
                "agent_id": "agent",
                "token": "token",
                "config": {},
            }
        )

        with patch("auth.save_state") as mock_save:
            await _register_with_code(mock_ws, config)

            saved_state = mock_save.call_args[0][0]
            assert saved_state.registered_at is not None
            # Should be ISO format
            assert "T" in saved_state.registered_at
