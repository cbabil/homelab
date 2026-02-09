"""
Monitoring Service

Handles metrics collection and log management for system monitoring.
Provides data access layer for monitoring operations.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

import structlog

from models.log import LogEntry, LogFilter
from services.service_log import LogService

logger = structlog.get_logger("monitoring_service")


class MonitoringService:
    """Service for managing system metrics and logs."""

    def __init__(self, log_service: LogService | None = None):
        """Initialize monitoring service with storage."""
        self._log_service = log_service
        self.metrics_cache: dict[str, Any] = {}
        logger.info("Monitoring service initialized")

        # Initialize with sample data
        self._initialize_sample_data()

    def _initialize_sample_data(self):
        """Initialize with sample metrics and logs."""
        self._initialize_metrics()
        # Note: _initialize_logs() will be called async during first log request

    def _initialize_metrics(self):
        """Initialize sample system metrics in frontend-compatible format."""
        self.metrics_cache = {
            "cpu": {"usage": 45.2, "cores": 8, "temperature": 65.5},
            "memory": {"used": 6.8, "total": 16.0, "percentage": 42.5},
            "disk": {"used": 125.3, "total": 500.0, "percentage": 25.1},
            "network": {"inbound": 1024000, "outbound": 2048000, "connections": 24},
            "uptime": 86400,  # 1 day in seconds
            "processes": 127,
            "timestamp": datetime.now(UTC).isoformat(),
        }

    async def _initialize_logs(self):
        """Initialize sample log entries in database."""
        try:
            # Create diverse sample log entries for different categories
            sample_logs = [
                # System logs
                LogEntry(
                    id="log-sys-1",
                    timestamp=datetime.now(UTC),
                    level="INFO",
                    source="systemd",
                    message="Service nginx started successfully",
                    tags=["system", "systemd", "startup"],
                ),
                LogEntry(
                    id="log-sys-2",
                    timestamp=datetime.now(UTC) - timedelta(minutes=2),
                    level="WARN",
                    source="kernel",
                    message="CPU temperature high: 82°C",
                    tags=["system", "kernel", "temperature"],
                ),
                LogEntry(
                    id="log-sys-3",
                    timestamp=datetime.now(UTC) - timedelta(minutes=8),
                    level="ERROR",
                    source="disk",
                    message="Disk space low on /var partition",
                    tags=["system", "disk", "storage"],
                ),
                # Application logs
                LogEntry(
                    id="log-app-1",
                    timestamp=datetime.now(UTC) - timedelta(minutes=1),
                    level="INFO",
                    source="application",
                    message="User login successful",
                    tags=["application", "auth", "login"],
                ),
                LogEntry(
                    id="log-app-2",
                    timestamp=datetime.now(UTC) - timedelta(minutes=5),
                    level="ERROR",
                    source="application",
                    message="Failed to connect to database",
                    tags=["application", "database", "error"],
                ),
                LogEntry(
                    id="log-app-3",
                    timestamp=datetime.now(UTC) - timedelta(minutes=12),
                    level="DEBUG",
                    source="application",
                    message="Processing API request",
                    tags=["application", "api", "debug"],
                ),
                # Docker logs
                LogEntry(
                    id="log-docker-1",
                    timestamp=datetime.now(UTC) - timedelta(minutes=3),
                    level="INFO",
                    source="docker",
                    message="Container nginx started successfully",
                    tags=["docker", "nginx", "startup"],
                ),
                LogEntry(
                    id="log-docker-2",
                    timestamp=datetime.now(UTC) - timedelta(minutes=7),
                    level="WARN",
                    source="docker",
                    message="Container memory usage high",
                    tags=["docker", "memory", "performance"],
                ),
                # Security logs
                LogEntry(
                    id="log-sec-1",
                    timestamp=datetime.now(UTC) - timedelta(minutes=4),
                    level="WARN",
                    source="sshd",
                    message="Failed login attempt from 192.168.1.100",
                    tags=["security", "ssh", "failed-login"],
                ),
                LogEntry(
                    id="log-sec-2",
                    timestamp=datetime.now(UTC) - timedelta(minutes=9),
                    level="INFO",
                    source="firewall",
                    message="Blocked suspicious connection",
                    tags=["security", "firewall", "blocked"],
                ),
                # Network logs
                LogEntry(
                    id="log-net-1",
                    timestamp=datetime.now(UTC) - timedelta(minutes=6),
                    level="INFO",
                    source="dhcp",
                    message="New device connected: MAC aa:bb:cc:dd:ee:ff",
                    tags=["network", "dhcp", "connection"],
                ),
                LogEntry(
                    id="log-net-2",
                    timestamp=datetime.now(UTC) - timedelta(minutes=10),
                    level="ERROR",
                    source="router",
                    message="Network interface eth0 down",
                    tags=["network", "interface", "error"],
                ),
            ]

            # Store in database
            for log_entry in sample_logs:
                await self._log_service.create_log_entry(log_entry)

            logger.info("Sample logs initialized in database")

        except Exception as e:
            logger.warning("Failed to initialize sample logs", error=str(e))

    def get_current_metrics(self) -> dict[str, Any]:
        """Get current system metrics."""
        # Update timestamp for real-time feeling
        self.metrics_cache["timestamp"] = datetime.now(UTC).isoformat()
        return self.metrics_cache

    async def get_filtered_logs(
        self, filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Get logs with optional filtering from database."""
        try:
            # Convert dict filters to LogFilter model
            log_filter = None
            if filters:
                log_filter = LogFilter(
                    level=filters.get("level"),
                    source=filters.get("source"),
                    limit=min(int(filters.get("limit", 100)), 1000)
                    if filters.get("limit")
                    else 100,
                )

            # Get logs from database
            log_entries = await self._log_service.get_logs(log_filter)

            # If no logs exist, initialize sample data
            if not log_entries:
                await self._initialize_logs()
                log_entries = await self._log_service.get_logs(log_filter)

            # Convert LogEntry models to dict format for frontend compatibility
            filtered_logs = []
            for log_entry in log_entries:
                log_dict = {
                    "id": log_entry.id,
                    "timestamp": log_entry.timestamp.isoformat(),
                    "level": log_entry.level,
                    "source": log_entry.source,
                    "message": log_entry.message,
                    "tags": log_entry.tags,
                }
                filtered_logs.append(log_dict)

            logger.info("Logs retrieved from database", count=len(filtered_logs))
            return filtered_logs

        except Exception as e:
            logger.error("Failed to get filtered logs", error=str(e))
            return []
