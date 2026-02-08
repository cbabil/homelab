"""
Unit tests for services/csrf_service.py

Tests CSRF token generation and validation.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest

import services.csrf_service as csrf_module
from services.csrf_service import CSRFService


@pytest.fixture(autouse=True)
def clear_tokens():
    """Clear CSRF tokens before and after each test."""
    csrf_module._csrf_tokens.clear()
    yield
    csrf_module._csrf_tokens.clear()


@pytest.fixture
def csrf_service():
    """Create CSRFService instance."""
    return CSRFService()


class TestCSRFServiceInit:
    """Tests for CSRFService initialization."""

    def test_init_logs_message(self):
        """CSRFService should log initialization."""
        with patch("services.csrf_service.logger") as mock_logger:
            CSRFService()
            mock_logger.info.assert_called_once_with("CSRF service initialized")


class TestHashToken:
    """Tests for _hash_token method."""

    def test_hash_token_returns_hex(self, csrf_service):
        """_hash_token should return hex string."""
        result = csrf_service._hash_token("test_token")
        assert isinstance(result, str)
        assert len(result) == 64  # SHA256 hex length

    def test_hash_token_deterministic(self, csrf_service):
        """_hash_token should return same hash for same input."""
        hash1 = csrf_service._hash_token("test_token")
        hash2 = csrf_service._hash_token("test_token")
        assert hash1 == hash2

    def test_hash_token_different_for_different_input(self, csrf_service):
        """_hash_token should return different hash for different input."""
        hash1 = csrf_service._hash_token("token1")
        hash2 = csrf_service._hash_token("token2")
        assert hash1 != hash2


class TestGenerateToken:
    """Tests for generate_token method."""

    def test_generate_token_returns_string(self, csrf_service):
        """generate_token should return string token."""
        token = csrf_service.generate_token("user1", "session1")
        assert isinstance(token, str)

    def test_generate_token_correct_length(self, csrf_service):
        """generate_token should return token of configured length."""
        token = csrf_service.generate_token("user1", "session1")
        assert len(token) == csrf_module.TOKEN_LENGTH

    def test_generate_token_stores_metadata(self, csrf_service):
        """generate_token should store token metadata."""
        token = csrf_service.generate_token("user1", "session1")
        token_hash = csrf_service._hash_token(token)

        assert token_hash in csrf_module._csrf_tokens
        data = csrf_module._csrf_tokens[token_hash]
        assert data["user_id"] == "user1"
        assert data["session_id"] == "session1"
        assert data["used"] is False

    def test_generate_token_unique(self, csrf_service):
        """generate_token should return unique tokens."""
        token1 = csrf_service.generate_token("user1", "session1")
        token2 = csrf_service.generate_token("user1", "session1")
        assert token1 != token2

    def test_generate_token_logs(self, csrf_service):
        """generate_token should log token generation."""
        with patch("services.csrf_service.logger") as mock_logger:
            csrf_service.generate_token("user1", "session1")
            mock_logger.info.assert_called()


class TestValidateToken:
    """Tests for validate_token method."""

    def test_validate_token_success(self, csrf_service):
        """validate_token should return True for valid token."""
        token = csrf_service.generate_token("user1", "session1")
        is_valid, error = csrf_service.validate_token(token, "user1", "session1")

        assert is_valid is True
        assert error is None

    def test_validate_token_consumes_by_default(self, csrf_service):
        """validate_token should mark token as used by default."""
        token = csrf_service.generate_token("user1", "session1")
        csrf_service.validate_token(token, "user1", "session1")

        token_hash = csrf_service._hash_token(token)
        assert csrf_module._csrf_tokens[token_hash]["used"] is True

    def test_validate_token_no_consume(self, csrf_service):
        """validate_token with consume=False should not mark as used."""
        token = csrf_service.generate_token("user1", "session1")
        csrf_service.validate_token(token, "user1", "session1", consume=False)

        token_hash = csrf_service._hash_token(token)
        assert csrf_module._csrf_tokens[token_hash]["used"] is False

    def test_validate_token_invalid_format(self, csrf_service):
        """validate_token should reject short tokens."""
        is_valid, error = csrf_service.validate_token("short", "user1", "session1")

        assert is_valid is False
        assert "Invalid token format" in error

    def test_validate_token_empty(self, csrf_service):
        """validate_token should reject empty token."""
        is_valid, error = csrf_service.validate_token("", "user1", "session1")

        assert is_valid is False
        assert "Invalid token format" in error

    def test_validate_token_not_found(self, csrf_service):
        """validate_token should reject unknown token."""
        fake_token = "a" * 64
        is_valid, error = csrf_service.validate_token(fake_token, "user1", "session1")

        assert is_valid is False
        assert "not found" in error.lower()

    def test_validate_token_expired(self, csrf_service):
        """validate_token should reject expired token."""
        token = csrf_service.generate_token("user1", "session1")
        token_hash = csrf_service._hash_token(token)

        # Manually expire the token
        past = datetime.now(UTC) - timedelta(hours=2)
        csrf_module._csrf_tokens[token_hash]["expires_at"] = past.isoformat()

        # Mock cleanup so expired token is still present for the expiration check
        with patch.object(csrf_service, "_cleanup_expired_tokens"):
            is_valid, error = csrf_service.validate_token(token, "user1", "session1")

        assert is_valid is False
        assert "expired" in error.lower()
        # Verify the token was deleted
        assert token_hash not in csrf_module._csrf_tokens

    def test_validate_token_already_used(self, csrf_service):
        """validate_token should reject already used token."""
        token = csrf_service.generate_token("user1", "session1")
        token_hash = csrf_service._hash_token(token)

        # Mark as used
        csrf_module._csrf_tokens[token_hash]["used"] = True

        is_valid, error = csrf_service.validate_token(token, "user1", "session1")

        assert is_valid is False
        assert "already used" in error.lower()

    def test_validate_token_wrong_user(self, csrf_service):
        """validate_token should reject token from different user."""
        token = csrf_service.generate_token("user1", "session1")

        is_valid, error = csrf_service.validate_token(token, "user2", "session1")

        assert is_valid is False
        assert "does not belong to this user" in error

    def test_validate_token_wrong_session(self, csrf_service):
        """validate_token should reject token from different session."""
        token = csrf_service.generate_token("user1", "session1")

        is_valid, error = csrf_service.validate_token(token, "user1", "session2")

        assert is_valid is False
        assert "does not belong to this session" in error


class TestCleanupExpiredTokens:
    """Tests for _cleanup_expired_tokens method."""

    def test_cleanup_removes_expired(self, csrf_service):
        """_cleanup_expired_tokens should remove expired tokens."""
        token = csrf_service.generate_token("user1", "session1")
        token_hash = csrf_service._hash_token(token)

        # Expire the token
        past = datetime.now(UTC) - timedelta(hours=2)
        csrf_module._csrf_tokens[token_hash]["expires_at"] = past.isoformat()

        csrf_service._cleanup_expired_tokens()

        assert token_hash not in csrf_module._csrf_tokens

    def test_cleanup_keeps_valid(self, csrf_service):
        """_cleanup_expired_tokens should keep non-expired tokens."""
        token = csrf_service.generate_token("user1", "session1")
        token_hash = csrf_service._hash_token(token)

        csrf_service._cleanup_expired_tokens()

        assert token_hash in csrf_module._csrf_tokens


class TestCleanupUserTokens:
    """Tests for _cleanup_user_tokens method."""

    def test_cleanup_limits_tokens_per_user(self, csrf_service):
        """_cleanup_user_tokens should enforce MAX_TOKENS_PER_USER."""
        # Generate more tokens than the limit
        for i in range(csrf_module.MAX_TOKENS_PER_USER + 3):
            csrf_service.generate_token("user1", f"session{i}")

        csrf_service._cleanup_user_tokens("user1")

        user_tokens = [
            data
            for data in csrf_module._csrf_tokens.values()
            if data["user_id"] == "user1"
        ]
        assert len(user_tokens) <= csrf_module.MAX_TOKENS_PER_USER

    def test_cleanup_only_affects_specified_user(self, csrf_service):
        """_cleanup_user_tokens should not affect other users."""
        # Generate tokens for user1
        for i in range(csrf_module.MAX_TOKENS_PER_USER + 2):
            csrf_service.generate_token("user1", f"session{i}")

        # Generate token for user2
        csrf_service.generate_token("user2", "session1")

        csrf_service._cleanup_user_tokens("user1")

        user2_tokens = [
            data
            for data in csrf_module._csrf_tokens.values()
            if data["user_id"] == "user2"
        ]
        assert len(user2_tokens) == 1


class TestRevokeUserTokens:
    """Tests for revoke_user_tokens method."""

    def test_revoke_user_tokens_removes_all(self, csrf_service):
        """revoke_user_tokens should remove all user tokens."""
        csrf_service.generate_token("user1", "session1")
        csrf_service.generate_token("user1", "session2")
        csrf_service.generate_token("user1", "session3")

        count = csrf_service.revoke_user_tokens("user1")

        assert count == 3
        user_tokens = [
            data
            for data in csrf_module._csrf_tokens.values()
            if data["user_id"] == "user1"
        ]
        assert len(user_tokens) == 0

    def test_revoke_user_tokens_does_not_affect_others(self, csrf_service):
        """revoke_user_tokens should not affect other users."""
        csrf_service.generate_token("user1", "session1")
        csrf_service.generate_token("user2", "session1")

        csrf_service.revoke_user_tokens("user1")

        user2_tokens = [
            data
            for data in csrf_module._csrf_tokens.values()
            if data["user_id"] == "user2"
        ]
        assert len(user2_tokens) == 1

    def test_revoke_user_tokens_returns_zero_if_none(self, csrf_service):
        """revoke_user_tokens should return 0 if no tokens."""
        count = csrf_service.revoke_user_tokens("nonexistent")
        assert count == 0


class TestGlobalInstance:
    """Tests for global csrf_service instance."""

    def test_csrf_service_exists(self):
        """Module should export csrf_service instance."""
        from services.csrf_service import csrf_service

        assert isinstance(csrf_service, CSRFService)
