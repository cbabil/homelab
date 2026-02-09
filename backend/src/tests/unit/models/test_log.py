"""
Unit tests for models/log.py

Tests log entry models including validation, serialization, and conversions.
"""

import json
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from models.log import (
    LogEntry,
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

    def test_from_row(self):
        """Test creation from a dict-like row (aiosqlite.Row)."""
        row = {
            "id": "log-123",
            "timestamp": "2024-01-15T10:00:00",
            "level": "WARNING",
            "source": "application",
            "message": "Warning message",
            "tags": json.dumps(["tag1", "tag2"]),
            "extra_data": json.dumps({"key": "value"}),
            "created_at": "2024-01-15T10:00:01",
        }

        entry = LogEntry.from_row(row)
        assert entry.id == "log-123"
        assert entry.level == "WARNING"
        assert entry.source == "application"
        assert entry.message == "Warning message"
        assert entry.tags == ["tag1", "tag2"]
        assert entry.metadata == {"key": "value"}

    def test_from_row_empty_json(self):
        """Test from_row handles None JSON fields."""
        row = {
            "id": "log-123",
            "timestamp": "2024-01-15T10:00:00",
            "level": "INFO",
            "source": "system",
            "message": "Message",
            "tags": None,
            "extra_data": None,
            "created_at": None,
        }

        entry = LogEntry.from_row(row)
        assert entry.tags == []
        assert entry.metadata == {}
        assert entry.created_at is None

    def test_to_insert_params(self):
        """Test conversion to insert parameters dict."""
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
        params = entry.to_insert_params()
        assert params["id"] == "log-123"
        assert params["timestamp"] == "2024-01-15T10:00:00"
        assert params["level"] == "ERROR"
        assert params["source"] == "docker"
        assert params["message"] == "Error message"
        assert json.loads(params["tags"]) == ["error", "critical"]
        assert json.loads(params["extra_data"]) == {"error_code": 500}

    def test_to_insert_params_empty_collections(self):
        """Test to_insert_params with empty tags and metadata."""
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
        params = entry.to_insert_params()
        assert params["tags"] is None
        assert params["extra_data"] is None

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
