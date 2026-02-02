"""Application data models and database mappings for the Tomo marketplace."""

from __future__ import annotations

import json
from datetime import datetime, UTC
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict
from pydantic.alias_generators import to_camel
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


class AppCategoryTable(Base):
    """SQLAlchemy table for application categories."""

    __tablename__ = "app_categories"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    icon = Column(String, nullable=False)
    color = Column(String, nullable=False)


class ApplicationTable(Base):
    """SQLAlchemy table for applications."""

    __tablename__ = "applications"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    long_description = Column(Text)
    version = Column(String, nullable=False)
    category_id = Column(String, ForeignKey("app_categories.id"), nullable=False, index=True)
    tags = Column(Text)
    icon = Column(String)
    screenshots = Column(Text)
    author = Column(String, nullable=False)
    repository = Column(String)
    documentation = Column(String)
    license = Column(String, nullable=False)
    requirements = Column(Text)
    status = Column(String, nullable=False, index=True)
    install_count = Column(Integer)
    rating = Column(Float)
    featured = Column(Boolean, default=False)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    connected_server_id = Column(String, nullable=True, index=True)

    __table_args__ = (
        Index("idx_applications_category_status", "category_id", "status"),
    )


class AppStatus(str, Enum):
    """Application status states."""

    AVAILABLE = "available"
    INSTALLED = "installed"
    INSTALLING = "installing"
    UPDATING = "updating"
    REMOVING = "removing"
    ERROR = "error"
    DEPRECATED = "deprecated"


class AppRequirements(BaseModel):
    """Application system requirements."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    min_ram: Optional[str] = Field(None, description="Minimum RAM requirement")
    min_storage: Optional[str] = Field(None, description="Minimum storage requirement")
    required_ports: Optional[List[int]] = Field(None, description="Required network ports")
    dependencies: Optional[List[str]] = Field(None, description="Runtime dependencies")
    supported_architectures: Optional[List[str]] = Field(
        None, description="Supported CPU architectures"
    )


class AppCategory(BaseModel):
    """Application category definition."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    id: str = Field(..., description="Category identifier")
    name: str = Field(..., description="Category display name")
    description: str = Field(..., description="Category description")
    icon: str = Field(..., description="Icon identifier (Lucide icon name)")
    color: str = Field(..., description="Category color theme classes")

    @staticmethod
    def from_table(table: AppCategoryTable) -> "AppCategory":
        """Create a Pydantic model from a database row."""

        return AppCategory(
            id=table.id,
            name=table.name,
            description=table.description,
            icon=table.icon,
            color=table.color,
        )

    def to_table_model(self) -> AppCategoryTable:
        """Convert model to SQLAlchemy table instance."""

        return AppCategoryTable(
            id=self.id,
            name=self.name,
            description=self.description,
            icon=self.icon,
            color=self.color,
        )


class App(BaseModel):
    """Application marketplace entry."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    id: str = Field(..., description="Unique application identifier")
    name: str = Field(..., min_length=1, max_length=100, description="Application name")
    description: str = Field(..., min_length=1, max_length=500, description="Short description")
    long_description: Optional[str] = Field(None, description="Detailed description")
    version: str = Field(..., description="Current version")
    category: AppCategory = Field(..., description="Application category")
    tags: List[str] = Field(default_factory=list, description="Search tags")
    icon: Optional[str] = Field(None, description="Application icon URL")
    screenshots: Optional[List[str]] = Field(None, description="Screenshot URLs")
    author: str = Field(..., description="Application author")
    repository: Optional[str] = Field(None, description="Source repository URL")
    documentation: Optional[str] = Field(None, description="Documentation URL")
    license: str = Field(..., description="Software license")
    requirements: AppRequirements = Field(default_factory=AppRequirements, description="System requirements")
    status: AppStatus = Field(default=AppStatus.AVAILABLE, description="Installation status")
    install_count: Optional[int] = Field(None, description="Installation count")
    rating: Optional[float] = Field(None, ge=0, le=5, description="User rating")
    featured: Optional[bool] = Field(False, description="Featured application flag")
    created_at: str = Field(..., description="Creation timestamp (ISO format)")
    updated_at: str = Field(..., description="Last update timestamp (ISO format)")
    connected_server_id: Optional[str] = Field(
        None, description="Identifier of the server where the app is installed"
    )

    @staticmethod
    def from_table(app_row: ApplicationTable, category_row: AppCategoryTable) -> "App":
        """Create an App model from database rows."""

        tags = json.loads(app_row.tags) if app_row.tags else []
        screenshots = json.loads(app_row.screenshots) if app_row.screenshots else []
        requirements_data = json.loads(app_row.requirements) if app_row.requirements else {}

        return App(
            id=app_row.id,
            name=app_row.name,
            description=app_row.description,
            long_description=app_row.long_description,
            version=app_row.version,
            category=AppCategory.from_table(category_row),
            tags=tags,
            icon=app_row.icon,
            screenshots=screenshots or None,
            author=app_row.author,
            repository=app_row.repository,
            documentation=app_row.documentation,
            license=app_row.license,
            requirements=AppRequirements(**requirements_data) if requirements_data else AppRequirements(),
            status=AppStatus(app_row.status),
            install_count=app_row.install_count,
            rating=app_row.rating,
            featured=app_row.featured,
            created_at=App._serialize_datetime(app_row.created_at),
            updated_at=App._serialize_datetime(app_row.updated_at),
            connected_server_id=app_row.connected_server_id,
        )

    def to_table_model(self) -> ApplicationTable:
        """Convert the App model into an ApplicationTable instance."""

        requirements_payload = (
            self.requirements.model_dump(exclude_none=True, by_alias=False)
            if self.requirements
            else {}
        )

        return ApplicationTable(
            id=self.id,
            name=self.name,
            description=self.description,
            long_description=self.long_description,
            version=self.version,
            category_id=self.category.id,
            tags=json.dumps(self.tags) if self.tags else None,
            icon=self.icon,
            screenshots=json.dumps(self.screenshots) if self.screenshots else None,
            author=self.author,
            repository=self.repository,
            documentation=self.documentation,
            license=self.license,
            requirements=json.dumps(requirements_payload) if requirements_payload else None,
            status=self.status.value if isinstance(self.status, AppStatus) else str(self.status),
            install_count=self.install_count,
            rating=self.rating,
            featured=self.featured,
            created_at=self._parse_datetime(self.created_at),
            updated_at=self._parse_datetime(self.updated_at),
            connected_server_id=self.connected_server_id,
        )

    @staticmethod
    def _serialize_datetime(value: Optional[datetime]) -> str:
        """Serialize datetime to ISO 8601 string."""

        if value is None:
            return datetime.now(UTC).isoformat()
        return value.replace(microsecond=0).isoformat()

    @staticmethod
    def _parse_datetime(value: str) -> datetime:
        """Parse ISO 8601 string into datetime object."""

        if value.lower().endswith("z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)


class AppInstallation(BaseModel):
    """Application installation record."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    app_id: str = Field(..., description="Application identifier")
    status: AppStatus = Field(..., description="Installation status")
    version: str = Field(..., description="Installed version")
    installed_at: str = Field(..., description="Installation timestamp")
    last_updated: Optional[str] = Field(None, description="Last update timestamp")
    config: Optional[Dict[str, Any]] = Field(None, description="Installation configuration")
    logs: Optional[List[str]] = Field(None, description="Installation logs")


class AppFilter(BaseModel):
    """Application search and filter criteria."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    category: Optional[str] = Field(None, description="Category filter")
    tags: Optional[List[str]] = Field(None, description="Tag filters")
    status: Optional[AppStatus] = Field(None, description="Status filter")
    search: Optional[str] = Field(None, description="Text search query")
    featured: Optional[bool] = Field(None, description="Featured apps only")
    sort_by: Optional[str] = Field("name", description="Sort field")
    sort_order: Optional[str] = Field("asc", description="Sort direction")


class AppSearchResult(BaseModel):
    """Paginated application search results."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    apps: List[App] = Field(..., description="Found applications")
    total: int = Field(..., description="Total result count")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Results per page")
    filters: AppFilter = Field(..., description="Applied filters")
