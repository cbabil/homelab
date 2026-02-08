"""
Unit tests for models/log.py

Tests log entry models including validation, serialization, and conversions.
"""

import json
from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from models.log import (
    LogEntry,
    LogEntryTable,
    LogFilter,
)


class TestLogEntry:
    """Tests for LogEntry model."""

    def test_required_fields(self):
        """Test required fields."""
        now = datetime.now(UTC)
        entry = LogEntry(
            id="log-123",
            timestamp=now,
            level="INFO",
            source="system",
            message="Test log message",
        )
        assert entry.id == "log-123"
        assert entry.timestamp == now
        assert entry.level == "INFO"
        assert entry.source == "system"
        assert entry.message == "Test log message"

    def test_default_values(self):
        """Test default values for optional fields."""
        now = datetime.now(UTC)
        entry = LogEntry(
            id="log-123",
            timestamp=now,
            level="INFO",
            source="system",
            message="Test message",
        )
        assert entry.tags == []
        assert entry.metadata == {}
        assert entry.created_at is None

    def test_all_fields(self):
        """Test all fields populated."""
        now = datetime.now(UTC)
        entry = LogEntry(
            id="log-123",
            timestamp=now,
            level="ERROR",
            source="docker",
            message="Container failed",
            tags=["container", "error", "nginx"],
            metadata={"container_id": "abc123", "exit_code": 1},
            created_at=now,
        )
        assert entry.tags == ["container", "error", "nginx"]
        assert entry.metadata["container_id"] == "abc123"
        assert entry.metadata["exit_code"] == 1
        assert entry.created_at == now

    def test_missing_required_fields(self):
        """Test validation error when required fields are missing."""
        with pytest.raises(ValidationError):
            LogEntry(id="log-123")

    def test_serialize_datetime(self):
        """Test datetime serialization."""
        now = datetime(2024, 1, 15, 10, 30, 45)
        entry = LogEntry(
            id="log-123",
            timestamp=now,
            level="INFO",
            source="system",
            message="Test",
            created_at=now,
        )
        # Test serialization via model_dump
        data = entry.model_dump()
        assert data["timestamp"] == "2024-01-15T10:30:45"
        assert data["created_at"] == "2024-01-15T10:30:45"

    def test_serialize_datetime_none(self):
        """Test datetime serialization with None value."""
        now = datetime(2024, 1, 15, 10, 30, 45)
        entry = LogEntry(
            id="log-123",
            timestamp=now,
            level="INFO",
            source="system",
            message="Test",
            created_at=None,
        )
        data = entry.model_dump()
        assert data["created_at"] is None

    def test_from_table_model(self):
        """Test conversion from SQLAlchemy model."""
        table = MagicMock(spec=LogEntryTable)
        table.id = "log-123"
        table.timestamp = datetime(2024, 1, 15, 10, 0, 0)
        table.level = "WARNING"
        table.source = "application"
        table.message = "Warning message"
        table.tags = json.dumps(["tag1", "tag2"])
        table.extra_data = json.dumps({"key": "value"})
        table.created_at = datetime(2024, 1, 15, 10, 0, 1)

        entry = LogEntry.from_table_model(table)
        assert entry.id == "log-123"
        assert entry.level == "WARNING"
        assert entry.source == "application"
        assert entry.message == "Warning message"
        assert entry.tags == ["tag1", "tag2"]
        assert entry.metadata == {"key": "value"}
        assert entry.created_at == datetime(2024, 1, 15, 10, 0, 1)

    def test_from_table_model_empty_json(self):
        """Test conversion handles empty JSON fields."""
        table = MagicMock(spec=LogEntryTable)
        table.id = "log-123"
        table.timestamp = datetime(2024, 1, 15, 10, 0, 0)
        table.level = "INFO"
        table.source = "system"
        table.message = "Message"
        table.tags = None
        table.extra_data = None
        table.created_at = None

        entry = LogEntry.from_table_model(table)
        assert entry.tags == []
        assert entry.metadata == {}
        assert entry.created_at is None

    def test_to_table_model(self):
        """Test conversion to SQLAlchemy model."""
        now = datetime(2024, 1, 15, 10, 0, 0)
        entry = LogEntry(
            id="log-123",
            timestamp=now,
            level="ERROR",
            source="docker",
            message="Error message",
            tags=["error", "critical"],
            metadata={"error_code": 500},
        )
        table = entry.to_table_model()
        assert table.id == "log-123"
        assert table.timestamp == now
        assert table.level == "ERROR"
        assert table.source == "docker"
        assert table.message == "Error message"
        assert json.loads(table.tags) == ["error", "critical"]
        assert json.loads(table.extra_data) == {"error_code": 500}

    def test_to_table_model_empty_collections(self):
        """Test conversion with empty tags and metadata."""
        now = datetime(2024, 1, 15, 10, 0, 0)
        entry = LogEntry(
            id="log-123",
            timestamp=now,
            level="INFO",
            source="system",
            message="Message",
            tags=[],
            metadata={},
        )
        table = entry.to_table_model()
        assert table.tags is None
        assert table.extra_data is None

    def test_log_levels(self):
        """Test various log levels."""
        now = datetime.now(UTC)
        levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        for level in levels:
            entry = LogEntry(
                id=f"log-{level}",
                timestamp=now,
                level=level,
                source="test",
                message=f"{level} message",
            )
            assert entry.level == level

    def test_log_sources(self):
        """Test various log sources."""
        now = datetime.now(UTC)
        sources = ["docker", "application", "system", "agent"]
        for source in sources:
            entry = LogEntry(
                id=f"log-{source}",
                timestamp=now,
                level="INFO",
                source=source,
                message=f"Message from {source}",
            )
            assert entry.source == source


class TestLogFilter:
    """Tests for LogFilter model."""

    def test_default_values(self):
        """Test default filter values."""
        filter = LogFilter()
        assert filter.level is None
        assert filter.source is None
        assert filter.limit == 100
        assert filter.offset == 0

    def test_custom_values(self):
        """Test custom filter values."""
        filter = LogFilter(
            level="ERROR",
            source="docker",
            limit=50,
            offset=10,
        )
        assert filter.level == "ERROR"
        assert filter.source == "docker"
        assert filter.limit == 50
        assert filter.offset == 10

    def test_limit_min_validation(self):
        """Test limit minimum value validation."""
        with pytest.raises(ValidationError) as exc_info:
            LogFilter(limit=0)
        assert "limit" in str(exc_info.value)

    def test_limit_max_validation(self):
        """Test limit maximum value validation."""
        with pytest.raises(ValidationError) as exc_info:
            LogFilter(limit=1001)
        assert "limit" in str(exc_info.value)

    def test_offset_min_validation(self):
        """Test offset minimum value validation."""
        with pytest.raises(ValidationError) as exc_info:
            LogFilter(offset=-1)
        assert "offset" in str(exc_info.value)

    def test_limit_boundary_values(self):
        """Test limit boundary values."""
        filter_min = LogFilter(limit=1)
        assert filter_min.limit == 1

        filter_max = LogFilter(limit=1000)
        assert filter_max.limit == 1000

    def test_offset_boundary_value(self):
        """Test offset boundary value."""
        filter = LogFilter(offset=0)
        assert filter.offset == 0

    def test_partial_filter(self):
        """Test filter with only some fields set."""
        filter = LogFilter(level="WARNING")
        assert filter.level == "WARNING"
        assert filter.source is None
        assert filter.limit == 100
        assert filter.offset == 0
