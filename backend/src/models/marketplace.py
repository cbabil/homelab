"""Marketplace repository models."""
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.sql import func

from database.connection import Base


# SQLAlchemy Table Definitions

class MarketplaceRepoTable(Base):
    """SQLAlchemy table for marketplace repositories."""

    __tablename__ = "marketplace_repos"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    branch = Column(String, nullable=False, default="main")
    repo_type = Column(String, nullable=False, default="community")
    enabled = Column(Boolean, nullable=False, default=True)
    status = Column(String, nullable=False, default="active")
    last_synced = Column(DateTime, nullable=True)
    app_count = Column(Integer, nullable=False, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())


class MarketplaceAppTable(Base):
    """SQLAlchemy table for marketplace applications."""

    __tablename__ = "marketplace_apps"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    long_description = Column(Text, nullable=True)
    version = Column(String, nullable=False)
    category = Column(String, nullable=False, index=True)
    tags = Column(Text, nullable=True)  # JSON array stored as text
    icon = Column(String, nullable=True)
    author = Column(String, nullable=False)
    license = Column(String, nullable=False)
    maintainers = Column(Text, nullable=True)  # JSON array stored as text
    repository = Column(String, nullable=True)
    documentation = Column(String, nullable=True)
    repo_id = Column(String, ForeignKey("marketplace_repos.id"), nullable=False, index=True)
    docker_config = Column(Text, nullable=False)  # JSON stored as text
    requirements = Column(Text, nullable=True)  # JSON stored as text
    install_count = Column(Integer, nullable=False, default=0)
    avg_rating = Column(Float, nullable=True)
    rating_count = Column(Integer, nullable=False, default=0)
    featured = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())


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
        Index("idx_app_ratings_unique", "app_id", "user_id", unique=True),
    )


# Pydantic Models

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
    """Marketplace repository configuration and status."""

    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True
    )

    id: str = Field(..., description="Unique repository identifier")
    name: str = Field(..., description="Human-readable repository name")
    url: str = Field(..., description="Git repository URL")
    branch: str = Field(..., description="Branch to sync from")
    repo_type: RepoType = Field(..., alias="repoType", description="Repository type")
    enabled: bool = Field(..., description="Whether repository is enabled for syncing")
    status: RepoStatus = Field(..., description="Current repository status")
    last_synced: Optional[datetime] = Field(None, alias="lastSynced", description="Last successful sync timestamp")
    app_count: int = Field(..., alias="appCount", description="Number of apps in repository")
    error_message: Optional[str] = Field(None, alias="errorMessage", description="Error message if status is ERROR")
    created_at: datetime = Field(..., alias="createdAt", description="Repository creation timestamp")
    updated_at: datetime = Field(..., alias="updatedAt", description="Last update timestamp")


class AppPort(BaseModel):
    """Docker container port mapping."""

    model_config = ConfigDict(populate_by_name=True)

    container: int = Field(..., description="Container port number")
    host: int = Field(..., description="Host port number")
    protocol: str = Field("tcp", description="Protocol (tcp/udp)")


class AppVolume(BaseModel):
    """Docker container volume mapping."""

    model_config = ConfigDict(populate_by_name=True)

    host_path: str = Field(..., alias="hostPath", description="Host path")
    container_path: str = Field(..., alias="containerPath", description="Container path")
    readonly: bool = Field(False, description="Whether volume is read-only")


class AppEnvVar(BaseModel):
    """Application environment variable configuration."""

    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(..., description="Environment variable name")
    description: Optional[str] = Field(None, description="Variable description")
    required: bool = Field(..., description="Whether variable is required")
    default: Optional[str] = Field(None, description="Default value")


class DockerConfig(BaseModel):
    """Docker container configuration."""

    model_config = ConfigDict(populate_by_name=True)

    image: str = Field(..., description="Docker image name and tag")
    ports: List[AppPort] = Field(..., description="Port mappings")
    volumes: List[AppVolume] = Field(..., description="Volume mappings")
    environment: List[AppEnvVar] = Field(..., description="Environment variables")
    restart_policy: str = Field(..., alias="restartPolicy", description="Container restart policy")
    network_mode: Optional[str] = Field(None, alias="networkMode", description="Docker network mode")
    privileged: bool = Field(..., description="Whether container runs in privileged mode")
    capabilities: List[str] = Field(..., description="Additional Linux capabilities")


class AppRequirements(BaseModel):
    """Application system requirements."""

    model_config = ConfigDict(populate_by_name=True)

    min_ram: Optional[int] = Field(None, alias="minRam", description="Minimum RAM in MB")
    min_storage: Optional[int] = Field(None, alias="minStorage", description="Minimum storage in MB")
    architectures: List[str] = Field(..., description="Supported CPU architectures")


class MarketplaceApp(BaseModel):
    """Marketplace application with full metadata and configuration."""

    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True
    )

    id: str = Field(..., description="Unique application identifier")
    name: str = Field(..., description="Application name")
    description: str = Field(..., description="Short description")
    long_description: Optional[str] = Field(None, alias="longDescription", description="Detailed description")
    version: str = Field(..., description="Application version")
    category: str = Field(..., description="Application category")
    tags: List[str] = Field(..., description="Search tags")
    icon: Optional[str] = Field(None, description="Icon URL")
    author: str = Field(..., description="Application author")
    license: str = Field(..., description="Software license")
    maintainers: List[str] = Field(default_factory=list, description="Package maintainers")
    repository: Optional[str] = Field(None, description="Source code repository URL")
    documentation: Optional[str] = Field(None, description="Documentation URL")
    repo_id: str = Field(..., alias="repoId", description="Source marketplace repository ID")
    docker: DockerConfig = Field(..., description="Docker configuration")
    requirements: AppRequirements = Field(..., description="System requirements")
    install_count: int = Field(0, alias="installCount", description="Number of installations")
    avg_rating: float = Field(0.0, alias="avgRating", description="Average user rating")
    rating_count: int = Field(0, alias="ratingCount", description="Number of ratings")
    featured: bool = Field(False, description="Whether app is featured")
    created_at: datetime = Field(..., alias="createdAt", description="App creation timestamp")
    updated_at: datetime = Field(..., alias="updatedAt", description="Last update timestamp")


class AppRating(BaseModel):
    """User rating for a marketplace application."""

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., description="Unique rating identifier")
    app_id: str = Field(..., alias="appId", description="Application being rated")
    user_id: str = Field(..., alias="userId", description="User who submitted the rating")
    rating: int = Field(..., ge=1, le=5, description="Rating value (1-5)")
    created_at: str = Field(..., alias="createdAt", description="Rating creation timestamp")
    updated_at: str = Field(..., alias="updatedAt", description="Last update timestamp")
