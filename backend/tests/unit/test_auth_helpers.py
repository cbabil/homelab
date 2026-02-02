"""
Unit tests for lib/auth_helpers.py

Tests for authentication helper utilities including password hashing,
JWT operations, and user management.
"""

import pytest
import time
from datetime import datetime, UTC
import jwt as pyjwt

from lib.auth_helpers import (
    hash_password,
    verify_password,
    generate_jwt_token,
    validate_jwt_token,
    create_session_data,
    generate_session_id,
    create_default_admin,
)
from models.auth import User, UserRole


class TestHashPassword:
    """Tests for password hashing."""

    def test_hash_password_returns_string(self):
        """Should return a string hash."""
        hashed = hash_password("test_password")

        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_password_different_for_same_input(self):
        """Should produce different hashes due to salt."""
        hash1 = hash_password("password123")
        hash2 = hash_password("password123")

        assert hash1 != hash2

    def test_hash_password_bcrypt_format(self):
        """Should produce bcrypt format hash."""
        hashed = hash_password("test")

        # bcrypt hashes start with $2b$ or $2a$
        assert hashed.startswith("$2")


class TestVerifyPassword:
    """Tests for password verification."""

    def test_verify_password_correct(self):
        """Should return True for correct password."""
        hashed = hash_password("correct_password")
        result = verify_password("correct_password", hashed)

        assert result is True

    def test_verify_password_incorrect(self):
        """Should return False for incorrect password."""
        hashed = hash_password("correct_password")
        result = verify_password("wrong_password", hashed)

        assert result is False

    def test_verify_password_with_string_hash(self):
        """Should handle string hash format."""
        hashed = hash_password("test")
        result = verify_password("test", hashed)

        assert result is True

    def test_verify_password_with_bytes_hash(self):
        """Should handle bytes hash format."""
        hashed = hash_password("test")
        hashed_bytes = hashed.encode("utf-8")
        result = verify_password("test", hashed_bytes)

        assert result is True


class TestGenerateJwtToken:
    """Tests for JWT token generation."""

    @pytest.fixture
    def mock_user(self):
        """Create mock user for testing."""
        return User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            role=UserRole.USER,
            is_active=True,
            last_login=datetime.now(UTC).isoformat(),
        )

    def test_generate_jwt_token_creates_valid_token(self, mock_user):
        """Should create a valid JWT token."""
        secret = "test_secret_key"
        token = generate_jwt_token(mock_user, secret)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_generate_jwt_token_contains_user_data(self, mock_user):
        """Should include user data in token."""
        secret = "test_secret_key"
        token = generate_jwt_token(mock_user, secret)

        decoded = pyjwt.decode(token, secret, algorithms=["HS256"])
        assert decoded["user_id"] == "user-123"
        assert decoded["username"] == "testuser"
        assert decoded["role"] == "user"

    def test_generate_jwt_token_has_expiry(self, mock_user):
        """Should include expiry in token."""
        secret = "test_secret_key"
        token = generate_jwt_token(mock_user, secret, expiry_hours=24)

        decoded = pyjwt.decode(token, secret, algorithms=["HS256"])
        assert "exp" in decoded

    def test_generate_jwt_token_has_issuer(self, mock_user):
        """Should include issuer in token."""
        secret = "test_secret_key"
        token = generate_jwt_token(mock_user, secret)

        decoded = pyjwt.decode(token, secret, algorithms=["HS256"])
        assert decoded["iss"] == "tomo"

    def test_generate_jwt_token_admin_role(self):
        """Should handle admin role."""
        admin_user = User(
            id="admin-123",
            username="admin",
            email="admin@example.com",
            role=UserRole.ADMIN,
            is_active=True,
            last_login=datetime.now(UTC).isoformat(),
        )
        secret = "test_secret"
        token = generate_jwt_token(admin_user, secret)

        decoded = pyjwt.decode(token, secret, algorithms=["HS256"])
        assert decoded["role"] == "admin"


class TestValidateJwtToken:
    """Tests for JWT token validation."""

    @pytest.fixture
    def mock_user(self):
        """Create mock user for testing."""
        return User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            role=UserRole.USER,
            is_active=True,
            last_login=datetime.now(UTC).isoformat(),
        )

    def test_validate_jwt_token_valid(self, mock_user):
        """Should return payload for valid token."""
        secret = "test_secret"
        token = generate_jwt_token(mock_user, secret)

        payload = validate_jwt_token(token, secret)

        assert payload is not None
        assert payload["user_id"] == "user-123"

    def test_validate_jwt_token_invalid(self):
        """Should return None for invalid token."""
        secret = "test_secret"

        payload = validate_jwt_token("invalid_token", secret)

        assert payload is None

    def test_validate_jwt_token_wrong_secret(self, mock_user):
        """Should return None for token with wrong secret."""
        token = generate_jwt_token(mock_user, "correct_secret")

        payload = validate_jwt_token(token, "wrong_secret")

        assert payload is None

    def test_validate_jwt_token_expired(self, mock_user):
        """Should return None for expired token."""
        secret = "test_secret"

        # Create token with 0 hours expiry (already expired)
        token = generate_jwt_token(mock_user, secret, expiry_hours=0)

        # Wait a moment to ensure expiry
        time.sleep(0.1)

        payload = validate_jwt_token(token, secret)

        assert payload is None


class TestCreateSessionData:
    """Tests for session data creation."""

    def test_create_session_data_has_user_id(self):
        """Should include user_id."""
        data = create_session_data("user-123")

        assert data["user_id"] == "user-123"

    def test_create_session_data_has_timestamps(self):
        """Should include all timestamps."""
        data = create_session_data("user-123")

        assert "created_at" in data
        assert "last_activity" in data
        assert "expires_at" in data

    def test_create_session_data_custom_expiry(self):
        """Should respect custom expiry hours."""
        data_24h = create_session_data("user-123", expiry_hours=24)
        data_1h = create_session_data("user-123", expiry_hours=1)

        expires_24h = datetime.fromisoformat(data_24h["expires_at"])
        expires_1h = datetime.fromisoformat(data_1h["expires_at"])

        # 24h expiry should be later than 1h expiry
        assert expires_24h > expires_1h


class TestGenerateSessionId:
    """Tests for session ID generation."""

    def test_generate_session_id_format(self):
        """Should generate UUID format string."""
        session_id = generate_session_id()

        assert isinstance(session_id, str)
        # UUID format: 8-4-4-4-12 characters
        assert len(session_id) == 36
        assert session_id.count("-") == 4

    def test_generate_session_id_unique(self):
        """Should generate unique IDs."""
        ids = [generate_session_id() for _ in range(100)]

        # All IDs should be unique
        assert len(set(ids)) == 100


class TestCreateDefaultAdmin:
    """Tests for default admin creation."""

    def test_create_default_admin_returns_user(self):
        """Should return User instance."""
        admin = create_default_admin()

        assert isinstance(admin, User)

    def test_create_default_admin_has_admin_role(self):
        """Should have admin role."""
        admin = create_default_admin()

        assert admin.role == UserRole.ADMIN

    def test_create_default_admin_username(self):
        """Should have 'admin' username."""
        admin = create_default_admin()

        assert admin.username == "admin"

    def test_create_default_admin_is_active(self):
        """Should be active."""
        admin = create_default_admin()

        assert admin.is_active is True

    def test_create_default_admin_has_preferences(self):
        """Should have default preferences."""
        admin = create_default_admin()

        assert admin.preferences is not None
        assert admin.preferences["theme"] == "dark"
        assert admin.preferences["language"] == "en"
        assert admin.preferences["notifications"] is True

    def test_create_default_admin_unique_ids(self):
        """Should generate unique IDs each time."""
        admin1 = create_default_admin()
        admin2 = create_default_admin()

        assert admin1.id != admin2.id
