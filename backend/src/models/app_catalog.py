"""
App Catalog Models

Defines models for application definitions and installations.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
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
    description: Optional[str] = Field(None, description="Help text")
    required: bool = Field(default=False, description="Is required")
    default: Optional[str] = Field(None, description="Default value")


class AppDefinition(BaseModel):
    """Application definition from catalog."""
    id: str = Field(..., description="Unique app identifier")
    name: str = Field(..., description="Display name")
    description: str = Field(..., description="App description")
    category: AppCategory = Field(..., description="App category")
    image: str = Field(..., description="Docker image")
    ports: List[AppPort] = Field(default_factory=list)
    volumes: List[AppVolume] = Field(default_factory=list)
    env_vars: List[AppEnvVar] = Field(default_factory=list)
    restart_policy: str = Field(default="unless-stopped")
    network_mode: Optional[str] = Field(None, description="Docker network mode")
    privileged: bool = Field(default=False, description="Run privileged")
    capabilities: List[str] = Field(default_factory=list)


class InstalledApp(BaseModel):
    """Installed application instance."""
    id: str = Field(..., description="Installation ID")
    server_id: str = Field(..., description="Server where installed")
    app_id: str = Field(..., description="App definition ID")
    container_id: Optional[str] = Field(None, description="Docker container ID")
    container_name: Optional[str] = Field(None, description="Docker container name")
    status: InstallationStatus = Field(default=InstallationStatus.PENDING)
    config: Dict[str, Any] = Field(default_factory=dict)
    installed_at: Optional[str] = Field(None)
    started_at: Optional[str] = Field(None)
    error_message: Optional[str] = Field(None)
    step_durations: Optional[Dict[str, int]] = Field(default=None, description="Duration in seconds for each step")
    step_started_at: Optional[str] = Field(default=None, description="When current step started")
    networks: Optional[List[str]] = Field(default=None, description="Docker networks")
    named_volumes: Optional[List[Dict[str, str]]] = Field(default=None, description="Named volume mounts")
    bind_mounts: Optional[List[Dict[str, str]]] = Field(default=None, description="Bind mounts")
