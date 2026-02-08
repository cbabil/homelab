"""
Auth Tools Unit Tests

Tests for authentication tools: login, logout, get_current_user.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestAuthTools:
    """Tests for authentication tools."""

    @pytest.fixture
    def mock_auth_service(self):
        """Create mock auth service."""
        service = MagicMock()
        service.sessions = {}
        service._validate_jwt_token = MagicMock(return_value=None)
        service.get_user_by_id = AsyncMock(return_value=None)
        service._log_security_event = AsyncMock()
        return service

    @pytest.fixture
    def mock_user(self):
        """Create a mock user object."""
        user = MagicMock()
        user.id = "user-123"
        user.username = "testuser"
        user.email = "test@example.com"
        user.role = "user"
        user.is_active = True
        user.model_dump = MagicMock(
            return_value={
                "id": "user-123",
                "username": "testuser",
                "email": "test@example.com",
                "role": "user",
                "is_active": True,
            }
        )
        return user

    @pytest.fixture
    def auth_tools(self, mock_auth_service):
        """Create AuthTools instance with mock service."""
        from tools.auth.tools import AuthTools

        return AuthTools(mock_auth_service)


class TestLogin:
    """Tests for the login tool."""

    @pytest.fixture
    def mock_auth_service(self):
        """Create mock auth service for login tests."""
        service = MagicMock()
        service.sessions = {}
        return service

    @pytest.fixture
    def mock_login_response(self):
        """Mock successful login response."""
        return MagicMock(
            user=MagicMock(
                model_dump=MagicMock(
                    return_value={
                        "id": "user-123",
                        "username": "testuser",
                        "role": "user",
                    }
                )
            ),
            token="jwt-token-123",
            expires_in=3600,
            session_id="session-123",
            token_type=MagicMock(value="bearer"),
        )

    @pytest.mark.asyncio
    async def test_login_success(self, mock_auth_service, mock_login_response):
        """Test successful login."""
        from tools.auth.tools import AuthTools

        # Setup mock
        mock_auth_service.authenticate_user = AsyncMock(
            return_value=mock_login_response
        )
        mock_auth_service.db_service = MagicMock()
        mock_auth_service.db_service.is_account_locked = AsyncMock(
            return_value=(False, {})
        )

        auth_tools = AuthTools(mock_auth_service)

        # Create mock context
        ctx = MagicMock()
        ctx.get_http_request = MagicMock(
            return_value=MagicMock(
                client=MagicMock(host="127.0.0.1"), headers={"user-agent": "test-agent"}
            )
        )

        with patch("tools.auth.login_tool.login_rate_limiter") as mock_limiter:
            mock_limiter.is_allowed.return_value = True
            result = await auth_tools.login(
                {"username": "testuser", "password": "password123"}, ctx
            )

        assert result["success"] is True
        assert "data" in result
        assert result["data"]["user"]["username"] == "testuser"
        assert result["data"]["token"] == "jwt-token-123"

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, mock_auth_service):
        """Test login with invalid credentials."""
        from tools.auth.tools import AuthTools

        mock_auth_service.authenticate_user = AsyncMock(return_value=None)
        mock_auth_service.db_service = MagicMock()
        mock_auth_service.db_service.is_account_locked = AsyncMock(
            return_value=(False, {})
        )

        auth_tools = AuthTools(mock_auth_service)
        ctx = MagicMock()
        ctx.get_http_request = MagicMock(
            return_value=MagicMock(client=MagicMock(host="127.0.0.1"), headers={})
        )

        with patch("tools.auth.login_tool.login_rate_limiter") as mock_limiter:
            mock_limiter.is_allowed.return_value = True
            result = await auth_tools.login(
                {"username": "baduser", "password": "wrongpass"}, ctx
            )

        assert result["success"] is False
        assert result["error"] == "INVALID_CREDENTIALS"


class TestLogout:
    """Tests for the logout tool."""

    @pytest.fixture
    def mock_auth_service(self):
        """Create mock auth service for logout tests."""
        service = MagicMock()
        service.sessions = {"session-123": {"user_id": "user-123"}}
        service._log_security_event = AsyncMock()
        service.db_service = MagicMock()
        service.db_service.get_user_by_id = AsyncMock(
            return_value=MagicMock(username="testuser")
        )
        return service

    @pytest.mark.asyncio
    async def test_logout_success(self, mock_auth_service):
        """Test successful logout."""
        from tools.auth.tools import AuthTools

        auth_tools = AuthTools(mock_auth_service)

        result = await auth_tools.logout(session_id="session-123", username="testuser")

        assert result["success"] is True
        assert result["message"] == "Logout successful"
        # Session should be removed
        assert "session-123" not in mock_auth_service.sessions

    @pytest.mark.asyncio
    async def test_logout_no_session(self, mock_auth_service):
        """Test logout when session doesn't exist."""
        from tools.auth.tools import AuthTools

        mock_auth_service.sessions = {}
        auth_tools = AuthTools(mock_auth_service)

        result = await auth_tools.logout(session_id="nonexistent")

        # Should still succeed (idempotent)
        assert result["success"] is True


class TestGetCurrentUser:
    """Tests for the get_current_user tool."""

    @pytest.fixture
    def mock_auth_service(self):
        """Create mock auth service."""
        service = MagicMock()
        return service

    @pytest.fixture
    def mock_user(self):
        """Create mock user."""
        user = MagicMock()
        user.id = "user-123"
        user.username = "testuser"
        user.is_active = True
        user.model_dump = MagicMock(
            return_value={"id": "user-123", "username": "testuser", "is_active": True}
        )
        return user

    @pytest.mark.asyncio
    async def test_get_current_user_valid_token(self, mock_auth_service, mock_user):
        """Test getting current user with valid token."""
        from tools.auth.tools import AuthTools

        mock_auth_service.get_user = AsyncMock(return_value=mock_user)

        auth_tools = AuthTools(mock_auth_service)

        result = await auth_tools.get_current_user("valid-token")

        assert result["success"] is True
        assert result["data"]["user"]["username"] == "testuser"

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, mock_auth_service):
        """Test getting current user with invalid token."""
        from tools.auth.tools import AuthTools

        mock_auth_service.get_user = AsyncMock(return_value=None)

        auth_tools = AuthTools(mock_auth_service)

        result = await auth_tools.get_current_user("invalid-token")

        assert result["success"] is False
        assert result["error"] == "INVALID_TOKEN"

    @pytest.mark.asyncio
    async def test_get_current_user_inactive_user(self, mock_auth_service):
        """Test getting current user when user is inactive."""
        from tools.auth.tools import AuthTools

        inactive_user = MagicMock()
        inactive_user.is_active = False
        mock_auth_service.get_user = AsyncMock(return_value=inactive_user)

        auth_tools = AuthTools(mock_auth_service)

        result = await auth_tools.get_current_user("token-for-inactive")

        assert result["success"] is False
        # Both None and inactive user return INVALID_TOKEN
        assert result["error"] == "INVALID_TOKEN"

    @pytest.mark.asyncio
    async def test_get_current_user_not_found(self, mock_auth_service):
        """Test getting current user when user doesn't exist."""
        from tools.auth.tools import AuthTools

        mock_auth_service.get_user = AsyncMock(return_value=None)

        auth_tools = AuthTools(mock_auth_service)

        result = await auth_tools.get_current_user("token-for-missing")

        assert result["success"] is False
        assert result["error"] == "INVALID_TOKEN"


class TestCreateInitialAdmin:
    """Tests for the create_initial_admin tool."""

    @pytest.fixture
    def mock_auth_service(self):
        """Create mock auth service with db_service."""
        service = MagicMock()
        service.sessions = {}
        service.db_service = MagicMock()
        return service

    @pytest.fixture
    def mock_user(self):
        """Create mock admin user."""
        user = MagicMock()
        user.id = "admin-123"
        user.username = "admin"
        user.email = "admin@example.com"
        user.role = "admin"
        user.is_active = True
        return user

    @pytest.mark.asyncio
    async def test_create_initial_admin_success(self, mock_auth_service, mock_user):
        """Test creating initial admin when system not set up."""
        from tools.auth.tools import AuthTools

        mock_auth_service.db_service.is_system_setup = AsyncMock(return_value=False)
        mock_auth_service.has_admin_user = AsyncMock(return_value=False)
        mock_auth_service.create_user = AsyncMock(return_value=mock_user)
        mock_auth_service.db_service.mark_system_setup_complete = AsyncMock(
            return_value=True
        )

        auth_tools = AuthTools(mock_auth_service)

        result = await auth_tools.create_initial_admin(
            {
                "username": "admin",
                "email": "admin@example.com",
                "password": "SecurePassword123",
            }
        )

        assert result["success"] is True
        assert result["message"] == "Admin user created successfully"
        assert result["data"]["username"] == "admin"
        assert result["data"]["email"] == "admin@example.com"

        # Verify create_user was called with admin role
        mock_auth_service.create_user.assert_called_once()
        call_kwargs = mock_auth_service.create_user.call_args.kwargs
        assert call_kwargs["username"] == "admin"
        assert call_kwargs["email"] == "admin@example.com"
        assert call_kwargs["password"] == "SecurePassword123"

        # Verify system was marked as setup complete
        mock_auth_service.db_service.mark_system_setup_complete.assert_called_once_with(
            "admin-123"
        )

    @pytest.mark.asyncio
    async def test_create_initial_admin_fails_when_already_setup(
        self, mock_auth_service
    ):
        """Test create_initial_admin fails when system is already set up."""
        from tools.auth.tools import AuthTools

        mock_auth_service.db_service.is_system_setup = AsyncMock(return_value=True)

        auth_tools = AuthTools(mock_auth_service)

        result = await auth_tools.create_initial_admin(
            {
                "username": "admin",
                "email": "admin@example.com",
                "password": "SecurePassword123",
            }
        )

        assert result["success"] is False
        assert result["error"] == "ALREADY_SETUP"
        assert "already set up" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_create_initial_admin_fails_when_admin_exists(
        self, mock_auth_service
    ):
        """Test create_initial_admin fails when an admin already exists."""
        from tools.auth.tools import AuthTools

        mock_auth_service.db_service.is_system_setup = AsyncMock(return_value=False)
        mock_auth_service.has_admin_user = AsyncMock(return_value=True)

        auth_tools = AuthTools(mock_auth_service)

        result = await auth_tools.create_initial_admin(
            {
                "username": "admin",
                "email": "admin@example.com",
                "password": "SecurePassword123",
            }
        )

        assert result["success"] is False
        assert result["error"] == "ADMIN_EXISTS"
        assert "admin user already exists" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_create_initial_admin_missing_username(self, mock_auth_service):
        """Test create_initial_admin fails when username is missing."""
        from tools.auth.tools import AuthTools

        mock_auth_service.db_service.is_system_setup = AsyncMock(return_value=False)
        mock_auth_service.has_admin_user = AsyncMock(return_value=False)

        auth_tools = AuthTools(mock_auth_service)

        result = await auth_tools.create_initial_admin(
            {"email": "admin@example.com", "password": "SecurePassword123"}
        )

        assert result["success"] is False
        assert result["error"] == "MISSING_FIELDS"

    @pytest.mark.asyncio
    async def test_create_initial_admin_email_is_optional(self, mock_auth_service):
        """Test create_initial_admin succeeds without email (email is optional)."""
        from tools.auth.tools import AuthTools

        mock_auth_service.db_service.is_system_setup = AsyncMock(return_value=False)
        mock_auth_service.has_admin_user = AsyncMock(return_value=False)
        mock_user = MagicMock()
        mock_user.id = "admin-123"
        mock_auth_service.create_user = AsyncMock(return_value=mock_user)
        mock_auth_service.db_service.mark_system_setup_complete = AsyncMock(
            return_value=True
        )

        auth_tools = AuthTools(mock_auth_service)

        result = await auth_tools.create_initial_admin(
            {"username": "admin", "password": "SecurePassword123"}
        )

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_create_initial_admin_missing_password(self, mock_auth_service):
        """Test create_initial_admin fails when password is missing."""
        from tools.auth.tools import AuthTools

        mock_auth_service.db_service.is_system_setup = AsyncMock(return_value=False)
        mock_auth_service.has_admin_user = AsyncMock(return_value=False)

        auth_tools = AuthTools(mock_auth_service)

        result = await auth_tools.create_initial_admin(
            {"username": "admin", "email": "admin@example.com"}
        )

        assert result["success"] is False
        assert result["error"] == "MISSING_FIELDS"

    @pytest.mark.asyncio
    async def test_create_initial_admin_weak_password(self, mock_auth_service):
        """Test create_initial_admin fails with short password."""
        from tools.auth.tools import AuthTools

        mock_auth_service.db_service.is_system_setup = AsyncMock(return_value=False)
        mock_auth_service.has_admin_user = AsyncMock(return_value=False)

        auth_tools = AuthTools(mock_auth_service)

        result = await auth_tools.create_initial_admin(
            {"username": "admin", "email": "admin@example.com", "password": "short"}
        )

        assert result["success"] is False
        assert result["error"] == "WEAK_PASSWORD"
        assert "8 characters" in result["message"]

    @pytest.mark.asyncio
    async def test_create_initial_admin_create_user_fails(self, mock_auth_service):
        """Test create_initial_admin handles create_user failure."""
        from tools.auth.tools import AuthTools

        mock_auth_service.db_service.is_system_setup = AsyncMock(return_value=False)
        mock_auth_service.has_admin_user = AsyncMock(return_value=False)
        mock_auth_service.create_user = AsyncMock(return_value=None)

        auth_tools = AuthTools(mock_auth_service)

        result = await auth_tools.create_initial_admin(
            {
                "username": "admin",
                "email": "admin@example.com",
                "password": "SecurePassword123",
            }
        )

        assert result["success"] is False
        assert result["error"] == "CREATE_FAILED"

    @pytest.mark.asyncio
    async def test_create_initial_admin_handles_exception(self, mock_auth_service):
        """Test create_initial_admin handles unexpected exceptions."""
        from tools.auth.tools import AuthTools

        mock_auth_service.db_service.is_system_setup = AsyncMock(return_value=False)
        mock_auth_service.has_admin_user = AsyncMock(return_value=False)
        mock_auth_service.create_user = AsyncMock(
            side_effect=Exception("Database error")
        )

        auth_tools = AuthTools(mock_auth_service)

        result = await auth_tools.create_initial_admin(
            {
                "username": "admin",
                "email": "admin@example.com",
                "password": "SecurePassword123",
            }
        )

        assert result["success"] is False
        assert result["error"] == "CREATE_ERROR"
        assert "Database error" in result["message"]

    @pytest.mark.asyncio
    async def test_create_initial_admin_mark_setup_fails_but_succeeds(
        self, mock_auth_service, mock_user
    ):
        """Test create_initial_admin succeeds even if marking setup fails."""
        from tools.auth.tools import AuthTools

        mock_auth_service.db_service.is_system_setup = AsyncMock(return_value=False)
        mock_auth_service.has_admin_user = AsyncMock(return_value=False)
        mock_auth_service.create_user = AsyncMock(return_value=mock_user)
        mock_auth_service.db_service.mark_system_setup_complete = AsyncMock(
            return_value=False
        )

        auth_tools = AuthTools(mock_auth_service)

        result = await auth_tools.create_initial_admin(
            {
                "username": "admin",
                "email": "admin@example.com",
                "password": "SecurePassword123",
            }
        )

        # Should still succeed - admin was created
        assert result["success"] is True
        assert result["message"] == "Admin user created successfully"


class TestGetUserByUsername:
    """Tests for the get_user_by_username tool."""

    @pytest.fixture
    def mock_auth_service(self):
        """Create mock auth service."""
        service = MagicMock()
        service.db_service = MagicMock()
        return service

    @pytest.fixture
    def mock_user(self):
        """Create mock user."""
        from datetime import datetime

        user = MagicMock()
        user.id = "user-123"
        user.username = "testuser"
        user.email = "test@example.com"
        user.role = MagicMock(value="user")
        user.is_active = True
        user.created_at = datetime(2024, 1, 1, 12, 0, 0)
        user.updated_at = datetime(2024, 1, 15, 10, 0, 0)
        return user

    @pytest.mark.asyncio
    async def test_get_user_by_username_success(self, mock_auth_service, mock_user):
        """Test getting user by username successfully."""
        from tools.auth.tools import AuthTools

        mock_auth_service._validate_jwt_token = MagicMock(
            return_value={"user_id": "user-1"}
        )
        mock_auth_service.db_service.get_user_by_username = AsyncMock(
            return_value=mock_user
        )

        auth_tools = AuthTools(mock_auth_service)

        result = await auth_tools.get_user_by_username(
            {"token": "valid-token", "username": "testuser"}
        )

        assert result["success"] is True
        assert result["data"]["username"] == "testuser"
        assert result["data"]["email"] == "test@example.com"
        assert result["data"]["role"] == "user"
        assert result["data"]["is_active"] is True

    @pytest.mark.asyncio
    async def test_get_user_by_username_not_found(self, mock_auth_service):
        """Test getting non-existent user."""
        from tools.auth.tools import AuthTools

        mock_auth_service._validate_jwt_token = MagicMock(
            return_value={"user_id": "user-1"}
        )
        mock_auth_service.db_service.get_user_by_username = AsyncMock(return_value=None)

        auth_tools = AuthTools(mock_auth_service)

        result = await auth_tools.get_user_by_username(
            {"token": "valid-token", "username": "nonexistent"}
        )

        assert result["success"] is False
        assert result["error"] == "NOT_FOUND"

    @pytest.mark.asyncio
    async def test_get_user_by_username_missing_token(self, mock_auth_service):
        """Test get_user_by_username fails when token is missing."""
        from tools.auth.tools import AuthTools

        auth_tools = AuthTools(mock_auth_service)

        result = await auth_tools.get_user_by_username({"username": "testuser"})

        assert result["success"] is False
        assert result["error"] == "MISSING_TOKEN"

    @pytest.mark.asyncio
    async def test_get_user_by_username_invalid_token(self, mock_auth_service):
        """Test get_user_by_username fails with invalid token."""
        from tools.auth.tools import AuthTools

        mock_auth_service._validate_jwt_token = MagicMock(return_value=None)

        auth_tools = AuthTools(mock_auth_service)

        result = await auth_tools.get_user_by_username(
            {"token": "bad-token", "username": "testuser"}
        )

        assert result["success"] is False
        assert result["error"] == "INVALID_TOKEN"

    @pytest.mark.asyncio
    async def test_get_user_by_username_missing_username(self, mock_auth_service):
        """Test get_user_by_username fails when username is missing."""
        from tools.auth.tools import AuthTools

        mock_auth_service._validate_jwt_token = MagicMock(
            return_value={"user_id": "user-1"}
        )

        auth_tools = AuthTools(mock_auth_service)

        result = await auth_tools.get_user_by_username({"token": "valid-token"})

        assert result["success"] is False
        assert result["error"] == "MISSING_USERNAME"

    @pytest.mark.asyncio
    async def test_get_user_by_username_handles_error(self, mock_auth_service):
        """Test get_user_by_username handles errors gracefully."""
        from tools.auth.tools import AuthTools

        mock_auth_service._validate_jwt_token = MagicMock(
            return_value={"user_id": "user-1"}
        )
        mock_auth_service.db_service.get_user_by_username = AsyncMock(
            side_effect=Exception("Database error")
        )

        auth_tools = AuthTools(mock_auth_service)

        result = await auth_tools.get_user_by_username(
            {"token": "valid-token", "username": "testuser"}
        )

        assert result["success"] is False
        assert result["error"] == "GET_USER_ERROR"
        assert "Database error" in result["message"]


class TestResetUserPassword:
    """Tests for the reset_user_password tool."""

    @pytest.fixture
    def mock_admin_user(self):
        """Create mock admin user for auth context."""
        admin = MagicMock()
        admin.id = "admin-001"
        admin.username = "admin"
        admin.is_active = True
        admin.role = MagicMock()
        admin.role.value = "admin"
        return admin

    @pytest.fixture
    def mock_auth_service(self, mock_admin_user):
        """Create mock auth service with admin auth context."""
        service = MagicMock()
        service.db_service = MagicMock()
        service._validate_jwt_token = MagicMock(
            return_value={"user_id": "admin-001", "role": "admin"}
        )
        service.get_user_by_id = AsyncMock(return_value=mock_admin_user)
        return service

    @pytest.fixture
    def mock_user(self):
        """Create mock user."""
        user = MagicMock()
        user.id = "user-123"
        user.username = "testuser"
        return user

    @pytest.mark.asyncio
    async def test_reset_user_password_success(self, mock_auth_service, mock_user):
        """Test resetting user password successfully."""
        from tools.auth.tools import AuthTools

        mock_auth_service.db_service.get_user_by_username = AsyncMock(
            return_value=mock_user
        )
        mock_auth_service.db_service.update_user_password = AsyncMock(return_value=True)

        auth_tools = AuthTools(mock_auth_service)

        with patch("lib.auth_helpers.hash_password", return_value="hashed_password"):
            result = await auth_tools.reset_user_password(
                {
                    "token": "valid-admin-token",
                    "username": "testuser",
                    "password": "NewSecurePassword123",
                }
            )

        assert result["success"] is True
        assert result["message"] == "Password reset successfully"
        assert result["data"]["username"] == "testuser"

    @pytest.mark.asyncio
    async def test_reset_user_password_missing_token(self, mock_auth_service):
        """Test reset_user_password fails when token is missing."""
        from tools.auth.tools import AuthTools

        auth_tools = AuthTools(mock_auth_service)

        result = await auth_tools.reset_user_password(
            {"username": "testuser", "password": "NewPassword123"}
        )

        assert result["success"] is False
        assert result["error"] == "MISSING_TOKEN"

    @pytest.mark.asyncio
    async def test_reset_user_password_missing_username(self, mock_auth_service):
        """Test reset_user_password fails when username is missing."""
        from tools.auth.tools import AuthTools

        auth_tools = AuthTools(mock_auth_service)

        result = await auth_tools.reset_user_password(
            {"token": "valid-admin-token", "password": "NewPassword123"}
        )

        assert result["success"] is False
        assert result["error"] == "MISSING_USERNAME"

    @pytest.mark.asyncio
    async def test_reset_user_password_missing_password(self, mock_auth_service):
        """Test reset_user_password fails when password is missing."""
        from tools.auth.tools import AuthTools

        auth_tools = AuthTools(mock_auth_service)

        result = await auth_tools.reset_user_password(
            {"token": "valid-admin-token", "username": "testuser"}
        )

        assert result["success"] is False
        assert result["error"] == "MISSING_PASSWORD"

    @pytest.mark.asyncio
    async def test_reset_user_password_weak_password(self, mock_auth_service):
        """Test reset_user_password fails with short password."""
        from tools.auth.tools import AuthTools

        auth_tools = AuthTools(mock_auth_service)

        result = await auth_tools.reset_user_password(
            {"token": "valid-admin-token", "username": "testuser", "password": "short"}
        )

        assert result["success"] is False
        assert result["error"] == "WEAK_PASSWORD"
        assert "8 characters" in result["message"]

    @pytest.mark.asyncio
    async def test_reset_user_password_user_not_found(self, mock_auth_service):
        """Test reset_user_password fails when user doesn't exist."""
        from tools.auth.tools import AuthTools

        mock_auth_service.db_service.get_user_by_username = AsyncMock(return_value=None)

        auth_tools = AuthTools(mock_auth_service)

        result = await auth_tools.reset_user_password(
            {
                "token": "valid-admin-token",
                "username": "nonexistent",
                "password": "NewSecurePassword123",
            }
        )

        assert result["success"] is False
        assert result["error"] == "NOT_FOUND"

    @pytest.mark.asyncio
    async def test_reset_user_password_update_fails(self, mock_auth_service, mock_user):
        """Test reset_user_password handles update failure."""
        from tools.auth.tools import AuthTools

        mock_auth_service.db_service.get_user_by_username = AsyncMock(
            return_value=mock_user
        )
        mock_auth_service.db_service.update_user_password = AsyncMock(
            return_value=False
        )

        auth_tools = AuthTools(mock_auth_service)

        with patch("lib.auth_helpers.hash_password", return_value="hashed_password"):
            result = await auth_tools.reset_user_password(
                {
                    "token": "valid-admin-token",
                    "username": "testuser",
                    "password": "NewSecurePassword123",
                }
            )

        assert result["success"] is False
        assert result["error"] == "UPDATE_FAILED"

    @pytest.mark.asyncio
    async def test_reset_user_password_handles_error(self, mock_auth_service):
        """Test reset_user_password handles errors gracefully."""
        from tools.auth.tools import AuthTools

        mock_auth_service.db_service.get_user_by_username = AsyncMock(
            side_effect=Exception("Database error")
        )

        auth_tools = AuthTools(mock_auth_service)

        result = await auth_tools.reset_user_password(
            {
                "token": "valid-admin-token",
                "username": "testuser",
                "password": "NewSecurePassword123",
            }
        )

        assert result["success"] is False
        assert result["error"] == "RESET_ERROR"
        assert "Database error" in result["message"]
