"""
Unit tests for services/service_log.py

Tests log service CRUD operations using raw aiosqlite.
"""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.service_log import LogService


def _make_mock_connection():
    """Create a mock DatabaseConnection with async context manager."""
    mock_cursor = AsyncMock()
    mock_cursor.fetchone = AsyncMock(return_value=None)
    mock_cursor.fetchall = AsyncMock(return_value=[])

    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock(return_value=mock_cursor)
    mock_conn.commit = AsyncMock()

    mock_db_connection = MagicMock()

    @asynccontextmanager
    async def _get_connection():
        yield mock_conn

    mock_db_connection.get_connection = _get_connection

    return mock_db_connection, mock_conn, mock_cursor


@pytest.fixture
def mock_connection():
    """Create mock DatabaseConnection with get_connection async context manager."""
    db_connection, conn, cursor = _make_mock_connection()
    return db_connection, conn, cursor


@pytest.fixture
def log_service(mock_connection):
    """Create LogService instance with mock connection."""
    db_connection, _, _ = mock_connection
    return LogService(connection=db_connection)


@pytest.fixture
def mock_log_entry():
    """Create mock LogEntry with all required attributes."""
    entry = MagicMock()
    entry.id = "log-12345678"
    entry.level = "INFO"
    entry.message = "Test message"
    entry.source = "test"
    entry.to_insert_params.return_value = {
        "id": "log-12345678",
        "timestamp": "2025-01-01T00:00:00",
        "level": "INFO",
        "source": "test",
        "message": "Test message",
        "tags": None,
        "extra_data": None,
    }
    return entry


@pytest.fixture
def mock_row():
    """Create a mock database row with dict-like access."""
    row = MagicMock()
    row.__getitem__ = MagicMock(
        side_effect=lambda key: {
            "id": "log-12345678",
            "timestamp": "2025-01-01T00:00:00",
            "level": "INFO",
            "source": "test",
            "message": "Test message",
            "tags": None,
            "extra_data": None,
            "created_at": None,
        }[key]
    )
    return row


class TestLogServiceInit:
    """Tests for LogService initialization."""

    def test_init_stores_connection(self):
        """LogService should store the database connection."""
        mock_db = MagicMock()
        service = LogService(connection=mock_db)
        assert service._conn is mock_db


class TestCreateLogEntry:
    """Tests for create_log_entry method."""

    @pytest.mark.asyncio
    async def test_create_log_entry_success(
        self, log_service, mock_connection, mock_log_entry, mock_row
    ):
        """create_log_entry should insert and return re-fetched log entry."""
        _, mock_conn, mock_cursor = mock_connection

        # Second execute (SELECT after INSERT) returns the row
        mock_cursor.fetchone.return_value = mock_row
        returned_entry = MagicMock()

        with patch(
            "services.service_log.LogEntry.from_row", return_value=returned_entry
        ):
            result = await log_service.create_log_entry(mock_log_entry)

        assert result == returned_entry
        assert mock_conn.execute.call_count == 2
        mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_log_entry_generates_id_when_none(
        self, mock_connection
    ):
        """create_log_entry should generate an ID if log_entry.id is falsy."""
        db_connection, mock_conn, mock_cursor = mock_connection

        mock_log_entry = MagicMock()
        mock_log_entry.id = None

        copied_entry = MagicMock()
        copied_entry.id = "log-generated1"
        copied_entry.level = "INFO"
        copied_entry.to_insert_params.return_value = {
            "id": "log-generated1",
            "timestamp": "2025-01-01T00:00:00",
            "level": "INFO",
            "source": "test",
            "message": "Test",
            "tags": None,
            "extra_data": None,
        }
        mock_log_entry.model_copy.return_value = copied_entry

        mock_row = MagicMock()
        mock_cursor.fetchone.return_value = mock_row
        returned_entry = MagicMock()

        service = LogService(connection=db_connection)

        with patch(
            "services.service_log.LogEntry.from_row", return_value=returned_entry
        ):
            result = await service.create_log_entry(mock_log_entry)

        mock_log_entry.model_copy.assert_called_once()
        call_kwargs = mock_log_entry.model_copy.call_args
        update_dict = call_kwargs.kwargs.get(
            "update", call_kwargs[1].get("update", {})
        )
        assert "id" in update_dict
        assert update_dict["id"].startswith("log-")
        assert result == returned_entry

    @pytest.mark.asyncio
    async def test_create_log_entry_keeps_existing_id(
        self, log_service, mock_connection, mock_log_entry, mock_row
    ):
        """create_log_entry should not generate ID if one already exists."""
        _, _, mock_cursor = mock_connection
        mock_cursor.fetchone.return_value = mock_row

        with patch(
            "services.service_log.LogEntry.from_row", return_value=mock_log_entry
        ):
            await log_service.create_log_entry(mock_log_entry)

        mock_log_entry.model_copy.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_log_entry_db_error(
        self, log_service, mock_connection
    ):
        """create_log_entry should raise on database error."""
        _, mock_conn, _ = mock_connection
        mock_conn.execute.side_effect = Exception("DB error")

        mock_entry = MagicMock()
        mock_entry.id = "log-test123"
        mock_entry.level = "INFO"
        mock_entry.to_insert_params.return_value = {
            "id": "log-test123",
            "timestamp": "2025-01-01T00:00:00",
            "level": "INFO",
            "source": "test",
            "message": "Test",
            "tags": None,
            "extra_data": None,
        }

        with pytest.raises(Exception, match="DB error"):
            await log_service.create_log_entry(mock_entry)

    @pytest.mark.asyncio
    async def test_create_log_entry_returns_original_when_row_not_found(
        self, log_service, mock_connection, mock_log_entry
    ):
        """create_log_entry should return original entry if re-fetch returns None."""
        _, _, mock_cursor = mock_connection
        mock_cursor.fetchone.return_value = None

        result = await log_service.create_log_entry(mock_log_entry)

        assert result == mock_log_entry


class TestGetLogs:
    """Tests for get_logs method."""

    @pytest.mark.asyncio
    async def test_get_logs_no_filter(self, log_service, mock_connection):
        """get_logs should return logs with default limit and offset."""
        _, mock_conn, mock_cursor = mock_connection
        mock_cursor.fetchall.return_value = []

        result = await log_service.get_logs()

        assert result == []
        mock_conn.execute.assert_called_once()
        call_args = mock_conn.execute.call_args
        sql = call_args[0][0]
        params = call_args[0][1]
        assert "WHERE" not in sql
        assert "LIMIT" in sql
        assert "OFFSET" in sql
        # Default limit=100, offset=0
        assert params == [100, 0]

    @pytest.mark.asyncio
    async def test_get_logs_with_level_filter(
        self, log_service, mock_connection
    ):
        """get_logs should apply level filter."""
        _, mock_conn, mock_cursor = mock_connection
        mock_cursor.fetchall.return_value = []

        mock_filter = MagicMock()
        mock_filter.level = "ERROR"
        mock_filter.source = None
        mock_filter.limit = 100
        mock_filter.offset = 0

        result = await log_service.get_logs(filters=mock_filter)

        assert result == []
        call_args = mock_conn.execute.call_args
        sql = call_args[0][0]
        params = call_args[0][1]
        assert "WHERE" in sql
        assert "level = ?" in sql
        assert "ERROR" in params

    @pytest.mark.asyncio
    async def test_get_logs_with_all_filters(
        self, log_service, mock_connection
    ):
        """get_logs should apply level, source, limit, and offset filters."""
        _, mock_conn, mock_cursor = mock_connection

        mock_row = MagicMock()
        mock_cursor.fetchall.return_value = [mock_row]
        returned_entry = MagicMock()

        mock_filter = MagicMock()
        mock_filter.level = "ERROR"
        mock_filter.source = "api"
        mock_filter.limit = 50
        mock_filter.offset = 10

        with patch(
            "services.service_log.LogEntry.from_row", return_value=returned_entry
        ):
            result = await log_service.get_logs(filters=mock_filter)

        assert result == [returned_entry]
        call_args = mock_conn.execute.call_args
        sql = call_args[0][0]
        params = call_args[0][1]
        assert "level = ?" in sql
        assert "source = ?" in sql
        assert params == ["ERROR", "api", 50, 10]

    @pytest.mark.asyncio
    async def test_get_logs_db_error(self, log_service, mock_connection):
        """get_logs should raise on database error."""
        _, mock_conn, _ = mock_connection
        mock_conn.execute.side_effect = Exception("DB error")

        with pytest.raises(Exception, match="DB error"):
            await log_service.get_logs()


class TestGetLogById:
    """Tests for get_log_by_id method."""

    @pytest.mark.asyncio
    async def test_get_log_by_id_found(
        self, log_service, mock_connection, mock_row
    ):
        """get_log_by_id should return log entry when found."""
        _, _, mock_cursor = mock_connection
        mock_cursor.fetchone.return_value = mock_row
        returned_entry = MagicMock()

        with patch(
            "services.service_log.LogEntry.from_row", return_value=returned_entry
        ):
            result = await log_service.get_log_by_id("log-12345678")

        assert result == returned_entry

    @pytest.mark.asyncio
    async def test_get_log_by_id_not_found(
        self, log_service, mock_connection
    ):
        """get_log_by_id should return None when not found."""
        _, _, mock_cursor = mock_connection
        mock_cursor.fetchone.return_value = None

        result = await log_service.get_log_by_id("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_log_by_id_executes_correct_sql(
        self, log_service, mock_connection
    ):
        """get_log_by_id should query by id."""
        _, mock_conn, mock_cursor = mock_connection
        mock_cursor.fetchone.return_value = None

        await log_service.get_log_by_id("log-abc12345")

        mock_conn.execute.assert_called_once()
        call_args = mock_conn.execute.call_args
        sql = call_args[0][0]
        params = call_args[0][1]
        assert "WHERE id = ?" in sql
        assert params == ("log-abc12345",)

    @pytest.mark.asyncio
    async def test_get_log_by_id_db_error(
        self, log_service, mock_connection
    ):
        """get_log_by_id should raise on database error."""
        _, mock_conn, _ = mock_connection
        mock_conn.execute.side_effect = Exception("DB error")

        with pytest.raises(Exception, match="DB error"):
            await log_service.get_log_by_id("log-12345678")


class TestCountLogs:
    """Tests for count_logs method."""

    @pytest.mark.asyncio
    async def test_count_logs_no_filter(self, log_service, mock_connection):
        """count_logs should return count without filters."""
        _, _, mock_cursor = mock_connection
        mock_cursor.fetchone.return_value = MagicMock(
            __getitem__=lambda self, i: 42
        )

        result = await log_service.count_logs()

        assert result == 42

    @pytest.mark.asyncio
    async def test_count_logs_with_filter(
        self, log_service, mock_connection
    ):
        """count_logs should apply level and source filters."""
        _, mock_conn, mock_cursor = mock_connection
        mock_cursor.fetchone.return_value = MagicMock(
            __getitem__=lambda self, i: 10
        )

        mock_filter = MagicMock()
        mock_filter.level = "ERROR"
        mock_filter.source = "api"

        result = await log_service.count_logs(filters=mock_filter)

        assert result == 10
        call_args = mock_conn.execute.call_args
        sql = call_args[0][0]
        params = call_args[0][1]
        assert "WHERE" in sql
        assert "level = ?" in sql
        assert "source = ?" in sql
        assert params == ["ERROR", "api"]

    @pytest.mark.asyncio
    async def test_count_logs_returns_zero_when_no_row(
        self, log_service, mock_connection
    ):
        """count_logs should return 0 when fetchone returns None."""
        _, _, mock_cursor = mock_connection
        mock_cursor.fetchone.return_value = None

        result = await log_service.count_logs()

        assert result == 0

    @pytest.mark.asyncio
    async def test_count_logs_db_error(self, log_service, mock_connection):
        """count_logs should raise on database error."""
        _, mock_conn, _ = mock_connection
        mock_conn.execute.side_effect = Exception("DB error")

        with pytest.raises(Exception, match="DB error"):
            await log_service.count_logs()


class TestPurgeLogs:
    """Tests for purge_logs method."""

    @pytest.mark.asyncio
    async def test_purge_logs_success(self, log_service, mock_connection):
        """purge_logs should delete all logs and return count."""
        _, mock_conn, mock_cursor = mock_connection

        # First execute (SELECT COUNT) returns the count row
        count_row = MagicMock(__getitem__=lambda self, i: 100)
        mock_cursor.fetchone.return_value = count_row

        result = await log_service.purge_logs()

        assert result == 100
        mock_conn.commit.assert_called_once()
        # execute called twice: once for count, once for delete
        assert mock_conn.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_purge_logs_returns_zero_when_empty(
        self, log_service, mock_connection
    ):
        """purge_logs should return 0 when no logs exist."""
        _, mock_conn, mock_cursor = mock_connection
        mock_cursor.fetchone.return_value = None

        result = await log_service.purge_logs()

        assert result == 0

    @pytest.mark.asyncio
    async def test_purge_logs_db_error(self, log_service, mock_connection):
        """purge_logs should raise on database error."""
        _, mock_conn, _ = mock_connection
        mock_conn.execute.side_effect = Exception("DB error")

        with pytest.raises(Exception, match="DB error"):
            await log_service.purge_logs()
