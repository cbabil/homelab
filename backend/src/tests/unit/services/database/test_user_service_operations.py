"""
Unit tests for services/database/user_service.py - User operations.

Tests create_user, update_user_password, has_admin_user,
update_user_preferences, and update_user_avatar.
"""

import json
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.auth import UserRole
from services.database.user_service import UserDatabaseService


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


class TestCreateUser:
    """Tests for create_user method."""

    @pytest.mark.asyncio
    async def test_create_user_success(self, user_service, mock_connection):
        """create_user should return User on success."""
        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.user_service.logger"):
            with patch("services.database.user_service.uuid.uuid4") as mock_uuid:
                mock_uuid.return_value = MagicMock(
                    __str__=lambda _: "generated-uuid-123"
                )
                result = await user_service.create_user(
                    username="newuser",
                    password_hash="hashed_password",
                    email="new@test.com",
                    role=UserRole.USER,
                )

        assert result is not None
        assert result.username == "newuser"
        assert result.email == "new@test.com"
        assert result.role == UserRole.USER
        assert result.is_active is True
        mock_conn.execute.assert_called_once()
        mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_user_admin_role(self, user_service, mock_connection):
        """create_user should accept admin role."""
        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.user_service.logger"):
            result = await user_service.create_user(
                username="adminuser",
                password_hash="hashed_password",
                role=UserRole.ADMIN,
            )

        assert result is not None
        assert result.role == UserRole.ADMIN

    @pytest.mark.asyncio
    async def test_create_user_with_preferences(self, user_service, mock_connection):
        """create_user should store preferences."""
        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        prefs = {"theme": "dark", "language": "en"}

        with patch("services.database.user_service.logger"):
            result = await user_service.create_user(
                username="newuser",
                password_hash="hashed_password",
                preferences=prefs,
            )

        assert result is not None
        assert result.preferences == prefs

    @pytest.mark.asyncio
    async def test_create_user_empty_email(self, user_service, mock_connection):
        """create_user should accept empty email."""
        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.user_service.logger"):
            result = await user_service.create_user(
                username="newuser",
                password_hash="hashed_password",
            )

        assert result is not None
        assert result.email == ""

    @pytest.mark.asyncio
    async def test_create_user_error_returns_none(self, user_service, mock_connection):
        """create_user should return None on error."""
        mock_conn = AsyncMock()
        mock_conn.execute.side_effect = Exception("Duplicate username")

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.user_service.logger"):
            result = await user_service.create_user(
                username="newuser",
                password_hash="hashed_password",
            )

        assert result is None

    @pytest.mark.asyncio
    async def test_create_user_sets_timestamps(self, user_service, mock_connection):
        """create_user should set created_at and password_changed_at."""
        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.user_service.logger"):
            result = await user_service.create_user(
                username="newuser",
                password_hash="hashed_password",
            )

        assert result is not None
        assert result.password_changed_at is not None
        # Verify the SQL contains the timestamps
        call_args = mock_conn.execute.call_args[0]
        params = call_args[1]
        # Verify ISO timestamp format for created_at and password_changed_at
        assert "T" in params[5]  # created_at
        assert "T" in params[6]  # password_changed_at


class TestUpdateUserPassword:
    """Tests for update_user_password method."""

    @pytest.mark.asyncio
    async def test_update_password_success(self, user_service, mock_connection):
        """update_user_password should return True on success."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 1

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.user_service.logger"):
            result = await user_service.update_user_password(
                "testuser", "new_hashed_password"
            )

        assert result is True
        mock_conn.execute.assert_called_once()
        mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_password_user_not_found(self, user_service, mock_connection):
        """update_user_password should return False when user not found."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 0

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.user_service.logger"):
            result = await user_service.update_user_password(
                "nonexistent", "new_hashed_password"
            )

        assert result is False

    @pytest.mark.asyncio
    async def test_update_password_error_returns_false(
        self, user_service, mock_connection
    ):
        """update_user_password should return False on error."""
        mock_conn = AsyncMock()
        mock_conn.execute.side_effect = Exception("DB error")

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.user_service.logger"):
            result = await user_service.update_user_password(
                "testuser", "new_hashed_password"
            )

        assert result is False

    @pytest.mark.asyncio
    async def test_update_password_updates_timestamp(
        self, user_service, mock_connection
    ):
        """update_user_password should update password_changed_at."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 1

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.user_service.logger"):
            await user_service.update_user_password("testuser", "new_hash")

        call_args = mock_conn.execute.call_args[0]
        params = call_args[1]
        # Second param should be password_changed_at timestamp
        assert "T" in params[1]


class TestHasAdminUser:
    """Tests for has_admin_user method."""

    @pytest.mark.asyncio
    async def test_has_admin_user_true(self, user_service, mock_connection):
        """has_admin_user should return True when admin exists."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = {"count": 1}

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.user_service.logger"):
            result = await user_service.has_admin_user()

        assert result is True

    @pytest.mark.asyncio
    async def test_has_admin_user_false(self, user_service, mock_connection):
        """has_admin_user should return False when no admin exists."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = {"count": 0}

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.user_service.logger"):
            result = await user_service.has_admin_user()

        assert result is False

    @pytest.mark.asyncio
    async def test_has_admin_user_multiple_admins(self, user_service, mock_connection):
        """has_admin_user should return True when multiple admins exist."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = {"count": 3}

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.user_service.logger"):
            result = await user_service.has_admin_user()

        assert result is True

    @pytest.mark.asyncio
    async def test_has_admin_user_null_row(self, user_service, mock_connection):
        """has_admin_user should return False when row is None."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = None

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.user_service.logger"):
            result = await user_service.has_admin_user()

        assert result is False

    @pytest.mark.asyncio
    async def test_has_admin_user_error_returns_false(
        self, user_service, mock_connection
    ):
        """has_admin_user should return False on error."""
        mock_conn = AsyncMock()
        mock_conn.execute.side_effect = Exception("DB error")

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.user_service.logger"):
            result = await user_service.has_admin_user()

        assert result is False

    @pytest.mark.asyncio
    async def test_has_admin_user_queries_admin_role(
        self, user_service, mock_connection
    ):
        """has_admin_user should query for admin role specifically."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = {"count": 1}

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.user_service.logger"):
            await user_service.has_admin_user()

        call_args = mock_conn.execute.call_args[0]
        assert "role = ?" in call_args[0]
        assert call_args[1] == ("admin",)


class TestUpdateUserPreferences:
    """Tests for update_user_preferences method."""

    @pytest.mark.asyncio
    async def test_update_preferences_success(self, user_service, mock_connection):
        """update_user_preferences should return True on success."""
        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        prefs = {"theme": "dark", "notifications": True}

        with patch("services.database.user_service.logger"):
            result = await user_service.update_user_preferences("user-123", prefs)

        assert result is True
        mock_conn.execute.assert_called_once()
        mock_conn.commit.assert_called_once()

        # Verify preferences are JSON encoded
        call_args = mock_conn.execute.call_args[0]
        assert json.loads(call_args[1][0]) == prefs

    @pytest.mark.asyncio
    async def test_update_preferences_empty_dict(self, user_service, mock_connection):
        """update_user_preferences should accept empty dict."""
        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.user_service.logger"):
            result = await user_service.update_user_preferences("user-123", {})

        assert result is True

    @pytest.mark.asyncio
    async def test_update_preferences_error_returns_false(
        self, user_service, mock_connection
    ):
        """update_user_preferences should return False on error."""
        mock_conn = AsyncMock()
        mock_conn.execute.side_effect = Exception("DB error")

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.user_service.logger"):
            result = await user_service.update_user_preferences(
                "user-123", {"key": "value"}
            )

        assert result is False

    @pytest.mark.asyncio
    async def test_update_preferences_complex_object(
        self, user_service, mock_connection
    ):
        """update_user_preferences should handle complex nested objects."""
        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        prefs = {
            "theme": "dark",
            "notifications": {"email": True, "push": False},
            "dashboard": {"widgets": ["cpu", "memory", "disk"]},
        }

        with patch("services.database.user_service.logger"):
            result = await user_service.update_user_preferences("user-123", prefs)

        assert result is True
        call_args = mock_conn.execute.call_args[0]
        stored_prefs = json.loads(call_args[1][0])
        assert stored_prefs == prefs


class TestUpdateUserAvatar:
    """Tests for update_user_avatar method."""

    @pytest.mark.asyncio
    async def test_update_avatar_success(self, user_service, mock_connection):
        """update_user_avatar should return True on success."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 1

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        avatar_data = "data:image/png;base64,abc123"

        with patch("services.database.user_service.logger"):
            result = await user_service.update_user_avatar("user-123", avatar_data)

        assert result is True
        mock_conn.execute.assert_called_once()
        mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_avatar_remove(self, user_service, mock_connection):
        """update_user_avatar should accept None to remove avatar."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 1

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.user_service.logger"):
            result = await user_service.update_user_avatar("user-123", None)

        assert result is True
        call_args = mock_conn.execute.call_args[0]
        assert call_args[1][0] is None

    @pytest.mark.asyncio
    async def test_update_avatar_user_not_found(self, user_service, mock_connection):
        """update_user_avatar should return False when user not found."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 0

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.user_service.logger"):
            result = await user_service.update_user_avatar(
                "nonexistent", "data:image/png;base64,abc"
            )

        assert result is False

    @pytest.mark.asyncio
    async def test_update_avatar_error_returns_false(
        self, user_service, mock_connection
    ):
        """update_user_avatar should return False on error."""
        mock_conn = AsyncMock()
        mock_conn.execute.side_effect = Exception("DB error")

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.user_service.logger"):
            result = await user_service.update_user_avatar(
                "user-123", "data:image/png;base64,abc"
            )

        assert result is False

    @pytest.mark.asyncio
    async def test_update_avatar_large_data(self, user_service, mock_connection):
        """update_user_avatar should handle large base64 data."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 1

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        # Simulate a larger avatar (base64 encoded image)
        large_avatar = "data:image/png;base64," + "A" * 10000

        with patch("services.database.user_service.logger"):
            result = await user_service.update_user_avatar("user-123", large_avatar)

        assert result is True
        call_args = mock_conn.execute.call_args[0]
        assert call_args[1][0] == large_avatar

    @pytest.mark.asyncio
    async def test_update_avatar_jpeg_format(self, user_service, mock_connection):
        """update_user_avatar should handle JPEG data URLs."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 1

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        jpeg_avatar = "data:image/jpeg;base64,/9j/4AAQSkZJRg=="

        with patch("services.database.user_service.logger"):
            result = await user_service.update_user_avatar("user-123", jpeg_avatar)

        assert result is True
        call_args = mock_conn.execute.call_args[0]
        assert call_args[1][0] == jpeg_avatar
