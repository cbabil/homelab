"""
Log Models

Pydantic and SQLAlchemy models for log entry storage and validation.
Supports structured logging with tags, metadata, and filtering capabilities.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, field_serializer
from sqlalchemy import Column, String, DateTime, Text, Index
from sqlalchemy.sql import func
from database.connection import Base
import json


class LogEntryTable(Base):
    """SQLAlchemy table model for log entries."""
    
    __tablename__ = "log_entries"
    
    id = Column(String, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    level = Column(String, nullable=False, index=True)
    source = Column(String, nullable=False, index=True)
    message = Column(Text, nullable=False)
    tags = Column(Text)  # JSON array
    extra_data = Column(Text)  # JSON object
    created_at = Column(DateTime, nullable=False, default=func.now(), index=True)
    
    __table_args__ = (
        Index('idx_logs_timestamp', 'timestamp'),
        Index('idx_logs_level_source', 'level', 'source'),
    )


class LogEntry(BaseModel):
    """Pydantic model for log entry validation and serialization."""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Unique log entry identifier")
    timestamp: datetime = Field(..., description="Log entry timestamp")
    level: str = Field(..., description="Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
    source: str = Field(..., description="Log source (docker, application, system)")
    message: str = Field(..., description="Log message content")
    tags: List[str] = Field(default_factory=list, description="Searchable tags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: Optional[datetime] = Field(default=None, description="Database creation timestamp")

    @field_serializer('timestamp', 'created_at')
    def serialize_datetime(self, value: Optional[datetime]) -> Optional[str]:  # pylint: disable=no-self-use
        if value is None:
            return None
        return value.isoformat()

    @classmethod
    def from_table_model(cls, table_model: LogEntryTable) -> "LogEntry":
        """Convert SQLAlchemy model to Pydantic model."""
        return cls(
            id=table_model.id,
            timestamp=table_model.timestamp,
            level=table_model.level,
            source=table_model.source,
            message=table_model.message,
            tags=json.loads(table_model.tags) if table_model.tags else [],
            metadata=json.loads(table_model.extra_data) if table_model.extra_data else {},
            created_at=table_model.created_at
        )
    
    def to_table_model(self) -> LogEntryTable:
        """Convert Pydantic model to SQLAlchemy model."""
        return LogEntryTable(
            id=self.id,
            timestamp=self.timestamp,
            level=self.level,
            source=self.source,
            message=self.message,
            tags=json.dumps(self.tags) if self.tags else None,
            extra_data=json.dumps(self.metadata) if self.metadata else None,
        )


class LogFilter(BaseModel):
    """Pydantic model for log filtering parameters."""

    level: Optional[str] = None
    source: Optional[str] = None
    limit: Optional[int] = Field(default=100, ge=1, le=1000)
    offset: Optional[int] = Field(default=0, ge=0)
