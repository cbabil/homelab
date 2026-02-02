"""
Unit tests for services/agent_service.py - Registration operations.

Tests create_agent, registration code validation, complete_registration,
token validation, revocation, and deletion.
"""

import pytest
from datetime import datetime, timedelta, UTC
from unittest.mock import AsyncMock, MagicMock, patch

from services.agent_service import AgentService
from models.agent import (
    Agent,
    AgentRegistrationResponse,
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


class TestCreateAgent:
    """Tests for create_agent method."""

    @pytest.mark.asyncio
    async def test_create_agent_success(
        self, agent_service, mock_agent_db, sample_agent, sample_registration_code
    ):
        """create_agent should create agent and registration code."""
        mock_agent_db.get_agent_by_server = AsyncMock(return_value=None)
        mock_agent_db.create_agent = AsyncMock(return_value=sample_agent)
        mock_agent_db.create_registration_code = AsyncMock(
            return_value=sample_registration_code
        )

        with patch("services.agent_service.logger"), \
             patch("services.agent_service.log_event", new_callable=AsyncMock):
            agent, code = await agent_service.create_agent("server-456")

        assert agent is sample_agent
        assert code is sample_registration_code
        mock_agent_db.create_agent.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_agent_deletes_existing(
        self, agent_service, mock_agent_db, sample_agent, sample_registration_code
    ):
        """create_agent should delete existing agent first."""
        existing_agent = Agent(
            id="old-agent-id",
            server_id="server-456",
            status=AgentStatus.DISCONNECTED,
        )
        mock_agent_db.get_agent_by_server = AsyncMock(return_value=existing_agent)
        mock_agent_db.get_agent = AsyncMock(return_value=existing_agent)
        mock_agent_db.delete_agent = AsyncMock(return_value=True)
        mock_agent_db.create_agent = AsyncMock(return_value=sample_agent)
        mock_agent_db.create_registration_code = AsyncMock(
            return_value=sample_registration_code
        )

        with patch("services.agent_service.logger"), \
             patch("services.agent_service.log_event", new_callable=AsyncMock):
            await agent_service.create_agent("server-456")

        mock_agent_db.delete_agent.assert_called_once_with("old-agent-id")

    @pytest.mark.asyncio
    async def test_create_agent_logs_event(
        self, agent_service, mock_agent_db, sample_agent, sample_registration_code
    ):
        """create_agent should log AGENT_INSTALLED event."""
        mock_agent_db.get_agent_by_server = AsyncMock(return_value=None)
        mock_agent_db.create_agent = AsyncMock(return_value=sample_agent)
        mock_agent_db.create_registration_code = AsyncMock(
            return_value=sample_registration_code
        )

        with patch("services.agent_service.logger"), \
             patch("services.agent_service.log_event", new_callable=AsyncMock) as mock_log:
            await agent_service.create_agent("server-456")

        mock_log.assert_called()
        call_args = mock_log.call_args[0]
        assert call_args[4]["event_type"] == "AGENT_INSTALLED"


class TestValidateRegistrationCode:
    """Tests for validate_registration_code method."""

    @pytest.mark.asyncio
    async def test_validate_code_success(
        self, agent_service, mock_agent_db, sample_registration_code
    ):
        """validate_registration_code should return code when valid."""
        mock_agent_db.get_registration_code = AsyncMock(
            return_value=sample_registration_code
        )

        with patch("services.agent_service.logger"):
            result = await agent_service.validate_registration_code("test-code-abc123")

        assert result is sample_registration_code

    @pytest.mark.asyncio
    async def test_validate_code_not_found(self, agent_service, mock_agent_db):
        """validate_registration_code should return None when not found."""
        mock_agent_db.get_registration_code = AsyncMock(return_value=None)

        with patch("services.agent_service.logger"):
            result = await agent_service.validate_registration_code("invalid-code")

        assert result is None

    @pytest.mark.asyncio
    async def test_validate_code_already_used(
        self, agent_service, mock_agent_db, sample_registration_code
    ):
        """validate_registration_code should return None when used."""
        sample_registration_code.used = True
        mock_agent_db.get_registration_code = AsyncMock(
            return_value=sample_registration_code
        )

        with patch("services.agent_service.logger"):
            result = await agent_service.validate_registration_code("test-code-abc123")

        assert result is None

    @pytest.mark.asyncio
    async def test_validate_code_expired(
        self, agent_service, mock_agent_db, sample_registration_code
    ):
        """validate_registration_code should return None when expired."""
        sample_registration_code.expires_at = datetime.now(UTC) - timedelta(hours=1)
        mock_agent_db.get_registration_code = AsyncMock(
            return_value=sample_registration_code
        )

        with patch("services.agent_service.logger"):
            result = await agent_service.validate_registration_code("test-code-abc123")

        assert result is None


class TestCompleteRegistration:
    """Tests for complete_registration method."""

    @pytest.mark.asyncio
    async def test_complete_registration_success(
        self, agent_service, mock_agent_db, sample_agent, sample_registration_code
    ):
        """complete_registration should return response on success."""
        mock_agent_db.get_registration_code = AsyncMock(
            return_value=sample_registration_code
        )
        mock_agent_db.update_agent = AsyncMock(return_value=sample_agent)

        with patch("services.agent_service.logger"), \
             patch("services.agent_service.log_event", new_callable=AsyncMock):
            result = await agent_service.complete_registration(
                "test-code-abc123", "1.0.0"
            )

        assert isinstance(result, AgentRegistrationResponse)
        assert result.agent_id == "agent-123"
        assert result.server_id == "server-456"
        assert result.token is not None
        mock_agent_db.mark_code_used.assert_called_once()

    @pytest.mark.asyncio
    async def test_complete_registration_invalid_code(
        self, agent_service, mock_agent_db
    ):
        """complete_registration should return None for invalid code."""
        mock_agent_db.get_registration_code = AsyncMock(return_value=None)

        with patch("services.agent_service.logger"):
            result = await agent_service.complete_registration(
                "invalid-code", "1.0.0"
            )

        assert result is None

    @pytest.mark.asyncio
    async def test_complete_registration_update_fails(
        self, agent_service, mock_agent_db, sample_registration_code
    ):
        """complete_registration should return None if update fails."""
        mock_agent_db.get_registration_code = AsyncMock(
            return_value=sample_registration_code
        )
        mock_agent_db.update_agent = AsyncMock(return_value=None)

        with patch("services.agent_service.logger"):
            result = await agent_service.complete_registration(
                "test-code-abc123", "1.0.0"
            )

        assert result is None

    @pytest.mark.asyncio
    async def test_complete_registration_logs_event(
        self, agent_service, mock_agent_db, sample_agent, sample_registration_code
    ):
        """complete_registration should log AGENT_REGISTERED event."""
        mock_agent_db.get_registration_code = AsyncMock(
            return_value=sample_registration_code
        )
        mock_agent_db.update_agent = AsyncMock(return_value=sample_agent)

        with patch("services.agent_service.logger"), \
             patch("services.agent_service.log_event", new_callable=AsyncMock) as mock_log:
            await agent_service.complete_registration("test-code-abc123", "1.0.0")

        mock_log.assert_called()
        call_args = mock_log.call_args[0]
        assert call_args[4]["event_type"] == "AGENT_REGISTERED"


class TestValidateToken:
    """Tests for validate_token method."""

    @pytest.mark.asyncio
    async def test_validate_token_success(
        self, agent_service, mock_agent_db, sample_agent
    ):
        """validate_token should return agent when valid."""
        mock_agent_db.get_agent_by_token_hash = AsyncMock(return_value=sample_agent)

        with patch("services.agent_service.logger"):
            result = await agent_service.validate_token("test-token")

        assert result is sample_agent

    @pytest.mark.asyncio
    async def test_validate_token_not_found(self, agent_service, mock_agent_db):
        """validate_token should return None when not found."""
        mock_agent_db.get_agent_by_token_hash = AsyncMock(return_value=None)

        with patch("services.agent_service.logger"):
            result = await agent_service.validate_token("invalid-token")

        assert result is None

    @pytest.mark.asyncio
    async def test_validate_token_disconnected_allowed(
        self, agent_service, mock_agent_db
    ):
        """validate_token should allow DISCONNECTED agents to reconnect."""
        disconnected_agent = Agent(
            id="agent-123",
            server_id="server-456",
            status=AgentStatus.DISCONNECTED,
        )
        mock_agent_db.get_agent_by_token_hash = AsyncMock(
            return_value=disconnected_agent
        )

        with patch("services.agent_service.logger"):
            result = await agent_service.validate_token("test-token")

        assert result is disconnected_agent


class TestRevokeAgentToken:
    """Tests for revoke_agent_token method."""

    @pytest.mark.asyncio
    async def test_revoke_token_success(
        self, agent_service, mock_agent_db, sample_agent
    ):
        """revoke_agent_token should return True on success."""
        mock_agent_db.update_agent = AsyncMock(return_value=sample_agent)

        with patch("services.agent_service.logger"), \
             patch("services.agent_service.log_event", new_callable=AsyncMock):
            result = await agent_service.revoke_agent_token("agent-123")

        assert result is True
        call_args = mock_agent_db.update_agent.call_args[0]
        assert call_args[0] == "agent-123"
        update = call_args[1]
        assert update.token_hash is None
        assert update.status == AgentStatus.DISCONNECTED

    @pytest.mark.asyncio
    async def test_revoke_token_not_found(self, agent_service, mock_agent_db):
        """revoke_agent_token should return False when not found."""
        mock_agent_db.update_agent = AsyncMock(return_value=None)

        with patch("services.agent_service.logger"):
            result = await agent_service.revoke_agent_token("nonexistent")

        assert result is False

    @pytest.mark.asyncio
    async def test_revoke_token_logs_event(
        self, agent_service, mock_agent_db, sample_agent
    ):
        """revoke_agent_token should log AGENT_REVOKED event."""
        mock_agent_db.update_agent = AsyncMock(return_value=sample_agent)

        with patch("services.agent_service.logger"), \
             patch("services.agent_service.log_event", new_callable=AsyncMock) as mock_log:
            await agent_service.revoke_agent_token("agent-123")

        mock_log.assert_called()
        call_args = mock_log.call_args[0]
        assert call_args[4]["event_type"] == "AGENT_REVOKED"


class TestDeleteAgent:
    """Tests for delete_agent method."""

    @pytest.mark.asyncio
    async def test_delete_agent_success(
        self, agent_service, mock_agent_db, sample_agent
    ):
        """delete_agent should return True on success."""
        mock_agent_db.get_agent = AsyncMock(return_value=sample_agent)
        mock_agent_db.delete_agent = AsyncMock(return_value=True)

        with patch("services.agent_service.logger"), \
             patch("services.agent_service.log_event", new_callable=AsyncMock):
            result = await agent_service.delete_agent("agent-123")

        assert result is True
        mock_agent_db.delete_agent.assert_called_once_with("agent-123")

    @pytest.mark.asyncio
    async def test_delete_agent_not_found(self, agent_service, mock_agent_db):
        """delete_agent should return False when not found."""
        mock_agent_db.get_agent = AsyncMock(return_value=None)
        mock_agent_db.delete_agent = AsyncMock(return_value=False)

        with patch("services.agent_service.logger"):
            result = await agent_service.delete_agent("nonexistent")

        assert result is False

    @pytest.mark.asyncio
    async def test_delete_agent_logs_event(
        self, agent_service, mock_agent_db, sample_agent
    ):
        """delete_agent should log AGENT_UNINSTALLED event on success."""
        mock_agent_db.get_agent = AsyncMock(return_value=sample_agent)
        mock_agent_db.delete_agent = AsyncMock(return_value=True)

        with patch("services.agent_service.logger"), \
             patch("services.agent_service.log_event", new_callable=AsyncMock) as mock_log:
            await agent_service.delete_agent("agent-123")

        mock_log.assert_called()
        call_args = mock_log.call_args[0]
        assert call_args[4]["event_type"] == "AGENT_UNINSTALLED"

    @pytest.mark.asyncio
    async def test_delete_agent_no_log_on_failure(self, agent_service, mock_agent_db):
        """delete_agent should not log event on failure."""
        mock_agent_db.get_agent = AsyncMock(return_value=None)
        mock_agent_db.delete_agent = AsyncMock(return_value=False)

        with patch("services.agent_service.logger"), \
             patch("services.agent_service.log_event", new_callable=AsyncMock) as mock_log:
            await agent_service.delete_agent("nonexistent")

        mock_log.assert_not_called()
