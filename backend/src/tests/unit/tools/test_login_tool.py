"""
Unit tests for tools/auth/login_tool.py - LoginTool class.

Tests for login authentication functionality.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.auth import LoginResponse, TokenType, User, UserRole
from tools.auth.login_tool import LoginTool


@pytest.fixture
def mock_auth_service():
    """Create mock auth service."""
    service = MagicMock()
    service.authenticate_user = AsyncMock()
    service.db_service = MagicMock()
    service.db_service.is_account_locked = AsyncMock(return_value=(False, {}))
    return service


@pytest.fixture
def login_tool(mock_auth_service):
    """Create LoginTool instance."""
    return LoginTool(mock_auth_service)


@pytest.fixture
def mock_context():
    """Create mock FastMCP context."""
    ctx = MagicMock()
    request = MagicMock()
    request.client = MagicMock()
    request.client.host = "192.168.1.100"
    request.headers = {"user-agent": "TestClient/1.0"}
    ctx.get_http_request.return_value = request
    return ctx


@pytest.fixture
def mock_user():
    """Create mock User instance."""
    return User(
        id="user-123",
        username="testuser",
        email="test@example.com",
        role=UserRole.USER,
        last_login="2024-01-15T10:00:00Z",
        is_active=True,
    )


class TestLoginToolInit:
    """Tests for LoginTool initialization."""

    def test_initialization(self, mock_auth_service):
        """Test LoginTool is initialized correctly."""
        tool = LoginTool(mock_auth_service)
        assert tool.auth_service == mock_auth_service


class TestFormatLockTimeRemaining:
    """Tests for _format_lock_time_remaining method."""

    def test_none_lock_expires_returns_permanently(self, login_tool):
        """Test None lock_expires_at returns permanently."""
        result = login_tool._format_lock_time_remaining(None)
        assert result == "permanently"

    def test_expired_lock_returns_shortly(self, login_tool):
        """Test expired lock returns shortly."""
        past_time = (datetime.now(UTC) - timedelta(minutes=5)).isoformat()
        result = login_tool._format_lock_time_remaining(past_time)
        assert result == "shortly"

    def test_less_than_one_minute(self, login_tool):
        """Test less than one minute remaining."""
        future_time = (datetime.now(UTC) + timedelta(seconds=30)).isoformat()
        result = login_tool._format_lock_time_remaining(future_time)
        assert result == "less than a minute"

    def test_exactly_one_minute(self, login_tool):
        """Test exactly one minute remaining."""
        future_time = (datetime.now(UTC) + timedelta(seconds=90)).isoformat()
        result = login_tool._format_lock_time_remaining(future_time)
        assert result == "1 minute"

    def test_multiple_minutes(self, login_tool):
        """Test multiple minutes remaining."""
        # Use 5.5 minutes to ensure we get "5 minutes" even with execution time
        future_time = (datetime.now(UTC) + timedelta(minutes=5, seconds=30)).isoformat()
        result = login_tool._format_lock_time_remaining(future_time)
        assert result == "5 minutes"

    def test_invalid_format_returns_some_time(self, login_tool):
        """Test invalid format returns some time."""
        result = login_tool._format_lock_time_remaining("not-a-date")
        assert result == "some time"

    def test_z_suffix_is_handled(self, login_tool):
        """Test ISO format with Z suffix is handled."""
        future_time = (datetime.now(UTC) + timedelta(minutes=3)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        result = login_tool._format_lock_time_remaining(future_time)
        assert "minute" in result


class TestLogin:
    """Tests for login method."""

    @pytest.mark.asyncio
    async def test_login_success(
        self, login_tool, mock_auth_service, mock_context, mock_user
    ):
        """Test successful login."""
        mock_auth_service.authenticate_user.return_value = LoginResponse(
            user=mock_user,
            token="test-token",
            token_type=TokenType.BEARER,
            expires_in=3600,
            session_id="session-123",
        )

        with patch("tools.auth.login_tool.login_rate_limiter") as mock_limiter:
            mock_limiter.is_allowed.return_value = True

            result = await login_tool.login(
                {"username": "testuser", "password": "password123"}, ctx=mock_context
            )

        assert result["success"] is True
        assert result["data"]["token"] == "test-token"
        assert result["data"]["session_id"] == "session-123"

    @pytest.mark.asyncio
    async def test_login_with_nested_credentials(
        self, login_tool, mock_auth_service, mock_user
    ):
        """Test login with nested credentials structure."""
        mock_auth_service.authenticate_user.return_value = LoginResponse(
            user=mock_user,
            token="test-token",
            token_type=TokenType.BEARER,
            expires_in=3600,
            session_id="session-123",
        )

        with patch("tools.auth.login_tool.login_rate_limiter") as mock_limiter:
            mock_limiter.is_allowed.return_value = True

            result = await login_tool.login(
                {"credentials": {"username": "testuser", "password": "password123"}}
            )

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_login_rate_limit_exceeded(self, login_tool):
        """Test login when rate limit is exceeded."""
        with patch("tools.auth.login_tool.login_rate_limiter") as mock_limiter:
            mock_limiter.is_allowed.return_value = False

            result = await login_tool.login(
                {"username": "testuser", "password": "password123"}
            )

        assert result["success"] is False
        assert result["error"] == "RATE_LIMIT_EXCEEDED"
        assert "retry_after" in result

    @pytest.mark.asyncio
    async def test_login_username_locked(self, login_tool, mock_auth_service):
        """Test login when username is locked."""
        mock_auth_service.db_service.is_account_locked.return_value = (
            True,
            {"lock_expires_at": "2024-01-15T12:00:00Z"},
        )

        with patch("tools.auth.login_tool.login_rate_limiter") as mock_limiter:
            mock_limiter.is_allowed.return_value = True

            result = await login_tool.login(
                {"username": "lockeduser", "password": "password123"}
            )

        assert result["success"] is False
        assert result["error"] == "ACCOUNT_LOCKED"

    @pytest.mark.asyncio
    async def test_login_ip_locked(self, login_tool, mock_auth_service, mock_context):
        """Test login when IP is locked."""
        # First call returns False (username not locked)
        # Second call returns True (IP is locked)
        mock_auth_service.db_service.is_account_locked.side_effect = [
            (False, {}),
            (True, {"lock_expires_at": "2024-01-15T12:00:00Z"}),
        ]

        with patch("tools.auth.login_tool.login_rate_limiter") as mock_limiter:
            mock_limiter.is_allowed.return_value = True

            result = await login_tool.login(
                {"username": "testuser", "password": "password123"}, ctx=mock_context
            )

        assert result["success"] is False
        assert result["error"] == "IP_LOCKED"

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, login_tool, mock_auth_service):
        """Test login with invalid credentials."""
        mock_auth_service.authenticate_user.return_value = None

        with patch("tools.auth.login_tool.login_rate_limiter") as mock_limiter:
            mock_limiter.is_allowed.return_value = True

            result = await login_tool.login(
                {"username": "testuser", "password": "wrongpassword"}
            )

        assert result["success"] is False
        assert result["error"] == "INVALID_CREDENTIALS"

    @pytest.mark.asyncio
    async def test_login_exception(self, login_tool, mock_auth_service):
        """Test login handles exceptions."""
        mock_auth_service.db_service.is_account_locked.side_effect = Exception(
            "Database error"
        )

        with patch("tools.auth.login_tool.login_rate_limiter") as mock_limiter:
            mock_limiter.is_allowed.return_value = True

            result = await login_tool.login(
                {"username": "testuser", "password": "password123"}
            )

        assert result["success"] is False
        assert result["error"] == "LOGIN_ERROR"
        # Error message should be sanitized (no raw exception details)
        assert "Database error" not in result["message"]
        assert "Login failed" in result["message"]

    @pytest.mark.asyncio
    async def test_login_context_extraction_exception(
        self, login_tool, mock_auth_service, mock_user
    ):
        """Test login handles context extraction exception."""
        mock_auth_service.authenticate_user.return_value = LoginResponse(
            user=mock_user,
            token="test-token",
            token_type=TokenType.BEARER,
            expires_in=3600,
            session_id="session-123",
        )

        ctx = MagicMock()
        ctx.get_http_request.side_effect = Exception("No HTTP context")

        with patch("tools.auth.login_tool.login_rate_limiter") as mock_limiter:
            mock_limiter.is_allowed.return_value = True

            result = await login_tool.login(
                {"username": "testuser", "password": "password123"}, ctx=ctx
            )

        # Should still succeed, just use default client_ip
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_login_role_serialization(self, login_tool, mock_auth_service):
        """Test that user role enum is properly serialized."""
        admin_user = User(
            id="user-123",
            username="admin",
            email="admin@example.com",
            role=UserRole.ADMIN,
            last_login="2024-01-15T10:00:00Z",
            is_active=True,
        )

        mock_auth_service.authenticate_user.return_value = LoginResponse(
            user=admin_user,
            token="test-token",
            token_type=TokenType.BEARER,
            expires_in=3600,
            session_id="session-123",
        )

        with patch("tools.auth.login_tool.login_rate_limiter") as mock_limiter:
            mock_limiter.is_allowed.return_value = True

            result = await login_tool.login(
                {"username": "admin", "password": "password123"}
            )

        assert result["success"] is True
        assert result["data"]["user"]["role"] == "admin"

    @pytest.mark.asyncio
    async def test_login_without_context(
        self, login_tool, mock_auth_service, mock_user
    ):
        """Test login works without context."""
        mock_auth_service.authenticate_user.return_value = LoginResponse(
            user=mock_user,
            token="test-token",
            token_type=TokenType.BEARER,
            expires_in=3600,
            session_id="session-123",
        )

        with patch("tools.auth.login_tool.login_rate_limiter") as mock_limiter:
            mock_limiter.is_allowed.return_value = True

            result = await login_tool.login(
                {"username": "testuser", "password": "password123"}, ctx=None
            )

        assert result["success"] is True
