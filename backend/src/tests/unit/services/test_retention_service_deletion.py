"""
Unit tests for services/retention_service.py - Deletion operations.

Tests preview_records_for_deletion, preview_log_deletion, perform_secure_deletion,
and delete_logs_batch methods.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.retention import (
    CleanupPreview,
    RetentionType,
)
from services.retention_service import RetentionService


@pytest.fixture
def mock_db_service():
    """Create mock database service."""
    return MagicMock()


@pytest.fixture
def mock_auth_service():
    """Create mock auth service."""
    return MagicMock()


@pytest.fixture
def mock_connection():
    """Create mock database connection."""
    conn = AsyncMock()
    conn.execute = AsyncMock()
    conn.commit = AsyncMock()
    conn.rollback = AsyncMock()
    return conn


@pytest.fixture
def retention_service(mock_db_service, mock_auth_service, mock_connection):
    """Create RetentionService with mocked dependencies."""
    mock_db_service.get_connection = MagicMock()
    mock_db_service.get_connection.return_value.__aenter__ = AsyncMock(
        return_value=mock_connection
    )
    mock_db_service.get_connection.return_value.__aexit__ = AsyncMock()

    with patch("services.retention_service.logger"):
        return RetentionService(mock_db_service, mock_auth_service)


class TestPreviewRecordsForDeletion:
    """Tests for _preview_records_for_deletion method."""

    @pytest.mark.asyncio
    async def test_preview_audit_logs(self, retention_service):
        """_preview_records_for_deletion should preview audit logs."""
        preview = CleanupPreview(
            retention_type=RetentionType.AUDIT_LOGS,
            affected_records=50,
            cutoff_date="2024-01-15T00:00:00+00:00",
        )

        with (
            patch("services.retention_service.logger"),
            patch.object(
                retention_service,
                "_preview_log_deletion",
                new_callable=AsyncMock,
                return_value=preview,
            ),
        ):
            result = await retention_service._preview_records_for_deletion(
                RetentionType.AUDIT_LOGS, "2024-01-15T00:00:00+00:00"
            )

        assert result is not None
        assert result.affected_records == 50

    @pytest.mark.asyncio
    async def test_preview_access_logs(self, retention_service):
        """_preview_records_for_deletion should preview access logs."""
        preview = CleanupPreview(
            retention_type=RetentionType.ACCESS_LOGS,
            affected_records=100,
            cutoff_date="2024-01-15T00:00:00+00:00",
        )

        with (
            patch("services.retention_service.logger"),
            patch.object(
                retention_service,
                "_preview_log_deletion",
                new_callable=AsyncMock,
                return_value=preview,
            ),
        ):
            result = await retention_service._preview_records_for_deletion(
                RetentionType.ACCESS_LOGS, "2024-01-15T00:00:00+00:00"
            )

        assert result is not None

    @pytest.mark.asyncio
    async def test_preview_application_logs(self, retention_service):
        """_preview_records_for_deletion should preview application logs."""
        preview = CleanupPreview(
            retention_type=RetentionType.APPLICATION_LOGS,
            affected_records=75,
            cutoff_date="2024-01-15T00:00:00+00:00",
        )

        with (
            patch("services.retention_service.logger"),
            patch.object(
                retention_service,
                "_preview_log_deletion",
                new_callable=AsyncMock,
                return_value=preview,
            ),
        ):
            result = await retention_service._preview_records_for_deletion(
                RetentionType.APPLICATION_LOGS, "2024-01-15T00:00:00+00:00"
            )

        assert result is not None

    @pytest.mark.asyncio
    async def test_preview_server_logs(self, retention_service):
        """_preview_records_for_deletion should preview server logs."""
        preview = CleanupPreview(
            retention_type=RetentionType.SERVER_LOGS,
            affected_records=200,
            cutoff_date="2024-01-15T00:00:00+00:00",
        )

        with (
            patch("services.retention_service.logger"),
            patch.object(
                retention_service,
                "_preview_log_deletion",
                new_callable=AsyncMock,
                return_value=preview,
            ),
        ):
            result = await retention_service._preview_records_for_deletion(
                RetentionType.SERVER_LOGS, "2024-01-15T00:00:00+00:00"
            )

        assert result is not None

    @pytest.mark.asyncio
    async def test_preview_unsupported_type_returns_none(self, retention_service):
        """_preview_records_for_deletion should return None for unsupported types."""
        with patch("services.retention_service.logger"):
            result = await retention_service._preview_records_for_deletion(
                RetentionType.METRICS, "2024-01-15T00:00:00+00:00"
            )

        assert result is None

    @pytest.mark.asyncio
    async def test_preview_handles_exception(self, retention_service):
        """_preview_records_for_deletion should handle exceptions."""
        with (
            patch("services.retention_service.logger") as mock_logger,
            patch.object(
                retention_service,
                "_preview_log_deletion",
                new_callable=AsyncMock,
                side_effect=Exception("Preview error"),
            ),
        ):
            result = await retention_service._preview_records_for_deletion(
                RetentionType.AUDIT_LOGS, "2024-01-15T00:00:00+00:00"
            )

        assert result is None
        mock_logger.error.assert_called()


class TestPreviewLogDeletion:
    """Tests for _preview_log_deletion method."""

    @pytest.mark.asyncio
    async def test_preview_log_deletion_with_records(
        self, retention_service, mock_connection
    ):
        """_preview_log_deletion should return preview with affected records."""
        # Mock count query
        count_cursor = AsyncMock()
        count_cursor.fetchone = AsyncMock(return_value={"count": 150})

        # Mock date range query
        date_cursor = AsyncMock()
        date_cursor.fetchone = AsyncMock(
            return_value={
                "oldest": "2024-01-01T00:00:00+00:00",
                "newest": "2024-01-14T00:00:00+00:00",
            }
        )

        mock_connection.execute = AsyncMock(side_effect=[count_cursor, date_cursor])

        with patch("services.retention_service.logger"):
            result = await retention_service._preview_log_deletion(
                RetentionType.AUDIT_LOGS, "2024-01-15T00:00:00+00:00"
            )

        assert result is not None
        assert result.affected_records == 150
        assert result.oldest_record_date == "2024-01-01T00:00:00+00:00"
        assert result.newest_record_date == "2024-01-14T00:00:00+00:00"
        assert result.estimated_space_freed_mb == 0.15  # 150 * 0.001

    @pytest.mark.asyncio
    async def test_preview_log_deletion_no_records(
        self, retention_service, mock_connection
    ):
        """_preview_log_deletion should return zero preview when no records."""
        count_cursor = AsyncMock()
        count_cursor.fetchone = AsyncMock(return_value={"count": 0})
        mock_connection.execute = AsyncMock(return_value=count_cursor)

        with patch("services.retention_service.logger"):
            result = await retention_service._preview_log_deletion(
                RetentionType.AUDIT_LOGS, "2024-01-15T00:00:00+00:00"
            )

        assert result is not None
        assert result.affected_records == 0
        assert result.oldest_record_date is None
        assert result.newest_record_date is None

    @pytest.mark.asyncio
    async def test_preview_log_deletion_null_count(
        self, retention_service, mock_connection
    ):
        """_preview_log_deletion should handle null count result."""
        count_cursor = AsyncMock()
        count_cursor.fetchone = AsyncMock(return_value=None)
        mock_connection.execute = AsyncMock(return_value=count_cursor)

        with patch("services.retention_service.logger"):
            result = await retention_service._preview_log_deletion(
                RetentionType.AUDIT_LOGS, "2024-01-15T00:00:00+00:00"
            )

        assert result is not None
        assert result.affected_records == 0

    @pytest.mark.asyncio
    async def test_preview_log_deletion_null_date_result(
        self, retention_service, mock_connection
    ):
        """_preview_log_deletion should handle null date result."""
        count_cursor = AsyncMock()
        count_cursor.fetchone = AsyncMock(return_value={"count": 50})

        date_cursor = AsyncMock()
        date_cursor.fetchone = AsyncMock(return_value=None)

        mock_connection.execute = AsyncMock(side_effect=[count_cursor, date_cursor])

        with patch("services.retention_service.logger"):
            result = await retention_service._preview_log_deletion(
                RetentionType.AUDIT_LOGS, "2024-01-15T00:00:00+00:00"
            )

        assert result is not None
        assert result.affected_records == 50
        assert result.oldest_record_date is None
        assert result.newest_record_date is None

    @pytest.mark.asyncio
    async def test_preview_log_deletion_handles_exception(self, mock_auth_service):
        """_preview_log_deletion should handle database exceptions."""
        # Create a fresh service with error-raising connection
        mock_db_svc = MagicMock()
        mock_error_conn = AsyncMock()
        mock_error_conn.execute = AsyncMock(side_effect=Exception("DB error"))

        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__.return_value = mock_error_conn
        mock_context_manager.__aexit__.return_value = None
        mock_db_svc.get_connection = MagicMock(return_value=mock_context_manager)

        with patch("services.retention_service.logger") as mock_logger:
            service = RetentionService(mock_db_svc, mock_auth_service)
            result = await service._preview_log_deletion(
                RetentionType.AUDIT_LOGS, "2024-01-15T00:00:00+00:00"
            )

        assert result is None
        mock_logger.error.assert_called()


class TestPerformSecureDeletion:
    """Tests for _perform_secure_deletion method."""

    @pytest.mark.asyncio
    async def test_perform_secure_deletion_audit_logs(self, retention_service):
        """_perform_secure_deletion should delete audit logs."""
        with (
            patch("services.retention_service.logger"),
            patch.object(
                retention_service,
                "_delete_logs_batch",
                new_callable=AsyncMock,
                return_value=(500, 0.5),
            ),
        ):
            deleted, space = await retention_service._perform_secure_deletion(
                RetentionType.AUDIT_LOGS, "2024-01-15T00:00:00+00:00", 1000
            )

        assert deleted == 500
        assert space == 0.5

    @pytest.mark.asyncio
    async def test_perform_secure_deletion_access_logs(self, retention_service):
        """_perform_secure_deletion should delete access logs."""
        with (
            patch("services.retention_service.logger"),
            patch.object(
                retention_service,
                "_delete_logs_batch",
                new_callable=AsyncMock,
                return_value=(300, 0.3),
            ),
        ):
            deleted, space = await retention_service._perform_secure_deletion(
                RetentionType.ACCESS_LOGS, "2024-01-15T00:00:00+00:00", 1000
            )

        assert deleted == 300
        assert space == 0.3

    @pytest.mark.asyncio
    async def test_perform_secure_deletion_application_logs(self, retention_service):
        """_perform_secure_deletion should delete application logs."""
        with (
            patch("services.retention_service.logger"),
            patch.object(
                retention_service,
                "_delete_logs_batch",
                new_callable=AsyncMock,
                return_value=(200, 0.2),
            ),
        ):
            deleted, space = await retention_service._perform_secure_deletion(
                RetentionType.APPLICATION_LOGS, "2024-01-15T00:00:00+00:00", 1000
            )

        assert deleted == 200

    @pytest.mark.asyncio
    async def test_perform_secure_deletion_server_logs(self, retention_service):
        """_perform_secure_deletion should delete server logs."""
        with (
            patch("services.retention_service.logger"),
            patch.object(
                retention_service,
                "_delete_logs_batch",
                new_callable=AsyncMock,
                return_value=(1000, 1.0),
            ),
        ):
            deleted, space = await retention_service._perform_secure_deletion(
                RetentionType.SERVER_LOGS, "2024-01-15T00:00:00+00:00", 1000
            )

        assert deleted == 1000
        assert space == 1.0

    @pytest.mark.asyncio
    async def test_perform_secure_deletion_unsupported_type(self, retention_service):
        """_perform_secure_deletion should return zero for unsupported types."""
        with patch("services.retention_service.logger"):
            deleted, space = await retention_service._perform_secure_deletion(
                RetentionType.METRICS, "2024-01-15T00:00:00+00:00", 1000
            )

        assert deleted == 0
        assert space == 0.0

    @pytest.mark.asyncio
    async def test_perform_secure_deletion_handles_exception(self, retention_service):
        """_perform_secure_deletion should propagate exceptions."""
        with (
            patch("services.retention_service.logger") as mock_logger,
            patch.object(
                retention_service,
                "_delete_logs_batch",
                new_callable=AsyncMock,
                side_effect=Exception("Delete error"),
            ),
            pytest.raises(Exception) as exc_info,
        ):
            await retention_service._perform_secure_deletion(
                RetentionType.AUDIT_LOGS, "2024-01-15T00:00:00+00:00", 1000
            )

        assert "Delete error" in str(exc_info.value)
        mock_logger.error.assert_called()


class TestDeleteLogsBatch:
    """Tests for _delete_logs_batch method."""

    @pytest.mark.asyncio
    async def test_delete_logs_batch_single_batch(
        self, retention_service, mock_connection
    ):
        """_delete_logs_batch should delete in single batch."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 500  # Less than batch size
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        with patch("services.retention_service.logger"):
            deleted, space = await retention_service._delete_logs_batch(
                "2024-01-15T00:00:00+00:00", 1000
            )

        assert deleted == 500
        assert space == 0.5  # 500 * 0.001
        mock_connection.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_logs_batch_multiple_batches(
        self, retention_service, mock_connection
    ):
        """_delete_logs_batch should delete in multiple batches."""
        mock_cursor = AsyncMock()
        # First batch full, second batch partial
        mock_cursor.rowcount = 1000

        call_count = 0

        async def execute_side_effect(*args, **kwargs):
            nonlocal call_count
            # Skip the BEGIN IMMEDIATE call
            if "BEGIN" in str(args[0]) if args else False:
                return mock_cursor
            call_count += 1
            if call_count <= 2:
                mock_cursor.rowcount = 1000
            else:
                mock_cursor.rowcount = 500  # Last batch
            return mock_cursor

        mock_connection.execute = AsyncMock(side_effect=execute_side_effect)

        with patch("services.retention_service.logger"):
            deleted, space = await retention_service._delete_logs_batch(
                "2024-01-15T00:00:00+00:00", 1000
            )

        assert deleted == 2500  # 1000 + 1000 + 500
        mock_connection.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_logs_batch_no_records(
        self, retention_service, mock_connection
    ):
        """_delete_logs_batch should handle no records to delete."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 0
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        with patch("services.retention_service.logger"):
            deleted, space = await retention_service._delete_logs_batch(
                "2024-01-15T00:00:00+00:00", 1000
            )

        assert deleted == 0
        assert space == 0.0
        mock_connection.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_logs_batch_rollback_on_error(self, mock_auth_service):
        """_delete_logs_batch should rollback on error."""
        # Create a fresh service with error-raising connection
        mock_db_svc = MagicMock()
        mock_error_conn = AsyncMock()
        call_count = 0

        async def execute_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:  # BEGIN IMMEDIATE
                return AsyncMock()
            raise Exception("Delete failed")

        mock_error_conn.execute = AsyncMock(side_effect=execute_side_effect)
        mock_error_conn.rollback = AsyncMock()
        mock_error_conn.commit = AsyncMock()

        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__.return_value = mock_error_conn
        mock_context_manager.__aexit__.return_value = None
        mock_db_svc.get_connection = MagicMock(return_value=mock_context_manager)

        with (
            patch("services.retention_service.logger") as mock_logger,
            pytest.raises(Exception) as exc_info,
        ):
            service = RetentionService(mock_db_svc, mock_auth_service)
            await service._delete_logs_batch("2024-01-15T00:00:00+00:00", 1000)

        assert "Delete failed" in str(exc_info.value)
        mock_error_conn.rollback.assert_called_once()
        mock_logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_delete_logs_batch_connection_error(self, mock_auth_service):
        """_delete_logs_batch should handle connection errors."""
        # Create a fresh service with error-raising connection
        mock_db_svc = MagicMock()
        mock_error_conn = AsyncMock()
        mock_error_conn.execute = AsyncMock(side_effect=Exception("Connection lost"))
        mock_error_conn.rollback = AsyncMock()

        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__.return_value = mock_error_conn
        mock_context_manager.__aexit__.return_value = None
        mock_db_svc.get_connection = MagicMock(return_value=mock_context_manager)

        with (
            patch("services.retention_service.logger") as mock_logger,
            pytest.raises(Exception) as exc_info,
        ):
            service = RetentionService(mock_db_svc, mock_auth_service)
            await service._delete_logs_batch("2024-01-15T00:00:00+00:00", 1000)

        assert "Connection lost" in str(exc_info.value)
        mock_logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_delete_logs_batch_space_calculation(
        self, retention_service, mock_connection
    ):
        """_delete_logs_batch should calculate space freed correctly."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 1234
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        with patch("services.retention_service.logger"):
            deleted, space = await retention_service._delete_logs_batch(
                "2024-01-15T00:00:00+00:00", 2000
            )

        assert deleted == 1234
        assert space == 1.23  # Rounded to 2 decimal places
