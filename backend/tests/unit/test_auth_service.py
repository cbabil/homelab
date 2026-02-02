"""
Unit tests for services/auth_service.py

Tests for user authentication, JWT token management, and session control.
"""

from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import services.auth_service as auth_module
from models.auth import LoginCredentials, LoginResponse, User, UserRole
from services.auth_service import AuthService


@pytest.fixture
def mock_db_service():
    """Create mock DatabaseService."""
    return AsyncMock()


@pytest.fixture
def mock_session_service():
    """Create mock SessionService."""
    return AsyncMock()


@pytest.fixture
def auth_service(mock_db_service, mock_session_service):
    """Create AuthService with mocked dependencies."""
    with patch.object(auth_module, "logger"):
        return AuthService(
            jwt_secret="test-secret-key-for-jwt-signing",
            db_service=mock_db_service,
            session_service=mock_session_service,
        )


@pytest.fixture
def sample_user():
    """Create sample user for testing."""
    return User(
        id="user-123",
        username="testuser",
        email="test@example.com",
        role=UserRole.USER,
        is_active=True,
        created_at=datetime.now(UTC).isoformat(),
        last_login=datetime.now(UTC).isoformat(),
    )


@pytest.fixture
def admin_user():
    """Create admin user for testing."""
    return User(
        id="admin-123",
        username="admin",
        email="admin@example.com",
        role=UserRole.ADMIN,
        is_active=True,
        created_at=datetime.now(UTC).isoformat(),
        last_login=datetime.now(UTC).isoformat(),
    )


class TestAuthServiceInit:
    """Tests for AuthService initialization."""

    def test_init_with_provided_jwt_secret(self, mock_db_service, mock_session_service):
        """Should initialize with provided JWT secret."""
        with patch.object(auth_module, "logger"):
            service = AuthService(
                jwt_secret="my-secret",
                db_service=mock_db_service,
                session_service=mock_session_service,
            )

            assert service.jwt_secret == "my-secret"
            assert service.jwt_algorithm == "HS256"
            assert service.token_expiry_hours == 24

    def test_init_with_env_jwt_secret(self, mock_db_service, mock_session_service):
        """Should use JWT secret from environment variable."""
        with (
            patch.object(auth_module, "logger"),
            patch.dict("os.environ", {"JWT_SECRET_KEY": "env-secret"}),
        ):
            service = AuthService(
                db_service=mock_db_service,
                session_service=mock_session_service,
            )

            assert service.jwt_secret == "env-secret"

    def test_init_without_jwt_secret_raises(self, mock_db_service, mock_session_service):
        """Should raise ValueError when JWT secret is missing."""
        with (
            patch.object(auth_module, "logger"),
            patch.dict("os.environ", {}, clear=True),
            pytest.raises(ValueError) as exc_info,
        ):
            AuthService(
                db_service=mock_db_service,
                session_service=mock_session_service,
            )

        assert "JWT_SECRET_KEY" in str(exc_info.value)

    def test_init_creates_default_db_service(self, mock_session_service):
        """Should create default DatabaseService if not provided."""
        with (
            patch.object(auth_module, "logger"),
            patch.object(auth_module, "DatabaseService") as mock_db_cls,
        ):
            mock_db_cls.return_value = MagicMock()

            service = AuthService(
                jwt_secret="secret",
                session_service=mock_session_service,
            )

            assert service.db_service is mock_db_cls.return_value

    def test_init_creates_default_session_service(self, mock_db_service):
        """Should create default SessionService if not provided."""
        with (
            patch.object(auth_module, "logger"),
            patch.object(auth_module, "SessionService") as mock_session_cls,
        ):
            mock_session_cls.return_value = MagicMock()

            service = AuthService(
                jwt_secret="secret",
                db_service=mock_db_service,
            )

            assert service.session_service is mock_session_cls.return_value


class TestVerifyDatabaseConnection:
    """Tests for _verify_database_connection method."""

    @pytest.mark.asyncio
    async def test_verify_database_connection_delegates(
        self, auth_service, mock_db_service
    ):
        """Should delegate to db_service."""
        mock_db_service.verify_database_connection.return_value = True

        result = await auth_service._verify_database_connection()

        assert result is True
        mock_db_service.verify_database_connection.assert_called_once()


class TestLogSecurityEvent:
    """Tests for _log_security_event method."""

    @pytest.mark.asyncio
    async def test_log_security_event_success(self, auth_service):
        """Should log successful security event."""
        with patch.object(auth_module, "log_service") as mock_log_service:
            mock_log_service.create_log_entry = AsyncMock()

            await auth_service._log_security_event(
                "LOGIN", "testuser", True, client_ip="192.168.1.1", user_agent="TestUA"
            )

            mock_log_service.create_log_entry.assert_called_once()
            log_entry = mock_log_service.create_log_entry.call_args[0][0]
            assert log_entry.level == "INFO"
            assert "successful" in log_entry.message

    @pytest.mark.asyncio
    async def test_log_security_event_failure(self, auth_service):
        """Should log failed security event."""
        with patch.object(auth_module, "log_service") as mock_log_service:
            mock_log_service.create_log_entry = AsyncMock()

            await auth_service._log_security_event(
                "LOGIN", "testuser", False, client_ip="192.168.1.1"
            )

            mock_log_service.create_log_entry.assert_called_once()
            log_entry = mock_log_service.create_log_entry.call_args[0][0]
            assert log_entry.level == "WARNING"
            assert "failed" in log_entry.message

    @pytest.mark.asyncio
    async def test_log_security_event_handles_exception(self, auth_service):
        """Should handle exceptions when logging fails."""
        with (
            patch.object(auth_module, "log_service") as mock_log_service,
            patch.object(auth_module, "logger") as mock_logger,
        ):
            mock_log_service.create_log_entry = AsyncMock(
                side_effect=RuntimeError("Log failed")
            )

            # Should not raise
            await auth_service._log_security_event("LOGIN", "testuser", True)

            mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_log_security_event_without_client_ip(self, auth_service):
        """Should log event without client IP."""
        with patch.object(auth_module, "log_service") as mock_log_service:
            mock_log_service.create_log_entry = AsyncMock()

            await auth_service._log_security_event("LOGIN", "testuser", True)

            log_entry = mock_log_service.create_log_entry.call_args[0][0]
            assert "unknown" in log_entry.metadata["client_ip"]


class TestGetSecuritySettings:
    """Tests for _get_security_settings method."""

    @pytest.mark.asyncio
    async def test_get_security_settings_from_database(
        self, auth_service, mock_db_service
    ):
        """Should get settings from database."""
        import json

        mock_conn = AsyncMock()
        mock_cursor1 = AsyncMock()
        mock_cursor2 = AsyncMock()

        # Each execute call gets its own cursor with its own fetchone result
        mock_cursor1.fetchone.return_value = (json.dumps(10),)
        mock_cursor2.fetchone.return_value = (json.dumps(1800),)
        mock_conn.execute.side_effect = [mock_cursor1, mock_cursor2]

        @asynccontextmanager
        async def mock_get_connection():
            yield mock_conn

        mock_db_service.get_connection = mock_get_connection

        max_attempts, lock_duration = await auth_service._get_security_settings()

        assert max_attempts == 10
        assert lock_duration == 1800

    @pytest.mark.asyncio
    async def test_get_security_settings_defaults(self, auth_service, mock_db_service):
        """Should use defaults when database query fails."""
        mock_db_service.get_connection.return_value.__aenter__.side_effect = (
            RuntimeError("DB error")
        )

        with patch.object(auth_module, "logger"):
            max_attempts, lock_duration = await auth_service._get_security_settings()

        assert max_attempts == AuthService.DEFAULT_MAX_LOGIN_ATTEMPTS
        assert lock_duration == AuthService.DEFAULT_LOCK_DURATION_SECONDS

    @pytest.mark.asyncio
    async def test_get_security_settings_partial_data(
        self, auth_service, mock_db_service
    ):
        """Should handle partial data from database."""
        import json

        mock_conn = AsyncMock()
        mock_cursor1 = AsyncMock()
        mock_cursor2 = AsyncMock()

        # First query returns JSON value, second returns None
        mock_cursor1.fetchone.return_value = (json.dumps(7),)
        mock_cursor2.fetchone.return_value = None
        mock_conn.execute.side_effect = [mock_cursor1, mock_cursor2]

        @asynccontextmanager
        async def mock_get_connection():
            yield mock_conn

        mock_db_service.get_connection = mock_get_connection

        max_attempts, lock_duration = await auth_service._get_security_settings()

        assert max_attempts == 7
        assert lock_duration == AuthService.DEFAULT_LOCK_DURATION_SECONDS


class TestAuthenticateUser:
    """Tests for authenticate_user method."""

    @pytest.mark.asyncio
    async def test_authenticate_user_username_locked(
        self, auth_service, mock_db_service
    ):
        """Should reject when username is locked."""
        mock_db_service.is_account_locked.return_value = (
            True,
            {"lock_expires_at": datetime.now(UTC).isoformat()},
        )

        with (
            patch.object(auth_module, "logger"),
            patch.object(
                auth_service, "_log_security_event", new_callable=AsyncMock
            ) as mock_log,
            patch.object(
                auth_service,
                "_get_security_settings",
                new_callable=AsyncMock,
                return_value=(5, 900),
            ),
        ):
            credentials = LoginCredentials(username="locked_user", password="pass")
            result = await auth_service.authenticate_user(credentials)

            assert result is None
            mock_log.assert_called()

    @pytest.mark.asyncio
    async def test_authenticate_user_ip_locked(self, auth_service, mock_db_service):
        """Should reject when IP is locked."""
        # Username not locked, but IP is locked
        mock_db_service.is_account_locked.side_effect = [
            (False, {}),  # username check
            (True, {"lock_expires_at": datetime.now(UTC).isoformat()}),  # IP check
        ]

        with (
            patch.object(auth_module, "logger"),
            patch.object(
                auth_service, "_log_security_event", new_callable=AsyncMock
            ),
            patch.object(
                auth_service,
                "_get_security_settings",
                new_callable=AsyncMock,
                return_value=(5, 900),
            ),
        ):
            credentials = LoginCredentials(username="user", password="pass")
            result = await auth_service.authenticate_user(
                credentials, client_ip="192.168.1.100"
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self, auth_service, mock_db_service):
        """Should reject when user not found."""
        mock_db_service.is_account_locked.return_value = (False, {})
        mock_db_service.get_user_by_username.return_value = None
        mock_db_service.record_failed_login_attempt.return_value = (False, 1, None)

        with (
            patch.object(auth_module, "logger"),
            patch.object(
                auth_service, "_log_security_event", new_callable=AsyncMock
            ),
            patch.object(
                auth_service,
                "_get_security_settings",
                new_callable=AsyncMock,
                return_value=(5, 900),
            ),
        ):
            credentials = LoginCredentials(username="nonexistent", password="pass")
            result = await auth_service.authenticate_user(credentials)

            assert result is None
            mock_db_service.record_failed_login_attempt.assert_called()

    @pytest.mark.asyncio
    async def test_authenticate_user_inactive(
        self, auth_service, mock_db_service, sample_user
    ):
        """Should reject when user is inactive."""
        sample_user.is_active = False
        mock_db_service.is_account_locked.return_value = (False, {})
        mock_db_service.get_user_by_username.return_value = sample_user
        mock_db_service.record_failed_login_attempt.return_value = (False, 1, None)

        with (
            patch.object(auth_module, "logger"),
            patch.object(
                auth_service, "_log_security_event", new_callable=AsyncMock
            ),
            patch.object(
                auth_service,
                "_get_security_settings",
                new_callable=AsyncMock,
                return_value=(5, 900),
            ),
        ):
            credentials = LoginCredentials(username="testuser", password="pass")
            result = await auth_service.authenticate_user(credentials)

            assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_user_invalid_password(
        self, auth_service, mock_db_service, sample_user
    ):
        """Should reject when password is invalid."""
        mock_db_service.is_account_locked.return_value = (False, {})
        mock_db_service.get_user_by_username.return_value = sample_user
        mock_db_service.get_user_password_hash.return_value = "hashed_password"
        mock_db_service.record_failed_login_attempt.return_value = (False, 1, None)

        with (
            patch.object(auth_module, "logger"),
            patch.object(
                auth_service, "_log_security_event", new_callable=AsyncMock
            ),
            patch.object(
                auth_service,
                "_get_security_settings",
                new_callable=AsyncMock,
                return_value=(5, 900),
            ),
            patch.object(auth_module, "verify_password", return_value=False),
        ):
            credentials = LoginCredentials(username="testuser", password="wrong")
            result = await auth_service.authenticate_user(credentials)

            assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_user_no_password_hash(
        self, auth_service, mock_db_service, sample_user
    ):
        """Should reject when no password hash stored."""
        mock_db_service.is_account_locked.return_value = (False, {})
        mock_db_service.get_user_by_username.return_value = sample_user
        mock_db_service.get_user_password_hash.return_value = None
        mock_db_service.record_failed_login_attempt.return_value = (False, 1, None)

        with (
            patch.object(auth_module, "logger"),
            patch.object(
                auth_service, "_log_security_event", new_callable=AsyncMock
            ),
            patch.object(
                auth_service,
                "_get_security_settings",
                new_callable=AsyncMock,
                return_value=(5, 900),
            ),
        ):
            credentials = LoginCredentials(username="testuser", password="pass")
            result = await auth_service.authenticate_user(credentials)

            assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_user_account_locked_after_attempts(
        self, auth_service, mock_db_service, sample_user
    ):
        """Should lock account after max failed attempts."""
        mock_db_service.is_account_locked.return_value = (False, {})
        mock_db_service.get_user_by_username.return_value = sample_user
        mock_db_service.get_user_password_hash.return_value = "hash"
        mock_db_service.record_failed_login_attempt.return_value = (
            True,
            5,
            datetime.now(UTC) + timedelta(minutes=15),
        )

        with (
            patch.object(auth_module, "logger"),
            patch.object(
                auth_service, "_log_security_event", new_callable=AsyncMock
            ) as mock_log,
            patch.object(
                auth_service,
                "_get_security_settings",
                new_callable=AsyncMock,
                return_value=(5, 900),
            ),
            patch.object(auth_module, "verify_password", return_value=False),
        ):
            credentials = LoginCredentials(username="testuser", password="wrong")
            result = await auth_service.authenticate_user(credentials)

            assert result is None
            # Should log ACCOUNT_LOCKED event
            calls = [c[0][0] for c in mock_log.call_args_list]
            assert "ACCOUNT_LOCKED" in calls

    @pytest.mark.asyncio
    async def test_authenticate_user_success(
        self, auth_service, mock_db_service, mock_session_service, sample_user
    ):
        """Should authenticate successfully with valid credentials."""
        mock_db_service.is_account_locked.return_value = (False, {})
        mock_db_service.get_user_by_username.return_value = sample_user
        mock_db_service.get_user_password_hash.return_value = "hashed_password"
        mock_db_service.clear_failed_attempts = AsyncMock()
        mock_db_service.update_user_last_login = AsyncMock()

        mock_session = MagicMock()
        mock_session.id = "session-123"
        mock_session_service.create_session.return_value = mock_session

        with (
            patch.object(auth_module, "logger"),
            patch.object(
                auth_service, "_log_security_event", new_callable=AsyncMock
            ),
            patch.object(
                auth_service,
                "_get_security_settings",
                new_callable=AsyncMock,
                return_value=(5, 900),
            ),
            patch.object(auth_module, "verify_password", return_value=True),
            patch.object(
                auth_module, "generate_jwt_token", return_value="jwt-token"
            ),
            patch.object(
                auth_module, "create_session_data", return_value={"user_id": "user-123"}
            ),
        ):
            credentials = LoginCredentials(username="testuser", password="correct")
            result = await auth_service.authenticate_user(credentials)

            assert result is not None
            assert isinstance(result, LoginResponse)
            assert result.token == "jwt-token"
            assert result.session_id == "session-123"
            mock_db_service.clear_failed_attempts.assert_called()

    @pytest.mark.asyncio
    async def test_authenticate_user_success_with_ip(
        self, auth_service, mock_db_service, mock_session_service, sample_user
    ):
        """Should clear IP failed attempts on success."""
        mock_db_service.is_account_locked.return_value = (False, {})
        mock_db_service.get_user_by_username.return_value = sample_user
        mock_db_service.get_user_password_hash.return_value = "hash"
        mock_db_service.clear_failed_attempts = AsyncMock()
        mock_db_service.update_user_last_login = AsyncMock()

        mock_session = MagicMock()
        mock_session.id = "session-456"
        mock_session_service.create_session.return_value = mock_session

        with (
            patch.object(auth_module, "logger"),
            patch.object(
                auth_service, "_log_security_event", new_callable=AsyncMock
            ),
            patch.object(
                auth_service,
                "_get_security_settings",
                new_callable=AsyncMock,
                return_value=(5, 900),
            ),
            patch.object(auth_module, "verify_password", return_value=True),
            patch.object(
                auth_module, "generate_jwt_token", return_value="jwt"
            ),
            patch.object(
                auth_module, "create_session_data", return_value={}
            ),
        ):
            credentials = LoginCredentials(username="testuser", password="pass")
            result = await auth_service.authenticate_user(
                credentials, client_ip="192.168.1.1"
            )

            assert result is not None
            # Should clear failed attempts for both username and IP
            assert mock_db_service.clear_failed_attempts.call_count == 2

    @pytest.mark.asyncio
    async def test_authenticate_user_exception(self, auth_service, mock_db_service):
        """Should handle exceptions during authentication."""
        mock_db_service.is_account_locked.side_effect = RuntimeError("DB error")

        with (
            patch.object(auth_module, "logger"),
            patch.object(
                auth_service, "_log_security_event", new_callable=AsyncMock
            ),
            patch.object(
                auth_service,
                "_get_security_settings",
                new_callable=AsyncMock,
                return_value=(5, 900),
            ),
        ):
            credentials = LoginCredentials(username="user", password="pass")
            result = await auth_service.authenticate_user(credentials)

            assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_user_records_ip_attempt_on_failure(
        self, auth_service, mock_db_service
    ):
        """Should record failed attempt for IP on login failure."""
        mock_db_service.is_account_locked.return_value = (False, {})
        mock_db_service.get_user_by_username.return_value = None
        mock_db_service.record_failed_login_attempt.return_value = (False, 1, None)

        with (
            patch.object(auth_module, "logger"),
            patch.object(
                auth_service, "_log_security_event", new_callable=AsyncMock
            ),
            patch.object(
                auth_service,
                "_get_security_settings",
                new_callable=AsyncMock,
                return_value=(5, 900),
            ),
        ):
            credentials = LoginCredentials(username="user", password="pass")
            await auth_service.authenticate_user(credentials, client_ip="10.0.0.1")

            # Should record for both username and IP
            assert mock_db_service.record_failed_login_attempt.call_count == 2

    @pytest.mark.asyncio
    async def test_authenticate_user_locks_account_on_user_not_found(
        self, auth_service, mock_db_service
    ):
        """Should lock account after max failed attempts for non-existent user."""
        mock_db_service.is_account_locked.return_value = (False, {})
        mock_db_service.get_user_by_username.return_value = None
        mock_db_service.record_failed_login_attempt.return_value = (
            True,
            5,
            datetime.now(UTC) + timedelta(minutes=15),
        )

        with (
            patch.object(auth_module, "logger"),
            patch.object(
                auth_service, "_log_security_event", new_callable=AsyncMock
            ) as mock_log,
            patch.object(
                auth_service,
                "_get_security_settings",
                new_callable=AsyncMock,
                return_value=(5, 900),
            ),
        ):
            credentials = LoginCredentials(username="attacker", password="guess")
            result = await auth_service.authenticate_user(credentials)

            assert result is None
            # Should log ACCOUNT_LOCKED event
            calls = [c[0][0] for c in mock_log.call_args_list]
            assert "ACCOUNT_LOCKED" in calls

    @pytest.mark.asyncio
    async def test_authenticate_user_records_ip_on_password_failure(
        self, auth_service, mock_db_service, sample_user
    ):
        """Should record IP failed attempt when password is wrong."""
        mock_db_service.is_account_locked.return_value = (False, {})
        mock_db_service.get_user_by_username.return_value = sample_user
        mock_db_service.get_user_password_hash.return_value = "hash"
        mock_db_service.record_failed_login_attempt.return_value = (False, 1, None)

        with (
            patch.object(auth_module, "logger"),
            patch.object(
                auth_service, "_log_security_event", new_callable=AsyncMock
            ),
            patch.object(
                auth_service,
                "_get_security_settings",
                new_callable=AsyncMock,
                return_value=(5, 900),
            ),
            patch.object(auth_module, "verify_password", return_value=False),
        ):
            credentials = LoginCredentials(username="testuser", password="wrong")
            await auth_service.authenticate_user(credentials, client_ip="192.168.1.1")

            # Should record for both username and IP
            assert mock_db_service.record_failed_login_attempt.call_count == 2


class TestValidateJwtToken:
    """Tests for _validate_jwt_token method."""

    def test_validate_jwt_token_delegates(self, auth_service):
        """Should delegate to helper function."""
        with patch.object(
            auth_module, "validate_jwt_token", return_value={"user_id": "123"}
        ) as mock_validate:
            result = auth_service._validate_jwt_token("some-token")

            assert result == {"user_id": "123"}
            mock_validate.assert_called_once_with(
                "some-token",
                auth_service.jwt_secret,
                auth_service.jwt_algorithm,
            )

    def test_validate_jwt_token_invalid(self, auth_service):
        """Should return None for invalid token."""
        with patch.object(auth_module, "validate_jwt_token", return_value=None):
            result = auth_service._validate_jwt_token("invalid-token")

            assert result is None


class TestGetUser:
    """Tests for get_user method."""

    @pytest.mark.asyncio
    async def test_get_user_by_token(self, auth_service, mock_db_service, sample_user):
        """Should get user by validating token."""
        mock_db_service.get_user.return_value = sample_user

        with patch.object(
            auth_service, "_validate_jwt_token", return_value={"user_id": "user-123"}
        ):
            result = await auth_service.get_user(token="valid-token")

            assert result == sample_user
            mock_db_service.get_user.assert_called_with(
                user_id="user-123", username=None
            )

    @pytest.mark.asyncio
    async def test_get_user_by_invalid_token(self, auth_service, mock_db_service):
        """Should return None for invalid token."""
        with patch.object(auth_service, "_validate_jwt_token", return_value=None):
            result = await auth_service.get_user(token="invalid-token")

            assert result is None
            mock_db_service.get_user.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_user_by_id(self, auth_service, mock_db_service, sample_user):
        """Should get user by ID."""
        mock_db_service.get_user.return_value = sample_user

        result = await auth_service.get_user(user_id="user-123")

        assert result == sample_user
        mock_db_service.get_user.assert_called_with(user_id="user-123", username=None)

    @pytest.mark.asyncio
    async def test_get_user_by_username(
        self, auth_service, mock_db_service, sample_user
    ):
        """Should get user by username."""
        mock_db_service.get_user.return_value = sample_user

        result = await auth_service.get_user(username="testuser")

        assert result == sample_user
        mock_db_service.get_user.assert_called_with(user_id=None, username="testuser")


class TestGetUserWrappers:
    """Tests for get_user wrapper methods."""

    @pytest.mark.asyncio
    async def test_get_user_by_username_wrapper(
        self, auth_service, mock_db_service, sample_user
    ):
        """Should delegate to get_user."""
        mock_db_service.get_user.return_value = sample_user

        result = await auth_service.get_user_by_username("testuser")

        assert result == sample_user

    @pytest.mark.asyncio
    async def test_get_user_by_id_wrapper(
        self, auth_service, mock_db_service, sample_user
    ):
        """Should delegate to get_user."""
        mock_db_service.get_user.return_value = sample_user

        result = await auth_service.get_user_by_id("user-123")

        assert result == sample_user


class TestGetAllUsers:
    """Tests for get_all_users method."""

    @pytest.mark.asyncio
    async def test_get_all_users(self, auth_service, mock_db_service, sample_user):
        """Should delegate to db_service."""
        mock_db_service.get_all_users.return_value = [sample_user]

        result = await auth_service.get_all_users()

        assert result == [sample_user]
        mock_db_service.get_all_users.assert_called_once()


class TestHasAdminUser:
    """Tests for has_admin_user method."""

    @pytest.mark.asyncio
    async def test_has_admin_user_true(self, auth_service, mock_db_service):
        """Should return True when admin exists."""
        mock_db_service.has_admin_user.return_value = True

        result = await auth_service.has_admin_user()

        assert result is True
        mock_db_service.has_admin_user.assert_called_once()

    @pytest.mark.asyncio
    async def test_has_admin_user_false(self, auth_service, mock_db_service):
        """Should return False when no admin exists."""
        mock_db_service.has_admin_user.return_value = False

        result = await auth_service.has_admin_user()

        assert result is False


class TestCreateUser:
    """Tests for create_user method."""

    @pytest.mark.asyncio
    async def test_create_user_success(
        self, auth_service, mock_db_service, sample_user
    ):
        """Should create user successfully."""
        mock_db_service.create_user.return_value = sample_user

        with (
            patch.object(auth_module, "logger"),
            patch("lib.auth_helpers.hash_password", return_value="hashed") as mock_hash,
        ):
            result = await auth_service.create_user(
                username="newuser",
                password="password123",
                email="new@example.com",
                role=UserRole.USER,
            )

            assert result == sample_user
            mock_hash.assert_called_once_with("password123")
            mock_db_service.create_user.assert_called_once_with(
                username="newuser",
                password_hash="hashed",
                email="new@example.com",
                role=UserRole.USER,
            )

    @pytest.mark.asyncio
    async def test_create_user_failure(self, auth_service, mock_db_service):
        """Should return None on failure."""
        mock_db_service.create_user.side_effect = RuntimeError("DB error")

        with (
            patch.object(auth_module, "logger") as mock_logger,
            patch("lib.auth_helpers.hash_password", return_value="hashed"),
        ):
            result = await auth_service.create_user(
                username="newuser",
                password="pass",
            )

            assert result is None
            mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_user_default_values(self, auth_service, mock_db_service):
        """Should use default values for email and role."""
        mock_db_service.create_user.return_value = MagicMock()

        with (
            patch.object(auth_module, "logger"),
            patch("lib.auth_helpers.hash_password", return_value="hashed"),
        ):
            await auth_service.create_user(
                username="newuser",
                password="pass",
            )

            mock_db_service.create_user.assert_called_once_with(
                username="newuser",
                password_hash="hashed",
                email="",
                role=UserRole.USER,
            )
