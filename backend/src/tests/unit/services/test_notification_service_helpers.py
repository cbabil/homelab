"""
Unit tests for services/notification_service.py - Helper methods.

Tests _dict_factory and _row_to_notification conversions.
"""

from unittest.mock import MagicMock, patch

import pytest

from models.notification import Notification, NotificationType
from services.notification_service import NotificationService


@pytest.fixture
def mock_db_service():
    """Create mock database service."""
    return MagicMock()


@pytest.fixture
def notification_service(mock_db_service):
    """Create NotificationService with mocked dependencies."""
    with patch("services.notification_service.logger"):
        return NotificationService(mock_db_service)


@pytest.fixture
def base_notification_row():
    """Base row for notification tests."""
    return {
        "id": "notif-123",
        "user_id": "user-123",
        "type": "info",
        "title": "Test",
        "message": "Message",
        "read": 0,
        "created_at": "2024-01-15T10:00:00+00:00",
        "read_at": None,
        "dismissed_at": None,
        "expires_at": None,
        "source": None,
        "metadata": None,
    }


class TestDictFactory:
    """Tests for _dict_factory method."""

    def test_dict_factory_converts_row(self, notification_service):
        """_dict_factory should convert row to dictionary."""
        mock_cursor = MagicMock()
        mock_cursor.description = [("id",), ("name",), ("value",)]
        row = ("notif-123", "Test", 42)

        result = notification_service._dict_factory(mock_cursor, row)

        assert result == {"id": "notif-123", "name": "Test", "value": 42}

    def test_dict_factory_handles_empty_row(self, notification_service):
        """_dict_factory should handle empty row."""
        mock_cursor = MagicMock()
        mock_cursor.description = []
        row = ()

        result = notification_service._dict_factory(mock_cursor, row)

        assert result == {}


class TestRowToNotification:
    """Tests for _row_to_notification method."""

    def test_row_to_notification_basic(
        self, notification_service, base_notification_row
    ):
        """_row_to_notification should convert basic row."""
        result = notification_service._row_to_notification(base_notification_row)

        assert isinstance(result, Notification)
        assert result.id == "notif-123"
        assert result.type == NotificationType.INFO
        assert result.read is False

    def test_row_to_notification_with_read_at(
        self, notification_service, base_notification_row
    ):
        """_row_to_notification should parse read_at."""
        row = {
            **base_notification_row,
            "type": "success",
            "read": 1,
            "read_at": "2024-01-15T12:00:00+00:00",
            "source": "system",
        }

        result = notification_service._row_to_notification(row)

        assert result.read is True
        assert result.read_at is not None

    def test_row_to_notification_with_dismissed_at(
        self, notification_service, base_notification_row
    ):
        """_row_to_notification should parse dismissed_at."""
        row = {
            **base_notification_row,
            "type": "warning",
            "dismissed_at": "2024-01-16T08:00:00+00:00",
        }

        result = notification_service._row_to_notification(row)

        assert result.dismissed_at is not None

    def test_row_to_notification_with_expires_at(
        self, notification_service, base_notification_row
    ):
        """_row_to_notification should parse expires_at."""
        row = {
            **base_notification_row,
            "type": "error",
            "expires_at": "2024-01-20T10:00:00+00:00",
        }

        result = notification_service._row_to_notification(row)

        assert result.expires_at is not None

    def test_row_to_notification_with_metadata(
        self, notification_service, base_notification_row
    ):
        """_row_to_notification should parse metadata JSON."""
        row = {
            **base_notification_row,
            "source": "app",
            "metadata": '{"server_id": "srv-1", "count": 5}',
        }

        result = notification_service._row_to_notification(row)

        assert result.metadata == {"server_id": "srv-1", "count": 5}
        assert result.source == "app"

    def test_row_to_notification_all_types(
        self, notification_service, base_notification_row
    ):
        """_row_to_notification should handle all notification types."""
        for ntype in NotificationType:
            row = {**base_notification_row, "type": ntype.value}
            result = notification_service._row_to_notification(row)
            assert result.type == ntype
