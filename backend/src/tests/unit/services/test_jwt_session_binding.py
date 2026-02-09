"""
Unit tests for JWT session binding (BE-21).

Verifies that JWT tokens are bound to sessions and rejected
after session termination (logout).
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from lib.auth_helpers import generate_jwt_token, validate_jwt_token
from models.auth import User, UserRole
from services.auth_service import AuthService


@pytest.fixture
def test_user():
    """Create test user for JWT generation."""
    return User(
        id="user-123",
        username="testuser",
        email="test@example.com",
        role=UserRole.USER,
        is_active=True,
        last_login="2025-01-01T00:00:00+00:00",
    )


@pytest.fixture
def jwt_secret():
    """JWT signing secret."""
    return "test-secret-key-for-jwt-signing"


class TestGenerateJWTWithSessionId:
    """Tests for session_id in JWT generation."""

    def test_jwt_includes_session_id(self, test_user, jwt_secret):
        """JWT payload should include session_id when provided."""
        token = generate_jwt_token(
            test_user, jwt_secret, session_id="sess_abc123"
        )
        payload = validate_jwt_token(token, jwt_secret)

        assert payload is not None
        assert payload["session_id"] == "sess_abc123"
        assert payload["user_id"] == "user-123"

    def test_jwt_without_session_id(self, test_user, jwt_secret):
        """JWT payload should not include session_id when not provided."""
        token = generate_jwt_token(test_user, jwt_secret)
        payload = validate_jwt_token(token, jwt_secret)

        assert payload is not None
        assert "session_id" not in payload

    def test_jwt_still_includes_standard_claims(self, test_user, jwt_secret):
        """JWT should still include all standard claims."""
        token = generate_jwt_token(
            test_user, jwt_secret, session_id="sess_abc123"
        )
        payload = validate_jwt_token(token, jwt_secret)

        assert "jti" in payload
        assert payload["user_id"] == "user-123"
        assert payload["username"] == "testuser"
        assert payload["role"] == "user"
        assert payload["iss"] == "tomo"
        assert "exp" in payload
        assert "iat" in payload


class TestGetUserSessionValidation:
    """Tests for session validation in AuthService.get_user()."""

    @pytest.fixture
    def mock_db_service(self):
        """Create mock database service."""
        db = MagicMock()
        return db

    @pytest.fixture
    def mock_session_service(self):
        """Create mock session service."""
        return MagicMock()

    @pytest.fixture
    def auth_service(self, jwt_secret, mock_db_service, mock_session_service):
        """Create AuthService with mocks."""
        return AuthService(
            jwt_secret=jwt_secret,
            db_service=mock_db_service,
            session_service=mock_session_service,
        )

    @pytest.mark.asyncio
    async def test_valid_token_with_active_session(
        self, auth_service, test_user, jwt_secret, mock_session_service, mock_db_service
    ):
        """get_user should return user when session is active."""
        token = generate_jwt_token(
            test_user, jwt_secret, session_id="sess_active"
        )

        # Mock active session
        mock_session = MagicMock()
        mock_session.status = "active"
        mock_session_service.validate_session = AsyncMock(
            return_value=mock_session
        )

        mock_db_service.get_user = AsyncMock(return_value=test_user)

        user = await auth_service.get_user(token=token)
        assert user is not None
        assert user.id == "user-123"

        # Verify session was validated
        mock_session_service.validate_session.assert_called_once_with(
            "sess_active"
        )

    @pytest.mark.asyncio
    async def test_valid_token_with_terminated_session(
        self, auth_service, test_user, jwt_secret, mock_session_service
    ):
        """get_user should return None when session is terminated."""
        token = generate_jwt_token(
            test_user, jwt_secret, session_id="sess_terminated"
        )

        # Mock terminated session (validate_session returns None)
        mock_session_service.validate_session = AsyncMock(return_value=None)

        user = await auth_service.get_user(token=token)
        assert user is None

    @pytest.mark.asyncio
    async def test_valid_token_without_session_id(
        self, auth_service, test_user, jwt_secret, mock_session_service, mock_db_service
    ):
        """get_user should work for tokens without session_id (backward compat)."""
        token = generate_jwt_token(test_user, jwt_secret)

        mock_db_service.get_user = AsyncMock(return_value=test_user)

        user = await auth_service.get_user(token=token)
        assert user is not None

        # Session validation should not be called
        mock_session_service.validate_session.assert_not_called()

    @pytest.mark.asyncio
    async def test_invalid_token_rejected(self, auth_service):
        """get_user should return None for invalid tokens."""
        user = await auth_service.get_user(token="invalid-token")
        assert user is None

    @pytest.mark.asyncio
    async def test_logout_invalidates_subsequent_jwt(
        self, auth_service, test_user, jwt_secret, mock_session_service, mock_db_service
    ):
        """After logout, JWT with that session should be rejected."""
        token = generate_jwt_token(
            test_user, jwt_secret, session_id="sess_logout_test"
        )

        # First call: session is active
        mock_session = MagicMock()
        mock_session.status = "active"
        mock_session_service.validate_session = AsyncMock(
            return_value=mock_session
        )
        mock_db_service.get_user = AsyncMock(return_value=test_user)

        user = await auth_service.get_user(token=token)
        assert user is not None

        # After logout: session is terminated
        mock_session_service.validate_session = AsyncMock(return_value=None)

        user = await auth_service.get_user(token=token)
        assert user is None


class TestAuthenticateUserSessionBinding:
    """Tests for session binding during authentication."""

    @pytest.fixture
    def mock_db_service(self):
        """Create mock database service."""
        db = MagicMock()
        db.verify_database_connection = AsyncMock(return_value=True)
        return db

    @pytest.fixture
    def mock_session_service(self):
        """Create mock session service."""
        return MagicMock()

    @pytest.fixture
    def auth_service(self, jwt_secret, mock_db_service, mock_session_service):
        """Create AuthService with mocks."""
        return AuthService(
            jwt_secret=jwt_secret,
            db_service=mock_db_service,
            session_service=mock_session_service,
        )

    @pytest.mark.asyncio
    async def test_session_created_before_jwt(
        self,
        auth_service,
        test_user,
        jwt_secret,
        mock_db_service,
        mock_session_service,
    ):
        """Session should be created before JWT to bind session_id."""
        from models.auth import LoginCredentials

        mock_db_service.is_account_locked = AsyncMock(
            return_value=(False, None)
        )
        mock_db_service.get_user_by_username = AsyncMock(
            return_value=test_user
        )
        mock_db_service.get_user_password_hash = AsyncMock(
            return_value="$hash$"
        )
        mock_db_service.clear_failed_attempts = AsyncMock()
        mock_db_service.update_user_last_login = AsyncMock()

        mock_session = MagicMock()
        mock_session.id = "sess_new123"
        mock_session_service.create_session = AsyncMock(
            return_value=mock_session
        )

        credentials = LoginCredentials(username="testuser", password="pass")

        with patch("services.auth_service.verify_password", return_value=True):
            response = await auth_service.authenticate_user(credentials)

        assert response is not None
        assert response.session_id == "sess_new123"

        # Verify session was created
        mock_session_service.create_session.assert_called_once()

        # Decode the JWT and verify session_id is present
        payload = validate_jwt_token(response.token, jwt_secret)
        assert payload is not None
        assert payload["session_id"] == "sess_new123"
