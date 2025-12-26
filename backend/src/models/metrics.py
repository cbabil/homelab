"""
Metrics and Activity Log Models

Defines models for server metrics, container metrics, and activity logging.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class MetricType(str, Enum):
    """Types of metrics collected."""
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"


class ActivityType(str, Enum):
    """Types of logged activities."""
    # User activities
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_CREATED = "user_created"

    # Server activities
    SERVER_ADDED = "server_added"
    SERVER_UPDATED = "server_updated"
    SERVER_DELETED = "server_deleted"
    SERVER_CONNECTED = "server_connected"
    SERVER_DISCONNECTED = "server_disconnected"

    # Preparation activities
    PREPARATION_STARTED = "preparation_started"
    PREPARATION_COMPLETE = "preparation_complete"
    PREPARATION_FAILED = "preparation_failed"

    # App activities
    APP_INSTALLED = "app_installed"
    APP_UNINSTALLED = "app_uninstalled"
    APP_STARTED = "app_started"
    APP_STOPPED = "app_stopped"
    APP_CRASHED = "app_crashed"

    # System activities
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"
    BACKUP_CREATED = "backup_created"
    BACKUP_RESTORED = "backup_restored"


class ServerMetrics(BaseModel):
    """Server resource metrics snapshot."""
    id: str = Field(..., description="Metric record ID")
    server_id: str = Field(..., description="Server ID")
    cpu_percent: float = Field(..., description="CPU usage percentage")
    memory_percent: float = Field(..., description="Memory usage percentage")
    memory_used_mb: int = Field(..., description="Memory used in MB")
    memory_total_mb: int = Field(..., description="Total memory in MB")
    disk_percent: float = Field(..., description="Disk usage percentage")
    disk_used_gb: int = Field(..., description="Disk used in GB")
    disk_total_gb: int = Field(..., description="Total disk in GB")
    network_rx_bytes: int = Field(default=0, description="Network bytes received")
    network_tx_bytes: int = Field(default=0, description="Network bytes transmitted")
    load_average_1m: Optional[float] = Field(None, description="1 minute load average")
    load_average_5m: Optional[float] = Field(None, description="5 minute load average")
    load_average_15m: Optional[float] = Field(None, description="15 minute load average")
    uptime_seconds: Optional[int] = Field(None, description="Server uptime in seconds")
    timestamp: str = Field(..., description="Collection timestamp")


class ContainerMetrics(BaseModel):
    """Docker container metrics snapshot."""
    id: str = Field(..., description="Metric record ID")
    server_id: str = Field(..., description="Server ID")
    container_id: str = Field(..., description="Docker container ID")
    container_name: str = Field(..., description="Container name")
    cpu_percent: float = Field(..., description="CPU usage percentage")
    memory_usage_mb: int = Field(..., description="Memory usage in MB")
    memory_limit_mb: int = Field(..., description="Memory limit in MB")
    network_rx_bytes: int = Field(default=0, description="Network bytes received")
    network_tx_bytes: int = Field(default=0, description="Network bytes transmitted")
    status: str = Field(..., description="Container status")
    timestamp: str = Field(..., description="Collection timestamp")


class ActivityLog(BaseModel):
    """Activity log entry."""
    id: str = Field(..., description="Log entry ID")
    activity_type: ActivityType = Field(..., description="Type of activity")
    user_id: Optional[str] = Field(None, description="User who performed action")
    server_id: Optional[str] = Field(None, description="Related server")
    app_id: Optional[str] = Field(None, description="Related app")
    message: str = Field(..., description="Human-readable message")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional details")
    timestamp: str = Field(..., description="Activity timestamp")


class DashboardSummary(BaseModel):
    """Aggregated dashboard data."""
    total_servers: int = Field(default=0)
    online_servers: int = Field(default=0)
    offline_servers: int = Field(default=0)
    total_apps: int = Field(default=0)
    running_apps: int = Field(default=0)
    stopped_apps: int = Field(default=0)
    error_apps: int = Field(default=0)
    avg_cpu_percent: float = Field(default=0.0)
    avg_memory_percent: float = Field(default=0.0)
    avg_disk_percent: float = Field(default=0.0)
    recent_activities: List[ActivityLog] = Field(default_factory=list)
