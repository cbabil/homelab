"""
Notification Data Models

Defines notification data models using Pydantic.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class NotificationType(str, Enum):
    """Notification type values."""

    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


class Notification(BaseModel):
    """Database notification model."""

    id: str = Field(..., description="Notification ID")
    user_id: str = Field(..., description="User ID")
    type: NotificationType = Field(..., description="Notification type")
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    read: bool = Field(default=False, description="Read status")
    created_at: datetime = Field(..., description="Creation timestamp")
    read_at: datetime | None = Field(None, description="When marked as read")
    dismissed_at: datetime | None = Field(None, description="When dismissed")
    expires_at: datetime | None = Field(None, description="Expiration time")
    source: str | None = Field(None, description="Source of notification")
    metadata: dict[str, Any] | None = Field(None, description="Additional data")


class NotificationCreate(BaseModel):
    """Parameters for creating a notification."""

    user_id: str = Field(..., description="User ID")
    type: NotificationType = Field(..., description="Notification type")
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    source: str | None = Field(None, description="Source of notification")
    metadata: dict[str, Any] | None = Field(None, description="Additional data")
    expires_at: datetime | None = Field(None, description="Expiration time")


class NotificationListResponse(BaseModel):
    """Response item for list_notifications tool."""

    id: str
    user_id: str
    type: str
    title: str
    message: str
    read: bool
    created_at: str
    read_at: str | None = None
    source: str | None = None
    metadata: dict[str, Any] | None = None


class NotificationListResult(BaseModel):
    """Result for list_notifications tool."""

    notifications: list[NotificationListResponse]
    total: int
    unread_count: int


class NotificationCountResponse(BaseModel):
    """Response for unread count."""

    unread_count: int
    total: int
