# Phase 5: Monitoring & Logs - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Built-in dashboard showing server health, app status, and activity logs. API available for integrations.

**Architecture:** Monitoring service polls servers via SSH for metrics, stores time-series data in SQLite. Activity log tracks user actions and system events. MCP tools expose data, JSON API for external integrations.

**Tech Stack:** Python (Paramiko for SSH, SQLite for storage), structured logging

---

## Task 1: Create Metrics and Activity Log Models

**Files:**
- Create: `backend/src/models/metrics.py`
- Create: `backend/src/init_db/schema_metrics.py`
- Test: `backend/tests/unit/test_metrics_models.py`

**Step 1: Write the failing test**

Create `backend/tests/unit/test_metrics_models.py`:

```python
"""Tests for metrics and activity log models."""
import pytest
from models.metrics import (
    MetricType,
    ActivityType,
    ServerMetrics,
    ContainerMetrics,
    ActivityLog,
    DashboardSummary
)


class TestMetricsModels:
    """Tests for metrics data models."""

    def test_metric_type_enum(self):
        """Should have correct metric types."""
        assert MetricType.CPU.value == "cpu"
        assert MetricType.MEMORY.value == "memory"
        assert MetricType.DISK.value == "disk"
        assert MetricType.NETWORK.value == "network"

    def test_activity_type_enum(self):
        """Should have correct activity types."""
        assert ActivityType.USER_LOGIN.value == "user_login"
        assert ActivityType.USER_LOGOUT.value == "user_logout"
        assert ActivityType.SERVER_ADDED.value == "server_added"
        assert ActivityType.APP_INSTALLED.value == "app_installed"
        assert ActivityType.APP_STARTED.value == "app_started"
        assert ActivityType.PREPARATION_COMPLETE.value == "preparation_complete"

    def test_server_metrics_model(self):
        """Should create valid server metrics."""
        metrics = ServerMetrics(
            id="metric-123",
            server_id="server-456",
            cpu_percent=45.5,
            memory_percent=62.3,
            memory_used_mb=4096,
            memory_total_mb=8192,
            disk_percent=78.0,
            disk_used_gb=156,
            disk_total_gb=200,
            network_rx_bytes=1024000,
            network_tx_bytes=512000,
            timestamp="2025-01-01T00:00:00Z"
        )
        assert metrics.cpu_percent == 45.5
        assert metrics.memory_percent == 62.3

    def test_container_metrics_model(self):
        """Should create valid container metrics."""
        metrics = ContainerMetrics(
            id="cmetric-123",
            server_id="server-456",
            container_id="abc123",
            container_name="portainer",
            cpu_percent=12.5,
            memory_usage_mb=256,
            memory_limit_mb=512,
            status="running",
            timestamp="2025-01-01T00:00:00Z"
        )
        assert metrics.container_name == "portainer"
        assert metrics.status == "running"

    def test_activity_log_model(self):
        """Should create valid activity log."""
        log = ActivityLog(
            id="log-123",
            activity_type=ActivityType.USER_LOGIN,
            user_id="user-456",
            server_id=None,
            app_id=None,
            message="User admin logged in",
            details={"ip": "192.168.1.1"},
            timestamp="2025-01-01T00:00:00Z"
        )
        assert log.activity_type == ActivityType.USER_LOGIN
        assert log.user_id == "user-456"

    def test_dashboard_summary_model(self):
        """Should create valid dashboard summary."""
        summary = DashboardSummary(
            total_servers=5,
            online_servers=4,
            offline_servers=1,
            total_apps=12,
            running_apps=10,
            stopped_apps=2,
            avg_cpu_percent=35.0,
            avg_memory_percent=55.0,
            recent_activities=[]
        )
        assert summary.total_servers == 5
        assert summary.running_apps == 10
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/christophebabilotte/source/tomo/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && PYTHONPATH=src pytest tests/unit/test_metrics_models.py -v --no-cov
```

Expected: FAIL - `ModuleNotFoundError: No module named 'models.metrics'`

**Step 3: Create metrics models**

Create `backend/src/models/metrics.py`:

```python
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
```

**Step 4: Create database schema**

Create `backend/src/init_db/schema_metrics.py`:

```python
"""Metrics and activity log database schema."""

METRICS_SCHEMA = """
CREATE TABLE IF NOT EXISTS server_metrics (
    id TEXT PRIMARY KEY,
    server_id TEXT NOT NULL,
    cpu_percent REAL NOT NULL,
    memory_percent REAL NOT NULL,
    memory_used_mb INTEGER NOT NULL,
    memory_total_mb INTEGER NOT NULL,
    disk_percent REAL NOT NULL,
    disk_used_gb INTEGER NOT NULL,
    disk_total_gb INTEGER NOT NULL,
    network_rx_bytes INTEGER DEFAULT 0,
    network_tx_bytes INTEGER DEFAULT 0,
    load_average_1m REAL,
    load_average_5m REAL,
    load_average_15m REAL,
    uptime_seconds INTEGER,
    timestamp TEXT NOT NULL,
    FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS container_metrics (
    id TEXT PRIMARY KEY,
    server_id TEXT NOT NULL,
    container_id TEXT NOT NULL,
    container_name TEXT NOT NULL,
    cpu_percent REAL NOT NULL,
    memory_usage_mb INTEGER NOT NULL,
    memory_limit_mb INTEGER NOT NULL,
    network_rx_bytes INTEGER DEFAULT 0,
    network_tx_bytes INTEGER DEFAULT 0,
    status TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS activity_logs (
    id TEXT PRIMARY KEY,
    activity_type TEXT NOT NULL,
    user_id TEXT,
    server_id TEXT,
    app_id TEXT,
    message TEXT NOT NULL,
    details TEXT,
    timestamp TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_server_metrics_server ON server_metrics(server_id);
CREATE INDEX IF NOT EXISTS idx_server_metrics_timestamp ON server_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_container_metrics_server ON container_metrics(server_id);
CREATE INDEX IF NOT EXISTS idx_container_metrics_timestamp ON container_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_activity_logs_type ON activity_logs(activity_type);
CREATE INDEX IF NOT EXISTS idx_activity_logs_timestamp ON activity_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_activity_logs_user ON activity_logs(user_id);
"""


def get_metrics_schema() -> str:
    """Return metrics schema SQL."""
    return METRICS_SCHEMA
```

**Step 5: Run test to verify it passes**

```bash
cd /Users/christophebabilotte/source/tomo/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && PYTHONPATH=src pytest tests/unit/test_metrics_models.py -v --no-cov
```

Expected: PASS

**Step 6: Commit**

```bash
git add backend/src/models/metrics.py backend/src/init_db/schema_metrics.py backend/tests/unit/test_metrics_models.py
git commit -m "feat(metrics): add metrics and activity log models"
```

---

## Task 2: Create Metrics Collection Service

**Files:**
- Create: `backend/src/services/metrics_service.py`
- Test: `backend/tests/unit/test_metrics_service.py`

**Step 1: Write the failing test**

Create `backend/tests/unit/test_metrics_service.py`:

```python
"""Tests for metrics collection service."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from services.metrics_service import MetricsService


class TestMetricsService:
    """Tests for MetricsService."""

    @pytest.fixture
    def mock_ssh_service(self):
        """Create mock SSH service."""
        ssh = MagicMock()
        ssh.execute_command = AsyncMock()
        return ssh

    @pytest.fixture
    def mock_db_service(self):
        """Create mock database service."""
        db = MagicMock()
        db.save_server_metrics = AsyncMock()
        db.save_container_metrics = AsyncMock()
        db.get_server_metrics = AsyncMock(return_value=[])
        db.get_container_metrics = AsyncMock(return_value=[])
        return db

    @pytest.fixture
    def mock_server_service(self):
        """Create mock server service."""
        svc = MagicMock()
        svc.list_servers = AsyncMock(return_value=[])
        return svc

    @pytest.fixture
    def metrics_service(self, mock_ssh_service, mock_db_service, mock_server_service):
        """Create metrics service with mocks."""
        return MetricsService(
            ssh_service=mock_ssh_service,
            db_service=mock_db_service,
            server_service=mock_server_service
        )

    def test_parse_cpu_output(self, metrics_service):
        """Should parse CPU usage from top command."""
        output = "top - 10:00:00 up 5 days, %Cpu(s): 25.5 us, 10.2 sy"
        result = metrics_service._parse_cpu_percent(output)
        assert result == pytest.approx(35.7, rel=0.1)

    def test_parse_memory_output(self, metrics_service):
        """Should parse memory usage from free command."""
        output = """              total        used        free
Mem:        8192000     4096000     2048000"""
        used, total, percent = metrics_service._parse_memory(output)
        assert total == 8192000
        assert used == 4096000
        assert percent == pytest.approx(50.0, rel=0.1)

    def test_parse_disk_output(self, metrics_service):
        """Should parse disk usage from df command."""
        output = """/dev/sda1      200G  156G   44G  78% /"""
        used, total, percent = metrics_service._parse_disk(output)
        assert total == 200
        assert used == 156
        assert percent == 78.0

    def test_parse_docker_stats(self, metrics_service):
        """Should parse docker stats output."""
        output = """abc123|portainer|12.5%|256MiB / 512MiB|1024|2048|running"""
        containers = metrics_service._parse_docker_stats(output)
        assert len(containers) == 1
        assert containers[0]["name"] == "portainer"
        assert containers[0]["cpu_percent"] == 12.5

    @pytest.mark.asyncio
    async def test_collect_server_metrics(self, metrics_service, mock_ssh_service, mock_db_service):
        """Should collect and save server metrics."""
        mock_ssh_service.execute_command.side_effect = [
            (0, "%Cpu(s): 25.0 us, 10.0 sy", ""),  # CPU
            (0, "Mem: 8192000 4096000 2048000", ""),  # Memory
            (0, "/dev/sda1 200G 156G 44G 78% /", ""),  # Disk
        ]

        result = await metrics_service.collect_server_metrics("server-123")

        assert result is not None
        mock_db_service.save_server_metrics.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_server_metrics_with_period(self, metrics_service, mock_db_service):
        """Should get metrics for specified period."""
        mock_db_service.get_server_metrics.return_value = [
            MagicMock(cpu_percent=30.0, memory_percent=50.0)
        ]

        result = await metrics_service.get_server_metrics("server-123", period="24h")

        assert result is not None
        mock_db_service.get_server_metrics.assert_called_once()
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/christophebabilotte/source/tomo/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && PYTHONPATH=src pytest tests/unit/test_metrics_service.py -v --no-cov
```

Expected: FAIL

**Step 3: Create metrics service**

Create `backend/src/services/metrics_service.py`:

```python
"""
Metrics Collection Service

Collects server and container metrics via SSH.
"""

import re
import uuid
from datetime import datetime, UTC, timedelta
from typing import Dict, Any, Optional, List
import structlog
from models.metrics import ServerMetrics, ContainerMetrics, MetricType

logger = structlog.get_logger("metrics_service")


# Period to timedelta mapping
PERIOD_MAP = {
    "1h": timedelta(hours=1),
    "24h": timedelta(hours=24),
    "7d": timedelta(days=7),
    "30d": timedelta(days=30),
}


class MetricsService:
    """Service for collecting and managing metrics."""

    def __init__(self, ssh_service, db_service, server_service):
        """Initialize metrics service."""
        self.ssh_service = ssh_service
        self.db_service = db_service
        self.server_service = server_service
        logger.info("Metrics service initialized")

    def _parse_cpu_percent(self, output: str) -> float:
        """Parse CPU usage from top/mpstat output."""
        try:
            # Match patterns like "25.5 us, 10.2 sy" or "25.5%us"
            match = re.search(r'(\d+\.?\d*)\s*(?:%\s*)?us.*?(\d+\.?\d*)\s*(?:%\s*)?sy', output)
            if match:
                user = float(match.group(1))
                system = float(match.group(2))
                return user + system

            # Alternative: match single CPU percentage
            match = re.search(r'(\d+\.?\d*)%?\s*(?:cpu|CPU)', output)
            if match:
                return float(match.group(1))

            return 0.0
        except Exception as e:
            logger.error("Failed to parse CPU", error=str(e))
            return 0.0

    def _parse_memory(self, output: str) -> tuple:
        """Parse memory from free command output."""
        try:
            lines = output.strip().split('\n')
            for line in lines:
                if line.startswith('Mem:'):
                    parts = line.split()
                    total = int(parts[1])
                    used = int(parts[2])
                    percent = (used / total) * 100 if total > 0 else 0
                    return used, total, percent
            return 0, 0, 0.0
        except Exception as e:
            logger.error("Failed to parse memory", error=str(e))
            return 0, 0, 0.0

    def _parse_disk(self, output: str) -> tuple:
        """Parse disk usage from df command output."""
        try:
            lines = output.strip().split('\n')
            for line in lines:
                if '/' in line and not line.startswith('Filesystem'):
                    parts = line.split()
                    # Parse size (e.g., "200G")
                    total_str = parts[1]
                    used_str = parts[2]
                    percent_str = parts[4].replace('%', '')

                    total = int(re.sub(r'[^\d]', '', total_str))
                    used = int(re.sub(r'[^\d]', '', used_str))
                    percent = float(percent_str)

                    return used, total, percent
            return 0, 0, 0.0
        except Exception as e:
            logger.error("Failed to parse disk", error=str(e))
            return 0, 0, 0.0

    def _parse_docker_stats(self, output: str) -> List[Dict[str, Any]]:
        """Parse docker stats output."""
        containers = []
        try:
            for line in output.strip().split('\n'):
                if not line:
                    continue
                parts = line.split('|')
                if len(parts) >= 7:
                    # Parse memory like "256MiB / 512MiB"
                    mem_parts = parts[3].split('/')
                    mem_used = int(re.sub(r'[^\d]', '', mem_parts[0]))
                    mem_limit = int(re.sub(r'[^\d]', '', mem_parts[1])) if len(mem_parts) > 1 else 0

                    containers.append({
                        "container_id": parts[0].strip(),
                        "name": parts[1].strip(),
                        "cpu_percent": float(parts[2].replace('%', '').strip()),
                        "memory_usage_mb": mem_used,
                        "memory_limit_mb": mem_limit,
                        "network_rx": int(parts[4]) if parts[4].isdigit() else 0,
                        "network_tx": int(parts[5]) if parts[5].isdigit() else 0,
                        "status": parts[6].strip()
                    })
        except Exception as e:
            logger.error("Failed to parse docker stats", error=str(e))
        return containers

    async def collect_server_metrics(self, server_id: str) -> Optional[ServerMetrics]:
        """Collect current metrics from a server."""
        try:
            # Collect CPU
            exit_code, cpu_out, _ = await self.ssh_service.execute_command(
                server_id,
                "top -bn1 | head -5"
            )
            cpu_percent = self._parse_cpu_percent(cpu_out) if exit_code == 0 else 0.0

            # Collect Memory
            exit_code, mem_out, _ = await self.ssh_service.execute_command(
                server_id,
                "free -k | grep -E '^Mem:'"
            )
            mem_used, mem_total, mem_percent = self._parse_memory(mem_out) if exit_code == 0 else (0, 0, 0.0)

            # Collect Disk
            exit_code, disk_out, _ = await self.ssh_service.execute_command(
                server_id,
                "df -h / | tail -1"
            )
            disk_used, disk_total, disk_percent = self._parse_disk(disk_out) if exit_code == 0 else (0, 0, 0.0)

            metrics = ServerMetrics(
                id=f"sm-{uuid.uuid4().hex[:8]}",
                server_id=server_id,
                cpu_percent=cpu_percent,
                memory_percent=mem_percent,
                memory_used_mb=mem_used // 1024,  # Convert KB to MB
                memory_total_mb=mem_total // 1024,
                disk_percent=disk_percent,
                disk_used_gb=disk_used,
                disk_total_gb=disk_total,
                timestamp=datetime.now(UTC).isoformat()
            )

            await self.db_service.save_server_metrics(metrics)
            logger.debug("Collected server metrics", server_id=server_id)
            return metrics

        except Exception as e:
            logger.error("Failed to collect metrics", server_id=server_id, error=str(e))
            return None

    async def collect_container_metrics(self, server_id: str) -> List[ContainerMetrics]:
        """Collect metrics for all containers on a server."""
        try:
            # Get docker stats in parseable format
            cmd = 'docker stats --no-stream --format "{{.ID}}|{{.Name}}|{{.CPUPerc}}|{{.MemUsage}}|{{.NetIO}}|{{.Status}}"'
            exit_code, output, _ = await self.ssh_service.execute_command(server_id, cmd)

            if exit_code != 0:
                return []

            containers = self._parse_docker_stats(output)
            results = []

            for c in containers:
                metrics = ContainerMetrics(
                    id=f"cm-{uuid.uuid4().hex[:8]}",
                    server_id=server_id,
                    container_id=c["container_id"],
                    container_name=c["name"],
                    cpu_percent=c["cpu_percent"],
                    memory_usage_mb=c["memory_usage_mb"],
                    memory_limit_mb=c["memory_limit_mb"],
                    network_rx_bytes=c["network_rx"],
                    network_tx_bytes=c["network_tx"],
                    status=c["status"],
                    timestamp=datetime.now(UTC).isoformat()
                )
                await self.db_service.save_container_metrics(metrics)
                results.append(metrics)

            return results

        except Exception as e:
            logger.error("Failed to collect container metrics", error=str(e))
            return []

    async def get_server_metrics(
        self,
        server_id: str,
        period: str = "24h"
    ) -> List[ServerMetrics]:
        """Get historical metrics for a server."""
        try:
            delta = PERIOD_MAP.get(period, timedelta(hours=24))
            since = datetime.now(UTC) - delta

            return await self.db_service.get_server_metrics(
                server_id=server_id,
                since=since.isoformat()
            )
        except Exception as e:
            logger.error("Failed to get server metrics", error=str(e))
            return []

    async def get_container_metrics(
        self,
        server_id: str,
        container_name: str = None,
        period: str = "24h"
    ) -> List[ContainerMetrics]:
        """Get historical container metrics."""
        try:
            delta = PERIOD_MAP.get(period, timedelta(hours=24))
            since = datetime.now(UTC) - delta

            return await self.db_service.get_container_metrics(
                server_id=server_id,
                container_name=container_name,
                since=since.isoformat()
            )
        except Exception as e:
            logger.error("Failed to get container metrics", error=str(e))
            return []
```

**Step 4: Run test to verify it passes**

```bash
cd /Users/christophebabilotte/source/tomo/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && PYTHONPATH=src pytest tests/unit/test_metrics_service.py -v --no-cov
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/services/metrics_service.py backend/tests/unit/test_metrics_service.py
git commit -m "feat(metrics): add metrics collection service"
```

---

## Task 3: Create Activity Log Service

**Files:**
- Create: `backend/src/services/activity_service.py`
- Test: `backend/tests/unit/test_activity_service.py`

**Step 1: Write the failing test**

Create `backend/tests/unit/test_activity_service.py`:

```python
"""Tests for activity log service."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from services.activity_service import ActivityService
from models.metrics import ActivityType


class TestActivityService:
    """Tests for ActivityService."""

    @pytest.fixture
    def mock_db_service(self):
        """Create mock database service."""
        db = MagicMock()
        db.save_activity_log = AsyncMock()
        db.get_activity_logs = AsyncMock(return_value=[])
        return db

    @pytest.fixture
    def activity_service(self, mock_db_service):
        """Create activity service with mocks."""
        return ActivityService(db_service=mock_db_service)

    @pytest.mark.asyncio
    async def test_log_user_login(self, activity_service, mock_db_service):
        """Should log user login activity."""
        await activity_service.log_activity(
            activity_type=ActivityType.USER_LOGIN,
            user_id="user-123",
            message="User admin logged in"
        )

        mock_db_service.save_activity_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_log_server_added(self, activity_service, mock_db_service):
        """Should log server added activity."""
        await activity_service.log_activity(
            activity_type=ActivityType.SERVER_ADDED,
            user_id="user-123",
            server_id="server-456",
            message="Server 'web-01' added"
        )

        mock_db_service.save_activity_log.assert_called_once()
        call_args = mock_db_service.save_activity_log.call_args[0][0]
        assert call_args.server_id == "server-456"

    @pytest.mark.asyncio
    async def test_log_app_installed(self, activity_service, mock_db_service):
        """Should log app installation activity."""
        await activity_service.log_activity(
            activity_type=ActivityType.APP_INSTALLED,
            user_id="user-123",
            server_id="server-456",
            app_id="portainer",
            message="Portainer installed on server web-01"
        )

        mock_db_service.save_activity_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_recent_activities(self, activity_service, mock_db_service):
        """Should get recent activities."""
        mock_db_service.get_activity_logs.return_value = [
            MagicMock(activity_type=ActivityType.USER_LOGIN, message="Login")
        ]

        result = await activity_service.get_recent_activities(limit=10)

        assert len(result) == 1
        mock_db_service.get_activity_logs.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_activities_filtered(self, activity_service, mock_db_service):
        """Should filter activities by type."""
        await activity_service.get_activities(
            activity_types=[ActivityType.USER_LOGIN, ActivityType.USER_LOGOUT],
            limit=50
        )

        mock_db_service.get_activity_logs.assert_called_once()
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/christophebabilotte/source/tomo/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && PYTHONPATH=src pytest tests/unit/test_activity_service.py -v --no-cov
```

Expected: FAIL

**Step 3: Create activity service**

Create `backend/src/services/activity_service.py`:

```python
"""
Activity Log Service

Tracks user actions and system events.
"""

import uuid
from datetime import datetime, UTC
from typing import Dict, Any, Optional, List
import structlog
from models.metrics import ActivityLog, ActivityType

logger = structlog.get_logger("activity_service")


class ActivityService:
    """Service for logging and querying activities."""

    def __init__(self, db_service):
        """Initialize activity service."""
        self.db_service = db_service
        logger.info("Activity service initialized")

    async def log_activity(
        self,
        activity_type: ActivityType,
        message: str,
        user_id: str = None,
        server_id: str = None,
        app_id: str = None,
        details: Dict[str, Any] = None
    ) -> ActivityLog:
        """Log an activity event."""
        try:
            log_entry = ActivityLog(
                id=f"act-{uuid.uuid4().hex[:8]}",
                activity_type=activity_type,
                user_id=user_id,
                server_id=server_id,
                app_id=app_id,
                message=message,
                details=details or {},
                timestamp=datetime.now(UTC).isoformat()
            )

            await self.db_service.save_activity_log(log_entry)
            logger.info(
                "Activity logged",
                type=activity_type.value,
                message=message
            )
            return log_entry

        except Exception as e:
            logger.error("Failed to log activity", error=str(e))
            raise

    async def get_recent_activities(self, limit: int = 20) -> List[ActivityLog]:
        """Get most recent activities."""
        try:
            return await self.db_service.get_activity_logs(limit=limit)
        except Exception as e:
            logger.error("Failed to get recent activities", error=str(e))
            return []

    async def get_activities(
        self,
        activity_types: List[ActivityType] = None,
        user_id: str = None,
        server_id: str = None,
        since: str = None,
        until: str = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[ActivityLog]:
        """Get activities with filters."""
        try:
            type_values = [t.value for t in activity_types] if activity_types else None

            return await self.db_service.get_activity_logs(
                activity_types=type_values,
                user_id=user_id,
                server_id=server_id,
                since=since,
                until=until,
                limit=limit,
                offset=offset
            )
        except Exception as e:
            logger.error("Failed to get activities", error=str(e))
            return []

    async def get_activity_count(
        self,
        activity_types: List[ActivityType] = None,
        since: str = None
    ) -> int:
        """Get count of activities matching filters."""
        try:
            type_values = [t.value for t in activity_types] if activity_types else None
            return await self.db_service.count_activity_logs(
                activity_types=type_values,
                since=since
            )
        except Exception as e:
            logger.error("Failed to count activities", error=str(e))
            return 0
```

**Step 4: Run test to verify it passes**

```bash
cd /Users/christophebabilotte/source/tomo/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && PYTHONPATH=src pytest tests/unit/test_activity_service.py -v --no-cov
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/services/activity_service.py backend/tests/unit/test_activity_service.py
git commit -m "feat(metrics): add activity log service"
```

---

## Task 4: Add Metrics Database Methods

**Files:**
- Modify: `backend/src/services/database_service.py`
- Test: `backend/tests/unit/test_metrics_database.py`

**Step 1: Write the failing test**

Create `backend/tests/unit/test_metrics_database.py`:

```python
"""Tests for metrics database operations."""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from contextlib import asynccontextmanager


class TestMetricsDatabaseOperations:
    """Tests for metrics CRUD in database."""

    @pytest.fixture
    def mock_connection(self):
        """Create mock database connection."""
        conn = MagicMock()
        conn.execute = AsyncMock()
        conn.commit = AsyncMock()
        return conn

    @pytest.fixture
    def db_service(self, mock_connection):
        """Create database service with mocked connection."""
        from services.database_service import DatabaseService

        @asynccontextmanager
        async def mock_get_connection():
            yield mock_connection

        with patch.object(DatabaseService, 'get_connection', mock_get_connection):
            service = DatabaseService(data_directory="/tmp/test")
            service._mock_conn = mock_connection
            return service

    @pytest.mark.asyncio
    async def test_save_server_metrics(self, db_service, mock_connection):
        """Should save server metrics."""
        from models.metrics import ServerMetrics

        metrics = ServerMetrics(
            id="sm-123",
            server_id="server-456",
            cpu_percent=45.5,
            memory_percent=62.3,
            memory_used_mb=4096,
            memory_total_mb=8192,
            disk_percent=78.0,
            disk_used_gb=156,
            disk_total_gb=200,
            timestamp="2025-01-01T00:00:00Z"
        )

        result = await db_service.save_server_metrics(metrics)

        assert result is True
        mock_connection.execute.assert_called()

    @pytest.mark.asyncio
    async def test_save_container_metrics(self, db_service, mock_connection):
        """Should save container metrics."""
        from models.metrics import ContainerMetrics

        metrics = ContainerMetrics(
            id="cm-123",
            server_id="server-456",
            container_id="abc123",
            container_name="portainer",
            cpu_percent=12.5,
            memory_usage_mb=256,
            memory_limit_mb=512,
            status="running",
            timestamp="2025-01-01T00:00:00Z"
        )

        result = await db_service.save_container_metrics(metrics)

        assert result is True

    @pytest.mark.asyncio
    async def test_save_activity_log(self, db_service, mock_connection):
        """Should save activity log."""
        from models.metrics import ActivityLog, ActivityType

        log = ActivityLog(
            id="act-123",
            activity_type=ActivityType.USER_LOGIN,
            user_id="user-456",
            message="User logged in",
            details={},
            timestamp="2025-01-01T00:00:00Z"
        )

        result = await db_service.save_activity_log(log)

        assert result is True

    @pytest.mark.asyncio
    async def test_get_server_metrics(self, db_service, mock_connection):
        """Should get server metrics."""
        mock_rows = [
            {"id": "sm-1", "server_id": "server-456", "cpu_percent": 45.5,
             "memory_percent": 62.3, "memory_used_mb": 4096, "memory_total_mb": 8192,
             "disk_percent": 78.0, "disk_used_gb": 156, "disk_total_gb": 200,
             "network_rx_bytes": 0, "network_tx_bytes": 0, "load_average_1m": None,
             "load_average_5m": None, "load_average_15m": None, "uptime_seconds": None,
             "timestamp": "2025-01-01T00:00:00Z"}
        ]
        mock_connection.execute.return_value = MagicMock(
            fetchall=AsyncMock(return_value=mock_rows)
        )

        result = await db_service.get_server_metrics("server-456")

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_activity_logs(self, db_service, mock_connection):
        """Should get activity logs."""
        mock_rows = [
            {"id": "act-1", "activity_type": "user_login", "user_id": "user-456",
             "server_id": None, "app_id": None, "message": "Login",
             "details": "{}", "timestamp": "2025-01-01T00:00:00Z"}
        ]
        mock_connection.execute.return_value = MagicMock(
            fetchall=AsyncMock(return_value=mock_rows)
        )

        result = await db_service.get_activity_logs(limit=10)

        assert len(result) == 1
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/christophebabilotte/source/tomo/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && PYTHONPATH=src pytest tests/unit/test_metrics_database.py -v --no-cov
```

Expected: FAIL

**Step 3: Add database methods to database_service.py**

Add to `backend/src/services/database_service.py`:

```python
# Add imports at top
from models.metrics import ServerMetrics, ContainerMetrics, ActivityLog, ActivityType
import json

async def save_server_metrics(self, metrics: ServerMetrics) -> bool:
    """Save server metrics to database."""
    try:
        async with self.get_connection() as conn:
            await conn.execute(
                """INSERT INTO server_metrics
                   (id, server_id, cpu_percent, memory_percent, memory_used_mb,
                    memory_total_mb, disk_percent, disk_used_gb, disk_total_gb,
                    network_rx_bytes, network_tx_bytes, load_average_1m,
                    load_average_5m, load_average_15m, uptime_seconds, timestamp)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (metrics.id, metrics.server_id, metrics.cpu_percent,
                 metrics.memory_percent, metrics.memory_used_mb, metrics.memory_total_mb,
                 metrics.disk_percent, metrics.disk_used_gb, metrics.disk_total_gb,
                 metrics.network_rx_bytes, metrics.network_tx_bytes,
                 metrics.load_average_1m, metrics.load_average_5m,
                 metrics.load_average_15m, metrics.uptime_seconds, metrics.timestamp)
            )
            await conn.commit()
        return True
    except Exception as e:
        logger.error("Failed to save server metrics", error=str(e))
        return False

async def save_container_metrics(self, metrics: ContainerMetrics) -> bool:
    """Save container metrics to database."""
    try:
        async with self.get_connection() as conn:
            await conn.execute(
                """INSERT INTO container_metrics
                   (id, server_id, container_id, container_name, cpu_percent,
                    memory_usage_mb, memory_limit_mb, network_rx_bytes,
                    network_tx_bytes, status, timestamp)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (metrics.id, metrics.server_id, metrics.container_id,
                 metrics.container_name, metrics.cpu_percent,
                 metrics.memory_usage_mb, metrics.memory_limit_mb,
                 metrics.network_rx_bytes, metrics.network_tx_bytes,
                 metrics.status, metrics.timestamp)
            )
            await conn.commit()
        return True
    except Exception as e:
        logger.error("Failed to save container metrics", error=str(e))
        return False

async def save_activity_log(self, log: ActivityLog) -> bool:
    """Save activity log to database."""
    try:
        details_json = json.dumps(log.details) if log.details else "{}"
        async with self.get_connection() as conn:
            await conn.execute(
                """INSERT INTO activity_logs
                   (id, activity_type, user_id, server_id, app_id, message, details, timestamp)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (log.id, log.activity_type.value, log.user_id, log.server_id,
                 log.app_id, log.message, details_json, log.timestamp)
            )
            await conn.commit()
        return True
    except Exception as e:
        logger.error("Failed to save activity log", error=str(e))
        return False

async def get_server_metrics(
    self,
    server_id: str,
    since: str = None,
    limit: int = 100
) -> list:
    """Get server metrics from database."""
    try:
        query = "SELECT * FROM server_metrics WHERE server_id = ?"
        params = [server_id]

        if since:
            query += " AND timestamp >= ?"
            params.append(since)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        async with self.get_connection() as conn:
            cursor = await conn.execute(query, params)
            rows = await cursor.fetchall()

        return [
            ServerMetrics(
                id=row["id"],
                server_id=row["server_id"],
                cpu_percent=row["cpu_percent"],
                memory_percent=row["memory_percent"],
                memory_used_mb=row["memory_used_mb"],
                memory_total_mb=row["memory_total_mb"],
                disk_percent=row["disk_percent"],
                disk_used_gb=row["disk_used_gb"],
                disk_total_gb=row["disk_total_gb"],
                network_rx_bytes=row["network_rx_bytes"],
                network_tx_bytes=row["network_tx_bytes"],
                load_average_1m=row["load_average_1m"],
                load_average_5m=row["load_average_5m"],
                load_average_15m=row["load_average_15m"],
                uptime_seconds=row["uptime_seconds"],
                timestamp=row["timestamp"]
            )
            for row in rows
        ]
    except Exception as e:
        logger.error("Failed to get server metrics", error=str(e))
        return []

async def get_container_metrics(
    self,
    server_id: str,
    container_name: str = None,
    since: str = None,
    limit: int = 100
) -> list:
    """Get container metrics from database."""
    try:
        query = "SELECT * FROM container_metrics WHERE server_id = ?"
        params = [server_id]

        if container_name:
            query += " AND container_name = ?"
            params.append(container_name)

        if since:
            query += " AND timestamp >= ?"
            params.append(since)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        async with self.get_connection() as conn:
            cursor = await conn.execute(query, params)
            rows = await cursor.fetchall()

        return [
            ContainerMetrics(
                id=row["id"],
                server_id=row["server_id"],
                container_id=row["container_id"],
                container_name=row["container_name"],
                cpu_percent=row["cpu_percent"],
                memory_usage_mb=row["memory_usage_mb"],
                memory_limit_mb=row["memory_limit_mb"],
                network_rx_bytes=row["network_rx_bytes"],
                network_tx_bytes=row["network_tx_bytes"],
                status=row["status"],
                timestamp=row["timestamp"]
            )
            for row in rows
        ]
    except Exception as e:
        logger.error("Failed to get container metrics", error=str(e))
        return []

async def get_activity_logs(
    self,
    activity_types: list = None,
    user_id: str = None,
    server_id: str = None,
    since: str = None,
    until: str = None,
    limit: int = 100,
    offset: int = 0
) -> list:
    """Get activity logs from database."""
    try:
        query = "SELECT * FROM activity_logs WHERE 1=1"
        params = []

        if activity_types:
            placeholders = ",".join("?" * len(activity_types))
            query += f" AND activity_type IN ({placeholders})"
            params.extend(activity_types)

        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)

        if server_id:
            query += " AND server_id = ?"
            params.append(server_id)

        if since:
            query += " AND timestamp >= ?"
            params.append(since)

        if until:
            query += " AND timestamp <= ?"
            params.append(until)

        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        async with self.get_connection() as conn:
            cursor = await conn.execute(query, params)
            rows = await cursor.fetchall()

        return [
            ActivityLog(
                id=row["id"],
                activity_type=ActivityType(row["activity_type"]),
                user_id=row["user_id"],
                server_id=row["server_id"],
                app_id=row["app_id"],
                message=row["message"],
                details=json.loads(row["details"]) if row["details"] else {},
                timestamp=row["timestamp"]
            )
            for row in rows
        ]
    except Exception as e:
        logger.error("Failed to get activity logs", error=str(e))
        return []

async def count_activity_logs(
    self,
    activity_types: list = None,
    since: str = None
) -> int:
    """Count activity logs matching filters."""
    try:
        query = "SELECT COUNT(*) as count FROM activity_logs WHERE 1=1"
        params = []

        if activity_types:
            placeholders = ",".join("?" * len(activity_types))
            query += f" AND activity_type IN ({placeholders})"
            params.extend(activity_types)

        if since:
            query += " AND timestamp >= ?"
            params.append(since)

        async with self.get_connection() as conn:
            cursor = await conn.execute(query, params)
            row = await cursor.fetchone()

        return row["count"] if row else 0
    except Exception as e:
        logger.error("Failed to count activity logs", error=str(e))
        return 0
```

**Step 4: Run test to verify it passes**

```bash
cd /Users/christophebabilotte/source/tomo/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && PYTHONPATH=src pytest tests/unit/test_metrics_database.py -v --no-cov
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/services/database_service.py backend/tests/unit/test_metrics_database.py
git commit -m "feat(metrics): add metrics database CRUD methods"
```

---

## Task 5: Create Dashboard Service

**Files:**
- Create: `backend/src/services/dashboard_service.py`
- Test: `backend/tests/unit/test_dashboard_service.py`

**Step 1: Write the failing test**

Create `backend/tests/unit/test_dashboard_service.py`:

```python
"""Tests for dashboard service."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from services.dashboard_service import DashboardService
from models.metrics import DashboardSummary


class TestDashboardService:
    """Tests for DashboardService."""

    @pytest.fixture
    def mock_server_service(self):
        """Create mock server service."""
        svc = MagicMock()
        svc.list_servers = AsyncMock(return_value=[])
        return svc

    @pytest.fixture
    def mock_deployment_service(self):
        """Create mock deployment service."""
        svc = MagicMock()
        svc.get_installed_apps = AsyncMock(return_value=[])
        return svc

    @pytest.fixture
    def mock_metrics_service(self):
        """Create mock metrics service."""
        svc = MagicMock()
        svc.get_server_metrics = AsyncMock(return_value=[])
        return svc

    @pytest.fixture
    def mock_activity_service(self):
        """Create mock activity service."""
        svc = MagicMock()
        svc.get_recent_activities = AsyncMock(return_value=[])
        return svc

    @pytest.fixture
    def dashboard_service(self, mock_server_service, mock_deployment_service,
                          mock_metrics_service, mock_activity_service):
        """Create dashboard service with mocks."""
        return DashboardService(
            server_service=mock_server_service,
            deployment_service=mock_deployment_service,
            metrics_service=mock_metrics_service,
            activity_service=mock_activity_service
        )

    @pytest.mark.asyncio
    async def test_get_dashboard_summary_empty(self, dashboard_service):
        """Should return empty summary when no data."""
        result = await dashboard_service.get_summary()

        assert isinstance(result, DashboardSummary)
        assert result.total_servers == 0
        assert result.total_apps == 0

    @pytest.mark.asyncio
    async def test_get_dashboard_summary_with_servers(self, dashboard_service, mock_server_service):
        """Should count servers correctly."""
        mock_server_service.list_servers.return_value = [
            MagicMock(id="s1", status="online"),
            MagicMock(id="s2", status="online"),
            MagicMock(id="s3", status="offline"),
        ]

        result = await dashboard_service.get_summary()

        assert result.total_servers == 3
        assert result.online_servers == 2
        assert result.offline_servers == 1

    @pytest.mark.asyncio
    async def test_get_dashboard_summary_with_apps(self, dashboard_service,
                                                    mock_server_service, mock_deployment_service):
        """Should count apps correctly."""
        mock_server_service.list_servers.return_value = [MagicMock(id="s1")]
        mock_deployment_service.get_installed_apps.return_value = [
            {"status": "running"},
            {"status": "running"},
            {"status": "stopped"},
        ]

        result = await dashboard_service.get_summary()

        assert result.total_apps == 3
        assert result.running_apps == 2
        assert result.stopped_apps == 1

    @pytest.mark.asyncio
    async def test_get_dashboard_summary_with_metrics(self, dashboard_service,
                                                       mock_server_service, mock_metrics_service):
        """Should calculate average metrics."""
        mock_server_service.list_servers.return_value = [
            MagicMock(id="s1"),
            MagicMock(id="s2")
        ]
        mock_metrics_service.get_server_metrics.side_effect = [
            [MagicMock(cpu_percent=30.0, memory_percent=50.0, disk_percent=60.0)],
            [MagicMock(cpu_percent=40.0, memory_percent=60.0, disk_percent=70.0)],
        ]

        result = await dashboard_service.get_summary()

        assert result.avg_cpu_percent == pytest.approx(35.0, rel=0.1)
        assert result.avg_memory_percent == pytest.approx(55.0, rel=0.1)
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/christophebabilotte/source/tomo/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && PYTHONPATH=src pytest tests/unit/test_dashboard_service.py -v --no-cov
```

Expected: FAIL

**Step 3: Create dashboard service**

Create `backend/src/services/dashboard_service.py`:

```python
"""
Dashboard Service

Aggregates data for dashboard display.
"""

from typing import List
import structlog
from models.metrics import DashboardSummary, ActivityLog

logger = structlog.get_logger("dashboard_service")


class DashboardService:
    """Service for dashboard data aggregation."""

    def __init__(self, server_service, deployment_service, metrics_service, activity_service):
        """Initialize dashboard service."""
        self.server_service = server_service
        self.deployment_service = deployment_service
        self.metrics_service = metrics_service
        self.activity_service = activity_service
        logger.info("Dashboard service initialized")

    async def get_summary(self) -> DashboardSummary:
        """Get aggregated dashboard summary."""
        try:
            # Get server counts
            servers = await self.server_service.list_servers()
            total_servers = len(servers)
            online_servers = sum(1 for s in servers if getattr(s, 'status', '') == 'online')
            offline_servers = total_servers - online_servers

            # Get app counts across all servers
            total_apps = 0
            running_apps = 0
            stopped_apps = 0
            error_apps = 0

            for server in servers:
                apps = await self.deployment_service.get_installed_apps(server.id)
                for app in apps:
                    total_apps += 1
                    status = app.get('status', '') if isinstance(app, dict) else getattr(app, 'status', '')
                    if status == 'running':
                        running_apps += 1
                    elif status == 'stopped':
                        stopped_apps += 1
                    elif status == 'error':
                        error_apps += 1

            # Calculate average metrics
            cpu_values = []
            memory_values = []
            disk_values = []

            for server in servers:
                metrics = await self.metrics_service.get_server_metrics(server.id, period="1h")
                if metrics:
                    latest = metrics[0]
                    cpu_values.append(latest.cpu_percent)
                    memory_values.append(latest.memory_percent)
                    disk_values.append(latest.disk_percent)

            avg_cpu = sum(cpu_values) / len(cpu_values) if cpu_values else 0.0
            avg_memory = sum(memory_values) / len(memory_values) if memory_values else 0.0
            avg_disk = sum(disk_values) / len(disk_values) if disk_values else 0.0

            # Get recent activities
            recent_activities = await self.activity_service.get_recent_activities(limit=10)

            return DashboardSummary(
                total_servers=total_servers,
                online_servers=online_servers,
                offline_servers=offline_servers,
                total_apps=total_apps,
                running_apps=running_apps,
                stopped_apps=stopped_apps,
                error_apps=error_apps,
                avg_cpu_percent=avg_cpu,
                avg_memory_percent=avg_memory,
                avg_disk_percent=avg_disk,
                recent_activities=recent_activities
            )

        except Exception as e:
            logger.error("Failed to get dashboard summary", error=str(e))
            return DashboardSummary()
```

**Step 4: Run test to verify it passes**

```bash
cd /Users/christophebabilotte/source/tomo/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && PYTHONPATH=src pytest tests/unit/test_dashboard_service.py -v --no-cov
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/services/dashboard_service.py backend/tests/unit/test_dashboard_service.py
git commit -m "feat(metrics): add dashboard aggregation service"
```

---

## Task 6: Create Monitoring MCP Tools

**Files:**
- Create: `backend/src/tools/metrics_tools.py`
- Test: `backend/tests/unit/test_metrics_tools.py`

**Step 1: Write the failing test**

Create `backend/tests/unit/test_metrics_tools.py`:

```python
"""Tests for metrics MCP tools."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from tools.metrics_tools import MetricsTools
from models.metrics import DashboardSummary


@pytest.fixture
def mock_metrics_service():
    """Create mock metrics service."""
    svc = MagicMock()
    svc.get_server_metrics = AsyncMock(return_value=[])
    svc.get_container_metrics = AsyncMock(return_value=[])
    svc.collect_server_metrics = AsyncMock()
    return svc


@pytest.fixture
def mock_activity_service():
    """Create mock activity service."""
    svc = MagicMock()
    svc.get_activities = AsyncMock(return_value=[])
    svc.get_activity_count = AsyncMock(return_value=0)
    return svc


@pytest.fixture
def mock_dashboard_service():
    """Create mock dashboard service."""
    svc = MagicMock()
    svc.get_summary = AsyncMock(return_value=DashboardSummary())
    return svc


@pytest.fixture
def metrics_tools(mock_metrics_service, mock_activity_service, mock_dashboard_service):
    """Create metrics tools with mocks."""
    return MetricsTools(
        metrics_service=mock_metrics_service,
        activity_service=mock_activity_service,
        dashboard_service=mock_dashboard_service
    )


class TestGetServerMetrics:
    """Tests for get_server_metrics tool."""

    @pytest.mark.asyncio
    async def test_get_metrics_success(self, metrics_tools, mock_metrics_service):
        """Should return server metrics."""
        mock_metrics_service.get_server_metrics.return_value = [
            MagicMock(cpu_percent=45.0, memory_percent=60.0,
                     model_dump=lambda: {"cpu_percent": 45.0})
        ]

        result = await metrics_tools.get_server_metrics(
            server_id="server-123",
            period="24h"
        )

        assert result["success"] is True
        assert len(result["data"]["metrics"]) == 1


class TestGetActivityLogs:
    """Tests for get_activity_logs tool."""

    @pytest.mark.asyncio
    async def test_get_logs_success(self, metrics_tools, mock_activity_service):
        """Should return activity logs."""
        mock_activity_service.get_activities.return_value = [
            MagicMock(activity_type="user_login", message="Login",
                     model_dump=lambda: {"type": "user_login"})
        ]
        mock_activity_service.get_activity_count.return_value = 1

        result = await metrics_tools.get_activity_logs(limit=50)

        assert result["success"] is True


class TestGetDashboardSummary:
    """Tests for get_dashboard_summary tool."""

    @pytest.mark.asyncio
    async def test_get_summary_success(self, metrics_tools, mock_dashboard_service):
        """Should return dashboard summary."""
        mock_dashboard_service.get_summary.return_value = DashboardSummary(
            total_servers=5,
            online_servers=4,
            running_apps=10
        )

        result = await metrics_tools.get_dashboard_summary()

        assert result["success"] is True
        assert result["data"]["total_servers"] == 5
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/christophebabilotte/source/tomo/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && PYTHONPATH=src pytest tests/unit/test_metrics_tools.py -v --no-cov
```

Expected: FAIL

**Step 3: Create metrics tools**

Create `backend/src/tools/metrics_tools.py`:

```python
"""
Monitoring and Metrics MCP Tools

Provides MCP tools for server metrics, activity logs, and dashboard.
"""

from typing import Dict, Any, List
import structlog
from fastmcp import FastMCP
from services.metrics_service import MetricsService
from services.activity_service import ActivityService
from services.dashboard_service import DashboardService
from models.metrics import ActivityType

logger = structlog.get_logger("metrics_tools")


class MetricsTools:
    """Metrics tools for the MCP server."""

    def __init__(self, metrics_service: MetricsService,
                 activity_service: ActivityService,
                 dashboard_service: DashboardService):
        """Initialize metrics tools."""
        self.metrics_service = metrics_service
        self.activity_service = activity_service
        self.dashboard_service = dashboard_service
        logger.info("Metrics tools initialized")

    async def get_server_metrics(
        self,
        server_id: str,
        period: str = "24h"
    ) -> Dict[str, Any]:
        """Get server metrics for a time period."""
        try:
            metrics = await self.metrics_service.get_server_metrics(server_id, period)

            return {
                "success": True,
                "data": {
                    "server_id": server_id,
                    "period": period,
                    "metrics": [m.model_dump() for m in metrics],
                    "count": len(metrics)
                },
                "message": f"Retrieved {len(metrics)} metric records"
            }
        except Exception as e:
            logger.error("Get server metrics error", error=str(e))
            return {
                "success": False,
                "message": f"Failed to get metrics: {str(e)}",
                "error": "GET_METRICS_ERROR"
            }

    async def get_app_metrics(
        self,
        server_id: str,
        app_id: str = None,
        period: str = "24h"
    ) -> Dict[str, Any]:
        """Get container metrics for an app."""
        try:
            metrics = await self.metrics_service.get_container_metrics(
                server_id=server_id,
                container_name=app_id,
                period=period
            )

            return {
                "success": True,
                "data": {
                    "server_id": server_id,
                    "app_id": app_id,
                    "period": period,
                    "metrics": [m.model_dump() for m in metrics],
                    "count": len(metrics)
                },
                "message": f"Retrieved {len(metrics)} container metrics"
            }
        except Exception as e:
            logger.error("Get app metrics error", error=str(e))
            return {
                "success": False,
                "message": f"Failed to get app metrics: {str(e)}",
                "error": "GET_APP_METRICS_ERROR"
            }

    async def get_activity_logs(
        self,
        activity_types: List[str] = None,
        server_id: str = None,
        user_id: str = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get activity logs with optional filters."""
        try:
            # Convert string types to enum
            types = None
            if activity_types:
                types = [ActivityType(t) for t in activity_types]

            logs = await self.activity_service.get_activities(
                activity_types=types,
                server_id=server_id,
                user_id=user_id,
                limit=limit,
                offset=offset
            )

            total = await self.activity_service.get_activity_count(activity_types=types)

            return {
                "success": True,
                "data": {
                    "logs": [log.model_dump() for log in logs],
                    "count": len(logs),
                    "total": total,
                    "limit": limit,
                    "offset": offset
                },
                "message": f"Retrieved {len(logs)} activity logs"
            }
        except Exception as e:
            logger.error("Get activity logs error", error=str(e))
            return {
                "success": False,
                "message": f"Failed to get activity logs: {str(e)}",
                "error": "GET_LOGS_ERROR"
            }

    async def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get aggregated dashboard data."""
        try:
            summary = await self.dashboard_service.get_summary()

            return {
                "success": True,
                "data": {
                    "total_servers": summary.total_servers,
                    "online_servers": summary.online_servers,
                    "offline_servers": summary.offline_servers,
                    "total_apps": summary.total_apps,
                    "running_apps": summary.running_apps,
                    "stopped_apps": summary.stopped_apps,
                    "error_apps": summary.error_apps,
                    "avg_cpu_percent": summary.avg_cpu_percent,
                    "avg_memory_percent": summary.avg_memory_percent,
                    "avg_disk_percent": summary.avg_disk_percent,
                    "recent_activities": [a.model_dump() for a in summary.recent_activities]
                },
                "message": "Dashboard summary retrieved"
            }
        except Exception as e:
            logger.error("Get dashboard summary error", error=str(e))
            return {
                "success": False,
                "message": f"Failed to get dashboard summary: {str(e)}",
                "error": "GET_DASHBOARD_ERROR"
            }


def register_metrics_tools(
    app: FastMCP,
    metrics_service: MetricsService,
    activity_service: ActivityService,
    dashboard_service: DashboardService
):
    """Register metrics tools with FastMCP app."""
    tools = MetricsTools(metrics_service, activity_service, dashboard_service)

    app.tool(tools.get_server_metrics)
    app.tool(tools.get_app_metrics)
    app.tool(tools.get_activity_logs)
    app.tool(tools.get_dashboard_summary)

    logger.info("Metrics tools registered")
```

**Step 4: Run test to verify it passes**

```bash
cd /Users/christophebabilotte/source/tomo/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && PYTHONPATH=src pytest tests/unit/test_metrics_tools.py -v --no-cov
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/tools/metrics_tools.py backend/tests/unit/test_metrics_tools.py
git commit -m "feat(metrics): add monitoring MCP tools"
```

---

## Task 7: Verify All Phase 5 Tests Pass

**Step 1: Run all Phase 5 tests**

```bash
cd /Users/christophebabilotte/source/tomo/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && PYTHONPATH=src pytest tests/unit/test_metrics*.py tests/unit/test_activity*.py tests/unit/test_dashboard*.py -v --no-cov
```

**Step 2: Run all project tests to ensure no regressions**

```bash
cd /Users/christophebabilotte/source/tomo/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && PYTHONPATH=src pytest tests/unit/test_auth*.py tests/unit/test_server*.py tests/unit/test_preparation*.py tests/unit/test_app*.py tests/unit/test_catalog*.py tests/unit/test_deployment*.py tests/unit/test_metrics*.py tests/unit/test_activity*.py tests/unit/test_dashboard*.py tests/unit/test_health*.py tests/unit/test_cli.py -v --no-cov
```

**Step 3: Commit if any fixes needed**

```bash
git add .
git commit -m "fix(metrics): fix test failures in Phase 5"
```

---

## Quality Gates Checklist

- [ ] Metrics models created (ServerMetrics, ContainerMetrics, ActivityLog)
- [ ] Database schema for metrics and logs
- [ ] Metrics collection parses SSH output correctly
- [ ] Activity logging tracks all event types
- [ ] Dashboard aggregation works
- [ ] MCP tools implemented:
  - [ ] get_server_metrics
  - [ ] get_app_metrics
  - [ ] get_activity_logs
  - [ ] get_dashboard_summary
- [ ] All unit tests pass

---

## Definition of Done

Backend can:
1. Collect CPU, memory, disk metrics from servers
2. Collect Docker container metrics
3. Log user and system activities
4. Aggregate dashboard summary data
5. Query historical metrics and logs

Note: Actual SSH metric collection will be tested with real VMs in integration testing.

---

**Document Version:** 1.0
**Created:** 2025-12-26
