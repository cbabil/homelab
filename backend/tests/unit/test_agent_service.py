"""
Unit tests for services/agent_service.py

Tests for agent lifecycle management service.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import services.agent_service as agent_module
from models.agent import (
    Agent,
    AgentConfig,
    AgentRegistrationResponse,
    AgentStatus,
    RegistrationCode,
)
from services.agent_service import AgentService


@pytest.fixture
def mock_db_service():
    """Create mock database service."""
    return MagicMock()


@pytest.fixture
def mock_settings_service():
    """Create mock settings service."""
    return MagicMock()


@pytest.fixture
def mock_agent_db():
    """Create mock agent database service."""
    return AsyncMock()


@pytest.fixture
def agent_service(mock_db_service, mock_settings_service, mock_agent_db):
    """Create agent service with mocked dependencies."""
    with patch.object(agent_module, "logger"):
        return AgentService(
            db_service=mock_db_service,
            settings_service=mock_settings_service,
            agent_db=mock_agent_db,
        )


@pytest.fixture
def sample_agent():
    """Create sample agent."""
    return Agent(
        id="agent-1",
        server_id="server-1",
        status=AgentStatus.CONNECTED,
        version="1.0.0",
        token_hash="abc123",
        registered_at=datetime.now(UTC),
        last_seen=datetime.now(UTC),
        config=AgentConfig(),
    )


@pytest.fixture
def sample_registration_code():
    """Create sample registration code."""
    return RegistrationCode(
        id="code-1",
        code="abc123456",
        agent_id="agent-1",
        used=False,
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        created_at=datetime.now(UTC),
    )


class TestAgentServiceInit:
    """Tests for AgentService initialization."""

    def test_init_with_dependencies(
        self, mock_db_service, mock_settings_service, mock_agent_db
    ):
        """Should initialize with provided dependencies."""
        with patch.object(agent_module, "logger"):
            service = AgentService(
                db_service=mock_db_service,
                settings_service=mock_settings_service,
                agent_db=mock_agent_db,
            )

            assert service.db_service is mock_db_service
            assert service.settings_service is mock_settings_service
            assert service._agent_db is mock_agent_db

    def test_init_creates_default_services(self):
        """Should create default services when not provided."""
        with (
            patch.object(agent_module, "logger"),
            patch.object(agent_module, "DatabaseService") as mock_db_class,
            patch.object(agent_module, "SettingsService") as mock_settings_class,
        ):
            mock_db_class.return_value = MagicMock()
            mock_settings_class.return_value = MagicMock()

            service = AgentService()

            mock_db_class.assert_called_once()
            mock_settings_class.assert_called_once()
            assert service._agent_db is None  # Lazy initialization


class TestGetAgentDb:
    """Tests for _get_agent_db method."""

    def test_get_agent_db_returns_existing(self, agent_service, mock_agent_db):
        """Should return existing agent_db if set."""
        result = agent_service._get_agent_db()

        assert result is mock_agent_db

    def test_get_agent_db_creates_new(self, mock_db_service, mock_settings_service):
        """Should create new agent_db if not set."""
        mock_db_service.db_path = "/tmp/test.db"

        with (
            patch.object(agent_module, "logger"),
            patch.dict(
                "sys.modules",
                {"services.database": MagicMock()},
            ),
        ):
            service = AgentService(
                db_service=mock_db_service,
                settings_service=mock_settings_service,
                agent_db=None,  # Not provided
            )

            # Patch the import that happens inside _get_agent_db
            with (
                patch("services.database.DatabaseConnection") as mock_conn_class,
                patch("services.database.AgentDatabaseService") as mock_db_class,
            ):
                mock_conn = MagicMock()
                mock_conn_class.return_value = mock_conn
                mock_agent_db_instance = MagicMock()
                mock_db_class.return_value = mock_agent_db_instance

                result = service._get_agent_db()

                mock_conn_class.assert_called_once_with(db_path="/tmp/test.db")
                mock_db_class.assert_called_once_with(mock_conn)
                assert result is mock_agent_db_instance


class TestHashToken:
    """Tests for _hash_token method."""

    def test_hash_token_returns_hex(self, agent_service):
        """Should return SHA256 hex hash."""
        result = agent_service._hash_token("test_token")

        assert len(result) == 64  # SHA256 hex length
        assert all(c in "0123456789abcdef" for c in result)

    def test_hash_token_deterministic(self, agent_service):
        """Should return same hash for same input."""
        hash1 = agent_service._hash_token("test_token")
        hash2 = agent_service._hash_token("test_token")

        assert hash1 == hash2

    def test_hash_token_different_input(self, agent_service):
        """Should return different hash for different input."""
        hash1 = agent_service._hash_token("token1")
        hash2 = agent_service._hash_token("token2")

        assert hash1 != hash2


class TestLogAgentEvent:
    """Tests for _log_agent_event method."""

    @pytest.mark.asyncio
    async def test_log_agent_event_calls_log_event(self, agent_service):
        """Should call log_event with correct parameters."""
        with patch.object(
            agent_module, "log_event", new_callable=AsyncMock
        ) as mock_log:
            await agent_service._log_agent_event(
                event_type="AGENT_INSTALLED",
                level="INFO",
                message="Agent installed",
                server_id="server-1",
                server_name="My Server",
                agent_id="agent-1",
                success=True,
                details={"version": "1.0.0"},
            )

            mock_log.assert_called_once()
            call_args = mock_log.call_args
            assert call_args[0][0] == "agent"
            assert call_args[0][1] == "INFO"
            assert "Agent installed" in call_args[0][2]


class TestGetServerName:
    """Tests for _get_server_name method."""

    @pytest.mark.asyncio
    async def test_get_server_name_found(self, agent_service, mock_db_service):
        """Should return server name when found."""
        mock_server = MagicMock()
        mock_server.name = "My Server"
        mock_db_service.get_server_by_id = AsyncMock(return_value=mock_server)

        result = await agent_service._get_server_name("server-1")

        assert result == "My Server"

    @pytest.mark.asyncio
    async def test_get_server_name_not_found(self, agent_service, mock_db_service):
        """Should return server_id as fallback."""
        mock_db_service.get_server_by_id = AsyncMock(return_value=None)

        result = await agent_service._get_server_name("server-1")

        assert result == "server-1"

    @pytest.mark.asyncio
    async def test_get_server_name_error(self, agent_service, mock_db_service):
        """Should return server_id on error."""
        mock_db_service.get_server_by_id = AsyncMock(
            side_effect=RuntimeError("DB error")
        )

        with patch.object(agent_module, "logger"):
            result = await agent_service._get_server_name("server-1")

        assert result == "server-1"


class TestGetAgentConfig:
    """Tests for _get_agent_config method."""

    @pytest.mark.asyncio
    async def test_get_agent_config_defaults(
        self, agent_service, mock_settings_service
    ):
        """Should return default config when no settings."""
        mock_settings_service.get_system_setting = AsyncMock(return_value=None)

        with patch.object(agent_module, "logger"):
            result = await agent_service._get_agent_config()

        assert isinstance(result, AgentConfig)

    @pytest.mark.asyncio
    async def test_get_agent_config_from_settings(
        self, agent_service, mock_settings_service
    ):
        """Should load config from settings."""
        mock_setting = MagicMock()
        mock_setting.setting_value = MagicMock()
        mock_setting.setting_value.get_parsed_value.return_value = 60

        mock_settings_service.get_system_setting = AsyncMock(return_value=mock_setting)

        with patch.object(agent_module, "logger"):
            result = await agent_service._get_agent_config()

        assert result.metrics_interval == 60

    @pytest.mark.asyncio
    async def test_get_agent_config_handles_error(
        self, agent_service, mock_settings_service
    ):
        """Should return defaults on error."""
        mock_settings_service.get_system_setting = AsyncMock(
            side_effect=RuntimeError("Error")
        )

        with patch.object(agent_module, "logger"):
            result = await agent_service._get_agent_config()

        assert isinstance(result, AgentConfig)


class TestCreateAgent:
    """Tests for create_agent method."""

    @pytest.mark.asyncio
    async def test_create_agent_new(self, agent_service, mock_agent_db, sample_agent):
        """Should create new agent."""
        mock_agent_db.get_agent_by_server.return_value = None
        mock_agent_db.create_agent.return_value = sample_agent
        mock_agent_db.create_registration_code.return_value = MagicMock(
            expires_at=datetime.now(UTC) + timedelta(hours=1)
        )

        with (
            patch.object(
                agent_service, "_get_server_name", new_callable=AsyncMock
            ) as mock_name,
            patch.object(agent_service, "_log_agent_event", new_callable=AsyncMock),
            patch.object(agent_module, "logger"),
        ):
            mock_name.return_value = "My Server"

            agent, code = await agent_service.create_agent("server-1")

            assert agent is sample_agent
            mock_agent_db.create_agent.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_agent_replaces_existing(
        self, agent_service, mock_agent_db, sample_agent
    ):
        """Should delete existing agent before creating new."""
        existing_agent = MagicMock()
        existing_agent.id = "old-agent"
        mock_agent_db.get_agent_by_server.return_value = existing_agent
        mock_agent_db.delete_agent.return_value = True
        mock_agent_db.create_agent.return_value = sample_agent
        mock_agent_db.create_registration_code.return_value = MagicMock(
            expires_at=datetime.now(UTC) + timedelta(hours=1)
        )

        with (
            patch.object(
                agent_service, "_get_server_name", new_callable=AsyncMock
            ) as mock_name,
            patch.object(agent_service, "_log_agent_event", new_callable=AsyncMock),
            patch.object(agent_module, "logger"),
        ):
            mock_name.return_value = "My Server"

            agent, code = await agent_service.create_agent("server-1")

            mock_agent_db.delete_agent.assert_called_once_with("old-agent")


class TestValidateRegistrationCode:
    """Tests for validate_registration_code method."""

    @pytest.mark.asyncio
    async def test_validate_code_valid(
        self, agent_service, mock_agent_db, sample_registration_code
    ):
        """Should return code when valid."""
        mock_agent_db.get_registration_code.return_value = sample_registration_code

        with patch.object(agent_module, "logger"):
            result = await agent_service.validate_registration_code("abc123")

        assert result is sample_registration_code

    @pytest.mark.asyncio
    async def test_validate_code_not_found(self, agent_service, mock_agent_db):
        """Should return None when code not found."""
        mock_agent_db.get_registration_code.return_value = None

        with patch.object(agent_module, "logger"):
            result = await agent_service.validate_registration_code("invalid")

        assert result is None

    @pytest.mark.asyncio
    async def test_validate_code_already_used(self, agent_service, mock_agent_db):
        """Should return None when code already used."""
        used_code = RegistrationCode(
            id="code-1",
            code="abc123",
            agent_id="agent-1",
            used=True,
            expires_at=datetime.now(UTC) + timedelta(hours=1),
            created_at=datetime.now(UTC),
        )
        mock_agent_db.get_registration_code.return_value = used_code

        with patch.object(agent_module, "logger"):
            result = await agent_service.validate_registration_code("abc123")

        assert result is None

    @pytest.mark.asyncio
    async def test_validate_code_expired(self, agent_service, mock_agent_db):
        """Should return None when code expired."""
        expired_code = RegistrationCode(
            id="code-1",
            code="abc123",
            agent_id="agent-1",
            used=False,
            expires_at=datetime.now(UTC) - timedelta(hours=1),  # Expired
            created_at=datetime.now(UTC) - timedelta(hours=2),
        )
        mock_agent_db.get_registration_code.return_value = expired_code

        with patch.object(agent_module, "logger"):
            result = await agent_service.validate_registration_code("abc123")

        assert result is None


class TestCompleteRegistration:
    """Tests for complete_registration method."""

    @pytest.mark.asyncio
    async def test_complete_registration_success(
        self, agent_service, mock_agent_db, sample_agent, sample_registration_code
    ):
        """Should complete registration successfully."""
        mock_agent_db.get_registration_code.return_value = sample_registration_code
        mock_agent_db.update_agent.return_value = sample_agent
        mock_agent_db.mark_code_used = AsyncMock()

        with (
            patch.object(
                agent_service,
                "validate_registration_code",
                new_callable=AsyncMock,
                return_value=sample_registration_code,
            ),
            patch.object(
                agent_service,
                "_get_agent_config",
                new_callable=AsyncMock,
                return_value=AgentConfig(),
            ),
            patch.object(
                agent_service, "_get_server_name", new_callable=AsyncMock
            ) as mock_name,
            patch.object(agent_service, "_log_agent_event", new_callable=AsyncMock),
            patch.object(agent_module, "logger"),
        ):
            mock_name.return_value = "My Server"

            result = await agent_service.complete_registration("abc123", "1.0.0")

            assert isinstance(result, AgentRegistrationResponse)
            assert result.agent_id == sample_agent.id
            mock_agent_db.mark_code_used.assert_called_once()

    @pytest.mark.asyncio
    async def test_complete_registration_invalid_code(
        self, agent_service, mock_agent_db
    ):
        """Should return None for invalid code."""
        with (
            patch.object(
                agent_service,
                "validate_registration_code",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch.object(agent_module, "logger"),
        ):
            result = await agent_service.complete_registration("invalid", "1.0.0")

        assert result is None

    @pytest.mark.asyncio
    async def test_complete_registration_update_fails(
        self, agent_service, mock_agent_db, sample_registration_code
    ):
        """Should return None when agent update fails."""
        mock_agent_db.update_agent.return_value = None

        with (
            patch.object(
                agent_service,
                "validate_registration_code",
                new_callable=AsyncMock,
                return_value=sample_registration_code,
            ),
            patch.object(
                agent_service,
                "_get_agent_config",
                new_callable=AsyncMock,
                return_value=AgentConfig(),
            ),
            patch.object(agent_module, "logger"),
        ):
            result = await agent_service.complete_registration("abc123", "1.0.0")

        assert result is None


class TestValidateToken:
    """Tests for validate_token method."""

    @pytest.mark.asyncio
    async def test_validate_token_success(
        self, agent_service, mock_agent_db, sample_agent
    ):
        """Should return agent for valid token."""
        mock_agent_db.get_agent_by_token_hash.return_value = sample_agent

        with patch.object(agent_module, "logger"):
            result = await agent_service.validate_token("valid_token")

        assert result is sample_agent

    @pytest.mark.asyncio
    async def test_validate_token_not_found(self, agent_service, mock_agent_db):
        """Should return None for invalid token."""
        mock_agent_db.get_agent_by_token_hash.return_value = None
        mock_agent_db.get_agent_by_pending_token_hash.return_value = None

        with patch.object(agent_module, "logger"):
            result = await agent_service.validate_token("invalid_token")

        assert result is None


class TestRevokeAgentToken:
    """Tests for revoke_agent_token method."""

    @pytest.mark.asyncio
    async def test_revoke_agent_token_success(
        self, agent_service, mock_agent_db, sample_agent
    ):
        """Should revoke token successfully."""
        mock_agent_db.update_agent.return_value = sample_agent

        with (
            patch.object(
                agent_service, "_get_server_name", new_callable=AsyncMock
            ) as mock_name,
            patch.object(agent_service, "_log_agent_event", new_callable=AsyncMock),
            patch.object(agent_module, "logger"),
        ):
            mock_name.return_value = "My Server"

            result = await agent_service.revoke_agent_token("agent-1")

        assert result is True

    @pytest.mark.asyncio
    async def test_revoke_agent_token_not_found(self, agent_service, mock_agent_db):
        """Should return False when agent not found."""
        mock_agent_db.update_agent.return_value = None

        with patch.object(agent_module, "logger"):
            result = await agent_service.revoke_agent_token("unknown")

        assert result is False


class TestGetAgentByServer:
    """Tests for get_agent_by_server method."""

    @pytest.mark.asyncio
    async def test_get_agent_by_server_found(
        self, agent_service, mock_agent_db, sample_agent
    ):
        """Should return agent when found."""
        mock_agent_db.get_agent_by_server.return_value = sample_agent

        result = await agent_service.get_agent_by_server("server-1")

        assert result is sample_agent

    @pytest.mark.asyncio
    async def test_get_agent_by_server_not_found(self, agent_service, mock_agent_db):
        """Should return None when not found."""
        mock_agent_db.get_agent_by_server.return_value = None

        result = await agent_service.get_agent_by_server("unknown")

        assert result is None


class TestListAllAgents:
    """Tests for list_all_agents method."""

    @pytest.mark.asyncio
    async def test_list_all_agents(self, agent_service, mock_agent_db, sample_agent):
        """Should return list of agents."""
        mock_agent_db.list_all_agents.return_value = [sample_agent]

        result = await agent_service.list_all_agents()

        assert len(result) == 1
        assert result[0] is sample_agent


class TestDeleteAgent:
    """Tests for delete_agent method."""

    @pytest.mark.asyncio
    async def test_delete_agent_success(
        self, agent_service, mock_agent_db, sample_agent
    ):
        """Should delete agent successfully."""
        mock_agent_db.get_agent.return_value = sample_agent
        mock_agent_db.delete_agent.return_value = True

        with (
            patch.object(
                agent_service, "_get_server_name", new_callable=AsyncMock
            ) as mock_name,
            patch.object(agent_service, "_log_agent_event", new_callable=AsyncMock),
            patch.object(agent_module, "logger"),
        ):
            mock_name.return_value = "My Server"

            result = await agent_service.delete_agent("agent-1")

        assert result is True

    @pytest.mark.asyncio
    async def test_delete_agent_not_found(self, agent_service, mock_agent_db):
        """Should return False when deletion fails."""
        mock_agent_db.get_agent.return_value = None
        mock_agent_db.delete_agent.return_value = False

        with patch.object(agent_module, "logger"):
            result = await agent_service.delete_agent("unknown")

        assert result is False


class TestRegisterAgent:
    """Tests for register_agent method (WebSocket API)."""

    @pytest.mark.asyncio
    async def test_register_agent_success(self, agent_service, sample_agent):
        """Should register agent successfully."""
        response = AgentRegistrationResponse(
            agent_id=sample_agent.id,
            server_id=sample_agent.server_id,
            token="token123",
            config=AgentConfig(),
        )

        with patch.object(
            agent_service,
            "complete_registration",
            new_callable=AsyncMock,
            return_value=response,
        ):
            result = await agent_service.register_agent("abc123", "1.0.0")

        assert result is not None
        assert result[0] == sample_agent.id
        assert result[1] == "token123"

    @pytest.mark.asyncio
    async def test_register_agent_failure(self, agent_service):
        """Should return None on failure."""
        with patch.object(
            agent_service,
            "complete_registration",
            new_callable=AsyncMock,
            return_value=None,
        ):
            result = await agent_service.register_agent("invalid", "1.0.0")

        assert result is None

    @pytest.mark.asyncio
    async def test_register_agent_default_version(self, agent_service, sample_agent):
        """Should use 'unknown' as default version."""
        response = AgentRegistrationResponse(
            agent_id=sample_agent.id,
            server_id=sample_agent.server_id,
            token="token123",
            config=AgentConfig(),
        )

        with patch.object(
            agent_service,
            "complete_registration",
            new_callable=AsyncMock,
            return_value=response,
        ) as mock_complete:
            await agent_service.register_agent("abc123")

            mock_complete.assert_called_once_with("abc123", "unknown")


class TestAuthenticateAgent:
    """Tests for authenticate_agent method (WebSocket API)."""

    @pytest.mark.asyncio
    async def test_authenticate_agent_success(
        self, agent_service, mock_agent_db, sample_agent
    ):
        """Should authenticate agent successfully."""
        mock_agent_db.update_agent.return_value = sample_agent

        with (
            patch.object(
                agent_service,
                "validate_token",
                new_callable=AsyncMock,
                return_value=sample_agent,
            ),
            patch.object(
                agent_service,
                "_get_agent_config",
                new_callable=AsyncMock,
                return_value=AgentConfig(),
            ),
        ):
            result = await agent_service.authenticate_agent("valid_token", "1.0.0")

        assert result is not None
        assert result[0] == sample_agent.id
        assert result[2] == sample_agent.server_id

    @pytest.mark.asyncio
    async def test_authenticate_agent_invalid_token(self, agent_service):
        """Should return None for invalid token."""
        with patch.object(
            agent_service,
            "validate_token",
            new_callable=AsyncMock,
            return_value=None,
        ):
            result = await agent_service.authenticate_agent("invalid_token")

        assert result is None


class TestResetStaleAgentStatuses:
    """Tests for reset_stale_agent_statuses method."""

    @pytest.mark.asyncio
    async def test_reset_connected_agents(self, agent_service, mock_agent_db):
        """Should reset CONNECTED agents to DISCONNECTED."""
        connected_agent = Agent(
            id="agent-1",
            server_id="server-1",
            status=AgentStatus.CONNECTED,
            version="1.0.0",
            config=AgentConfig(),
        )
        mock_agent_db.list_all_agents.return_value = [connected_agent]
        mock_agent_db.update_agent.return_value = connected_agent

        with patch.object(agent_module, "logger"):
            result = await agent_service.reset_stale_agent_statuses()

        assert result == 1
        mock_agent_db.update_agent.assert_called_once()

    @pytest.mark.asyncio
    async def test_reset_stale_pending_agents(self, agent_service, mock_agent_db):
        """Should reset stale PENDING agents."""
        pending_agent = Agent(
            id="agent-1",
            server_id="server-1",
            status=AgentStatus.PENDING,
            version="1.0.0",
            registered_at=datetime.now(UTC) - timedelta(minutes=15),  # Stale
            config=AgentConfig(),
        )
        mock_agent_db.list_all_agents.return_value = [pending_agent]
        mock_agent_db.update_agent.return_value = pending_agent

        with patch.object(agent_module, "logger"):
            result = await agent_service.reset_stale_agent_statuses()

        assert result == 1

    @pytest.mark.asyncio
    async def test_reset_pending_no_timestamp(self, agent_service, mock_agent_db):
        """Should reset PENDING agents with no timestamp."""
        pending_agent = Agent(
            id="agent-1",
            server_id="server-1",
            status=AgentStatus.PENDING,
            version="1.0.0",
            registered_at=None,
            last_seen=None,
            config=AgentConfig(),
        )
        mock_agent_db.list_all_agents.return_value = [pending_agent]
        mock_agent_db.update_agent.return_value = pending_agent

        with patch.object(agent_module, "logger"):
            result = await agent_service.reset_stale_agent_statuses()

        assert result == 1

    @pytest.mark.asyncio
    async def test_no_reset_fresh_pending(self, agent_service, mock_agent_db):
        """Should not reset fresh PENDING agents."""
        fresh_pending = Agent(
            id="agent-1",
            server_id="server-1",
            status=AgentStatus.PENDING,
            version="1.0.0",
            registered_at=datetime.now(UTC) - timedelta(minutes=5),  # Fresh (< 10 min)
            config=AgentConfig(),
        )
        mock_agent_db.list_all_agents.return_value = [fresh_pending]

        with patch.object(agent_module, "logger"):
            result = await agent_service.reset_stale_agent_statuses()

        assert result == 0
        mock_agent_db.update_agent.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_reset_disconnected(self, agent_service, mock_agent_db):
        """Should not reset DISCONNECTED agents."""
        disconnected_agent = Agent(
            id="agent-1",
            server_id="server-1",
            status=AgentStatus.DISCONNECTED,
            version="1.0.0",
            config=AgentConfig(),
        )
        mock_agent_db.list_all_agents.return_value = [disconnected_agent]

        with patch.object(agent_module, "logger"):
            result = await agent_service.reset_stale_agent_statuses()

        assert result == 0
        mock_agent_db.update_agent.assert_not_called()

    @pytest.mark.asyncio
    async def test_reset_multiple_agents(self, agent_service, mock_agent_db):
        """Should reset multiple stale agents."""
        connected = Agent(
            id="agent-1",
            server_id="server-1",
            status=AgentStatus.CONNECTED,
            version="1.0.0",
            config=AgentConfig(),
        )
        stale_pending = Agent(
            id="agent-2",
            server_id="server-2",
            status=AgentStatus.PENDING,
            version="1.0.0",
            registered_at=datetime.now(UTC) - timedelta(minutes=15),
            config=AgentConfig(),
        )
        mock_agent_db.list_all_agents.return_value = [connected, stale_pending]
        mock_agent_db.update_agent.return_value = MagicMock()

        with patch.object(agent_module, "logger"):
            result = await agent_service.reset_stale_agent_statuses()

        assert result == 2
        assert mock_agent_db.update_agent.call_count == 2


class TestInitiateRotation:
    """Tests for initiate_rotation method."""

    @pytest.mark.asyncio
    async def test_initiate_rotation_success(
        self, agent_service, mock_agent_db, sample_agent
    ):
        """Should generate new token and store pending hash."""
        mock_agent_db.get_agent.return_value = sample_agent
        mock_agent_db.update_agent.return_value = sample_agent

        with (
            patch.object(agent_module, "logger"),
            patch.object(
                agent_service, "_get_server_name", new_callable=AsyncMock
            ) as mock_name,
            patch.object(agent_service, "_log_agent_event", new_callable=AsyncMock),
        ):
            mock_name.return_value = "Test Server"
            result = await agent_service.initiate_rotation("agent-1")

        assert result is not None
        assert len(result) > 20  # token_urlsafe(32) produces ~43 chars
        mock_agent_db.update_agent.assert_called_once()

    @pytest.mark.asyncio
    async def test_initiate_rotation_agent_not_found(
        self, agent_service, mock_agent_db
    ):
        """Should return None if agent doesn't exist."""
        mock_agent_db.get_agent.return_value = None

        with patch.object(agent_module, "logger"):
            result = await agent_service.initiate_rotation("unknown")

        assert result is None

    @pytest.mark.asyncio
    async def test_initiate_rotation_no_token(self, agent_service, mock_agent_db):
        """Should return None if agent has no current token."""
        agent_no_token = Agent(
            id="agent-1",
            server_id="server-1",
            status=AgentStatus.PENDING,
            token_hash=None,
        )
        mock_agent_db.get_agent.return_value = agent_no_token

        with patch.object(agent_module, "logger"):
            result = await agent_service.initiate_rotation("agent-1")

        assert result is None

    @pytest.mark.asyncio
    async def test_initiate_rotation_already_pending(
        self, agent_service, mock_agent_db
    ):
        """Should return None if rotation already in progress."""
        agent_with_pending = Agent(
            id="agent-1",
            server_id="server-1",
            status=AgentStatus.CONNECTED,
            token_hash="current_hash",
            pending_token_hash="pending_hash",
        )
        mock_agent_db.get_agent.return_value = agent_with_pending

        with patch.object(agent_module, "logger"):
            result = await agent_service.initiate_rotation("agent-1")

        assert result is None


class TestCompleteRotation:
    """Tests for complete_rotation method."""

    @pytest.mark.asyncio
    async def test_complete_rotation_success(self, agent_service, mock_agent_db):
        """Should promote pending token to current."""
        agent_with_pending = Agent(
            id="agent-1",
            server_id="server-1",
            status=AgentStatus.CONNECTED,
            token_hash="old_hash",
            pending_token_hash="new_hash",
        )
        mock_agent_db.get_agent.return_value = agent_with_pending
        mock_agent_db.update_agent.return_value = agent_with_pending

        with (
            patch.object(agent_module, "logger"),
            patch.object(
                agent_service, "_get_token_rotation_settings", new_callable=AsyncMock
            ) as mock_settings,
            patch.object(
                agent_service, "_get_server_name", new_callable=AsyncMock
            ) as mock_name,
            patch.object(agent_service, "_log_agent_event", new_callable=AsyncMock),
        ):
            mock_settings.return_value = (7, 5)
            mock_name.return_value = "Test Server"
            result = await agent_service.complete_rotation("agent-1")

        assert result is True
        # Verify update was called with pending promoted to current
        call_args = mock_agent_db.update_agent.call_args
        update_data = call_args[0][1]
        assert update_data.token_hash == "new_hash"
        assert update_data.pending_token_hash is None

    @pytest.mark.asyncio
    async def test_complete_rotation_no_pending(
        self, agent_service, mock_agent_db, sample_agent
    ):
        """Should return False if no pending token."""
        sample_agent.pending_token_hash = None
        mock_agent_db.get_agent.return_value = sample_agent

        with patch.object(agent_module, "logger"):
            result = await agent_service.complete_rotation("agent-1")

        assert result is False

    @pytest.mark.asyncio
    async def test_complete_rotation_agent_not_found(
        self, agent_service, mock_agent_db
    ):
        """Should return False if agent not found."""
        mock_agent_db.get_agent.return_value = None

        with patch.object(agent_module, "logger"):
            result = await agent_service.complete_rotation("unknown")

        assert result is False


class TestCancelRotation:
    """Tests for cancel_rotation method."""

    @pytest.mark.asyncio
    async def test_cancel_rotation_success(
        self, agent_service, mock_agent_db, sample_agent
    ):
        """Should clear pending token hash."""
        mock_agent_db.get_agent.return_value = sample_agent
        mock_agent_db.update_agent.return_value = sample_agent

        with (
            patch.object(agent_module, "logger"),
            patch.object(
                agent_service, "_get_server_name", new_callable=AsyncMock
            ) as mock_name,
            patch.object(agent_service, "_log_agent_event", new_callable=AsyncMock),
        ):
            mock_name.return_value = "Test Server"
            result = await agent_service.cancel_rotation("agent-1")

        assert result is True
        call_args = mock_agent_db.update_agent.call_args
        update_data = call_args[0][1]
        assert update_data.pending_token_hash is None

    @pytest.mark.asyncio
    async def test_cancel_rotation_agent_not_found(self, agent_service, mock_agent_db):
        """Should return False if agent not found."""
        mock_agent_db.get_agent.return_value = None

        with patch.object(agent_module, "logger"):
            result = await agent_service.cancel_rotation("unknown")

        assert result is False


class TestGetAgentsNeedingRotation:
    """Tests for get_agents_needing_rotation method."""

    @pytest.mark.asyncio
    async def test_get_agents_needing_rotation(
        self, agent_service, mock_agent_db, sample_agent
    ):
        """Should return agents with expired tokens."""
        mock_agent_db.get_agents_with_expiring_tokens.return_value = [sample_agent]

        result = await agent_service.get_agents_needing_rotation()

        assert len(result) == 1
        assert result[0].id == sample_agent.id


class TestValidateTokenWithPending:
    """Tests for validate_token with pending token rotation."""

    @pytest.mark.asyncio
    async def test_validate_pending_token_completes_rotation(
        self, agent_service, mock_agent_db
    ):
        """Should complete rotation when agent uses pending token."""
        agent_with_pending = Agent(
            id="agent-1",
            server_id="server-1",
            status=AgentStatus.CONNECTED,
            token_hash="old_hash",
            pending_token_hash="new_hash",
        )
        # First call returns None (not matching current token)
        # Second call returns agent (matching pending token)
        mock_agent_db.get_agent_by_token_hash.return_value = None
        mock_agent_db.get_agent_by_pending_token_hash.return_value = agent_with_pending
        mock_agent_db.get_agent.return_value = agent_with_pending
        mock_agent_db.update_agent.return_value = agent_with_pending

        with (
            patch.object(agent_module, "logger"),
            patch.object(
                agent_service, "complete_rotation", new_callable=AsyncMock
            ) as mock_complete,
        ):
            mock_complete.return_value = True
            result = await agent_service.validate_token("new_token")

        assert result is not None
        mock_complete.assert_called_once_with("agent-1")
