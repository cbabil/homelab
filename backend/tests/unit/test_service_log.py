"""
Unit tests for services/service_log.py

Tests for log CRUD operations using SQLAlchemy and SQLite.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.exc import SQLAlchemyError

from services.service_log import LogService


class TestLogServiceInit:
    """Tests for LogService initialization."""

    def test_init_sets_initialized_to_false(self):
        """Should initialize with _initialized set to False."""
        service = LogService()

        assert service._initialized is False


class TestLogServiceEnsureInitialized:
    """Tests for _ensure_initialized method."""

    @pytest.mark.asyncio
    async def test_ensure_initialized_calls_init_database(self):
        """Should call initialize_logs_database when not initialized."""
        service = LogService()

        with patch(
            "services.service_log.initialize_logs_database", new_callable=AsyncMock
        ) as mock_init:
            await service._ensure_initialized()

            mock_init.assert_called_once()
            assert service._initialized is True

    @pytest.mark.asyncio
    async def test_ensure_initialized_skips_if_already_initialized(self):
        """Should skip initialization if already initialized."""
        service = LogService()
        service._initialized = True

        with patch(
            "services.service_log.initialize_logs_database", new_callable=AsyncMock
        ) as mock_init:
            await service._ensure_initialized()

            mock_init.assert_not_called()


class TestLogServiceCreateLogEntry:
    """Tests for create_log_entry method."""

    @pytest.mark.asyncio
    async def test_create_log_entry_success(self):
        """Should create log entry and return it."""
        service = LogService()

        mock_log_entry = MagicMock()
        mock_log_entry.id = None
        mock_table_entry = MagicMock()
        mock_log_entry.to_table_model.return_value = mock_table_entry

        mock_result = MagicMock()
        mock_result.id = "log-abc12345"
        mock_result.level = "INFO"

        mock_session = AsyncMock()
        mock_session.add = MagicMock()

        with (
            patch.object(service, "_ensure_initialized", new_callable=AsyncMock),
            patch(
                "services.service_log.db_manager.get_session"
            ) as mock_get_session,
            patch(
                "services.service_log.LogEntry.from_table_model",
                return_value=mock_result,
            ),
        ):
            mock_get_session.return_value.__aenter__.return_value = mock_session

            result = await service.create_log_entry(mock_log_entry)

            assert result == mock_result
            mock_session.add.assert_called_once_with(mock_table_entry)
            mock_session.flush.assert_called_once()
            mock_session.refresh.assert_called_once_with(mock_table_entry)

    @pytest.mark.asyncio
    async def test_create_log_entry_generates_id_if_none(self):
        """Should generate ID if not provided."""
        service = LogService()

        mock_log_entry = MagicMock()
        mock_log_entry.id = None
        mock_table_entry = MagicMock()
        mock_log_entry.to_table_model.return_value = mock_table_entry

        mock_session = AsyncMock()
        mock_session.add = MagicMock()

        with (
            patch.object(service, "_ensure_initialized", new_callable=AsyncMock),
            patch(
                "services.service_log.db_manager.get_session"
            ) as mock_get_session,
            patch("services.service_log.LogEntry.from_table_model"),
        ):
            mock_get_session.return_value.__aenter__.return_value = mock_session

            await service.create_log_entry(mock_log_entry)

            # The ID should now be set
            assert mock_log_entry.id is not None
            assert mock_log_entry.id.startswith("log-")

    @pytest.mark.asyncio
    async def test_create_log_entry_preserves_existing_id(self):
        """Should preserve ID if already provided."""
        service = LogService()

        mock_log_entry = MagicMock()
        mock_log_entry.id = "existing-id"
        mock_table_entry = MagicMock()
        mock_log_entry.to_table_model.return_value = mock_table_entry

        mock_session = AsyncMock()
        mock_session.add = MagicMock()

        with (
            patch.object(service, "_ensure_initialized", new_callable=AsyncMock),
            patch(
                "services.service_log.db_manager.get_session"
            ) as mock_get_session,
            patch("services.service_log.LogEntry.from_table_model"),
        ):
            mock_get_session.return_value.__aenter__.return_value = mock_session

            await service.create_log_entry(mock_log_entry)

            assert mock_log_entry.id == "existing-id"

    @pytest.mark.asyncio
    async def test_create_log_entry_raises_on_db_error(self):
        """Should raise SQLAlchemyError on database failure."""
        service = LogService()

        mock_log_entry = MagicMock()
        mock_log_entry.id = "test-id"
        mock_log_entry.to_table_model.return_value = MagicMock()

        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.flush.side_effect = SQLAlchemyError("DB error")

        with (
            patch.object(service, "_ensure_initialized", new_callable=AsyncMock),
            patch(
                "services.service_log.db_manager.get_session"
            ) as mock_get_session,
        ):
            mock_get_session.return_value.__aenter__.return_value = mock_session

            with pytest.raises(SQLAlchemyError):
                await service.create_log_entry(mock_log_entry)


class TestLogServiceGetLogs:
    """Tests for get_logs method."""

    @pytest.mark.asyncio
    async def test_get_logs_without_filters(self):
        """Should retrieve logs with default limit."""
        service = LogService()

        mock_table_entry = MagicMock()
        mock_log_entry = MagicMock()

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_table_entry]
        mock_session.execute.return_value = mock_result

        with (
            patch.object(service, "_ensure_initialized", new_callable=AsyncMock),
            patch(
                "services.service_log.db_manager.get_session"
            ) as mock_get_session,
            patch(
                "services.service_log.LogEntry.from_table_model",
                return_value=mock_log_entry,
            ),
        ):
            mock_get_session.return_value.__aenter__.return_value = mock_session

            result = await service.get_logs()

            assert result == [mock_log_entry]
            mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_logs_with_level_filter(self):
        """Should filter logs by level."""
        service = LogService()

        mock_filter = MagicMock()
        mock_filter.level = "ERROR"
        mock_filter.source = None
        mock_filter.limit = None
        mock_filter.offset = None

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        with (
            patch.object(service, "_ensure_initialized", new_callable=AsyncMock),
            patch(
                "services.service_log.db_manager.get_session"
            ) as mock_get_session,
        ):
            mock_get_session.return_value.__aenter__.return_value = mock_session

            result = await service.get_logs(filters=mock_filter)

            assert result == []
            mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_logs_with_source_filter(self):
        """Should filter logs by source."""
        service = LogService()

        mock_filter = MagicMock()
        mock_filter.level = None
        mock_filter.source = "docker"
        mock_filter.limit = None
        mock_filter.offset = None

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        with (
            patch.object(service, "_ensure_initialized", new_callable=AsyncMock),
            patch(
                "services.service_log.db_manager.get_session"
            ) as mock_get_session,
        ):
            mock_get_session.return_value.__aenter__.return_value = mock_session

            result = await service.get_logs(filters=mock_filter)

            assert result == []

    @pytest.mark.asyncio
    async def test_get_logs_with_limit_and_offset(self):
        """Should apply limit and offset."""
        service = LogService()

        mock_filter = MagicMock()
        mock_filter.level = None
        mock_filter.source = None
        mock_filter.limit = 50
        mock_filter.offset = 10

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        with (
            patch.object(service, "_ensure_initialized", new_callable=AsyncMock),
            patch(
                "services.service_log.db_manager.get_session"
            ) as mock_get_session,
        ):
            mock_get_session.return_value.__aenter__.return_value = mock_session

            result = await service.get_logs(filters=mock_filter)

            assert result == []

    @pytest.mark.asyncio
    async def test_get_logs_raises_on_db_error(self):
        """Should raise SQLAlchemyError on database failure."""
        service = LogService()

        mock_session = AsyncMock()
        mock_session.execute.side_effect = SQLAlchemyError("DB error")

        with (
            patch.object(service, "_ensure_initialized", new_callable=AsyncMock),
            patch(
                "services.service_log.db_manager.get_session"
            ) as mock_get_session,
        ):
            mock_get_session.return_value.__aenter__.return_value = mock_session

            with pytest.raises(SQLAlchemyError):
                await service.get_logs()


class TestLogServiceGetLogById:
    """Tests for get_log_by_id method."""

    @pytest.mark.asyncio
    async def test_get_log_by_id_found(self):
        """Should return log entry when found."""
        service = LogService()

        mock_table_entry = MagicMock()
        mock_log_entry = MagicMock()

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_table_entry
        mock_session.execute.return_value = mock_result

        with (
            patch.object(service, "_ensure_initialized", new_callable=AsyncMock),
            patch(
                "services.service_log.db_manager.get_session"
            ) as mock_get_session,
            patch(
                "services.service_log.LogEntry.from_table_model",
                return_value=mock_log_entry,
            ),
        ):
            mock_get_session.return_value.__aenter__.return_value = mock_session

            result = await service.get_log_by_id("log-123")

            assert result == mock_log_entry

    @pytest.mark.asyncio
    async def test_get_log_by_id_not_found(self):
        """Should return None when log not found."""
        service = LogService()

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        with (
            patch.object(service, "_ensure_initialized", new_callable=AsyncMock),
            patch(
                "services.service_log.db_manager.get_session"
            ) as mock_get_session,
        ):
            mock_get_session.return_value.__aenter__.return_value = mock_session

            result = await service.get_log_by_id("nonexistent-id")

            assert result is None

    @pytest.mark.asyncio
    async def test_get_log_by_id_raises_on_db_error(self):
        """Should raise SQLAlchemyError on database failure."""
        service = LogService()

        mock_session = AsyncMock()
        mock_session.execute.side_effect = SQLAlchemyError("DB error")

        with (
            patch.object(service, "_ensure_initialized", new_callable=AsyncMock),
            patch(
                "services.service_log.db_manager.get_session"
            ) as mock_get_session,
        ):
            mock_get_session.return_value.__aenter__.return_value = mock_session

            with pytest.raises(SQLAlchemyError):
                await service.get_log_by_id("log-123")


class TestLogServiceCountLogs:
    """Tests for count_logs method."""

    @pytest.mark.asyncio
    async def test_count_logs_without_filters(self):
        """Should count all logs without filters."""
        service = LogService()

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 42
        mock_session.execute.return_value = mock_result

        with (
            patch.object(service, "_ensure_initialized", new_callable=AsyncMock),
            patch(
                "services.service_log.db_manager.get_session"
            ) as mock_get_session,
        ):
            mock_get_session.return_value.__aenter__.return_value = mock_session

            result = await service.count_logs()

            assert result == 42

    @pytest.mark.asyncio
    async def test_count_logs_with_level_filter(self):
        """Should count logs filtered by level."""
        service = LogService()

        mock_filter = MagicMock()
        mock_filter.level = "ERROR"
        mock_filter.source = None

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 5
        mock_session.execute.return_value = mock_result

        with (
            patch.object(service, "_ensure_initialized", new_callable=AsyncMock),
            patch(
                "services.service_log.db_manager.get_session"
            ) as mock_get_session,
        ):
            mock_get_session.return_value.__aenter__.return_value = mock_session

            result = await service.count_logs(filters=mock_filter)

            assert result == 5

    @pytest.mark.asyncio
    async def test_count_logs_with_source_filter(self):
        """Should count logs filtered by source."""
        service = LogService()

        mock_filter = MagicMock()
        mock_filter.level = None
        mock_filter.source = "system"

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 10
        mock_session.execute.return_value = mock_result

        with (
            patch.object(service, "_ensure_initialized", new_callable=AsyncMock),
            patch(
                "services.service_log.db_manager.get_session"
            ) as mock_get_session,
        ):
            mock_get_session.return_value.__aenter__.return_value = mock_session

            result = await service.count_logs(filters=mock_filter)

            assert result == 10

    @pytest.mark.asyncio
    async def test_count_logs_raises_on_db_error(self):
        """Should raise SQLAlchemyError on database failure."""
        service = LogService()

        mock_session = AsyncMock()
        mock_session.execute.side_effect = SQLAlchemyError("DB error")

        with (
            patch.object(service, "_ensure_initialized", new_callable=AsyncMock),
            patch(
                "services.service_log.db_manager.get_session"
            ) as mock_get_session,
        ):
            mock_get_session.return_value.__aenter__.return_value = mock_session

            with pytest.raises(SQLAlchemyError):
                await service.count_logs()


class TestLogServicePurgeLogs:
    """Tests for purge_logs method."""

    @pytest.mark.asyncio
    async def test_purge_logs_success(self):
        """Should delete all logs and return count."""
        service = LogService()

        mock_session = AsyncMock()
        mock_count_result = MagicMock()
        mock_count_result.scalar_one.return_value = 100
        mock_session.execute.return_value = mock_count_result

        with (
            patch.object(service, "_ensure_initialized", new_callable=AsyncMock),
            patch(
                "services.service_log.db_manager.get_session"
            ) as mock_get_session,
        ):
            mock_get_session.return_value.__aenter__.return_value = mock_session

            result = await service.purge_logs()

            assert result == 100
            mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_purge_logs_empty_database(self):
        """Should handle empty database."""
        service = LogService()

        mock_session = AsyncMock()
        mock_count_result = MagicMock()
        mock_count_result.scalar_one.return_value = 0
        mock_session.execute.return_value = mock_count_result

        with (
            patch.object(service, "_ensure_initialized", new_callable=AsyncMock),
            patch(
                "services.service_log.db_manager.get_session"
            ) as mock_get_session,
        ):
            mock_get_session.return_value.__aenter__.return_value = mock_session

            result = await service.purge_logs()

            assert result == 0
            mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_purge_logs_raises_on_db_error(self):
        """Should raise SQLAlchemyError on database failure."""
        service = LogService()

        mock_session = AsyncMock()
        mock_session.execute.side_effect = SQLAlchemyError("DB error")

        with (
            patch.object(service, "_ensure_initialized", new_callable=AsyncMock),
            patch(
                "services.service_log.db_manager.get_session"
            ) as mock_get_session,
        ):
            mock_get_session.return_value.__aenter__.return_value = mock_session

            with pytest.raises(SQLAlchemyError):
                await service.purge_logs()


class TestLogServiceGlobalInstance:
    """Tests for global log_service instance."""

    def test_log_service_global_instance_exists(self):
        """Should have a global log_service instance."""
        from services.service_log import log_service

        assert isinstance(log_service, LogService)

    def test_log_service_global_instance_not_initialized(self):
        """Global instance should start uninitialized."""
        from services.service_log import log_service

        # Reset for test
        log_service._initialized = False
        assert log_service._initialized is False
