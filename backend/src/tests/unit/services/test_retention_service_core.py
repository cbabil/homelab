"""
Unit tests for services/retention_service.py - Core operations.

Tests initialization, security validation, retention settings, and audit logging.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.auth import User, UserRole
from models.retention import (
    CleanupRequest,
    RetentionOperation,
    RetentionSettings,
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


@pytest.fixture
def admin_user():
    """Create admin user for testing."""
    return User(
        id="admin-123",
        username="admin",
        email="admin@example.com",
        role=UserRole.ADMIN,
        last_login="2024-01-15T10:00:00+00:00",
        is_active=True,
    )


@pytest.fixture
def regular_user():
    """Create regular user for testing."""
    return User(
        id="user-456",
        username="regular",
        email="user@example.com",
        role=UserRole.USER,
        last_login="2024-01-15T10:00:00+00:00",
        is_active=True,
    )


@pytest.fixture
def cleanup_request():
    """Create cleanup request for testing."""
    return CleanupRequest(
        retention_type=RetentionType.AUDIT_LOGS,
        dry_run=True,
        admin_user_id="admin-123",
        session_token="valid-token-abc123",
    )


class TestRetentionServiceInit:
    """Tests for RetentionService initialization."""

    def test_init_stores_services(self, mock_db_service, mock_auth_service):
        """RetentionService should store service references."""
        with patch("services.retention_service.logger"):
            service = RetentionService(mock_db_service, mock_auth_service)
            assert service.db_service is mock_db_service
            assert service.auth_service is mock_auth_service

    def test_init_creates_default_services(self):
        """RetentionService should create default services if not provided."""
        with (
            patch("services.retention_service.logger"),
            patch("services.retention_service.DatabaseService") as MockDB,
            patch("services.retention_service.AuthService") as MockAuth,
        ):
            MockDB.return_value = MagicMock()
            MockAuth.return_value = MagicMock()
            service = RetentionService()
            assert service.db_service is MockDB.return_value
            assert service.auth_service is MockAuth.return_value

    def test_init_sets_batch_sizes(self, mock_db_service, mock_auth_service):
        """RetentionService should set batch size limits."""
        with patch("services.retention_service.logger"):
            service = RetentionService(mock_db_service, mock_auth_service)
            assert service.max_batch_size == 10000
            assert service.min_batch_size == 100

    def test_init_logs_message(self, mock_db_service, mock_auth_service):
        """RetentionService should log initialization."""
        with patch("services.retention_service.logger") as mock_logger:
            RetentionService(mock_db_service, mock_auth_service)
            mock_logger.info.assert_called_with("Retention service initialized")


class TestValidateSecurity:
    """Tests for _validate_security method."""

    @pytest.mark.asyncio
    async def test_validate_security_invalid_token(
        self, retention_service, mock_auth_service, cleanup_request
    ):
        """_validate_security should return invalid for bad token."""
        mock_auth_service._validate_jwt_token.return_value = None

        with patch("services.retention_service.logger"):
            result = await retention_service._validate_security(cleanup_request)

        assert result.is_valid is False
        assert "Invalid or expired session token" in result.error_message

    @pytest.mark.asyncio
    async def test_validate_security_missing_username_in_token(
        self, retention_service, mock_auth_service, cleanup_request
    ):
        """_validate_security should return invalid when username missing."""
        # Token is valid but has no username key
        mock_auth_service._validate_jwt_token.return_value = {"exp": 12345}

        with patch("services.retention_service.logger"):
            result = await retention_service._validate_security(cleanup_request)

        assert result.is_valid is False
        assert "Invalid token payload" in result.error_message

    @pytest.mark.asyncio
    async def test_validate_security_user_not_found(
        self, retention_service, mock_auth_service, cleanup_request
    ):
        """_validate_security should return invalid when user not found."""
        mock_auth_service._validate_jwt_token.return_value = {"username": "admin"}
        mock_auth_service.get_user_by_username = AsyncMock(return_value=None)

        with patch("services.retention_service.logger"):
            result = await retention_service._validate_security(cleanup_request)

        assert result.is_valid is False
        assert "User not found or inactive" in result.error_message

    @pytest.mark.asyncio
    async def test_validate_security_user_inactive(
        self, retention_service, mock_auth_service, cleanup_request, admin_user
    ):
        """_validate_security should return invalid for inactive user."""
        mock_auth_service._validate_jwt_token.return_value = {"username": "admin"}
        admin_user.is_active = False
        mock_auth_service.get_user_by_username = AsyncMock(return_value=admin_user)

        with patch("services.retention_service.logger"):
            result = await retention_service._validate_security(cleanup_request)

        assert result.is_valid is False
        assert "User not found or inactive" in result.error_message

    @pytest.mark.asyncio
    async def test_validate_security_non_admin_user(
        self, retention_service, mock_auth_service, cleanup_request, regular_user
    ):
        """_validate_security should return invalid for non-admin user."""
        mock_auth_service._validate_jwt_token.return_value = {"username": "regular"}
        mock_auth_service.get_user_by_username = AsyncMock(return_value=regular_user)

        with patch("services.retention_service.logger"):
            result = await retention_service._validate_security(cleanup_request)

        assert result.is_valid is False
        assert result.is_admin is False
        assert result.session_valid is True
        assert "Admin privileges required" in result.error_message

    @pytest.mark.asyncio
    async def test_validate_security_admin_success(
        self, retention_service, mock_auth_service, cleanup_request, admin_user
    ):
        """_validate_security should return valid for admin user."""
        mock_auth_service._validate_jwt_token.return_value = {"username": "admin"}
        mock_auth_service.get_user_by_username = AsyncMock(return_value=admin_user)

        with patch("services.retention_service.logger"):
            result = await retention_service._validate_security(cleanup_request)

        assert result.is_valid is True
        assert result.is_admin is True
        assert result.session_valid is True
        assert result.user_id == "admin-123"

    @pytest.mark.asyncio
    async def test_validate_security_force_cleanup_requires_verification(
        self, retention_service, mock_auth_service, admin_user
    ):
        """_validate_security should flag additional verification for force cleanup."""
        request = CleanupRequest(
            retention_type=RetentionType.AUDIT_LOGS,
            dry_run=False,
            force_cleanup=True,
            admin_user_id="admin-123",
            session_token="valid-token",
        )
        mock_auth_service._validate_jwt_token.return_value = {"username": "admin"}
        mock_auth_service.get_user_by_username = AsyncMock(return_value=admin_user)

        with patch("services.retention_service.logger"):
            result = await retention_service._validate_security(request)

        assert result.is_valid is True
        assert result.requires_additional_verification is True

    @pytest.mark.asyncio
    async def test_validate_security_handles_exception(
        self, retention_service, mock_auth_service, cleanup_request
    ):
        """_validate_security should handle exceptions gracefully."""
        mock_auth_service._validate_jwt_token.side_effect = Exception("Token error")

        with patch("services.retention_service.logger") as mock_logger:
            result = await retention_service._validate_security(cleanup_request)

        assert result.is_valid is False
        assert "Security validation error" in result.error_message
        mock_logger.error.assert_called()


class TestLogRetentionOperation:
    """Tests for _log_retention_operation method."""

    @pytest.mark.asyncio
    async def test_log_retention_operation_success(self, retention_service):
        """_log_retention_operation should log successful operations."""
        with (
            patch("services.retention_service.logger") as mock_logger,
            patch("services.retention_service.log_service") as mock_log_svc,
        ):
            mock_log_svc.create_log_entry = AsyncMock()

            await retention_service._log_retention_operation(
                RetentionOperation.CLEANUP,
                RetentionType.AUDIT_LOGS,
                "admin-123",
                True,
                records_affected=100,
            )

            mock_log_svc.create_log_entry.assert_called_once()
            mock_logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_log_retention_operation_failure(self, retention_service):
        """_log_retention_operation should log failed operations."""
        with (
            patch("services.retention_service.logger"),
            patch("services.retention_service.log_service") as mock_log_svc,
        ):
            mock_log_svc.create_log_entry = AsyncMock()

            await retention_service._log_retention_operation(
                RetentionOperation.CLEANUP,
                RetentionType.AUDIT_LOGS,
                "admin-123",
                False,
                error_message="Cleanup failed",
            )

            mock_log_svc.create_log_entry.assert_called_once()
            call_args = mock_log_svc.create_log_entry.call_args[0][0]
            assert call_args.level == "ERROR"

    @pytest.mark.asyncio
    async def test_log_retention_operation_with_metadata(self, retention_service):
        """_log_retention_operation should include metadata."""
        with (
            patch("services.retention_service.logger"),
            patch("services.retention_service.log_service") as mock_log_svc,
        ):
            mock_log_svc.create_log_entry = AsyncMock()

            await retention_service._log_retention_operation(
                RetentionOperation.SETTINGS_UPDATE,
                None,
                "admin-123",
                True,
                metadata={"settings": {"log_retention": 30}},
            )

            call_args = mock_log_svc.create_log_entry.call_args[0][0]
            assert "retention" in call_args.tags

    @pytest.mark.asyncio
    async def test_log_retention_operation_handles_log_error(self, retention_service):
        """_log_retention_operation should handle logging errors."""
        with (
            patch("services.retention_service.logger") as mock_logger,
            patch("services.retention_service.log_service") as mock_log_svc,
        ):
            mock_log_svc.create_log_entry = AsyncMock(
                side_effect=Exception("Log error")
            )

            # Should not raise
            await retention_service._log_retention_operation(
                RetentionOperation.CLEANUP,
                RetentionType.AUDIT_LOGS,
                "admin-123",
                True,
            )

            mock_logger.error.assert_called()


class TestGetRetentionSettings:
    """Tests for get_retention_settings method."""

    @pytest.mark.asyncio
    async def test_get_retention_settings_found(
        self, retention_service, mock_connection
    ):
        """get_retention_settings should return settings from database."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(
            return_value={
                "access_log_retention": 30,
                "metrics_retention": 90,
                "last_updated": "2024-01-15T10:00:00+00:00",
                "updated_by_user_id": "admin-123",
            }
        )
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        with patch("services.retention_service.logger"):
            result = await retention_service.get_retention_settings("admin-123")

        assert result is not None
        assert result.log_retention == 30
        assert result.data_retention == 90
        assert result.updated_by_user_id == "admin-123"

    @pytest.mark.asyncio
    async def test_get_retention_settings_not_found(
        self, retention_service, mock_connection
    ):
        """get_retention_settings should return defaults when not found."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=None)
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        with patch("services.retention_service.logger"):
            result = await retention_service.get_retention_settings("admin-123")

        assert result is not None
        assert result.log_retention == 30  # Default
        assert result.data_retention == 90  # Default

    @pytest.mark.asyncio
    async def test_get_retention_settings_handles_error(
        self, retention_service, mock_connection
    ):
        """get_retention_settings should return defaults on error."""
        mock_connection.execute = AsyncMock(side_effect=Exception("DB error"))

        with patch("services.retention_service.logger") as mock_logger:
            result = await retention_service.get_retention_settings("admin-123")

        assert result is not None
        assert result.log_retention == 30  # Default
        mock_logger.error.assert_called()


class TestUpdateRetentionSettings:
    """Tests for update_retention_settings method."""

    @pytest.mark.asyncio
    async def test_update_retention_settings_success(
        self, retention_service, mock_db_service, mock_connection, admin_user
    ):
        """update_retention_settings should update database."""
        mock_db_service.get_user_by_id = AsyncMock(return_value=admin_user)

        settings = RetentionSettings(log_retention=45, data_retention=120)

        with (
            patch("services.retention_service.logger"),
            patch.object(
                retention_service, "_log_retention_operation", new_callable=AsyncMock
            ),
        ):
            result = await retention_service.update_retention_settings(
                "admin-123", settings
            )

        assert result is True
        mock_connection.execute.assert_called()
        mock_connection.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_retention_settings_non_admin(
        self, retention_service, mock_db_service, regular_user
    ):
        """update_retention_settings should reject non-admin users."""
        mock_db_service.get_user_by_id = AsyncMock(return_value=regular_user)

        settings = RetentionSettings(log_retention=45, data_retention=120)

        with patch("services.retention_service.logger") as mock_logger:
            result = await retention_service.update_retention_settings(
                "user-456", settings
            )

        assert result is False
        mock_logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_update_retention_settings_user_not_found(
        self, retention_service, mock_db_service
    ):
        """update_retention_settings should reject when user not found."""
        mock_db_service.get_user_by_id = AsyncMock(return_value=None)

        settings = RetentionSettings(log_retention=45, data_retention=120)

        with patch("services.retention_service.logger") as mock_logger:
            result = await retention_service.update_retention_settings(
                "unknown-user", settings
            )

        assert result is False
        mock_logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_update_retention_settings_handles_error(
        self, mock_auth_service, admin_user
    ):
        """update_retention_settings should handle database errors."""
        # Create a fresh service with error-raising connection
        mock_db_svc = MagicMock()
        mock_db_svc.get_user_by_id = AsyncMock(return_value=admin_user)

        mock_error_conn = AsyncMock()
        mock_error_conn.execute = AsyncMock(side_effect=Exception("DB error"))

        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__.return_value = mock_error_conn
        mock_context_manager.__aexit__.return_value = None
        mock_db_svc.get_connection = MagicMock(return_value=mock_context_manager)

        settings = RetentionSettings(log_retention=45, data_retention=120)

        with (
            patch("services.retention_service.logger") as mock_logger,
            patch("services.retention_service.log_service") as mock_log_svc,
        ):
            mock_log_svc.create_log_entry = AsyncMock()
            service = RetentionService(mock_db_svc, mock_auth_service)
            result = await service.update_retention_settings("admin-123", settings)

        assert result is False
        mock_logger.error.assert_called()
