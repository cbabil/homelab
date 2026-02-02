"""
Unit Tests for Authentication Service

Tests the authentication service including JWT token management and user validation.
Ensures secure authentication functionality.
"""

import pytest
from models.auth import LoginCredentials, UserRole
from services.auth_service import AuthService
from lib.auth_helpers import (
    hash_password,
    verify_password,
    generate_jwt_token,
    validate_jwt_token,
    create_default_admin,
)


@pytest.mark.unit
@pytest.mark.security
class TestAuthService:
    """Test cases for AuthService class."""

    @pytest.fixture
    def auth_service(self):
        """Create AuthService instance for testing."""
        return AuthService(jwt_secret="test-secret-key")

    @pytest.fixture
    def test_user(self):
        """Create a test user for token tests."""
        return create_default_admin()

    @pytest.mark.asyncio
    async def test_authenticate_valid_admin(self, auth_service):
        """Test successful authentication with admin credentials."""
        credentials = LoginCredentials(
            username="admin",
            password="admin123",
            remember_me=False
        )

        response = await auth_service.authenticate_user(credentials)

        assert response is not None
        assert response.user.username == "admin"
        assert response.user.role == UserRole.ADMIN
        assert response.token is not None
        assert response.expires_in > 0
        assert response.session_id is not None

    @pytest.mark.asyncio
    async def test_authenticate_invalid_username(self, auth_service):
        """Test authentication with invalid username."""
        credentials = LoginCredentials(
            username="nonexistent",
            password="admin123",
            remember_me=False
        )

        response = await auth_service.authenticate_user(credentials)

        assert response is None

    @pytest.mark.asyncio
    async def test_authenticate_invalid_password(self, auth_service):
        """Test authentication with invalid password."""
        credentials = LoginCredentials(
            username="admin",
            password="wrongpassword",
            remember_me=False
        )

        response = await auth_service.authenticate_user(credentials)

        assert response is None

    def test_hash_password(self):
        """Test password hashing functionality."""
        password = "testpassword123"
        hashed = hash_password(password)

        assert hashed is not None
        assert isinstance(hashed, str)
        assert len(hashed) > 0
        # Verify password can be verified
        assert verify_password(password, hashed)

    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "testpassword123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False

    def test_generate_jwt_token(self, auth_service, test_user):
        """Test JWT token generation."""
        token = generate_jwt_token(test_user, auth_service.jwt_secret)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

        # Verify token can be decoded
        payload = validate_jwt_token(token, auth_service.jwt_secret)
        assert payload is not None
        assert payload["username"] == test_user.username
        assert payload["user_id"] == test_user.id

    def test_validate_jwt_token_valid(self, auth_service, test_user):
        """Test JWT token validation with valid token."""
        token = generate_jwt_token(test_user, auth_service.jwt_secret)

        payload = validate_jwt_token(token, auth_service.jwt_secret)

        assert payload is not None
        assert payload["username"] == test_user.username
        assert payload["user_id"] == test_user.id
        assert payload["role"] == test_user.role.value

    def test_validate_jwt_token_invalid(self, auth_service):
        """Test JWT token validation with invalid token."""
        invalid_token = "invalid.jwt.token"

        payload = validate_jwt_token(invalid_token, auth_service.jwt_secret)

        assert payload is None

    @pytest.mark.asyncio
    async def test_user_session_creation(self, auth_service):
        """Test session creation during authentication."""
        credentials = LoginCredentials(username="admin", password="admin123")
        response = await auth_service.authenticate_user(credentials)

        assert response.session_id in auth_service.sessions
        session = auth_service.sessions[response.session_id]
        assert session["user_id"] == response.user.id
        assert "created_at" in session
        assert "expires_at" in session
