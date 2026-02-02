"""
Unit tests for services/agent_service.py - WebSocket API and lifecycle.

Tests register_agent, authenticate_agent, and reset_stale_agent_statuses.
"""

import pytest
from datetime import datetime, timedelta, UTC
from unittest.mock import AsyncMock, MagicMock, patch

from services.agent_service import AgentService
from models.agent import (
    Agent,
    AgentConfig,
    AgentStatus,
    RegistrationCode,
)


@pytest.fixture
def mock_db_service():
    """Create mock database service."""
    db = MagicMock()
    db.db_path = ":memory:"
    db.get_server_by_id = AsyncMock(return_value=None)
    return db


@pytest.fixture
def mock_settings_service():
    """Create mock settings service."""
    service = MagicMock()
    service.get_system_setting = AsyncMock(return_value=None)
    return service


@pytest.fixture
def mock_agent_db():
    """Create mock agent database service."""
    db = MagicMock()
    db.create_agent = AsyncMock()
    db.update_agent = AsyncMock()
    db.get_agent = AsyncMock()
    db.get_agent_by_server = AsyncMock()
    db.get_agent_by_token_hash = AsyncMock()
    db.delete_agent = AsyncMock()
    db.list_all_agents = AsyncMock(return_value=[])
    db.create_registration_code = AsyncMock()
    db.get_registration_code = AsyncMock()
    db.mark_code_used = AsyncMock()
    return db


@pytest.fixture
def agent_service(mock_db_service, mock_settings_service, mock_agent_db):
    """Create AgentService with mocked dependencies."""
    with patch("services.agent_service.logger"):
        return AgentService(
            db_service=mock_db_service,
            settings_service=mock_settings_service,
            agent_db=mock_agent_db,
        )


@pytest.fixture
def sample_agent():
    """Create sample agent for testing."""
    return Agent(
        id="agent-123",
        server_id="server-456",
        token_hash="hashed_token",
        version="1.0.0",
        status=AgentStatus.CONNECTED,
        last_seen=datetime.now(UTC),
        registered_at=datetime.now(UTC),
    )


@pytest.fixture
def sample_registration_code():
    """Create sample registration code for testing."""
    return RegistrationCode(
        id="code-123",
        agent_id="agent-123",
        code="test-code-abc123",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        used=False,
    )


class TestRegisterAgent:
    """Tests for register_agent method (WebSocket API)."""

    @pytest.mark.asyncio
    async def test_register_agent_success(
        self, agent_service, mock_agent_db, sample_agent, sample_registration_code
    ):
        """register_agent should return tuple on success."""
        mock_agent_db.get_registration_code = AsyncMock(
            return_value=sample_registration_code
        )
        mock_agent_db.update_agent = AsyncMock(return_value=sample_agent)

        with patch("services.agent_service.logger"), \
             patch("services.agent_service.log_event", new_callable=AsyncMock):
            result = await agent_service.register_agent("test-code", "1.0.0")

        assert result is not None
        agent_id, token, config, server_id = result
        assert agent_id == "agent-123"
        assert token is not None
        assert isinstance(config, AgentConfig)
        assert server_id == "server-456"

    @pytest.mark.asyncio
    async def test_register_agent_no_version(
        self, agent_service, mock_agent_db, sample_agent, sample_registration_code
    ):
        """register_agent should use 'unknown' for missing version."""
        mock_agent_db.get_registration_code = AsyncMock(
            return_value=sample_registration_code
        )
        mock_agent_db.update_agent = AsyncMock(return_value=sample_agent)

        with patch("services.agent_service.logger"), \
             patch("services.agent_service.log_event", new_callable=AsyncMock):
            result = await agent_service.register_agent("test-code")

        assert result is not None

    @pytest.mark.asyncio
    async def test_register_agent_failure(self, agent_service, mock_agent_db):
        """register_agent should return None on failure."""
        mock_agent_db.get_registration_code = AsyncMock(return_value=None)

        with patch("services.agent_service.logger"):
            result = await agent_service.register_agent("invalid-code")

        assert result is None


class TestAuthenticateAgent:
    """Tests for authenticate_agent method (WebSocket API)."""

    @pytest.mark.asyncio
    async def test_authenticate_agent_success(
        self, agent_service, mock_agent_db, sample_agent
    ):
        """authenticate_agent should return tuple on success."""
        mock_agent_db.get_agent_by_token_hash = AsyncMock(return_value=sample_agent)
        mock_agent_db.update_agent = AsyncMock(return_value=sample_agent)

        with patch("services.agent_service.logger"):
            result = await agent_service.authenticate_agent("test-token", "1.0.0")

        assert result is not None
        agent_id, config, server_id = result
        assert agent_id == "agent-123"
        assert isinstance(config, AgentConfig)
        assert server_id == "server-456"

    @pytest.mark.asyncio
    async def test_authenticate_agent_updates_last_seen(
        self, agent_service, mock_agent_db, sample_agent
    ):
        """authenticate_agent should update last_seen."""
        mock_agent_db.get_agent_by_token_hash = AsyncMock(return_value=sample_agent)
        mock_agent_db.update_agent = AsyncMock(return_value=sample_agent)

        with patch("services.agent_service.logger"):
            await agent_service.authenticate_agent("test-token")

        call_args = mock_agent_db.update_agent.call_args[0]
        update = call_args[1]
        assert update.last_seen is not None

    @pytest.mark.asyncio
    async def test_authenticate_agent_updates_version(
        self, agent_service, mock_agent_db, sample_agent
    ):
        """authenticate_agent should update version if provided."""
        mock_agent_db.get_agent_by_token_hash = AsyncMock(return_value=sample_agent)
        mock_agent_db.update_agent = AsyncMock(return_value=sample_agent)

        with patch("services.agent_service.logger"):
            await agent_service.authenticate_agent("test-token", "2.0.0")

        call_args = mock_agent_db.update_agent.call_args[0]
        update = call_args[1]
        assert update.version == "2.0.0"

    @pytest.mark.asyncio
    async def test_authenticate_agent_failure(self, agent_service, mock_agent_db):
        """authenticate_agent should return None on failure."""
        mock_agent_db.get_agent_by_token_hash = AsyncMock(return_value=None)

        with patch("services.agent_service.logger"):
            result = await agent_service.authenticate_agent("invalid-token")

        assert result is None


class TestResetStaleAgentStatuses:
    """Tests for reset_stale_agent_statuses method."""

    @pytest.mark.asyncio
    async def test_reset_stale_no_agents(self, agent_service, mock_agent_db):
        """reset_stale_agent_statuses should return 0 when no agents."""
        mock_agent_db.list_all_agents = AsyncMock(return_value=[])

        with patch("services.agent_service.logger"):
            result = await agent_service.reset_stale_agent_statuses()

        assert result == 0

    @pytest.mark.asyncio
    async def test_reset_stale_connected_agents(self, agent_service, mock_agent_db):
        """reset_stale_agent_statuses should reset CONNECTED agents."""
        connected_agent = Agent(
            id="agent-1",
            server_id="srv-1",
            status=AgentStatus.CONNECTED,
        )
        mock_agent_db.list_all_agents = AsyncMock(return_value=[connected_agent])
        mock_agent_db.update_agent = AsyncMock()

        with patch("services.agent_service.logger"):
            result = await agent_service.reset_stale_agent_statuses()

        assert result == 1
        call_args = mock_agent_db.update_agent.call_args[0]
        assert call_args[1].status == AgentStatus.DISCONNECTED

    @pytest.mark.asyncio
    async def test_reset_stale_pending_agents_old(self, agent_service, mock_agent_db):
        """reset_stale_agent_statuses should reset old PENDING agents."""
        old_time = datetime.now(UTC) - timedelta(minutes=15)
        pending_agent = Agent(
            id="agent-1",
            server_id="srv-1",
            status=AgentStatus.PENDING,
            registered_at=old_time,
        )
        mock_agent_db.list_all_agents = AsyncMock(return_value=[pending_agent])
        mock_agent_db.update_agent = AsyncMock()

        with patch("services.agent_service.logger"):
            result = await agent_service.reset_stale_agent_statuses()

        assert result == 1

    @pytest.mark.asyncio
    async def test_reset_stale_pending_no_timestamp(self, agent_service, mock_agent_db):
        """reset_stale_agent_statuses should reset PENDING agents with no timestamp."""
        pending_agent = Agent(
            id="agent-1",
            server_id="srv-1",
            status=AgentStatus.PENDING,
            registered_at=None,
            last_seen=None,
        )
        mock_agent_db.list_all_agents = AsyncMock(return_value=[pending_agent])
        mock_agent_db.update_agent = AsyncMock()

        with patch("services.agent_service.logger"):
            result = await agent_service.reset_stale_agent_statuses()

        assert result == 1

    @pytest.mark.asyncio
    async def test_reset_stale_recent_pending_not_reset(
        self, agent_service, mock_agent_db
    ):
        """reset_stale_agent_statuses should not reset recent PENDING agents."""
        recent_time = datetime.now(UTC) - timedelta(minutes=5)
        pending_agent = Agent(
            id="agent-1",
            server_id="srv-1",
            status=AgentStatus.PENDING,
            registered_at=recent_time,
        )
        mock_agent_db.list_all_agents = AsyncMock(return_value=[pending_agent])

        with patch("services.agent_service.logger"):
            result = await agent_service.reset_stale_agent_statuses()

        assert result == 0

    @pytest.mark.asyncio
    async def test_reset_stale_disconnected_not_reset(
        self, agent_service, mock_agent_db
    ):
        """reset_stale_agent_statuses should not reset DISCONNECTED agents."""
        disconnected_agent = Agent(
            id="agent-1",
            server_id="srv-1",
            status=AgentStatus.DISCONNECTED,
        )
        mock_agent_db.list_all_agents = AsyncMock(return_value=[disconnected_agent])

        with patch("services.agent_service.logger"):
            result = await agent_service.reset_stale_agent_statuses()

        assert result == 0

    @pytest.mark.asyncio
    async def test_reset_stale_logs_when_reset(self, agent_service, mock_agent_db):
        """reset_stale_agent_statuses should log when agents reset."""
        connected_agent = Agent(
            id="agent-1",
            server_id="srv-1",
            status=AgentStatus.CONNECTED,
        )
        mock_agent_db.list_all_agents = AsyncMock(return_value=[connected_agent])
        mock_agent_db.update_agent = AsyncMock()

        with patch("services.agent_service.logger") as mock_logger:
            await agent_service.reset_stale_agent_statuses()

        # Should log for each agent reset and summary
        assert mock_logger.info.call_count >= 2

    @pytest.mark.asyncio
    async def test_reset_stale_multiple_agents(self, agent_service, mock_agent_db):
        """reset_stale_agent_statuses should handle multiple agents."""
        old_time = datetime.now(UTC) - timedelta(minutes=15)
        agents = [
            Agent(id="agent-1", server_id="srv-1", status=AgentStatus.CONNECTED),
            Agent(
                id="agent-2", server_id="srv-2", status=AgentStatus.PENDING,
                registered_at=old_time
            ),
            Agent(id="agent-3", server_id="srv-3", status=AgentStatus.DISCONNECTED),
        ]
        mock_agent_db.list_all_agents = AsyncMock(return_value=agents)
        mock_agent_db.update_agent = AsyncMock()

        with patch("services.agent_service.logger"):
            result = await agent_service.reset_stale_agent_statuses()

        assert result == 2  # Only CONNECTED and old PENDING should be reset

    @pytest.mark.asyncio
    async def test_reset_stale_uses_last_seen_for_pending(
        self, agent_service, mock_agent_db
    ):
        """reset_stale_agent_statuses should use last_seen if no registered_at."""
        old_time = datetime.now(UTC) - timedelta(minutes=15)
        pending_agent = Agent(
            id="agent-1",
            server_id="srv-1",
            status=AgentStatus.PENDING,
            registered_at=None,
            last_seen=old_time,
        )
        mock_agent_db.list_all_agents = AsyncMock(return_value=[pending_agent])
        mock_agent_db.update_agent = AsyncMock()

        with patch("services.agent_service.logger"):
            result = await agent_service.reset_stale_agent_statuses()

        assert result == 1
