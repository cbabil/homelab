"""
App Catalog Models

Defines models for application definitions and installations.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AppCategory(str, Enum):
    """Application categories."""

    STORAGE = "storage"
    MEDIA = "media"
    NETWORKING = "networking"
    MONITORING = "monitoring"
    UTILITY = "utility"
    DATABASE = "database"
    DEVELOPMENT = "development"


class InstallationStatus(str, Enum):
    """Installation workflow status."""

    PENDING = "pending"
    PULLING = "pulling"
    CREATING = "creating"
    STARTING = "starting"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    REMOVING = "removing"


class AppPort(BaseModel):
    """Port mapping for an app."""

    container: int = Field(..., description="Container port")
    host: int = Field(..., description="Host port")
    protocol: str = Field(default="tcp", description="Protocol (tcp/udp)")


class AppVolume(BaseModel):
    """Volume mapping for an app."""

    host_path: str = Field(..., description="Path on host")
    container_path: str = Field(..., description="Path in container")
    readonly: bool = Field(default=False, description="Mount as read-only")


class AppEnvVar(BaseModel):
    """Environment variable for an app."""

    name: str = Field(..., description="Variable name")
    description: str | None = Field(None, description="Help text")
    required: bool = Field(default=False, description="Is required")
    default: str | None = Field(None, description="Default value")


class AppDefinition(BaseModel):
    """Application definition from catalog."""

    id: str = Field(..., description="Unique app identifier")
    name: str = Field(..., description="Display name")
    description: str = Field(..., description="App description")
    category: AppCategory = Field(..., description="App category")
    image: str = Field(..., description="Docker image")
    ports: list[AppPort] = Field(default_factory=list)
    volumes: list[AppVolume] = Field(default_factory=list)
    env_vars: list[AppEnvVar] = Field(default_factory=list)
    restart_policy: str = Field(default="unless-stopped")
    network_mode: str | None = Field(None, description="Docker network mode")
    privileged: bool = Field(default=False, description="Run privileged")
    capabilities: list[str] = Field(default_factory=list)


class InstalledApp(BaseModel):
    """Installed application instance."""

    id: str = Field(..., description="Installation ID")
    server_id: str = Field(..., description="Server where installed")
    app_id: str = Field(..., description="App definition ID")
    container_id: str | None = Field(None, description="Docker container ID")
    container_name: str | None = Field(None, description="Docker container name")
    status: InstallationStatus = Field(default=InstallationStatus.PENDING)
    config: dict[str, Any] = Field(default_factory=dict)
    installed_at: str | None = Field(None)
    started_at: str | None = Field(None)
    error_message: str | None = Field(None)
    step_durations: dict[str, int] | None = Field(
        default=None, description="Duration in seconds for each step"
    )
    step_started_at: str | None = Field(
        default=None, description="When current step started"
    )
    networks: list[str] | None = Field(default=None, description="Docker networks")
    named_volumes: list[dict[str, str]] | None = Field(
        default=None, description="Named volume mounts"
    )
    bind_mounts: list[dict[str, str]] | None = Field(
        default=None, description="Bind mounts"
    )
