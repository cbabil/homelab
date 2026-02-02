"""
Agent Data Models

Defines agent management data models using Pydantic for type-safe handling
of WebSocket-based agent communication and registration.
"""

from datetime import datetime
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    """Agent connection status states."""

    PENDING = "pending"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    UPDATING = "updating"


class AgentConfig(BaseModel):
    """Agent configuration settings."""

    metrics_interval: int = Field(
        default=30, ge=5, le=300, description="Metrics collection interval in seconds"
    )
    health_interval: int = Field(
        default=60, ge=10, le=600, description="Health check interval in seconds"
    )
    reconnect_timeout: int = Field(
        default=30, ge=5, le=120, description="WebSocket reconnect timeout in seconds"
    )
    heartbeat_interval: int = Field(
        default=30, ge=10, le=120, description="Heartbeat ping interval in seconds"
    )
    heartbeat_timeout: int = Field(
        default=90,
        ge=30,
        le=300,
        description="Heartbeat timeout before marking agent stale",
    )
    auto_update: bool = Field(
        default=True, description="Enable automatic agent updates"
    )


class Agent(BaseModel):
    """Agent model representing a registered agent instance."""

    id: str = Field(..., description="Unique agent identifier")
    server_id: str = Field(..., description="Associated server identifier")
    token_hash: Optional[str] = Field(None, description="Hashed authentication token")
    version: Optional[str] = Field(None, description="Agent software version")
    status: AgentStatus = Field(
        default=AgentStatus.PENDING, description="Current agent status"
    )
    last_seen: Optional[datetime] = Field(None, description="Last heartbeat timestamp")
    registered_at: Optional[datetime] = Field(
        None, description="Agent registration timestamp"
    )
    config: Optional[AgentConfig] = Field(None, description="Agent configuration")
    created_at: Optional[datetime] = Field(
        None, description="Record creation timestamp"
    )
    updated_at: Optional[datetime] = Field(None, description="Record update timestamp")

    # Token rotation fields
    pending_token_hash: Optional[str] = Field(
        None, description="Pending token hash during rotation"
    )
    token_issued_at: Optional[datetime] = Field(
        None, description="When current token was issued"
    )
    token_expires_at: Optional[datetime] = Field(
        None, description="When current token should be rotated"
    )


class AgentCreate(BaseModel):
    """Parameters for creating an agent."""

    server_id: str = Field(..., description="Associated server identifier")


class AgentUpdate(BaseModel):
    """Parameters for updating an agent (all fields optional for partial updates)."""

    server_id: Optional[str] = Field(None, description="Associated server identifier")
    token_hash: Optional[str] = Field(None, description="Hashed authentication token")
    version: Optional[str] = Field(None, description="Agent software version")
    status: Optional[AgentStatus] = Field(None, description="Current agent status")
    last_seen: Optional[datetime] = Field(None, description="Last heartbeat timestamp")
    registered_at: Optional[datetime] = Field(
        None, description="Agent registration timestamp"
    )
    config: Optional[AgentConfig] = Field(None, description="Agent configuration")

    # Token rotation fields
    pending_token_hash: Optional[str] = Field(
        None, description="Pending token hash during rotation"
    )
    token_issued_at: Optional[datetime] = Field(
        None, description="When current token was issued"
    )
    token_expires_at: Optional[datetime] = Field(
        None, description="When current token should be rotated"
    )


class RegistrationCode(BaseModel):
    """Agent registration code for secure agent onboarding."""

    id: str = Field(..., description="Unique registration code identifier")
    agent_id: str = Field(..., description="Associated agent identifier")
    code: str = Field(..., description="Registration code value")
    expires_at: datetime = Field(..., description="Code expiration timestamp")
    used: bool = Field(default=False, description="Whether code has been used")
    created_at: Optional[datetime] = Field(None, description="Code creation timestamp")


class AgentRegistrationRequest(BaseModel):
    """Request payload for agent registration."""

    code: str = Field(..., description="Registration code for authentication")


class AgentRegistrationResponse(BaseModel):
    """Response payload for successful agent registration."""

    agent_id: str = Field(..., description="Assigned agent identifier")
    server_id: str = Field(..., description="Associated server identifier")
    token: str = Field(..., description="Authentication token for WebSocket connection")
    config: AgentConfig = Field(..., description="Agent configuration settings")


class AgentInfo(BaseModel):
    """Lightweight agent information for listings and status displays."""

    id: str = Field(..., description="Unique agent identifier")
    server_id: str = Field(..., description="Associated server identifier")
    status: AgentStatus = Field(..., description="Current agent status")
    version: Optional[str] = Field(None, description="Agent software version")
    last_seen: Optional[datetime] = Field(None, description="Last heartbeat timestamp")
    registered_at: Optional[datetime] = Field(
        None, description="Agent registration timestamp"
    )
    is_stale: bool = Field(default=False, description="Whether agent missed heartbeats")


class AgentHeartbeat(BaseModel):
    """Heartbeat data sent by agent."""

    agent_id: str = Field(..., description="Agent identifier")
    timestamp: datetime = Field(..., description="Heartbeat timestamp")
    cpu_percent: Optional[float] = Field(None, description="Current CPU usage")
    memory_percent: Optional[float] = Field(None, description="Current memory usage")
    uptime_seconds: Optional[int] = Field(None, description="Agent uptime in seconds")


class AgentVersionInfo(BaseModel):
    """Agent version information for update checks."""

    current_version: str = Field(..., description="Currently installed version")
    latest_version: str = Field(..., description="Latest available version")
    update_available: bool = Field(..., description="Whether update is available")
    release_notes: Optional[str] = Field(None, description="Release notes for update")
    update_url: Optional[str] = Field(None, description="URL to download update")


class AgentShutdownRequest(BaseModel):
    """Graceful shutdown request from agent."""

    agent_id: str = Field(..., description="Agent identifier")
    reason: str = Field(default="user_request", description="Shutdown reason")
    restart: bool = Field(default=False, description="Whether agent will restart")
