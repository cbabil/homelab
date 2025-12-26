"""
Unit tests for data retention service.

Tests comprehensive business logic, security validation, transaction safety,
and error handling for all retention service operations with focus on critical security controls.
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from services.retention_service import RetentionService
from models.retention import (
    DataRetentionSettings, CleanupRequest, CleanupResult, CleanupPreview,
    RetentionType, RetentionOperation, SecurityValidationResult
)
from models.auth import User, UserRole
from models.log import LogEntry


class TestRetentionService:
    """Test retention service initialization and dependencies."""

    def test_service_initialization(self):
        """Test service initializes with correct dependencies."""
        service = RetentionService()

        assert service.db_service is not None
        assert service.auth_service is not None
        assert service.max_batch_size == 10000
        assert service.min_batch_size == 100


class TestSecurityValidation:
    """Test comprehensive security validation for retention operations."""

    @pytest.fixture
    def service(self):
        """Create retention service with mocked dependencies."""
        service = RetentionService()
        service.db_service = AsyncMock()

        # Create a mixed mock for auth_service (sync and async methods)
        auth_mock = AsyncMock()
        auth_mock._validate_jwt_token = MagicMock()  # Sync method
        service.auth_service = auth_mock
        return service

    @pytest.fixture
    def valid_admin_user(self):
        """Create valid admin user for tests."""
        return User(
            id="admin-123",
            username="admin",
            email="admin@example.com",
            role=UserRole.ADMIN,
            last_login="2023-09-14T10:30:00.000Z",
            is_active=True,
            preferences={}
        )

    @pytest.fixture
    def valid_regular_user(self):
        """Create valid regular user for tests."""
        return User(
            id="user-456",
            username="user",
            email="user@example.com",
            role=UserRole.USER,
            last_login="2023-09-14T09:30:00.000Z",
            is_active=True,
            preferences={}
        )

    @pytest.fixture
    def cleanup_request(self):
        """Create valid cleanup request."""
        return CleanupRequest(
            retention_type=RetentionType.LOGS,
            admin_user_id="admin-123",
            session_token="valid-token",
            dry_run=True
        )

    async def test_valid_admin_security_validation(self, service, valid_admin_user, cleanup_request):
        """Test successful security validation for admin user."""
        # Mock token validation
        service.auth_service._validate_jwt_token.return_value = {"username": "admin"}
        service.auth_service.get_user_by_username = AsyncMock(return_value=valid_admin_user)

        result = await service._validate_security(cleanup_request)

        assert result.is_valid is True
        assert result.is_admin is True
        assert result.session_valid is True
        assert result.user_id == "admin-123"
        assert result.error_message is None

    async def test_invalid_token_security_validation(self, service, cleanup_request):
        """Test security validation with invalid token."""
        service.auth_service._validate_jwt_token.return_value = None

        result = await service._validate_security(cleanup_request)

        assert result.is_valid is False
        assert result.error_message == "Invalid or expired session token"

    async def test_missing_username_in_token(self, service, cleanup_request):
        """Test security validation with malformed token."""
        service.auth_service._validate_jwt_token.return_value = {"invalid": "payload"}

        result = await service._validate_security(cleanup_request)

        assert result.is_valid is False
        assert result.error_message == "Invalid token payload"

    async def test_user_not_found_validation(self, service, cleanup_request):
        """Test security validation when user doesn't exist."""
        service.auth_service._validate_jwt_token.return_value = {"username": "nonexistent"}
        service.auth_service.get_user_by_username = AsyncMock(return_value=None)

        result = await service._validate_security(cleanup_request)

        assert result.is_valid is False
        assert result.error_message == "User not found or inactive"

    async def test_inactive_user_validation(self, service, cleanup_request):
        """Test security validation for inactive user."""
        inactive_user = User(
            id="admin-123",
            username="admin",
            email="admin@example.com",
            role=UserRole.ADMIN,
            last_login="2023-09-14T08:30:00.000Z",
            is_active=False,
            preferences={}
        )

        service.auth_service._validate_jwt_token.return_value = {"username": "admin"}
        service.auth_service.get_user_by_username = AsyncMock(return_value=inactive_user)

        result = await service._validate_security(cleanup_request)

        assert result.is_valid is False
        assert result.error_message == "User not found or inactive"

    async def test_non_admin_user_validation(self, service, valid_regular_user, cleanup_request):
        """Test security validation for non-admin user."""
        service.auth_service._validate_jwt_token.return_value = {"username": "user"}
        service.auth_service.get_user_by_username = AsyncMock(return_value=valid_regular_user)

        result = await service._validate_security(cleanup_request)

        assert result.is_valid is False
        assert result.is_admin is False
        assert result.session_valid is True
        assert result.user_id == "user-456"
        assert "Admin privileges required" in result.error_message

    async def test_additional_verification_for_force_cleanup(self, service, valid_admin_user):
        """Test additional verification requirement for force cleanup."""
        force_cleanup_request = CleanupRequest(
            retention_type=RetentionType.LOGS,
            admin_user_id="admin-123",
            session_token="valid-token",
            dry_run=False,
            force_cleanup=True
        )

        service.auth_service._validate_jwt_token.return_value = {"username": "admin"}
        service.auth_service.get_user_by_username = AsyncMock(return_value=valid_admin_user)

        result = await service._validate_security(force_cleanup_request)

        assert result.is_valid is True
        assert result.requires_additional_verification is True

    async def test_security_validation_exception_handling(self, service, cleanup_request):
        """Test security validation handles exceptions gracefully."""
        service.auth_service._validate_jwt_token.side_effect = Exception("Database error")

        result = await service._validate_security(cleanup_request)

        assert result.is_valid is False
        assert "Security validation error" in result.error_message


class TestRetentionSettingsManagement:
    """Test retention settings CRUD operations with security controls."""

    @pytest.fixture
    def service(self):
        """Create retention service with mocked dependencies."""
        service = RetentionService()
        service.db_service = AsyncMock()
        service.auth_service = AsyncMock()
        return service

    @pytest.fixture
    def admin_user_with_settings(self):
        """Create admin user with existing retention settings."""
        return User(
            id="admin-123",
            username="admin",
            email="admin@example.com",
            role=UserRole.ADMIN,
            last_login="2023-09-14T10:30:00.000Z",
            is_active=True,
            preferences={
                'retention_settings': {
                    'log_retention_days': 60,
                    'user_data_retention_days': 730,
                    'auto_cleanup_enabled': True
                }
            }
        )

    async def test_get_retention_settings_success(self, service, admin_user_with_settings):
        """Test successful retrieval of retention settings."""
        service.db_service.get_user_by_id.return_value = admin_user_with_settings

        settings = await service.get_retention_settings("admin-123")

        assert settings is not None
        assert settings.log_retention_days == 60
        assert settings.user_data_retention_days == 730
        assert settings.auto_cleanup_enabled is True

    async def test_get_retention_settings_no_user(self, service):
        """Test retention settings retrieval when user doesn't exist."""
        service.db_service.get_user_by_id.return_value = None

        settings = await service.get_retention_settings("nonexistent")

        assert settings is not None
        assert settings.log_retention_days == 30  # Default values

    async def test_get_retention_settings_no_preferences(self, service):
        """Test retention settings retrieval when user has no preferences."""
        user = User(
            id="admin-123",
            username="admin",
            email="admin@example.com",
            role=UserRole.ADMIN,
            last_login="2023-09-14T10:30:00.000Z",
            is_active=True,
            preferences=None
        )
        service.db_service.get_user_by_id.return_value = user

        settings = await service.get_retention_settings("admin-123")

        assert settings is not None
        assert settings.log_retention_days == 30  # Default values

    async def test_get_retention_settings_empty_preferences(self, service):
        """Test retention settings retrieval with empty retention settings."""
        user = User(
            id="admin-123",
            username="admin",
            email="admin@example.com",
            role=UserRole.ADMIN,
            last_login="2023-09-14T10:30:00.000Z",
            is_active=True,
            preferences={'other_settings': 'value'}
        )
        service.db_service.get_user_by_id.return_value = user

        settings = await service.get_retention_settings("admin-123")

        assert settings is not None
        assert settings.log_retention_days == 30  # Default values

    async def test_update_retention_settings_success(self, service):
        """Test successful retention settings update."""
        admin_user = User(
            id="admin-123",
            username="admin",
            email="admin@example.com",
            role=UserRole.ADMIN,
            last_login="2023-09-14T10:30:00.000Z",
            is_active=True,
            preferences={'existing': 'data'}
        )

        service.db_service.get_user_by_id.return_value = admin_user

        # Mock database connection
        mock_conn = AsyncMock()
        service.db_service.get_connection.return_value.__aenter__.return_value = mock_conn

        new_settings = DataRetentionSettings(
            log_retention_days=90,
            auto_cleanup_enabled=True
        )

        with patch('services.retention_service.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value.isoformat.return_value = "2023-09-14T10:30:00.000Z"

            result = await service.update_retention_settings("admin-123", new_settings)

        assert result is True
        mock_conn.execute.assert_called()
        mock_conn.commit.assert_called_once()

    async def test_update_retention_settings_non_admin_rejected(self, service):
        """Test retention settings update rejected for non-admin user."""
        regular_user = User(
            id="user-456",
            username="user",
            email="user@example.com",
            role=UserRole.USER,
            last_login="2023-09-14T09:30:00.000Z",
            is_active=True,
            preferences={}
        )

        service.db_service.get_user_by_id.return_value = regular_user

        new_settings = DataRetentionSettings(log_retention_days=90)
        result = await service.update_retention_settings("user-456", new_settings)

        assert result is False

    async def test_update_retention_settings_user_not_found(self, service):
        """Test retention settings update when user doesn't exist."""
        service.db_service.get_user_by_id.return_value = None

        new_settings = DataRetentionSettings(log_retention_days=90)
        result = await service.update_retention_settings("nonexistent", new_settings)

        assert result is False

    async def test_update_retention_settings_database_error(self, service):
        """Test retention settings update handles database errors."""
        admin_user = User(
            id="admin-123",
            username="admin",
            email="admin@example.com",
            role=UserRole.ADMIN,
            last_login="2023-09-14T10:30:00.000Z",
            is_active=True,
            preferences={}
        )

        service.db_service.get_user_by_id.return_value = admin_user
        service.db_service.get_connection.side_effect = Exception("Database error")

        new_settings = DataRetentionSettings(log_retention_days=90)
        result = await service.update_retention_settings("admin-123", new_settings)

        assert result is False


class TestCleanupPreview:
    """Test cleanup preview operations (dry-run functionality)."""

    @pytest.fixture
    def service(self):
        """Create retention service with mocked dependencies."""
        service = RetentionService()
        service.db_service = AsyncMock()
        service.auth_service = AsyncMock()
        return service

    @pytest.fixture
    def valid_security_result(self):
        """Create valid security validation result."""
        return SecurityValidationResult(
            is_valid=True,
            is_admin=True,
            session_valid=True,
            user_id="admin-123"
        )

    @pytest.fixture
    def cleanup_request(self):
        """Create cleanup request for preview."""
        return CleanupRequest(
            retention_type=RetentionType.LOGS,
            admin_user_id="admin-123",
            session_token="valid-token",
            dry_run=True
        )

    async def test_preview_cleanup_success(self, service, cleanup_request, valid_security_result):
        """Test successful cleanup preview operation."""
        # Mock security validation
        with patch.object(service, '_validate_security', return_value=valid_security_result):
            # Mock settings retrieval
            settings = DataRetentionSettings(log_retention_days=30)
            with patch.object(service, 'get_retention_settings', return_value=settings):
                # Mock cutoff date calculation
                cutoff_date = "2023-08-15T00:00:00.000Z"
                with patch.object(service, '_calculate_cutoff_date', return_value=cutoff_date):
                    # Mock preview records
                    preview = CleanupPreview(
                        retention_type=RetentionType.LOGS,
                        affected_records=150,
                        cutoff_date=cutoff_date
                    )
                    with patch.object(service, '_preview_records_for_deletion', return_value=preview):
                        result = await service.preview_cleanup(cleanup_request)

        assert result is not None
        assert result.retention_type == RetentionType.LOGS
        assert result.affected_records == 150

    async def test_preview_cleanup_security_validation_failed(self, service, cleanup_request):
        """Test cleanup preview with failed security validation."""
        invalid_security = SecurityValidationResult(
            is_valid=False,
            error_message="Invalid session token"
        )

        with patch.object(service, '_validate_security', return_value=invalid_security):
            result = await service.preview_cleanup(cleanup_request)

        assert result is None

    async def test_preview_cleanup_no_settings_found(self, service, cleanup_request, valid_security_result):
        """Test cleanup preview when no retention settings found."""
        with patch.object(service, '_validate_security', return_value=valid_security_result):
            with patch.object(service, 'get_retention_settings', return_value=None):
                result = await service.preview_cleanup(cleanup_request)

        assert result is None

    async def test_preview_cleanup_invalid_cutoff_date(self, service, cleanup_request, valid_security_result):
        """Test cleanup preview with invalid cutoff date calculation."""
        with patch.object(service, '_validate_security', return_value=valid_security_result):
            settings = DataRetentionSettings(log_retention_days=30)
            with patch.object(service, 'get_retention_settings', return_value=settings):
                with patch.object(service, '_calculate_cutoff_date', return_value=None):
                    result = await service.preview_cleanup(cleanup_request)

        assert result is None


class TestCleanupExecution:
    """Test actual cleanup execution with transaction safety."""

    @pytest.fixture
    def service(self):
        """Create retention service with mocked dependencies."""
        service = RetentionService()
        service.db_service = AsyncMock()
        service.auth_service = AsyncMock()
        return service

    async def test_cleanup_mandatory_dry_run_check(self, service):
        """Test that actual cleanup requires dry-run to be performed first."""
        cleanup_request = CleanupRequest(
            retention_type=RetentionType.LOGS,
            admin_user_id="admin-123",
            session_token="valid-token",
            dry_run=False,  # Actual cleanup
            force_cleanup=False  # But no force flag
        )

        valid_security = SecurityValidationResult(
            is_valid=True,
            is_admin=True,
            session_valid=True,
            user_id="admin-123"
        )

        with patch.object(service, '_validate_security', return_value=valid_security):
            result = await service.perform_cleanup(cleanup_request)

        assert result is not None
        assert result.success is False
        assert "Dry-run must be performed before actual cleanup" in result.error_message

    async def test_cleanup_with_force_flag_success(self, service):
        """Test successful cleanup with force flag."""
        cleanup_request = CleanupRequest(
            retention_type=RetentionType.LOGS,
            admin_user_id="admin-123",
            session_token="valid-token",
            dry_run=False,
            force_cleanup=True
        )

        valid_security = SecurityValidationResult(
            is_valid=True,
            is_admin=True,
            session_valid=True,
            user_id="admin-123"
        )

        settings = DataRetentionSettings(log_retention_days=30)
        cutoff_date = "2023-08-15T00:00:00.000Z"

        with patch.object(service, '_validate_security', return_value=valid_security):
            with patch.object(service, 'get_retention_settings', return_value=settings):
                with patch.object(service, '_calculate_cutoff_date', return_value=cutoff_date):
                    with patch.object(service, '_perform_secure_deletion', return_value=(100, 10.5)):
                        result = await service.perform_cleanup(cleanup_request)

        assert result is not None
        assert result.success is True
        assert result.records_affected == 100
        assert result.space_freed_mb == 10.5

    async def test_cleanup_dry_run_execution(self, service):
        """Test dry-run cleanup execution returns preview data."""
        cleanup_request = CleanupRequest(
            retention_type=RetentionType.LOGS,
            admin_user_id="admin-123",
            session_token="valid-token",
            dry_run=True
        )

        valid_security = SecurityValidationResult(
            is_valid=True,
            is_admin=True,
            session_valid=True,
            user_id="admin-123"
        )

        settings = DataRetentionSettings(log_retention_days=30)
        cutoff_date = "2023-08-15T00:00:00.000Z"
        preview = CleanupPreview(
            retention_type=RetentionType.LOGS,
            affected_records=75,
            cutoff_date=cutoff_date
        )

        with patch.object(service, '_validate_security', return_value=valid_security):
            with patch.object(service, 'get_retention_settings', return_value=settings):
                with patch.object(service, '_calculate_cutoff_date', return_value=cutoff_date):
                    with patch.object(service, '_preview_records_for_deletion', return_value=preview):
                        result = await service.perform_cleanup(cleanup_request)

        assert result is not None
        assert result.success is True
        assert result.operation == RetentionOperation.DRY_RUN
        assert result.preview_data is not None
        assert result.preview_data.affected_records == 75


class TestCutoffDateCalculation:
    """Test cutoff date calculation logic."""

    def test_calculate_cutoff_date_logs(self):
        """Test cutoff date calculation for logs."""
        service = RetentionService()
        settings = DataRetentionSettings(log_retention_days=30)

        with patch('services.retention_service.datetime') as mock_datetime:
            mock_now = datetime(2023, 9, 14, 10, 30, 0)
            mock_datetime.utcnow.return_value = mock_now

            cutoff_date = service._calculate_cutoff_date(RetentionType.LOGS, settings)

        assert cutoff_date is not None
        # Should be 30 days ago from mock_now
        expected_cutoff = mock_now - timedelta(days=30)
        assert cutoff_date == expected_cutoff.isoformat()

    def test_calculate_cutoff_date_user_data(self):
        """Test cutoff date calculation for user data."""
        service = RetentionService()
        settings = DataRetentionSettings(user_data_retention_days=365)

        with patch('services.retention_service.datetime') as mock_datetime:
            mock_now = datetime(2023, 9, 14, 10, 30, 0)
            mock_datetime.utcnow.return_value = mock_now

            cutoff_date = service._calculate_cutoff_date(RetentionType.USER_DATA, settings)

        assert cutoff_date is not None
        expected_cutoff = mock_now - timedelta(days=365)
        assert cutoff_date == expected_cutoff.isoformat()

    def test_calculate_cutoff_date_invalid_type(self):
        """Test cutoff date calculation with invalid retention type."""
        service = RetentionService()
        settings = DataRetentionSettings()

        # Use invalid enum value (this should not happen in practice due to type checking)
        with patch('services.retention_service.logger'):
            cutoff_date = service._calculate_cutoff_date("invalid_type", settings)

        assert cutoff_date is None


class TestLogDeletion:
    """Test log deletion operations with transaction safety."""

    @pytest.fixture
    def service(self):
        """Create retention service with mocked dependencies."""
        service = RetentionService()
        service.db_service = AsyncMock()
        return service

    async def test_preview_log_deletion_with_records(self, service):
        """Test log deletion preview when records exist."""
        cutoff_date = "2023-08-15T00:00:00.000Z"

        # Mock database connection and results
        mock_conn = AsyncMock()
        service.db_service.get_connection.return_value.__aenter__.return_value = mock_conn

        # Mock count query result
        count_cursor = AsyncMock()
        count_cursor.fetchone.return_value = {'count': 150}
        mock_conn.execute.return_value = count_cursor

        # Mock date range query result
        date_cursor = AsyncMock()
        date_cursor.fetchone.return_value = {
            'oldest': '2023-01-01T00:00:00.000Z',
            'newest': '2023-08-01T00:00:00.000Z'
        }

        # Configure mock to return different cursors for different queries
        mock_conn.execute.side_effect = [count_cursor, date_cursor]

        preview = await service._preview_log_deletion(cutoff_date)

        assert preview is not None
        assert preview.retention_type == RetentionType.LOGS
        assert preview.affected_records == 150
        assert preview.oldest_record_date == '2023-01-01T00:00:00.000Z'
        assert preview.newest_record_date == '2023-08-01T00:00:00.000Z'
        assert preview.estimated_space_freed_mb == 0.15  # 150 * 0.001

    async def test_preview_log_deletion_no_records(self, service):
        """Test log deletion preview when no records to delete."""
        cutoff_date = "2023-08-15T00:00:00.000Z"

        mock_conn = AsyncMock()
        service.db_service.get_connection.return_value.__aenter__.return_value = mock_conn

        count_cursor = AsyncMock()
        count_cursor.fetchone.return_value = {'count': 0}
        mock_conn.execute.return_value = count_cursor

        preview = await service._preview_log_deletion(cutoff_date)

        assert preview is not None
        assert preview.affected_records == 0
        assert preview.oldest_record_date is None
        assert preview.newest_record_date is None

    async def test_delete_logs_batch_success(self, service):
        """Test successful log deletion in batches."""
        cutoff_date = "2023-08-15T00:00:00.000Z"
        batch_size = 100

        mock_conn = AsyncMock()
        service.db_service.get_connection.return_value.__aenter__.return_value = mock_conn

        # Mock cursors for batch deletion (simulate 2 batches then completion)
        mock_cursors = [
            AsyncMock(rowcount=100),  # First batch: 100 deleted
            AsyncMock(rowcount=50),   # Second batch: 50 deleted (less than batch_size, so done)
        ]
        mock_conn.execute.side_effect = mock_cursors

        total_deleted, space_freed = await service._delete_logs_batch(cutoff_date, batch_size)

        assert total_deleted == 150
        assert space_freed == 0.15  # 150 * 0.001
        mock_conn.execute.assert_any_call("BEGIN IMMEDIATE")
        mock_conn.commit.assert_called_once()

    async def test_delete_logs_batch_with_rollback(self, service):
        """Test log deletion with transaction rollback on error."""
        cutoff_date = "2023-08-15T00:00:00.000Z"
        batch_size = 100

        mock_conn = AsyncMock()
        service.db_service.get_connection.return_value.__aenter__.return_value = mock_conn

        # Mock database error during deletion
        mock_conn.execute.side_effect = [
            None,  # BEGIN IMMEDIATE succeeds
            Exception("Database error during deletion")  # DELETE fails
        ]

        with pytest.raises(Exception):
            await service._delete_logs_batch(cutoff_date, batch_size)

        mock_conn.rollback.assert_called_once()


class TestAuditLogging:
    """Test comprehensive audit logging for all retention operations."""

    @pytest.fixture
    def service(self):
        """Create retention service with mocked dependencies."""
        service = RetentionService()
        service.db_service = AsyncMock()
        return service

    async def test_log_retention_operation_success(self, service):
        """Test successful retention operation logging."""
        with patch('services.retention_service.log_service') as mock_log_service:
            await service._log_retention_operation(
                RetentionOperation.CLEANUP,
                RetentionType.LOGS,
                "admin-123",
                True,
                records_affected=100,
                client_ip="192.168.1.100",
                metadata={"operation_id": "cleanup-abc123"}
            )

        mock_log_service.create_log_entry.assert_called_once()
        # Verify log entry contains expected data
        call_args = mock_log_service.create_log_entry.call_args[0][0]
        assert isinstance(call_args, LogEntry)
        assert call_args.level == "INFO"
        assert call_args.source == "retention_service"
        assert "100 records affected" in call_args.message

    async def test_log_retention_operation_failure(self, service):
        """Test failed retention operation logging."""
        with patch('services.retention_service.log_service') as mock_log_service:
            await service._log_retention_operation(
                RetentionOperation.CLEANUP,
                RetentionType.LOGS,
                "admin-123",
                False,
                error_message="Security validation failed"
            )

        mock_log_service.create_log_entry.assert_called_once()
        call_args = mock_log_service.create_log_entry.call_args[0][0]
        assert call_args.level == "ERROR"
        assert "failed" in call_args.message

    async def test_log_retention_operation_exception_handling(self, service):
        """Test audit logging handles exceptions gracefully."""
        with patch('services.retention_service.log_service') as mock_log_service:
            mock_log_service.create_log_entry.side_effect = Exception("Logging service error")

            # Should not raise exception
            await service._log_retention_operation(
                RetentionOperation.CLEANUP,
                RetentionType.LOGS,
                "admin-123",
                True
            )

        # Verify logging was attempted despite the error
        mock_log_service.create_log_entry.assert_called_once()


class TestErrorHandling:
    """Test comprehensive error handling and edge cases."""

    @pytest.fixture
    def service(self):
        """Create retention service with mocked dependencies."""
        service = RetentionService()
        service.db_service = AsyncMock()
        service.auth_service = AsyncMock()
        return service

    async def test_get_retention_settings_exception_handling(self, service):
        """Test retention settings retrieval handles exceptions."""
        service.db_service.get_user_by_id.side_effect = Exception("Database connection error")

        settings = await service.get_retention_settings("admin-123")

        # Should return default settings on error
        assert settings is not None
        assert settings.log_retention_days == 30

    async def test_preview_cleanup_exception_handling(self, service):
        """Test cleanup preview handles exceptions gracefully."""
        cleanup_request = CleanupRequest(
            retention_type=RetentionType.LOGS,
            admin_user_id="admin-123",
            session_token="valid-token",
            dry_run=True
        )

        # Mock exception during security validation
        with patch.object(service, '_validate_security', side_effect=Exception("Unexpected error")):
            result = await service.preview_cleanup(cleanup_request)

        assert result is None

    async def test_perform_cleanup_exception_handling(self, service):
        """Test cleanup execution handles exceptions gracefully."""
        cleanup_request = CleanupRequest(
            retention_type=RetentionType.LOGS,
            admin_user_id="admin-123",
            session_token="valid-token",
            dry_run=True
        )

        # Mock exception during cleanup
        with patch.object(service, '_validate_security', side_effect=Exception("Critical error")):
            result = await service.perform_cleanup(cleanup_request)

        assert result is not None
        assert result.success is False
        assert "Critical error" in result.error_message