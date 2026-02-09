"""Log Models.

Pydantic models for log entry storage and validation.
Supports structured logging with tags, metadata, and filtering capabilities.
"""

import json
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_serializer


class LogEntry(BaseModel):
    """Pydantic model for log entry validation and serialization."""

    id: str = Field(..., description="Unique log entry identifier")
    timestamp: datetime = Field(..., description="Log entry timestamp")
    level: str = Field(
        ..., description="Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    source: str = Field(..., description="Log source (docker, application, system)")
    message: str = Field(..., description="Log message content")
    tags: list[str] = Field(default_factory=list, description="Searchable tags")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    created_at: datetime | None = Field(
        default=None, description="Database creation timestamp"
    )

    @field_serializer("timestamp", "created_at")
    def serialize_datetime(self, value: datetime | None) -> str | None:  # pylint: disable=no-self-use
        if value is None:
            return None
        return value.isoformat()

    @classmethod
    def from_row(cls, row: Any) -> "LogEntry":
        """Create a LogEntry from an aiosqlite.Row (dict-like access)."""
        return cls(
            id=row["id"],
            timestamp=row["timestamp"],
            level=row["level"],
            source=row["source"],
            message=row["message"],
            tags=json.loads(row["tags"]) if row["tags"] else [],
            metadata=json.loads(row["extra_data"]) if row["extra_data"] else {},
            created_at=row["created_at"],
        )

    def to_insert_params(self) -> dict[str, Any]:
        """Return a dict of column values for INSERT."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "level": self.level,
            "source": self.source,
            "message": self.message,
            "tags": json.dumps(self.tags) if self.tags else None,
            "extra_data": json.dumps(self.metadata) if self.metadata else None,
        }


class LogFilter(BaseModel):
    """Pydantic model for log filtering parameters."""

    level: str | None = None
    source: str | None = None
    limit: int | None = Field(default=100, ge=1, le=1000)
    offset: int | None = Field(default=0, ge=0)
