# Phase 3: Server Preparation - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Automatically prepare target servers with Docker and prerequisites via SSH.

**Architecture:** Preparation service executes step-by-step commands over SSH, tracks status in database, stores logs per server. Supports Ubuntu, Debian, RHEL, Rocky, Fedora.

**Tech Stack:** Python (Paramiko for SSH, SQLite for logs), React (progress stepper UI)

---

## Task 1: Create Preparation Models and Database Schema

**Files:**
- Create: `backend/src/models/preparation.py`
- Create: `backend/src/init_db/schema_preparation.py`
- Test: `backend/tests/unit/test_preparation_models.py`

**Step 1: Write the failing test**

Create `backend/tests/unit/test_preparation_models.py`:

```python
"""Tests for preparation models."""
import pytest
from models.preparation import (
    PreparationStatus,
    PreparationStep,
    PreparationLog,
    ServerPreparation
)


class TestPreparationModels:
    """Tests for preparation data models."""

    def test_preparation_status_enum(self):
        """Should have correct status values."""
        assert PreparationStatus.PENDING.value == "pending"
        assert PreparationStatus.IN_PROGRESS.value == "in_progress"
        assert PreparationStatus.COMPLETED.value == "completed"
        assert PreparationStatus.FAILED.value == "failed"

    def test_preparation_step_enum(self):
        """Should have all required steps."""
        steps = [s.value for s in PreparationStep]
        assert "detect_os" in steps
        assert "update_packages" in steps
        assert "install_dependencies" in steps
        assert "install_docker" in steps
        assert "start_docker" in steps
        assert "configure_user" in steps
        assert "verify_docker" in steps

    def test_preparation_log_model(self):
        """Should create valid preparation log."""
        log = PreparationLog(
            id="log-123",
            server_id="server-456",
            step=PreparationStep.DETECT_OS,
            status=PreparationStatus.COMPLETED,
            message="Detected Ubuntu 22.04",
            timestamp="2025-01-01T00:00:00Z"
        )
        assert log.server_id == "server-456"
        assert log.step == PreparationStep.DETECT_OS

    def test_server_preparation_model(self):
        """Should create valid server preparation."""
        prep = ServerPreparation(
            id="prep-123",
            server_id="server-456",
            status=PreparationStatus.IN_PROGRESS,
            current_step=PreparationStep.INSTALL_DOCKER,
            detected_os="ubuntu",
            started_at="2025-01-01T00:00:00Z"
        )
        assert prep.current_step == PreparationStep.INSTALL_DOCKER
        assert prep.detected_os == "ubuntu"
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/christophebabilotte/source/homelab/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && PYTHONPATH=src pytest tests/unit/test_preparation_models.py -v --no-cov
```

Expected: FAIL - `ModuleNotFoundError: No module named 'models.preparation'`

**Step 3: Create preparation models**

Create `backend/src/models/preparation.py`:

```python
"""
Preparation Data Models

Defines models for server preparation workflow and logging.
"""

from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


class PreparationStatus(str, Enum):
    """Preparation workflow status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class PreparationStep(str, Enum):
    """Preparation workflow steps."""
    DETECT_OS = "detect_os"
    UPDATE_PACKAGES = "update_packages"
    INSTALL_DEPENDENCIES = "install_dependencies"
    INSTALL_DOCKER = "install_docker"
    START_DOCKER = "start_docker"
    CONFIGURE_USER = "configure_user"
    VERIFY_DOCKER = "verify_docker"


# Step order for sequential execution
PREPARATION_STEPS = [
    PreparationStep.DETECT_OS,
    PreparationStep.UPDATE_PACKAGES,
    PreparationStep.INSTALL_DEPENDENCIES,
    PreparationStep.INSTALL_DOCKER,
    PreparationStep.START_DOCKER,
    PreparationStep.CONFIGURE_USER,
    PreparationStep.VERIFY_DOCKER,
]


class PreparationLog(BaseModel):
    """Log entry for a preparation step."""
    id: str = Field(..., description="Unique log entry ID")
    server_id: str = Field(..., description="Server being prepared")
    step: PreparationStep = Field(..., description="Preparation step")
    status: PreparationStatus = Field(..., description="Step status")
    message: str = Field(..., description="Log message")
    output: Optional[str] = Field(None, description="Command output")
    error: Optional[str] = Field(None, description="Error message if failed")
    timestamp: str = Field(..., description="Log timestamp")


class ServerPreparation(BaseModel):
    """Server preparation state."""
    id: str = Field(..., description="Preparation ID")
    server_id: str = Field(..., description="Server being prepared")
    status: PreparationStatus = Field(default=PreparationStatus.PENDING)
    current_step: Optional[PreparationStep] = Field(None, description="Current step")
    detected_os: Optional[str] = Field(None, description="Detected OS type")
    started_at: Optional[str] = Field(None, description="Start timestamp")
    completed_at: Optional[str] = Field(None, description="Completion timestamp")
    error_message: Optional[str] = Field(None, description="Error if failed")
    logs: List[PreparationLog] = Field(default_factory=list)
```

**Step 4: Create database schema**

Create `backend/src/init_db/schema_preparation.py`:

```python
"""Preparation database schema."""

PREPARATION_SCHEMA = """
CREATE TABLE IF NOT EXISTS server_preparations (
    id TEXT PRIMARY KEY,
    server_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    current_step TEXT,
    detected_os TEXT,
    started_at TEXT,
    completed_at TEXT,
    error_message TEXT,
    FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS preparation_logs (
    id TEXT PRIMARY KEY,
    server_id TEXT NOT NULL,
    preparation_id TEXT NOT NULL,
    step TEXT NOT NULL,
    status TEXT NOT NULL,
    message TEXT NOT NULL,
    output TEXT,
    error TEXT,
    timestamp TEXT NOT NULL,
    FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE,
    FOREIGN KEY (preparation_id) REFERENCES server_preparations(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_preparations_server ON server_preparations(server_id);
CREATE INDEX IF NOT EXISTS idx_preparations_status ON server_preparations(status);
CREATE INDEX IF NOT EXISTS idx_prep_logs_server ON preparation_logs(server_id);
CREATE INDEX IF NOT EXISTS idx_prep_logs_preparation ON preparation_logs(preparation_id);
"""


def get_preparation_schema() -> str:
    """Return preparation schema SQL."""
    return PREPARATION_SCHEMA
```

**Step 5: Run test to verify it passes**

```bash
cd /Users/christophebabilotte/source/homelab/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && PYTHONPATH=src pytest tests/unit/test_preparation_models.py -v --no-cov
```

Expected: PASS

**Step 6: Commit**

```bash
git add backend/src/models/preparation.py backend/src/init_db/schema_preparation.py backend/tests/unit/test_preparation_models.py
git commit -m "feat(prep): add preparation models and database schema"
```

---

## Task 2: Create Preparation Service with OS Detection

**Files:**
- Create: `backend/src/services/preparation_service.py`
- Test: `backend/tests/unit/test_preparation_service.py`

**Step 1: Write the failing test**

Create `backend/tests/unit/test_preparation_service.py`:

```python
"""Tests for preparation service."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from services.preparation_service import PreparationService
from models.preparation import PreparationStatus, PreparationStep


class TestPreparationService:
    """Tests for PreparationService."""

    @pytest.fixture
    def mock_ssh_service(self):
        """Create mock SSH service."""
        ssh = MagicMock()
        ssh.execute_command = AsyncMock()
        return ssh

    @pytest.fixture
    def mock_server_service(self):
        """Create mock server service."""
        svc = MagicMock()
        svc.get_server = AsyncMock()
        svc.get_credentials = AsyncMock()
        return svc

    @pytest.fixture
    def mock_db_service(self):
        """Create mock database service."""
        db = MagicMock()
        db.create_preparation = AsyncMock()
        db.update_preparation = AsyncMock()
        db.add_preparation_log = AsyncMock()
        db.get_preparation = AsyncMock()
        db.get_preparation_logs = AsyncMock(return_value=[])
        return db

    @pytest.fixture
    def prep_service(self, mock_ssh_service, mock_server_service, mock_db_service):
        """Create preparation service with mocks."""
        return PreparationService(
            ssh_service=mock_ssh_service,
            server_service=mock_server_service,
            db_service=mock_db_service
        )

    def test_detect_os_ubuntu(self, prep_service):
        """Should detect Ubuntu OS."""
        os_release = "Ubuntu 22.04.3 LTS"
        result = prep_service._detect_os_type(os_release)
        assert result == "ubuntu"

    def test_detect_os_debian(self, prep_service):
        """Should detect Debian OS."""
        os_release = "Debian GNU/Linux 12 (bookworm)"
        result = prep_service._detect_os_type(os_release)
        assert result == "debian"

    def test_detect_os_rocky(self, prep_service):
        """Should detect Rocky Linux."""
        os_release = "Rocky Linux 9.3 (Blue Onyx)"
        result = prep_service._detect_os_type(os_release)
        assert result == "rhel"

    def test_detect_os_fedora(self, prep_service):
        """Should detect Fedora."""
        os_release = "Fedora Linux 39"
        result = prep_service._detect_os_type(os_release)
        assert result == "fedora"

    def test_get_docker_install_commands_ubuntu(self, prep_service):
        """Should return Ubuntu Docker commands."""
        commands = prep_service._get_docker_commands("ubuntu")
        assert "apt-get" in commands["update_packages"]
        assert "docker-ce" in commands["install_docker"]

    def test_get_docker_install_commands_rhel(self, prep_service):
        """Should return RHEL Docker commands."""
        commands = prep_service._get_docker_commands("rhel")
        assert "dnf" in commands["update_packages"]
        assert "docker-ce" in commands["install_docker"]

    @pytest.mark.asyncio
    async def test_start_preparation_creates_record(self, prep_service, mock_db_service, mock_server_service):
        """Should create preparation record."""
        mock_server_service.get_server.return_value = MagicMock(id="server-123")
        mock_db_service.create_preparation.return_value = MagicMock(id="prep-123")

        result = await prep_service.start_preparation("server-123")

        assert result is not None
        mock_db_service.create_preparation.assert_called_once()
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/christophebabilotte/source/homelab/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && PYTHONPATH=src pytest tests/unit/test_preparation_service.py -v --no-cov
```

Expected: FAIL - `ModuleNotFoundError: No module named 'services.preparation_service'`

**Step 3: Create preparation service**

Create `backend/src/services/preparation_service.py`:

```python
"""
Server Preparation Service

Handles automated Docker installation on remote servers.
Supports Ubuntu, Debian, RHEL, Rocky, and Fedora.
"""

import uuid
from datetime import datetime, UTC
from typing import Dict, Any, Optional
import structlog
from models.preparation import (
    PreparationStatus, PreparationStep, PreparationLog,
    ServerPreparation, PREPARATION_STEPS
)

logger = structlog.get_logger("preparation_service")


# OS-specific Docker installation commands
DOCKER_COMMANDS = {
    "ubuntu": {
        "update_packages": "sudo apt-get update -y",
        "install_dependencies": "sudo apt-get install -y ca-certificates curl gnupg",
        "install_docker": """
            sudo install -m 0755 -d /etc/apt/keyrings
            curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
            sudo chmod a+r /etc/apt/keyrings/docker.gpg
            echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
            sudo apt-get update -y
            sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
        """,
        "start_docker": "sudo systemctl enable docker && sudo systemctl start docker",
        "configure_user": "sudo usermod -aG docker $USER",
        "verify_docker": "docker --version && docker compose version"
    },
    "debian": {
        "update_packages": "sudo apt-get update -y",
        "install_dependencies": "sudo apt-get install -y ca-certificates curl gnupg",
        "install_docker": """
            sudo install -m 0755 -d /etc/apt/keyrings
            curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
            sudo chmod a+r /etc/apt/keyrings/docker.gpg
            echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
            sudo apt-get update -y
            sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
        """,
        "start_docker": "sudo systemctl enable docker && sudo systemctl start docker",
        "configure_user": "sudo usermod -aG docker $USER",
        "verify_docker": "docker --version && docker compose version"
    },
    "rhel": {
        "update_packages": "sudo dnf update -y",
        "install_dependencies": "sudo dnf install -y yum-utils",
        "install_docker": """
            sudo dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
            sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
        """,
        "start_docker": "sudo systemctl enable docker && sudo systemctl start docker",
        "configure_user": "sudo usermod -aG docker $USER",
        "verify_docker": "docker --version && docker compose version"
    },
    "fedora": {
        "update_packages": "sudo dnf update -y",
        "install_dependencies": "sudo dnf install -y dnf-plugins-core",
        "install_docker": """
            sudo dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo
            sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
        """,
        "start_docker": "sudo systemctl enable docker && sudo systemctl start docker",
        "configure_user": "sudo usermod -aG docker $USER",
        "verify_docker": "docker --version && docker compose version"
    }
}


class PreparationService:
    """Service for preparing servers with Docker."""

    def __init__(self, ssh_service, server_service, db_service):
        """Initialize preparation service."""
        self.ssh_service = ssh_service
        self.server_service = server_service
        self.db_service = db_service
        logger.info("Preparation service initialized")

    def _detect_os_type(self, os_release: str) -> str:
        """Detect OS type from release string."""
        os_lower = os_release.lower()
        if "ubuntu" in os_lower:
            return "ubuntu"
        elif "debian" in os_lower:
            return "debian"
        elif "rocky" in os_lower or "centos" in os_lower or "rhel" in os_lower or "red hat" in os_lower:
            return "rhel"
        elif "fedora" in os_lower:
            return "fedora"
        else:
            return "unknown"

    def _get_docker_commands(self, os_type: str) -> Dict[str, str]:
        """Get Docker installation commands for OS type."""
        return DOCKER_COMMANDS.get(os_type, DOCKER_COMMANDS["ubuntu"])

    async def start_preparation(self, server_id: str) -> Optional[ServerPreparation]:
        """Start server preparation workflow."""
        try:
            server = await self.server_service.get_server(server_id)
            if not server:
                logger.error("Server not found", server_id=server_id)
                return None

            prep_id = f"prep-{uuid.uuid4().hex[:8]}"
            now = datetime.now(UTC).isoformat()

            preparation = await self.db_service.create_preparation(
                id=prep_id,
                server_id=server_id,
                status=PreparationStatus.PENDING.value,
                started_at=now
            )

            logger.info("Preparation started", prep_id=prep_id, server_id=server_id)
            return preparation

        except Exception as e:
            logger.error("Failed to start preparation", error=str(e))
            return None

    async def get_preparation_status(self, server_id: str) -> Optional[Dict[str, Any]]:
        """Get current preparation status for a server."""
        try:
            prep = await self.db_service.get_preparation(server_id)
            if not prep:
                return None

            logs = await self.db_service.get_preparation_logs(server_id)

            return {
                "id": prep.id,
                "server_id": server_id,
                "status": prep.status,
                "current_step": prep.current_step,
                "detected_os": prep.detected_os,
                "started_at": prep.started_at,
                "completed_at": prep.completed_at,
                "error_message": prep.error_message,
                "logs": [log.model_dump() for log in logs]
            }
        except Exception as e:
            logger.error("Failed to get status", error=str(e))
            return None
```

**Step 4: Run test to verify it passes**

```bash
cd /Users/christophebabilotte/source/homelab/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && PYTHONPATH=src pytest tests/unit/test_preparation_service.py -v --no-cov
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/services/preparation_service.py backend/tests/unit/test_preparation_service.py
git commit -m "feat(prep): add preparation service with OS detection"
```

---

## Task 3: Add Preparation Database Methods

**Files:**
- Modify: `backend/src/services/database_service.py`
- Test: `backend/tests/unit/test_preparation_database.py`

**Step 1: Write the failing test**

Create `backend/tests/unit/test_preparation_database.py`:

```python
"""Tests for preparation database operations."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from contextlib import asynccontextmanager


class TestPreparationDatabaseOperations:
    """Tests for preparation CRUD in database."""

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
    async def test_create_preparation(self, db_service, mock_connection):
        """Should create preparation record."""
        result = await db_service.create_preparation(
            id="prep-123",
            server_id="server-456",
            status="pending",
            started_at="2025-01-01T00:00:00Z"
        )

        assert result is not None
        mock_connection.execute.assert_called()

    @pytest.mark.asyncio
    async def test_update_preparation(self, db_service, mock_connection):
        """Should update preparation record."""
        result = await db_service.update_preparation(
            prep_id="prep-123",
            status="in_progress",
            current_step="install_docker"
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_add_preparation_log(self, db_service, mock_connection):
        """Should add preparation log entry."""
        result = await db_service.add_preparation_log(
            id="log-123",
            server_id="server-456",
            preparation_id="prep-123",
            step="detect_os",
            status="completed",
            message="Detected Ubuntu 22.04",
            timestamp="2025-01-01T00:00:00Z"
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_get_preparation(self, db_service, mock_connection):
        """Should get preparation by server ID."""
        mock_row = {
            "id": "prep-123",
            "server_id": "server-456",
            "status": "in_progress",
            "current_step": "install_docker",
            "detected_os": "ubuntu",
            "started_at": "2025-01-01T00:00:00Z",
            "completed_at": None,
            "error_message": None
        }
        mock_connection.execute.return_value = MagicMock(
            fetchone=AsyncMock(return_value=mock_row)
        )

        result = await db_service.get_preparation("server-456")

        assert result is not None
        assert result.status == "in_progress"

    @pytest.mark.asyncio
    async def test_get_preparation_logs(self, db_service, mock_connection):
        """Should get all logs for a server."""
        mock_rows = [
            {"id": "log-1", "server_id": "server-456", "preparation_id": "prep-123",
             "step": "detect_os", "status": "completed", "message": "OK",
             "output": None, "error": None, "timestamp": "2025-01-01T00:00:00Z"},
            {"id": "log-2", "server_id": "server-456", "preparation_id": "prep-123",
             "step": "update_packages", "status": "completed", "message": "OK",
             "output": None, "error": None, "timestamp": "2025-01-01T00:01:00Z"}
        ]
        mock_connection.execute.return_value = MagicMock(
            fetchall=AsyncMock(return_value=mock_rows)
        )

        result = await db_service.get_preparation_logs("server-456")

        assert len(result) == 2
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/christophebabilotte/source/homelab/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && PYTHONPATH=src pytest tests/unit/test_preparation_database.py -v --no-cov
```

Expected: FAIL - methods don't exist

**Step 3: Add database methods**

Add to `backend/src/services/database_service.py`:

```python
# Add these imports at top if not present
from models.preparation import ServerPreparation, PreparationLog, PreparationStatus, PreparationStep

async def create_preparation(
    self,
    id: str,
    server_id: str,
    status: str,
    started_at: str
) -> Optional[ServerPreparation]:
    """Create a new preparation record."""
    try:
        async with self.get_connection() as conn:
            await conn.execute(
                """INSERT INTO server_preparations (id, server_id, status, started_at)
                   VALUES (?, ?, ?, ?)""",
                (id, server_id, status, started_at)
            )
            await conn.commit()

        return ServerPreparation(
            id=id,
            server_id=server_id,
            status=PreparationStatus(status),
            started_at=started_at
        )
    except Exception as e:
        logger.error("Failed to create preparation", error=str(e))
        return None

async def update_preparation(self, prep_id: str, **kwargs) -> bool:
    """Update preparation record."""
    try:
        updates = []
        values = []
        for key, value in kwargs.items():
            if value is not None:
                updates.append(f"{key} = ?")
                values.append(value)

        if not updates:
            return True

        values.append(prep_id)
        query = f"UPDATE server_preparations SET {', '.join(updates)} WHERE id = ?"

        async with self.get_connection() as conn:
            await conn.execute(query, values)
            await conn.commit()
        return True
    except Exception as e:
        logger.error("Failed to update preparation", error=str(e))
        return False

async def add_preparation_log(
    self,
    id: str,
    server_id: str,
    preparation_id: str,
    step: str,
    status: str,
    message: str,
    timestamp: str,
    output: str = None,
    error: str = None
) -> bool:
    """Add preparation log entry."""
    try:
        async with self.get_connection() as conn:
            await conn.execute(
                """INSERT INTO preparation_logs
                   (id, server_id, preparation_id, step, status, message, output, error, timestamp)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (id, server_id, preparation_id, step, status, message, output, error, timestamp)
            )
            await conn.commit()
        return True
    except Exception as e:
        logger.error("Failed to add preparation log", error=str(e))
        return False

async def get_preparation(self, server_id: str) -> Optional[ServerPreparation]:
    """Get latest preparation for a server."""
    try:
        async with self.get_connection() as conn:
            cursor = await conn.execute(
                """SELECT * FROM server_preparations
                   WHERE server_id = ? ORDER BY started_at DESC LIMIT 1""",
                (server_id,)
            )
            row = await cursor.fetchone()

        if not row:
            return None

        return ServerPreparation(
            id=row["id"],
            server_id=row["server_id"],
            status=PreparationStatus(row["status"]),
            current_step=PreparationStep(row["current_step"]) if row["current_step"] else None,
            detected_os=row["detected_os"],
            started_at=row["started_at"],
            completed_at=row["completed_at"],
            error_message=row["error_message"]
        )
    except Exception as e:
        logger.error("Failed to get preparation", error=str(e))
        return None

async def get_preparation_logs(self, server_id: str) -> list:
    """Get all preparation logs for a server."""
    try:
        async with self.get_connection() as conn:
            cursor = await conn.execute(
                """SELECT * FROM preparation_logs
                   WHERE server_id = ? ORDER BY timestamp ASC""",
                (server_id,)
            )
            rows = await cursor.fetchall()

        return [
            PreparationLog(
                id=row["id"],
                server_id=row["server_id"],
                step=PreparationStep(row["step"]),
                status=PreparationStatus(row["status"]),
                message=row["message"],
                output=row["output"],
                error=row["error"],
                timestamp=row["timestamp"]
            )
            for row in rows
        ]
    except Exception as e:
        logger.error("Failed to get preparation logs", error=str(e))
        return []
```

**Step 4: Run test to verify it passes**

```bash
cd /Users/christophebabilotte/source/homelab/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && PYTHONPATH=src pytest tests/unit/test_preparation_database.py -v --no-cov
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/services/database_service.py backend/tests/unit/test_preparation_database.py
git commit -m "feat(prep): add preparation database CRUD methods"
```

---

## Task 4: Create Preparation MCP Tools

**Files:**
- Create: `backend/src/tools/preparation_tools.py`
- Test: `backend/tests/unit/test_preparation_tools.py`

**Step 1: Write the failing test**

Create `backend/tests/unit/test_preparation_tools.py`:

```python
"""Tests for preparation MCP tools."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from tools.preparation_tools import PreparationTools
from models.preparation import PreparationStatus, PreparationStep


@pytest.fixture
def mock_prep_service():
    """Create mock preparation service."""
    svc = MagicMock()
    svc.start_preparation = AsyncMock()
    svc.get_preparation_status = AsyncMock()
    svc.execute_preparation = AsyncMock()
    return svc


@pytest.fixture
def prep_tools(mock_prep_service):
    """Create preparation tools with mock."""
    return PreparationTools(mock_prep_service)


class TestPrepareServer:
    """Tests for prepare_server tool."""

    @pytest.mark.asyncio
    async def test_prepare_server_success(self, prep_tools, mock_prep_service):
        """Should start preparation successfully."""
        mock_prep_service.start_preparation.return_value = MagicMock(id="prep-123")

        result = await prep_tools.prepare_server(server_id="server-456")

        assert result["success"] is True
        assert "prep-123" in str(result["data"])

    @pytest.mark.asyncio
    async def test_prepare_server_not_found(self, prep_tools, mock_prep_service):
        """Should return error if server not found."""
        mock_prep_service.start_preparation.return_value = None

        result = await prep_tools.prepare_server(server_id="nonexistent")

        assert result["success"] is False
        assert result["error"] == "PREPARATION_START_FAILED"


class TestGetPreparationStatus:
    """Tests for get_preparation_status tool."""

    @pytest.mark.asyncio
    async def test_get_status_success(self, prep_tools, mock_prep_service):
        """Should return preparation status."""
        mock_prep_service.get_preparation_status.return_value = {
            "id": "prep-123",
            "status": "in_progress",
            "current_step": "install_docker",
            "logs": []
        }

        result = await prep_tools.get_preparation_status(server_id="server-456")

        assert result["success"] is True
        assert result["data"]["status"] == "in_progress"

    @pytest.mark.asyncio
    async def test_get_status_not_found(self, prep_tools, mock_prep_service):
        """Should return error if no preparation found."""
        mock_prep_service.get_preparation_status.return_value = None

        result = await prep_tools.get_preparation_status(server_id="server-456")

        assert result["success"] is False
        assert result["error"] == "PREPARATION_NOT_FOUND"
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/christophebabilotte/source/homelab/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && PYTHONPATH=src pytest tests/unit/test_preparation_tools.py -v --no-cov
```

Expected: FAIL

**Step 3: Create preparation tools**

Create `backend/src/tools/preparation_tools.py`:

```python
"""
Server Preparation Tools

Provides MCP tools for server preparation workflow.
"""

from typing import Dict, Any
import structlog
from fastmcp import FastMCP
from services.preparation_service import PreparationService


logger = structlog.get_logger("preparation_tools")


class PreparationTools:
    """Preparation tools for the MCP server."""

    def __init__(self, preparation_service: PreparationService):
        """Initialize preparation tools."""
        self.preparation_service = preparation_service
        logger.info("Preparation tools initialized")

    async def prepare_server(self, server_id: str) -> Dict[str, Any]:
        """Start server preparation to install Docker."""
        try:
            preparation = await self.preparation_service.start_preparation(server_id)

            if not preparation:
                return {
                    "success": False,
                    "message": "Failed to start preparation",
                    "error": "PREPARATION_START_FAILED"
                }

            logger.info("Preparation started", server_id=server_id, prep_id=preparation.id)
            return {
                "success": True,
                "data": {"preparation_id": preparation.id, "server_id": server_id},
                "message": "Preparation started"
            }
        except Exception as e:
            logger.error("Prepare server error", error=str(e))
            return {
                "success": False,
                "message": f"Failed to prepare server: {str(e)}",
                "error": "PREPARE_SERVER_ERROR"
            }

    async def get_preparation_status(self, server_id: str) -> Dict[str, Any]:
        """Get current preparation status for a server."""
        try:
            status = await self.preparation_service.get_preparation_status(server_id)

            if not status:
                return {
                    "success": False,
                    "message": "No preparation found for server",
                    "error": "PREPARATION_NOT_FOUND"
                }

            return {
                "success": True,
                "data": status,
                "message": "Preparation status retrieved"
            }
        except Exception as e:
            logger.error("Get preparation status error", error=str(e))
            return {
                "success": False,
                "message": f"Failed to get status: {str(e)}",
                "error": "GET_STATUS_ERROR"
            }

    async def get_preparation_logs(self, server_id: str) -> Dict[str, Any]:
        """Get full preparation log history."""
        try:
            status = await self.preparation_service.get_preparation_status(server_id)

            if not status:
                return {
                    "success": False,
                    "message": "No preparation found",
                    "error": "PREPARATION_NOT_FOUND"
                }

            return {
                "success": True,
                "data": {"logs": status.get("logs", [])},
                "message": f"Retrieved {len(status.get('logs', []))} log entries"
            }
        except Exception as e:
            logger.error("Get preparation logs error", error=str(e))
            return {
                "success": False,
                "message": f"Failed to get logs: {str(e)}",
                "error": "GET_LOGS_ERROR"
            }

    async def retry_preparation(self, server_id: str) -> Dict[str, Any]:
        """Retry failed preparation from last failed step."""
        try:
            # Get current status to find failed step
            status = await self.preparation_service.get_preparation_status(server_id)

            if not status:
                return {
                    "success": False,
                    "message": "No preparation found",
                    "error": "PREPARATION_NOT_FOUND"
                }

            if status["status"] != "failed":
                return {
                    "success": False,
                    "message": "Preparation is not in failed state",
                    "error": "INVALID_STATE"
                }

            # Start new preparation (will continue from where it left off)
            preparation = await self.preparation_service.start_preparation(server_id)

            if not preparation:
                return {
                    "success": False,
                    "message": "Failed to retry preparation",
                    "error": "RETRY_FAILED"
                }

            return {
                "success": True,
                "data": {"preparation_id": preparation.id},
                "message": "Preparation retry started"
            }
        except Exception as e:
            logger.error("Retry preparation error", error=str(e))
            return {
                "success": False,
                "message": f"Failed to retry: {str(e)}",
                "error": "RETRY_ERROR"
            }


def register_preparation_tools(app: FastMCP, preparation_service: PreparationService):
    """Register preparation tools with FastMCP app."""
    tools = PreparationTools(preparation_service)

    app.tool(tools.prepare_server)
    app.tool(tools.get_preparation_status)
    app.tool(tools.get_preparation_logs)
    app.tool(tools.retry_preparation)

    logger.info("Preparation tools registered")
```

**Step 4: Run test to verify it passes**

```bash
cd /Users/christophebabilotte/source/homelab/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && PYTHONPATH=src pytest tests/unit/test_preparation_tools.py -v --no-cov
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/tools/preparation_tools.py backend/tests/unit/test_preparation_tools.py
git commit -m "feat(prep): add preparation MCP tools"
```

---

## Task 5: Verify All Phase 3 Tests Pass

**Step 1: Run all Phase 3 tests**

```bash
cd /Users/christophebabilotte/source/homelab/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && PYTHONPATH=src pytest tests/unit/test_preparation*.py -v --no-cov
```

**Step 2: Run all project tests to ensure no regressions**

```bash
cd /Users/christophebabilotte/source/homelab/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && PYTHONPATH=src pytest tests/unit/test_auth*.py tests/unit/test_server*.py tests/unit/test_preparation*.py tests/unit/test_health*.py tests/unit/test_cli.py -v --no-cov
```

**Step 3: Commit if any fixes needed**

```bash
git add .
git commit -m "fix(prep): fix test failures in Phase 3"
```

---

## Quality Gates Checklist

- [ ] Preparation models created
- [ ] Database schema for preparations
- [ ] OS detection works (Ubuntu, Debian, RHEL, Fedora)
- [ ] Docker installation commands per OS
- [ ] MCP tools implemented:
  - [ ] prepare_server
  - [ ] get_preparation_status
  - [ ] get_preparation_logs
  - [ ] retry_preparation
- [ ] All unit tests pass

---

## Definition of Done

Backend can:
1. Start a preparation workflow for a server
2. Detect the OS type
3. Track preparation status and logs
4. Retry failed preparations

Note: Actual SSH command execution will be tested with real VMs in integration testing.

---

**Document Version:** 1.0
**Created:** 2025-12-25
