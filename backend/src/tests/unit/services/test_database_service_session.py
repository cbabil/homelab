"""
Unit tests for services/database_service.py - Session/Account lock method delegation.

Tests account lock methods that delegate to SessionDatabaseService.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def mock_session_service():
    """Create mock SessionDatabaseService."""
    return MagicMock()


@pytest.fixture
def db_service_with_session_mock(mock_session_service):
    """Create DatabaseService with mocked session service."""
    with (
        patch("services.database_service.DatabaseConnection"),
        patch("services.database_service.UserDatabaseService"),
        patch("services.database_service.ServerDatabaseService"),
        patch("services.database_service.SessionDatabaseService") as MockSession,
        patch("services.database_service.AppDatabaseService"),
        patch("services.database_service.MetricsDatabaseService"),
        patch("services.database_service.SystemDatabaseService"),
        patch("services.database_service.ExportDatabaseService"),
        patch("services.database_service.SchemaInitializer"),
    ):
        from services.database_service import DatabaseService

        MockSession.return_value = mock_session_service
        return DatabaseService()


@pytest.fixture
def sample_lock_info():
    """Create sample lock info dict."""
    return {
        "id": "lock-123",
        "identifier": "testuser",
        "identifier_type": "username",
        "failed_attempts": 5,
        "locked_until": "2024-01-15T10:30:00Z",
        "locked_at": "2024-01-15T10:00:00Z",
    }


class TestIsAccountLocked:
    """Tests for is_account_locked method."""

    @pytest.mark.asyncio
    async def test_is_account_locked_true(
        self, db_service_with_session_mock, mock_session_service, sample_lock_info
    ):
        """is_account_locked should return True with lock info when locked."""
        mock_session_service.is_account_locked = AsyncMock(
            return_value=(True, sample_lock_info)
        )

        result = await db_service_with_session_mock.is_account_locked("testuser")

        mock_session_service.is_account_locked.assert_awaited_once_with(
            "testuser", "username"
        )
        assert result == (True, sample_lock_info)

    @pytest.mark.asyncio
    async def test_is_account_locked_false(
        self, db_service_with_session_mock, mock_session_service
    ):
        """is_account_locked should return False, None when not locked."""
        mock_session_service.is_account_locked = AsyncMock(return_value=(False, None))

        result = await db_service_with_session_mock.is_account_locked("testuser")

        assert result == (False, None)

    @pytest.mark.asyncio
    async def test_is_account_locked_by_ip(
        self, db_service_with_session_mock, mock_session_service, sample_lock_info
    ):
        """is_account_locked should accept ip_address identifier type."""
        mock_session_service.is_account_locked = AsyncMock(
            return_value=(True, sample_lock_info)
        )

        result = await db_service_with_session_mock.is_account_locked(
            "192.168.1.100", identifier_type="ip_address"
        )

        mock_session_service.is_account_locked.assert_awaited_once_with(
            "192.168.1.100", "ip_address"
        )
        assert result[0] is True


class TestRecordFailedLoginAttempt:
    """Tests for record_failed_login_attempt method."""

    @pytest.mark.asyncio
    async def test_record_failed_login_not_locked(
        self, db_service_with_session_mock, mock_session_service
    ):
        """record_failed_login_attempt should return False when not locked."""
        mock_session_service.record_failed_login_attempt = AsyncMock(
            return_value=(False, 3, None)
        )

        result = await db_service_with_session_mock.record_failed_login_attempt(
            "testuser"
        )

        mock_session_service.record_failed_login_attempt.assert_awaited_once_with(
            "testuser", "username", None, None, 5, 15
        )
        assert result == (False, 3, None)

    @pytest.mark.asyncio
    async def test_record_failed_login_locked(
        self, db_service_with_session_mock, mock_session_service
    ):
        """record_failed_login_attempt should return True when locked."""
        mock_session_service.record_failed_login_attempt = AsyncMock(
            return_value=(True, 5, "2024-01-15T10:30:00Z")
        )

        result = await db_service_with_session_mock.record_failed_login_attempt(
            "testuser"
        )

        assert result == (True, 5, "2024-01-15T10:30:00Z")

    @pytest.mark.asyncio
    async def test_record_failed_login_with_params(
        self, db_service_with_session_mock, mock_session_service
    ):
        """record_failed_login_attempt should pass all params."""
        mock_session_service.record_failed_login_attempt = AsyncMock(
            return_value=(False, 2, None)
        )

        await db_service_with_session_mock.record_failed_login_attempt(
            identifier="testuser",
            identifier_type="username",
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0",
            max_attempts=3,
            lock_duration_minutes=30,
        )

        mock_session_service.record_failed_login_attempt.assert_awaited_once_with(
            "testuser", "username", "192.168.1.100", "Mozilla/5.0", 3, 30
        )


class TestClearFailedAttempts:
    """Tests for clear_failed_attempts method."""

    @pytest.mark.asyncio
    async def test_clear_failed_attempts_success(
        self, db_service_with_session_mock, mock_session_service
    ):
        """clear_failed_attempts should delegate to session service."""
        mock_session_service.clear_failed_attempts = AsyncMock(return_value=True)

        result = await db_service_with_session_mock.clear_failed_attempts("testuser")

        mock_session_service.clear_failed_attempts.assert_awaited_once_with(
            "testuser", "username"
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_clear_failed_attempts_ip_type(
        self, db_service_with_session_mock, mock_session_service
    ):
        """clear_failed_attempts should accept ip_address identifier type."""
        mock_session_service.clear_failed_attempts = AsyncMock(return_value=True)

        result = await db_service_with_session_mock.clear_failed_attempts(
            "192.168.1.100", identifier_type="ip_address"
        )

        mock_session_service.clear_failed_attempts.assert_awaited_once_with(
            "192.168.1.100", "ip_address"
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_clear_failed_attempts_failure(
        self, db_service_with_session_mock, mock_session_service
    ):
        """clear_failed_attempts should return False on failure."""
        mock_session_service.clear_failed_attempts = AsyncMock(return_value=False)

        result = await db_service_with_session_mock.clear_failed_attempts("unknown")

        assert result is False


class TestGetLockedAccounts:
    """Tests for get_locked_accounts method."""

    @pytest.mark.asyncio
    async def test_get_locked_accounts_default(
        self, db_service_with_session_mock, mock_session_service, sample_lock_info
    ):
        """get_locked_accounts should use default params."""
        mock_session_service.get_locked_accounts = AsyncMock(
            return_value=[sample_lock_info]
        )

        result = await db_service_with_session_mock.get_locked_accounts()

        mock_session_service.get_locked_accounts.assert_awaited_once_with(False, False)
        assert result == [sample_lock_info]

    @pytest.mark.asyncio
    async def test_get_locked_accounts_include_expired(
        self, db_service_with_session_mock, mock_session_service, sample_lock_info
    ):
        """get_locked_accounts should pass include_expired param."""
        mock_session_service.get_locked_accounts = AsyncMock(
            return_value=[sample_lock_info]
        )

        await db_service_with_session_mock.get_locked_accounts(include_expired=True)

        mock_session_service.get_locked_accounts.assert_awaited_once_with(True, False)

    @pytest.mark.asyncio
    async def test_get_locked_accounts_include_unlocked(
        self, db_service_with_session_mock, mock_session_service, sample_lock_info
    ):
        """get_locked_accounts should pass include_unlocked param."""
        mock_session_service.get_locked_accounts = AsyncMock(
            return_value=[sample_lock_info]
        )

        await db_service_with_session_mock.get_locked_accounts(include_unlocked=True)

        mock_session_service.get_locked_accounts.assert_awaited_once_with(False, True)

    @pytest.mark.asyncio
    async def test_get_locked_accounts_empty(
        self, db_service_with_session_mock, mock_session_service
    ):
        """get_locked_accounts should return empty list when none."""
        mock_session_service.get_locked_accounts = AsyncMock(return_value=[])

        result = await db_service_with_session_mock.get_locked_accounts()

        assert result == []


class TestUnlockAccount:
    """Tests for unlock_account method."""

    @pytest.mark.asyncio
    async def test_unlock_account_success(
        self, db_service_with_session_mock, mock_session_service
    ):
        """unlock_account should delegate to session service."""
        mock_session_service.unlock_account = AsyncMock(return_value=True)

        result = await db_service_with_session_mock.unlock_account(
            "lock-123", "admin-user"
        )

        mock_session_service.unlock_account.assert_awaited_once_with(
            "lock-123", "admin-user", None
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_unlock_account_with_notes(
        self, db_service_with_session_mock, mock_session_service
    ):
        """unlock_account should pass notes parameter."""
        mock_session_service.unlock_account = AsyncMock(return_value=True)

        result = await db_service_with_session_mock.unlock_account(
            "lock-123", "admin-user", notes="Manual unlock requested by user"
        )

        mock_session_service.unlock_account.assert_awaited_once_with(
            "lock-123", "admin-user", "Manual unlock requested by user"
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_unlock_account_failure(
        self, db_service_with_session_mock, mock_session_service
    ):
        """unlock_account should return False on failure."""
        mock_session_service.unlock_account = AsyncMock(return_value=False)

        result = await db_service_with_session_mock.unlock_account(
            "nonexistent", "admin"
        )

        assert result is False


class TestLockAccount:
    """Tests for lock_account method."""

    @pytest.mark.asyncio
    async def test_lock_account_success(
        self, db_service_with_session_mock, mock_session_service
    ):
        """lock_account should delegate to session service."""
        mock_session_service.lock_account = AsyncMock(return_value=True)

        result = await db_service_with_session_mock.lock_account(
            "lock-123", "admin-user"
        )

        mock_session_service.lock_account.assert_awaited_once_with(
            "lock-123", "admin-user", None, 15
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_lock_account_with_params(
        self, db_service_with_session_mock, mock_session_service
    ):
        """lock_account should pass all params."""
        mock_session_service.lock_account = AsyncMock(return_value=True)

        result = await db_service_with_session_mock.lock_account(
            "lock-123",
            "admin-user",
            notes="Suspicious activity",
            lock_duration_minutes=60,
        )

        mock_session_service.lock_account.assert_awaited_once_with(
            "lock-123", "admin-user", "Suspicious activity", 60
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_lock_account_failure(
        self, db_service_with_session_mock, mock_session_service
    ):
        """lock_account should return False on failure."""
        mock_session_service.lock_account = AsyncMock(return_value=False)

        result = await db_service_with_session_mock.lock_account("nonexistent", "admin")

        assert result is False


class TestGetLockById:
    """Tests for get_lock_by_id method."""

    @pytest.mark.asyncio
    async def test_get_lock_by_id_found(
        self, db_service_with_session_mock, mock_session_service, sample_lock_info
    ):
        """get_lock_by_id should return lock info when found."""
        mock_session_service.get_lock_by_id = AsyncMock(return_value=sample_lock_info)

        result = await db_service_with_session_mock.get_lock_by_id("lock-123")

        mock_session_service.get_lock_by_id.assert_awaited_once_with("lock-123")
        assert result == sample_lock_info

    @pytest.mark.asyncio
    async def test_get_lock_by_id_not_found(
        self, db_service_with_session_mock, mock_session_service
    ):
        """get_lock_by_id should return None when not found."""
        mock_session_service.get_lock_by_id = AsyncMock(return_value=None)

        result = await db_service_with_session_mock.get_lock_by_id("nonexistent")

        assert result is None
