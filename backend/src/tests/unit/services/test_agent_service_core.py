"""
Unit tests for services/agent_service.py - Core operations.

Tests initialization, token hashing, config loading, server name lookup,
and event logging.
"""

import hashlib
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.agent import (
    Agent,
    AgentConfig,
    AgentStatus,
    RegistrationCode,
)
from services.agent_service import AgentService


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


class TestAgentServiceInit:
    """Tests for AgentService initialization."""

    def test_init_with_provided_services(
        self, mock_db_service, mock_settings_service, mock_agent_db
    ):
        """AgentService should use provided services."""
        with patch("services.agent_service.logger"):
            service = AgentService(
                db_service=mock_db_service,
                settings_service=mock_settings_service,
                agent_db=mock_agent_db,
            )
        assert service.db_service is mock_db_service
        assert service.settings_service is mock_settings_service
        assert service._agent_db is mock_agent_db

    def test_init_creates_default_services(self):
        """AgentService should create default services if not provided."""
        with (
            patch("services.agent_service.logger"),
            patch("services.agent_service.DatabaseService") as MockDB,
            patch("services.agent_service.SettingsService") as MockSettings,
        ):
            MockDB.return_value = MagicMock()
            MockSettings.return_value = MagicMock()
            service = AgentService()
            assert service.db_service is MockDB.return_value
            assert service.settings_service is MockSettings.return_value
            assert service._agent_db is None

    def test_init_logs_message(self, mock_db_service, mock_settings_service):
        """AgentService should log initialization."""
        with patch("services.agent_service.logger") as mock_logger:
            AgentService(
                db_service=mock_db_service,
                settings_service=mock_settings_service,
            )
            mock_logger.info.assert_called_with("Agent service initialized")


class TestGetAgentDb:
    """Tests for _get_agent_db method."""

    def test_get_agent_db_returns_injected(
        self, mock_db_service, mock_settings_service, mock_agent_db
    ):
        """_get_agent_db should return injected agent_db."""
        with patch("services.agent_service.logger"):
            service = AgentService(
                db_service=mock_db_service,
                settings_service=mock_settings_service,
                agent_db=mock_agent_db,
            )
        result = service._get_agent_db()
        assert result is mock_agent_db

    def test_get_agent_db_creates_lazily(self, mock_db_service, mock_settings_service):
        """_get_agent_db should create agent_db lazily if not provided."""
        with patch("services.agent_service.logger"):
            service = AgentService(
                db_service=mock_db_service,
                settings_service=mock_settings_service,
                agent_db=None,
            )

        # Patch at module level where imports happen inside the method
        with (
            patch("services.database.DatabaseConnection") as MockConn,
            patch("services.database.AgentDatabaseService") as MockAgentDB,
        ):
            MockConn.return_value = MagicMock()
            MockAgentDB.return_value = MagicMock()

            result = service._get_agent_db()

            MockConn.assert_called_once_with(db_path=mock_db_service.db_path)
            MockAgentDB.assert_called_once()
            assert result is MockAgentDB.return_value


class TestHashToken:
    """Tests for _hash_token method."""

    def test_hash_token_returns_sha256(self, agent_service):
        """_hash_token should return SHA256 hash of token."""
        token = "test-token-123"
        expected = hashlib.sha256(token.encode("utf-8")).hexdigest()

        result = agent_service._hash_token(token)

        assert result == expected

    def test_hash_token_same_input_same_output(self, agent_service):
        """_hash_token should return same hash for same input."""
        token = "consistent-token"

        result1 = agent_service._hash_token(token)
        result2 = agent_service._hash_token(token)

        assert result1 == result2

    def test_hash_token_different_for_different_input(self, agent_service):
        """_hash_token should return different hash for different input."""
        result1 = agent_service._hash_token("token-a")
        result2 = agent_service._hash_token("token-b")

        assert result1 != result2


class TestLogAgentEvent:
    """Tests for _log_agent_event method."""

    @pytest.mark.asyncio
    async def test_log_agent_event_calls_log_event(self, agent_service):
        """_log_agent_event should call log_event with correct params."""
        with patch("services.agent_service.log_event", new_callable=AsyncMock) as mock:
            await agent_service._log_agent_event(
                event_type="AGENT_INSTALLED",
                level="INFO",
                message="Test message",
                server_id="srv-123",
                server_name="my-server",
                agent_id="agent-456",
                success=True,
                details={"key": "value"},
            )

            mock.assert_called_once_with(
                "agent",
                "INFO",
                "Test message",
                ["agent", "lifecycle"],
                {
                    "event_type": "AGENT_INSTALLED",
                    "server_id": "srv-123",
                    "server_name": "my-server",
                    "agent_id": "agent-456",
                    "success": True,
                    "details": {"key": "value"},
                },
            )

    @pytest.mark.asyncio
    async def test_log_agent_event_default_details(self, agent_service):
        """_log_agent_event should use empty dict for default details."""
        with patch("services.agent_service.log_event", new_callable=AsyncMock) as mock:
            await agent_service._log_agent_event(
                event_type="AGENT_CONNECTED",
                level="INFO",
                message="Connected",
                server_id="srv-123",
            )

            call_args = mock.call_args[0]
            assert call_args[4]["details"] == {}


class TestGetServerName:
    """Tests for _get_server_name method."""

    @pytest.mark.asyncio
    async def test_get_server_name_found(self, agent_service, mock_db_service):
        """_get_server_name should return server name when found."""
        mock_server = MagicMock()
        mock_server.name = "production-server"
        mock_db_service.get_server_by_id = AsyncMock(return_value=mock_server)

        with patch("services.agent_service.logger"):
            result = await agent_service._get_server_name("srv-123")

        assert result == "production-server"

    @pytest.mark.asyncio
    async def test_get_server_name_not_found(self, agent_service, mock_db_service):
        """_get_server_name should return server_id when not found."""
        mock_db_service.get_server_by_id = AsyncMock(return_value=None)

        with patch("services.agent_service.logger"):
            result = await agent_service._get_server_name("srv-123")

        assert result == "srv-123"

    @pytest.mark.asyncio
    async def test_get_server_name_server_no_name(self, agent_service, mock_db_service):
        """_get_server_name should return server_id when server has no name."""
        mock_server = MagicMock()
        mock_server.name = None
        mock_db_service.get_server_by_id = AsyncMock(return_value=mock_server)

        with patch("services.agent_service.logger"):
            result = await agent_service._get_server_name("srv-123")

        assert result == "srv-123"

    @pytest.mark.asyncio
    async def test_get_server_name_error_returns_fallback(
        self, agent_service, mock_db_service
    ):
        """_get_server_name should return server_id on error."""
        mock_db_service.get_server_by_id = AsyncMock(side_effect=Exception("DB error"))

        with patch("services.agent_service.logger") as mock_logger:
            result = await agent_service._get_server_name("srv-123")

        assert result == "srv-123"
        mock_logger.warning.assert_called()


class TestGetAgentConfig:
    """Tests for _get_agent_config method."""

    @pytest.mark.asyncio
    async def test_get_agent_config_default_values(
        self, agent_service, mock_settings_service
    ):
        """_get_agent_config should return defaults when no settings."""
        mock_settings_service.get_system_setting = AsyncMock(return_value=None)

        with patch("services.agent_service.logger"):
            result = await agent_service._get_agent_config()

        assert isinstance(result, AgentConfig)
        assert result.metrics_interval == 30
        assert result.health_interval == 60
        assert result.reconnect_timeout == 30

    @pytest.mark.asyncio
    async def test_get_agent_config_from_settings(
        self, agent_service, mock_settings_service
    ):
        """_get_agent_config should load values from settings."""

        def create_setting(value):
            setting = MagicMock()
            setting.setting_value = MagicMock()
            setting.setting_value.get_parsed_value = MagicMock(return_value=value)
            return setting

        async def mock_get_setting(key):
            settings_map = {
                "agent.metrics_interval": create_setting(45),
                "agent.health_interval": create_setting(90),
                "agent.reconnect_timeout": create_setting(60),
            }
            return settings_map.get(key)

        mock_settings_service.get_system_setting = mock_get_setting

        with patch("services.agent_service.logger"):
            result = await agent_service._get_agent_config()

        assert result.metrics_interval == 45
        assert result.health_interval == 90
        assert result.reconnect_timeout == 60

    @pytest.mark.asyncio
    async def test_get_agent_config_partial_settings(
        self, agent_service, mock_settings_service
    ):
        """_get_agent_config should use defaults for missing settings."""

        def create_setting(value):
            setting = MagicMock()
            setting.setting_value = MagicMock()
            setting.setting_value.get_parsed_value = MagicMock(return_value=value)
            return setting

        async def mock_get_setting(key):
            if key == "agent.metrics_interval":
                return create_setting(45)
            return None

        mock_settings_service.get_system_setting = mock_get_setting

        with patch("services.agent_service.logger"):
            result = await agent_service._get_agent_config()

        assert result.metrics_interval == 45
        assert result.health_interval == 60  # Default
        assert result.reconnect_timeout == 30  # Default

    @pytest.mark.asyncio
    async def test_get_agent_config_error_returns_defaults(
        self, agent_service, mock_settings_service
    ):
        """_get_agent_config should return defaults on error."""
        mock_settings_service.get_system_setting = AsyncMock(
            side_effect=Exception("Settings error")
        )

        with patch("services.agent_service.logger") as mock_logger:
            result = await agent_service._get_agent_config()

        assert isinstance(result, AgentConfig)
        mock_logger.warning.assert_called()

    @pytest.mark.asyncio
    async def test_get_agent_config_setting_no_value(
        self, agent_service, mock_settings_service
    ):
        """_get_agent_config should handle settings with no value."""
        setting_no_value = MagicMock()
        setting_no_value.setting_value = None
        mock_settings_service.get_system_setting = AsyncMock(
            return_value=setting_no_value
        )

        with patch("services.agent_service.logger"):
            result = await agent_service._get_agent_config()

        # Should use defaults since setting_value is None
        assert result.metrics_interval == 30


class TestGetAgentByServer:
    """Tests for get_agent_by_server method."""

    @pytest.mark.asyncio
    async def test_get_agent_by_server_found(
        self, agent_service, mock_agent_db, sample_agent
    ):
        """get_agent_by_server should return agent when found."""
        mock_agent_db.get_agent_by_server = AsyncMock(return_value=sample_agent)

        result = await agent_service.get_agent_by_server("server-456")

        assert result is sample_agent
        mock_agent_db.get_agent_by_server.assert_called_once_with("server-456")

    @pytest.mark.asyncio
    async def test_get_agent_by_server_not_found(self, agent_service, mock_agent_db):
        """get_agent_by_server should return None when not found."""
        mock_agent_db.get_agent_by_server = AsyncMock(return_value=None)

        result = await agent_service.get_agent_by_server("nonexistent")

        assert result is None


class TestListAllAgents:
    """Tests for list_all_agents method."""

    @pytest.mark.asyncio
    async def test_list_all_agents_returns_list(
        self, agent_service, mock_agent_db, sample_agent
    ):
        """list_all_agents should return list of agents."""
        mock_agent_db.list_all_agents = AsyncMock(return_value=[sample_agent])

        result = await agent_service.list_all_agents()

        assert len(result) == 1
        assert result[0] is sample_agent

    @pytest.mark.asyncio
    async def test_list_all_agents_empty(self, agent_service, mock_agent_db):
        """list_all_agents should return empty list when no agents."""
        mock_agent_db.list_all_agents = AsyncMock(return_value=[])

        result = await agent_service.list_all_agents()

        assert result == []
