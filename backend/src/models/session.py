"""
Session Data Models

Defines session management data models using Pydantic.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class SessionStatus(str, Enum):
    """Session status values."""

    ACTIVE = "active"
    IDLE = "idle"
    EXPIRED = "expired"
    TERMINATED = "terminated"


class Session(BaseModel):
    """Database session model."""

    id: str = Field(..., description="Session ID")
    user_id: str = Field(..., description="User ID")
    ip_address: str | None = Field(None, description="Client IP address")
    user_agent: str | None = Field(None, description="Browser/device info")
    created_at: datetime = Field(..., description="Session start time")
    expires_at: datetime = Field(..., description="Expiration time")
    last_activity: datetime = Field(..., description="Last activity timestamp")
    status: SessionStatus = Field(default=SessionStatus.ACTIVE)
    terminated_at: datetime | None = Field(None, description="When terminated")
    terminated_by: str | None = Field(None, description="User ID or 'system'")


class SessionCreate(BaseModel):
    """Parameters for creating a session."""

    user_id: str = Field(..., description="User ID")
    ip_address: str | None = Field(None, description="Client IP address")
    user_agent: str | None = Field(None, description="Browser/device info")
    expires_at: datetime = Field(..., description="Expiration time")


class SessionUpdate(BaseModel):
    """Parameters for updating a session."""

    last_activity: datetime | None = Field(None)
    status: SessionStatus | None = Field(None)


class SessionListResponse(BaseModel):
    """Response item for list_sessions tool."""

    id: str
    user_id: str
    username: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    created_at: str
    expires_at: str
    last_activity: str
    status: str
    is_current: bool = False
