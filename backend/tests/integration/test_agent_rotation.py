"""
Integration tests for agent token rotation flow.

Tests the full rotation flow including WebSocket communication mocking.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import services.agent_service as agent_module
from models.agent import Agent, AgentStatus
from services.agent_manager import AgentManager
from services.agent_service import AgentService


@pytest.fixture
def mock_db_service():
    """Create mock database service."""
    return MagicMock()


@pytest.fixture
def mock_agent_db():
    """Create mock AgentDatabaseService."""
    db = AsyncMock()
    db.get_agent = AsyncMock(return_value=None)
    db.update_agent = AsyncMock(return_value=True)
    db.get_agent_by_pending_token_hash = AsyncMock(return_value=None)
    return db


@pytest.fixture
def mock_settings_service():
    """Create mock SettingsService."""
    service = MagicMock()
    service.get_setting = AsyncMock(side_effect=lambda key, default: default)
    return service


@pytest.fixture
def mock_websocket():
    """Create mock WebSocket that simulates agent responses."""
    ws = AsyncMock()
    ws.send_text = AsyncMock()
    ws.close = AsyncMock()
    return ws


@pytest.fixture
def agent_manager(mock_agent_db):
    """Create AgentManager with mocked dependencies."""
    return AgentManager(mock_agent_db)


@pytest.fixture
def agent_service(mock_db_service, mock_agent_db, mock_settings_service):
    """Create AgentService with mocked dependencies."""
    with patch.object(agent_module, "logger"):
        return AgentService(
            db_service=mock_db_service,
            settings_service=mock_settings_service,
            agent_db=mock_agent_db,
        )


class TestFullRotationFlow:
    """Integration tests for complete rotation flow."""

    @pytest.mark.asyncio
    async def test_rotation_flow_success(
        self, agent_service, agent_manager, mock_agent_db, mock_websocket
    ):
        """Test successful end-to-end rotation flow."""
        # Setup: Create an agent that's connected
        agent = Agent(
            id="agent-123",
            server_id="server-1",
            token_hash="old_hash_abc",
            status=AgentStatus.CONNECTED,
            registered_at=datetime.now(UTC),
            token_issued_at=datetime.now(UTC) - timedelta(days=10),
            token_expires_at=datetime.now(UTC) - timedelta(days=3),
        )
        mock_agent_db.get_agent.return_value = agent

        # Register the agent connection
        await agent_manager.register_connection("agent-123", mock_websocket, "server-1")

        # Step 1: Initiate rotation
        new_token = await agent_service.initiate_rotation("agent-123")

        assert new_token is not None
        assert len(new_token) > 20  # Token should be substantial

        # Verify pending_token_hash was set
        update_call = mock_agent_db.update_agent.call_args
        assert update_call is not None
        update_data = update_call[0][1]
        assert update_data.pending_token_hash is not None

        # Step 2: Simulate sending to agent via WebSocket
        with patch.object(
            agent_manager, "send_command",
            new_callable=AsyncMock,
            return_value={"status": "ok", "rotated_at": datetime.now(UTC).isoformat()}
        ):
            result = await agent_manager.send_rotation_request(
                "agent-123", new_token, 300
            )

        assert result is True

    @pytest.mark.asyncio
    async def test_rotation_flow_with_pending_token_auth(
        self, agent_service, mock_agent_db, mock_settings_service
    ):
        """Test that agent can authenticate with pending token."""
        # Setup: Agent with pending rotation
        agent = Agent(
            id="agent-123",
            server_id="server-1",
            token_hash="old_hash",
            pending_token_hash="pending_hash_xyz",
            status=AgentStatus.CONNECTED,
            registered_at=datetime.now(UTC),
            token_issued_at=datetime.now(UTC) - timedelta(days=5),
            token_expires_at=datetime.now(UTC) + timedelta(days=2),
        )

        # Mock: current token lookup fails, pending token lookup returns agent
        mock_agent_db.get_agent_by_token_hash = AsyncMock(return_value=None)
        mock_agent_db.get_agent_by_pending_token_hash = AsyncMock(return_value=agent)
        mock_agent_db.get_agent = AsyncMock(return_value=agent)

        # Simulate agent authenticating with pending token
        with patch.object(agent_service, "_hash_token", return_value="pending_hash_xyz"):
            result = await agent_service.validate_token("new-token-value")

        # Should find agent and auto-complete rotation
        assert result is not None
        assert result.id == "agent-123"

        # Verify rotation was completed (pending promoted to current)
        update_calls = mock_agent_db.update_agent.call_args_list
        assert len(update_calls) >= 1


class TestRotationWithOfflineAgent:
    """Tests for rotation when agent is offline."""

    @pytest.mark.asyncio
    async def test_rotation_fails_when_agent_offline(
        self, agent_service, agent_manager, mock_agent_db
    ):
        """Test that rotation fails gracefully when agent is not connected."""
        agent = Agent(
            id="agent-123",
            server_id="server-1",
            token_hash="current_hash",
            status=AgentStatus.DISCONNECTED,
            registered_at=datetime.now(UTC),
        )
        mock_agent_db.get_agent.return_value = agent

        # Agent is NOT connected (not registered with manager)
        assert agent_manager.is_connected("agent-123") is False

        # Attempt rotation request - should fail
        result = await agent_manager.send_rotation_request(
            "agent-123", "new-token", 300
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_rotation_timeout_handling(
        self, agent_manager, mock_agent_db, mock_websocket
    ):
        """Test rotation request timeout is handled gracefully."""
        # Register connection
        await agent_manager.register_connection("agent-123", mock_websocket, "server-1")

        # Simulate timeout
        with patch.object(
            agent_manager, "send_command",
            new_callable=AsyncMock,
            side_effect=TimeoutError("Agent did not respond")
        ):
            result = await agent_manager.send_rotation_request(
                "agent-123", "new-token", 300
            )

        assert result is False


class TestRotationRecovery:
    """Tests for rotation recovery scenarios."""

    @pytest.mark.asyncio
    async def test_cancel_rotation_on_failure(
        self, agent_service, mock_agent_db
    ):
        """Test that rotation can be cancelled on failure."""
        agent = Agent(
            id="agent-123",
            server_id="server-1",
            token_hash="current_hash",
            pending_token_hash="pending_hash",
            status=AgentStatus.CONNECTED,
            registered_at=datetime.now(UTC),
        )
        mock_agent_db.get_agent.return_value = agent

        # Cancel the rotation
        result = await agent_service.cancel_rotation("agent-123")

        assert result is True

        # Verify pending_token_hash was cleared (set to None)
        update_call = mock_agent_db.update_agent.call_args
        update_data = update_call[0][1]
        assert update_data.pending_token_hash is None

    @pytest.mark.asyncio
    async def test_agent_reconnect_with_old_token_during_grace(
        self, agent_service, mock_agent_db, mock_settings_service
    ):
        """Test agent can still use old token during grace period."""
        # Agent with pending rotation but old token still valid
        agent = Agent(
            id="agent-123",
            server_id="server-1",
            token_hash="current_hash_abc",
            pending_token_hash="pending_hash_xyz",
            status=AgentStatus.DISCONNECTED,
            registered_at=datetime.now(UTC),
            token_issued_at=datetime.now(UTC) - timedelta(days=5),
            token_expires_at=datetime.now(UTC) + timedelta(days=2),
        )
        # Mock: current token lookup succeeds
        mock_agent_db.get_agent_by_token_hash = AsyncMock(return_value=agent)
        mock_agent_db.get_agent_by_pending_token_hash = AsyncMock(return_value=None)

        # Agent reconnects with OLD token (current_hash_abc)
        with patch.object(agent_service, "_hash_token", return_value="current_hash_abc"):
            result = await agent_service.validate_token("old-token-value")

        # Should succeed - old token still valid
        assert result is not None
        assert result.id == "agent-123"

    @pytest.mark.asyncio
    async def test_agent_reconnect_with_new_token_completes_rotation(
        self, agent_service, mock_agent_db, mock_settings_service
    ):
        """Test agent reconnecting with new token completes rotation."""
        agent = Agent(
            id="agent-123",
            server_id="server-1",
            token_hash="old_hash",
            pending_token_hash="new_hash_xyz",
            status=AgentStatus.DISCONNECTED,
            registered_at=datetime.now(UTC),
            token_issued_at=datetime.now(UTC) - timedelta(days=5),
            token_expires_at=datetime.now(UTC) - timedelta(days=1),
        )

        # Not found by current token, but found by pending token
        mock_agent_db.get_agent_by_token_hash = AsyncMock(return_value=None)
        mock_agent_db.get_agent_by_pending_token_hash = AsyncMock(return_value=agent)
        mock_agent_db.get_agent = AsyncMock(return_value=agent)

        # Agent reconnects with NEW token
        with patch.object(agent_service, "_hash_token", return_value="new_hash_xyz"):
            result = await agent_service.validate_token("new-token-value")

        assert result is not None
        assert result.id == "agent-123"

        # Rotation should be auto-completed
        update_calls = mock_agent_db.update_agent.call_args_list
        # Should have called update to complete rotation
        assert len(update_calls) >= 1
