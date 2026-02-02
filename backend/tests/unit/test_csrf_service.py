"""
Unit tests for services/csrf_service.py

Tests for CSRF token generation and validation.
"""

from datetime import datetime, timedelta, UTC
from unittest.mock import patch

import pytest

import services.csrf_service as csrf_module
from services.csrf_service import CSRFService


@pytest.fixture
def csrf_service():
    """Create CSRF service with fresh token storage."""
    csrf_module._csrf_tokens.clear()
    return CSRFService()


@pytest.fixture
def cleanup_tokens():
    """Clear tokens after each test."""
    yield
    csrf_module._csrf_tokens.clear()


class TestCSRFServiceInit:
    """Tests for CSRFService initialization."""

    def test_init_logs_initialization(self, cleanup_tokens):
        """Should log initialization."""
        with patch.object(csrf_module, "logger") as mock_logger:
            CSRFService()

            mock_logger.info.assert_called_once_with("CSRF service initialized")


class TestCSRFServiceHashToken:
    """Tests for _hash_token method."""

    def test_hash_token_returns_hex_string(self, csrf_service, cleanup_tokens):
        """Should return hex string."""
        token = "test_token"
        result = csrf_service._hash_token(token)

        assert isinstance(result, str)
        assert len(result) == 64  # SHA256 hex is 64 chars

    def test_hash_token_is_deterministic(self, csrf_service, cleanup_tokens):
        """Should return same hash for same input."""
        token = "test_token"

        result1 = csrf_service._hash_token(token)
        result2 = csrf_service._hash_token(token)

        assert result1 == result2

    def test_hash_token_different_inputs(self, csrf_service, cleanup_tokens):
        """Should return different hashes for different inputs."""
        result1 = csrf_service._hash_token("token1")
        result2 = csrf_service._hash_token("token2")

        assert result1 != result2


class TestCSRFServiceCleanupExpiredTokens:
    """Tests for _cleanup_expired_tokens method."""

    def test_cleanup_removes_expired_tokens(self, csrf_service, cleanup_tokens):
        """Should remove tokens past expiration."""
        expired_time = (datetime.now(UTC) - timedelta(hours=2)).isoformat()
        csrf_module._csrf_tokens["expired_hash"] = {
            "user_id": "user1",
            "session_id": "session1",
            "expires_at": expired_time,
            "used": False,
        }

        csrf_service._cleanup_expired_tokens()

        assert "expired_hash" not in csrf_module._csrf_tokens

    def test_cleanup_keeps_valid_tokens(self, csrf_service, cleanup_tokens):
        """Should keep tokens not yet expired."""
        valid_time = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
        csrf_module._csrf_tokens["valid_hash"] = {
            "user_id": "user1",
            "session_id": "session1",
            "expires_at": valid_time,
            "used": False,
        }

        csrf_service._cleanup_expired_tokens()

        assert "valid_hash" in csrf_module._csrf_tokens

    def test_cleanup_logs_when_tokens_removed(self, csrf_service, cleanup_tokens):
        """Should log when expired tokens are removed."""
        expired_time = (datetime.now(UTC) - timedelta(hours=2)).isoformat()
        csrf_module._csrf_tokens["expired_hash"] = {
            "user_id": "user1",
            "session_id": "session1",
            "expires_at": expired_time,
            "used": False,
        }

        with patch.object(csrf_module, "logger") as mock_logger:
            csrf_service._cleanup_expired_tokens()

            mock_logger.debug.assert_called_once_with(
                "Cleaned up expired CSRF tokens", count=1
            )


class TestCSRFServiceCleanupUserTokens:
    """Tests for _cleanup_user_tokens method."""

    def test_cleanup_removes_oldest_tokens(self, csrf_service, cleanup_tokens):
        """Should remove oldest tokens when over limit."""
        user_id = "user1"

        # Create more than MAX_TOKENS_PER_USER tokens
        for i in range(7):
            expires = (datetime.now(UTC) + timedelta(hours=i)).isoformat()
            csrf_module._csrf_tokens[f"hash_{i}"] = {
                "user_id": user_id,
                "session_id": f"session_{i}",
                "expires_at": expires,
                "used": False,
            }

        csrf_service._cleanup_user_tokens(user_id)

        # Should only keep MAX_TOKENS_PER_USER (5)
        user_tokens = [
            k for k, v in csrf_module._csrf_tokens.items()
            if v["user_id"] == user_id
        ]
        assert len(user_tokens) <= csrf_module.MAX_TOKENS_PER_USER

    def test_cleanup_keeps_tokens_under_limit(self, csrf_service, cleanup_tokens):
        """Should not remove tokens when under limit."""
        user_id = "user1"

        for i in range(3):
            expires = (datetime.now(UTC) + timedelta(hours=i)).isoformat()
            csrf_module._csrf_tokens[f"hash_{i}"] = {
                "user_id": user_id,
                "session_id": f"session_{i}",
                "expires_at": expires,
                "used": False,
            }

        csrf_service._cleanup_user_tokens(user_id)

        user_tokens = [
            k for k, v in csrf_module._csrf_tokens.items()
            if v["user_id"] == user_id
        ]
        assert len(user_tokens) == 3


class TestCSRFServiceGenerateToken:
    """Tests for generate_token method."""

    def test_generate_token_returns_string(self, csrf_service, cleanup_tokens):
        """Should return a token string."""
        token = csrf_service.generate_token("user1", "session1")

        assert isinstance(token, str)
        assert len(token) == csrf_module.TOKEN_LENGTH

    def test_generate_token_stores_metadata(self, csrf_service, cleanup_tokens):
        """Should store token metadata."""
        token = csrf_service.generate_token("user1", "session1")
        token_hash = csrf_service._hash_token(token)

        assert token_hash in csrf_module._csrf_tokens
        data = csrf_module._csrf_tokens[token_hash]
        assert data["user_id"] == "user1"
        assert data["session_id"] == "session1"
        assert data["used"] is False

    def test_generate_token_sets_expiration(self, csrf_service, cleanup_tokens):
        """Should set expiration time."""
        before = datetime.now(UTC)
        token = csrf_service.generate_token("user1", "session1")
        after = datetime.now(UTC)

        token_hash = csrf_service._hash_token(token)
        data = csrf_module._csrf_tokens[token_hash]
        expires_at = datetime.fromisoformat(data["expires_at"])

        expected_min = before + timedelta(minutes=csrf_module.TOKEN_EXPIRY_MINUTES)
        expected_max = after + timedelta(minutes=csrf_module.TOKEN_EXPIRY_MINUTES)

        assert expected_min <= expires_at <= expected_max

    def test_generate_token_unique(self, csrf_service, cleanup_tokens):
        """Should generate unique tokens."""
        token1 = csrf_service.generate_token("user1", "session1")
        token2 = csrf_service.generate_token("user1", "session1")

        assert token1 != token2

    def test_generate_token_calls_cleanup(self, csrf_service, cleanup_tokens):
        """Should call cleanup methods."""
        with (
            patch.object(csrf_service, "_cleanup_expired_tokens") as mock_expired,
            patch.object(csrf_service, "_cleanup_user_tokens") as mock_user,
        ):
            csrf_service.generate_token("user1", "session1")

            mock_expired.assert_called_once()
            mock_user.assert_called_once_with("user1")


class TestCSRFServiceValidateToken:
    """Tests for validate_token method."""

    def test_validate_token_success(self, csrf_service, cleanup_tokens):
        """Should validate correct token."""
        token = csrf_service.generate_token("user1", "session1")

        is_valid, error = csrf_service.validate_token(token, "user1", "session1")

        assert is_valid is True
        assert error is None

    def test_validate_token_marks_as_used(self, csrf_service, cleanup_tokens):
        """Should mark token as used when consume=True."""
        token = csrf_service.generate_token("user1", "session1")

        csrf_service.validate_token(token, "user1", "session1", consume=True)

        token_hash = csrf_service._hash_token(token)
        assert csrf_module._csrf_tokens[token_hash]["used"] is True

    def test_validate_token_not_consumed(self, csrf_service, cleanup_tokens):
        """Should not mark as used when consume=False."""
        token = csrf_service.generate_token("user1", "session1")

        csrf_service.validate_token(token, "user1", "session1", consume=False)

        token_hash = csrf_service._hash_token(token)
        assert csrf_module._csrf_tokens[token_hash]["used"] is False

    def test_validate_token_invalid_format_empty(self, csrf_service, cleanup_tokens):
        """Should reject empty token."""
        is_valid, error = csrf_service.validate_token("", "user1", "session1")

        assert is_valid is False
        assert error == "Invalid token format"

    def test_validate_token_invalid_format_short(self, csrf_service, cleanup_tokens):
        """Should reject short token."""
        is_valid, error = csrf_service.validate_token("short", "user1", "session1")

        assert is_valid is False
        assert error == "Invalid token format"

    def test_validate_token_not_found(self, csrf_service, cleanup_tokens):
        """Should reject unknown token."""
        is_valid, error = csrf_service.validate_token(
            "a" * 64, "user1", "session1"
        )

        assert is_valid is False
        assert error == "Token not found or expired"

    def test_validate_token_expired_removed_by_cleanup(
        self, csrf_service, cleanup_tokens
    ):
        """Should reject expired token (removed by cleanup)."""
        token = csrf_service.generate_token("user1", "session1")
        token_hash = csrf_service._hash_token(token)

        # Manually expire the token - will be cleaned up
        expired = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
        csrf_module._csrf_tokens[token_hash]["expires_at"] = expired

        is_valid, error = csrf_service.validate_token(token, "user1", "session1")

        assert is_valid is False
        # Cleanup removes expired tokens, so error is "not found"
        assert error == "Token not found or expired"

    def test_validate_token_expired_not_cleaned_up(
        self, csrf_service, cleanup_tokens
    ):
        """Should reject token that expired but wasn't cleaned up yet."""
        token = csrf_service.generate_token("user1", "session1")
        token_hash = csrf_service._hash_token(token)

        # Set expiration to 1 second ago - very recently expired
        expired = (datetime.now(UTC) - timedelta(seconds=1)).isoformat()
        csrf_module._csrf_tokens[token_hash]["expires_at"] = expired

        # Mock cleanup to not remove tokens, simulating race condition
        with patch.object(csrf_service, "_cleanup_expired_tokens"):
            is_valid, error = csrf_service.validate_token(
                token, "user1", "session1"
            )

        assert is_valid is False
        assert error == "Token expired"
        # Token should be removed after failed validation
        assert token_hash not in csrf_module._csrf_tokens

    def test_validate_token_already_used(self, csrf_service, cleanup_tokens):
        """Should reject already used token."""
        token = csrf_service.generate_token("user1", "session1")

        # First use
        csrf_service.validate_token(token, "user1", "session1", consume=True)

        # Second use
        is_valid, error = csrf_service.validate_token(token, "user1", "session1")

        assert is_valid is False
        assert error == "Token already used"

    def test_validate_token_wrong_user(self, csrf_service, cleanup_tokens):
        """Should reject token for different user."""
        token = csrf_service.generate_token("user1", "session1")

        is_valid, error = csrf_service.validate_token(token, "user2", "session1")

        assert is_valid is False
        assert error == "Token does not belong to this user"

    def test_validate_token_wrong_session(self, csrf_service, cleanup_tokens):
        """Should reject token for different session."""
        token = csrf_service.generate_token("user1", "session1")

        is_valid, error = csrf_service.validate_token(token, "user1", "session2")

        assert is_valid is False
        assert error == "Token does not belong to this session"


class TestCSRFServiceRevokeUserTokens:
    """Tests for revoke_user_tokens method."""

    def test_revoke_user_tokens_removes_all(self, csrf_service, cleanup_tokens):
        """Should remove all tokens for user."""
        csrf_service.generate_token("user1", "session1")
        csrf_service.generate_token("user1", "session2")
        csrf_service.generate_token("user2", "session3")

        count = csrf_service.revoke_user_tokens("user1")

        assert count == 2
        # Verify user1 tokens removed
        user1_tokens = [
            k for k, v in csrf_module._csrf_tokens.items()
            if v["user_id"] == "user1"
        ]
        assert len(user1_tokens) == 0

    def test_revoke_user_tokens_keeps_other_users(self, csrf_service, cleanup_tokens):
        """Should keep tokens for other users."""
        csrf_service.generate_token("user1", "session1")
        csrf_service.generate_token("user2", "session2")

        csrf_service.revoke_user_tokens("user1")

        user2_tokens = [
            k for k, v in csrf_module._csrf_tokens.items()
            if v["user_id"] == "user2"
        ]
        assert len(user2_tokens) == 1

    def test_revoke_user_tokens_returns_zero_if_none(
        self, csrf_service, cleanup_tokens
    ):
        """Should return 0 if no tokens to revoke."""
        count = csrf_service.revoke_user_tokens("nonexistent_user")

        assert count == 0

    def test_revoke_user_tokens_logs_when_revoked(self, csrf_service, cleanup_tokens):
        """Should log when tokens are revoked."""
        csrf_service.generate_token("user1", "session1")

        with patch.object(csrf_module, "logger") as mock_logger:
            csrf_service.revoke_user_tokens("user1")

            mock_logger.info.assert_called_with(
                "User CSRF tokens revoked", user_id="user1", count=1
            )


class TestCSRFServiceSingleton:
    """Tests for global csrf_service instance."""

    def test_singleton_exists(self, cleanup_tokens):
        """Should have global csrf_service instance."""
        from services.csrf_service import csrf_service

        assert isinstance(csrf_service, CSRFService)
