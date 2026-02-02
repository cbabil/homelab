"""
Tests for auth_helpers module.

Tests password hashing, verification, and JWT operations.
"""

import pytest
from datetime import datetime, UTC
import time
from lib.auth_helpers import (
    hash_password,
    verify_password,
    generate_jwt_token,
    validate_jwt_token,
    create_session_data,
    generate_session_id,
    create_default_admin,
    BCRYPT_ROUNDS,
)
from models.auth import User, UserRole


class TestPasswordHashing:
    """Tests for password hashing functions."""

    def test_hash_password_returns_string(self):
        """hash_password should return a string."""
        result = hash_password("testpassword123")
        assert isinstance(result, str)

    def test_hash_password_produces_valid_bcrypt_hash(self):
        """hash_password should produce a valid bcrypt hash."""
        result = hash_password("testpassword123")
        # bcrypt hashes start with $2b$ or $2a$
        assert result.startswith("$2")
        # bcrypt hashes are 60 characters
        assert len(result) == 60

    def test_hash_password_uses_correct_rounds(self):
        """hash_password should use 12 rounds (must match CLI)."""
        assert BCRYPT_ROUNDS == 12
        result = hash_password("testpassword123")
        # The cost factor is embedded in the hash: $2b$12$...
        assert "$12$" in result

    def test_hash_password_different_passwords_different_hashes(self):
        """Different passwords should produce different hashes."""
        hash1 = hash_password("password1")
        hash2 = hash_password("password2")
        assert hash1 != hash2

    def test_hash_password_same_password_different_hashes(self):
        """Same password should produce different hashes (unique salt)."""
        hash1 = hash_password("samepassword")
        hash2 = hash_password("samepassword")
        assert hash1 != hash2

    def test_hash_password_empty_string(self):
        """hash_password should handle empty string."""
        result = hash_password("")
        assert isinstance(result, str)
        assert result.startswith("$2")

    def test_hash_password_unicode(self):
        """hash_password should handle unicode characters."""
        result = hash_password("пароль123")
        assert isinstance(result, str)
        assert result.startswith("$2")

    def test_hash_password_special_characters(self):
        """hash_password should handle special characters."""
        result = hash_password("p@$$w0rd!#%^&*()")
        assert isinstance(result, str)
        assert result.startswith("$2")


class TestPasswordVerification:
    """Tests for password verification functions."""

    def test_verify_password_correct_password(self):
        """verify_password should return True for correct password."""
        password = "correctpassword"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect_password(self):
        """verify_password should return False for incorrect password."""
        hashed = hash_password("correctpassword")
        assert verify_password("wrongpassword", hashed) is False

    def test_verify_password_case_sensitive(self):
        """verify_password should be case-sensitive."""
        hashed = hash_password("Password123")
        assert verify_password("Password123", hashed) is True
        assert verify_password("password123", hashed) is False
        assert verify_password("PASSWORD123", hashed) is False

    def test_verify_password_with_string_hash(self):
        """verify_password should handle string hash."""
        password = "testpassword"
        hashed = hash_password(password)
        assert isinstance(hashed, str)
        assert verify_password(password, hashed) is True

    def test_verify_password_unicode(self):
        """verify_password should handle unicode passwords."""
        password = "пароль123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True
        assert verify_password("пароль124", hashed) is False

    def test_verify_password_empty_string(self):
        """verify_password should handle empty string password."""
        hashed = hash_password("")
        assert verify_password("", hashed) is True
        assert verify_password("notempty", hashed) is False

    def test_verify_password_with_bytes_hash(self):
        """verify_password should handle bytes hash (legacy format)."""
        password = "testpassword"
        hashed_str = hash_password(password)
        hashed_bytes = hashed_str.encode("utf-8")
        assert verify_password(password, hashed_bytes) is True


class TestJWTOperations:
    """Tests for JWT token operations."""

    @pytest.fixture
    def test_user(self):
        """Create a test user."""
        return User(
            id="test-user-id-123",
            username="testuser",
            email="test@example.com",
            role=UserRole.ADMIN,
            last_login=datetime.now(UTC).isoformat(),
            is_active=True,
            preferences={}
        )

    @pytest.fixture
    def jwt_secret(self):
        """JWT secret for testing."""
        return "test-secret-key-for-jwt"

    def test_generate_jwt_token_returns_string(self, test_user, jwt_secret):
        """generate_jwt_token should return a string."""
        token = generate_jwt_token(test_user, jwt_secret)
        assert isinstance(token, str)

    def test_generate_jwt_token_format(self, test_user, jwt_secret):
        """generate_jwt_token should return a valid JWT format (3 parts)."""
        token = generate_jwt_token(test_user, jwt_secret)
        parts = token.split(".")
        assert len(parts) == 3

    def test_validate_jwt_token_valid(self, test_user, jwt_secret):
        """validate_jwt_token should decode valid token."""
        token = generate_jwt_token(test_user, jwt_secret)
        payload = validate_jwt_token(token, jwt_secret)

        assert payload is not None
        assert payload["user_id"] == test_user.id
        assert payload["username"] == test_user.username
        assert payload["role"] == test_user.role.value

    def test_validate_jwt_token_wrong_secret(self, test_user, jwt_secret):
        """validate_jwt_token should return None for wrong secret."""
        token = generate_jwt_token(test_user, jwt_secret)
        payload = validate_jwt_token(token, "wrong-secret")
        assert payload is None

    def test_validate_jwt_token_invalid_token(self, jwt_secret):
        """validate_jwt_token should return None for invalid token."""
        payload = validate_jwt_token("invalid.token.here", jwt_secret)
        assert payload is None

    def test_validate_jwt_token_malformed(self, jwt_secret):
        """validate_jwt_token should return None for malformed token."""
        payload = validate_jwt_token("not-a-jwt", jwt_secret)
        assert payload is None

    def test_generate_jwt_token_contains_issuer(self, test_user, jwt_secret):
        """generate_jwt_token should include issuer claim."""
        token = generate_jwt_token(test_user, jwt_secret)
        payload = validate_jwt_token(token, jwt_secret)
        assert payload["iss"] == "tomo"

    def test_validate_jwt_token_expired(self, test_user, jwt_secret):
        """validate_jwt_token should return None for expired token."""
        # Generate token that expires immediately
        token = generate_jwt_token(test_user, jwt_secret, expiry_hours=0)
        # Wait a tiny bit to ensure expiry
        time.sleep(0.1)
        payload = validate_jwt_token(token, jwt_secret)
        assert payload is None


class TestSessionOperations:
    """Tests for session-related functions."""

    def test_generate_session_id_returns_string(self):
        """generate_session_id should return a string."""
        session_id = generate_session_id()
        assert isinstance(session_id, str)

    def test_generate_session_id_is_uuid_format(self):
        """generate_session_id should return UUID format."""
        session_id = generate_session_id()
        # UUID format: 8-4-4-4-12 characters
        parts = session_id.split("-")
        assert len(parts) == 5
        assert len(parts[0]) == 8
        assert len(parts[1]) == 4
        assert len(parts[2]) == 4
        assert len(parts[3]) == 4
        assert len(parts[4]) == 12

    def test_generate_session_id_unique(self):
        """generate_session_id should generate unique IDs."""
        ids = [generate_session_id() for _ in range(100)]
        assert len(set(ids)) == 100

    def test_create_session_data_structure(self):
        """create_session_data should return correct structure."""
        data = create_session_data("user-123")

        assert "user_id" in data
        assert "created_at" in data
        assert "last_activity" in data
        assert "expires_at" in data
        assert data["user_id"] == "user-123"

    def test_create_session_data_timestamps_are_iso_format(self):
        """create_session_data timestamps should be ISO format."""
        data = create_session_data("user-123")

        # Should be parseable as ISO datetime
        datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
        datetime.fromisoformat(data["last_activity"].replace("Z", "+00:00"))
        datetime.fromisoformat(data["expires_at"].replace("Z", "+00:00"))

    def test_create_session_data_custom_expiry(self):
        """create_session_data should respect custom expiry hours."""
        data_default = create_session_data("user-123")
        data_custom = create_session_data("user-123", expiry_hours=48)

        # Custom expiry should be later than default
        expires_default = datetime.fromisoformat(data_default["expires_at"].replace("Z", "+00:00"))
        expires_custom = datetime.fromisoformat(data_custom["expires_at"].replace("Z", "+00:00"))

        assert expires_custom > expires_default


class TestDefaultAdmin:
    """Tests for create_default_admin function."""

    def test_create_default_admin_returns_user(self):
        """create_default_admin should return a User object."""
        admin = create_default_admin()
        assert isinstance(admin, User)

    def test_create_default_admin_has_correct_username(self):
        """create_default_admin should have username 'admin'."""
        admin = create_default_admin()
        assert admin.username == "admin"

    def test_create_default_admin_has_admin_role(self):
        """create_default_admin should have ADMIN role."""
        admin = create_default_admin()
        assert admin.role == UserRole.ADMIN

    def test_create_default_admin_is_active(self):
        """create_default_admin should be active."""
        admin = create_default_admin()
        assert admin.is_active is True

    def test_create_default_admin_has_email(self):
        """create_default_admin should have email."""
        admin = create_default_admin()
        assert admin.email == "admin@tomo.dev"

    def test_create_default_admin_has_preferences(self):
        """create_default_admin should have default preferences."""
        admin = create_default_admin()
        assert admin.preferences is not None
        assert admin.preferences["theme"] == "dark"
        assert admin.preferences["language"] == "en"
        assert admin.preferences["notifications"] is True

    def test_create_default_admin_has_unique_id(self):
        """create_default_admin should generate unique IDs."""
        admin1 = create_default_admin()
        admin2 = create_default_admin()
        assert admin1.id != admin2.id
