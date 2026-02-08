"""
Unit tests for services/retention_service.py - Cleanup operations.

Tests preview_cleanup, perform_cleanup, cutoff date calculation, and deletion.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.retention import (
    CleanupPreview,
    CleanupRequest,
    RetentionOperation,
    RetentionSettings,
    RetentionType,
    SecurityValidationResult,
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


@pytest.fixture
def valid_security_result():
    """Create valid security validation result."""
    return SecurityValidationResult(
        is_valid=True,
        is_admin=True,
        session_valid=True,
        user_id="admin-123",
    )


@pytest.fixture
def invalid_security_result():
    """Create invalid security validation result."""
    return SecurityValidationResult(
        is_valid=False,
        error_message="Invalid token",
    )


@pytest.fixture
def retention_settings():
    """Create retention settings for testing."""
    return RetentionSettings(
        log_retention=30,
        data_retention=90,
    )


@pytest.fixture
def cleanup_preview():
    """Create cleanup preview for testing."""
    return CleanupPreview(
        retention_type=RetentionType.AUDIT_LOGS,
        affected_records=100,
        oldest_record_date="2024-01-01T00:00:00+00:00",
        newest_record_date="2024-01-15T00:00:00+00:00",
        estimated_space_freed_mb=0.1,
        cutoff_date="2024-01-15T00:00:00+00:00",
    )


class TestPreviewCleanup:
    """Tests for preview_cleanup method."""

    @pytest.mark.asyncio
    async def test_preview_cleanup_security_failure(
        self, retention_service, invalid_security_result
    ):
        """preview_cleanup should return None on security failure."""
        request = CleanupRequest(
            retention_type=RetentionType.AUDIT_LOGS,
            dry_run=True,
            admin_user_id="admin-123",
            session_token="invalid-token",
        )

        with (
            patch("services.retention_service.logger"),
            patch.object(
                retention_service,
                "_validate_security",
                new_callable=AsyncMock,
                return_value=invalid_security_result,
            ),
        ):
            result = await retention_service.preview_cleanup(request)

        assert result is None

    @pytest.mark.asyncio
    async def test_preview_cleanup_no_settings(
        self, retention_service, valid_security_result
    ):
        """preview_cleanup should return None when settings not found."""
        request = CleanupRequest(
            retention_type=RetentionType.AUDIT_LOGS,
            dry_run=True,
            admin_user_id="admin-123",
            session_token="valid-token",
        )

        with (
            patch("services.retention_service.logger"),
            patch.object(
                retention_service,
                "_validate_security",
                new_callable=AsyncMock,
                return_value=valid_security_result,
            ),
            patch.object(
                retention_service,
                "get_retention_settings",
                new_callable=AsyncMock,
                return_value=None,
            ),
        ):
            result = await retention_service.preview_cleanup(request)

        assert result is None

    @pytest.mark.asyncio
    async def test_preview_cleanup_success(
        self,
        retention_service,
        valid_security_result,
        retention_settings,
        cleanup_preview,
    ):
        """preview_cleanup should return preview on success."""
        request = CleanupRequest(
            retention_type=RetentionType.AUDIT_LOGS,
            dry_run=True,
            admin_user_id="admin-123",
            session_token="valid-token",
        )

        with (
            patch("services.retention_service.logger"),
            patch.object(
                retention_service,
                "_validate_security",
                new_callable=AsyncMock,
                return_value=valid_security_result,
            ),
            patch.object(
                retention_service,
                "get_retention_settings",
                new_callable=AsyncMock,
                return_value=retention_settings,
            ),
            patch.object(
                retention_service,
                "_calculate_cutoff_date",
                return_value="2024-01-15T00:00:00+00:00",
            ),
            patch.object(
                retention_service,
                "_preview_records_for_deletion",
                new_callable=AsyncMock,
                return_value=cleanup_preview,
            ),
            patch.object(
                retention_service, "_log_retention_operation", new_callable=AsyncMock
            ),
        ):
            result = await retention_service.preview_cleanup(request)

        assert result is not None
        assert result.affected_records == 100

    @pytest.mark.asyncio
    async def test_preview_cleanup_invalid_cutoff(
        self, retention_service, valid_security_result, retention_settings
    ):
        """preview_cleanup should return None for invalid cutoff date."""
        request = CleanupRequest(
            retention_type=RetentionType.AUDIT_LOGS,
            dry_run=True,
            admin_user_id="admin-123",
            session_token="valid-token",
        )

        with (
            patch("services.retention_service.logger"),
            patch.object(
                retention_service,
                "_validate_security",
                new_callable=AsyncMock,
                return_value=valid_security_result,
            ),
            patch.object(
                retention_service,
                "get_retention_settings",
                new_callable=AsyncMock,
                return_value=retention_settings,
            ),
            patch.object(
                retention_service, "_calculate_cutoff_date", return_value=None
            ),
        ):
            result = await retention_service.preview_cleanup(request)

        assert result is None

    @pytest.mark.asyncio
    async def test_preview_cleanup_handles_exception(
        self, retention_service, valid_security_result
    ):
        """preview_cleanup should handle exceptions gracefully."""
        request = CleanupRequest(
            retention_type=RetentionType.AUDIT_LOGS,
            dry_run=True,
            admin_user_id="admin-123",
            session_token="valid-token",
        )

        with (
            patch("services.retention_service.logger") as mock_logger,
            patch.object(
                retention_service,
                "_validate_security",
                new_callable=AsyncMock,
                side_effect=Exception("Validation error"),
            ),
            patch.object(
                retention_service, "_log_retention_operation", new_callable=AsyncMock
            ),
        ):
            result = await retention_service.preview_cleanup(request)

        assert result is None
        mock_logger.error.assert_called()


class TestPerformCleanup:
    """Tests for perform_cleanup method."""

    @pytest.mark.asyncio
    async def test_perform_cleanup_security_failure(
        self, retention_service, invalid_security_result
    ):
        """perform_cleanup should return error result on security failure."""
        request = CleanupRequest(
            retention_type=RetentionType.AUDIT_LOGS,
            dry_run=False,
            force_cleanup=True,
            admin_user_id="admin-123",
            session_token="invalid-token",
        )

        with (
            patch("services.retention_service.logger"),
            patch.object(
                retention_service,
                "_validate_security",
                new_callable=AsyncMock,
                return_value=invalid_security_result,
            ),
        ):
            result = await retention_service.perform_cleanup(request)

        assert result is not None
        assert result.success is False
        assert "Invalid token" in result.error_message

    @pytest.mark.asyncio
    async def test_perform_cleanup_requires_dry_run_first(
        self, retention_service, valid_security_result
    ):
        """perform_cleanup should require dry-run before actual cleanup."""
        request = CleanupRequest(
            retention_type=RetentionType.AUDIT_LOGS,
            dry_run=False,
            force_cleanup=False,  # Not forced
            admin_user_id="admin-123",
            session_token="valid-token",
        )

        with (
            patch("services.retention_service.logger"),
            patch.object(
                retention_service,
                "_validate_security",
                new_callable=AsyncMock,
                return_value=valid_security_result,
            ),
        ):
            result = await retention_service.perform_cleanup(request)

        assert result is not None
        assert result.success is False
        assert "Dry-run must be performed" in result.error_message

    @pytest.mark.asyncio
    async def test_perform_cleanup_dry_run_success(
        self,
        retention_service,
        valid_security_result,
        retention_settings,
        cleanup_preview,
    ):
        """perform_cleanup should handle dry-run successfully."""
        request = CleanupRequest(
            retention_type=RetentionType.AUDIT_LOGS,
            dry_run=True,
            admin_user_id="admin-123",
            session_token="valid-token",
        )

        with (
            patch("services.retention_service.logger"),
            patch.object(
                retention_service,
                "_validate_security",
                new_callable=AsyncMock,
                return_value=valid_security_result,
            ),
            patch.object(
                retention_service,
                "get_retention_settings",
                new_callable=AsyncMock,
                return_value=retention_settings,
            ),
            patch.object(
                retention_service,
                "_calculate_cutoff_date",
                return_value="2024-01-15T00:00:00+00:00",
            ),
            patch.object(
                retention_service,
                "_preview_records_for_deletion",
                new_callable=AsyncMock,
                return_value=cleanup_preview,
            ),
            patch.object(
                retention_service, "_log_retention_operation", new_callable=AsyncMock
            ),
        ):
            result = await retention_service.perform_cleanup(request)

        assert result is not None
        assert result.success is True
        assert result.operation == RetentionOperation.DRY_RUN
        assert result.records_affected == 100
        assert result.preview_data is not None

    @pytest.mark.asyncio
    async def test_perform_cleanup_actual_cleanup_success(
        self, retention_service, valid_security_result, retention_settings
    ):
        """perform_cleanup should handle actual cleanup successfully."""
        request = CleanupRequest(
            retention_type=RetentionType.AUDIT_LOGS,
            dry_run=False,
            force_cleanup=True,
            admin_user_id="admin-123",
            session_token="valid-token",
        )

        with (
            patch("services.retention_service.logger"),
            patch.object(
                retention_service,
                "_validate_security",
                new_callable=AsyncMock,
                return_value=valid_security_result,
            ),
            patch.object(
                retention_service,
                "get_retention_settings",
                new_callable=AsyncMock,
                return_value=retention_settings,
            ),
            patch.object(
                retention_service,
                "_calculate_cutoff_date",
                return_value="2024-01-15T00:00:00+00:00",
            ),
            patch.object(
                retention_service,
                "_perform_secure_deletion",
                new_callable=AsyncMock,
                return_value=(500, 0.5),
            ),
            patch.object(
                retention_service, "_log_retention_operation", new_callable=AsyncMock
            ),
        ):
            result = await retention_service.perform_cleanup(request)

        assert result is not None
        assert result.success is True
        assert result.operation == RetentionOperation.CLEANUP
        assert result.records_affected == 500
        assert result.space_freed_mb == 0.5

    @pytest.mark.asyncio
    async def test_perform_cleanup_no_settings(
        self, retention_service, valid_security_result
    ):
        """perform_cleanup should return error when settings not found."""
        request = CleanupRequest(
            retention_type=RetentionType.AUDIT_LOGS,
            dry_run=False,
            force_cleanup=True,
            admin_user_id="admin-123",
            session_token="valid-token",
        )

        with (
            patch("services.retention_service.logger"),
            patch.object(
                retention_service,
                "_validate_security",
                new_callable=AsyncMock,
                return_value=valid_security_result,
            ),
            patch.object(
                retention_service,
                "get_retention_settings",
                new_callable=AsyncMock,
                return_value=None,
            ),
        ):
            result = await retention_service.perform_cleanup(request)

        assert result is not None
        assert result.success is False
        assert "No retention settings found" in result.error_message

    @pytest.mark.asyncio
    async def test_perform_cleanup_invalid_retention_type(
        self, retention_service, valid_security_result, retention_settings
    ):
        """perform_cleanup should return error for invalid retention type."""
        request = CleanupRequest(
            retention_type=RetentionType.AUDIT_LOGS,
            dry_run=False,
            force_cleanup=True,
            admin_user_id="admin-123",
            session_token="valid-token",
        )

        with (
            patch("services.retention_service.logger"),
            patch.object(
                retention_service,
                "_validate_security",
                new_callable=AsyncMock,
                return_value=valid_security_result,
            ),
            patch.object(
                retention_service,
                "get_retention_settings",
                new_callable=AsyncMock,
                return_value=retention_settings,
            ),
            patch.object(
                retention_service, "_calculate_cutoff_date", return_value=None
            ),
        ):
            result = await retention_service.perform_cleanup(request)

        assert result is not None
        assert result.success is False
        assert "Invalid retention type" in result.error_message

    @pytest.mark.asyncio
    async def test_perform_cleanup_handles_exception(
        self, retention_service, valid_security_result
    ):
        """perform_cleanup should handle exceptions gracefully."""
        request = CleanupRequest(
            retention_type=RetentionType.AUDIT_LOGS,
            dry_run=False,
            force_cleanup=True,
            admin_user_id="admin-123",
            session_token="valid-token",
        )

        with (
            patch("services.retention_service.logger") as mock_logger,
            patch.object(
                retention_service,
                "_validate_security",
                new_callable=AsyncMock,
                side_effect=Exception("Unexpected error"),
            ),
            patch.object(
                retention_service, "_log_retention_operation", new_callable=AsyncMock
            ),
        ):
            result = await retention_service.perform_cleanup(request)

        assert result is not None
        assert result.success is False
        assert "Unexpected error" in result.error_message
        mock_logger.error.assert_called()


class TestCalculateCutoffDate:
    """Tests for _calculate_cutoff_date method."""

    def test_calculate_cutoff_date_audit_logs(self, retention_service):
        """_calculate_cutoff_date should calculate for audit logs."""
        settings = RetentionSettings(log_retention=30, data_retention=90)

        with patch("services.retention_service.logger"):
            result = retention_service._calculate_cutoff_date(
                RetentionType.AUDIT_LOGS, settings
            )

        assert result is not None
        # Verify it's approximately 30 days ago
        cutoff = datetime.fromisoformat(result)
        expected = datetime.now(UTC) - timedelta(days=30)
        assert abs((cutoff - expected).total_seconds()) < 60  # Within 1 minute

    def test_calculate_cutoff_date_access_logs(self, retention_service):
        """_calculate_cutoff_date should calculate for access logs."""
        settings = RetentionSettings(log_retention=45, data_retention=90)

        with patch("services.retention_service.logger"):
            result = retention_service._calculate_cutoff_date(
                RetentionType.ACCESS_LOGS, settings
            )

        assert result is not None
        cutoff = datetime.fromisoformat(result)
        expected = datetime.now(UTC) - timedelta(days=45)
        assert abs((cutoff - expected).total_seconds()) < 60

    def test_calculate_cutoff_date_application_logs(self, retention_service):
        """_calculate_cutoff_date should calculate for application logs."""
        settings = RetentionSettings(log_retention=14, data_retention=90)

        with patch("services.retention_service.logger"):
            result = retention_service._calculate_cutoff_date(
                RetentionType.APPLICATION_LOGS, settings
            )

        assert result is not None

    def test_calculate_cutoff_date_server_logs(self, retention_service):
        """_calculate_cutoff_date should calculate for server logs."""
        settings = RetentionSettings(log_retention=60, data_retention=90)

        with patch("services.retention_service.logger"):
            result = retention_service._calculate_cutoff_date(
                RetentionType.SERVER_LOGS, settings
            )

        assert result is not None

    def test_calculate_cutoff_date_metrics(self, retention_service):
        """_calculate_cutoff_date should calculate for metrics."""
        settings = RetentionSettings(log_retention=30, data_retention=120)

        with patch("services.retention_service.logger"):
            result = retention_service._calculate_cutoff_date(
                RetentionType.METRICS, settings
            )

        assert result is not None
        cutoff = datetime.fromisoformat(result)
        expected = datetime.now(UTC) - timedelta(days=120)
        assert abs((cutoff - expected).total_seconds()) < 60

    def test_calculate_cutoff_date_notifications(self, retention_service):
        """_calculate_cutoff_date should calculate for notifications."""
        settings = RetentionSettings(log_retention=30, data_retention=60)

        with patch("services.retention_service.logger"):
            result = retention_service._calculate_cutoff_date(
                RetentionType.NOTIFICATIONS, settings
            )

        assert result is not None

    def test_calculate_cutoff_date_sessions(self, retention_service):
        """_calculate_cutoff_date should calculate for sessions."""
        settings = RetentionSettings(log_retention=30, data_retention=7)

        with patch("services.retention_service.logger"):
            result = retention_service._calculate_cutoff_date(
                RetentionType.SESSIONS, settings
            )

        assert result is not None
        cutoff = datetime.fromisoformat(result)
        expected = datetime.now(UTC) - timedelta(days=7)
        assert abs((cutoff - expected).total_seconds()) < 60

    def test_calculate_cutoff_date_unknown_type(self, retention_service):
        """_calculate_cutoff_date should return None for unknown retention type."""
        settings = RetentionSettings(log_retention=30, data_retention=90)

        # Create a mock object that looks like a RetentionType but isn't recognized
        mock_unknown_type = MagicMock()
        mock_unknown_type.value = "unknown_type"

        with patch("services.retention_service.logger"):
            result = retention_service._calculate_cutoff_date(
                mock_unknown_type, settings
            )

        assert result is None

    def test_calculate_cutoff_date_exception(self, retention_service):
        """_calculate_cutoff_date should return None and log error on exception."""
        # Create settings that raise an exception when accessed
        mock_settings = MagicMock()
        mock_settings.log_retention = property(
            lambda self: (_ for _ in ()).throw(ValueError("Invalid settings"))
        )
        type(mock_settings).log_retention = property(lambda self: self._raise_error())

        # Simpler approach: make log_retention a property that raises
        class BrokenSettings:
            @property
            def log_retention(self):
                raise ValueError("Invalid settings")

            @property
            def data_retention(self):
                return 90

        broken_settings = BrokenSettings()

        with patch("services.retention_service.logger") as mock_logger:
            result = retention_service._calculate_cutoff_date(
                RetentionType.AUDIT_LOGS, broken_settings
            )

        assert result is None
        mock_logger.error.assert_called()


class TestCreateErrorResult:
    """Tests for _create_error_result method."""

    def test_create_error_result_dry_run(self, retention_service):
        """_create_error_result should create dry-run error result."""
        request = CleanupRequest(
            retention_type=RetentionType.AUDIT_LOGS,
            dry_run=True,
            admin_user_id="admin-123",
            session_token="valid-token",
        )
        start_time = datetime.now(UTC)

        result = retention_service._create_error_result(
            "op-123", request, start_time, "admin-123", "Test error"
        )

        assert result.operation_id == "op-123"
        assert result.success is False
        assert result.operation == RetentionOperation.DRY_RUN
        assert result.error_message == "Test error"
        assert result.admin_user_id == "admin-123"

    def test_create_error_result_cleanup(self, retention_service):
        """_create_error_result should create cleanup error result."""
        request = CleanupRequest(
            retention_type=RetentionType.METRICS,
            dry_run=False,
            force_cleanup=True,
            admin_user_id="admin-123",
            session_token="valid-token",
        )
        start_time = datetime.now(UTC)

        result = retention_service._create_error_result(
            "op-456", request, start_time, "admin-123", "Cleanup failed"
        )

        assert result.operation_id == "op-456"
        assert result.success is False
        assert result.operation == RetentionOperation.CLEANUP
        assert result.retention_type == RetentionType.METRICS
