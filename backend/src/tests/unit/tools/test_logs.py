"""
Logs Tools Unit Tests

Tests for log management tools: get_logs, purge_logs, get_audit_logs.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.log import LogEntry
from models.metrics import ActivityType
from tools.logs.tools import LogsTools


class TestLogsToolsInit:
    """Tests for LogsTools initialization."""

    def test_initialization(self):
        """Test LogsTools is initialized correctly."""
        mock_activity_service = MagicMock()
        mock_log_service = MagicMock()

        with patch("tools.logs.tools.logger"):
            tools = LogsTools(mock_activity_service, log_service=mock_log_service)

        assert tools.activity_service == mock_activity_service
        assert tools.log_service == mock_log_service


class TestGetLogs:
    """Tests for the get_logs tool."""

    @pytest.fixture
    def mock_log_service(self):
        """Create mock log service."""
        return MagicMock()

    @pytest.fixture
    def logs_tools(self, mock_log_service):
        """Create LogsTools instance."""
        with patch("tools.logs.tools.logger"):
            return LogsTools(MagicMock(), log_service=mock_log_service)

    @pytest.fixture
    def sample_logs(self):
        """Create sample log entries."""
        return [
            LogEntry(
                id="log-001",
                timestamp=datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC),
                level="INFO",
                source="system",
                message="System started",
                tags=["startup"],
                metadata={"session_id": "sess-123"},
                created_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC),
            ),
            LogEntry(
                id="log-002",
                timestamp=datetime(2024, 1, 15, 10, 5, 0, tzinfo=UTC),
                level="ERROR",
                source="docker",
                message="Container failed",
                tags=["docker", "error"],
                metadata={},
                created_at=datetime(2024, 1, 15, 10, 5, 0, tzinfo=UTC),
            ),
        ]

    @pytest.mark.asyncio
    async def test_get_logs_success(self, logs_tools, sample_logs):
        """Test successfully getting logs."""
        logs_tools.log_service.get_logs = AsyncMock(return_value=sample_logs)

        result = await logs_tools.get_logs()

        assert result["success"] is True
        assert len(result["data"]["logs"]) == 2
        assert result["data"]["total"] == 2
        assert result["data"]["filtered"] is False
        assert "Retrieved 2 log entries" in result["message"]

    @pytest.mark.asyncio
    async def test_get_logs_with_level_filter(self, logs_tools, sample_logs):
        """Test getting logs with level filter."""
        logs_tools.log_service.get_logs = AsyncMock(return_value=[sample_logs[1]])

        result = await logs_tools.get_logs(level="ERROR")

        assert result["success"] is True
        assert result["data"]["filtered"] is True

    @pytest.mark.asyncio
    async def test_get_logs_with_source_filter(self, logs_tools, sample_logs):
        """Test getting logs with source filter."""
        logs_tools.log_service.get_logs = AsyncMock(return_value=[sample_logs[0]])

        result = await logs_tools.get_logs(source="system")

        assert result["success"] is True
        assert result["data"]["filtered"] is True

    @pytest.mark.asyncio
    async def test_get_logs_with_limit(self, logs_tools, sample_logs):
        """Test getting logs with limit."""
        logs_tools.log_service.get_logs = AsyncMock(return_value=[sample_logs[0]])

        result = await logs_tools.get_logs(limit=1)

        assert result["success"] is True
        assert result["data"]["filtered"] is True

    @pytest.mark.asyncio
    async def test_get_logs_with_pagination(self, logs_tools, sample_logs):
        """Test getting logs with pagination."""
        logs_tools.log_service.get_logs = AsyncMock(return_value=[sample_logs[1]])

        result = await logs_tools.get_logs(limit=1, page=2)

        assert result["success"] is True
        assert result["data"]["filtered"] is True

    @pytest.mark.asyncio
    async def test_get_logs_empty_result(self, logs_tools):
        """Test getting logs when no logs exist."""
        logs_tools.log_service.get_logs = AsyncMock(return_value=[])

        result = await logs_tools.get_logs()

        assert result["success"] is True
        assert result["data"]["logs"] == []
        assert result["data"]["total"] == 0

    @pytest.mark.asyncio
    async def test_get_logs_log_format(self, logs_tools, sample_logs):
        """Test log entry format in response."""
        logs_tools.log_service.get_logs = AsyncMock(return_value=[sample_logs[0]])

        result = await logs_tools.get_logs()

        log = result["data"]["logs"][0]
        assert log["id"] == "log-001"
        assert log["level"] == "INFO"
        assert log["source"] == "system"
        assert log["message"] == "System started"
        assert log["tags"] == ["startup"]
        assert log["session_id"] == "sess-123"
        assert "timestamp" in log
        assert "created_at" in log

    @pytest.mark.asyncio
    async def test_get_logs_without_metadata(self, logs_tools):
        """Test log entry with empty metadata."""
        log_without_metadata = LogEntry(
            id="log-003",
            timestamp=datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC),
            level="DEBUG",
            source="app",
            message="Debug message",
            tags=[],
            metadata={},
            created_at=None,
        )

        logs_tools.log_service.get_logs = AsyncMock(
            return_value=[log_without_metadata]
        )

        result = await logs_tools.get_logs()

        log = result["data"]["logs"][0]
        assert log["session_id"] is None
        assert log["created_at"] is None

    @pytest.mark.asyncio
    async def test_get_logs_exception(self, logs_tools):
        """Test get_logs handles exceptions."""
        logs_tools.log_service.get_logs = AsyncMock(
            side_effect=Exception("Database error")
        )

        result = await logs_tools.get_logs()

        assert result["success"] is False
        assert result["error"] == "LOGS_ERROR"
        assert "Database error" in result["message"]


class TestPurgeLogs:
    """Tests for the purge_logs tool."""

    @pytest.fixture
    def mock_log_service(self):
        """Create mock log service."""
        return MagicMock()

    @pytest.fixture
    def logs_tools(self, mock_log_service):
        """Create LogsTools instance."""
        with patch("tools.logs.tools.logger"):
            return LogsTools(MagicMock(), log_service=mock_log_service)

    @pytest.mark.asyncio
    async def test_purge_logs_success(self, logs_tools):
        """Test successful log purge."""
        logs_tools.log_service.purge_logs = AsyncMock(return_value=100)
        logs_tools.log_service.create_log_entry = AsyncMock()

        result = await logs_tools.purge_logs()

        assert result["success"] is True
        assert result["deleted"] == 100
        assert "Purged 100 log entries" in result["message"]
        logs_tools.log_service.create_log_entry.assert_called_once()

    @pytest.mark.asyncio
    async def test_purge_logs_zero_deleted(self, logs_tools):
        """Test purge when no logs to delete."""
        logs_tools.log_service.purge_logs = AsyncMock(return_value=0)
        logs_tools.log_service.create_log_entry = AsyncMock()

        result = await logs_tools.purge_logs()

        assert result["success"] is True
        assert result["deleted"] == 0

    @pytest.mark.asyncio
    async def test_purge_logs_log_entry_fails(self, logs_tools):
        """Test purge succeeds even if logging the action fails."""
        logs_tools.log_service.purge_logs = AsyncMock(return_value=50)
        logs_tools.log_service.create_log_entry = AsyncMock(
            side_effect=Exception("Log write error")
        )

        result = await logs_tools.purge_logs()

        # Should still succeed - logging failure is not critical
        assert result["success"] is True
        assert result["deleted"] == 50

    @pytest.mark.asyncio
    async def test_purge_logs_exception(self, logs_tools):
        """Test purge_logs handles exceptions."""
        logs_tools.log_service.purge_logs = AsyncMock(
            side_effect=Exception("Purge failed")
        )

        result = await logs_tools.purge_logs()

        assert result["success"] is False
        assert result["error"] == "PURGE_LOGS_ERROR"
        assert "Purge failed" in result["message"]


class TestGetAuditLogs:
    """Tests for the get_audit_logs tool."""

    @pytest.fixture
    def mock_activity_service(self):
        """Create mock activity service."""
        service = MagicMock()
        service.get_activities = AsyncMock(return_value=[])
        service.get_activity_count = AsyncMock(return_value=0)
        return service

    @pytest.fixture
    def logs_tools(self, mock_activity_service):
        """Create LogsTools instance."""
        with patch("tools.logs.tools.logger"):
            return LogsTools(mock_activity_service, log_service=MagicMock())

    @pytest.fixture
    def sample_activity(self):
        """Create sample activity for testing."""
        activity = MagicMock()
        activity.model_dump = MagicMock(
            return_value={
                "id": "act-001",
                "type": "user_login",
                "user_id": "user-123",
                "server_id": None,
                "details": {"ip": "192.168.1.1"},
                "timestamp": "2024-01-15T10:00:00Z",
            }
        )
        return activity

    @pytest.mark.asyncio
    async def test_get_audit_logs_success(
        self, logs_tools, mock_activity_service, sample_activity
    ):
        """Test successfully getting audit logs."""
        mock_activity_service.get_activities = AsyncMock(return_value=[sample_activity])
        mock_activity_service.get_activity_count = AsyncMock(return_value=1)

        result = await logs_tools.get_audit_logs()

        assert result["success"] is True
        assert result["data"]["count"] == 1
        assert result["data"]["total"] == 1
        assert result["data"]["limit"] == 50
        assert result["data"]["offset"] == 0

    @pytest.mark.asyncio
    async def test_get_audit_logs_with_activity_types(
        self, logs_tools, mock_activity_service
    ):
        """Test getting audit logs filtered by activity types."""
        mock_activity_service.get_activities = AsyncMock(return_value=[])
        mock_activity_service.get_activity_count = AsyncMock(return_value=0)

        result = await logs_tools.get_audit_logs(
            activity_types=["user_login", "user_logout"]
        )

        assert result["success"] is True
        call_args = mock_activity_service.get_activities.call_args
        assert call_args.kwargs["activity_types"] == [
            ActivityType.USER_LOGIN,
            ActivityType.USER_LOGOUT,
        ]

    @pytest.mark.asyncio
    async def test_get_audit_logs_with_server_filter(
        self, logs_tools, mock_activity_service
    ):
        """Test getting audit logs filtered by server ID."""
        mock_activity_service.get_activities = AsyncMock(return_value=[])
        mock_activity_service.get_activity_count = AsyncMock(return_value=0)

        result = await logs_tools.get_audit_logs(server_id="server-123")

        assert result["success"] is True
        call_args = mock_activity_service.get_activities.call_args
        assert call_args.kwargs["server_id"] == "server-123"

    @pytest.mark.asyncio
    async def test_get_audit_logs_with_user_filter(
        self, logs_tools, mock_activity_service
    ):
        """Test getting audit logs filtered by user ID."""
        mock_activity_service.get_activities = AsyncMock(return_value=[])
        mock_activity_service.get_activity_count = AsyncMock(return_value=0)

        result = await logs_tools.get_audit_logs(user_id="user-456")

        assert result["success"] is True
        call_args = mock_activity_service.get_activities.call_args
        assert call_args.kwargs["user_id"] == "user-456"

    @pytest.mark.asyncio
    async def test_get_audit_logs_with_pagination(
        self, logs_tools, mock_activity_service
    ):
        """Test getting audit logs with custom pagination."""
        mock_activity_service.get_activities = AsyncMock(return_value=[])
        mock_activity_service.get_activity_count = AsyncMock(return_value=100)

        result = await logs_tools.get_audit_logs(limit=10, offset=20)

        assert result["success"] is True
        assert result["data"]["limit"] == 10
        assert result["data"]["offset"] == 20
        call_args = mock_activity_service.get_activities.call_args
        assert call_args.kwargs["limit"] == 10
        assert call_args.kwargs["offset"] == 20

    @pytest.mark.asyncio
    async def test_get_audit_logs_empty_result(self, logs_tools, mock_activity_service):
        """Test getting audit logs when no activities exist."""
        mock_activity_service.get_activities = AsyncMock(return_value=[])
        mock_activity_service.get_activity_count = AsyncMock(return_value=0)

        result = await logs_tools.get_audit_logs()

        assert result["success"] is True
        assert result["data"]["logs"] == []
        assert result["data"]["count"] == 0
        assert result["data"]["total"] == 0

    @pytest.mark.asyncio
    async def test_get_audit_logs_exception(self, logs_tools, mock_activity_service):
        """Test get_audit_logs handles exceptions."""
        mock_activity_service.get_activities = AsyncMock(
            side_effect=Exception("Database connection lost")
        )

        result = await logs_tools.get_audit_logs()

        assert result["success"] is False
        assert result["error"] == "GET_AUDIT_LOGS_ERROR"
        assert "Database connection lost" in result["message"]

    @pytest.mark.asyncio
    async def test_get_audit_logs_no_activity_types(
        self, logs_tools, mock_activity_service
    ):
        """Test that None activity_types doesn't filter by type."""
        mock_activity_service.get_activities = AsyncMock(return_value=[])
        mock_activity_service.get_activity_count = AsyncMock(return_value=0)

        result = await logs_tools.get_audit_logs(activity_types=None)

        assert result["success"] is True
        call_args = mock_activity_service.get_activities.call_args
        assert call_args.kwargs["activity_types"] is None
