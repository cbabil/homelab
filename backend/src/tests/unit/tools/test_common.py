"""
Unit tests for tools/common.py.

Tests for log_event utility function.
"""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime

from tools.common import log_event


class TestLogEvent:
    """Tests for log_event function."""

    @pytest.mark.asyncio
    async def test_log_event_success(self):
        """Test successful log event creation."""
        with patch("tools.common.log_service") as mock_log_service:
            mock_log_service.create_log_entry = AsyncMock()

            await log_event(
                source="test",
                level="INFO",
                message="Test message",
                tags=["tag1", "tag2"],
                metadata={"key": "value"}
            )

            mock_log_service.create_log_entry.assert_called_once()
            call_args = mock_log_service.create_log_entry.call_args
            entry = call_args[0][0]

            assert entry.source == "test"
            assert entry.level == "INFO"
            assert entry.message == "Test message"
            assert entry.tags == ["tag1", "tag2"]
            assert entry.metadata == {"key": "value"}
            assert entry.id.startswith("test-")

    @pytest.mark.asyncio
    async def test_log_event_without_metadata(self):
        """Test log event creation without metadata."""
        with patch("tools.common.log_service") as mock_log_service:
            mock_log_service.create_log_entry = AsyncMock()

            await log_event(
                source="srv",
                level="WARNING",
                message="Warning message",
                tags=["server"]
            )

            mock_log_service.create_log_entry.assert_called_once()
            call_args = mock_log_service.create_log_entry.call_args
            entry = call_args[0][0]

            assert entry.metadata == {}

    @pytest.mark.asyncio
    async def test_log_event_handles_exception(self):
        """Test log event handles exceptions gracefully."""
        with (
            patch("tools.common.log_service") as mock_log_service,
            patch("tools.common.logger") as mock_logger,
        ):
            mock_log_service.create_log_entry = AsyncMock(
                side_effect=Exception("Database error")
            )

            # Should not raise, just log the error
            await log_event(
                source="test",
                level="ERROR",
                message="Error message",
                tags=["error"]
            )

            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args
            assert "Failed to create log entry" in call_args[0][0]
            assert call_args[1]["source"] == "test"

    @pytest.mark.asyncio
    async def test_log_event_entry_has_timestamp(self):
        """Test log entry has a timestamp."""
        with patch("tools.common.log_service") as mock_log_service:
            mock_log_service.create_log_entry = AsyncMock()

            await log_event(
                source="app",
                level="INFO",
                message="Test",
                tags=[]
            )

            call_args = mock_log_service.create_log_entry.call_args
            entry = call_args[0][0]

            assert isinstance(entry.timestamp, datetime)
