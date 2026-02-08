"""
Unit tests for models/notification.py

Tests notification models including types, notifications, and responses.
"""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from models.notification import (
    Notification,
    NotificationCountResponse,
    NotificationCreate,
    NotificationListResponse,
    NotificationListResult,
    NotificationType,
)


class TestNotificationType:
    """Tests for NotificationType enum."""

    def test_notification_type_values(self):
        """Test all notification type enum values."""
        assert NotificationType.INFO == "info"
        assert NotificationType.SUCCESS == "success"
        assert NotificationType.WARNING == "warning"
        assert NotificationType.ERROR == "error"

    def test_notification_type_is_string_enum(self):
        """Test that notification type values are strings."""
        assert isinstance(NotificationType.INFO.value, str)
        assert isinstance(NotificationType.SUCCESS.value, str)
        assert isinstance(NotificationType.WARNING.value, str)
        assert isinstance(NotificationType.ERROR.value, str)

    def test_notification_type_from_value(self):
        """Test creating enum from string value."""
        assert NotificationType("info") == NotificationType.INFO
        assert NotificationType("success") == NotificationType.SUCCESS
        assert NotificationType("warning") == NotificationType.WARNING
        assert NotificationType("error") == NotificationType.ERROR


class TestNotification:
    """Tests for Notification model."""

    def test_required_fields(self):
        """Test required fields."""
        now = datetime.now(UTC)
        notification = Notification(
            id="notif-123",
            user_id="user-456",
            type=NotificationType.INFO,
            title="Test Title",
            message="Test message content",
            created_at=now,
        )
        assert notification.id == "notif-123"
        assert notification.user_id == "user-456"
        assert notification.type == NotificationType.INFO
        assert notification.title == "Test Title"
        assert notification.message == "Test message content"
        assert notification.created_at == now

    def test_default_values(self):
        """Test default values for optional fields."""
        now = datetime.now(UTC)
        notification = Notification(
            id="notif-123",
            user_id="user-456",
            type=NotificationType.INFO,
            title="Test",
            message="Test message",
            created_at=now,
        )
        assert notification.read is False
        assert notification.read_at is None
        assert notification.dismissed_at is None
        assert notification.expires_at is None
        assert notification.source is None
        assert notification.metadata is None

    def test_all_fields(self):
        """Test all fields populated."""
        now = datetime.now(UTC)
        expires = datetime(2025, 12, 31, 23, 59, 59)
        notification = Notification(
            id="notif-123",
            user_id="user-456",
            type=NotificationType.ERROR,
            title="Server Down",
            message="Server web-01 is not responding",
            read=True,
            created_at=now,
            read_at=now,
            dismissed_at=now,
            expires_at=expires,
            source="monitoring",
            metadata={"server_id": "web-01", "retry_count": 3},
        )
        assert notification.read is True
        assert notification.read_at == now
        assert notification.dismissed_at == now
        assert notification.expires_at == expires
        assert notification.source == "monitoring"
        assert notification.metadata == {"server_id": "web-01", "retry_count": 3}

    def test_all_notification_types(self):
        """Test notification with each type."""
        now = datetime.now(UTC)
        for ntype in NotificationType:
            notification = Notification(
                id=f"notif-{ntype.value}",
                user_id="user-123",
                type=ntype,
                title=f"{ntype.value.title()} Notification",
                message=f"This is a {ntype.value} notification",
                created_at=now,
            )
            assert notification.type == ntype

    def test_missing_required_fields(self):
        """Test validation error when required fields are missing."""
        with pytest.raises(ValidationError):
            Notification(id="notif-123")

    def test_missing_type(self):
        """Test validation error when type is missing."""
        now = datetime.now(UTC)
        with pytest.raises(ValidationError):
            Notification(
                id="notif-123",
                user_id="user-456",
                title="Test",
                message="Test message",
                created_at=now,
            )

    def test_missing_title(self):
        """Test validation error when title is missing."""
        now = datetime.now(UTC)
        with pytest.raises(ValidationError):
            Notification(
                id="notif-123",
                user_id="user-456",
                type=NotificationType.INFO,
                message="Test message",
                created_at=now,
            )


class TestNotificationCreate:
    """Tests for NotificationCreate model."""

    def test_required_fields(self):
        """Test required fields."""
        create = NotificationCreate(
            user_id="user-123",
            type=NotificationType.SUCCESS,
            title="Task Complete",
            message="Your task has been completed",
        )
        assert create.user_id == "user-123"
        assert create.type == NotificationType.SUCCESS
        assert create.title == "Task Complete"
        assert create.message == "Your task has been completed"

    def test_default_values(self):
        """Test default values for optional fields."""
        create = NotificationCreate(
            user_id="user-123",
            type=NotificationType.INFO,
            title="Info",
            message="Information",
        )
        assert create.source is None
        assert create.metadata is None
        assert create.expires_at is None

    def test_all_fields(self):
        """Test all fields populated."""
        expires = datetime(2025, 6, 1, 12, 0, 0)
        create = NotificationCreate(
            user_id="user-123",
            type=NotificationType.WARNING,
            title="Disk Space Low",
            message="Server has less than 10% disk space",
            source="monitoring",
            metadata={"disk_percent": 8.5, "server": "db-01"},
            expires_at=expires,
        )
        assert create.source == "monitoring"
        assert create.metadata == {"disk_percent": 8.5, "server": "db-01"}
        assert create.expires_at == expires

    def test_missing_required_fields(self):
        """Test validation error when required fields are missing."""
        with pytest.raises(ValidationError):
            NotificationCreate(user_id="user-123")

    def test_all_notification_types_create(self):
        """Test creating notifications with each type."""
        for ntype in NotificationType:
            create = NotificationCreate(
                user_id="user-123",
                type=ntype,
                title=f"{ntype.value.title()}",
                message="Test",
            )
            assert create.type == ntype


class TestNotificationListResponse:
    """Tests for NotificationListResponse model."""

    def test_required_fields(self):
        """Test required fields."""
        response = NotificationListResponse(
            id="notif-123",
            user_id="user-456",
            type="info",
            title="Test Title",
            message="Test message",
            read=False,
            created_at="2024-01-15T10:00:00Z",
        )
        assert response.id == "notif-123"
        assert response.user_id == "user-456"
        assert response.type == "info"
        assert response.title == "Test Title"
        assert response.message == "Test message"
        assert response.read is False
        assert response.created_at == "2024-01-15T10:00:00Z"

    def test_default_values(self):
        """Test default values for optional fields."""
        response = NotificationListResponse(
            id="notif-123",
            user_id="user-456",
            type="info",
            title="Test",
            message="Test message",
            read=False,
            created_at="2024-01-15T10:00:00Z",
        )
        assert response.read_at is None
        assert response.source is None
        assert response.metadata is None

    def test_all_fields(self):
        """Test all fields populated."""
        response = NotificationListResponse(
            id="notif-123",
            user_id="user-456",
            type="error",
            title="Error Alert",
            message="Something went wrong",
            read=True,
            created_at="2024-01-15T10:00:00Z",
            read_at="2024-01-15T11:00:00Z",
            source="system",
            metadata={"error_code": 500},
        )
        assert response.read is True
        assert response.read_at == "2024-01-15T11:00:00Z"
        assert response.source == "system"
        assert response.metadata == {"error_code": 500}

    def test_missing_required_fields(self):
        """Test validation error when required fields are missing."""
        with pytest.raises(ValidationError):
            NotificationListResponse(id="notif-123")


class TestNotificationListResult:
    """Tests for NotificationListResult model."""

    def test_required_fields(self):
        """Test required fields."""
        result = NotificationListResult(
            notifications=[],
            total=0,
            unread_count=0,
        )
        assert result.notifications == []
        assert result.total == 0
        assert result.unread_count == 0

    def test_with_notifications(self):
        """Test with notification list."""
        notif1 = NotificationListResponse(
            id="notif-1",
            user_id="user-123",
            type="info",
            title="Info 1",
            message="Message 1",
            read=False,
            created_at="2024-01-15T10:00:00Z",
        )
        notif2 = NotificationListResponse(
            id="notif-2",
            user_id="user-123",
            type="success",
            title="Success 1",
            message="Message 2",
            read=True,
            created_at="2024-01-15T11:00:00Z",
        )
        result = NotificationListResult(
            notifications=[notif1, notif2],
            total=2,
            unread_count=1,
        )
        assert len(result.notifications) == 2
        assert result.total == 2
        assert result.unread_count == 1
        assert result.notifications[0].id == "notif-1"
        assert result.notifications[1].id == "notif-2"

    def test_missing_required_fields(self):
        """Test validation error when required fields are missing."""
        with pytest.raises(ValidationError):
            NotificationListResult(notifications=[])


class TestNotificationCountResponse:
    """Tests for NotificationCountResponse model."""

    def test_required_fields(self):
        """Test required fields."""
        response = NotificationCountResponse(
            unread_count=5,
            total=10,
        )
        assert response.unread_count == 5
        assert response.total == 10

    def test_zero_counts(self):
        """Test with zero counts."""
        response = NotificationCountResponse(
            unread_count=0,
            total=0,
        )
        assert response.unread_count == 0
        assert response.total == 0

    def test_all_unread(self):
        """Test when all notifications are unread."""
        response = NotificationCountResponse(
            unread_count=100,
            total=100,
        )
        assert response.unread_count == response.total

    def test_missing_required_fields(self):
        """Test validation error when required fields are missing."""
        with pytest.raises(ValidationError):
            NotificationCountResponse(unread_count=5)
