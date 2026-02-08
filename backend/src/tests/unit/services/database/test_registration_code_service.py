"""
Unit tests for services/database/registration_code_service.py

Tests RegistrationCodeDatabaseService class methods.
"""

from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.database.registration_code_service import (
    RegistrationCodeDatabaseService,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_connection():
    """Create mock DatabaseConnection."""
    return MagicMock()


@pytest.fixture
def service(mock_connection):
    """Create RegistrationCodeDatabaseService instance."""
    return RegistrationCodeDatabaseService(mock_connection)


def create_mock_context(mock_conn):
    """Create async context manager for database connection."""

    @asynccontextmanager
    async def context():
        yield mock_conn

    return context()


@pytest.fixture
def sample_registration_code_row():
    """Create sample registration code database row."""
    now = datetime.now(UTC)
    expires = now + timedelta(minutes=5)
    return {
        "id": "code-123",
        "agent_id": "agent-456",
        "code": "ABCD-EFGH-IJKL-MNOP",
        "expires_at": expires.isoformat(),
        "used": 0,
        "created_at": now.isoformat(),
    }


# =============================================================================
# Tests for RegistrationCodeDatabaseService initialization
# =============================================================================


class TestRegistrationCodeDatabaseServiceInit:
    """Tests for RegistrationCodeDatabaseService initialization."""

    def test_init_stores_connection(self, mock_connection):
        """Service should store connection reference."""
        service = RegistrationCodeDatabaseService(mock_connection)
        assert service._conn is mock_connection


# =============================================================================
# Tests for create method
# =============================================================================


class TestCreate:
    """Tests for create method."""

    @pytest.mark.asyncio
    async def test_create_returns_registration_code(self, service, mock_connection):
        """create should return RegistrationCode model."""
        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with (
            patch("services.database.registration_code_service.logger"),
            patch("services.database.registration_code_service.uuid4") as mock_uuid,
        ):
            mock_uuid.return_value = MagicMock()
            mock_uuid.return_value.__str__ = lambda self: "test-uuid"

            with patch(
                "services.database.registration_code_service.secrets.token_hex"
            ) as mock_token:
                mock_token.return_value = "abcd1234efgh5678"

                result = await service.create("agent-123", expiry_minutes=10)

        assert result.id == "test-uuid"
        assert result.agent_id == "agent-123"
        assert result.code == "ABCD-1234-EFGH-5678"
        assert result.used is False
        assert result.created_at is not None

    @pytest.mark.asyncio
    async def test_create_inserts_into_database(self, service, mock_connection):
        """create should insert record into database."""
        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.registration_code_service.logger"):
            await service.create("agent-123")

        mock_conn.execute.assert_called_once()
        call_args = mock_conn.execute.call_args[0]
        assert "INSERT INTO agent_registration_codes" in call_args[0]
        mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_uses_default_expiry(self, service, mock_connection):
        """create should use 5 minute default expiry."""
        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        before = datetime.now(UTC)
        with patch("services.database.registration_code_service.logger"):
            result = await service.create("agent-123")
        after = datetime.now(UTC)

        # Expiry should be approximately 5 minutes from now
        expected_min = before + timedelta(minutes=5)
        expected_max = after + timedelta(minutes=5)
        assert expected_min <= result.expires_at <= expected_max

    @pytest.mark.asyncio
    async def test_create_uses_custom_expiry(self, service, mock_connection):
        """create should use custom expiry minutes."""
        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        before = datetime.now(UTC)
        with patch("services.database.registration_code_service.logger"):
            result = await service.create("agent-123", expiry_minutes=30)
        after = datetime.now(UTC)

        # Expiry should be approximately 30 minutes from now
        expected_min = before + timedelta(minutes=30)
        expected_max = after + timedelta(minutes=30)
        assert expected_min <= result.expires_at <= expected_max

    @pytest.mark.asyncio
    async def test_create_logs_creation(self, service, mock_connection):
        """create should log code creation."""
        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.registration_code_service.logger") as mock_logger:
            await service.create("agent-123")

        mock_logger.info.assert_called_once()
        call_kwargs = mock_logger.info.call_args.kwargs
        assert "code_id" in call_kwargs
        assert "agent_id" in call_kwargs
        assert call_kwargs["agent_id"] == "agent-123"

    @pytest.mark.asyncio
    async def test_create_generates_unique_codes(self, service, mock_connection):
        """create should generate unique codes via secrets module."""
        mock_conn = AsyncMock()

        # Use side_effect to return a fresh context manager for each call
        def get_fresh_context():
            return create_mock_context(mock_conn)

        mock_connection.get_connection = get_fresh_context

        codes = []
        with patch("services.database.registration_code_service.logger"):
            for _ in range(3):
                result = await service.create("agent-123")
                codes.append(result.code)

        # All codes should be unique (extremely high probability)
        assert len(set(codes)) == 3

    @pytest.mark.asyncio
    async def test_create_code_format(self, service, mock_connection):
        """create should generate code in XXXX-XXXX-XXXX-XXXX format."""
        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.registration_code_service.logger"):
            result = await service.create("agent-123")

        parts = result.code.split("-")
        assert len(parts) == 4
        for part in parts:
            assert len(part) == 4
            assert part.isupper() or part.isdigit()


# =============================================================================
# Tests for get_by_code method
# =============================================================================


class TestGetByCode:
    """Tests for get_by_code method."""

    @pytest.mark.asyncio
    async def test_get_by_code_returns_registration_code(
        self, service, mock_connection, sample_registration_code_row
    ):
        """get_by_code should return RegistrationCode when found."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = sample_registration_code_row

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        result = await service.get_by_code("ABCD-EFGH-IJKL-MNOP")

        assert result is not None
        assert result.id == "code-123"
        assert result.agent_id == "agent-456"
        assert result.code == "ABCD-EFGH-IJKL-MNOP"
        assert result.used is False

    @pytest.mark.asyncio
    async def test_get_by_code_returns_none_when_not_found(
        self, service, mock_connection
    ):
        """get_by_code should return None when code not found."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = None

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        result = await service.get_by_code("NONEXISTENT-CODE")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_code_queries_correct_table(self, service, mock_connection):
        """get_by_code should query agent_registration_codes table."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = None

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        await service.get_by_code("TEST-CODE")

        call_args = mock_conn.execute.call_args[0]
        assert "agent_registration_codes" in call_args[0]
        assert "code = ?" in call_args[0]

    @pytest.mark.asyncio
    async def test_get_by_code_parses_used_as_bool(
        self, service, mock_connection, sample_registration_code_row
    ):
        """get_by_code should convert used field to boolean."""
        # Test with used = 1
        row_used = dict(sample_registration_code_row)
        row_used["used"] = 1

        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = row_used

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        result = await service.get_by_code("ABCD-EFGH-IJKL-MNOP")

        assert result.used is True

    @pytest.mark.asyncio
    async def test_get_by_code_handles_none_created_at(
        self, service, mock_connection, sample_registration_code_row
    ):
        """get_by_code should handle None created_at."""
        row = dict(sample_registration_code_row)
        row["created_at"] = None

        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = row

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        result = await service.get_by_code("ABCD-EFGH-IJKL-MNOP")

        assert result.created_at is None


# =============================================================================
# Tests for mark_used method
# =============================================================================


class TestMarkUsed:
    """Tests for mark_used method."""

    @pytest.mark.asyncio
    async def test_mark_used_updates_database(self, service, mock_connection):
        """mark_used should update used field to True."""
        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.registration_code_service.logger"):
            await service.mark_used("code-123")

        mock_conn.execute.assert_called_once()
        call_args = mock_conn.execute.call_args[0]
        assert "UPDATE agent_registration_codes" in call_args[0]
        assert "used = ?" in call_args[0]
        assert call_args[1] == (True, "code-123")
        mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_mark_used_logs_action(self, service, mock_connection):
        """mark_used should log the action."""
        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.registration_code_service.logger") as mock_logger:
            await service.mark_used("code-123")

        mock_logger.info.assert_called_once()
        call_kwargs = mock_logger.info.call_args.kwargs
        assert call_kwargs["code_id"] == "code-123"


# =============================================================================
# Tests for cleanup_expired method
# =============================================================================


class TestCleanupExpired:
    """Tests for cleanup_expired method."""

    @pytest.mark.asyncio
    async def test_cleanup_expired_deletes_old_codes(self, service, mock_connection):
        """cleanup_expired should delete codes past expiration."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 5

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.registration_code_service.logger"):
            result = await service.cleanup_expired()

        assert result == 5
        mock_conn.execute.assert_called_once()
        call_args = mock_conn.execute.call_args[0]
        assert "DELETE FROM agent_registration_codes" in call_args[0]
        assert "expires_at <" in call_args[0]
        mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_expired_returns_zero_when_none(
        self, service, mock_connection
    ):
        """cleanup_expired should return 0 when no expired codes."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 0

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.registration_code_service.logger"):
            result = await service.cleanup_expired()

        assert result == 0

    @pytest.mark.asyncio
    async def test_cleanup_expired_logs_when_deleted(self, service, mock_connection):
        """cleanup_expired should log when codes are deleted."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 3

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.registration_code_service.logger") as mock_logger:
            await service.cleanup_expired()

        mock_logger.info.assert_called_once()
        call_kwargs = mock_logger.info.call_args.kwargs
        assert call_kwargs["count"] == 3

    @pytest.mark.asyncio
    async def test_cleanup_expired_does_not_log_when_zero(
        self, service, mock_connection
    ):
        """cleanup_expired should not log when no codes deleted."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 0

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.registration_code_service.logger") as mock_logger:
            await service.cleanup_expired()

        mock_logger.info.assert_not_called()


# =============================================================================
# Tests for delete_by_agent method
# =============================================================================


class TestDeleteByAgent:
    """Tests for delete_by_agent method."""

    @pytest.mark.asyncio
    async def test_delete_by_agent_removes_codes(self, service, mock_connection):
        """delete_by_agent should delete all codes for agent."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 2

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        result = await service.delete_by_agent("agent-123")

        assert result == 2
        mock_conn.execute.assert_called_once()
        call_args = mock_conn.execute.call_args[0]
        assert "DELETE FROM agent_registration_codes" in call_args[0]
        assert "agent_id = ?" in call_args[0]
        assert call_args[1] == ("agent-123",)
        mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_by_agent_returns_zero_when_none(
        self, service, mock_connection
    ):
        """delete_by_agent should return 0 when agent has no codes."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 0

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        result = await service.delete_by_agent("nonexistent-agent")

        assert result == 0

    @pytest.mark.asyncio
    async def test_delete_by_agent_commits_transaction(self, service, mock_connection):
        """delete_by_agent should commit after deletion."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 1

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        await service.delete_by_agent("agent-123")

        mock_conn.commit.assert_called_once()
