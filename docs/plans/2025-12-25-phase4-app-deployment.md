# Phase 4: App Deployment - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Users browse an extensible catalog and deploy Docker applications to their servers with one click.

**Architecture:** YAML-based app definitions loaded from built-in + custom directories. Deployment service executes Docker commands over SSH. Installation state tracked in database.

**Tech Stack:** Python (Pydantic for schema, PyYAML for parsing, Paramiko for SSH), SQLite for tracking

---

## Task 1: Create App Definition Models and Schema

**Files:**
- Create: `backend/src/models/app_catalog.py`
- Create: `backend/src/init_db/schema_apps.py`
- Test: `backend/tests/unit/test_app_models.py`

**Step 1: Write the failing test**

Create `backend/tests/unit/test_app_models.py`:

```python
"""Tests for app catalog models."""
import pytest
from models.app_catalog import (
    AppDefinition,
    AppPort,
    AppVolume,
    AppEnvVar,
    AppCategory,
    InstallationStatus,
    InstalledApp
)


class TestAppModels:
    """Tests for app catalog data models."""

    def test_app_category_enum(self):
        """Should have correct category values."""
        assert AppCategory.STORAGE.value == "storage"
        assert AppCategory.MEDIA.value == "media"
        assert AppCategory.NETWORKING.value == "networking"
        assert AppCategory.MONITORING.value == "monitoring"
        assert AppCategory.UTILITY.value == "utility"

    def test_installation_status_enum(self):
        """Should have correct status values."""
        assert InstallationStatus.PENDING.value == "pending"
        assert InstallationStatus.PULLING.value == "pulling"
        assert InstallationStatus.RUNNING.value == "running"
        assert InstallationStatus.STOPPED.value == "stopped"
        assert InstallationStatus.ERROR.value == "error"

    def test_app_port_model(self):
        """Should create valid port mapping."""
        port = AppPort(container=80, host=8080, protocol="tcp")
        assert port.container == 80
        assert port.host == 8080
        assert port.protocol == "tcp"

    def test_app_volume_model(self):
        """Should create valid volume mapping."""
        volume = AppVolume(
            host_path="/var/data",
            container_path="/app/data",
            readonly=False
        )
        assert volume.host_path == "/var/data"
        assert volume.container_path == "/app/data"

    def test_app_env_var_model(self):
        """Should create valid env var."""
        env = AppEnvVar(name="DB_HOST", required=True, default=None)
        assert env.name == "DB_HOST"
        assert env.required is True

    def test_app_definition_model(self):
        """Should create valid app definition."""
        app = AppDefinition(
            id="nextcloud",
            name="Nextcloud",
            description="Personal cloud storage",
            category=AppCategory.STORAGE,
            image="nextcloud:latest",
            ports=[AppPort(container=80, host=8080)],
            volumes=[],
            env_vars=[]
        )
        assert app.id == "nextcloud"
        assert app.category == AppCategory.STORAGE

    def test_installed_app_model(self):
        """Should create valid installed app."""
        installed = InstalledApp(
            id="inst-123",
            server_id="server-456",
            app_id="nextcloud",
            container_id="abc123",
            status=InstallationStatus.RUNNING,
            config={"ports": {"80": 8080}},
            installed_at="2025-01-01T00:00:00Z"
        )
        assert installed.status == InstallationStatus.RUNNING
        assert installed.container_id == "abc123"
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/christophebabilotte/source/homelab/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && PYTHONPATH=src pytest tests/unit/test_app_models.py -v --no-cov
```

Expected: FAIL - `ModuleNotFoundError: No module named 'models.app_catalog'`

**Step 3: Create app catalog models**

Create `backend/src/models/app_catalog.py`:

```python
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
```

**Step 4: Create database schema**

Create `backend/src/init_db/schema_apps.py`:

```python
"""App installation database schema."""

APPS_SCHEMA = """
CREATE TABLE IF NOT EXISTS installed_apps (
    id TEXT PRIMARY KEY,
    server_id TEXT NOT NULL,
    app_id TEXT NOT NULL,
    container_id TEXT,
    container_name TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    config TEXT,
    installed_at TEXT,
    started_at TEXT,
    error_message TEXT,
    FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE,
    UNIQUE(server_id, app_id)
);

CREATE INDEX IF NOT EXISTS idx_installed_apps_server ON installed_apps(server_id);
CREATE INDEX IF NOT EXISTS idx_installed_apps_status ON installed_apps(status);
"""


def get_apps_schema() -> str:
    """Return apps schema SQL."""
    return APPS_SCHEMA
```

**Step 5: Run test to verify it passes**

```bash
cd /Users/christophebabilotte/source/homelab/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && PYTHONPATH=src pytest tests/unit/test_app_models.py -v --no-cov
```

Expected: PASS

**Step 6: Commit**

```bash
git add backend/src/models/app_catalog.py backend/src/init_db/schema_apps.py backend/tests/unit/test_app_models.py
git commit -m "feat(apps): add app catalog models and database schema"
```

---

## Task 2: Create Catalog Loader Service

**Files:**
- Create: `backend/src/services/catalog_service.py`
- Create: `backend/data/catalog/portainer.yaml`
- Test: `backend/tests/unit/test_catalog_service.py`

**Step 1: Write the failing test**

Create `backend/tests/unit/test_catalog_service.py`:

```python
"""Tests for catalog service."""
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from services.catalog_service import CatalogService
from models.app_catalog import AppCategory


class TestCatalogService:
    """Tests for CatalogService."""

    @pytest.fixture
    def catalog_service(self, tmp_path):
        """Create catalog service with temp directory."""
        return CatalogService(catalog_dirs=[str(tmp_path)])

    def test_parse_app_definition(self, catalog_service, tmp_path):
        """Should parse YAML app definition."""
        yaml_content = """
id: test-app
name: Test App
description: A test application
category: utility
image: test:latest
ports:
  - container: 80
    host: 8080
"""
        app_file = tmp_path / "test-app.yaml"
        app_file.write_text(yaml_content)

        app = catalog_service._parse_app_file(app_file)

        assert app.id == "test-app"
        assert app.name == "Test App"
        assert app.category == AppCategory.UTILITY
        assert len(app.ports) == 1

    def test_load_catalog(self, catalog_service, tmp_path):
        """Should load all apps from catalog directory."""
        yaml1 = """
id: app1
name: App One
description: First app
category: storage
image: app1:latest
"""
        yaml2 = """
id: app2
name: App Two
description: Second app
category: media
image: app2:latest
"""
        (tmp_path / "app1.yaml").write_text(yaml1)
        (tmp_path / "app2.yaml").write_text(yaml2)

        catalog_service.load_catalog()

        assert len(catalog_service.apps) == 2
        assert "app1" in catalog_service.apps
        assert "app2" in catalog_service.apps

    def test_get_app(self, catalog_service, tmp_path):
        """Should get specific app by ID."""
        yaml_content = """
id: myapp
name: My App
description: My application
category: utility
image: myapp:latest
"""
        (tmp_path / "myapp.yaml").write_text(yaml_content)
        catalog_service.load_catalog()

        app = catalog_service.get_app("myapp")

        assert app is not None
        assert app.id == "myapp"

    def test_get_app_not_found(self, catalog_service):
        """Should return None for unknown app."""
        app = catalog_service.get_app("nonexistent")
        assert app is None

    def test_list_apps(self, catalog_service, tmp_path):
        """Should list all apps."""
        yaml1 = """
id: app1
name: App One
description: First
category: storage
image: app1:latest
"""
        (tmp_path / "app1.yaml").write_text(yaml1)
        catalog_service.load_catalog()

        apps = catalog_service.list_apps()

        assert len(apps) == 1
        assert apps[0].id == "app1"

    def test_list_apps_by_category(self, catalog_service, tmp_path):
        """Should filter apps by category."""
        yaml1 = """
id: storage1
name: Storage App
description: Storage
category: storage
image: s1:latest
"""
        yaml2 = """
id: media1
name: Media App
description: Media
category: media
image: m1:latest
"""
        (tmp_path / "storage1.yaml").write_text(yaml1)
        (tmp_path / "media1.yaml").write_text(yaml2)
        catalog_service.load_catalog()

        storage_apps = catalog_service.list_apps(category="storage")

        assert len(storage_apps) == 1
        assert storage_apps[0].id == "storage1"
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/christophebabilotte/source/homelab/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && PYTHONPATH=src pytest tests/unit/test_catalog_service.py -v --no-cov
```

Expected: FAIL

**Step 3: Create catalog service**

Create `backend/src/services/catalog_service.py`:

```python
"""
App Catalog Service

Loads and manages application definitions from YAML files.
"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional
import structlog
from models.app_catalog import AppDefinition, AppCategory, AppPort, AppVolume, AppEnvVar

logger = structlog.get_logger("catalog_service")


class CatalogService:
    """Service for loading and querying app catalog."""

    def __init__(self, catalog_dirs: List[str] = None):
        """Initialize catalog service."""
        self.catalog_dirs = catalog_dirs or []
        self.apps: Dict[str, AppDefinition] = {}
        logger.info("Catalog service initialized", dirs=self.catalog_dirs)

    def _parse_app_file(self, file_path: Path) -> Optional[AppDefinition]:
        """Parse a YAML app definition file."""
        try:
            with open(file_path, 'r') as f:
                data = yaml.safe_load(f)

            # Parse ports
            ports = []
            for p in data.get('ports', []):
                ports.append(AppPort(
                    container=p.get('container'),
                    host=p.get('host'),
                    protocol=p.get('protocol', 'tcp')
                ))

            # Parse volumes
            volumes = []
            for v in data.get('volumes', []):
                if isinstance(v, str):
                    # Format: host:container or host:container:ro
                    parts = v.split(':')
                    volumes.append(AppVolume(
                        host_path=parts[0],
                        container_path=parts[1],
                        readonly=len(parts) > 2 and parts[2] == 'ro'
                    ))
                else:
                    volumes.append(AppVolume(
                        host_path=v.get('host_path'),
                        container_path=v.get('container_path'),
                        readonly=v.get('readonly', False)
                    ))

            # Parse env vars
            env_vars = []
            for e in data.get('env', data.get('env_vars', [])):
                if isinstance(e, str):
                    # Format: NAME=value or NAME
                    if '=' in e:
                        name, default = e.split('=', 1)
                        env_vars.append(AppEnvVar(name=name, default=default))
                    else:
                        env_vars.append(AppEnvVar(name=e, required=True))
                else:
                    env_vars.append(AppEnvVar(
                        name=e.get('name'),
                        description=e.get('description'),
                        required=e.get('required', False),
                        default=e.get('default')
                    ))

            return AppDefinition(
                id=data['id'],
                name=data['name'],
                description=data.get('description', ''),
                category=AppCategory(data.get('category', 'utility')),
                image=data['image'],
                ports=ports,
                volumes=volumes,
                env_vars=env_vars,
                restart_policy=data.get('restart_policy', 'unless-stopped'),
                network_mode=data.get('network_mode'),
                privileged=data.get('privileged', False),
                capabilities=data.get('capabilities', [])
            )

        except Exception as e:
            logger.error("Failed to parse app file", file=str(file_path), error=str(e))
            return None

    def load_catalog(self) -> None:
        """Load all app definitions from catalog directories."""
        self.apps = {}

        for dir_path in self.catalog_dirs:
            catalog_dir = Path(dir_path)
            if not catalog_dir.exists():
                logger.warning("Catalog directory not found", path=dir_path)
                continue

            for yaml_file in catalog_dir.glob("*.yaml"):
                app = self._parse_app_file(yaml_file)
                if app:
                    self.apps[app.id] = app
                    logger.debug("Loaded app", app_id=app.id)

            for yml_file in catalog_dir.glob("*.yml"):
                app = self._parse_app_file(yml_file)
                if app:
                    self.apps[app.id] = app
                    logger.debug("Loaded app", app_id=app.id)

        logger.info("Catalog loaded", app_count=len(self.apps))

    def get_app(self, app_id: str) -> Optional[AppDefinition]:
        """Get app definition by ID."""
        return self.apps.get(app_id)

    def list_apps(self, category: str = None) -> List[AppDefinition]:
        """List all apps, optionally filtered by category."""
        apps = list(self.apps.values())

        if category:
            apps = [a for a in apps if a.category.value == category]

        return sorted(apps, key=lambda a: a.name)

    def reload_catalog(self) -> None:
        """Reload catalog from disk."""
        self.load_catalog()
```

**Step 4: Create sample Portainer app definition**

Create `backend/data/catalog/portainer.yaml`:

```yaml
id: portainer
name: Portainer
description: Docker management UI for managing containers, images, and networks
category: utility
image: portainer/portainer-ce:latest
ports:
  - container: 9000
    host: 9000
  - container: 9443
    host: 9443
volumes:
  - host_path: /var/run/docker.sock
    container_path: /var/run/docker.sock
    readonly: false
  - host_path: /var/portainer/data
    container_path: /data
restart_policy: unless-stopped
```

**Step 5: Run test to verify it passes**

```bash
cd /Users/christophebabilotte/source/homelab/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && PYTHONPATH=src pytest tests/unit/test_catalog_service.py -v --no-cov
```

Expected: PASS

**Step 6: Commit**

```bash
git add backend/src/services/catalog_service.py backend/tests/unit/test_catalog_service.py backend/data/catalog/portainer.yaml
git commit -m "feat(apps): add catalog service with YAML parser"
```

---

## Task 3: Create Deployment Service

**Files:**
- Create: `backend/src/services/deployment_service.py`
- Test: `backend/tests/unit/test_deployment_service.py`

**Step 1: Write the failing test**

Create `backend/tests/unit/test_deployment_service.py`:

```python
"""Tests for deployment service."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from services.deployment_service import DeploymentService
from models.app_catalog import (
    AppDefinition, AppPort, AppVolume, AppCategory, InstallationStatus
)


class TestDeploymentService:
    """Tests for DeploymentService."""

    @pytest.fixture
    def mock_ssh_service(self):
        """Create mock SSH service."""
        ssh = MagicMock()
        ssh.execute_command = AsyncMock(return_value=(0, "success", ""))
        return ssh

    @pytest.fixture
    def mock_server_service(self):
        """Create mock server service."""
        svc = MagicMock()
        svc.get_server = AsyncMock(return_value=MagicMock(id="server-123", host="192.168.1.100"))
        svc.get_credentials = AsyncMock(return_value={"username": "admin", "password": "pass"})
        return svc

    @pytest.fixture
    def mock_catalog_service(self):
        """Create mock catalog service."""
        svc = MagicMock()
        svc.get_app = MagicMock(return_value=AppDefinition(
            id="testapp",
            name="Test App",
            description="Test",
            category=AppCategory.UTILITY,
            image="test:latest",
            ports=[AppPort(container=80, host=8080)],
            volumes=[],
            env_vars=[]
        ))
        return svc

    @pytest.fixture
    def mock_db_service(self):
        """Create mock database service."""
        db = MagicMock()
        db.create_installation = AsyncMock()
        db.update_installation = AsyncMock()
        db.get_installation = AsyncMock()
        db.get_installations = AsyncMock(return_value=[])
        db.delete_installation = AsyncMock()
        return db

    @pytest.fixture
    def deployment_service(self, mock_ssh_service, mock_server_service, mock_catalog_service, mock_db_service):
        """Create deployment service with mocks."""
        return DeploymentService(
            ssh_service=mock_ssh_service,
            server_service=mock_server_service,
            catalog_service=mock_catalog_service,
            db_service=mock_db_service
        )

    def test_build_docker_run_command(self, deployment_service):
        """Should build correct docker run command."""
        app = AppDefinition(
            id="myapp",
            name="My App",
            description="Test",
            category=AppCategory.UTILITY,
            image="myapp:latest",
            ports=[AppPort(container=80, host=8080)],
            volumes=[AppVolume(host_path="/data", container_path="/app/data")],
            env_vars=[]
        )
        config = {"env": {"MY_VAR": "value"}}

        cmd = deployment_service._build_docker_run_command(app, "myapp-container", config)

        assert "docker run" in cmd
        assert "-p 8080:80" in cmd
        assert "-v /data:/app/data" in cmd
        assert "myapp:latest" in cmd
        assert "--name myapp-container" in cmd

    def test_build_docker_run_with_env(self, deployment_service):
        """Should include environment variables."""
        app = AppDefinition(
            id="myapp",
            name="My App",
            description="Test",
            category=AppCategory.UTILITY,
            image="myapp:latest",
            ports=[],
            volumes=[],
            env_vars=[]
        )
        config = {"env": {"DB_HOST": "localhost", "DB_PORT": "5432"}}

        cmd = deployment_service._build_docker_run_command(app, "myapp", config)

        assert "-e DB_HOST=localhost" in cmd
        assert "-e DB_PORT=5432" in cmd

    @pytest.mark.asyncio
    async def test_install_app_creates_record(self, deployment_service, mock_db_service):
        """Should create installation record."""
        mock_db_service.create_installation.return_value = MagicMock(id="inst-123")

        result = await deployment_service.install_app(
            server_id="server-123",
            app_id="testapp",
            config={}
        )

        assert result is not None
        mock_db_service.create_installation.assert_called_once()

    @pytest.mark.asyncio
    async def test_uninstall_app(self, deployment_service, mock_ssh_service, mock_db_service):
        """Should stop and remove container."""
        mock_db_service.get_installation.return_value = MagicMock(
            container_name="testapp-container",
            status=InstallationStatus.RUNNING
        )

        result = await deployment_service.uninstall_app(
            server_id="server-123",
            app_id="testapp",
            remove_data=False
        )

        assert result is True
        assert mock_ssh_service.execute_command.call_count >= 2  # stop + rm

    @pytest.mark.asyncio
    async def test_get_app_status(self, deployment_service, mock_ssh_service, mock_db_service):
        """Should get container status."""
        mock_db_service.get_installation.return_value = MagicMock(
            container_name="testapp-container"
        )
        mock_ssh_service.execute_command.return_value = (0, "running", "")

        status = await deployment_service.get_app_status("server-123", "testapp")

        assert status is not None
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/christophebabilotte/source/homelab/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && PYTHONPATH=src pytest tests/unit/test_deployment_service.py -v --no-cov
```

Expected: FAIL

**Step 3: Create deployment service**

Create `backend/src/services/deployment_service.py`:

```python
"""
App Deployment Service

Handles Docker container deployment and management on remote servers.
"""

import uuid
from datetime import datetime, UTC
from typing import Dict, Any, Optional, List
import structlog
from models.app_catalog import (
    AppDefinition, InstallationStatus, InstalledApp
)

logger = structlog.get_logger("deployment_service")


class DeploymentService:
    """Service for deploying apps to servers."""

    def __init__(self, ssh_service, server_service, catalog_service, db_service):
        """Initialize deployment service."""
        self.ssh_service = ssh_service
        self.server_service = server_service
        self.catalog_service = catalog_service
        self.db_service = db_service
        logger.info("Deployment service initialized")

    def _build_docker_run_command(
        self,
        app: AppDefinition,
        container_name: str,
        config: Dict[str, Any]
    ) -> str:
        """Build docker run command for an app."""
        parts = ["docker run -d"]

        # Container name
        parts.append(f"--name {container_name}")

        # Restart policy
        parts.append(f"--restart {app.restart_policy}")

        # Port mappings
        for port in app.ports:
            host_port = config.get("ports", {}).get(str(port.container), port.host)
            parts.append(f"-p {host_port}:{port.container}/{port.protocol}")

        # Volume mappings
        for volume in app.volumes:
            host_path = config.get("volumes", {}).get(volume.container_path, volume.host_path)
            ro = ":ro" if volume.readonly else ""
            parts.append(f"-v {host_path}:{volume.container_path}{ro}")

        # Environment variables from config
        for key, value in config.get("env", {}).items():
            parts.append(f"-e {key}={value}")

        # Network mode
        if app.network_mode:
            parts.append(f"--network {app.network_mode}")

        # Privileged mode
        if app.privileged:
            parts.append("--privileged")

        # Capabilities
        for cap in app.capabilities:
            parts.append(f"--cap-add {cap}")

        # Image
        parts.append(app.image)

        return " ".join(parts)

    async def install_app(
        self,
        server_id: str,
        app_id: str,
        config: Dict[str, Any] = None
    ) -> Optional[InstalledApp]:
        """Install an app on a server."""
        config = config or {}

        try:
            # Get app definition
            app = self.catalog_service.get_app(app_id)
            if not app:
                logger.error("App not found", app_id=app_id)
                return None

            # Get server
            server = await self.server_service.get_server(server_id)
            if not server:
                logger.error("Server not found", server_id=server_id)
                return None

            # Create installation record
            install_id = f"inst-{uuid.uuid4().hex[:8]}"
            container_name = f"{app_id}-{install_id[-4:]}"
            now = datetime.now(UTC).isoformat()

            installation = await self.db_service.create_installation(
                id=install_id,
                server_id=server_id,
                app_id=app_id,
                container_name=container_name,
                status=InstallationStatus.PENDING.value,
                config=config,
                installed_at=now
            )

            # Pull image
            await self.db_service.update_installation(
                install_id, status=InstallationStatus.PULLING.value
            )
            pull_cmd = f"docker pull {app.image}"
            exit_code, stdout, stderr = await self.ssh_service.execute_command(
                server_id, pull_cmd
            )
            if exit_code != 0:
                await self.db_service.update_installation(
                    install_id,
                    status=InstallationStatus.ERROR.value,
                    error_message=f"Failed to pull image: {stderr}"
                )
                return None

            # Run container
            await self.db_service.update_installation(
                install_id, status=InstallationStatus.CREATING.value
            )
            run_cmd = self._build_docker_run_command(app, container_name, config)
            exit_code, stdout, stderr = await self.ssh_service.execute_command(
                server_id, run_cmd
            )
            if exit_code != 0:
                await self.db_service.update_installation(
                    install_id,
                    status=InstallationStatus.ERROR.value,
                    error_message=f"Failed to create container: {stderr}"
                )
                return None

            # Get container ID
            container_id = stdout.strip()
            await self.db_service.update_installation(
                install_id,
                status=InstallationStatus.RUNNING.value,
                container_id=container_id,
                started_at=datetime.now(UTC).isoformat()
            )

            logger.info("App installed", app_id=app_id, server_id=server_id, container=container_name)
            return installation

        except Exception as e:
            logger.error("Install failed", error=str(e))
            return None

    async def uninstall_app(
        self,
        server_id: str,
        app_id: str,
        remove_data: bool = False
    ) -> bool:
        """Uninstall an app from a server."""
        try:
            installation = await self.db_service.get_installation(server_id, app_id)
            if not installation:
                logger.error("Installation not found", server_id=server_id, app_id=app_id)
                return False

            container_name = installation.container_name

            # Stop container
            stop_cmd = f"docker stop {container_name}"
            await self.ssh_service.execute_command(server_id, stop_cmd)

            # Remove container
            rm_cmd = f"docker rm {container_name}"
            if remove_data:
                rm_cmd += " -v"  # Remove volumes too
            await self.ssh_service.execute_command(server_id, rm_cmd)

            # Delete installation record
            await self.db_service.delete_installation(server_id, app_id)

            logger.info("App uninstalled", app_id=app_id, server_id=server_id)
            return True

        except Exception as e:
            logger.error("Uninstall failed", error=str(e))
            return False

    async def start_app(self, server_id: str, app_id: str) -> bool:
        """Start a stopped app."""
        try:
            installation = await self.db_service.get_installation(server_id, app_id)
            if not installation:
                return False

            cmd = f"docker start {installation.container_name}"
            exit_code, _, _ = await self.ssh_service.execute_command(server_id, cmd)

            if exit_code == 0:
                await self.db_service.update_installation(
                    installation.id,
                    status=InstallationStatus.RUNNING.value,
                    started_at=datetime.now(UTC).isoformat()
                )
                return True
            return False

        except Exception as e:
            logger.error("Start app failed", error=str(e))
            return False

    async def stop_app(self, server_id: str, app_id: str) -> bool:
        """Stop a running app."""
        try:
            installation = await self.db_service.get_installation(server_id, app_id)
            if not installation:
                return False

            cmd = f"docker stop {installation.container_name}"
            exit_code, _, _ = await self.ssh_service.execute_command(server_id, cmd)

            if exit_code == 0:
                await self.db_service.update_installation(
                    installation.id,
                    status=InstallationStatus.STOPPED.value
                )
                return True
            return False

        except Exception as e:
            logger.error("Stop app failed", error=str(e))
            return False

    async def get_app_status(self, server_id: str, app_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of an installed app."""
        try:
            installation = await self.db_service.get_installation(server_id, app_id)
            if not installation:
                return None

            # Check actual container status
            cmd = f"docker inspect --format '{{{{.State.Status}}}}' {installation.container_name}"
            exit_code, stdout, _ = await self.ssh_service.execute_command(server_id, cmd)

            container_status = stdout.strip() if exit_code == 0 else "unknown"

            return {
                "installation_id": installation.id,
                "app_id": app_id,
                "container_name": installation.container_name,
                "container_id": installation.container_id,
                "status": container_status,
                "installed_at": installation.installed_at,
                "started_at": installation.started_at
            }

        except Exception as e:
            logger.error("Get status failed", error=str(e))
            return None

    async def get_installed_apps(self, server_id: str) -> List[Dict[str, Any]]:
        """Get all installed apps for a server."""
        try:
            installations = await self.db_service.get_installations(server_id)
            return [
                {
                    "installation_id": inst.id,
                    "app_id": inst.app_id,
                    "container_name": inst.container_name,
                    "status": inst.status,
                    "installed_at": inst.installed_at
                }
                for inst in installations
            ]
        except Exception as e:
            logger.error("Get installed apps failed", error=str(e))
            return []
```

**Step 4: Run test to verify it passes**

```bash
cd /Users/christophebabilotte/source/homelab/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && PYTHONPATH=src pytest tests/unit/test_deployment_service.py -v --no-cov
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/services/deployment_service.py backend/tests/unit/test_deployment_service.py
git commit -m "feat(apps): add deployment service for Docker containers"
```

---

## Task 4: Add Installation Database Methods

**Files:**
- Modify: `backend/src/services/database_service.py`
- Test: `backend/tests/unit/test_app_database.py`

**Step 1: Write the failing test**

Create `backend/tests/unit/test_app_database.py`:

```python
"""Tests for app installation database operations."""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from contextlib import asynccontextmanager


class TestAppDatabaseOperations:
    """Tests for app installation CRUD in database."""

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
    async def test_create_installation(self, db_service, mock_connection):
        """Should create installation record."""
        result = await db_service.create_installation(
            id="inst-123",
            server_id="server-456",
            app_id="portainer",
            container_name="portainer-123",
            status="pending",
            config={"ports": {"9000": 9000}},
            installed_at="2025-01-01T00:00:00Z"
        )

        assert result is not None
        mock_connection.execute.assert_called()

    @pytest.mark.asyncio
    async def test_update_installation(self, db_service, mock_connection):
        """Should update installation record."""
        result = await db_service.update_installation(
            install_id="inst-123",
            status="running",
            container_id="abc123"
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_get_installation(self, db_service, mock_connection):
        """Should get installation by server and app ID."""
        mock_row = {
            "id": "inst-123",
            "server_id": "server-456",
            "app_id": "portainer",
            "container_id": "abc123",
            "container_name": "portainer-123",
            "status": "running",
            "config": '{"ports": {"9000": 9000}}',
            "installed_at": "2025-01-01T00:00:00Z",
            "started_at": "2025-01-01T00:01:00Z",
            "error_message": None
        }
        mock_connection.execute.return_value = MagicMock(
            fetchone=AsyncMock(return_value=mock_row)
        )

        result = await db_service.get_installation("server-456", "portainer")

        assert result is not None
        assert result.status == "running"

    @pytest.mark.asyncio
    async def test_get_installations(self, db_service, mock_connection):
        """Should get all installations for a server."""
        mock_rows = [
            {"id": "inst-1", "server_id": "server-456", "app_id": "portainer",
             "container_id": "abc", "container_name": "portainer-1",
             "status": "running", "config": "{}", "installed_at": "2025-01-01T00:00:00Z",
             "started_at": None, "error_message": None},
            {"id": "inst-2", "server_id": "server-456", "app_id": "nginx",
             "container_id": "def", "container_name": "nginx-1",
             "status": "stopped", "config": "{}", "installed_at": "2025-01-01T00:00:00Z",
             "started_at": None, "error_message": None}
        ]
        mock_connection.execute.return_value = MagicMock(
            fetchall=AsyncMock(return_value=mock_rows)
        )

        result = await db_service.get_installations("server-456")

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_delete_installation(self, db_service, mock_connection):
        """Should delete installation record."""
        result = await db_service.delete_installation("server-456", "portainer")

        assert result is True
        mock_connection.execute.assert_called()
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/christophebabilotte/source/homelab/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && PYTHONPATH=src pytest tests/unit/test_app_database.py -v --no-cov
```

Expected: FAIL

**Step 3: Add database methods to database_service.py**

Add to `backend/src/services/database_service.py`:

```python
# Add import at top
from models.app_catalog import InstalledApp, InstallationStatus
import json

async def create_installation(
    self,
    id: str,
    server_id: str,
    app_id: str,
    container_name: str,
    status: str,
    config: dict,
    installed_at: str
) -> Optional[InstalledApp]:
    """Create a new installation record."""
    try:
        config_json = json.dumps(config) if config else "{}"
        async with self.get_connection() as conn:
            await conn.execute(
                """INSERT INTO installed_apps
                   (id, server_id, app_id, container_name, status, config, installed_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (id, server_id, app_id, container_name, status, config_json, installed_at)
            )
            await conn.commit()

        return InstalledApp(
            id=id,
            server_id=server_id,
            app_id=app_id,
            container_name=container_name,
            status=InstallationStatus(status),
            config=config,
            installed_at=installed_at
        )
    except Exception as e:
        logger.error("Failed to create installation", error=str(e))
        return None

async def update_installation(self, install_id: str, **kwargs) -> bool:
    """Update installation record."""
    try:
        updates = []
        values = []
        for key, value in kwargs.items():
            if value is not None:
                updates.append(f"{key} = ?")
                values.append(value)

        if not updates:
            return True

        values.append(install_id)
        query = f"UPDATE installed_apps SET {', '.join(updates)} WHERE id = ?"

        async with self.get_connection() as conn:
            await conn.execute(query, values)
            await conn.commit()
        return True
    except Exception as e:
        logger.error("Failed to update installation", error=str(e))
        return False

async def get_installation(self, server_id: str, app_id: str) -> Optional[InstalledApp]:
    """Get installation by server and app ID."""
    try:
        async with self.get_connection() as conn:
            cursor = await conn.execute(
                """SELECT * FROM installed_apps
                   WHERE server_id = ? AND app_id = ?""",
                (server_id, app_id)
            )
            row = await cursor.fetchone()

        if not row:
            return None

        config = json.loads(row["config"]) if row["config"] else {}
        return InstalledApp(
            id=row["id"],
            server_id=row["server_id"],
            app_id=row["app_id"],
            container_id=row["container_id"],
            container_name=row["container_name"],
            status=InstallationStatus(row["status"]),
            config=config,
            installed_at=row["installed_at"],
            started_at=row["started_at"],
            error_message=row["error_message"]
        )
    except Exception as e:
        logger.error("Failed to get installation", error=str(e))
        return None

async def get_installations(self, server_id: str) -> list:
    """Get all installations for a server."""
    try:
        async with self.get_connection() as conn:
            cursor = await conn.execute(
                """SELECT * FROM installed_apps WHERE server_id = ?""",
                (server_id,)
            )
            rows = await cursor.fetchall()

        return [
            InstalledApp(
                id=row["id"],
                server_id=row["server_id"],
                app_id=row["app_id"],
                container_id=row["container_id"],
                container_name=row["container_name"],
                status=InstallationStatus(row["status"]),
                config=json.loads(row["config"]) if row["config"] else {},
                installed_at=row["installed_at"],
                started_at=row["started_at"],
                error_message=row["error_message"]
            )
            for row in rows
        ]
    except Exception as e:
        logger.error("Failed to get installations", error=str(e))
        return []

async def delete_installation(self, server_id: str, app_id: str) -> bool:
    """Delete installation record."""
    try:
        async with self.get_connection() as conn:
            await conn.execute(
                """DELETE FROM installed_apps WHERE server_id = ? AND app_id = ?""",
                (server_id, app_id)
            )
            await conn.commit()
        return True
    except Exception as e:
        logger.error("Failed to delete installation", error=str(e))
        return False
```

**Step 4: Run test to verify it passes**

```bash
cd /Users/christophebabilotte/source/homelab/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && PYTHONPATH=src pytest tests/unit/test_app_database.py -v --no-cov
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/services/database_service.py backend/tests/unit/test_app_database.py
git commit -m "feat(apps): add installation database CRUD methods"
```

---

## Task 5: Create App MCP Tools

**Files:**
- Create: `backend/src/tools/app_tools.py`
- Test: `backend/tests/unit/test_app_tools.py`

**Step 1: Write the failing test**

Create `backend/tests/unit/test_app_tools.py`:

```python
"""Tests for app MCP tools."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from tools.app_tools import AppTools
from models.app_catalog import AppDefinition, AppCategory, InstallationStatus


@pytest.fixture
def mock_catalog_service():
    """Create mock catalog service."""
    svc = MagicMock()
    svc.list_apps = MagicMock(return_value=[
        AppDefinition(
            id="portainer",
            name="Portainer",
            description="Docker management",
            category=AppCategory.UTILITY,
            image="portainer/portainer-ce:latest",
            ports=[], volumes=[], env_vars=[]
        )
    ])
    svc.get_app = MagicMock(return_value=AppDefinition(
        id="portainer",
        name="Portainer",
        description="Docker management",
        category=AppCategory.UTILITY,
        image="portainer/portainer-ce:latest",
        ports=[], volumes=[], env_vars=[]
    ))
    return svc


@pytest.fixture
def mock_deployment_service():
    """Create mock deployment service."""
    svc = MagicMock()
    svc.install_app = AsyncMock()
    svc.uninstall_app = AsyncMock()
    svc.start_app = AsyncMock()
    svc.stop_app = AsyncMock()
    svc.get_installed_apps = AsyncMock(return_value=[])
    svc.get_app_status = AsyncMock()
    return svc


@pytest.fixture
def app_tools(mock_catalog_service, mock_deployment_service):
    """Create app tools with mocks."""
    return AppTools(mock_catalog_service, mock_deployment_service)


class TestListCatalog:
    """Tests for list_catalog tool."""

    @pytest.mark.asyncio
    async def test_list_catalog_success(self, app_tools):
        """Should list all apps."""
        result = await app_tools.list_catalog()

        assert result["success"] is True
        assert len(result["data"]["apps"]) == 1

    @pytest.mark.asyncio
    async def test_list_catalog_with_category(self, app_tools, mock_catalog_service):
        """Should filter by category."""
        mock_catalog_service.list_apps.return_value = []

        result = await app_tools.list_catalog(category="storage")

        mock_catalog_service.list_apps.assert_called_with(category="storage")


class TestGetAppDefinition:
    """Tests for get_app_definition tool."""

    @pytest.mark.asyncio
    async def test_get_app_success(self, app_tools):
        """Should return app definition."""
        result = await app_tools.get_app_definition(app_id="portainer")

        assert result["success"] is True
        assert result["data"]["id"] == "portainer"

    @pytest.mark.asyncio
    async def test_get_app_not_found(self, app_tools, mock_catalog_service):
        """Should return error for unknown app."""
        mock_catalog_service.get_app.return_value = None

        result = await app_tools.get_app_definition(app_id="unknown")

        assert result["success"] is False
        assert result["error"] == "APP_NOT_FOUND"


class TestInstallApp:
    """Tests for install_app tool."""

    @pytest.mark.asyncio
    async def test_install_success(self, app_tools, mock_deployment_service):
        """Should install app successfully."""
        mock_deployment_service.install_app.return_value = MagicMock(id="inst-123")

        result = await app_tools.install_app(
            server_id="server-456",
            app_id="portainer",
            config={}
        )

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_install_failure(self, app_tools, mock_deployment_service):
        """Should handle install failure."""
        mock_deployment_service.install_app.return_value = None

        result = await app_tools.install_app(
            server_id="server-456",
            app_id="portainer",
            config={}
        )

        assert result["success"] is False


class TestUninstallApp:
    """Tests for uninstall_app tool."""

    @pytest.mark.asyncio
    async def test_uninstall_success(self, app_tools, mock_deployment_service):
        """Should uninstall app successfully."""
        mock_deployment_service.uninstall_app.return_value = True

        result = await app_tools.uninstall_app(
            server_id="server-456",
            app_id="portainer"
        )

        assert result["success"] is True
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/christophebabilotte/source/homelab/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && PYTHONPATH=src pytest tests/unit/test_app_tools.py -v --no-cov
```

Expected: FAIL

**Step 3: Create app tools**

Create `backend/src/tools/app_tools.py`:

```python
"""
App Catalog and Deployment Tools

Provides MCP tools for browsing catalog and managing app deployments.
"""

from typing import Dict, Any, Optional
import structlog
from fastmcp import FastMCP
from services.catalog_service import CatalogService
from services.deployment_service import DeploymentService

logger = structlog.get_logger("app_tools")


class AppTools:
    """App tools for the MCP server."""

    def __init__(self, catalog_service: CatalogService, deployment_service: DeploymentService):
        """Initialize app tools."""
        self.catalog_service = catalog_service
        self.deployment_service = deployment_service
        logger.info("App tools initialized")

    async def list_catalog(self, category: str = None) -> Dict[str, Any]:
        """List all available apps in the catalog."""
        try:
            apps = self.catalog_service.list_apps(category=category)
            return {
                "success": True,
                "data": {
                    "apps": [
                        {
                            "id": app.id,
                            "name": app.name,
                            "description": app.description,
                            "category": app.category.value,
                            "image": app.image
                        }
                        for app in apps
                    ],
                    "count": len(apps)
                },
                "message": f"Found {len(apps)} apps"
            }
        except Exception as e:
            logger.error("List catalog error", error=str(e))
            return {
                "success": False,
                "message": f"Failed to list catalog: {str(e)}",
                "error": "LIST_CATALOG_ERROR"
            }

    async def get_app_definition(self, app_id: str) -> Dict[str, Any]:
        """Get full app definition by ID."""
        try:
            app = self.catalog_service.get_app(app_id)
            if not app:
                return {
                    "success": False,
                    "message": f"App '{app_id}' not found",
                    "error": "APP_NOT_FOUND"
                }

            return {
                "success": True,
                "data": {
                    "id": app.id,
                    "name": app.name,
                    "description": app.description,
                    "category": app.category.value,
                    "image": app.image,
                    "ports": [p.model_dump() for p in app.ports],
                    "volumes": [v.model_dump() for v in app.volumes],
                    "env_vars": [e.model_dump() for e in app.env_vars],
                    "restart_policy": app.restart_policy,
                    "privileged": app.privileged
                },
                "message": "App definition retrieved"
            }
        except Exception as e:
            logger.error("Get app definition error", error=str(e))
            return {
                "success": False,
                "message": f"Failed to get app: {str(e)}",
                "error": "GET_APP_ERROR"
            }

    async def install_app(
        self,
        server_id: str,
        app_id: str,
        config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Install an app on a server."""
        try:
            installation = await self.deployment_service.install_app(
                server_id=server_id,
                app_id=app_id,
                config=config or {}
            )

            if not installation:
                return {
                    "success": False,
                    "message": "Failed to install app",
                    "error": "INSTALL_FAILED"
                }

            return {
                "success": True,
                "data": {
                    "installation_id": installation.id,
                    "server_id": server_id,
                    "app_id": app_id
                },
                "message": f"App '{app_id}' installation started"
            }
        except Exception as e:
            logger.error("Install app error", error=str(e))
            return {
                "success": False,
                "message": f"Failed to install: {str(e)}",
                "error": "INSTALL_ERROR"
            }

    async def uninstall_app(
        self,
        server_id: str,
        app_id: str,
        remove_data: bool = False
    ) -> Dict[str, Any]:
        """Uninstall an app from a server."""
        try:
            success = await self.deployment_service.uninstall_app(
                server_id=server_id,
                app_id=app_id,
                remove_data=remove_data
            )

            if not success:
                return {
                    "success": False,
                    "message": "Failed to uninstall app",
                    "error": "UNINSTALL_FAILED"
                }

            return {
                "success": True,
                "data": {"server_id": server_id, "app_id": app_id},
                "message": f"App '{app_id}' uninstalled"
            }
        except Exception as e:
            logger.error("Uninstall app error", error=str(e))
            return {
                "success": False,
                "message": f"Failed to uninstall: {str(e)}",
                "error": "UNINSTALL_ERROR"
            }

    async def get_installed_apps(self, server_id: str) -> Dict[str, Any]:
        """Get all installed apps on a server."""
        try:
            apps = await self.deployment_service.get_installed_apps(server_id)
            return {
                "success": True,
                "data": {"apps": apps, "count": len(apps)},
                "message": f"Found {len(apps)} installed apps"
            }
        except Exception as e:
            logger.error("Get installed apps error", error=str(e))
            return {
                "success": False,
                "message": f"Failed to get installed apps: {str(e)}",
                "error": "GET_INSTALLED_ERROR"
            }

    async def start_app(self, server_id: str, app_id: str) -> Dict[str, Any]:
        """Start a stopped app."""
        try:
            success = await self.deployment_service.start_app(server_id, app_id)
            if not success:
                return {
                    "success": False,
                    "message": "Failed to start app",
                    "error": "START_FAILED"
                }
            return {
                "success": True,
                "data": {"server_id": server_id, "app_id": app_id},
                "message": f"App '{app_id}' started"
            }
        except Exception as e:
            logger.error("Start app error", error=str(e))
            return {
                "success": False,
                "message": f"Failed to start: {str(e)}",
                "error": "START_ERROR"
            }

    async def stop_app(self, server_id: str, app_id: str) -> Dict[str, Any]:
        """Stop a running app."""
        try:
            success = await self.deployment_service.stop_app(server_id, app_id)
            if not success:
                return {
                    "success": False,
                    "message": "Failed to stop app",
                    "error": "STOP_FAILED"
                }
            return {
                "success": True,
                "data": {"server_id": server_id, "app_id": app_id},
                "message": f"App '{app_id}' stopped"
            }
        except Exception as e:
            logger.error("Stop app error", error=str(e))
            return {
                "success": False,
                "message": f"Failed to stop: {str(e)}",
                "error": "STOP_ERROR"
            }


def register_app_tools(app: FastMCP, catalog_service: CatalogService, deployment_service: DeploymentService):
    """Register app tools with FastMCP app."""
    tools = AppTools(catalog_service, deployment_service)

    app.tool(tools.list_catalog)
    app.tool(tools.get_app_definition)
    app.tool(tools.install_app)
    app.tool(tools.uninstall_app)
    app.tool(tools.get_installed_apps)
    app.tool(tools.start_app)
    app.tool(tools.stop_app)

    logger.info("App tools registered")
```

**Step 4: Run test to verify it passes**

```bash
cd /Users/christophebabilotte/source/homelab/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && PYTHONPATH=src pytest tests/unit/test_app_tools.py -v --no-cov
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/tools/app_tools.py backend/tests/unit/test_app_tools.py
git commit -m "feat(apps): add app catalog and deployment MCP tools"
```

---

## Task 6: Create Curated App Definitions

**Files:**
- Create: `backend/data/catalog/nginx-proxy-manager.yaml`
- Create: `backend/data/catalog/nextcloud.yaml`
- Create: `backend/data/catalog/jellyfin.yaml`
- Create: `backend/data/catalog/pihole.yaml`

**Step 1: Create Nginx Proxy Manager definition**

Create `backend/data/catalog/nginx-proxy-manager.yaml`:

```yaml
id: nginx-proxy-manager
name: Nginx Proxy Manager
description: Easy-to-use reverse proxy with SSL support and web UI
category: networking
image: jc21/nginx-proxy-manager:latest
ports:
  - container: 80
    host: 80
  - container: 443
    host: 443
  - container: 81
    host: 81
volumes:
  - host_path: /var/npm/data
    container_path: /data
  - host_path: /var/npm/letsencrypt
    container_path: /etc/letsencrypt
restart_policy: unless-stopped
```

**Step 2: Create Nextcloud definition**

Create `backend/data/catalog/nextcloud.yaml`:

```yaml
id: nextcloud
name: Nextcloud
description: Personal cloud storage and collaboration platform
category: storage
image: nextcloud:latest
ports:
  - container: 80
    host: 8080
volumes:
  - host_path: /var/nextcloud/data
    container_path: /var/www/html
env:
  - name: MYSQL_HOST
    description: MySQL database host
    required: false
  - name: MYSQL_DATABASE
    description: MySQL database name
    required: false
  - name: MYSQL_USER
    description: MySQL username
    required: false
  - name: MYSQL_PASSWORD
    description: MySQL password
    required: false
restart_policy: unless-stopped
```

**Step 3: Create Jellyfin definition**

Create `backend/data/catalog/jellyfin.yaml`:

```yaml
id: jellyfin
name: Jellyfin
description: Free media server for movies, TV, and music
category: media
image: jellyfin/jellyfin:latest
ports:
  - container: 8096
    host: 8096
  - container: 8920
    host: 8920
volumes:
  - host_path: /var/jellyfin/config
    container_path: /config
  - host_path: /var/jellyfin/cache
    container_path: /cache
  - host_path: /media
    container_path: /media
    readonly: true
restart_policy: unless-stopped
```

**Step 4: Create Pi-hole definition**

Create `backend/data/catalog/pihole.yaml`:

```yaml
id: pihole
name: Pi-hole
description: Network-wide ad blocking and DNS server
category: networking
image: pihole/pihole:latest
ports:
  - container: 53
    host: 53
    protocol: tcp
  - container: 53
    host: 53
    protocol: udp
  - container: 80
    host: 8053
volumes:
  - host_path: /var/pihole/etc
    container_path: /etc/pihole
  - host_path: /var/pihole/dnsmasq
    container_path: /etc/dnsmasq.d
env:
  - name: WEBPASSWORD
    description: Admin password for web interface
    required: true
  - name: TZ
    description: Timezone
    required: false
    default: UTC
capabilities:
  - NET_ADMIN
restart_policy: unless-stopped
```

**Step 5: Commit**

```bash
git add backend/data/catalog/*.yaml
git commit -m "feat(apps): add curated app definitions for v1.0"
```

---

## Task 7: Verify All Phase 4 Tests Pass

**Step 1: Run all Phase 4 tests**

```bash
cd /Users/christophebabilotte/source/homelab/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && PYTHONPATH=src pytest tests/unit/test_app*.py tests/unit/test_catalog*.py tests/unit/test_deployment*.py -v --no-cov
```

**Step 2: Run all project tests to ensure no regressions**

```bash
cd /Users/christophebabilotte/source/homelab/backend && source /Users/christophebabilotte/source/pythonvenv/bin/activate && PYTHONPATH=src pytest tests/unit/test_auth*.py tests/unit/test_server*.py tests/unit/test_preparation*.py tests/unit/test_app*.py tests/unit/test_catalog*.py tests/unit/test_deployment*.py tests/unit/test_health*.py tests/unit/test_cli.py -v --no-cov
```

**Step 3: Commit if any fixes needed**

```bash
git add .
git commit -m "fix(apps): fix test failures in Phase 4"
```

---

## Quality Gates Checklist

- [ ] App definition models created (AppDefinition, InstalledApp)
- [ ] Database schema for installations
- [ ] Catalog service loads YAML files
- [ ] Deployment service builds docker commands
- [ ] MCP tools implemented:
  - [ ] list_catalog
  - [ ] get_app_definition
  - [ ] install_app
  - [ ] uninstall_app
  - [ ] get_installed_apps
  - [ ] start_app
  - [ ] stop_app
- [ ] Curated apps defined (Portainer, NPM, Nextcloud, Jellyfin, Pi-hole)
- [ ] All unit tests pass

---

## Definition of Done

Backend can:
1. Load app definitions from YAML catalog
2. List and filter apps by category
3. Install apps to servers (pull image, run container)
4. Start/stop/uninstall apps
5. Track installation status

Note: Actual Docker deployment will be tested with real VMs in integration testing.

---

**Document Version:** 1.0
**Created:** 2025-12-26
