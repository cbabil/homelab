"""
Notification Data Models

Defines notification data models using Pydantic.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
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
    read_at: Optional[datetime] = Field(None, description="When marked as read")
    dismissed_at: Optional[datetime] = Field(None, description="When dismissed")
    expires_at: Optional[datetime] = Field(None, description="Expiration time")
    source: Optional[str] = Field(None, description="Source of notification")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional data")


class NotificationCreate(BaseModel):
    """Parameters for creating a notification."""
    user_id: str = Field(..., description="User ID")
    type: NotificationType = Field(..., description="Notification type")
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    source: Optional[str] = Field(None, description="Source of notification")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional data")
    expires_at: Optional[datetime] = Field(None, description="Expiration time")


class NotificationListResponse(BaseModel):
    """Response item for list_notifications tool."""
    id: str
    user_id: str
    type: str
    title: str
    message: str
    read: bool
    created_at: str
    read_at: Optional[str] = None
    source: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class NotificationListResult(BaseModel):
    """Result for list_notifications tool."""
    notifications: List[NotificationListResponse]
    total: int
    unread_count: int


class NotificationCountResponse(BaseModel):
    """Response for unread count."""
    unread_count: int
    total: int
