# Homelab Marketplace Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a community app marketplace with Git-based repositories, YAML app definitions, star ratings, and rich discovery features.

**Architecture:** Git repositories (central + user forks) store YAML app definitions. Backend syncs repos to local SQLite for fast queries. Frontend provides browsing, search, filtering, and rating UI. Apps deploy via existing Docker deployment service.

**Tech Stack:** Python/FastMCP backend, SQLAlchemy/SQLite, React/TypeScript/TailwindCSS frontend, Git CLI for repo operations, PyYAML for parsing.

---

## Phase 1: Marketplace Data Models

### Task 1.1: Create Marketplace Repository Model

**Files:**
- Create: `backend/src/models/marketplace.py`
- Test: `backend/tests/unit/test_marketplace_models.py`

**Step 1: Write the failing test**

```python
# backend/tests/unit/test_marketplace_models.py
import pytest
from models.marketplace import MarketplaceRepo, RepoType

def test_marketplace_repo_model():
    repo = MarketplaceRepo(
        id="official",
        name="Official Homelab Apps",
        url="https://github.com/homelab/app-catalog",
        repo_type=RepoType.OFFICIAL,
        enabled=True
    )
    assert repo.id == "official"
    assert repo.repo_type == RepoType.OFFICIAL
    assert repo.enabled is True
```

**Step 2: Run test to verify it fails**

Run: `cd backend && source venv/bin/activate && PYTHONPATH=src pytest tests/unit/test_marketplace_models.py -v`
Expected: FAIL with "No module named 'models.marketplace'"

**Step 3: Write minimal implementation**

```python
# backend/src/models/marketplace.py
"""Marketplace data models for Git-based app repositories."""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from pydantic.alias_generators import to_camel


class RepoType(str, Enum):
    """Repository type classification."""
    OFFICIAL = "official"
    COMMUNITY = "community"
    PERSONAL = "personal"


class RepoStatus(str, Enum):
    """Repository sync status."""
    ACTIVE = "active"
    SYNCING = "syncing"
    ERROR = "error"
    DISABLED = "disabled"


class MarketplaceRepo(BaseModel):
    """Git repository source for marketplace apps."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: str = Field(..., description="Unique repository identifier")
    name: str = Field(..., description="Display name")
    url: str = Field(..., description="Git repository URL")
    branch: str = Field(default="main", description="Git branch to sync")
    repo_type: RepoType = Field(default=RepoType.COMMUNITY, description="Repository type")
    enabled: bool = Field(default=True, description="Whether repo is enabled")
    status: RepoStatus = Field(default=RepoStatus.ACTIVE, description="Sync status")
    last_synced: Optional[str] = Field(None, description="Last sync timestamp")
    app_count: int = Field(default=0, description="Number of apps in repo")
    error_message: Optional[str] = Field(None, description="Last error if any")
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
```

**Step 4: Run test to verify it passes**

Run: `cd backend && source venv/bin/activate && PYTHONPATH=src pytest tests/unit/test_marketplace_models.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/models/marketplace.py backend/tests/unit/test_marketplace_models.py
git commit -m "feat(marketplace): add MarketplaceRepo model"
```

---

### Task 1.2: Add MarketplaceApp Model

**Files:**
- Modify: `backend/src/models/marketplace.py`
- Test: `backend/tests/unit/test_marketplace_models.py`

**Step 1: Write the failing test**

```python
# Add to backend/tests/unit/test_marketplace_models.py
from models.marketplace import MarketplaceApp, DockerConfig, AppPort, AppVolume

def test_marketplace_app_model():
    app = MarketplaceApp(
        id="jellyfin",
        name="Jellyfin",
        description="Free media system",
        version="10.8.13",
        category="media",
        repo_id="official",
        docker=DockerConfig(
            image="jellyfin/jellyfin:latest",
            ports=[AppPort(container=8096, host=8096)],
            volumes=[AppVolume(host_path="/config", container_path="/config")]
        )
    )
    assert app.id == "jellyfin"
    assert app.docker.image == "jellyfin/jellyfin:latest"
    assert len(app.docker.ports) == 1
```

**Step 2: Run test to verify it fails**

Run: `cd backend && source venv/bin/activate && PYTHONPATH=src pytest tests/unit/test_marketplace_models.py::test_marketplace_app_model -v`
Expected: FAIL with "cannot import name 'MarketplaceApp'"

**Step 3: Write minimal implementation**

```python
# Add to backend/src/models/marketplace.py

class AppPort(BaseModel):
    """Docker port mapping."""
    container: int = Field(..., description="Container port")
    host: int = Field(..., description="Host port")
    protocol: str = Field(default="tcp", description="Protocol (tcp/udp)")


class AppVolume(BaseModel):
    """Docker volume mapping."""
    host_path: str = Field(..., description="Path on host")
    container_path: str = Field(..., description="Path in container")
    readonly: bool = Field(default=False, description="Read-only mount")


class AppEnvVar(BaseModel):
    """Docker environment variable."""
    name: str = Field(..., description="Variable name")
    description: Optional[str] = Field(None, description="Help text")
    required: bool = Field(default=False, description="Is required")
    default: Optional[str] = Field(None, description="Default value")


class DockerConfig(BaseModel):
    """Docker container configuration."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    image: str = Field(..., description="Docker image")
    ports: List[AppPort] = Field(default_factory=list, description="Port mappings")
    volumes: List[AppVolume] = Field(default_factory=list, description="Volume mappings")
    environment: List[AppEnvVar] = Field(default_factory=list, description="Environment variables")
    restart_policy: str = Field(default="unless-stopped", description="Restart policy")
    network_mode: Optional[str] = Field(None, description="Network mode")
    privileged: bool = Field(default=False, description="Privileged mode")
    capabilities: List[str] = Field(default_factory=list, description="Linux capabilities")


class AppRequirements(BaseModel):
    """System requirements for an app."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    min_ram: Optional[int] = Field(None, description="Minimum RAM in MB")
    min_storage: Optional[int] = Field(None, description="Minimum storage in GB")
    architectures: List[str] = Field(default_factory=lambda: ["amd64", "arm64"])


class MarketplaceApp(BaseModel):
    """Application from marketplace repository."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: str = Field(..., description="Unique app identifier")
    name: str = Field(..., description="Display name")
    description: str = Field(..., description="Short description")
    long_description: Optional[str] = Field(None, description="Detailed description")
    version: str = Field(..., description="App version")
    category: str = Field(..., description="Category ID")
    tags: List[str] = Field(default_factory=list, description="Search tags")
    icon: Optional[str] = Field(None, description="Icon URL or name")
    author: str = Field(default="Community", description="Author name")
    license: str = Field(default="MIT", description="License")
    repository: Optional[str] = Field(None, description="Source repo URL")
    documentation: Optional[str] = Field(None, description="Docs URL")

    # Git source
    repo_id: str = Field(..., description="Source marketplace repo ID")

    # Docker config
    docker: DockerConfig = Field(..., description="Docker configuration")

    # Requirements
    requirements: AppRequirements = Field(default_factory=AppRequirements)

    # Metrics (local)
    install_count: int = Field(default=0, description="Local install count")
    avg_rating: Optional[float] = Field(None, ge=0, le=5, description="Average rating")
    rating_count: int = Field(default=0, description="Number of ratings")
    featured: bool = Field(default=False, description="Featured flag")

    # Timestamps
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
```

**Step 4: Run test to verify it passes**

Run: `cd backend && source venv/bin/activate && PYTHONPATH=src pytest tests/unit/test_marketplace_models.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/models/marketplace.py backend/tests/unit/test_marketplace_models.py
git commit -m "feat(marketplace): add MarketplaceApp and DockerConfig models"
```

---

### Task 1.3: Add AppRating Model

**Files:**
- Modify: `backend/src/models/marketplace.py`
- Test: `backend/tests/unit/test_marketplace_models.py`

**Step 1: Write the failing test**

```python
# Add to backend/tests/unit/test_marketplace_models.py
from models.marketplace import AppRating

def test_app_rating_model():
    rating = AppRating(
        id="rating-123",
        app_id="jellyfin",
        user_id="user-456",
        rating=5
    )
    assert rating.rating == 5
    assert rating.app_id == "jellyfin"
```

**Step 2: Run test to verify it fails**

Run: `cd backend && source venv/bin/activate && PYTHONPATH=src pytest tests/unit/test_marketplace_models.py::test_app_rating_model -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# Add to backend/src/models/marketplace.py

class AppRating(BaseModel):
    """User rating for an app."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: str = Field(..., description="Rating ID")
    app_id: str = Field(..., description="App being rated")
    user_id: str = Field(..., description="User who rated")
    rating: int = Field(..., ge=1, le=5, description="1-5 star rating")
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
```

**Step 4: Run test to verify it passes**

Run: `cd backend && source venv/bin/activate && PYTHONPATH=src pytest tests/unit/test_marketplace_models.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/models/marketplace.py backend/tests/unit/test_marketplace_models.py
git commit -m "feat(marketplace): add AppRating model"
```

---

### Task 1.4: Create Database Tables

**Files:**
- Create: `backend/src/init_db/schema_marketplace.py`
- Test: `backend/tests/unit/test_marketplace_schema.py`

**Step 1: Write the failing test**

```python
# backend/tests/unit/test_marketplace_schema.py
import pytest
from init_db.schema_marketplace import MarketplaceRepoTable, MarketplaceAppTable, AppRatingTable

def test_marketplace_tables_exist():
    assert MarketplaceRepoTable.__tablename__ == "marketplace_repos"
    assert MarketplaceAppTable.__tablename__ == "marketplace_apps"
    assert AppRatingTable.__tablename__ == "app_ratings"
```

**Step 2: Run test to verify it fails**

Run: `cd backend && source venv/bin/activate && PYTHONPATH=src pytest tests/unit/test_marketplace_schema.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# backend/src/init_db/schema_marketplace.py
"""Database schema for marketplace repositories and apps."""

from sqlalchemy import Column, String, Text, Integer, Float, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from database.connection import Base, db_manager
import structlog

logger = structlog.get_logger("schema_marketplace")


class MarketplaceRepoTable(Base):
    """SQLAlchemy table for marketplace repositories."""

    __tablename__ = "marketplace_repos"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    branch = Column(String, default="main")
    repo_type = Column(String, nullable=False, default="community")
    enabled = Column(Boolean, default=True)
    status = Column(String, default="active")
    last_synced = Column(DateTime, nullable=True)
    app_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())


class MarketplaceAppTable(Base):
    """SQLAlchemy table for marketplace apps."""

    __tablename__ = "marketplace_apps"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    long_description = Column(Text, nullable=True)
    version = Column(String, nullable=False)
    category = Column(String, nullable=False, index=True)
    tags = Column(Text, nullable=True)  # JSON array
    icon = Column(String, nullable=True)
    author = Column(String, nullable=False)
    license = Column(String, nullable=False)
    repository = Column(String, nullable=True)
    documentation = Column(String, nullable=True)

    repo_id = Column(String, ForeignKey("marketplace_repos.id"), nullable=False, index=True)
    docker_config = Column(Text, nullable=False)  # JSON
    requirements = Column(Text, nullable=True)  # JSON

    install_count = Column(Integer, default=0)
    avg_rating = Column(Float, nullable=True)
    rating_count = Column(Integer, default=0)
    featured = Column(Boolean, default=False)

    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_marketplace_apps_repo_category", "repo_id", "category"),
    )


class AppRatingTable(Base):
    """SQLAlchemy table for app ratings."""

    __tablename__ = "app_ratings"

    id = Column(String, primary_key=True)
    app_id = Column(String, ForeignKey("marketplace_apps.id"), nullable=False, index=True)
    user_id = Column(String, nullable=False, index=True)
    rating = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_app_ratings_app_user", "app_id", "user_id", unique=True),
    )


async def initialize_marketplace_database():
    """Create marketplace tables if they don't exist."""
    if not db_manager.engine:
        await db_manager.initialize()

    async with db_manager.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Marketplace database schema initialized")
```

**Step 4: Run test to verify it passes**

Run: `cd backend && source venv/bin/activate && PYTHONPATH=src pytest tests/unit/test_marketplace_schema.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/init_db/schema_marketplace.py backend/tests/unit/test_marketplace_schema.py
git commit -m "feat(marketplace): add database schema for repos, apps, ratings"
```

---

## Phase 2: Marketplace Service

### Task 2.1: Create MarketplaceService with Repo Management

**Files:**
- Create: `backend/src/services/marketplace_service.py`
- Test: `backend/tests/unit/test_marketplace_service.py`

**Step 1: Write the failing test**

```python
# backend/tests/unit/test_marketplace_service.py
import pytest
from services.marketplace_service import MarketplaceService
from models.marketplace import MarketplaceRepo, RepoType

@pytest.fixture
def marketplace_service():
    return MarketplaceService()

@pytest.mark.asyncio
async def test_add_repo(marketplace_service):
    repo = await marketplace_service.add_repo(
        name="Test Repo",
        url="https://github.com/test/apps",
        repo_type=RepoType.PERSONAL
    )
    assert repo.name == "Test Repo"
    assert repo.repo_type == RepoType.PERSONAL
```

**Step 2: Run test to verify it fails**

Run: `cd backend && source venv/bin/activate && PYTHONPATH=src pytest tests/unit/test_marketplace_service.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# backend/src/services/marketplace_service.py
"""Marketplace service for managing Git-based app repositories."""

import json
import uuid
from datetime import datetime, UTC
from typing import List, Optional, Dict, Any

import structlog
from sqlalchemy import select, delete, update

from database.connection import db_manager
from init_db.schema_marketplace import (
    MarketplaceRepoTable, MarketplaceAppTable, AppRatingTable,
    initialize_marketplace_database
)
from models.marketplace import (
    MarketplaceRepo, MarketplaceApp, AppRating,
    RepoType, RepoStatus, DockerConfig, AppRequirements
)

logger = structlog.get_logger("marketplace_service")


class MarketplaceService:
    """Service for managing marketplace repositories and apps."""

    def __init__(self):
        self._initialized = False
        logger.info("Marketplace service initialized")

    async def _ensure_initialized(self):
        if not self._initialized:
            await initialize_marketplace_database()
            self._initialized = True

    # ─────────────────────────────────────────────────────────────
    # Repository Management
    # ─────────────────────────────────────────────────────────────

    async def add_repo(
        self,
        name: str,
        url: str,
        repo_type: RepoType = RepoType.COMMUNITY,
        branch: str = "main"
    ) -> MarketplaceRepo:
        """Add a new repository source."""
        await self._ensure_initialized()

        repo_id = f"repo-{uuid.uuid4().hex[:8]}"
        now = datetime.now(UTC).isoformat()

        repo = MarketplaceRepo(
            id=repo_id,
            name=name,
            url=url,
            branch=branch,
            repo_type=repo_type,
            enabled=True,
            status=RepoStatus.ACTIVE,
            created_at=now,
            updated_at=now
        )

        async with db_manager.get_session() as session:
            table_row = MarketplaceRepoTable(
                id=repo.id,
                name=repo.name,
                url=repo.url,
                branch=repo.branch,
                repo_type=repo.repo_type.value,
                enabled=repo.enabled,
                status=repo.status.value,
                app_count=0
            )
            session.add(table_row)

        logger.info("Repository added", repo_id=repo_id, name=name)
        return repo

    async def get_repos(self, enabled_only: bool = False) -> List[MarketplaceRepo]:
        """Get all repositories."""
        await self._ensure_initialized()

        async with db_manager.get_session() as session:
            query = select(MarketplaceRepoTable)
            if enabled_only:
                query = query.where(MarketplaceRepoTable.enabled == True)

            result = await session.execute(query)
            rows = result.scalars().all()

        return [self._repo_from_table(row) for row in rows]

    async def get_repo(self, repo_id: str) -> Optional[MarketplaceRepo]:
        """Get repository by ID."""
        await self._ensure_initialized()

        async with db_manager.get_session() as session:
            result = await session.execute(
                select(MarketplaceRepoTable).where(MarketplaceRepoTable.id == repo_id)
            )
            row = result.scalar_one_or_none()

        return self._repo_from_table(row) if row else None

    async def remove_repo(self, repo_id: str) -> bool:
        """Remove a repository and its apps."""
        await self._ensure_initialized()

        async with db_manager.get_session() as session:
            # Delete apps from this repo
            await session.execute(
                delete(MarketplaceAppTable).where(MarketplaceAppTable.repo_id == repo_id)
            )
            # Delete repo
            result = await session.execute(
                delete(MarketplaceRepoTable).where(MarketplaceRepoTable.id == repo_id)
            )

        deleted = result.rowcount > 0
        if deleted:
            logger.info("Repository removed", repo_id=repo_id)
        return deleted

    async def toggle_repo(self, repo_id: str, enabled: bool) -> bool:
        """Enable or disable a repository."""
        await self._ensure_initialized()

        async with db_manager.get_session() as session:
            result = await session.execute(
                update(MarketplaceRepoTable)
                .where(MarketplaceRepoTable.id == repo_id)
                .values(enabled=enabled, updated_at=datetime.now(UTC))
            )

        return result.rowcount > 0

    @staticmethod
    def _repo_from_table(row: MarketplaceRepoTable) -> MarketplaceRepo:
        """Convert table row to model."""
        return MarketplaceRepo(
            id=row.id,
            name=row.name,
            url=row.url,
            branch=row.branch,
            repo_type=RepoType(row.repo_type),
            enabled=row.enabled,
            status=RepoStatus(row.status),
            last_synced=row.last_synced.isoformat() if row.last_synced else None,
            app_count=row.app_count,
            error_message=row.error_message,
            created_at=row.created_at.isoformat() if row.created_at else datetime.now(UTC).isoformat(),
            updated_at=row.updated_at.isoformat() if row.updated_at else datetime.now(UTC).isoformat()
        )
```

**Step 4: Run test to verify it passes**

Run: `cd backend && source venv/bin/activate && PYTHONPATH=src pytest tests/unit/test_marketplace_service.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/services/marketplace_service.py backend/tests/unit/test_marketplace_service.py
git commit -m "feat(marketplace): add MarketplaceService with repo management"
```

---

### Task 2.2: Add Git Sync Functionality

**Files:**
- Modify: `backend/src/services/marketplace_service.py`
- Create: `backend/src/lib/git_sync.py`
- Test: `backend/tests/unit/test_git_sync.py`

**Step 1: Write the failing test**

```python
# backend/tests/unit/test_git_sync.py
import pytest
from lib.git_sync import GitSync

def test_parse_app_yaml():
    yaml_content = """
name: jellyfin
version: 10.8.13
description: Free media system
category: media
tags:
  - streaming
  - movies
docker:
  image: jellyfin/jellyfin:latest
  ports:
    - container: 8096
      host: 8096
"""
    sync = GitSync()
    app = sync.parse_app_yaml(yaml_content, "official")

    assert app.name == "jellyfin"
    assert app.category == "media"
    assert app.docker.image == "jellyfin/jellyfin:latest"
```

**Step 2: Run test to verify it fails**

Run: `cd backend && source venv/bin/activate && PYTHONPATH=src pytest tests/unit/test_git_sync.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# backend/src/lib/git_sync.py
"""Git repository sync utilities for marketplace."""

import os
import shutil
import tempfile
import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Any

import yaml
import structlog

from models.marketplace import (
    MarketplaceApp, DockerConfig, AppRequirements,
    AppPort, AppVolume, AppEnvVar
)

logger = structlog.get_logger("git_sync")


class GitSync:
    """Handles Git repository synchronization."""

    def __init__(self, cache_dir: str = None):
        self.cache_dir = cache_dir or tempfile.mkdtemp(prefix="homelab-marketplace-")
        os.makedirs(self.cache_dir, exist_ok=True)

    def clone_or_pull(self, repo_url: str, branch: str = "main") -> Path:
        """Clone repo or pull if exists. Returns path to repo."""
        # Create safe directory name from URL
        repo_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
        repo_path = Path(self.cache_dir) / repo_name

        try:
            if repo_path.exists():
                # Pull latest
                subprocess.run(
                    ["git", "-C", str(repo_path), "fetch", "origin", branch],
                    check=True, capture_output=True
                )
                subprocess.run(
                    ["git", "-C", str(repo_path), "reset", "--hard", f"origin/{branch}"],
                    check=True, capture_output=True
                )
                logger.debug("Pulled latest", repo=repo_name, branch=branch)
            else:
                # Clone
                subprocess.run(
                    ["git", "clone", "--branch", branch, "--depth", "1", repo_url, str(repo_path)],
                    check=True, capture_output=True
                )
                logger.debug("Cloned repo", repo=repo_name, branch=branch)

            return repo_path

        except subprocess.CalledProcessError as e:
            logger.error("Git operation failed", repo=repo_url, error=e.stderr.decode())
            raise RuntimeError(f"Git operation failed: {e.stderr.decode()}")

    def find_app_files(self, repo_path: Path) -> List[Path]:
        """Find all app.yaml files in repository."""
        app_files = []

        # Look for apps/ directory first
        apps_dir = repo_path / "apps"
        if apps_dir.exists():
            for app_dir in apps_dir.iterdir():
                if app_dir.is_dir():
                    for yaml_file in ["app.yaml", "app.yml"]:
                        yaml_path = app_dir / yaml_file
                        if yaml_path.exists():
                            app_files.append(yaml_path)
                            break

        # Also check root for single-app repos
        for yaml_file in ["app.yaml", "app.yml"]:
            yaml_path = repo_path / yaml_file
            if yaml_path.exists():
                app_files.append(yaml_path)

        return app_files

    def parse_app_yaml(self, content: str, repo_id: str) -> MarketplaceApp:
        """Parse YAML content into MarketplaceApp."""
        data = yaml.safe_load(content)

        # Parse docker config
        docker_data = data.get("docker", {})
        ports = [
            AppPort(
                container=p.get("container", p) if isinstance(p, dict) else p,
                host=p.get("host", p) if isinstance(p, dict) else p,
                protocol=p.get("protocol", "tcp") if isinstance(p, dict) else "tcp"
            )
            for p in docker_data.get("ports", [])
        ]

        volumes = []
        for v in docker_data.get("volumes", []):
            if isinstance(v, str):
                parts = v.split(":")
                volumes.append(AppVolume(
                    host_path=parts[0],
                    container_path=parts[1] if len(parts) > 1 else parts[0],
                    readonly=len(parts) > 2 and parts[2] == "ro"
                ))
            else:
                volumes.append(AppVolume(
                    host_path=v.get("host_path", v.get("host", "")),
                    container_path=v.get("container_path", v.get("container", "")),
                    readonly=v.get("readonly", False)
                ))

        env_vars = []
        for e in docker_data.get("environment", docker_data.get("env", [])):
            if isinstance(e, str):
                if "=" in e:
                    name, default = e.split("=", 1)
                    env_vars.append(AppEnvVar(name=name, default=default))
                else:
                    env_vars.append(AppEnvVar(name=e, required=True))
            else:
                env_vars.append(AppEnvVar(
                    name=e.get("name"),
                    description=e.get("description"),
                    required=e.get("required", False),
                    default=e.get("default")
                ))

        docker_config = DockerConfig(
            image=docker_data.get("image", ""),
            ports=ports,
            volumes=volumes,
            environment=env_vars,
            restart_policy=docker_data.get("restart_policy", "unless-stopped"),
            network_mode=docker_data.get("network_mode"),
            privileged=docker_data.get("privileged", False),
            capabilities=docker_data.get("capabilities", [])
        )

        # Parse requirements
        req_data = data.get("requirements", {})
        requirements = AppRequirements(
            min_ram=req_data.get("min_ram"),
            min_storage=req_data.get("min_storage"),
            architectures=req_data.get("architectures", ["amd64", "arm64"])
        )

        return MarketplaceApp(
            id=data.get("id", data.get("name", "").lower().replace(" ", "-")),
            name=data.get("name", ""),
            description=data.get("description", ""),
            long_description=data.get("long_description"),
            version=data.get("version", "1.0.0"),
            category=data.get("category", "utility"),
            tags=data.get("tags", []),
            icon=data.get("icon"),
            author=data.get("author", "Community"),
            license=data.get("license", "MIT"),
            repository=data.get("repository"),
            documentation=data.get("documentation"),
            repo_id=repo_id,
            docker=docker_config,
            requirements=requirements
        )

    def load_app_from_file(self, file_path: Path, repo_id: str) -> Optional[MarketplaceApp]:
        """Load and parse an app.yaml file."""
        try:
            content = file_path.read_text()
            return self.parse_app_yaml(content, repo_id)
        except Exception as e:
            logger.error("Failed to parse app file", path=str(file_path), error=str(e))
            return None

    def cleanup(self):
        """Remove cached repositories."""
        if self.cache_dir and Path(self.cache_dir).exists():
            shutil.rmtree(self.cache_dir, ignore_errors=True)
```

**Step 4: Run test to verify it passes**

Run: `cd backend && source venv/bin/activate && PYTHONPATH=src pytest tests/unit/test_git_sync.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/lib/git_sync.py backend/tests/unit/test_git_sync.py
git commit -m "feat(marketplace): add GitSync for parsing app YAML files"
```

---

### Task 2.3: Integrate Sync into MarketplaceService

**Files:**
- Modify: `backend/src/services/marketplace_service.py`
- Test: `backend/tests/unit/test_marketplace_service.py`

**Step 1: Write the failing test**

```python
# Add to backend/tests/unit/test_marketplace_service.py
@pytest.mark.asyncio
async def test_sync_repo(marketplace_service, tmp_path):
    # Create a mock repo with app.yaml
    apps_dir = tmp_path / "apps" / "testapp"
    apps_dir.mkdir(parents=True)
    (apps_dir / "app.yaml").write_text("""
name: Test App
version: 1.0.0
description: A test application
category: utility
docker:
  image: test/app:latest
  ports:
    - container: 8080
      host: 8080
""")

    # Add repo pointing to local path
    repo = await marketplace_service.add_repo(
        name="Local Test",
        url=str(tmp_path),
        repo_type=RepoType.PERSONAL
    )

    # Sync (mock Git operations)
    apps = await marketplace_service.sync_repo(repo.id, local_path=tmp_path)

    assert len(apps) == 1
    assert apps[0].name == "Test App"
```

**Step 2: Run test to verify it fails**

Run: `cd backend && source venv/bin/activate && PYTHONPATH=src pytest tests/unit/test_marketplace_service.py::test_sync_repo -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Add to `backend/src/services/marketplace_service.py`:

```python
# Add import at top
from lib.git_sync import GitSync
from pathlib import Path

# Add to MarketplaceService class:

    async def sync_repo(
        self,
        repo_id: str,
        local_path: Path = None
    ) -> List[MarketplaceApp]:
        """Sync apps from a repository."""
        await self._ensure_initialized()

        repo = await self.get_repo(repo_id)
        if not repo:
            raise ValueError(f"Repository {repo_id} not found")

        # Update status to syncing
        async with db_manager.get_session() as session:
            await session.execute(
                update(MarketplaceRepoTable)
                .where(MarketplaceRepoTable.id == repo_id)
                .values(status=RepoStatus.SYNCING.value)
            )

        git_sync = GitSync()
        apps: List[MarketplaceApp] = []

        try:
            # Use local path for testing or clone from URL
            if local_path:
                repo_path = Path(local_path)
            else:
                repo_path = git_sync.clone_or_pull(repo.url, repo.branch)

            # Find and parse app files
            app_files = git_sync.find_app_files(repo_path)

            for app_file in app_files:
                app = git_sync.load_app_from_file(app_file, repo_id)
                if app:
                    apps.append(app)
                    await self._upsert_app(app)

            # Update repo with success
            async with db_manager.get_session() as session:
                await session.execute(
                    update(MarketplaceRepoTable)
                    .where(MarketplaceRepoTable.id == repo_id)
                    .values(
                        status=RepoStatus.ACTIVE.value,
                        last_synced=datetime.now(UTC),
                        app_count=len(apps),
                        error_message=None
                    )
                )

            logger.info("Repository synced", repo_id=repo_id, app_count=len(apps))

        except Exception as e:
            # Update repo with error
            async with db_manager.get_session() as session:
                await session.execute(
                    update(MarketplaceRepoTable)
                    .where(MarketplaceRepoTable.id == repo_id)
                    .values(
                        status=RepoStatus.ERROR.value,
                        error_message=str(e)
                    )
                )
            logger.error("Repository sync failed", repo_id=repo_id, error=str(e))
            raise

        finally:
            if not local_path:
                git_sync.cleanup()

        return apps

    async def _upsert_app(self, app: MarketplaceApp) -> None:
        """Insert or update an app in the database."""
        docker_json = app.docker.model_dump_json()
        req_json = app.requirements.model_dump_json()
        tags_json = json.dumps(app.tags)

        async with db_manager.get_session() as session:
            # Check if exists
            result = await session.execute(
                select(MarketplaceAppTable).where(MarketplaceAppTable.id == app.id)
            )
            existing = result.scalar_one_or_none()

            if existing:
                # Update
                await session.execute(
                    update(MarketplaceAppTable)
                    .where(MarketplaceAppTable.id == app.id)
                    .values(
                        name=app.name,
                        description=app.description,
                        long_description=app.long_description,
                        version=app.version,
                        category=app.category,
                        tags=tags_json,
                        icon=app.icon,
                        author=app.author,
                        license=app.license,
                        repository=app.repository,
                        documentation=app.documentation,
                        docker_config=docker_json,
                        requirements=req_json,
                        updated_at=datetime.now(UTC)
                    )
                )
            else:
                # Insert
                table_row = MarketplaceAppTable(
                    id=app.id,
                    name=app.name,
                    description=app.description,
                    long_description=app.long_description,
                    version=app.version,
                    category=app.category,
                    tags=tags_json,
                    icon=app.icon,
                    author=app.author,
                    license=app.license,
                    repository=app.repository,
                    documentation=app.documentation,
                    repo_id=app.repo_id,
                    docker_config=docker_json,
                    requirements=req_json
                )
                session.add(table_row)
```

**Step 4: Run test to verify it passes**

Run: `cd backend && source venv/bin/activate && PYTHONPATH=src pytest tests/unit/test_marketplace_service.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/services/marketplace_service.py backend/tests/unit/test_marketplace_service.py
git commit -m "feat(marketplace): add repo sync with Git integration"
```

---

### Task 2.4: Add App Search and Rating Methods

**Files:**
- Modify: `backend/src/services/marketplace_service.py`
- Test: `backend/tests/unit/test_marketplace_service.py`

**Step 1: Write the failing test**

```python
# Add to backend/tests/unit/test_marketplace_service.py
@pytest.mark.asyncio
async def test_search_apps(marketplace_service):
    # Search should return apps
    results = await marketplace_service.search_apps(category="media")
    assert isinstance(results, list)

@pytest.mark.asyncio
async def test_rate_app(marketplace_service):
    rating = await marketplace_service.rate_app(
        app_id="test-app",
        user_id="user-123",
        rating=4
    )
    assert rating.rating == 4
```

**Step 2: Run test to verify it fails**

Run: `cd backend && source venv/bin/activate && PYTHONPATH=src pytest tests/unit/test_marketplace_service.py::test_search_apps -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Add to `backend/src/services/marketplace_service.py`:

```python
    # ─────────────────────────────────────────────────────────────
    # App Search & Discovery
    # ─────────────────────────────────────────────────────────────

    async def search_apps(
        self,
        search: str = None,
        category: str = None,
        tags: List[str] = None,
        repo_id: str = None,
        featured: bool = None,
        sort_by: str = "name",
        sort_order: str = "asc",
        limit: int = 50,
        offset: int = 0
    ) -> List[MarketplaceApp]:
        """Search marketplace apps with filters."""
        await self._ensure_initialized()

        async with db_manager.get_session() as session:
            query = select(MarketplaceAppTable, MarketplaceRepoTable).join(
                MarketplaceRepoTable,
                MarketplaceAppTable.repo_id == MarketplaceRepoTable.id
            ).where(MarketplaceRepoTable.enabled == True)

            # Apply filters
            if category:
                query = query.where(MarketplaceAppTable.category == category)
            if repo_id:
                query = query.where(MarketplaceAppTable.repo_id == repo_id)
            if featured is not None:
                query = query.where(MarketplaceAppTable.featured == featured)

            result = await session.execute(query)
            rows = result.all()

        # Convert to models
        apps = [self._app_from_table(app_row) for app_row, _ in rows]

        # In-memory filtering for search and tags
        if search:
            search_lower = search.lower()
            apps = [
                a for a in apps
                if search_lower in a.name.lower() or search_lower in a.description.lower()
            ]

        if tags:
            required_tags = set(t.lower() for t in tags)
            apps = [
                a for a in apps
                if required_tags.issubset(set(t.lower() for t in a.tags))
            ]

        # Sort
        reverse = sort_order.lower() == "desc"
        if sort_by == "name":
            apps.sort(key=lambda a: a.name.lower(), reverse=reverse)
        elif sort_by == "rating":
            apps.sort(key=lambda a: a.avg_rating or 0, reverse=reverse)
        elif sort_by == "popularity":
            apps.sort(key=lambda a: a.install_count, reverse=reverse)
        elif sort_by == "updated":
            apps.sort(key=lambda a: a.updated_at, reverse=reverse)

        # Pagination
        return apps[offset:offset + limit]

    async def get_app(self, app_id: str) -> Optional[MarketplaceApp]:
        """Get app by ID."""
        await self._ensure_initialized()

        async with db_manager.get_session() as session:
            result = await session.execute(
                select(MarketplaceAppTable).where(MarketplaceAppTable.id == app_id)
            )
            row = result.scalar_one_or_none()

        return self._app_from_table(row) if row else None

    async def get_featured_apps(self, limit: int = 10) -> List[MarketplaceApp]:
        """Get featured apps."""
        return await self.search_apps(featured=True, limit=limit)

    async def get_trending_apps(self, limit: int = 10) -> List[MarketplaceApp]:
        """Get trending apps by recent popularity."""
        return await self.search_apps(
            sort_by="popularity",
            sort_order="desc",
            limit=limit
        )

    async def get_categories(self) -> List[Dict[str, Any]]:
        """Get all categories with app counts."""
        await self._ensure_initialized()

        async with db_manager.get_session() as session:
            result = await session.execute(select(MarketplaceAppTable.category))
            rows = result.all()

        # Count apps per category
        category_counts: Dict[str, int] = {}
        for row in rows:
            cat = row[0]
            category_counts[cat] = category_counts.get(cat, 0) + 1

        return [
            {"id": cat, "name": cat.title(), "count": count}
            for cat, count in sorted(category_counts.items())
        ]

    # ─────────────────────────────────────────────────────────────
    # Ratings
    # ─────────────────────────────────────────────────────────────

    async def rate_app(self, app_id: str, user_id: str, rating: int) -> AppRating:
        """Rate an app (1-5 stars). Updates existing rating if present."""
        await self._ensure_initialized()

        if not 1 <= rating <= 5:
            raise ValueError("Rating must be between 1 and 5")

        rating_id = f"rating-{uuid.uuid4().hex[:8]}"
        now = datetime.now(UTC)

        async with db_manager.get_session() as session:
            # Check for existing rating
            result = await session.execute(
                select(AppRatingTable).where(
                    AppRatingTable.app_id == app_id,
                    AppRatingTable.user_id == user_id
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                # Update existing
                await session.execute(
                    update(AppRatingTable)
                    .where(AppRatingTable.id == existing.id)
                    .values(rating=rating, updated_at=now)
                )
                rating_id = existing.id
            else:
                # Insert new
                new_rating = AppRatingTable(
                    id=rating_id,
                    app_id=app_id,
                    user_id=user_id,
                    rating=rating
                )
                session.add(new_rating)

            # Update app's average rating
            avg_result = await session.execute(
                select(AppRatingTable.rating).where(AppRatingTable.app_id == app_id)
            )
            all_ratings = [r[0] for r in avg_result.all()]
            avg_rating = sum(all_ratings) / len(all_ratings) if all_ratings else None

            await session.execute(
                update(MarketplaceAppTable)
                .where(MarketplaceAppTable.id == app_id)
                .values(avg_rating=avg_rating, rating_count=len(all_ratings))
            )

        logger.info("App rated", app_id=app_id, user_id=user_id, rating=rating)

        return AppRating(
            id=rating_id,
            app_id=app_id,
            user_id=user_id,
            rating=rating,
            created_at=now.isoformat(),
            updated_at=now.isoformat()
        )

    async def get_user_rating(self, app_id: str, user_id: str) -> Optional[int]:
        """Get user's rating for an app."""
        await self._ensure_initialized()

        async with db_manager.get_session() as session:
            result = await session.execute(
                select(AppRatingTable.rating).where(
                    AppRatingTable.app_id == app_id,
                    AppRatingTable.user_id == user_id
                )
            )
            row = result.scalar_one_or_none()

        return row if row else None

    @staticmethod
    def _app_from_table(row: MarketplaceAppTable) -> MarketplaceApp:
        """Convert table row to model."""
        docker_config = DockerConfig.model_validate_json(row.docker_config)
        requirements = AppRequirements.model_validate_json(row.requirements) if row.requirements else AppRequirements()
        tags = json.loads(row.tags) if row.tags else []

        return MarketplaceApp(
            id=row.id,
            name=row.name,
            description=row.description,
            long_description=row.long_description,
            version=row.version,
            category=row.category,
            tags=tags,
            icon=row.icon,
            author=row.author,
            license=row.license,
            repository=row.repository,
            documentation=row.documentation,
            repo_id=row.repo_id,
            docker=docker_config,
            requirements=requirements,
            install_count=row.install_count or 0,
            avg_rating=row.avg_rating,
            rating_count=row.rating_count or 0,
            featured=row.featured or False,
            created_at=row.created_at.isoformat() if row.created_at else datetime.now(UTC).isoformat(),
            updated_at=row.updated_at.isoformat() if row.updated_at else datetime.now(UTC).isoformat()
        )
```

**Step 4: Run test to verify it passes**

Run: `cd backend && source venv/bin/activate && PYTHONPATH=src pytest tests/unit/test_marketplace_service.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/services/marketplace_service.py backend/tests/unit/test_marketplace_service.py
git commit -m "feat(marketplace): add app search, categories, and rating"
```

---

## Phase 3: MCP Tools

### Task 3.1: Create Marketplace Tools

**Files:**
- Create: `backend/src/tools/marketplace_tools.py`
- Modify: `backend/src/main.py` (add service)

**Step 1: Create the tools file**

```python
# backend/src/tools/marketplace_tools.py
"""MCP tools for marketplace operations."""

from typing import Dict, Any, List, Optional
import structlog
from services.marketplace_service import MarketplaceService
from models.marketplace import RepoType

logger = structlog.get_logger("marketplace_tools")


def register_marketplace_tools(app, config: dict, dependencies: dict):
    """Register all marketplace tools."""

    marketplace_service: MarketplaceService = dependencies.get("marketplace_service")
    if not marketplace_service:
        logger.warning("MarketplaceService not provided, skipping tool registration")
        return

    @app.tool()
    async def list_repos() -> Dict[str, Any]:
        """List all marketplace repositories."""
        try:
            repos = await marketplace_service.get_repos()
            return {
                "success": True,
                "data": [r.model_dump(by_alias=True) for r in repos]
            }
        except Exception as e:
            logger.error("Failed to list repos", error=str(e))
            return {"success": False, "error": str(e)}

    @app.tool()
    async def add_repo(
        name: str,
        url: str,
        repo_type: str = "community",
        branch: str = "main"
    ) -> Dict[str, Any]:
        """Add a new marketplace repository."""
        try:
            repo = await marketplace_service.add_repo(
                name=name,
                url=url,
                repo_type=RepoType(repo_type),
                branch=branch
            )
            return {
                "success": True,
                "data": repo.model_dump(by_alias=True),
                "message": f"Repository '{name}' added successfully"
            }
        except Exception as e:
            logger.error("Failed to add repo", error=str(e))
            return {"success": False, "error": str(e)}

    @app.tool()
    async def remove_repo(repo_id: str) -> Dict[str, Any]:
        """Remove a marketplace repository."""
        try:
            removed = await marketplace_service.remove_repo(repo_id)
            return {
                "success": removed,
                "message": "Repository removed" if removed else "Repository not found"
            }
        except Exception as e:
            logger.error("Failed to remove repo", error=str(e))
            return {"success": False, "error": str(e)}

    @app.tool()
    async def sync_repo(repo_id: str) -> Dict[str, Any]:
        """Sync apps from a repository."""
        try:
            apps = await marketplace_service.sync_repo(repo_id)
            return {
                "success": True,
                "data": {"app_count": len(apps)},
                "message": f"Synced {len(apps)} apps"
            }
        except Exception as e:
            logger.error("Failed to sync repo", error=str(e))
            return {"success": False, "error": str(e)}

    @app.tool()
    async def search_marketplace(
        search: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        featured: Optional[bool] = None,
        sort_by: str = "name",
        limit: int = 50
    ) -> Dict[str, Any]:
        """Search marketplace apps."""
        try:
            apps = await marketplace_service.search_apps(
                search=search,
                category=category,
                tags=tags,
                featured=featured,
                sort_by=sort_by,
                limit=limit
            )
            return {
                "success": True,
                "data": {
                    "apps": [a.model_dump(by_alias=True) for a in apps],
                    "total": len(apps)
                }
            }
        except Exception as e:
            logger.error("Failed to search marketplace", error=str(e))
            return {"success": False, "error": str(e)}

    @app.tool()
    async def get_marketplace_app(app_id: str) -> Dict[str, Any]:
        """Get details of a marketplace app."""
        try:
            app = await marketplace_service.get_app(app_id)
            if not app:
                return {"success": False, "error": "App not found"}
            return {
                "success": True,
                "data": app.model_dump(by_alias=True)
            }
        except Exception as e:
            logger.error("Failed to get app", error=str(e))
            return {"success": False, "error": str(e)}

    @app.tool()
    async def rate_marketplace_app(
        app_id: str,
        user_id: str,
        rating: int
    ) -> Dict[str, Any]:
        """Rate a marketplace app (1-5 stars)."""
        try:
            result = await marketplace_service.rate_app(app_id, user_id, rating)
            return {
                "success": True,
                "data": result.model_dump(by_alias=True),
                "message": f"Rated {rating} stars"
            }
        except ValueError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error("Failed to rate app", error=str(e))
            return {"success": False, "error": str(e)}

    @app.tool()
    async def get_marketplace_categories() -> Dict[str, Any]:
        """Get all marketplace categories with counts."""
        try:
            categories = await marketplace_service.get_categories()
            return {
                "success": True,
                "data": categories
            }
        except Exception as e:
            logger.error("Failed to get categories", error=str(e))
            return {"success": False, "error": str(e)}

    @app.tool()
    async def get_featured_apps(limit: int = 10) -> Dict[str, Any]:
        """Get featured marketplace apps."""
        try:
            apps = await marketplace_service.get_featured_apps(limit)
            return {
                "success": True,
                "data": [a.model_dump(by_alias=True) for a in apps]
            }
        except Exception as e:
            logger.error("Failed to get featured apps", error=str(e))
            return {"success": False, "error": str(e)}

    @app.tool()
    async def get_trending_apps(limit: int = 10) -> Dict[str, Any]:
        """Get trending marketplace apps."""
        try:
            apps = await marketplace_service.get_trending_apps(limit)
            return {
                "success": True,
                "data": [a.model_dump(by_alias=True) for a in apps]
            }
        except Exception as e:
            logger.error("Failed to get trending apps", error=str(e))
            return {"success": False, "error": str(e)}

    logger.info("Marketplace tools registered")
```

**Step 2: Commit**

```bash
git add backend/src/tools/marketplace_tools.py
git commit -m "feat(marketplace): add MCP tools for marketplace operations"
```

---

### Task 3.2: Register Marketplace Service in Main

**Files:**
- Modify: `backend/src/main.py`

**Step 1: Add import and service initialization**

Add after other service imports:
```python
from services.marketplace_service import MarketplaceService
```

Add after other service initializations:
```python
marketplace_service = MarketplaceService()
```

Add to `tool_dependencies` dict:
```python
"marketplace_service": marketplace_service,
```

**Step 2: Commit**

```bash
git add backend/src/main.py
git commit -m "feat(marketplace): register MarketplaceService in main"
```

---

## Phase 4: Frontend Types and Service

### Task 4.1: Add Marketplace Types

**Files:**
- Create: `frontend/src/types/marketplace.ts`

```typescript
// frontend/src/types/marketplace.ts
/**
 * Marketplace Types
 *
 * Type definitions for Git-based app marketplace.
 */

export type RepoType = 'official' | 'community' | 'personal'
export type RepoStatus = 'active' | 'syncing' | 'error' | 'disabled'

export interface MarketplaceRepo {
  id: string
  name: string
  url: string
  branch: string
  repoType: RepoType
  enabled: boolean
  status: RepoStatus
  lastSynced?: string
  appCount: number
  errorMessage?: string
  createdAt: string
  updatedAt: string
}

export interface AppPort {
  container: number
  host: number
  protocol: string
}

export interface AppVolume {
  hostPath: string
  containerPath: string
  readonly: boolean
}

export interface AppEnvVar {
  name: string
  description?: string
  required: boolean
  default?: string
}

export interface DockerConfig {
  image: string
  ports: AppPort[]
  volumes: AppVolume[]
  environment: AppEnvVar[]
  restartPolicy: string
  networkMode?: string
  privileged: boolean
  capabilities: string[]
}

export interface AppRequirements {
  minRam?: number
  minStorage?: number
  architectures: string[]
}

export interface MarketplaceApp {
  id: string
  name: string
  description: string
  longDescription?: string
  version: string
  category: string
  tags: string[]
  icon?: string
  author: string
  license: string
  repository?: string
  documentation?: string
  repoId: string
  docker: DockerConfig
  requirements: AppRequirements
  installCount: number
  avgRating?: number
  ratingCount: number
  featured: boolean
  createdAt: string
  updatedAt: string
}

export interface MarketplaceCategory {
  id: string
  name: string
  count: number
}

export interface MarketplaceFilter {
  search?: string
  category?: string
  tags?: string[]
  repoId?: string
  featured?: boolean
  sortBy?: 'name' | 'rating' | 'popularity' | 'updated'
  sortOrder?: 'asc' | 'desc'
}

export interface MarketplaceSearchResult {
  apps: MarketplaceApp[]
  total: number
}
```

**Commit:**
```bash
git add frontend/src/types/marketplace.ts
git commit -m "feat(marketplace): add frontend TypeScript types"
```

---

### Task 4.2: Create Marketplace Data Service

**Files:**
- Create: `frontend/src/services/marketplaceService.ts`

```typescript
// frontend/src/services/marketplaceService.ts
/**
 * Marketplace Data Service
 *
 * Handles communication with marketplace MCP tools.
 */

import { callTool } from './mcpClient'
import type {
  MarketplaceRepo,
  MarketplaceApp,
  MarketplaceCategory,
  MarketplaceFilter,
  MarketplaceSearchResult,
  RepoType
} from '@/types/marketplace'

export const marketplaceService = {
  // Repository management
  async listRepos(): Promise<MarketplaceRepo[]> {
    const result = await callTool('list_repos', {})
    if (!result.success) throw new Error(result.error)
    return result.data
  },

  async addRepo(
    name: string,
    url: string,
    repoType: RepoType = 'community',
    branch: string = 'main'
  ): Promise<MarketplaceRepo> {
    const result = await callTool('add_repo', {
      name,
      url,
      repo_type: repoType,
      branch
    })
    if (!result.success) throw new Error(result.error)
    return result.data
  },

  async removeRepo(repoId: string): Promise<void> {
    const result = await callTool('remove_repo', { repo_id: repoId })
    if (!result.success) throw new Error(result.error)
  },

  async syncRepo(repoId: string): Promise<{ appCount: number }> {
    const result = await callTool('sync_repo', { repo_id: repoId })
    if (!result.success) throw new Error(result.error)
    return result.data
  },

  // App search and discovery
  async searchApps(filter: MarketplaceFilter): Promise<MarketplaceSearchResult> {
    const result = await callTool('search_marketplace', {
      search: filter.search,
      category: filter.category,
      tags: filter.tags,
      featured: filter.featured,
      sort_by: filter.sortBy || 'name',
      limit: 50
    })
    if (!result.success) throw new Error(result.error)
    return result.data
  },

  async getApp(appId: string): Promise<MarketplaceApp> {
    const result = await callTool('get_marketplace_app', { app_id: appId })
    if (!result.success) throw new Error(result.error)
    return result.data
  },

  async getFeaturedApps(limit: number = 10): Promise<MarketplaceApp[]> {
    const result = await callTool('get_featured_apps', { limit })
    if (!result.success) throw new Error(result.error)
    return result.data
  },

  async getTrendingApps(limit: number = 10): Promise<MarketplaceApp[]> {
    const result = await callTool('get_trending_apps', { limit })
    if (!result.success) throw new Error(result.error)
    return result.data
  },

  async getCategories(): Promise<MarketplaceCategory[]> {
    const result = await callTool('get_marketplace_categories', {})
    if (!result.success) throw new Error(result.error)
    return result.data
  },

  // Ratings
  async rateApp(appId: string, userId: string, rating: number): Promise<void> {
    const result = await callTool('rate_marketplace_app', {
      app_id: appId,
      user_id: userId,
      rating
    })
    if (!result.success) throw new Error(result.error)
  }
}
```

**Commit:**
```bash
git add frontend/src/services/marketplaceService.ts
git commit -m "feat(marketplace): add frontend marketplace service"
```

---

## Phase 5: Frontend UI Components

### Task 5.1: Create Marketplace Page Structure

**Files:**
- Create: `frontend/src/pages/marketplace/MarketplacePage.tsx`
- Create: `frontend/src/pages/marketplace/index.ts`

This task creates the main marketplace page with:
- Header with search
- Featured apps section
- Category grid
- App listing with filters

### Task 5.2: Create RepoManager Component

**Files:**
- Create: `frontend/src/components/marketplace/RepoManager.tsx`

Component for managing repository sources:
- List repos with status indicators
- Add repo form
- Sync/Remove actions

### Task 5.3: Create MarketplaceAppCard Component

**Files:**
- Create: `frontend/src/components/marketplace/MarketplaceAppCard.tsx`

Card component showing:
- App icon, name, description
- Rating stars
- Install count
- Category badge
- Install button

### Task 5.4: Create StarRating Component

**Files:**
- Create: `frontend/src/components/marketplace/StarRating.tsx`

Interactive star rating:
- Display current rating
- Allow user to rate (1-5)
- Show rating count

### Task 5.5: Add Route and Navigation

**Files:**
- Modify: `frontend/src/App.tsx` (add route)
- Modify: `frontend/src/components/layout/Sidebar.tsx` (add nav item)

---

## Phase 6: Integration and Testing

### Task 6.1: Create Sample App Repository

**Files:**
- Create: `backend/data/sample-apps/apps/portainer/app.yaml`
- Create: `backend/data/sample-apps/apps/nginx/app.yaml`

Sample apps for testing.

### Task 6.2: Add Default Official Repo on Init

Seed the official homelab apps repository on first run.

### Task 6.3: Write Integration Tests

Test the full flow:
- Add repo
- Sync apps
- Search apps
- Rate app

### Task 6.4: Final Commit and Documentation

Update README with marketplace usage.

---

## Summary

| Phase | Tasks | Description |
|-------|-------|-------------|
| 1 | 1.1-1.4 | Data models and database schema |
| 2 | 2.1-2.4 | MarketplaceService with Git sync |
| 3 | 3.1-3.2 | MCP tools registration |
| 4 | 4.1-4.2 | Frontend types and service |
| 5 | 5.1-5.5 | UI components and routing |
| 6 | 6.1-6.4 | Integration and testing |

**Estimated Tasks:** 18 bite-sized tasks
**TDD Approach:** Each task includes failing test → implementation → passing test → commit
