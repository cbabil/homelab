"""
Unit tests for services/csrf_service.py

Tests CSRF token generation and validation with database persistence.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import services.csrf_service as csrf_module
from services.csrf_service import CSRFService


@pytest.fixture
def mock_db_service():
    """Create mock database service."""
    db = MagicMock()
    mock_conn = AsyncMock()
    mock_cursor = AsyncMock()
    mock_cursor.rowcount = 0
    mock_cursor.fetchone = AsyncMock(return_value=None)
    mock_conn.execute = AsyncMock(return_value=mock_cursor)
    mock_conn.commit = AsyncMock()

    # Make get_connection an async context manager
    ctx_manager = AsyncMock()
    ctx_manager.__aenter__ = AsyncMock(return_value=mock_conn)
    ctx_manager.__aexit__ = AsyncMock(return_value=False)
    db.get_connection = MagicMock(return_value=ctx_manager)

    return db


@pytest.fixture
def csrf_service(mock_db_service):
    """Create CSRFService instance with mock DB."""
    return CSRFService(db_service=mock_db_service)


@pytest.fixture
def csrf_service_no_db():
    """Create CSRFService instance without DB."""
    return CSRFService()


class TestCSRFServiceInit:
    """Tests for CSRFService initialization."""

    def test_init_with_db(self, mock_db_service):
        """CSRFService should log initialization with persistence flag."""
        with patch("services.csrf_service.logger") as mock_logger:
            CSRFService(db_service=mock_db_service)
            mock_logger.info.assert_called_once_with(
                "CSRF service initialized", persistent=True
            )

    def test_init_without_db(self):
        """CSRFService should log initialization without persistence."""
        with patch("services.csrf_service.logger") as mock_logger:
            CSRFService()
            mock_logger.info.assert_called_once_with(
                "CSRF service initialized", persistent=False
            )


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

    @pytest.mark.asyncio
    async def test_generate_token_returns_string(self, csrf_service):
        """generate_token should return string token."""
        token = await csrf_service.generate_token("user1", "session1")
        assert isinstance(token, str)

    @pytest.mark.asyncio
    async def test_generate_token_correct_length(self, csrf_service):
        """generate_token should return token of configured length."""
        token = await csrf_service.generate_token("user1", "session1")
        assert len(token) == csrf_module.TOKEN_LENGTH

    @pytest.mark.asyncio
    async def test_generate_token_unique(self, csrf_service):
        """generate_token should return unique tokens."""
        token1 = await csrf_service.generate_token("user1", "session1")
        token2 = await csrf_service.generate_token("user1", "session1")
        assert token1 != token2

    @pytest.mark.asyncio
    async def test_generate_token_inserts_to_db(self, csrf_service, mock_db_service):
        """generate_token should insert token into database."""
        await csrf_service.generate_token("user1", "session1")

        # Verify INSERT was called
        ctx_manager = mock_db_service.get_connection()
        conn = await ctx_manager.__aenter__()
        calls = conn.execute.call_args_list
        insert_calls = [c for c in calls if "INSERT INTO csrf_tokens" in str(c)]
        assert len(insert_calls) > 0

    @pytest.mark.asyncio
    async def test_generate_token_logs(self, csrf_service):
        """generate_token should log token generation."""
        with patch("services.csrf_service.logger") as mock_logger:
            await csrf_service.generate_token("user1", "session1")
            mock_logger.info.assert_called()


class TestValidateToken:
    """Tests for validate_token method."""

    @pytest.mark.asyncio
    async def test_validate_token_invalid_format_short(self, csrf_service):
        """validate_token should reject short tokens."""
        is_valid, error = await csrf_service.validate_token(
            "short", "user1", "session1"
        )
        assert is_valid is False
        assert "Invalid token format" in error

    @pytest.mark.asyncio
    async def test_validate_token_invalid_format_empty(self, csrf_service):
        """validate_token should reject empty token."""
        is_valid, error = await csrf_service.validate_token(
            "", "user1", "session1"
        )
        assert is_valid is False
        assert "Invalid token format" in error

    @pytest.mark.asyncio
    async def test_validate_token_not_found(self, csrf_service):
        """validate_token should reject unknown token."""
        fake_token = "a" * 64
        is_valid, error = await csrf_service.validate_token(
            fake_token, "user1", "session1"
        )
        assert is_valid is False
        assert "not found" in error.lower()

    @pytest.mark.asyncio
    async def test_validate_token_no_db(self, csrf_service_no_db):
        """validate_token should fail when no DB is configured."""
        token = "a" * 64
        is_valid, error = await csrf_service_no_db.validate_token(
            token, "user1", "session1"
        )
        assert is_valid is False
        assert "unavailable" in error.lower()

    @pytest.mark.asyncio
    async def test_validate_token_success(self, csrf_service, mock_db_service):
        """validate_token should return True for valid token."""
        now = datetime.now(UTC)
        future = (now + timedelta(hours=1)).isoformat()

        # Mock the SELECT to return valid token data
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(
            return_value=("user1", "session1", future, 0)
        )
        mock_cursor.rowcount = 0
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_conn.commit = AsyncMock()

        ctx_manager = AsyncMock()
        ctx_manager.__aenter__ = AsyncMock(return_value=mock_conn)
        ctx_manager.__aexit__ = AsyncMock(return_value=False)
        mock_db_service.get_connection = MagicMock(return_value=ctx_manager)

        token = "a" * 64
        is_valid, error = await csrf_service.validate_token(
            token, "user1", "session1"
        )
        assert is_valid is True
        assert error is None

    @pytest.mark.asyncio
    async def test_validate_token_expired(self, csrf_service, mock_db_service):
        """validate_token should reject expired token."""
        past = (datetime.now(UTC) - timedelta(hours=2)).isoformat()

        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(
            return_value=("user1", "session1", past, 0)
        )
        mock_cursor.rowcount = 0
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_conn.commit = AsyncMock()

        ctx_manager = AsyncMock()
        ctx_manager.__aenter__ = AsyncMock(return_value=mock_conn)
        ctx_manager.__aexit__ = AsyncMock(return_value=False)
        mock_db_service.get_connection = MagicMock(return_value=ctx_manager)

        token = "a" * 64
        is_valid, error = await csrf_service.validate_token(
            token, "user1", "session1"
        )
        assert is_valid is False
        assert "expired" in error.lower()

    @pytest.mark.asyncio
    async def test_validate_token_already_used(self, csrf_service, mock_db_service):
        """validate_token should reject already used token."""
        future = (datetime.now(UTC) + timedelta(hours=1)).isoformat()

        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(
            return_value=("user1", "session1", future, 1)  # used=1
        )
        mock_cursor.rowcount = 0
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_conn.commit = AsyncMock()

        ctx_manager = AsyncMock()
        ctx_manager.__aenter__ = AsyncMock(return_value=mock_conn)
        ctx_manager.__aexit__ = AsyncMock(return_value=False)
        mock_db_service.get_connection = MagicMock(return_value=ctx_manager)

        token = "a" * 64
        is_valid, error = await csrf_service.validate_token(
            token, "user1", "session1"
        )
        assert is_valid is False
        assert "already used" in error.lower()

    @pytest.mark.asyncio
    async def test_validate_token_wrong_user(self, csrf_service, mock_db_service):
        """validate_token should reject token from different user."""
        future = (datetime.now(UTC) + timedelta(hours=1)).isoformat()

        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(
            return_value=("user1", "session1", future, 0)
        )
        mock_cursor.rowcount = 0
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_conn.commit = AsyncMock()

        ctx_manager = AsyncMock()
        ctx_manager.__aenter__ = AsyncMock(return_value=mock_conn)
        ctx_manager.__aexit__ = AsyncMock(return_value=False)
        mock_db_service.get_connection = MagicMock(return_value=ctx_manager)

        token = "a" * 64
        is_valid, error = await csrf_service.validate_token(
            token, "user2", "session1"
        )
        assert is_valid is False
        assert "does not belong to this user" in error

    @pytest.mark.asyncio
    async def test_validate_token_wrong_session(self, csrf_service, mock_db_service):
        """validate_token should reject token from different session."""
        future = (datetime.now(UTC) + timedelta(hours=1)).isoformat()

        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(
            return_value=("user1", "session1", future, 0)
        )
        mock_cursor.rowcount = 0
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_conn.commit = AsyncMock()

        ctx_manager = AsyncMock()
        ctx_manager.__aenter__ = AsyncMock(return_value=mock_conn)
        ctx_manager.__aexit__ = AsyncMock(return_value=False)
        mock_db_service.get_connection = MagicMock(return_value=ctx_manager)

        token = "a" * 64
        is_valid, error = await csrf_service.validate_token(
            token, "user1", "session2"
        )
        assert is_valid is False
        assert "does not belong to this session" in error


class TestRevokeUserTokens:
    """Tests for revoke_user_tokens method."""

    @pytest.mark.asyncio
    async def test_revoke_user_tokens(self, csrf_service, mock_db_service):
        """revoke_user_tokens should delete all user tokens."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 3
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_conn.commit = AsyncMock()

        ctx_manager = AsyncMock()
        ctx_manager.__aenter__ = AsyncMock(return_value=mock_conn)
        ctx_manager.__aexit__ = AsyncMock(return_value=False)
        mock_db_service.get_connection = MagicMock(return_value=ctx_manager)

        count = await csrf_service.revoke_user_tokens("user1")
        assert count == 3

    @pytest.mark.asyncio
    async def test_revoke_user_tokens_returns_zero_if_none(
        self, csrf_service, mock_db_service
    ):
        """revoke_user_tokens should return 0 if no tokens."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 0
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_conn.commit = AsyncMock()

        ctx_manager = AsyncMock()
        ctx_manager.__aenter__ = AsyncMock(return_value=mock_conn)
        ctx_manager.__aexit__ = AsyncMock(return_value=False)
        mock_db_service.get_connection = MagicMock(return_value=ctx_manager)

        count = await csrf_service.revoke_user_tokens("nonexistent")
        assert count == 0

    @pytest.mark.asyncio
    async def test_revoke_user_tokens_no_db(self, csrf_service_no_db):
        """revoke_user_tokens should return 0 if no DB."""
        count = await csrf_service_no_db.revoke_user_tokens("user1")
        assert count == 0
