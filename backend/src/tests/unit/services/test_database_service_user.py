"""
Unit tests for services/database_service.py - User method delegation.

Tests user-related methods that delegate to UserDatabaseService.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from models.auth import User, UserRole


@pytest.fixture
def mock_user_service():
    """Create mock UserDatabaseService."""
    service = MagicMock()
    return service


@pytest.fixture
def db_service_with_mocks(mock_user_service):
    """Create DatabaseService with mocked user service."""
    with patch("services.database_service.DatabaseConnection"), \
         patch("services.database_service.UserDatabaseService") as MockUser, \
         patch("services.database_service.ServerDatabaseService"), \
         patch("services.database_service.SessionDatabaseService"), \
         patch("services.database_service.AppDatabaseService"), \
         patch("services.database_service.MetricsDatabaseService"), \
         patch("services.database_service.SystemDatabaseService"), \
         patch("services.database_service.ExportDatabaseService"), \
         patch("services.database_service.SchemaInitializer"):
        from services.database_service import DatabaseService
        MockUser.return_value = mock_user_service
        return DatabaseService()


@pytest.fixture
def sample_user():
    """Create sample User for tests."""
    return User(
        id="user-123",
        username="testuser",
        email="test@example.com",
        role=UserRole.USER,
        is_active=True,
        last_login="2024-01-15T10:00:00Z",
    )


class TestGetUser:
    """Tests for get_user method."""

    @pytest.mark.asyncio
    async def test_get_user_by_id(self, db_service_with_mocks, mock_user_service, sample_user):
        """get_user should delegate to user service with user_id."""
        mock_user_service.get_user = AsyncMock(return_value=sample_user)

        result = await db_service_with_mocks.get_user(user_id="user-123")

        mock_user_service.get_user.assert_awaited_once_with("user-123", None)
        assert result == sample_user

    @pytest.mark.asyncio
    async def test_get_user_by_username(
        self, db_service_with_mocks, mock_user_service, sample_user
    ):
        """get_user should delegate to user service with username."""
        mock_user_service.get_user = AsyncMock(return_value=sample_user)

        result = await db_service_with_mocks.get_user(username="testuser")

        mock_user_service.get_user.assert_awaited_once_with(None, "testuser")
        assert result == sample_user

    @pytest.mark.asyncio
    async def test_get_user_not_found(self, db_service_with_mocks, mock_user_service):
        """get_user should return None when not found."""
        mock_user_service.get_user = AsyncMock(return_value=None)

        result = await db_service_with_mocks.get_user(user_id="nonexistent")

        assert result is None


class TestGetUserByUsername:
    """Tests for get_user_by_username method."""

    @pytest.mark.asyncio
    async def test_get_user_by_username_found(
        self, db_service_with_mocks, mock_user_service, sample_user
    ):
        """get_user_by_username should delegate to user service."""
        mock_user_service.get_user_by_username = AsyncMock(return_value=sample_user)

        result = await db_service_with_mocks.get_user_by_username("testuser")

        mock_user_service.get_user_by_username.assert_awaited_once_with("testuser")
        assert result == sample_user

    @pytest.mark.asyncio
    async def test_get_user_by_username_not_found(
        self, db_service_with_mocks, mock_user_service
    ):
        """get_user_by_username should return None when not found."""
        mock_user_service.get_user_by_username = AsyncMock(return_value=None)

        result = await db_service_with_mocks.get_user_by_username("unknown")

        assert result is None


class TestGetUserById:
    """Tests for get_user_by_id method."""

    @pytest.mark.asyncio
    async def test_get_user_by_id_found(
        self, db_service_with_mocks, mock_user_service, sample_user
    ):
        """get_user_by_id should delegate to user service."""
        mock_user_service.get_user_by_id = AsyncMock(return_value=sample_user)

        result = await db_service_with_mocks.get_user_by_id("user-123")

        mock_user_service.get_user_by_id.assert_awaited_once_with("user-123")
        assert result == sample_user

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(
        self, db_service_with_mocks, mock_user_service
    ):
        """get_user_by_id should return None when not found."""
        mock_user_service.get_user_by_id = AsyncMock(return_value=None)

        result = await db_service_with_mocks.get_user_by_id("nonexistent")

        assert result is None


class TestGetUserPasswordHash:
    """Tests for get_user_password_hash method."""

    @pytest.mark.asyncio
    async def test_get_user_password_hash_found(
        self, db_service_with_mocks, mock_user_service
    ):
        """get_user_password_hash should return hash."""
        mock_user_service.get_user_password_hash = AsyncMock(
            return_value="hashed_password"
        )

        result = await db_service_with_mocks.get_user_password_hash("testuser")

        mock_user_service.get_user_password_hash.assert_awaited_once_with("testuser")
        assert result == "hashed_password"

    @pytest.mark.asyncio
    async def test_get_user_password_hash_not_found(
        self, db_service_with_mocks, mock_user_service
    ):
        """get_user_password_hash should return None when user not found."""
        mock_user_service.get_user_password_hash = AsyncMock(return_value=None)

        result = await db_service_with_mocks.get_user_password_hash("unknown")

        assert result is None


class TestUpdateUserLastLogin:
    """Tests for update_user_last_login method."""

    @pytest.mark.asyncio
    async def test_update_user_last_login_success(
        self, db_service_with_mocks, mock_user_service
    ):
        """update_user_last_login should delegate to user service."""
        mock_user_service.update_user_last_login = AsyncMock(return_value=True)

        result = await db_service_with_mocks.update_user_last_login("testuser")

        mock_user_service.update_user_last_login.assert_awaited_once_with(
            "testuser", None
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_update_user_last_login_with_timestamp(
        self, db_service_with_mocks, mock_user_service
    ):
        """update_user_last_login should pass timestamp."""
        mock_user_service.update_user_last_login = AsyncMock(return_value=True)
        timestamp = "2024-01-15T10:00:00Z"

        result = await db_service_with_mocks.update_user_last_login("testuser", timestamp)

        mock_user_service.update_user_last_login.assert_awaited_once_with(
            "testuser", timestamp
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_update_user_last_login_failure(
        self, db_service_with_mocks, mock_user_service
    ):
        """update_user_last_login should return False on failure."""
        mock_user_service.update_user_last_login = AsyncMock(return_value=False)

        result = await db_service_with_mocks.update_user_last_login("unknown")

        assert result is False


class TestGetAllUsers:
    """Tests for get_all_users method."""

    @pytest.mark.asyncio
    async def test_get_all_users_returns_list(
        self, db_service_with_mocks, mock_user_service, sample_user
    ):
        """get_all_users should return list of users."""
        mock_user_service.get_all_users = AsyncMock(return_value=[sample_user])

        result = await db_service_with_mocks.get_all_users()

        mock_user_service.get_all_users.assert_awaited_once()
        assert result == [sample_user]

    @pytest.mark.asyncio
    async def test_get_all_users_empty(self, db_service_with_mocks, mock_user_service):
        """get_all_users should return empty list when no users."""
        mock_user_service.get_all_users = AsyncMock(return_value=[])

        result = await db_service_with_mocks.get_all_users()

        assert result == []


class TestCreateUser:
    """Tests for create_user method."""

    @pytest.mark.asyncio
    async def test_create_user_success(
        self, db_service_with_mocks, mock_user_service, sample_user
    ):
        """create_user should delegate to user service."""
        mock_user_service.create_user = AsyncMock(return_value=sample_user)

        result = await db_service_with_mocks.create_user(
            username="testuser",
            password_hash="hashed",
            email="test@example.com",
            role=UserRole.USER,
            preferences={"theme": "dark"},
        )

        mock_user_service.create_user.assert_awaited_once_with(
            "testuser", "hashed", "test@example.com", UserRole.USER, {"theme": "dark"}
        )
        assert result == sample_user

    @pytest.mark.asyncio
    async def test_create_user_defaults(
        self, db_service_with_mocks, mock_user_service, sample_user
    ):
        """create_user should use defaults for optional params."""
        mock_user_service.create_user = AsyncMock(return_value=sample_user)

        await db_service_with_mocks.create_user(
            username="testuser",
            password_hash="hashed",
        )

        mock_user_service.create_user.assert_awaited_once_with(
            "testuser", "hashed", "", UserRole.USER, None
        )

    @pytest.mark.asyncio
    async def test_create_user_failure(
        self, db_service_with_mocks, mock_user_service
    ):
        """create_user should return None on failure."""
        mock_user_service.create_user = AsyncMock(return_value=None)

        result = await db_service_with_mocks.create_user(
            username="testuser",
            password_hash="hashed",
        )

        assert result is None


class TestUpdateUserPassword:
    """Tests for update_user_password method."""

    @pytest.mark.asyncio
    async def test_update_user_password_success(
        self, db_service_with_mocks, mock_user_service
    ):
        """update_user_password should delegate to user service."""
        mock_user_service.update_user_password = AsyncMock(return_value=True)

        result = await db_service_with_mocks.update_user_password(
            "testuser", "new_hashed"
        )

        mock_user_service.update_user_password.assert_awaited_once_with(
            "testuser", "new_hashed"
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_update_user_password_failure(
        self, db_service_with_mocks, mock_user_service
    ):
        """update_user_password should return False on failure."""
        mock_user_service.update_user_password = AsyncMock(return_value=False)

        result = await db_service_with_mocks.update_user_password("unknown", "hash")

        assert result is False


class TestHasAdminUser:
    """Tests for has_admin_user method."""

    @pytest.mark.asyncio
    async def test_has_admin_user_true(
        self, db_service_with_mocks, mock_user_service
    ):
        """has_admin_user should return True when admin exists."""
        mock_user_service.has_admin_user = AsyncMock(return_value=True)

        result = await db_service_with_mocks.has_admin_user()

        mock_user_service.has_admin_user.assert_awaited_once()
        assert result is True

    @pytest.mark.asyncio
    async def test_has_admin_user_false(
        self, db_service_with_mocks, mock_user_service
    ):
        """has_admin_user should return False when no admin."""
        mock_user_service.has_admin_user = AsyncMock(return_value=False)

        result = await db_service_with_mocks.has_admin_user()

        assert result is False


class TestUpdateUserPreferences:
    """Tests for update_user_preferences method."""

    @pytest.mark.asyncio
    async def test_update_user_preferences_success(
        self, db_service_with_mocks, mock_user_service
    ):
        """update_user_preferences should delegate to user service."""
        mock_user_service.update_user_preferences = AsyncMock(return_value=True)
        prefs = {"theme": "light", "notifications": True}

        result = await db_service_with_mocks.update_user_preferences("user-123", prefs)

        mock_user_service.update_user_preferences.assert_awaited_once_with(
            "user-123", prefs
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_update_user_preferences_failure(
        self, db_service_with_mocks, mock_user_service
    ):
        """update_user_preferences should return False on failure."""
        mock_user_service.update_user_preferences = AsyncMock(return_value=False)

        result = await db_service_with_mocks.update_user_preferences("user-123", {})

        assert result is False


class TestUpdateUserAvatar:
    """Tests for update_user_avatar method."""

    @pytest.mark.asyncio
    async def test_update_user_avatar_success(
        self, db_service_with_mocks, mock_user_service
    ):
        """update_user_avatar should delegate to user service."""
        mock_user_service.update_user_avatar = AsyncMock(return_value=True)

        result = await db_service_with_mocks.update_user_avatar(
            "user-123", "avatar_url"
        )

        mock_user_service.update_user_avatar.assert_awaited_once_with(
            "user-123", "avatar_url"
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_update_user_avatar_remove(
        self, db_service_with_mocks, mock_user_service
    ):
        """update_user_avatar should handle None avatar."""
        mock_user_service.update_user_avatar = AsyncMock(return_value=True)

        result = await db_service_with_mocks.update_user_avatar("user-123", None)

        mock_user_service.update_user_avatar.assert_awaited_once_with("user-123", None)
        assert result is True

    @pytest.mark.asyncio
    async def test_update_user_avatar_failure(
        self, db_service_with_mocks, mock_user_service
    ):
        """update_user_avatar should return False on failure."""
        mock_user_service.update_user_avatar = AsyncMock(return_value=False)

        result = await db_service_with_mocks.update_user_avatar("unknown", "url")

        assert result is False
