"""Application data models for the Tomo marketplace."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


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

    min_ram: str | None = Field(None, description="Minimum RAM requirement")
    min_storage: str | None = Field(None, description="Minimum storage requirement")
    required_ports: list[int] | None = Field(None, description="Required network ports")
    dependencies: list[str] | None = Field(None, description="Runtime dependencies")
    supported_architectures: list[str] | None = Field(
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
    def from_row(row: Any) -> AppCategory:
        """Create from an aiosqlite.Row with cat_ prefixed columns or plain."""
        # Support both aliased (JOIN) and plain column access
        try:
            return AppCategory(
                id=row["cat_id"],
                name=row["cat_name"],
                description=row["cat_desc"],
                icon=row["cat_icon"],
                color=row["cat_color"],
            )
        except (IndexError, KeyError):
            return AppCategory(
                id=row["id"],
                name=row["name"],
                description=row["description"],
                icon=row["icon"],
                color=row["color"],
            )

    def to_insert_params(self) -> dict[str, Any]:
        """Return a dict of column values for INSERT."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "icon": self.icon,
            "color": self.color,
        }


class App(BaseModel):
    """Application marketplace entry."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    id: str = Field(..., description="Unique application identifier")
    name: str = Field(..., min_length=1, max_length=100, description="Application name")
    description: str = Field(
        ..., min_length=1, max_length=500, description="Short description"
    )
    long_description: str | None = Field(None, description="Detailed description")
    version: str = Field(..., description="Current version")
    category: AppCategory = Field(..., description="Application category")
    tags: list[str] = Field(default_factory=list, description="Search tags")
    icon: str | None = Field(None, description="Application icon URL")
    screenshots: list[str] | None = Field(None, description="Screenshot URLs")
    author: str = Field(..., description="Application author")
    repository: str | None = Field(None, description="Source repository URL")
    documentation: str | None = Field(None, description="Documentation URL")
    license: str = Field(..., description="Software license")
    requirements: AppRequirements = Field(
        default_factory=AppRequirements, description="System requirements"
    )
    status: AppStatus = Field(
        default=AppStatus.AVAILABLE, description="Installation status"
    )
    install_count: int | None = Field(None, description="Installation count")
    rating: float | None = Field(None, ge=0, le=5, description="User rating")
    featured: bool | None = Field(False, description="Featured application flag")
    created_at: str = Field(..., description="Creation timestamp (ISO format)")
    updated_at: str = Field(..., description="Last update timestamp (ISO format)")
    connected_server_id: str | None = Field(
        None, description="Identifier of the server where the app is installed"
    )

    @staticmethod
    def from_row(row: Any) -> App:
        """Create an App model from a JOIN result row with aliased category columns."""
        tags = json.loads(row["tags"]) if row["tags"] else []
        screenshots = json.loads(row["screenshots"]) if row["screenshots"] else []
        requirements_data = (
            json.loads(row["requirements"]) if row["requirements"] else {}
        )

        category = AppCategory(
            id=row["cat_id"],
            name=row["cat_name"],
            description=row["cat_desc"],
            icon=row["cat_icon"],
            color=row["cat_color"],
        )

        return App(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            long_description=row["long_description"],
            version=row["version"],
            category=category,
            tags=tags,
            icon=row["icon"],
            screenshots=screenshots or None,
            author=row["author"],
            repository=row["repository"],
            documentation=row["documentation"],
            license=row["license"],
            requirements=AppRequirements(**requirements_data)
            if requirements_data
            else AppRequirements(),
            status=AppStatus(row["status"]),
            install_count=row["install_count"],
            rating=row["rating"],
            featured=bool(row["featured"]),
            created_at=App._serialize_datetime_str(row["created_at"]),
            updated_at=App._serialize_datetime_str(row["updated_at"]),
            connected_server_id=row["connected_server_id"],
        )

    def to_insert_params(self) -> dict[str, Any]:
        """Return a dict of column values for INSERT."""
        requirements_payload = (
            self.requirements.model_dump(exclude_none=True, by_alias=False)
            if self.requirements
            else {}
        )

        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "long_description": self.long_description,
            "version": self.version,
            "category_id": self.category.id,
            "tags": json.dumps(self.tags) if self.tags else None,
            "icon": self.icon,
            "screenshots": json.dumps(self.screenshots) if self.screenshots else None,
            "author": self.author,
            "repository": self.repository,
            "documentation": self.documentation,
            "license": self.license,
            "requirements": json.dumps(requirements_payload)
            if requirements_payload
            else None,
            "status": self.status.value
            if isinstance(self.status, AppStatus)
            else str(self.status),
            "install_count": self.install_count,
            "rating": self.rating,
            "featured": 1 if self.featured else 0,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "connected_server_id": self.connected_server_id,
        }

    @staticmethod
    def _serialize_datetime_str(value: str | datetime | None) -> str:
        """Serialize a datetime or string to ISO 8601."""
        if value is None:
            return datetime.now(UTC).isoformat()
        if isinstance(value, datetime):
            return value.replace(microsecond=0).isoformat()
        return str(value)

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
    last_updated: str | None = Field(None, description="Last update timestamp")
    config: dict[str, Any] | None = Field(
        None, description="Installation configuration"
    )
    logs: list[str] | None = Field(None, description="Installation logs")


class AppFilter(BaseModel):
    """Application search and filter criteria."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    category: str | None = Field(None, description="Category filter")
    tags: list[str] | None = Field(None, description="Tag filters")
    status: AppStatus | None = Field(None, description="Status filter")
    search: str | None = Field(None, description="Text search query")
    featured: bool | None = Field(None, description="Featured apps only")
    sort_by: str | None = Field("name", description="Sort field")
    sort_order: str | None = Field("asc", description="Sort direction")


class AppSearchResult(BaseModel):
    """Paginated application search results."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    apps: list[App] = Field(..., description="Found applications")
    total: int = Field(..., description="Total result count")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Results per page")
    filters: AppFilter = Field(..., description="Applied filters")
