"""Marketplace repository models."""
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


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
