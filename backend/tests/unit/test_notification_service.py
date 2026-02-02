"""
Unit tests for services/notification_service.py

Tests for notification CRUD operations and management.
"""

import json
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import services.notification_service as notification_module
from models.notification import (
    Notification,
    NotificationCountResponse,
    NotificationListResult,
    NotificationType,
)
from services.notification_service import NotificationService


@pytest.fixture
def mock_db_service():
    """Create mock DatabaseService."""
    return MagicMock()


@pytest.fixture
def notification_service(mock_db_service):
    """Create NotificationService with mocked database."""
    with patch.object(notification_module, "logger"):
        return NotificationService(db_service=mock_db_service)


class TestNotificationServiceInit:
    """Tests for NotificationService initialization."""

    def test_init_with_provided_db_service(self, mock_db_service):
        """Should use provided db_service."""
        with patch.object(notification_module, "logger"):
            service = NotificationService(db_service=mock_db_service)

            assert service.db_service is mock_db_service

    def test_init_creates_default_db_service(self):
        """Should create default DatabaseService if not provided."""
        with (
            patch.object(notification_module, "logger"),
            patch.object(
                notification_module, "DatabaseService"
            ) as mock_db_cls,
        ):
            mock_db_cls.return_value = MagicMock()

            service = NotificationService()

            assert service.db_service is mock_db_cls.return_value


class TestCreateNotification:
    """Tests for create_notification method."""

    @pytest.mark.asyncio
    async def test_create_notification_success(
        self, notification_service, mock_db_service
    ):
        """Should create notification successfully."""
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock()
        mock_conn.commit = AsyncMock()

        @asynccontextmanager
        async def mock_get_connection():
            yield mock_conn

        mock_db_service.get_connection = mock_get_connection

        with patch.object(notification_module, "logger"):
            result = await notification_service.create_notification(
                user_id="user-123",
                notification_type=NotificationType.INFO,
                title="Test Notification",
                message="This is a test",
            )

            assert isinstance(result, Notification)
            assert result.user_id == "user-123"
            assert result.type == NotificationType.INFO
            assert result.title == "Test Notification"
            assert result.read is False
            mock_conn.execute.assert_called_once()
            mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_notification_with_metadata(
        self, notification_service, mock_db_service
    ):
        """Should create notification with metadata."""
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock()
        mock_conn.commit = AsyncMock()

        @asynccontextmanager
        async def mock_get_connection():
            yield mock_conn

        mock_db_service.get_connection = mock_get_connection

        metadata = {"key": "value", "count": 42}

        with patch.object(notification_module, "logger"):
            result = await notification_service.create_notification(
                user_id="user-123",
                notification_type=NotificationType.SUCCESS,
                title="Test",
                message="Message",
                metadata=metadata,
            )

            assert result.metadata == metadata

    @pytest.mark.asyncio
    async def test_create_notification_with_expires_at(
        self, notification_service, mock_db_service
    ):
        """Should create notification with expiration."""
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock()
        mock_conn.commit = AsyncMock()

        @asynccontextmanager
        async def mock_get_connection():
            yield mock_conn

        mock_db_service.get_connection = mock_get_connection

        expires = datetime.now(UTC) + timedelta(hours=24)

        with patch.object(notification_module, "logger"):
            result = await notification_service.create_notification(
                user_id="user-123",
                notification_type=NotificationType.WARNING,
                title="Test",
                message="Message",
                expires_at=expires,
            )

            assert result.expires_at == expires

    @pytest.mark.asyncio
    async def test_create_notification_with_source(
        self, notification_service, mock_db_service
    ):
        """Should create notification with source."""
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock()
        mock_conn.commit = AsyncMock()

        @asynccontextmanager
        async def mock_get_connection():
            yield mock_conn

        mock_db_service.get_connection = mock_get_connection

        with patch.object(notification_module, "logger"):
            result = await notification_service.create_notification(
                user_id="user-123",
                notification_type=NotificationType.ERROR,
                title="Test",
                message="Message",
                source="system",
            )

            assert result.source == "system"


class TestGetNotification:
    """Tests for get_notification method."""

    @pytest.mark.asyncio
    async def test_get_notification_found(
        self, notification_service, mock_db_service
    ):
        """Should return notification when found."""
        mock_conn = MagicMock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = {
            "id": "notif-123",
            "user_id": "user-123",
            "type": "info",
            "title": "Test",
            "message": "Message",
            "read": 0,
            "created_at": datetime.now(UTC).isoformat(),
            "read_at": None,
            "dismissed_at": None,
            "expires_at": None,
            "source": None,
            "metadata": None,
        }
        mock_conn.execute = AsyncMock(return_value=mock_cursor)

        @asynccontextmanager
        async def mock_get_connection():
            yield mock_conn

        mock_db_service.get_connection = mock_get_connection

        result = await notification_service.get_notification("notif-123")

        assert result is not None
        assert result.id == "notif-123"
        assert isinstance(result, Notification)

    @pytest.mark.asyncio
    async def test_get_notification_not_found(
        self, notification_service, mock_db_service
    ):
        """Should return None when not found."""
        mock_conn = MagicMock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = None
        mock_conn.execute = AsyncMock(return_value=mock_cursor)

        @asynccontextmanager
        async def mock_get_connection():
            yield mock_conn

        mock_db_service.get_connection = mock_get_connection

        result = await notification_service.get_notification("nonexistent")

        assert result is None


class TestListNotifications:
    """Tests for list_notifications method."""

    @pytest.mark.asyncio
    async def test_list_notifications_basic(
        self, notification_service, mock_db_service
    ):
        """Should list notifications for user."""
        mock_conn = MagicMock()
        mock_cursor = AsyncMock()
        mock_count_cursor = AsyncMock()

        mock_cursor.fetchall.return_value = [
            {
                "id": "notif-1",
                "user_id": "user-123",
                "type": "info",
                "title": "Title 1",
                "message": "Message 1",
                "read": 0,
                "created_at": datetime.now(UTC).isoformat(),
                "read_at": None,
                "source": None,
                "metadata": None,
            },
        ]
        mock_count_cursor.fetchone.return_value = {"total": 1, "unread_count": 1}

        mock_conn.execute = AsyncMock(
            side_effect=[mock_cursor, mock_count_cursor]
        )

        @asynccontextmanager
        async def mock_get_connection():
            yield mock_conn

        mock_db_service.get_connection = mock_get_connection

        with patch.object(
            notification_service, "cleanup_expired_notifications", new_callable=AsyncMock
        ):
            result = await notification_service.list_notifications("user-123")

            assert isinstance(result, NotificationListResult)
            assert len(result.notifications) == 1
            assert result.total == 1
            assert result.unread_count == 1

    @pytest.mark.asyncio
    async def test_list_notifications_with_read_filter(
        self, notification_service, mock_db_service
    ):
        """Should filter by read status."""
        mock_conn = MagicMock()
        mock_cursor = AsyncMock()
        mock_count_cursor = AsyncMock()

        mock_cursor.fetchall.return_value = []
        mock_count_cursor.fetchone.return_value = {"total": 0, "unread_count": 0}

        mock_conn.execute = AsyncMock(
            side_effect=[mock_cursor, mock_count_cursor]
        )

        @asynccontextmanager
        async def mock_get_connection():
            yield mock_conn

        mock_db_service.get_connection = mock_get_connection

        with patch.object(
            notification_service, "cleanup_expired_notifications", new_callable=AsyncMock
        ):
            await notification_service.list_notifications("user-123", read_filter=True)

            # Verify the query includes read filter
            call_args = mock_conn.execute.call_args_list[0]
            assert "AND read = ?" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_list_notifications_with_type_filter(
        self, notification_service, mock_db_service
    ):
        """Should filter by notification type."""
        mock_conn = MagicMock()
        mock_cursor = AsyncMock()
        mock_count_cursor = AsyncMock()

        mock_cursor.fetchall.return_value = []
        mock_count_cursor.fetchone.return_value = {"total": 0, "unread_count": 0}

        mock_conn.execute = AsyncMock(
            side_effect=[mock_cursor, mock_count_cursor]
        )

        @asynccontextmanager
        async def mock_get_connection():
            yield mock_conn

        mock_db_service.get_connection = mock_get_connection

        with patch.object(
            notification_service, "cleanup_expired_notifications", new_callable=AsyncMock
        ):
            await notification_service.list_notifications(
                "user-123", notification_type=NotificationType.ERROR
            )

            # Verify the query includes type filter
            call_args = mock_conn.execute.call_args_list[0]
            assert "AND type = ?" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_list_notifications_with_metadata(
        self, notification_service, mock_db_service
    ):
        """Should parse metadata JSON."""
        mock_conn = MagicMock()
        mock_cursor = AsyncMock()
        mock_count_cursor = AsyncMock()

        mock_cursor.fetchall.return_value = [
            {
                "id": "notif-1",
                "user_id": "user-123",
                "type": "info",
                "title": "Title",
                "message": "Message",
                "read": 0,
                "created_at": datetime.now(UTC).isoformat(),
                "read_at": None,
                "source": None,
                "metadata": json.dumps({"key": "value"}),
            },
        ]
        mock_count_cursor.fetchone.return_value = {"total": 1, "unread_count": 1}

        mock_conn.execute = AsyncMock(
            side_effect=[mock_cursor, mock_count_cursor]
        )

        @asynccontextmanager
        async def mock_get_connection():
            yield mock_conn

        mock_db_service.get_connection = mock_get_connection

        with patch.object(
            notification_service, "cleanup_expired_notifications", new_callable=AsyncMock
        ):
            result = await notification_service.list_notifications("user-123")

            assert result.notifications[0].metadata == {"key": "value"}


class TestMarkAsRead:
    """Tests for mark_as_read method."""

    @pytest.mark.asyncio
    async def test_mark_as_read_success(
        self, notification_service, mock_db_service
    ):
        """Should mark notification as read."""
        mock_conn = AsyncMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        mock_conn.execute.return_value = mock_cursor
        mock_conn.commit = AsyncMock()

        @asynccontextmanager
        async def mock_get_connection():
            yield mock_conn

        mock_db_service.get_connection = mock_get_connection

        with patch.object(notification_module, "logger"):
            result = await notification_service.mark_as_read("notif-123", "user-123")

            assert result is True
            mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_mark_as_read_not_found(
        self, notification_service, mock_db_service
    ):
        """Should return False when notification not found."""
        mock_conn = AsyncMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 0
        mock_conn.execute.return_value = mock_cursor
        mock_conn.commit = AsyncMock()

        @asynccontextmanager
        async def mock_get_connection():
            yield mock_conn

        mock_db_service.get_connection = mock_get_connection

        result = await notification_service.mark_as_read("nonexistent", "user-123")

        assert result is False


class TestMarkAllAsRead:
    """Tests for mark_all_as_read method."""

    @pytest.mark.asyncio
    async def test_mark_all_as_read_success(
        self, notification_service, mock_db_service
    ):
        """Should mark all notifications as read."""
        mock_conn = AsyncMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 5
        mock_conn.execute.return_value = mock_cursor
        mock_conn.commit = AsyncMock()

        @asynccontextmanager
        async def mock_get_connection():
            yield mock_conn

        mock_db_service.get_connection = mock_get_connection

        with patch.object(notification_module, "logger"):
            result = await notification_service.mark_all_as_read("user-123")

            assert result == 5
            mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_mark_all_as_read_none(
        self, notification_service, mock_db_service
    ):
        """Should return 0 when no unread notifications."""
        mock_conn = AsyncMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 0
        mock_conn.execute.return_value = mock_cursor
        mock_conn.commit = AsyncMock()

        @asynccontextmanager
        async def mock_get_connection():
            yield mock_conn

        mock_db_service.get_connection = mock_get_connection

        with patch.object(notification_module, "logger"):
            result = await notification_service.mark_all_as_read("user-123")

            assert result == 0


class TestDismissNotification:
    """Tests for dismiss_notification method."""

    @pytest.mark.asyncio
    async def test_dismiss_notification_success(
        self, notification_service, mock_db_service
    ):
        """Should dismiss notification."""
        mock_conn = AsyncMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        mock_conn.execute.return_value = mock_cursor
        mock_conn.commit = AsyncMock()

        @asynccontextmanager
        async def mock_get_connection():
            yield mock_conn

        mock_db_service.get_connection = mock_get_connection

        with patch.object(notification_module, "logger"):
            result = await notification_service.dismiss_notification(
                "notif-123", "user-123"
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_dismiss_notification_not_found(
        self, notification_service, mock_db_service
    ):
        """Should return False when not found."""
        mock_conn = AsyncMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 0
        mock_conn.execute.return_value = mock_cursor
        mock_conn.commit = AsyncMock()

        @asynccontextmanager
        async def mock_get_connection():
            yield mock_conn

        mock_db_service.get_connection = mock_get_connection

        result = await notification_service.dismiss_notification(
            "nonexistent", "user-123"
        )

        assert result is False


class TestDismissAll:
    """Tests for dismiss_all method."""

    @pytest.mark.asyncio
    async def test_dismiss_all_success(
        self, notification_service, mock_db_service
    ):
        """Should dismiss all notifications."""
        mock_conn = AsyncMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 10
        mock_conn.execute.return_value = mock_cursor
        mock_conn.commit = AsyncMock()

        @asynccontextmanager
        async def mock_get_connection():
            yield mock_conn

        mock_db_service.get_connection = mock_get_connection

        with patch.object(notification_module, "logger"):
            result = await notification_service.dismiss_all("user-123")

            assert result == 10


class TestGetUnreadCount:
    """Tests for get_unread_count method."""

    @pytest.mark.asyncio
    async def test_get_unread_count(
        self, notification_service, mock_db_service
    ):
        """Should return unread count."""
        mock_conn = MagicMock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = {"total": 15, "unread_count": 7}
        mock_conn.execute = AsyncMock(return_value=mock_cursor)

        @asynccontextmanager
        async def mock_get_connection():
            yield mock_conn

        mock_db_service.get_connection = mock_get_connection

        result = await notification_service.get_unread_count("user-123")

        assert isinstance(result, NotificationCountResponse)
        assert result.total == 15
        assert result.unread_count == 7

    @pytest.mark.asyncio
    async def test_get_unread_count_empty(
        self, notification_service, mock_db_service
    ):
        """Should handle empty results."""
        mock_conn = MagicMock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = {"total": None, "unread_count": None}
        mock_conn.execute = AsyncMock(return_value=mock_cursor)

        @asynccontextmanager
        async def mock_get_connection():
            yield mock_conn

        mock_db_service.get_connection = mock_get_connection

        result = await notification_service.get_unread_count("user-123")

        assert result.total == 0
        assert result.unread_count == 0


class TestCleanupExpiredNotifications:
    """Tests for cleanup_expired_notifications method."""

    @pytest.mark.asyncio
    async def test_cleanup_expired_all_users(
        self, notification_service, mock_db_service
    ):
        """Should cleanup expired notifications for all users."""
        mock_conn = AsyncMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 3
        mock_conn.execute.return_value = mock_cursor
        mock_conn.commit = AsyncMock()

        @asynccontextmanager
        async def mock_get_connection():
            yield mock_conn

        mock_db_service.get_connection = mock_get_connection

        with patch.object(notification_module, "logger"):
            result = await notification_service.cleanup_expired_notifications()

            assert result == 3
            # Query should not have user_id filter
            call_args = mock_conn.execute.call_args[0]
            assert "user_id" not in call_args[0]

    @pytest.mark.asyncio
    async def test_cleanup_expired_specific_user(
        self, notification_service, mock_db_service
    ):
        """Should cleanup for specific user."""
        mock_conn = AsyncMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 2
        mock_conn.execute.return_value = mock_cursor
        mock_conn.commit = AsyncMock()

        @asynccontextmanager
        async def mock_get_connection():
            yield mock_conn

        mock_db_service.get_connection = mock_get_connection

        with patch.object(notification_module, "logger"):
            result = await notification_service.cleanup_expired_notifications(
                user_id="user-123"
            )

            assert result == 2
            # Query should have user_id filter
            call_args = mock_conn.execute.call_args[0]
            assert "user_id" in call_args[0]

    @pytest.mark.asyncio
    async def test_cleanup_expired_none(
        self, notification_service, mock_db_service
    ):
        """Should return 0 when no expired notifications."""
        mock_conn = AsyncMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 0
        mock_conn.execute.return_value = mock_cursor
        mock_conn.commit = AsyncMock()

        @asynccontextmanager
        async def mock_get_connection():
            yield mock_conn

        mock_db_service.get_connection = mock_get_connection

        result = await notification_service.cleanup_expired_notifications()

        assert result == 0


class TestDeleteOldNotifications:
    """Tests for delete_old_notifications method."""

    @pytest.mark.asyncio
    async def test_delete_old_notifications_success(
        self, notification_service, mock_db_service
    ):
        """Should delete old dismissed notifications."""
        mock_conn = AsyncMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 5
        mock_conn.execute.return_value = mock_cursor
        mock_conn.commit = AsyncMock()

        @asynccontextmanager
        async def mock_get_connection():
            yield mock_conn

        mock_db_service.get_connection = mock_get_connection

        with patch.object(notification_module, "logger"):
            result = await notification_service.delete_old_notifications(days=30)

            assert result == 5
            mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_old_notifications_custom_days(
        self, notification_service, mock_db_service
    ):
        """Should use custom days parameter."""
        mock_conn = AsyncMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 0
        mock_conn.execute.return_value = mock_cursor
        mock_conn.commit = AsyncMock()

        @asynccontextmanager
        async def mock_get_connection():
            yield mock_conn

        mock_db_service.get_connection = mock_get_connection

        await notification_service.delete_old_notifications(days=7)

        call_args = mock_conn.execute.call_args[0]
        assert "-7 days" in call_args[1][0]


class TestDictFactory:
    """Tests for _dict_factory method."""

    def test_dict_factory(self, notification_service):
        """Should convert row to dictionary."""
        mock_cursor = MagicMock()
        mock_cursor.description = [("id",), ("name",), ("value",)]
        row = ("123", "test", 42)

        result = notification_service._dict_factory(mock_cursor, row)

        assert result == {"id": "123", "name": "test", "value": 42}


class TestRowToNotification:
    """Tests for _row_to_notification method."""

    def test_row_to_notification_full(self, notification_service):
        """Should convert row with all fields."""
        now = datetime.now(UTC)
        row = {
            "id": "notif-123",
            "user_id": "user-123",
            "type": "warning",
            "title": "Test Title",
            "message": "Test Message",
            "read": 1,
            "created_at": now.isoformat(),
            "read_at": now.isoformat(),
            "dismissed_at": now.isoformat(),
            "expires_at": now.isoformat(),
            "source": "system",
            "metadata": json.dumps({"key": "value"}),
        }

        result = notification_service._row_to_notification(row)

        assert result.id == "notif-123"
        assert result.type == NotificationType.WARNING
        assert result.read is True
        assert result.read_at is not None
        assert result.dismissed_at is not None
        assert result.expires_at is not None
        assert result.metadata == {"key": "value"}

    def test_row_to_notification_minimal(self, notification_service):
        """Should convert row with minimal fields."""
        now = datetime.now(UTC)
        row = {
            "id": "notif-123",
            "user_id": "user-123",
            "type": "info",
            "title": "Test",
            "message": "Msg",
            "read": 0,
            "created_at": now.isoformat(),
            "read_at": None,
            "dismissed_at": None,
            "expires_at": None,
            "source": None,
            "metadata": None,
        }

        result = notification_service._row_to_notification(row)

        assert result.read is False
        assert result.read_at is None
        assert result.dismissed_at is None
        assert result.expires_at is None
        assert result.metadata is None
