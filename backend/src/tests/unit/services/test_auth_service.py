"""
Auth Service Unit Tests

Tests for authentication service.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.auth import User, UserRole
from services.auth_service import AuthService


@pytest.fixture
def mock_db_service():
    """Create mock database service."""
    return MagicMock()


@pytest.fixture
def mock_session_service():
    """Create mock session service."""
    return MagicMock()


@pytest.fixture
def mock_log_service():
    """Create mock log service."""
    return MagicMock()


@pytest.fixture
def auth_service(mock_db_service, mock_session_service, mock_log_service):
    """Create AuthService instance with mocked dependencies."""
    with patch("services.auth_service.logger"):
        service = AuthService(
            jwt_secret="test-secret-key",
            db_service=mock_db_service,
            session_service=mock_session_service,
            log_service=mock_log_service,
        )
        return service


class TestAuthServiceInit:
    """Tests for AuthService initialization."""

    def test_init_with_jwt_secret(self, mock_db_service, mock_session_service):
        """AuthService should store provided jwt_secret."""
        with patch("services.auth_service.logger"):
            service = AuthService(
                jwt_secret="my-secret",
                db_service=mock_db_service,
                session_service=mock_session_service,
            )
        assert service.jwt_secret == "my-secret"

    def test_init_from_env(self, mock_db_service, mock_session_service):
        """AuthService should get jwt_secret from environment."""
        with (
            patch.dict("os.environ", {"JWT_SECRET_KEY": "env-secret"}),
            patch("services.auth_service.logger"),
        ):
            service = AuthService(
                db_service=mock_db_service,
                session_service=mock_session_service,
            )
        assert service.jwt_secret == "env-secret"

    def test_init_raises_without_secret(self, mock_db_service):
        """AuthService should raise ValueError without jwt_secret."""
        with (
            patch.dict("os.environ", {}, clear=True),
            patch("services.auth_service.logger"),
        ):
            # Clear the JWT_SECRET_KEY env var
            with patch("os.getenv", return_value=None):
                with pytest.raises(ValueError) as exc_info:
                    AuthService(db_service=mock_db_service)
                assert "JWT_SECRET_KEY" in str(exc_info.value)

    def test_init_creates_default_db_service(self):
        """AuthService should create DatabaseService if not provided."""
        with (
            patch("services.auth_service.DatabaseService") as MockDB,
            patch("services.auth_service.SessionService"),
            patch("services.auth_service.logger"),
        ):
            MockDB.return_value = MagicMock()
            AuthService(jwt_secret="secret")
            MockDB.assert_called_once()

    def test_init_creates_session_service(self, mock_db_service):
        """AuthService should create SessionService if not provided."""
        with (
            patch("services.auth_service.SessionService") as MockSS,
            patch("services.auth_service.logger"),
        ):
            MockSS.return_value = MagicMock()
            AuthService(jwt_secret="secret", db_service=mock_db_service)
            MockSS.assert_called_once_with(db_service=mock_db_service)

    def test_init_default_settings(self, mock_db_service, mock_session_service):
        """AuthService should have correct default settings."""
        with patch("services.auth_service.logger"):
            service = AuthService(
                jwt_secret="secret",
                db_service=mock_db_service,
                session_service=mock_session_service,
            )
        assert service.jwt_algorithm == "HS256"
        assert service.token_expiry_hours == 24


class TestHasAdminUser:
    """Tests for the has_admin_user method."""

    @pytest.mark.asyncio
    async def test_has_admin_user_returns_false(self, auth_service, mock_db_service):
        """has_admin_user should return False when no admins."""
        mock_db_service.has_admin_user = AsyncMock(return_value=False)
        result = await auth_service.has_admin_user()
        assert result is False

    @pytest.mark.asyncio
    async def test_has_admin_user_returns_true(self, auth_service, mock_db_service):
        """has_admin_user should return True when admin exists."""
        mock_db_service.has_admin_user = AsyncMock(return_value=True)
        result = await auth_service.has_admin_user()
        assert result is True


class TestVerifyDatabaseConnection:
    """Tests for _verify_database_connection method."""

    @pytest.mark.asyncio
    async def test_verify_database_connection_success(
        self, auth_service, mock_db_service
    ):
        """_verify_database_connection should delegate to db_service."""
        mock_db_service.verify_database_connection = AsyncMock(return_value=True)
        result = await auth_service._verify_database_connection()
        assert result is True

    @pytest.mark.asyncio
    async def test_verify_database_connection_failure(
        self, auth_service, mock_db_service
    ):
        """_verify_database_connection should return False on failure."""
        mock_db_service.verify_database_connection = AsyncMock(return_value=False)
        result = await auth_service._verify_database_connection()
        assert result is False


class TestLogSecurityEvent:
    """Tests for _log_security_event method."""

    @pytest.mark.asyncio
    async def test_log_security_event_success(self, auth_service):
        """_log_security_event should log event successfully."""
        auth_service._log_service.create_log_entry = AsyncMock()
        with patch("services.auth_service.logger"):
            await auth_service._log_security_event(
                "LOGIN", "testuser", True, "192.168.1.1", "Mozilla/5.0"
            )
            auth_service._log_service.create_log_entry.assert_called_once()

    @pytest.mark.asyncio
    async def test_log_security_event_failed_login(self, auth_service):
        """_log_security_event should log failed event with WARNING level."""
        auth_service._log_service.create_log_entry = AsyncMock()
        with patch("services.auth_service.logger"):
            await auth_service._log_security_event("LOGIN", "testuser", False)
            call_args = auth_service._log_service.create_log_entry.call_args[0][0]
            assert call_args.level == "WARNING"

    @pytest.mark.asyncio
    async def test_log_security_event_handles_error(self, auth_service):
        """_log_security_event should handle errors gracefully."""
        auth_service._log_service.create_log_entry = AsyncMock(
            side_effect=Exception("Log error")
        )
        with patch("services.auth_service.logger"):
            # Should not raise
            await auth_service._log_security_event("LOGIN", "testuser", True)


class TestGetSecuritySettings:
    """Tests for _get_security_settings method."""

    @pytest.mark.asyncio
    async def test_get_security_settings_from_db(self, auth_service, mock_db_service):
        """_get_security_settings should load settings from database."""
        import json

        mock_cursor = MagicMock()
        mock_cursor.fetchone = AsyncMock(
            side_effect=[
                (json.dumps(10),),  # max_login_attempts
                (json.dumps(1800),),  # lockout_duration
            ]
        )
        mock_conn = MagicMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)

        mock_context = MagicMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        mock_db_service.get_connection = MagicMock(return_value=mock_context)

        with patch("services.auth_service.logger"):
            max_attempts, lock_duration = await auth_service._get_security_settings()

        assert max_attempts == 10
        assert lock_duration == 1800

    @pytest.mark.asyncio
    async def test_get_security_settings_uses_defaults(
        self, auth_service, mock_db_service
    ):
        """_get_security_settings should use defaults on error."""
        mock_db_service.get_connection = MagicMock(side_effect=Exception("DB error"))

        with patch("services.auth_service.logger"):
            max_attempts, lock_duration = await auth_service._get_security_settings()

        assert max_attempts == AuthService.DEFAULT_MAX_LOGIN_ATTEMPTS
        assert lock_duration == AuthService.DEFAULT_LOCK_DURATION_SECONDS

    @pytest.mark.asyncio
    async def test_get_security_settings_partial_settings(
        self, auth_service, mock_db_service
    ):
        """_get_security_settings should handle partial settings."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone = AsyncMock(return_value=None)
        mock_conn = MagicMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)

        mock_context = MagicMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        mock_db_service.get_connection = MagicMock(return_value=mock_context)

        with patch("services.auth_service.logger"):
            max_attempts, lock_duration = await auth_service._get_security_settings()

        # Should use defaults when no settings found
        assert max_attempts == AuthService.DEFAULT_MAX_LOGIN_ATTEMPTS
        assert lock_duration == AuthService.DEFAULT_LOCK_DURATION_SECONDS


class TestValidateJwtToken:
    """Tests for _validate_jwt_token method."""

    def test_validate_jwt_token_valid(self, auth_service):
        """_validate_jwt_token should validate valid tokens."""
        with patch("services.auth_service.validate_jwt_token") as mock_validate:
            mock_validate.return_value = {"user_id": "user-123"}
            result = auth_service._validate_jwt_token("valid-token")
            assert result == {"user_id": "user-123"}
            mock_validate.assert_called_once_with(
                "valid-token", "test-secret-key", "HS256"
            )

    def test_validate_jwt_token_invalid(self, auth_service):
        """_validate_jwt_token should return None for invalid tokens."""
        with patch("services.auth_service.validate_jwt_token") as mock_validate:
            mock_validate.return_value = None
            result = auth_service._validate_jwt_token("invalid-token")
            assert result is None


class TestGetUser:
    """Tests for get_user method."""

    @pytest.mark.asyncio
    async def test_get_user_by_token(self, auth_service, mock_db_service):
        """get_user should validate token and get user."""
        mock_user = MagicMock(spec=User)
        mock_db_service.get_user = AsyncMock(return_value=mock_user)

        with patch.object(
            auth_service, "_validate_jwt_token", return_value={"user_id": "user-123"}
        ):
            result = await auth_service.get_user(token="valid-token")

        assert result is mock_user
        mock_db_service.get_user.assert_called_once_with(
            user_id="user-123", username=None
        )

    @pytest.mark.asyncio
    async def test_get_user_invalid_token(self, auth_service):
        """get_user should return None for invalid token."""
        with patch.object(auth_service, "_validate_jwt_token", return_value=None):
            result = await auth_service.get_user(token="invalid-token")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_user_by_id(self, auth_service, mock_db_service):
        """get_user should get user by ID."""
        mock_user = MagicMock(spec=User)
        mock_db_service.get_user = AsyncMock(return_value=mock_user)

        result = await auth_service.get_user(user_id="user-123")

        assert result is mock_user
        mock_db_service.get_user.assert_called_once_with(
            user_id="user-123", username=None
        )

    @pytest.mark.asyncio
    async def test_get_user_by_username(self, auth_service, mock_db_service):
        """get_user should get user by username."""
        mock_user = MagicMock(spec=User)
        mock_db_service.get_user = AsyncMock(return_value=mock_user)

        result = await auth_service.get_user(username="testuser")

        assert result is mock_user
        mock_db_service.get_user.assert_called_once_with(
            user_id=None, username="testuser"
        )


class TestGetUserWrappers:
    """Tests for backward compatibility wrappers."""

    @pytest.mark.asyncio
    async def test_get_user_by_username_wrapper(self, auth_service, mock_db_service):
        """get_user_by_username should delegate to get_user."""
        mock_user = MagicMock(spec=User)
        mock_db_service.get_user = AsyncMock(return_value=mock_user)

        result = await auth_service.get_user_by_username("testuser")

        assert result is mock_user

    @pytest.mark.asyncio
    async def test_get_user_by_id_wrapper(self, auth_service, mock_db_service):
        """get_user_by_id should delegate to get_user."""
        mock_user = MagicMock(spec=User)
        mock_db_service.get_user = AsyncMock(return_value=mock_user)

        result = await auth_service.get_user_by_id("user-123")

        assert result is mock_user


class TestGetAllUsers:
    """Tests for get_all_users method."""

    @pytest.mark.asyncio
    async def test_get_all_users(self, auth_service, mock_db_service):
        """get_all_users should delegate to db_service."""
        mock_users = [MagicMock(spec=User), MagicMock(spec=User)]
        mock_db_service.get_all_users = AsyncMock(return_value=mock_users)

        result = await auth_service.get_all_users()

        assert result == mock_users
        mock_db_service.get_all_users.assert_called_once()


class TestCreateUser:
    """Tests for create_user method."""

    @pytest.mark.asyncio
    async def test_create_user_success(self, auth_service, mock_db_service):
        """create_user should create user with hashed password."""
        mock_user = MagicMock(spec=User)
        mock_db_service.create_user = AsyncMock(return_value=mock_user)

        with (
            patch("services.auth_service.logger"),
            patch("lib.auth_helpers.hash_password", return_value="hashed-pwd"),
        ):
            result = await auth_service.create_user(
                username="newuser",
                password="password123",
                email="user@example.com",
                role=UserRole.ADMIN,
            )

        assert result is mock_user
        mock_db_service.create_user.assert_called_once()
        call_kwargs = mock_db_service.create_user.call_args.kwargs
        assert call_kwargs["username"] == "newuser"
        assert call_kwargs["password_hash"] == "hashed-pwd"
        assert call_kwargs["email"] == "user@example.com"
        assert call_kwargs["role"] == UserRole.ADMIN

    @pytest.mark.asyncio
    async def test_create_user_default_role(self, auth_service, mock_db_service):
        """create_user should use USER role by default."""
        mock_db_service.create_user = AsyncMock(return_value=MagicMock())

        with (
            patch("services.auth_service.logger"),
            patch("lib.auth_helpers.hash_password", return_value="hashed"),
        ):
            await auth_service.create_user(
                username="newuser",
                password="password123",
            )

        call_kwargs = mock_db_service.create_user.call_args.kwargs
        assert call_kwargs["role"] == UserRole.USER

    @pytest.mark.asyncio
    async def test_create_user_error(self, auth_service, mock_db_service):
        """create_user should return None on error."""
        mock_db_service.create_user = AsyncMock(side_effect=Exception("DB error"))

        with (
            patch("services.auth_service.logger"),
            patch("lib.auth_helpers.hash_password", return_value="hashed"),
        ):
            result = await auth_service.create_user(
                username="newuser",
                password="password123",
            )

        assert result is None
