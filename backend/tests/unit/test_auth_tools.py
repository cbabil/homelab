"""Tests for auth tools."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from tools.auth.tools import AuthTools
from models.auth import User, UserRole

pytestmark = pytest.mark.skip(reason="AuthTools not implemented")


@pytest.fixture
def mock_auth_service():
    """Create mock auth service."""
    service = MagicMock()
    service.get_user_by_id = AsyncMock()
    service._validate_jwt_token = MagicMock()
    return service


@pytest.fixture
def auth_tools(mock_auth_service):
    """Create auth tools with mock service."""
    return AuthTools(mock_auth_service)


class TestGetCurrentUser:
    """Tests for get_current_user tool."""

    @pytest.mark.asyncio
    async def test_get_current_user_valid_token(self, auth_tools, mock_auth_service):
        """Should return user data for valid token."""
        # Arrange
        user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            role=UserRole.USER,
            last_login="2025-01-01T00:00:00Z",
            is_active=True
        )
        mock_auth_service._validate_jwt_token.return_value = {
            "user_id": "user-123",
            "username": "testuser"
        }
        mock_auth_service.get_user_by_id.return_value = user

        # Act
        result = await auth_tools.get_current_user(token="valid-token")

        # Assert
        assert result["success"] is True
        assert result["data"]["user"]["username"] == "testuser"

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, auth_tools, mock_auth_service):
        """Should return error for invalid token."""
        mock_auth_service._validate_jwt_token.return_value = None

        result = await auth_tools.get_current_user(token="invalid-token")

        assert result["success"] is False
        assert result["error"] == "INVALID_TOKEN"

    @pytest.mark.asyncio
    async def test_get_current_user_inactive_user(self, auth_tools, mock_auth_service):
        """Should return error for inactive user."""
        user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            role=UserRole.USER,
            last_login="2025-01-01T00:00:00Z",
            is_active=False
        )
        mock_auth_service._validate_jwt_token.return_value = {"user_id": "user-123"}
        mock_auth_service.get_user_by_id.return_value = user

        result = await auth_tools.get_current_user(token="valid-token")

        assert result["success"] is False
        assert result["error"] == "USER_INACTIVE"


class TestCreateUser:
    """Tests for create_user tool (admin only)."""

    @pytest.mark.asyncio
    async def test_create_user_as_admin(self, auth_tools, mock_auth_service):
        """Admin should be able to create new user."""
        # Arrange
        admin = User(
            id="admin-123",
            username="admin",
            email="admin@example.com",
            role=UserRole.ADMIN,
            last_login="2025-01-01T00:00:00Z",
            is_active=True
        )
        new_user = User(
            id="user-456",
            username="newuser",
            email="new@example.com",
            role=UserRole.USER,
            last_login="2025-01-01T00:00:00Z",
            is_active=True
        )
        mock_auth_service._validate_jwt_token.return_value = {"user_id": "admin-123"}
        mock_auth_service.get_user_by_id.return_value = admin
        mock_auth_service.create_user = AsyncMock(return_value=new_user)

        # Act
        result = await auth_tools.create_user(
            token="admin-token",
            username="newuser",
            email="new@example.com",
            password="SecurePass123!",
            role="user"
        )

        # Assert
        assert result["success"] is True
        assert result["data"]["user"]["username"] == "newuser"

    @pytest.mark.asyncio
    async def test_create_user_as_non_admin_fails(self, auth_tools, mock_auth_service):
        """Non-admin should not be able to create users."""
        regular_user = User(
            id="user-123",
            username="regular",
            email="regular@example.com",
            role=UserRole.USER,
            last_login="2025-01-01T00:00:00Z",
            is_active=True
        )
        mock_auth_service._validate_jwt_token.return_value = {"user_id": "user-123"}
        mock_auth_service.get_user_by_id.return_value = regular_user

        result = await auth_tools.create_user(
            token="user-token",
            username="newuser",
            email="new@example.com",
            password="SecurePass123!",
            role="user"
        )

        assert result["success"] is False
        assert result["error"] == "PERMISSION_DENIED"


class TestListUsers:
    """Tests for list_users tool (admin only)."""

    @pytest.mark.asyncio
    async def test_list_users_as_admin(self, auth_tools, mock_auth_service):
        """Admin should be able to list all users."""
        admin = User(
            id="admin-123",
            username="admin",
            email="admin@example.com",
            role=UserRole.ADMIN,
            last_login="2025-01-01T00:00:00Z",
            is_active=True
        )
        users = [
            admin,
            User(
                id="user-456",
                username="user1",
                email="user1@example.com",
                role=UserRole.USER,
                last_login="2025-01-01T00:00:00Z",
                is_active=True
            )
        ]
        mock_auth_service._validate_jwt_token.return_value = {"user_id": "admin-123"}
        mock_auth_service.get_user_by_id.return_value = admin
        mock_auth_service.get_all_users = AsyncMock(return_value=users)

        result = await auth_tools.list_users(token="admin-token")

        assert result["success"] is True
        assert len(result["data"]["users"]) == 2

    @pytest.mark.asyncio
    async def test_list_users_as_non_admin_fails(self, auth_tools, mock_auth_service):
        """Non-admin should not be able to list users."""
        regular_user = User(
            id="user-123",
            username="regular",
            email="regular@example.com",
            role=UserRole.USER,
            last_login="2025-01-01T00:00:00Z",
            is_active=True
        )
        mock_auth_service._validate_jwt_token.return_value = {"user_id": "user-123"}
        mock_auth_service.get_user_by_id.return_value = regular_user

        result = await auth_tools.list_users(token="user-token")

        assert result["success"] is False
        assert result["error"] == "PERMISSION_DENIED"
