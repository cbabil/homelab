"""
Unit tests for services/database/user_service.py - Core operations.

Tests get_user, get_user_by_username, get_user_by_id, get_user_password_hash,
update_user_last_login, and get_all_users.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from contextlib import asynccontextmanager

from services.database.user_service import UserDatabaseService
from models.auth import User, UserRole


@pytest.fixture
def mock_connection():
    """Create mock DatabaseConnection."""
    return MagicMock()


@pytest.fixture
def user_service(mock_connection):
    """Create UserDatabaseService instance."""
    return UserDatabaseService(mock_connection)


def create_mock_context(mock_conn):
    """Create async context manager for database connection."""

    @asynccontextmanager
    async def context():
        yield mock_conn

    return context()


def create_user_row(
    user_id="user-123",
    username="testuser",
    email="test@example.com",
    role="user",
    created_at="2024-01-01T00:00:00Z",
    last_login="2024-01-02T00:00:00Z",
    password_changed_at="2024-01-01T00:00:00Z",
    is_active=1,
    preferences_json=None,
    avatar=None,
):
    """Create a mock user row dict."""
    return {
        "id": user_id,
        "username": username,
        "email": email,
        "role": role,
        "created_at": created_at,
        "last_login": last_login,
        "password_changed_at": password_changed_at,
        "is_active": is_active,
        "preferences_json": preferences_json,
        "avatar": avatar,
    }


class TestUserDatabaseServiceInit:
    """Tests for UserDatabaseService initialization."""

    def test_init_stores_connection(self, mock_connection):
        """UserDatabaseService should store connection reference."""
        service = UserDatabaseService(mock_connection)
        assert service._conn is mock_connection


class TestGetUser:
    """Tests for get_user method."""

    @pytest.mark.asyncio
    async def test_get_user_by_id_success(self, user_service, mock_connection):
        """get_user should return User when found by ID."""
        mock_row = create_user_row()
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = mock_row

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.user_service.logger"):
            result = await user_service.get_user(user_id="user-123")

        assert result is not None
        assert result.id == "user-123"
        assert result.username == "testuser"
        assert result.email == "test@example.com"
        assert result.role == UserRole.USER

    @pytest.mark.asyncio
    async def test_get_user_by_username_success(self, user_service, mock_connection):
        """get_user should return User when found by username."""
        mock_row = create_user_row(username="admin", role="admin")
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = mock_row

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.user_service.logger"):
            result = await user_service.get_user(username="admin")

        assert result is not None
        assert result.username == "admin"
        assert result.role == UserRole.ADMIN

    @pytest.mark.asyncio
    async def test_get_user_not_found(self, user_service, mock_connection):
        """get_user should return None when user not found."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = None

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.user_service.logger"):
            result = await user_service.get_user(user_id="nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_user_no_params_raises_value_error(self, user_service):
        """get_user should raise ValueError when no params provided."""
        with pytest.raises(ValueError, match="Either user_id or username"):
            await user_service.get_user()

    @pytest.mark.asyncio
    async def test_get_user_with_preferences(self, user_service, mock_connection):
        """get_user should parse preferences JSON."""
        prefs = {"theme": "dark", "notifications": True}
        mock_row = create_user_row(preferences_json=json.dumps(prefs))
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = mock_row

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.user_service.logger"):
            result = await user_service.get_user(user_id="user-123")

        assert result is not None
        assert result.preferences == prefs

    @pytest.mark.asyncio
    async def test_get_user_with_invalid_preferences_json(
        self, user_service, mock_connection
    ):
        """get_user should handle invalid preferences JSON."""
        mock_row = create_user_row(preferences_json="invalid-json")
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = mock_row

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.user_service.logger"):
            result = await user_service.get_user(user_id="user-123")

        assert result is not None
        assert result.preferences == {}

    @pytest.mark.asyncio
    async def test_get_user_with_avatar(self, user_service, mock_connection):
        """get_user should include avatar data."""
        avatar_data = "data:image/png;base64,abc123"
        mock_row = create_user_row(avatar=avatar_data)
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = mock_row

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.user_service.logger"):
            result = await user_service.get_user(user_id="user-123")

        assert result is not None
        assert result.avatar == avatar_data

    @pytest.mark.asyncio
    async def test_get_user_null_last_login_uses_current_time(
        self, user_service, mock_connection
    ):
        """get_user should use current time when last_login is null."""
        mock_row = create_user_row(last_login=None)
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = mock_row

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.user_service.logger"):
            result = await user_service.get_user(user_id="user-123")

        assert result is not None
        assert result.last_login is not None

    @pytest.mark.asyncio
    async def test_get_user_database_error_returns_none(
        self, user_service, mock_connection
    ):
        """get_user should return None on database error."""
        mock_conn = AsyncMock()
        mock_conn.execute.side_effect = Exception("DB connection failed")

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.user_service.logger"):
            result = await user_service.get_user(user_id="user-123")

        assert result is None


class TestGetUserByUsername:
    """Tests for get_user_by_username wrapper method."""

    @pytest.mark.asyncio
    async def test_get_user_by_username_delegates(self, user_service, mock_connection):
        """get_user_by_username should delegate to get_user."""
        mock_row = create_user_row()
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = mock_row

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.user_service.logger"):
            result = await user_service.get_user_by_username("testuser")

        assert result is not None
        assert result.username == "testuser"


class TestGetUserById:
    """Tests for get_user_by_id wrapper method."""

    @pytest.mark.asyncio
    async def test_get_user_by_id_delegates(self, user_service, mock_connection):
        """get_user_by_id should delegate to get_user."""
        mock_row = create_user_row()
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = mock_row

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.user_service.logger"):
            result = await user_service.get_user_by_id("user-123")

        assert result is not None
        assert result.id == "user-123"


class TestGetUserPasswordHash:
    """Tests for get_user_password_hash method."""

    @pytest.mark.asyncio
    async def test_get_password_hash_success(self, user_service, mock_connection):
        """get_user_password_hash should return hash when found."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = {"password_hash": "hashed_password_123"}

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.user_service.logger"):
            result = await user_service.get_user_password_hash("testuser")

        assert result == "hashed_password_123"

    @pytest.mark.asyncio
    async def test_get_password_hash_not_found(self, user_service, mock_connection):
        """get_user_password_hash should return None when user not found."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = None

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.user_service.logger"):
            result = await user_service.get_user_password_hash("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_password_hash_error_returns_none(
        self, user_service, mock_connection
    ):
        """get_user_password_hash should return None on error."""
        mock_conn = AsyncMock()
        mock_conn.execute.side_effect = Exception("DB error")

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.user_service.logger"):
            result = await user_service.get_user_password_hash("testuser")

        assert result is None


class TestUpdateUserLastLogin:
    """Tests for update_user_last_login method."""

    @pytest.mark.asyncio
    async def test_update_last_login_success(self, user_service, mock_connection):
        """update_user_last_login should return True on success."""
        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.user_service.logger"):
            result = await user_service.update_user_last_login(
                "testuser", "2024-01-15T12:00:00Z"
            )

        assert result is True
        mock_conn.execute.assert_called_once()
        mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_last_login_uses_current_time(
        self, user_service, mock_connection
    ):
        """update_user_last_login should use current time when not provided."""
        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.user_service.logger"):
            result = await user_service.update_user_last_login("testuser")

        assert result is True
        call_args = mock_conn.execute.call_args[0]
        assert call_args[1][1] == "testuser"
        # Timestamp should be ISO format
        assert "T" in call_args[1][0]

    @pytest.mark.asyncio
    async def test_update_last_login_error_returns_false(
        self, user_service, mock_connection
    ):
        """update_user_last_login should return False on error."""
        mock_conn = AsyncMock()
        mock_conn.execute.side_effect = Exception("DB error")

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.user_service.logger"):
            result = await user_service.update_user_last_login("testuser")

        assert result is False


class TestGetAllUsers:
    """Tests for get_all_users method."""

    @pytest.mark.asyncio
    async def test_get_all_users_success(self, user_service, mock_connection):
        """get_all_users should return list of User objects."""
        mock_rows = [
            {
                "id": "u1",
                "username": "admin",
                "email": "admin@test.com",
                "role": "admin",
                "created_at": "2024-01-01",
                "last_login": "2024-01-02",
                "is_active": 1,
                "preferences_json": None,
            },
            {
                "id": "u2",
                "username": "user",
                "email": "user@test.com",
                "role": "user",
                "created_at": "2024-01-01",
                "last_login": "2024-01-02",
                "is_active": 1,
                "preferences_json": '{"theme": "dark"}',
            },
        ]
        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = mock_rows

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.user_service.logger"):
            result = await user_service.get_all_users()

        assert len(result) == 2
        assert isinstance(result[0], User)
        assert result[0].username == "admin"
        assert result[0].role == UserRole.ADMIN
        assert result[1].preferences == {"theme": "dark"}

    @pytest.mark.asyncio
    async def test_get_all_users_empty(self, user_service, mock_connection):
        """get_all_users should return empty list when no users."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = []

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.user_service.logger"):
            result = await user_service.get_all_users()

        assert result == []

    @pytest.mark.asyncio
    async def test_get_all_users_with_invalid_preferences(
        self, user_service, mock_connection
    ):
        """get_all_users should handle invalid preferences JSON gracefully."""
        mock_rows = [
            {
                "id": "u1",
                "username": "user",
                "email": "user@test.com",
                "role": "user",
                "created_at": "2024-01-01",
                "last_login": "2024-01-02",
                "is_active": 1,
                "preferences_json": "not-valid-json",
            }
        ]
        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = mock_rows

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.user_service.logger"):
            result = await user_service.get_all_users()

        assert len(result) == 1
        assert result[0].preferences == {}

    @pytest.mark.asyncio
    async def test_get_all_users_null_last_login(self, user_service, mock_connection):
        """get_all_users should handle null last_login."""
        mock_rows = [
            {
                "id": "u1",
                "username": "user",
                "email": "user@test.com",
                "role": "user",
                "created_at": "2024-01-01",
                "last_login": None,
                "is_active": 1,
                "preferences_json": None,
            }
        ]
        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = mock_rows

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.user_service.logger"):
            result = await user_service.get_all_users()

        assert len(result) == 1
        assert result[0].last_login is not None

    @pytest.mark.asyncio
    async def test_get_all_users_error_returns_empty(
        self, user_service, mock_connection
    ):
        """get_all_users should return empty list on error."""
        mock_conn = AsyncMock()
        mock_conn.execute.side_effect = Exception("DB error")

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.user_service.logger"):
            result = await user_service.get_all_users()

        assert result == []
