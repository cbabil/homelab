"""
Auth Service Authentication Tests

Tests for authenticate_user method.
"""

import pytest
from datetime import datetime, UTC
from unittest.mock import MagicMock, AsyncMock, patch

from services.auth_service import AuthService
from models.auth import User, UserRole, LoginCredentials, TokenType


@pytest.fixture
def mock_db_service():
    """Create mock database service."""
    service = MagicMock()
    service.is_account_locked = AsyncMock(return_value=(False, {}))
    service.get_user_by_username = AsyncMock(return_value=None)
    service.get_user_password_hash = AsyncMock(return_value=None)
    service.record_failed_login_attempt = AsyncMock(return_value=(False, 1, None))
    service.clear_failed_attempts = AsyncMock()
    service.update_user_last_login = AsyncMock()
    return service


@pytest.fixture
def mock_session_service():
    """Create mock session service."""
    service = MagicMock()
    mock_session = MagicMock()
    mock_session.id = "session-123"
    service.create_session = AsyncMock(return_value=mock_session)
    return service


@pytest.fixture
def auth_service(mock_db_service, mock_session_service):
    """Create AuthService with mocked dependencies."""
    with patch("services.auth_service.logger"):
        service = AuthService(
            jwt_secret="test-secret-key",
            db_service=mock_db_service,
            session_service=mock_session_service,
        )
        return service


@pytest.fixture
def valid_user():
    """Create a valid user."""
    return User(
        id="user-123",
        username="testuser",
        email="test@example.com",
        role=UserRole.USER,
        is_active=True,
        last_login=datetime.now(UTC).isoformat(),
        created_at=datetime.now(UTC).isoformat(),
    )


@pytest.fixture
def login_credentials():
    """Create login credentials."""
    return LoginCredentials(username="testuser", password="password123")


class TestAuthenticateUserLocking:
    """Tests for account locking behavior."""

    @pytest.mark.asyncio
    async def test_authenticate_blocked_username_locked(
        self, auth_service, mock_db_service, login_credentials
    ):
        """authenticate_user should block locked username."""
        mock_db_service.is_account_locked = AsyncMock(
            return_value=(True, {"lock_expires_at": "2024-01-15T10:00:00"})
        )

        with patch.object(auth_service, "_get_security_settings", return_value=(5, 900)), \
             patch.object(auth_service, "_log_security_event", new_callable=AsyncMock), \
             patch("services.auth_service.logger"):
            result = await auth_service.authenticate_user(
                login_credentials, client_ip="192.168.1.1"
            )

        assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_blocked_ip_locked(
        self, auth_service, mock_db_service, login_credentials
    ):
        """authenticate_user should block locked IP."""
        mock_db_service.is_account_locked = AsyncMock(
            side_effect=[
                (False, {}),  # username not locked
                (True, {"lock_expires_at": "2024-01-15T10:00:00"}),  # IP locked
            ]
        )

        with patch.object(auth_service, "_get_security_settings", return_value=(5, 900)), \
             patch.object(auth_service, "_log_security_event", new_callable=AsyncMock), \
             patch("services.auth_service.logger"):
            result = await auth_service.authenticate_user(
                login_credentials, client_ip="192.168.1.1"
            )

        assert result is None


class TestAuthenticateUserNotFound:
    """Tests for user not found scenarios."""

    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(
        self, auth_service, mock_db_service, login_credentials
    ):
        """authenticate_user should return None when user not found."""
        mock_db_service.get_user_by_username = AsyncMock(return_value=None)

        with patch.object(auth_service, "_get_security_settings", return_value=(5, 900)), \
             patch.object(auth_service, "_log_security_event", new_callable=AsyncMock), \
             patch("services.auth_service.logger"):
            result = await auth_service.authenticate_user(login_credentials)

        assert result is None
        mock_db_service.record_failed_login_attempt.assert_called()

    @pytest.mark.asyncio
    async def test_authenticate_inactive_user(
        self, auth_service, mock_db_service, login_credentials, valid_user
    ):
        """authenticate_user should return None for inactive user."""
        valid_user.is_active = False
        mock_db_service.get_user_by_username = AsyncMock(return_value=valid_user)

        with patch.object(auth_service, "_get_security_settings", return_value=(5, 900)), \
             patch.object(auth_service, "_log_security_event", new_callable=AsyncMock), \
             patch("services.auth_service.logger"):
            result = await auth_service.authenticate_user(login_credentials)

        assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_records_failed_attempt_for_ip(
        self, auth_service, mock_db_service, login_credentials
    ):
        """authenticate_user should record failed attempt for IP."""
        mock_db_service.get_user_by_username = AsyncMock(return_value=None)

        with patch.object(auth_service, "_get_security_settings", return_value=(5, 900)), \
             patch.object(auth_service, "_log_security_event", new_callable=AsyncMock), \
             patch("services.auth_service.logger"):
            await auth_service.authenticate_user(
                login_credentials, client_ip="192.168.1.1"
            )

        # Should record for both username and IP
        assert mock_db_service.record_failed_login_attempt.call_count == 2

    @pytest.mark.asyncio
    async def test_authenticate_locks_account_after_max_attempts(
        self, auth_service, mock_db_service, login_credentials
    ):
        """authenticate_user should log account lock event."""
        mock_db_service.get_user_by_username = AsyncMock(return_value=None)
        mock_db_service.record_failed_login_attempt = AsyncMock(
            return_value=(True, 5, "2024-01-15T10:15:00")  # is_locked=True
        )

        with patch.object(auth_service, "_get_security_settings", return_value=(5, 900)), \
             patch.object(auth_service, "_log_security_event", new_callable=AsyncMock) as mock_log, \
             patch("services.auth_service.logger"):
            await auth_service.authenticate_user(login_credentials)

        # Should log ACCOUNT_LOCKED event
        assert any(
            call[0][0] == "ACCOUNT_LOCKED"
            for call in mock_log.call_args_list
        )


class TestAuthenticateInvalidPassword:
    """Tests for invalid password scenarios."""

    @pytest.mark.asyncio
    async def test_authenticate_no_password_hash(
        self, auth_service, mock_db_service, login_credentials, valid_user
    ):
        """authenticate_user should fail when no password hash."""
        mock_db_service.get_user_by_username = AsyncMock(return_value=valid_user)
        mock_db_service.get_user_password_hash = AsyncMock(return_value=None)

        with patch.object(auth_service, "_get_security_settings", return_value=(5, 900)), \
             patch.object(auth_service, "_log_security_event", new_callable=AsyncMock), \
             patch("services.auth_service.logger"):
            result = await auth_service.authenticate_user(login_credentials)

        assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_wrong_password(
        self, auth_service, mock_db_service, login_credentials, valid_user
    ):
        """authenticate_user should fail for wrong password."""
        mock_db_service.get_user_by_username = AsyncMock(return_value=valid_user)
        mock_db_service.get_user_password_hash = AsyncMock(return_value="hashed")

        with patch.object(auth_service, "_get_security_settings", return_value=(5, 900)), \
             patch.object(auth_service, "_log_security_event", new_callable=AsyncMock), \
             patch("services.auth_service.verify_password", return_value=False), \
             patch("services.auth_service.logger"):
            result = await auth_service.authenticate_user(login_credentials)

        assert result is None
        mock_db_service.record_failed_login_attempt.assert_called()


class TestAuthenticateSuccess:
    """Tests for successful authentication."""

    @pytest.mark.asyncio
    async def test_authenticate_success(
        self, auth_service, mock_db_service, mock_session_service,
        login_credentials, valid_user
    ):
        """authenticate_user should return LoginResponse on success."""
        mock_db_service.get_user_by_username = AsyncMock(return_value=valid_user)
        mock_db_service.get_user_password_hash = AsyncMock(return_value="hashed")

        with patch.object(auth_service, "_get_security_settings", return_value=(5, 900)), \
             patch.object(auth_service, "_log_security_event", new_callable=AsyncMock), \
             patch("services.auth_service.verify_password", return_value=True), \
             patch("services.auth_service.generate_jwt_token", return_value="jwt-token"), \
             patch("services.auth_service.create_session_data", return_value={}), \
             patch("services.auth_service.logger"):
            result = await auth_service.authenticate_user(
                login_credentials, client_ip="192.168.1.1", user_agent="Mozilla"
            )

        assert result is not None
        assert result.user == valid_user
        assert result.token == "jwt-token"
        assert result.session_id == "session-123"
        assert result.token_type == TokenType.JWT

    @pytest.mark.asyncio
    async def test_authenticate_clears_failed_attempts(
        self, auth_service, mock_db_service, mock_session_service,
        login_credentials, valid_user
    ):
        """authenticate_user should clear failed attempts on success."""
        mock_db_service.get_user_by_username = AsyncMock(return_value=valid_user)
        mock_db_service.get_user_password_hash = AsyncMock(return_value="hashed")

        with patch.object(auth_service, "_get_security_settings", return_value=(5, 900)), \
             patch.object(auth_service, "_log_security_event", new_callable=AsyncMock), \
             patch("services.auth_service.verify_password", return_value=True), \
             patch("services.auth_service.generate_jwt_token", return_value="jwt"), \
             patch("services.auth_service.create_session_data", return_value={}), \
             patch("services.auth_service.logger"):
            await auth_service.authenticate_user(
                login_credentials, client_ip="192.168.1.1"
            )

        # Should clear both username and IP
        assert mock_db_service.clear_failed_attempts.call_count == 2

    @pytest.mark.asyncio
    async def test_authenticate_updates_last_login(
        self, auth_service, mock_db_service, mock_session_service,
        login_credentials, valid_user
    ):
        """authenticate_user should update last login timestamp."""
        mock_db_service.get_user_by_username = AsyncMock(return_value=valid_user)
        mock_db_service.get_user_password_hash = AsyncMock(return_value="hashed")

        with patch.object(auth_service, "_get_security_settings", return_value=(5, 900)), \
             patch.object(auth_service, "_log_security_event", new_callable=AsyncMock), \
             patch("services.auth_service.verify_password", return_value=True), \
             patch("services.auth_service.generate_jwt_token", return_value="jwt"), \
             patch("services.auth_service.create_session_data", return_value={}), \
             patch("services.auth_service.logger"):
            await auth_service.authenticate_user(login_credentials)

        mock_db_service.update_user_last_login.assert_called_once()

    @pytest.mark.asyncio
    async def test_authenticate_creates_session(
        self, auth_service, mock_db_service, mock_session_service,
        login_credentials, valid_user
    ):
        """authenticate_user should create database session."""
        mock_db_service.get_user_by_username = AsyncMock(return_value=valid_user)
        mock_db_service.get_user_password_hash = AsyncMock(return_value="hashed")

        with patch.object(auth_service, "_get_security_settings", return_value=(5, 900)), \
             patch.object(auth_service, "_log_security_event", new_callable=AsyncMock), \
             patch("services.auth_service.verify_password", return_value=True), \
             patch("services.auth_service.generate_jwt_token", return_value="jwt"), \
             patch("services.auth_service.create_session_data", return_value={}), \
             patch("services.auth_service.logger"):
            await auth_service.authenticate_user(
                login_credentials, client_ip="192.168.1.1", user_agent="Mozilla"
            )

        mock_session_service.create_session.assert_called_once()
        call_kwargs = mock_session_service.create_session.call_args.kwargs
        assert call_kwargs["user_id"] == "user-123"
        assert call_kwargs["ip_address"] == "192.168.1.1"
        assert call_kwargs["user_agent"] == "Mozilla"


class TestAuthenticateException:
    """Tests for exception handling."""

    @pytest.mark.asyncio
    async def test_authenticate_handles_exception(
        self, auth_service, mock_db_service, login_credentials
    ):
        """authenticate_user should return None on exception."""
        mock_db_service.is_account_locked = AsyncMock(
            side_effect=Exception("DB error")
        )

        with patch.object(auth_service, "_get_security_settings", return_value=(5, 900)), \
             patch.object(auth_service, "_log_security_event", new_callable=AsyncMock), \
             patch("services.auth_service.logger"):
            result = await auth_service.authenticate_user(login_credentials)

        assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_logs_exception(
        self, auth_service, mock_db_service, login_credentials
    ):
        """authenticate_user should log failed login on exception."""
        mock_db_service.is_account_locked = AsyncMock(
            side_effect=Exception("DB error")
        )

        with patch.object(auth_service, "_get_security_settings", return_value=(5, 900)), \
             patch.object(auth_service, "_log_security_event", new_callable=AsyncMock) as mock_log, \
             patch("services.auth_service.logger"):
            await auth_service.authenticate_user(login_credentials)

        # Should log LOGIN failure
        mock_log.assert_called()
        assert any(
            call[0][0] == "LOGIN" and call[0][2] is False
            for call in mock_log.call_args_list
        )


class TestAuthenticateWrongPasswordWithIp:
    """Tests for wrong password with IP tracking."""

    @pytest.mark.asyncio
    async def test_authenticate_wrong_password_records_ip(
        self, auth_service, mock_db_service, login_credentials, valid_user
    ):
        """authenticate_user should record failed attempt for IP on wrong password."""
        mock_db_service.get_user_by_username = AsyncMock(return_value=valid_user)
        mock_db_service.get_user_password_hash = AsyncMock(return_value="hashed")

        with patch.object(auth_service, "_get_security_settings", return_value=(5, 900)), \
             patch.object(auth_service, "_log_security_event", new_callable=AsyncMock), \
             patch("services.auth_service.verify_password", return_value=False), \
             patch("services.auth_service.logger"):
            await auth_service.authenticate_user(
                login_credentials, client_ip="192.168.1.1"
            )

        # Should record for both username and IP
        assert mock_db_service.record_failed_login_attempt.call_count == 2

    @pytest.mark.asyncio
    async def test_authenticate_wrong_password_locks_account(
        self, auth_service, mock_db_service, login_credentials, valid_user
    ):
        """authenticate_user should log lock event on wrong password."""
        mock_db_service.get_user_by_username = AsyncMock(return_value=valid_user)
        mock_db_service.get_user_password_hash = AsyncMock(return_value="hashed")
        mock_db_service.record_failed_login_attempt = AsyncMock(
            return_value=(True, 5, "2024-01-15T10:15:00")  # is_locked=True
        )

        with patch.object(auth_service, "_get_security_settings", return_value=(5, 900)), \
             patch.object(auth_service, "_log_security_event", new_callable=AsyncMock) as mock_log, \
             patch("services.auth_service.verify_password", return_value=False), \
             patch("services.auth_service.logger"):
            await auth_service.authenticate_user(
                login_credentials, client_ip="192.168.1.1"
            )

        # Should log ACCOUNT_LOCKED event
        assert any(
            call[0][0] == "ACCOUNT_LOCKED"
            for call in mock_log.call_args_list
        )


class TestAuthenticateSkipIpLock:
    """Tests for IP locking edge cases."""

    @pytest.mark.asyncio
    async def test_authenticate_skips_ip_lock_when_unknown(
        self, auth_service, mock_db_service, login_credentials
    ):
        """authenticate_user should skip IP lock check for 'unknown' IP."""
        mock_db_service.get_user_by_username = AsyncMock(return_value=None)

        with patch.object(auth_service, "_get_security_settings", return_value=(5, 900)), \
             patch.object(auth_service, "_log_security_event", new_callable=AsyncMock), \
             patch("services.auth_service.logger"):
            await auth_service.authenticate_user(
                login_credentials, client_ip="unknown"
            )

        # Should only record for username, not IP
        assert mock_db_service.record_failed_login_attempt.call_count == 1

    @pytest.mark.asyncio
    async def test_authenticate_skips_ip_lock_when_none(
        self, auth_service, mock_db_service, login_credentials
    ):
        """authenticate_user should skip IP lock check for None IP."""
        mock_db_service.get_user_by_username = AsyncMock(return_value=None)

        with patch.object(auth_service, "_get_security_settings", return_value=(5, 900)), \
             patch.object(auth_service, "_log_security_event", new_callable=AsyncMock), \
             patch("services.auth_service.logger"):
            await auth_service.authenticate_user(
                login_credentials, client_ip=None
            )

        # Should only check username lock, not IP
        mock_db_service.is_account_locked.assert_called_once()
