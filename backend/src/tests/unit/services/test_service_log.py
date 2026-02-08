"""
Unit tests for services/service_log.py

Tests log service CRUD operations.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.exc import SQLAlchemyError

from services.service_log import LogService


@pytest.fixture
def log_service():
    """Create LogService instance."""
    return LogService()


@pytest.fixture
def mock_log_entry():
    """Create mock LogEntry."""
    entry = MagicMock()
    entry.id = "log-12345678"
    entry.level = "INFO"
    entry.message = "Test message"
    entry.source = "test"
    return entry


@pytest.fixture
def mock_table_entry():
    """Create mock table entry."""
    entry = MagicMock()
    entry.id = "log-12345678"
    entry.level = "INFO"
    entry.message = "Test message"
    return entry


class TestLogServiceInit:
    """Tests for LogService initialization."""

    def test_init_sets_initialized_false(self):
        """LogService should initialize with _initialized=False."""
        service = LogService()
        assert service._initialized is False


class TestEnsureInitialized:
    """Tests for _ensure_initialized method."""

    @pytest.mark.asyncio
    async def test_ensure_initialized_calls_init_db(self, log_service):
        """_ensure_initialized should call initialize_logs_database once."""
        with patch(
            "services.service_log.initialize_logs_database", new_callable=AsyncMock
        ) as mock_init:
            await log_service._ensure_initialized()
            mock_init.assert_called_once()
            assert log_service._initialized is True

    @pytest.mark.asyncio
    async def test_ensure_initialized_only_once(self, log_service):
        """_ensure_initialized should only initialize once."""
        with patch(
            "services.service_log.initialize_logs_database", new_callable=AsyncMock
        ) as mock_init:
            await log_service._ensure_initialized()
            await log_service._ensure_initialized()
            mock_init.assert_called_once()


class TestCreateLogEntry:
    """Tests for create_log_entry method."""

    @pytest.mark.asyncio
    async def test_create_log_entry_success(
        self, log_service, mock_log_entry, mock_table_entry
    ):
        """create_log_entry should create and return log entry."""
        mock_session = AsyncMock()
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_session
        mock_context.__aexit__.return_value = False

        mock_log_entry.to_table_model.return_value = mock_table_entry

        with (
            patch(
                "services.service_log.initialize_logs_database", new_callable=AsyncMock
            ),
            patch(
                "services.service_log.db_manager.get_session", return_value=mock_context
            ),
            patch(
                "services.service_log.LogEntry.from_table_model",
                return_value=mock_log_entry,
            ),
        ):
            result = await log_service.create_log_entry(mock_log_entry)

            assert result == mock_log_entry
            mock_session.add.assert_called_once_with(mock_table_entry)
            mock_session.flush.assert_called_once()
            mock_session.refresh.assert_called_once_with(mock_table_entry)

    @pytest.mark.asyncio
    async def test_create_log_entry_generates_id(self, log_service):
        """create_log_entry should generate ID if not provided."""
        mock_log_entry = MagicMock()
        mock_log_entry.id = None
        mock_table_entry = MagicMock()
        mock_log_entry.to_table_model.return_value = mock_table_entry

        mock_session = AsyncMock()
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_session
        mock_context.__aexit__.return_value = False

        with (
            patch(
                "services.service_log.initialize_logs_database", new_callable=AsyncMock
            ),
            patch(
                "services.service_log.db_manager.get_session", return_value=mock_context
            ),
            patch("services.service_log.LogEntry.from_table_model") as mock_from,
        ):
            mock_from.return_value = mock_log_entry
            await log_service.create_log_entry(mock_log_entry)

            assert mock_log_entry.id is not None
            assert mock_log_entry.id.startswith("log-")

    @pytest.mark.asyncio
    async def test_create_log_entry_db_error(self, log_service):
        """create_log_entry should raise on database error."""
        from contextlib import asynccontextmanager

        mock_log_entry = MagicMock()
        mock_log_entry.id = "log-test123"
        mock_log_entry.level = "INFO"
        mock_table_entry = MagicMock()
        mock_log_entry.to_table_model.return_value = mock_table_entry

        @asynccontextmanager
        async def mock_session_context():
            mock_session = AsyncMock()
            mock_session.flush.side_effect = SQLAlchemyError("DB error")
            yield mock_session

        with (
            patch(
                "services.service_log.initialize_logs_database", new_callable=AsyncMock
            ),
            patch("services.service_log.db_manager.get_session", mock_session_context),
            patch("services.service_log.logger"),
        ):
            with pytest.raises(SQLAlchemyError):
                await log_service.create_log_entry(mock_log_entry)


class TestGetLogs:
    """Tests for get_logs method."""

    @pytest.mark.asyncio
    async def test_get_logs_no_filter(self, log_service):
        """get_logs should return logs with default limit."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []

        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_session
        mock_context.__aexit__.return_value = False

        with (
            patch(
                "services.service_log.initialize_logs_database", new_callable=AsyncMock
            ),
            patch(
                "services.service_log.db_manager.get_session", return_value=mock_context
            ),
        ):
            result = await log_service.get_logs()
            assert result == []

    @pytest.mark.asyncio
    async def test_get_logs_with_filter(self, log_service):
        """get_logs should apply filters."""
        mock_filter = MagicMock()
        mock_filter.level = "ERROR"
        mock_filter.source = "test"
        mock_filter.limit = 50
        mock_filter.offset = 10

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []

        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_session
        mock_context.__aexit__.return_value = False

        with (
            patch(
                "services.service_log.initialize_logs_database", new_callable=AsyncMock
            ),
            patch(
                "services.service_log.db_manager.get_session", return_value=mock_context
            ),
        ):
            result = await log_service.get_logs(filters=mock_filter)
            assert result == []

    @pytest.mark.asyncio
    async def test_get_logs_db_error(self, log_service):
        """get_logs should raise on database error."""
        mock_session = AsyncMock()
        mock_session.execute.side_effect = SQLAlchemyError("DB error")
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_session
        mock_context.__aexit__.return_value = False

        with (
            patch(
                "services.service_log.initialize_logs_database", new_callable=AsyncMock
            ),
            patch(
                "services.service_log.db_manager.get_session", return_value=mock_context
            ),
        ):
            with pytest.raises(SQLAlchemyError):
                await log_service.get_logs()


class TestGetLogById:
    """Tests for get_log_by_id method."""

    @pytest.mark.asyncio
    async def test_get_log_by_id_found(
        self, log_service, mock_table_entry, mock_log_entry
    ):
        """get_log_by_id should return log entry when found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_table_entry

        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_session
        mock_context.__aexit__.return_value = False

        with (
            patch(
                "services.service_log.initialize_logs_database", new_callable=AsyncMock
            ),
            patch(
                "services.service_log.db_manager.get_session", return_value=mock_context
            ),
            patch(
                "services.service_log.LogEntry.from_table_model",
                return_value=mock_log_entry,
            ),
        ):
            result = await log_service.get_log_by_id("log-12345678")
            assert result == mock_log_entry

    @pytest.mark.asyncio
    async def test_get_log_by_id_not_found(self, log_service):
        """get_log_by_id should return None when not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_session
        mock_context.__aexit__.return_value = False

        with (
            patch(
                "services.service_log.initialize_logs_database", new_callable=AsyncMock
            ),
            patch(
                "services.service_log.db_manager.get_session", return_value=mock_context
            ),
        ):
            result = await log_service.get_log_by_id("nonexistent")
            assert result is None

    @pytest.mark.asyncio
    async def test_get_log_by_id_db_error(self, log_service):
        """get_log_by_id should raise on database error."""
        mock_session = AsyncMock()
        mock_session.execute.side_effect = SQLAlchemyError("DB error")
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_session
        mock_context.__aexit__.return_value = False

        with (
            patch(
                "services.service_log.initialize_logs_database", new_callable=AsyncMock
            ),
            patch(
                "services.service_log.db_manager.get_session", return_value=mock_context
            ),
        ):
            with pytest.raises(SQLAlchemyError):
                await log_service.get_log_by_id("log-12345678")


class TestCountLogs:
    """Tests for count_logs method."""

    @pytest.mark.asyncio
    async def test_count_logs_no_filter(self, log_service):
        """count_logs should return count without filters."""
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 42

        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_session
        mock_context.__aexit__.return_value = False

        with (
            patch(
                "services.service_log.initialize_logs_database", new_callable=AsyncMock
            ),
            patch(
                "services.service_log.db_manager.get_session", return_value=mock_context
            ),
        ):
            result = await log_service.count_logs()
            assert result == 42

    @pytest.mark.asyncio
    async def test_count_logs_with_filter(self, log_service):
        """count_logs should apply level and source filters."""
        mock_filter = MagicMock()
        mock_filter.level = "ERROR"
        mock_filter.source = "api"

        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 10

        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_session
        mock_context.__aexit__.return_value = False

        with (
            patch(
                "services.service_log.initialize_logs_database", new_callable=AsyncMock
            ),
            patch(
                "services.service_log.db_manager.get_session", return_value=mock_context
            ),
        ):
            result = await log_service.count_logs(filters=mock_filter)
            assert result == 10

    @pytest.mark.asyncio
    async def test_count_logs_db_error(self, log_service):
        """count_logs should raise on database error."""
        mock_session = AsyncMock()
        mock_session.execute.side_effect = SQLAlchemyError("DB error")
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_session
        mock_context.__aexit__.return_value = False

        with (
            patch(
                "services.service_log.initialize_logs_database", new_callable=AsyncMock
            ),
            patch(
                "services.service_log.db_manager.get_session", return_value=mock_context
            ),
        ):
            with pytest.raises(SQLAlchemyError):
                await log_service.count_logs()


class TestPurgeLogs:
    """Tests for purge_logs method."""

    @pytest.mark.asyncio
    async def test_purge_logs_success(self, log_service):
        """purge_logs should delete all logs and return count."""
        mock_count_result = MagicMock()
        mock_count_result.scalar_one.return_value = 100

        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_count_result
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_session
        mock_context.__aexit__.return_value = False

        with (
            patch(
                "services.service_log.initialize_logs_database", new_callable=AsyncMock
            ),
            patch(
                "services.service_log.db_manager.get_session", return_value=mock_context
            ),
        ):
            result = await log_service.purge_logs()

            assert result == 100
            mock_session.commit.assert_called_once()
            # execute called twice: once for count, once for delete
            assert mock_session.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_purge_logs_db_error(self, log_service):
        """purge_logs should raise on database error."""
        mock_session = AsyncMock()
        mock_session.execute.side_effect = SQLAlchemyError("DB error")
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_session
        mock_context.__aexit__.return_value = False

        with (
            patch(
                "services.service_log.initialize_logs_database", new_callable=AsyncMock
            ),
            patch(
                "services.service_log.db_manager.get_session", return_value=mock_context
            ),
        ):
            with pytest.raises(SQLAlchemyError):
                await log_service.purge_logs()


class TestGlobalInstance:
    """Tests for global log_service instance."""

    def test_log_service_exists(self):
        """Module should export log_service instance."""
        from services.service_log import log_service

        assert isinstance(log_service, LogService)
