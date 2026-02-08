"""
Auth Tools Unit Tests - Logout Operations

Tests for logout method including session handling and exception cases.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tools.auth.tools import AuthTools


class TestLogout:
    """Tests for logout method."""

    @pytest.fixture
    def mock_auth_service(self):
        """Create mock auth service."""
        service = MagicMock()
        service.sessions = {}
        service.session_service = MagicMock()
        service.db_service = MagicMock()
        service._log_security_event = AsyncMock()
        return service

    @pytest.fixture
    def auth_tools(self, mock_auth_service):
        """Create AuthTools instance."""
        with patch("tools.auth.tools.logger"):
            return AuthTools(mock_auth_service)

    @pytest.mark.asyncio
    async def test_logout_with_username(self, auth_tools, mock_auth_service):
        """Test logout with direct username parameter."""
        mock_auth_service.session_service.delete_session = AsyncMock(return_value=1)

        result = await auth_tools.logout(
            session_id="session-123",
            username="testuser",
        )

        assert result["success"] is True
        assert result["message"] == "Logout successful"
        mock_auth_service._log_security_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_logout_without_identifiable_user(
        self, auth_tools, mock_auth_service
    ):
        """Test logout without identifiable user."""
        mock_auth_service.session_service.get_session = AsyncMock(return_value=None)
        mock_auth_service.session_service.delete_session = AsyncMock(return_value=0)

        result = await auth_tools.logout(session_id="session-123")

        assert result["success"] is True
        # Should not log security event since user is unknown
        mock_auth_service._log_security_event.assert_not_called()

    @pytest.mark.asyncio
    async def test_logout_from_database_session(self, auth_tools, mock_auth_service):
        """Test logout retrieves username from database session."""
        db_session = MagicMock()
        db_session.user_id = "user-123"
        mock_auth_service.session_service.get_session = AsyncMock(
            return_value=db_session
        )
        mock_auth_service.session_service.delete_session = AsyncMock(return_value=1)

        user = MagicMock()
        user.username = "dbuser"
        mock_auth_service.db_service.get_user_by_id = AsyncMock(return_value=user)

        result = await auth_tools.logout(session_id="session-123")

        assert result["success"] is True
        mock_auth_service._log_security_event.assert_called_once()
        call_args = mock_auth_service._log_security_event.call_args
        assert call_args[1]["username"] == "dbuser"

    @pytest.mark.asyncio
    async def test_logout_db_session_no_user_id(self, auth_tools, mock_auth_service):
        """Test logout when db session has no user_id."""
        db_session = MagicMock()
        db_session.user_id = None
        mock_auth_service.session_service.get_session = AsyncMock(
            return_value=db_session
        )
        mock_auth_service.session_service.delete_session = AsyncMock(return_value=0)

        result = await auth_tools.logout(session_id="session-123")

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_logout_db_session_user_not_found(
        self, auth_tools, mock_auth_service
    ):
        """Test logout when user not found in database."""
        db_session = MagicMock()
        db_session.user_id = "user-123"
        mock_auth_service.session_service.get_session = AsyncMock(
            return_value=db_session
        )
        mock_auth_service.session_service.delete_session = AsyncMock(return_value=0)
        mock_auth_service.db_service.get_user_by_id = AsyncMock(return_value=None)

        result = await auth_tools.logout(session_id="session-123")

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_logout_db_session_exception(self, auth_tools, mock_auth_service):
        """Test logout handles db session lookup exception."""
        mock_auth_service.session_service.get_session = AsyncMock(
            side_effect=Exception("DB error")
        )
        mock_auth_service.session_service.delete_session = AsyncMock(return_value=0)

        result = await auth_tools.logout(session_id="session-123")

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_logout_from_legacy_session(self, auth_tools, mock_auth_service):
        """Test logout retrieves username from legacy in-memory session."""
        mock_auth_service.session_service.get_session = AsyncMock(return_value=None)
        mock_auth_service.session_service.delete_session = AsyncMock(return_value=0)
        mock_auth_service.sessions["session-123"] = {"user_id": "user-456"}

        user = MagicMock()
        user.username = "legacyuser"
        mock_auth_service.db_service.get_user_by_id = AsyncMock(return_value=user)

        result = await auth_tools.logout(session_id="session-123")

        assert result["success"] is True
        assert "session-123" not in mock_auth_service.sessions

    @pytest.mark.asyncio
    async def test_logout_legacy_session_no_user_id(
        self, auth_tools, mock_auth_service
    ):
        """Test logout with legacy session without user_id."""
        mock_auth_service.session_service.get_session = AsyncMock(return_value=None)
        mock_auth_service.session_service.delete_session = AsyncMock(return_value=0)
        mock_auth_service.sessions["session-123"] = {}

        result = await auth_tools.logout(session_id="session-123")

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_logout_legacy_session_user_lookup_exception(
        self, auth_tools, mock_auth_service
    ):
        """Test logout handles legacy user lookup exception."""
        mock_auth_service.session_service.get_session = AsyncMock(return_value=None)
        mock_auth_service.session_service.delete_session = AsyncMock(return_value=0)
        mock_auth_service.sessions["session-123"] = {"user_id": "user-456"}
        mock_auth_service.db_service.get_user_by_id = AsyncMock(
            side_effect=Exception("Lookup failed")
        )

        result = await auth_tools.logout(session_id="session-123")

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_logout_with_context_metadata(self, auth_tools, mock_auth_service):
        """Test logout extracts client metadata from context."""
        mock_auth_service.session_service.delete_session = AsyncMock(return_value=1)

        ctx = MagicMock()
        ctx.meta = {"clientIp": "192.168.1.1", "userAgent": "TestBrowser/1.0"}

        result = await auth_tools.logout(
            session_id="session-123",
            username="testuser",
            ctx=ctx,
        )

        assert result["success"] is True
        call_args = mock_auth_service._log_security_event.call_args
        assert call_args[1]["client_ip"] == "192.168.1.1"
        assert call_args[1]["user_agent"] == "TestBrowser/1.0"

    @pytest.mark.asyncio
    async def test_logout_session_termination_failed(
        self, auth_tools, mock_auth_service
    ):
        """Test logout when session termination fails."""
        mock_auth_service.session_service.delete_session = AsyncMock(
            side_effect=Exception("Delete failed")
        )

        result = await auth_tools.logout(
            session_id="session-123",
            username="testuser",
        )

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_logout_exception(self, auth_tools, mock_auth_service):
        """Test logout handles main exception."""
        mock_auth_service.session_service.delete_session = AsyncMock(return_value=1)
        mock_auth_service._log_security_event = AsyncMock(
            side_effect=Exception("Log error")
        )

        result = await auth_tools.logout(
            session_id="session-123",
            username="testuser",
        )

        assert result["success"] is False
        assert result["error"] == "LOGOUT_ERROR"

    @pytest.mark.asyncio
    async def test_logout_exception_with_failed_logging(
        self, auth_tools, mock_auth_service
    ):
        """Test logout exception when security logging also fails."""
        # First call for normal logout, second for error logging
        call_count = 0

        async def log_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Main error")
            else:
                raise Exception("Log error too")

        mock_auth_service.session_service.delete_session = AsyncMock(return_value=1)
        mock_auth_service._log_security_event = AsyncMock(side_effect=log_side_effect)

        result = await auth_tools.logout(
            session_id="session-123",
            username="testuser",
        )

        assert result["success"] is False
        assert result["error"] == "LOGOUT_ERROR"


class TestLogin:
    """Tests for login method."""

    @pytest.fixture
    def mock_auth_service(self):
        """Create mock auth service."""
        return MagicMock()

    @pytest.fixture
    def auth_tools(self, mock_auth_service):
        """Create AuthTools instance."""
        with patch("tools.auth.tools.logger"):
            return AuthTools(mock_auth_service)

    @pytest.mark.asyncio
    async def test_login_exception(self, auth_tools):
        """Test login handles exception from login tool."""
        auth_tools.login_tool.login = AsyncMock(side_effect=Exception("Login error"))

        ctx = MagicMock()
        with pytest.raises(Exception) as exc_info:
            await auth_tools.login({"username": "test"}, ctx)

        assert "Login error" in str(exc_info.value)


class TestGetCurrentUser:
    """Tests for get_current_user method."""

    @pytest.fixture
    def mock_auth_service(self):
        """Create mock auth service."""
        return MagicMock()

    @pytest.fixture
    def auth_tools(self, mock_auth_service):
        """Create AuthTools instance."""
        with patch("tools.auth.tools.logger"):
            return AuthTools(mock_auth_service)

    @pytest.mark.asyncio
    async def test_get_current_user_success(self, auth_tools, mock_auth_service):
        """Test successful get current user."""
        user = MagicMock()
        user.is_active = True
        user.model_dump.return_value = {"id": "user-123", "username": "testuser"}
        mock_auth_service.get_user = AsyncMock(return_value=user)

        result = await auth_tools.get_current_user("valid-token")

        assert result["success"] is True
        assert result["data"]["user"]["username"] == "testuser"

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, auth_tools, mock_auth_service):
        """Test get current user with invalid token."""
        mock_auth_service.get_user = AsyncMock(return_value=None)

        result = await auth_tools.get_current_user("invalid-token")

        assert result["success"] is False
        assert result["error"] == "INVALID_TOKEN"

    @pytest.mark.asyncio
    async def test_get_current_user_inactive(self, auth_tools, mock_auth_service):
        """Test get current user when user inactive."""
        user = MagicMock()
        user.is_active = False
        mock_auth_service.get_user = AsyncMock(return_value=user)

        result = await auth_tools.get_current_user("valid-token")

        assert result["success"] is False
        assert result["error"] == "INVALID_TOKEN"

    @pytest.mark.asyncio
    async def test_get_current_user_exception(self, auth_tools, mock_auth_service):
        """Test get current user handles exceptions."""
        mock_auth_service.get_user = AsyncMock(side_effect=Exception("DB error"))

        result = await auth_tools.get_current_user("valid-token")

        assert result["success"] is False
        assert result["error"] == "GET_USER_ERROR"
