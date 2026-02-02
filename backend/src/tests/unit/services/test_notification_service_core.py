"""
Unit tests for services/notification_service.py - Core operations.

Tests initialization, create, get, and list notifications.
"""

import json
import pytest
from datetime import datetime, timedelta, UTC
from unittest.mock import AsyncMock, MagicMock, patch

from services.notification_service import NotificationService
from models.notification import (
    NotificationType,
    NotificationListResult,
)


@pytest.fixture
def mock_db_service():
    """Create mock database service."""
    return MagicMock()


@pytest.fixture
def mock_connection():
    """Create mock database connection."""
    conn = AsyncMock()
    conn.row_factory = None
    conn.execute = AsyncMock()
    conn.commit = AsyncMock()
    return conn


@pytest.fixture
def notification_service(mock_db_service, mock_connection):
    """Create NotificationService with mocked dependencies."""
    mock_db_service.get_connection = MagicMock()
    mock_db_service.get_connection.return_value.__aenter__ = AsyncMock(
        return_value=mock_connection
    )
    mock_db_service.get_connection.return_value.__aexit__ = AsyncMock()

    with patch("services.notification_service.logger"):
        return NotificationService(mock_db_service)


class TestNotificationServiceInit:
    """Tests for NotificationService initialization."""

    def test_init_stores_db_service(self, mock_db_service):
        """NotificationService should store db_service reference."""
        with patch("services.notification_service.logger"):
            service = NotificationService(mock_db_service)
            assert service.db_service is mock_db_service

    def test_init_creates_default_db_service(self):
        """NotificationService should create default db_service if not provided."""
        with patch("services.notification_service.logger"), \
             patch("services.notification_service.DatabaseService") as MockDB:
            MockDB.return_value = MagicMock()
            service = NotificationService()
            assert service.db_service is MockDB.return_value

    def test_init_logs_message(self, mock_db_service):
        """NotificationService should log initialization."""
        with patch("services.notification_service.logger") as mock_logger:
            NotificationService(mock_db_service)
            mock_logger.info.assert_called_with("Notification service initialized")


class TestCreateNotification:
    """Tests for create_notification method."""

    @pytest.mark.asyncio
    async def test_create_notification_success(
        self, notification_service, mock_connection
    ):
        """create_notification should create notification in database."""
        with patch("services.notification_service.logger"):
            result = await notification_service.create_notification(
                user_id="user-123",
                notification_type=NotificationType.INFO,
                title="Test Title",
                message="Test Message",
            )

        assert result.user_id == "user-123"
        assert result.type == NotificationType.INFO
        assert result.title == "Test Title"
        assert result.message == "Test Message"
        assert result.read is False
        assert result.id.startswith("notif_")
        mock_connection.execute.assert_called_once()
        mock_connection.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_notification_with_metadata(
        self, notification_service, mock_connection
    ):
        """create_notification should handle metadata."""
        metadata = {"key": "value", "count": 42}

        with patch("services.notification_service.logger"):
            result = await notification_service.create_notification(
                user_id="user-123",
                notification_type=NotificationType.SUCCESS,
                title="Test",
                message="Message",
                metadata=metadata,
            )

        assert result.metadata == metadata
        call_args = mock_connection.execute.call_args[0][1]
        assert json.dumps(metadata) == call_args[8]

    @pytest.mark.asyncio
    async def test_create_notification_with_source(
        self, notification_service, mock_connection
    ):
        """create_notification should handle source."""
        with patch("services.notification_service.logger"):
            result = await notification_service.create_notification(
                user_id="user-123",
                notification_type=NotificationType.WARNING,
                title="Alert",
                message="Warning message",
                source="server",
            )

        assert result.source == "server"

    @pytest.mark.asyncio
    async def test_create_notification_with_expires_at(
        self, notification_service, mock_connection
    ):
        """create_notification should handle expiration."""
        expires = datetime.now(UTC) + timedelta(hours=24)

        with patch("services.notification_service.logger"):
            result = await notification_service.create_notification(
                user_id="user-123",
                notification_type=NotificationType.ERROR,
                title="Expiring",
                message="Expires soon",
                expires_at=expires,
            )

        assert result.expires_at == expires

    @pytest.mark.asyncio
    async def test_create_notification_logs_success(
        self, notification_service, mock_connection
    ):
        """create_notification should log creation."""
        with patch("services.notification_service.logger") as mock_logger:
            await notification_service.create_notification(
                user_id="user-123",
                notification_type=NotificationType.INFO,
                title="Test",
                message="Test",
            )

            mock_logger.info.assert_called()
            call_args = mock_logger.info.call_args
            assert call_args[0][0] == "Notification created"
            assert call_args[1]["user_id"] == "user-123"


class TestGetNotification:
    """Tests for get_notification method."""

    @pytest.mark.asyncio
    async def test_get_notification_found(
        self, notification_service, mock_connection
    ):
        """get_notification should return notification when found."""
        row = {
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
            "source": "system",
            "metadata": None,
        }
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=row)
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        with patch("services.notification_service.logger"):
            result = await notification_service.get_notification("notif-123")

        assert result is not None
        assert result.id == "notif-123"
        assert result.type == NotificationType.INFO

    @pytest.mark.asyncio
    async def test_get_notification_not_found(
        self, notification_service, mock_connection
    ):
        """get_notification should return None when not found."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=None)
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        with patch("services.notification_service.logger"):
            result = await notification_service.get_notification("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_notification_with_metadata(
        self, notification_service, mock_connection
    ):
        """get_notification should parse metadata JSON."""
        row = {
            "id": "notif-123",
            "user_id": "user-123",
            "type": "success",
            "title": "Test",
            "message": "Message",
            "read": 1,
            "created_at": datetime.now(UTC).isoformat(),
            "read_at": datetime.now(UTC).isoformat(),
            "dismissed_at": None,
            "expires_at": None,
            "source": None,
            "metadata": '{"key": "value"}',
        }
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=row)
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        with patch("services.notification_service.logger"):
            result = await notification_service.get_notification("notif-123")

        assert result.metadata == {"key": "value"}
        assert result.read is True


class TestListNotifications:
    """Tests for list_notifications method."""

    @pytest.mark.asyncio
    async def test_list_notifications_success(
        self, notification_service, mock_connection
    ):
        """list_notifications should return list with counts."""
        rows = [
            {
                "id": "notif-1",
                "user_id": "user-123",
                "type": "info",
                "title": "Test 1",
                "message": "Message 1",
                "read": 0,
                "created_at": datetime.now(UTC).isoformat(),
                "read_at": None,
                "source": None,
                "metadata": None,
            }
        ]
        count_row = {"total": 1, "unread_count": 1}

        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=rows)
        mock_count_cursor = AsyncMock()
        mock_count_cursor.fetchone = AsyncMock(return_value=count_row)

        call_count = [0]

        async def execute_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:  # cleanup
                cursor = AsyncMock()
                cursor.rowcount = 0
                return cursor
            elif call_count[0] == 2:  # list
                return mock_cursor
            else:  # count
                return mock_count_cursor

        mock_connection.execute = AsyncMock(side_effect=execute_side_effect)

        with patch("services.notification_service.logger"):
            result = await notification_service.list_notifications("user-123")

        assert isinstance(result, NotificationListResult)
        assert len(result.notifications) == 1
        assert result.total == 1
        assert result.unread_count == 1

    @pytest.mark.asyncio
    async def test_list_notifications_with_read_filter(
        self, notification_service, mock_connection
    ):
        """list_notifications should filter by read status."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=[])
        mock_count_cursor = AsyncMock()
        mock_count_cursor.fetchone = AsyncMock(
            return_value={"total": 0, "unread_count": 0}
        )

        async def execute_side_effect(*args, **kwargs):
            if "DELETE" in str(args) or "UPDATE" in str(args):
                cursor = AsyncMock()
                cursor.rowcount = 0
                return cursor
            elif "COUNT" in str(args):
                return mock_count_cursor
            return mock_cursor

        mock_connection.execute = AsyncMock(side_effect=execute_side_effect)

        with patch("services.notification_service.logger"):
            await notification_service.list_notifications(
                "user-123", read_filter=False
            )

        calls = mock_connection.execute.call_args_list
        list_call = [c for c in calls if "SELECT * FROM" in str(c)][0]
        assert "AND read = ?" in list_call[0][0]

    @pytest.mark.asyncio
    async def test_list_notifications_with_type_filter(
        self, notification_service, mock_connection
    ):
        """list_notifications should filter by notification type."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=[])
        mock_count_cursor = AsyncMock()
        mock_count_cursor.fetchone = AsyncMock(
            return_value={"total": 0, "unread_count": 0}
        )

        async def execute_side_effect(*args, **kwargs):
            if "DELETE" in str(args) or "UPDATE" in str(args):
                cursor = AsyncMock()
                cursor.rowcount = 0
                return cursor
            elif "COUNT" in str(args):
                return mock_count_cursor
            return mock_cursor

        mock_connection.execute = AsyncMock(side_effect=execute_side_effect)

        with patch("services.notification_service.logger"):
            await notification_service.list_notifications(
                "user-123", notification_type=NotificationType.ERROR
            )

        calls = mock_connection.execute.call_args_list
        list_call = [c for c in calls if "SELECT * FROM" in str(c)][0]
        assert "AND type = ?" in list_call[0][0]

    @pytest.mark.asyncio
    async def test_list_notifications_calls_cleanup(
        self, notification_service, mock_connection
    ):
        """list_notifications should cleanup expired notifications first."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=[])
        mock_cursor.rowcount = 0
        mock_count_cursor = AsyncMock()
        mock_count_cursor.fetchone = AsyncMock(
            return_value={"total": 0, "unread_count": 0}
        )

        async def execute_side_effect(*args, **kwargs):
            if "COUNT" in str(args):
                return mock_count_cursor
            return mock_cursor

        mock_connection.execute = AsyncMock(side_effect=execute_side_effect)

        with patch("services.notification_service.logger"):
            await notification_service.list_notifications("user-123")

        calls = mock_connection.execute.call_args_list
        first_call = calls[0][0][0]
        assert "UPDATE" in first_call or "expires_at" in first_call
