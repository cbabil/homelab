"""
Unit tests for services/database/session_service.py.

Tests SessionDatabaseService methods for account locks and login security.
"""

import pytest
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from services.database.session_service import SessionDatabaseService


@pytest.fixture
def mock_connection():
    """Create mock DatabaseConnection."""
    return MagicMock()


@pytest.fixture
def service(mock_connection):
    """Create SessionDatabaseService instance."""
    return SessionDatabaseService(mock_connection)


def create_mock_context(mock_conn):
    """Create async context manager for database connection."""
    @asynccontextmanager
    async def context():
        yield mock_conn
    return context()


@pytest.fixture
def sample_lock_row():
    """Create sample account lock row from database."""
    now = datetime.now(UTC)
    return {
        "id": "lock-123",
        "identifier": "testuser",
        "identifier_type": "username",
        "attempt_count": 3,
        "first_attempt_at": (now - timedelta(minutes=10)).isoformat(),
        "last_attempt_at": now.isoformat(),
        "locked_at": now.isoformat(),
        "lock_expires_at": (now + timedelta(minutes=15)).isoformat(),
        "ip_address": "192.168.1.100",
        "user_agent": "Mozilla/5.0",
        "reason": "too_many_attempts",
        "unlocked_at": None,
        "unlocked_by": None,
        "notes": None,
    }


class TestSessionDatabaseServiceInit:
    """Tests for SessionDatabaseService initialization."""

    def test_init_stores_connection(self, mock_connection):
        """Service should store connection reference."""
        service = SessionDatabaseService(mock_connection)
        assert service._conn is mock_connection


class TestIsAccountLocked:
    """Tests for is_account_locked method."""

    @pytest.mark.asyncio
    async def test_is_account_locked_true(
        self, service, mock_connection, sample_lock_row
    ):
        """is_account_locked should return True with lock info when locked."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=sample_lock_row)
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.session_service.logger"):
            is_locked, lock_info = await service.is_account_locked("testuser")

        assert is_locked is True
        assert lock_info is not None
        assert lock_info["identifier"] == "testuser"
        assert lock_info["attempt_count"] == 3

    @pytest.mark.asyncio
    async def test_is_account_locked_false(self, service, mock_connection):
        """is_account_locked should return False when not locked."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=None)
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.session_service.logger"):
            is_locked, lock_info = await service.is_account_locked("testuser")

        assert is_locked is False
        assert lock_info is None

    @pytest.mark.asyncio
    async def test_is_account_locked_by_ip(
        self, service, mock_connection, sample_lock_row
    ):
        """is_account_locked should work with IP identifier type."""
        row = dict(sample_lock_row)
        row["identifier"] = "192.168.1.100"
        row["identifier_type"] = "ip"
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=row)
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.session_service.logger"):
            is_locked, lock_info = await service.is_account_locked(
                "192.168.1.100", identifier_type="ip"
            )

        assert is_locked is True
        assert lock_info["identifier_type"] == "ip"

    @pytest.mark.asyncio
    async def test_is_account_locked_exception(self, service, mock_connection):
        """is_account_locked should return False on exception."""
        mock_connection.get_connection.side_effect = Exception("DB error")

        with patch("services.database.session_service.logger"):
            is_locked, lock_info = await service.is_account_locked("testuser")

        assert is_locked is False
        assert lock_info is None


class TestRecordFailedLoginAttempt:
    """Tests for record_failed_login_attempt method."""

    @pytest.mark.asyncio
    async def test_record_first_attempt_no_lock(self, service, mock_connection):
        """First attempt should not lock with default max_attempts=5."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=None)
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.session_service.logger"):
            is_locked, count, expires = await service.record_failed_login_attempt(
                "testuser"
            )

        assert is_locked is False
        assert count == 1
        assert expires is None
        mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_record_first_attempt_locks_when_max_is_1(
        self, service, mock_connection
    ):
        """First attempt should lock when max_attempts=1."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=None)
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.session_service.logger"):
            is_locked, count, expires = await service.record_failed_login_attempt(
                "testuser", max_attempts=1
            )

        assert is_locked is True
        assert count == 1
        assert expires is not None

    @pytest.mark.asyncio
    async def test_record_existing_attempt_increments(
        self, service, mock_connection
    ):
        """Existing record should increment attempt count."""
        existing = {
            "attempt_count": 2,
            "locked_at": None,
            "unlocked_at": None,
            "lock_expires_at": None,
        }
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=existing)
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.session_service.logger"):
            is_locked, count, expires = await service.record_failed_login_attempt(
                "testuser"
            )

        assert is_locked is False
        assert count == 3
        assert expires is None

    @pytest.mark.asyncio
    async def test_record_locks_at_threshold(self, service, mock_connection):
        """Should lock when attempt count reaches threshold."""
        existing = {
            "attempt_count": 4,
            "locked_at": None,
            "unlocked_at": None,
            "lock_expires_at": None,
        }
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=existing)
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.session_service.logger"):
            is_locked, count, expires = await service.record_failed_login_attempt(
                "testuser", max_attempts=5
            )

        assert is_locked is True
        assert count == 5
        assert expires is not None

    @pytest.mark.asyncio
    async def test_record_already_locked_returns_existing(
        self, service, mock_connection
    ):
        """Should return existing lock info if already locked."""
        future_time = (datetime.now(UTC) + timedelta(minutes=10)).isoformat()
        existing = {
            "attempt_count": 5,
            "locked_at": datetime.now(UTC).isoformat(),
            "unlocked_at": None,
            "lock_expires_at": future_time,
        }
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=existing)
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.session_service.logger"):
            is_locked, count, expires = await service.record_failed_login_attempt(
                "testuser"
            )

        assert is_locked is True
        assert count == 6
        assert expires == future_time

    @pytest.mark.asyncio
    async def test_record_permanent_lock_when_duration_zero(
        self, service, mock_connection
    ):
        """Should create permanent lock when duration is 0."""
        existing = {
            "attempt_count": 4,
            "locked_at": None,
            "unlocked_at": None,
            "lock_expires_at": None,
        }
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=existing)
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.session_service.logger"):
            is_locked, count, expires = await service.record_failed_login_attempt(
                "testuser", max_attempts=5, lock_duration_minutes=0
            )

        assert is_locked is True
        assert count == 5
        assert expires is None

    @pytest.mark.asyncio
    async def test_record_with_ip_and_user_agent(self, service, mock_connection):
        """Should store IP and user agent."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=None)
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.session_service.logger"):
            await service.record_failed_login_attempt(
                "testuser", ip_address="10.0.0.1", user_agent="TestAgent/1.0"
            )

        call_args = mock_conn.execute.call_args_list[1][0]
        assert "10.0.0.1" in call_args[1]
        assert "TestAgent/1.0" in call_args[1]

    @pytest.mark.asyncio
    async def test_record_exception(self, service, mock_connection):
        """Should return defaults on exception."""
        mock_connection.get_connection.side_effect = Exception("DB error")

        with patch("services.database.session_service.logger"):
            is_locked, count, expires = await service.record_failed_login_attempt(
                "testuser"
            )

        assert is_locked is False
        assert count == 0
        assert expires is None


class TestClearFailedAttempts:
    """Tests for clear_failed_attempts method."""

    @pytest.mark.asyncio
    async def test_clear_success(self, service, mock_connection):
        """clear_failed_attempts should return True on success."""
        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.session_service.logger"):
            result = await service.clear_failed_attempts("testuser")

        assert result is True
        mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_clear_with_ip_type(self, service, mock_connection):
        """clear_failed_attempts should work with ip type."""
        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.session_service.logger"):
            result = await service.clear_failed_attempts("10.0.0.1", identifier_type="ip")

        assert result is True
        call_args = mock_conn.execute.call_args[0]
        assert "ip" in call_args[1]

    @pytest.mark.asyncio
    async def test_clear_exception(self, service, mock_connection):
        """clear_failed_attempts should return False on exception."""
        mock_connection.get_connection.side_effect = Exception("DB error")

        with patch("services.database.session_service.logger"):
            result = await service.clear_failed_attempts("testuser")

        assert result is False


class TestGetLockedAccounts:
    """Tests for get_locked_accounts method."""

    @pytest.mark.asyncio
    async def test_get_locked_accounts_success(
        self, service, mock_connection, sample_lock_row
    ):
        """get_locked_accounts should return list of locked accounts."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=[sample_lock_row])
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.session_service.logger"):
            result = await service.get_locked_accounts()

        assert len(result) == 1
        assert result[0]["identifier"] == "testuser"

    @pytest.mark.asyncio
    async def test_get_locked_accounts_empty(self, service, mock_connection):
        """get_locked_accounts should return empty list when none."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=[])
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.session_service.logger"):
            result = await service.get_locked_accounts()

        assert result == []

    @pytest.mark.asyncio
    async def test_get_locked_accounts_include_expired(
        self, service, mock_connection
    ):
        """get_locked_accounts should modify query for include_expired."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=[])
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.session_service.logger"):
            await service.get_locked_accounts(include_expired=True)

        call_args = mock_conn.execute.call_args[0]
        assert "lock_expires_at" not in call_args[0] or "IS NULL OR" in call_args[0]

    @pytest.mark.asyncio
    async def test_get_locked_accounts_include_unlocked(
        self, service, mock_connection
    ):
        """get_locked_accounts should modify query for include_unlocked."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=[])
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.session_service.logger"):
            await service.get_locked_accounts(include_unlocked=True)

        call_args = mock_conn.execute.call_args[0]
        assert "unlocked_at IS NULL" not in call_args[0]

    @pytest.mark.asyncio
    async def test_get_locked_accounts_exception(self, service, mock_connection):
        """get_locked_accounts should return empty list on exception."""
        mock_connection.get_connection.side_effect = Exception("DB error")

        with patch("services.database.session_service.logger"):
            result = await service.get_locked_accounts()

        assert result == []


class TestUnlockAccount:
    """Tests for unlock_account method."""

    @pytest.mark.asyncio
    async def test_unlock_success(self, service, mock_connection):
        """unlock_account should return True on success."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 1
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.session_service.logger"):
            result = await service.unlock_account("lock-123", "admin")

        assert result is True
        mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_unlock_with_notes(self, service, mock_connection):
        """unlock_account should store notes."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 1
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.session_service.logger"):
            result = await service.unlock_account(
                "lock-123", "admin", notes="Manual unlock"
            )

        assert result is True

    @pytest.mark.asyncio
    async def test_unlock_not_found(self, service, mock_connection):
        """unlock_account should return False when lock not found."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 0
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.session_service.logger"):
            result = await service.unlock_account("nonexistent", "admin")

        assert result is False

    @pytest.mark.asyncio
    async def test_unlock_exception(self, service, mock_connection):
        """unlock_account should return False on exception."""
        mock_connection.get_connection.side_effect = Exception("DB error")

        with patch("services.database.session_service.logger"):
            result = await service.unlock_account("lock-123", "admin")

        assert result is False


class TestLockAccount:
    """Tests for lock_account method."""

    @pytest.mark.asyncio
    async def test_lock_success(self, service, mock_connection):
        """lock_account should return True on success."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 1
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.session_service.logger"):
            result = await service.lock_account("lock-123", "admin")

        assert result is True
        mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_lock_with_notes(self, service, mock_connection):
        """lock_account should store notes."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 1
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.session_service.logger"):
            result = await service.lock_account(
                "lock-123", "admin", notes="Security concern"
            )

        assert result is True

    @pytest.mark.asyncio
    async def test_lock_custom_duration(self, service, mock_connection):
        """lock_account should use custom duration."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 1
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.session_service.logger"):
            result = await service.lock_account(
                "lock-123", "admin", lock_duration_minutes=60
            )

        assert result is True

    @pytest.mark.asyncio
    async def test_lock_not_found(self, service, mock_connection):
        """lock_account should return False when lock not found."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 0
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.session_service.logger"):
            result = await service.lock_account("nonexistent", "admin")

        assert result is False

    @pytest.mark.asyncio
    async def test_lock_exception(self, service, mock_connection):
        """lock_account should return False on exception."""
        mock_connection.get_connection.side_effect = Exception("DB error")

        with patch("services.database.session_service.logger"):
            result = await service.lock_account("lock-123", "admin")

        assert result is False


class TestGetLockById:
    """Tests for get_lock_by_id method."""

    @pytest.mark.asyncio
    async def test_get_lock_found(
        self, service, mock_connection, sample_lock_row
    ):
        """get_lock_by_id should return lock info when found."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=sample_lock_row)
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.session_service.logger"):
            result = await service.get_lock_by_id("lock-123")

        assert result is not None
        assert result["id"] == "lock-123"
        assert result["identifier"] == "testuser"

    @pytest.mark.asyncio
    async def test_get_lock_not_found(self, service, mock_connection):
        """get_lock_by_id should return None when not found."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=None)
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.session_service.logger"):
            result = await service.get_lock_by_id("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_lock_exception(self, service, mock_connection):
        """get_lock_by_id should return None on exception."""
        mock_connection.get_connection.side_effect = Exception("DB error")

        with patch("services.database.session_service.logger"):
            result = await service.get_lock_by_id("lock-123")

        assert result is None
