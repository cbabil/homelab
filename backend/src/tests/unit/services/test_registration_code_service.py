"""
Unit tests for services/database/registration_code_service.py.

Tests RegistrationCodeDatabaseService and helper functions.
"""

import pytest
from datetime import datetime, timedelta, UTC
from unittest.mock import AsyncMock, MagicMock, patch

from services.database.registration_code_service import (
    RegistrationCodeDatabaseService,
    constant_time_compare,
    hash_code,
)
from models.agent import RegistrationCode


@pytest.fixture
def mock_connection():
    """Create mock database connection."""
    conn = AsyncMock()
    conn.execute = AsyncMock()
    conn.commit = AsyncMock()
    return conn


@pytest.fixture
def mock_db_connection(mock_connection):
    """Create mock DatabaseConnection wrapper."""
    db_conn = MagicMock()
    db_conn.get_connection = MagicMock()
    db_conn.get_connection.return_value.__aenter__ = AsyncMock(return_value=mock_connection)
    db_conn.get_connection.return_value.__aexit__ = AsyncMock()
    return db_conn


@pytest.fixture
def service(mock_db_connection):
    """Create RegistrationCodeDatabaseService with mocked dependencies."""
    return RegistrationCodeDatabaseService(mock_db_connection)


class TestConstantTimeCompare:
    """Tests for constant_time_compare function."""

    def test_equal_strings(self):
        """constant_time_compare should return True for equal strings."""
        assert constant_time_compare("abc123", "abc123") is True

    def test_unequal_strings(self):
        """constant_time_compare should return False for unequal strings."""
        assert constant_time_compare("abc123", "abc456") is False

    def test_empty_strings(self):
        """constant_time_compare should handle empty strings."""
        assert constant_time_compare("", "") is True
        assert constant_time_compare("", "abc") is False

    def test_different_lengths(self):
        """constant_time_compare should return False for different lengths."""
        assert constant_time_compare("abc", "abcd") is False


class TestHashCode:
    """Tests for hash_code function."""

    def test_hash_code_basic(self):
        """hash_code should return SHA-256 hash."""
        result = hash_code("ABCD-1234-EFGH-5678")
        assert len(result) == 64  # SHA-256 hex is 64 chars
        assert result.isalnum()

    def test_hash_code_removes_dashes(self):
        """hash_code should normalize by removing dashes."""
        with_dashes = hash_code("ABCD-1234")
        without_dashes = hash_code("ABCD1234")
        assert with_dashes == without_dashes

    def test_hash_code_uppercase(self):
        """hash_code should normalize to uppercase."""
        upper = hash_code("ABCD1234")
        lower = hash_code("abcd1234")
        assert upper == lower

    def test_hash_code_deterministic(self):
        """hash_code should return same hash for same input."""
        code = "TEST-CODE-1234"
        assert hash_code(code) == hash_code(code)


class TestRegistrationCodeDatabaseServiceInit:
    """Tests for RegistrationCodeDatabaseService initialization."""

    def test_init_stores_connection(self, mock_db_connection):
        """Init should store connection reference."""
        service = RegistrationCodeDatabaseService(mock_db_connection)
        assert service._conn is mock_db_connection


class TestCreate:
    """Tests for create method."""

    @pytest.mark.asyncio
    async def test_create_success(self, service, mock_connection):
        """create should create registration code in database."""
        with patch("services.database.registration_code_service.logger"):
            result = await service.create("agent-123", expiry_minutes=10)

        assert isinstance(result, RegistrationCode)
        assert result.agent_id == "agent-123"
        assert result.used is False
        assert "-" in result.code  # Code has dashes
        assert len(result.code) == 19  # XXXX-XXXX-XXXX-XXXX
        mock_connection.execute.assert_called_once()
        mock_connection.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_default_expiry(self, service, mock_connection):
        """create should use default 5 minute expiry."""
        with patch("services.database.registration_code_service.logger"):
            result = await service.create("agent-123")

        # Check expiry is approximately 5 minutes from now
        now = datetime.now(UTC)
        expected_expiry = now + timedelta(minutes=5)
        diff = abs((result.expires_at - expected_expiry).total_seconds())
        assert diff < 2  # Within 2 seconds

    @pytest.mark.asyncio
    async def test_create_logs_success(self, service, mock_connection):
        """create should log code creation."""
        with patch("services.database.registration_code_service.logger") as mock_logger:
            await service.create("agent-123")

        mock_logger.info.assert_called()
        call_kwargs = mock_logger.info.call_args[1]
        assert call_kwargs["agent_id"] == "agent-123"
        assert "code_id" in call_kwargs


class TestGetByCode:
    """Tests for get_by_code method."""

    @pytest.mark.asyncio
    async def test_get_by_code_found(self, service, mock_connection):
        """get_by_code should return code when found."""
        now = datetime.now(UTC)
        row = {
            "id": "code-123",
            "agent_id": "agent-123",
            "code": "ABCD-1234-EFGH-5678",
            "expires_at": (now + timedelta(minutes=5)).isoformat(),
            "used": 0,
            "created_at": now.isoformat(),
        }
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=row)
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        with patch("services.database.registration_code_service.logger"):
            result = await service.get_by_code("ABCD-1234-EFGH-5678")

        assert result is not None
        assert isinstance(result, RegistrationCode)
        assert result.id == "code-123"
        assert result.agent_id == "agent-123"
        assert result.used is False

    @pytest.mark.asyncio
    async def test_get_by_code_not_found(self, service, mock_connection):
        """get_by_code should return None when not found."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=None)
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        with patch("services.database.registration_code_service.logger"):
            result = await service.get_by_code("NONEXISTENT")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_code_used(self, service, mock_connection):
        """get_by_code should return code with used=True."""
        now = datetime.now(UTC)
        row = {
            "id": "code-123",
            "agent_id": "agent-123",
            "code": "ABCD-1234-EFGH-5678",
            "expires_at": (now + timedelta(minutes=5)).isoformat(),
            "used": 1,
            "created_at": now.isoformat(),
        }
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=row)
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        with patch("services.database.registration_code_service.logger"):
            result = await service.get_by_code("ABCD-1234-EFGH-5678")

        assert result.used is True

    @pytest.mark.asyncio
    async def test_get_by_code_null_created_at(self, service, mock_connection):
        """get_by_code should handle null created_at."""
        now = datetime.now(UTC)
        row = {
            "id": "code-123",
            "agent_id": "agent-123",
            "code": "ABCD-1234-EFGH-5678",
            "expires_at": (now + timedelta(minutes=5)).isoformat(),
            "used": 0,
            "created_at": None,
        }
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=row)
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        with patch("services.database.registration_code_service.logger"):
            result = await service.get_by_code("ABCD-1234-EFGH-5678")

        assert result.created_at is None


class TestMarkUsed:
    """Tests for mark_used method."""

    @pytest.mark.asyncio
    async def test_mark_used_success(self, service, mock_connection):
        """mark_used should update code in database."""
        with patch("services.database.registration_code_service.logger"):
            await service.mark_used("code-123")

        mock_connection.execute.assert_called_once()
        call_args = mock_connection.execute.call_args[0]
        assert "UPDATE" in call_args[0]
        assert call_args[1] == (True, "code-123")
        mock_connection.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_mark_used_logs(self, service, mock_connection):
        """mark_used should log the update."""
        with patch("services.database.registration_code_service.logger") as mock_logger:
            await service.mark_used("code-123")

        mock_logger.info.assert_called()
        assert "code-123" in str(mock_logger.info.call_args)


class TestCleanupExpired:
    """Tests for cleanup_expired method."""

    @pytest.mark.asyncio
    async def test_cleanup_expired_deletes(self, service, mock_connection):
        """cleanup_expired should delete expired codes."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 5
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        with patch("services.database.registration_code_service.logger"):
            result = await service.cleanup_expired()

        assert result == 5
        mock_connection.execute.assert_called_once()
        call_args = mock_connection.execute.call_args[0]
        assert "DELETE" in call_args[0]
        mock_connection.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_expired_none(self, service, mock_connection):
        """cleanup_expired should return 0 when none expired."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 0
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        with patch("services.database.registration_code_service.logger"):
            result = await service.cleanup_expired()

        assert result == 0

    @pytest.mark.asyncio
    async def test_cleanup_expired_logs_when_deleted(self, service, mock_connection):
        """cleanup_expired should log when codes deleted."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 3
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        with patch("services.database.registration_code_service.logger") as mock_logger:
            await service.cleanup_expired()

        mock_logger.info.assert_called()
        assert mock_logger.info.call_args[1]["count"] == 3

    @pytest.mark.asyncio
    async def test_cleanup_expired_no_log_when_none(self, service, mock_connection):
        """cleanup_expired should not log when none deleted."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 0
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        with patch("services.database.registration_code_service.logger") as mock_logger:
            await service.cleanup_expired()

        # info should not be called for cleanup with 0 count
        cleanup_calls = [c for c in mock_logger.info.call_args_list if "cleaned up" in str(c)]
        assert len(cleanup_calls) == 0


class TestDeleteByAgent:
    """Tests for delete_by_agent method."""

    @pytest.mark.asyncio
    async def test_delete_by_agent_success(self, service, mock_connection):
        """delete_by_agent should delete all codes for agent."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 2
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        with patch("services.database.registration_code_service.logger"):
            result = await service.delete_by_agent("agent-123")

        assert result == 2
        mock_connection.execute.assert_called_once()
        call_args = mock_connection.execute.call_args[0]
        assert "DELETE" in call_args[0]
        assert "agent_id" in call_args[0]
        assert call_args[1] == ("agent-123",)

    @pytest.mark.asyncio
    async def test_delete_by_agent_none(self, service, mock_connection):
        """delete_by_agent should return 0 when agent has no codes."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 0
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        with patch("services.database.registration_code_service.logger"):
            result = await service.delete_by_agent("agent-no-codes")

        assert result == 0
