"""Tests for agent authentication - specifically reconnection scenarios."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, UTC

from models.agent import Agent, AgentStatus, AgentConfig
from services.agent_service import AgentService


@pytest.fixture
def mock_agent_db():
    """Create mock agent database."""
    db = MagicMock()
    db.get_agent_by_token_hash = AsyncMock()
    db.get_agent_by_pending_token_hash = AsyncMock(return_value=None)
    db.update_agent = AsyncMock()
    return db


@pytest.fixture
def agent_service(mock_agent_db):
    """Create agent service with mocks."""
    service = AgentService.__new__(AgentService)
    service._agent_db = mock_agent_db
    service._settings_service = MagicMock()
    service._settings_service.get_setting = AsyncMock(return_value=None)
    return service


class TestValidateToken:
    """Tests for validate_token - the reconnection scenario."""

    @pytest.mark.asyncio
    async def test_disconnected_agent_can_authenticate(self, agent_service, mock_agent_db):
        """CRITICAL: Disconnected agent with valid token should authenticate.

        This is the reconnection scenario:
        1. Backend restarts, sets all agents to DISCONNECTED
        2. Agent container tries to reconnect with valid token
        3. Should succeed so agent can reconnect
        """
        mock_agent = Agent(
            id="agent-123",
            server_id="server-456",
            status=AgentStatus.DISCONNECTED,  # Key: agent is DISCONNECTED
            token_hash="hashed_token",
            registered_at=datetime.now(UTC),
        )
        mock_agent_db.get_agent_by_token_hash.return_value = mock_agent

        result = await agent_service.validate_token("valid_token")

        assert result is not None, "DISCONNECTED agent should be able to authenticate"
        assert result.id == "agent-123"

    @pytest.mark.asyncio
    async def test_connected_agent_can_authenticate(self, agent_service, mock_agent_db):
        """Connected agent with valid token should authenticate."""
        mock_agent = Agent(
            id="agent-123",
            server_id="server-456",
            status=AgentStatus.CONNECTED,
            token_hash="hashed_token",
            registered_at=datetime.now(UTC),
        )
        mock_agent_db.get_agent_by_token_hash.return_value = mock_agent

        result = await agent_service.validate_token("valid_token")

        assert result is not None
        assert result.id == "agent-123"

    @pytest.mark.asyncio
    async def test_invalid_token_rejected(self, agent_service, mock_agent_db):
        """Invalid token should be rejected."""
        mock_agent_db.get_agent_by_token_hash.return_value = None

        result = await agent_service.validate_token("invalid_token")

        assert result is None


class TestAuthenticateAgent:
    """Tests for authenticate_agent flow."""

    @pytest.mark.asyncio
    async def test_authenticate_updates_last_seen(self, agent_service, mock_agent_db):
        """Successful authentication should update last_seen."""
        mock_agent = Agent(
            id="agent-123",
            server_id="server-456",
            status=AgentStatus.DISCONNECTED,
            token_hash="hashed_token",
            registered_at=datetime.now(UTC),
        )
        mock_agent_db.get_agent_by_token_hash.return_value = mock_agent

        result = await agent_service.authenticate_agent("valid_token", version="1.0.0")

        assert result is not None
        agent_id, config, server_id = result
        assert agent_id == "agent-123"
        assert server_id == "server-456"
        mock_agent_db.update_agent.assert_called_once()
