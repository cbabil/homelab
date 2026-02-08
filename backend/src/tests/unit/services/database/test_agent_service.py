"""
Unit tests for services/database/agent_service.py.

Tests AgentDatabaseService methods.
"""

from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.agent import AgentConfig, AgentCreate, AgentStatus, AgentUpdate
from services.database.agent_service import AgentDatabaseService


@pytest.fixture
def mock_connection():
    """Create mock DatabaseConnection."""
    return MagicMock()


@pytest.fixture
def service(mock_connection):
    """Create AgentDatabaseService instance."""
    with patch("services.database.agent_service.RegistrationCodeDatabaseService"):
        return AgentDatabaseService(mock_connection)


def create_mock_context(mock_conn):
    """Create async context manager for database connection."""

    @asynccontextmanager
    async def context():
        yield mock_conn

    return context()


@pytest.fixture
def sample_agent_row():
    """Create sample agent row from database."""
    now = datetime.now(UTC)
    return {
        "id": "agent-123",
        "server_id": "server-456",
        "token_hash": "hash123",
        "version": "1.0.0",
        "status": "connected",
        "last_seen": now.isoformat(),
        "registered_at": now.isoformat(),
        "config": '{"metrics_interval": 30}',
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }


class TestAgentDatabaseServiceInit:
    """Tests for AgentDatabaseService initialization."""

    def test_init_stores_connection(self, mock_connection):
        """Service should store connection reference."""
        with patch("services.database.agent_service.RegistrationCodeDatabaseService"):
            service = AgentDatabaseService(mock_connection)
        assert service._conn is mock_connection

    def test_init_creates_registration_code_service(self, mock_connection):
        """Service should create RegistrationCodeDatabaseService."""
        with patch(
            "services.database.agent_service.RegistrationCodeDatabaseService"
        ) as mock_reg:
            AgentDatabaseService(mock_connection)
        mock_reg.assert_called_once_with(mock_connection)


class TestRowToAgent:
    """Tests for _row_to_agent method."""

    def test_row_to_agent_basic(self, service, sample_agent_row):
        """_row_to_agent should convert row to Agent model."""
        with patch("services.database.agent_service.logger"):
            result = service._row_to_agent(sample_agent_row)
        assert result.id == "agent-123"
        assert result.server_id == "server-456"
        assert result.status == AgentStatus.CONNECTED

    def test_row_to_agent_with_config(self, service, sample_agent_row):
        """_row_to_agent should parse config JSON."""
        with patch("services.database.agent_service.logger"):
            result = service._row_to_agent(sample_agent_row)
        assert result.config is not None
        assert result.config.metrics_interval == 30

    def test_row_to_agent_invalid_config(self, service, sample_agent_row):
        """_row_to_agent should handle invalid config JSON."""
        row = dict(sample_agent_row)
        row["config"] = "invalid json"
        with patch("services.database.agent_service.logger"):
            result = service._row_to_agent(row)
        assert result.config is None

    def test_row_to_agent_null_config(self, service, sample_agent_row):
        """_row_to_agent should handle null config."""
        row = dict(sample_agent_row)
        row["config"] = None
        with patch("services.database.agent_service.logger"):
            result = service._row_to_agent(row)
        assert result.config is None

    def test_row_to_agent_null_dates(self, service, sample_agent_row):
        """_row_to_agent should handle null dates."""
        row = dict(sample_agent_row)
        row["last_seen"] = None
        row["registered_at"] = None
        row["created_at"] = None
        row["updated_at"] = None
        with patch("services.database.agent_service.logger"):
            result = service._row_to_agent(row)
        assert result.last_seen is None
        assert result.registered_at is None

    def test_row_to_agent_null_status(self, service, sample_agent_row):
        """_row_to_agent should default to PENDING for null status."""
        row = dict(sample_agent_row)
        row["status"] = None
        with patch("services.database.agent_service.logger"):
            result = service._row_to_agent(row)
        assert result.status == AgentStatus.PENDING


class TestCreateAgent:
    """Tests for create_agent method."""

    @pytest.mark.asyncio
    async def test_create_agent_success(
        self, service, mock_connection, sample_agent_row
    ):
        """create_agent should return created Agent."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=sample_agent_row)
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with (
            patch("services.database.agent_service.logger"),
            patch("services.database.agent_service.uuid4") as mock_uuid,
        ):
            mock_uuid.return_value = MagicMock()
            mock_uuid.return_value.__str__ = lambda s: "agent-123"
            result = await service.create_agent(AgentCreate(server_id="server-456"))

        assert result is not None
        mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_agent_logs(self, service, mock_connection, sample_agent_row):
        """create_agent should log creation."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=sample_agent_row)
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.agent_service.logger") as mock_log:
            await service.create_agent(AgentCreate(server_id="server-456"))
        mock_log.info.assert_called()


class TestGetAgent:
    """Tests for get_agent method."""

    @pytest.mark.asyncio
    async def test_get_agent_found(self, service, mock_connection, sample_agent_row):
        """get_agent should return agent when found."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=sample_agent_row)
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.agent_service.logger"):
            result = await service.get_agent("agent-123")

        assert result is not None
        assert result.id == "agent-123"

    @pytest.mark.asyncio
    async def test_get_agent_not_found(self, service, mock_connection):
        """get_agent should return None when not found."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=None)
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.agent_service.logger"):
            result = await service.get_agent("nonexistent")

        assert result is None


class TestGetAgentByServer:
    """Tests for get_agent_by_server method."""

    @pytest.mark.asyncio
    async def test_get_agent_by_server_found(
        self, service, mock_connection, sample_agent_row
    ):
        """get_agent_by_server should return agent when found."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=sample_agent_row)
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.agent_service.logger"):
            result = await service.get_agent_by_server("server-456")

        assert result is not None
        assert result.server_id == "server-456"

    @pytest.mark.asyncio
    async def test_get_agent_by_server_not_found(self, service, mock_connection):
        """get_agent_by_server should return None when not found."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=None)
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.agent_service.logger"):
            result = await service.get_agent_by_server("unknown")

        assert result is None


class TestListAllAgents:
    """Tests for list_all_agents method."""

    @pytest.mark.asyncio
    async def test_list_all_agents(self, service, mock_connection, sample_agent_row):
        """list_all_agents should return list of agents."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(
            return_value=[sample_agent_row, sample_agent_row]
        )
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.agent_service.logger"):
            result = await service.list_all_agents()

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_list_all_agents_empty(self, service, mock_connection):
        """list_all_agents should return empty list when no agents."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=[])
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.agent_service.logger"):
            result = await service.list_all_agents()

        assert result == []


class TestGetAgentByTokenHash:
    """Tests for get_agent_by_token_hash method."""

    @pytest.mark.asyncio
    async def test_get_agent_by_token_hash_found(
        self, service, mock_connection, sample_agent_row
    ):
        """get_agent_by_token_hash should return agent when found."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=sample_agent_row)
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.agent_service.logger"):
            result = await service.get_agent_by_token_hash("hash123")

        assert result is not None

    @pytest.mark.asyncio
    async def test_get_agent_by_token_hash_not_found(self, service, mock_connection):
        """get_agent_by_token_hash should return None when not found."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=None)
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.agent_service.logger"):
            result = await service.get_agent_by_token_hash("unknown")

        assert result is None


class TestUpdateAgent:
    """Tests for update_agent method."""

    @pytest.mark.asyncio
    async def test_update_agent_success(
        self, service, mock_connection, sample_agent_row
    ):
        """update_agent should return updated agent."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 1
        mock_cursor.fetchone = AsyncMock(return_value=sample_agent_row)
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.agent_service.logger"):
            result = await service.update_agent(
                "agent-123", AgentUpdate(version="2.0.0")
            )

        assert result is not None
        mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_agent_empty_updates(
        self, service, mock_connection, sample_agent_row
    ):
        """update_agent should return current agent when no updates."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=sample_agent_row)
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.agent_service.logger"):
            result = await service.update_agent("agent-123", AgentUpdate())

        assert result is not None

    @pytest.mark.asyncio
    async def test_update_agent_not_found(self, service, mock_connection):
        """update_agent should return None when agent not found."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 0
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.agent_service.logger"):
            result = await service.update_agent("unknown", AgentUpdate(version="2.0.0"))

        assert result is None


class TestSerializeUpdateFields:
    """Tests for _serialize_update_fields method."""

    def test_serialize_status_enum(self, service):
        """_serialize_update_fields should convert status enum to value."""
        updates = {"status": AgentStatus.CONNECTED}
        service._serialize_update_fields(updates)
        assert updates["status"] == "connected"

    def test_serialize_status_string(self, service):
        """_serialize_update_fields should keep string status as-is."""
        updates = {"status": "connected"}
        service._serialize_update_fields(updates)
        assert updates["status"] == "connected"

    def test_serialize_config_dict(self, service):
        """_serialize_update_fields should serialize config dict to JSON."""
        updates = {"config": {"key": "value"}}
        service._serialize_update_fields(updates)
        assert updates["config"] == '{"key": "value"}'

    def test_serialize_config_model(self, service):
        """_serialize_update_fields should serialize config model to JSON."""
        config = AgentConfig(metrics_interval=30)
        updates = {"config": config}
        service._serialize_update_fields(updates)
        assert "metrics_interval" in updates["config"]

    def test_serialize_config_string(self, service):
        """_serialize_update_fields should keep JSON string as-is."""
        updates = {"config": '{"key": "value"}'}
        service._serialize_update_fields(updates)
        assert updates["config"] == '{"key": "value"}'

    def test_serialize_last_seen_datetime(self, service):
        """_serialize_update_fields should convert datetime to ISO string."""
        now = datetime.now(UTC)
        updates = {"last_seen": now}
        service._serialize_update_fields(updates)
        assert updates["last_seen"] == now.isoformat()

    def test_serialize_registered_at_datetime(self, service):
        """_serialize_update_fields should convert registered_at datetime."""
        now = datetime.now(UTC)
        updates = {"registered_at": now}
        service._serialize_update_fields(updates)
        assert updates["registered_at"] == now.isoformat()

    def test_serialize_null_values(self, service):
        """_serialize_update_fields should handle null values."""
        updates = {"status": None, "config": None, "last_seen": None}
        service._serialize_update_fields(updates)
        assert updates["status"] is None


class TestDeleteAgent:
    """Tests for delete_agent method."""

    @pytest.mark.asyncio
    async def test_delete_agent_success(self, service, mock_connection):
        """delete_agent should return True on success."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 1
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.agent_service.logger"):
            result = await service.delete_agent("agent-123")

        assert result is True
        mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_agent_not_found(self, service, mock_connection):
        """delete_agent should return False when agent not found."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 0
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.agent_service.logger"):
            result = await service.delete_agent("unknown")

        assert result is False

    @pytest.mark.asyncio
    async def test_delete_agent_deletes_registration_codes(
        self, service, mock_connection
    ):
        """delete_agent should delete registration codes first."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 1
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.agent_service.logger"):
            await service.delete_agent("agent-123")

        calls = mock_conn.execute.call_args_list
        assert "agent_registration_codes" in str(calls[0])


class TestGetAgentsWithExpiringTokens:
    """Tests for get_agents_with_expiring_tokens method."""

    @pytest.mark.asyncio
    async def test_excludes_non_expired_agents(self, service, mock_connection):
        """get_agents_with_expiring_tokens should only return agents with expired tokens."""
        # No agents returned because none have expired tokens
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=[])
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        cutoff = datetime.now(UTC)
        with patch("services.database.agent_service.logger"):
            result = await service.get_agents_with_expiring_tokens(cutoff)

        assert result == []

        # Verify query includes token_expires_at < cutoff filter
        query_call = mock_conn.execute.call_args
        query = query_call[0][0]
        params = query_call[0][1]
        assert "token_expires_at < ?" in query
        assert params[0] == cutoff.isoformat()

    @pytest.mark.asyncio
    async def test_excludes_agents_with_pending_rotation(
        self, service, mock_connection
    ):
        """get_agents_with_expiring_tokens should exclude agents with pending_token_hash."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=[])
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        cutoff = datetime.now(UTC)
        with patch("services.database.agent_service.logger"):
            await service.get_agents_with_expiring_tokens(cutoff)

        # Verify query excludes agents with pending rotation
        query_call = mock_conn.execute.call_args
        query = query_call[0][0]
        assert "pending_token_hash IS NULL" in query

    @pytest.mark.asyncio
    async def test_excludes_agents_without_token_hash(self, service, mock_connection):
        """get_agents_with_expiring_tokens should exclude agents without current token."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=[])
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        cutoff = datetime.now(UTC)
        with patch("services.database.agent_service.logger"):
            await service.get_agents_with_expiring_tokens(cutoff)

        # Verify query requires token_hash to exist
        query_call = mock_conn.execute.call_args
        query = query_call[0][0]
        assert "token_hash IS NOT NULL" in query

    @pytest.mark.asyncio
    async def test_returns_expired_agents(
        self, service, mock_connection, sample_agent_row
    ):
        """get_agents_with_expiring_tokens should return agents with expired tokens."""
        expired_row = dict(sample_agent_row)
        expired_row["token_expires_at"] = (
            datetime.now(UTC) - timedelta(days=1)
        ).isoformat()

        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=[expired_row])
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        cutoff = datetime.now(UTC)
        with patch("services.database.agent_service.logger"):
            result = await service.get_agents_with_expiring_tokens(cutoff)

        assert len(result) == 1
        assert result[0].id == "agent-123"


class TestRegistrationCodeWrappers:
    """Tests for registration code wrapper methods."""

    @pytest.mark.asyncio
    async def test_create_registration_code(self, service):
        """create_registration_code should delegate to registration code service."""
        service._registration_codes.create = AsyncMock()
        await service.create_registration_code("agent-123", 10)
        service._registration_codes.create.assert_called_once_with("agent-123", 10)

    @pytest.mark.asyncio
    async def test_get_registration_code(self, service):
        """get_registration_code should delegate to registration code service."""
        service._registration_codes.get_by_code = AsyncMock()
        await service.get_registration_code("CODE-123")
        service._registration_codes.get_by_code.assert_called_once_with("CODE-123")

    @pytest.mark.asyncio
    async def test_mark_code_used(self, service):
        """mark_code_used should delegate to registration code service."""
        service._registration_codes.mark_used = AsyncMock()
        await service.mark_code_used("code-id")
        service._registration_codes.mark_used.assert_called_once_with("code-id")

    @pytest.mark.asyncio
    async def test_cleanup_expired_codes(self, service):
        """cleanup_expired_codes should delegate to registration code service."""
        service._registration_codes.cleanup_expired = AsyncMock(return_value=5)
        result = await service.cleanup_expired_codes()
        assert result == 5
