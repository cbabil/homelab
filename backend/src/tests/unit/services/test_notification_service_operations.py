"""
Unit tests for services/notification_service.py - Operations.

Tests mark_as_read, dismiss, cleanup, delete, and helpers.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.notification import NotificationCountResponse
from services.notification_service import NotificationService


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


class TestMarkAsRead:
    """Tests for mark_as_read method."""

    @pytest.mark.asyncio
    async def test_mark_as_read_success(self, notification_service, mock_connection):
        """mark_as_read should update notification."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 1
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        with patch("services.notification_service.logger"):
            result = await notification_service.mark_as_read("notif-123", "user-123")

        assert result is True
        mock_connection.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_mark_as_read_not_found(self, notification_service, mock_connection):
        """mark_as_read should return False when not found."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 0
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        with patch("services.notification_service.logger"):
            result = await notification_service.mark_as_read("nonexistent", "user-123")

        assert result is False

    @pytest.mark.asyncio
    async def test_mark_as_read_logs_success(
        self, notification_service, mock_connection
    ):
        """mark_as_read should log when successful."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 1
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        with patch("services.notification_service.logger") as mock_logger:
            await notification_service.mark_as_read("notif-123", "user-123")

            mock_logger.debug.assert_called_once()
            assert "marked as read" in mock_logger.debug.call_args[0][0]


class TestMarkAllAsRead:
    """Tests for mark_all_as_read method."""

    @pytest.mark.asyncio
    async def test_mark_all_as_read_success(
        self, notification_service, mock_connection
    ):
        """mark_all_as_read should update all unread notifications."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 5
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        with patch("services.notification_service.logger"):
            result = await notification_service.mark_all_as_read("user-123")

        assert result == 5
        mock_connection.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_mark_all_as_read_none(self, notification_service, mock_connection):
        """mark_all_as_read should return 0 when no unread."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 0
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        with patch("services.notification_service.logger"):
            result = await notification_service.mark_all_as_read("user-123")

        assert result == 0

    @pytest.mark.asyncio
    async def test_mark_all_as_read_logs(self, notification_service, mock_connection):
        """mark_all_as_read should log result."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 3
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        with patch("services.notification_service.logger") as mock_logger:
            await notification_service.mark_all_as_read("user-123")

            mock_logger.info.assert_called()
            call_kwargs = mock_logger.info.call_args[1]
            assert call_kwargs["count"] == 3


class TestDismissNotification:
    """Tests for dismiss_notification method."""

    @pytest.mark.asyncio
    async def test_dismiss_notification_success(
        self, notification_service, mock_connection
    ):
        """dismiss_notification should soft-delete notification."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 1
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        with patch("services.notification_service.logger"):
            result = await notification_service.dismiss_notification(
                "notif-123", "user-123"
            )

        assert result is True
        mock_connection.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_dismiss_notification_not_found(
        self, notification_service, mock_connection
    ):
        """dismiss_notification should return False when not found."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 0
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        with patch("services.notification_service.logger"):
            result = await notification_service.dismiss_notification(
                "nonexistent", "user-123"
            )

        assert result is False

    @pytest.mark.asyncio
    async def test_dismiss_notification_logs_success(
        self, notification_service, mock_connection
    ):
        """dismiss_notification should log when successful."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 1
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        with patch("services.notification_service.logger") as mock_logger:
            await notification_service.dismiss_notification("notif-123", "user-123")

            mock_logger.debug.assert_called_once()
            assert "dismissed" in mock_logger.debug.call_args[0][0]


class TestDismissAll:
    """Tests for dismiss_all method."""

    @pytest.mark.asyncio
    async def test_dismiss_all_success(self, notification_service, mock_connection):
        """dismiss_all should dismiss all notifications for user."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 10
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        with patch("services.notification_service.logger"):
            result = await notification_service.dismiss_all("user-123")

        assert result == 10
        mock_connection.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_dismiss_all_none(self, notification_service, mock_connection):
        """dismiss_all should return 0 when no notifications."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 0
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        with patch("services.notification_service.logger"):
            result = await notification_service.dismiss_all("user-123")

        assert result == 0

    @pytest.mark.asyncio
    async def test_dismiss_all_logs(self, notification_service, mock_connection):
        """dismiss_all should log result."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 7
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        with patch("services.notification_service.logger") as mock_logger:
            await notification_service.dismiss_all("user-123")

            mock_logger.info.assert_called()
            call_kwargs = mock_logger.info.call_args[1]
            assert call_kwargs["count"] == 7


class TestGetUnreadCount:
    """Tests for get_unread_count method."""

    @pytest.mark.asyncio
    async def test_get_unread_count_success(
        self, notification_service, mock_connection
    ):
        """get_unread_count should return counts."""
        count_row = {"total": 15, "unread_count": 8}
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=count_row)
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        with patch("services.notification_service.logger"):
            result = await notification_service.get_unread_count("user-123")

        assert isinstance(result, NotificationCountResponse)
        assert result.total == 15
        assert result.unread_count == 8

    @pytest.mark.asyncio
    async def test_get_unread_count_empty(self, notification_service, mock_connection):
        """get_unread_count should handle None values."""
        count_row = {"total": None, "unread_count": None}
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=count_row)
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        with patch("services.notification_service.logger"):
            result = await notification_service.get_unread_count("user-123")

        assert result.total == 0
        assert result.unread_count == 0


class TestCleanupExpiredNotifications:
    """Tests for cleanup_expired_notifications method."""

    @pytest.mark.asyncio
    async def test_cleanup_expired_success(self, notification_service, mock_connection):
        """cleanup_expired_notifications should dismiss expired."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 3
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        with patch("services.notification_service.logger"):
            result = await notification_service.cleanup_expired_notifications()

        assert result == 3
        mock_connection.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_expired_with_user_id(
        self, notification_service, mock_connection
    ):
        """cleanup_expired_notifications should filter by user_id."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 1
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        with patch("services.notification_service.logger"):
            await notification_service.cleanup_expired_notifications("user-123")

        call_args = mock_connection.execute.call_args[0]
        assert "user_id = ?" in call_args[0]
        assert "user-123" in call_args[1]

    @pytest.mark.asyncio
    async def test_cleanup_expired_logs_when_cleaned(
        self, notification_service, mock_connection
    ):
        """cleanup_expired_notifications should log when items cleaned."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 5
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        with patch("services.notification_service.logger") as mock_logger:
            await notification_service.cleanup_expired_notifications()

            mock_logger.info.assert_called()
            assert mock_logger.info.call_args[1]["count"] == 5

    @pytest.mark.asyncio
    async def test_cleanup_expired_no_log_when_none(
        self, notification_service, mock_connection
    ):
        """cleanup_expired_notifications should not log when nothing cleaned."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 0
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        with patch("services.notification_service.logger") as mock_logger:
            await notification_service.cleanup_expired_notifications()

            info_calls = [
                c for c in mock_logger.info.call_args_list if "cleaned up" in str(c)
            ]
            assert len(info_calls) == 0


class TestDeleteOldNotifications:
    """Tests for delete_old_notifications method."""

    @pytest.mark.asyncio
    async def test_delete_old_success(self, notification_service, mock_connection):
        """delete_old_notifications should delete old dismissed."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 20
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        with patch("services.notification_service.logger"):
            result = await notification_service.delete_old_notifications()

        assert result == 20
        mock_connection.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_old_custom_days(self, notification_service, mock_connection):
        """delete_old_notifications should use custom days parameter."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 5
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        with patch("services.notification_service.logger"):
            await notification_service.delete_old_notifications(days=7)

        call_args = mock_connection.execute.call_args[0]
        assert "-7 days" in call_args[1][0]

    @pytest.mark.asyncio
    async def test_delete_old_logs_when_deleted(
        self, notification_service, mock_connection
    ):
        """delete_old_notifications should log when items deleted."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 10
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        with patch("services.notification_service.logger") as mock_logger:
            await notification_service.delete_old_notifications(days=14)

            mock_logger.info.assert_called()
            kwargs = mock_logger.info.call_args[1]
            assert kwargs["count"] == 10
            assert kwargs["days"] == 14

    @pytest.mark.asyncio
    async def test_delete_old_no_log_when_none(
        self, notification_service, mock_connection
    ):
        """delete_old_notifications should not log when nothing deleted."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 0
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        with patch("services.notification_service.logger") as mock_logger:
            await notification_service.delete_old_notifications()

            delete_logs = [
                c for c in mock_logger.info.call_args_list if "deleted" in str(c)
            ]
            assert len(delete_logs) == 0
