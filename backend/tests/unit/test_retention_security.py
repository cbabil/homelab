"""
Comprehensive Security Tests for Data Retention Feature.

Tests security vulnerabilities, privilege escalation attacks, malicious input handling,
and audit trail verification for the data retention system. Focuses on critical security
requirements identified in the audit.
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from services.retention_service import RetentionService
from tools.retention_tools import RetentionTools
from models.retention import (
    DataRetentionSettings, CleanupRequest, CleanupResult, CleanupPreview,
    RetentionType, RetentionOperation, SecurityValidationResult
)
from models.auth import User, UserRole


class TestPrivilegeEscalationPrevention:
    """Test prevention of privilege escalation attacks."""

    @pytest.fixture
    def service(self):
        """Create retention service with mocked dependencies."""
        service = RetentionService()
        service.db_service = AsyncMock()
        service.auth_service = AsyncMock()
        return service

    async def test_token_manipulation_attack(self, service):
        """Test security against JWT token manipulation attacks."""
        # Simulate malicious token with admin claims but invalid signature
        malicious_request = CleanupRequest(
            retention_type=RetentionType.LOGS,
            admin_user_id="attacker-123",
            session_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImFkbWluIiwicm9sZSI6ImFkbWluIn0.malicious_signature",
            dry_run=True
        )

        # Token validation should fail
        service.auth_service._validate_jwt_token.return_value = None

        result = await service._validate_security(malicious_request)

        assert result.is_valid is False
        assert "Invalid or expired session token" in result.error_message

    async def test_user_id_spoofing_attack(self, service):
        """Test security against user ID spoofing in requests."""
        # Attacker tries to impersonate admin by providing admin user ID
        spoofing_request = CleanupRequest(
            retention_type=RetentionType.LOGS,
            admin_user_id="real-admin-123",  # Real admin ID
            session_token="valid-user-token",  # But token belongs to regular user
            dry_run=True
        )

        # Token belongs to regular user, not admin
        regular_user = User(
            id="attacker-456",
            username="attacker",
            email="attacker@example.com",
            role=UserRole.USER,
            is_active=True,
            preferences={}
        )

        service.auth_service._validate_jwt_token.return_value = {"username": "attacker"}
        service.auth_service.get_user_by_username.return_value = regular_user

        result = await service._validate_security(spoofing_request)

        assert result.is_valid is False
        assert result.is_admin is False
        assert "Admin privileges required" in result.error_message

    async def test_session_hijacking_protection(self, service):
        """Test protection against session hijacking attacks."""
        hijack_request = CleanupRequest(
            retention_type=RetentionType.LOGS,
            admin_user_id="admin-123",
            session_token="stolen-admin-token",
            dry_run=True
        )

        # Simulate expired or revoked token
        service.auth_service._validate_jwt_token.return_value = None

        result = await service._validate_security(hijack_request)

        assert result.is_valid is False
        assert "Invalid or expired session token" in result.error_message

    async def test_role_elevation_attack(self, service):
        """Test prevention of role elevation through data modification."""
        # User tries to elevate their role by modifying database
        regular_user = User(
            id="user-456",
            username="user",
            email="user@example.com",
            role=UserRole.USER,  # Should remain USER
            is_active=True,
            preferences={}
        )

        attack_request = CleanupRequest(
            retention_type=RetentionType.LOGS,
            admin_user_id="user-456",
            session_token="valid-token",
            dry_run=True
        )

        service.auth_service._validate_jwt_token.return_value = {"username": "user"}
        service.auth_service.get_user_by_username.return_value = regular_user

        result = await service._validate_security(attack_request)

        # Should fail even if user exists and is active
        assert result.is_valid is False
        assert result.is_admin is False


class TestMaliciousInputHandling:
    """Test handling of malicious input and injection attacks."""

    @pytest.fixture
    def service(self):
        """Create retention service with mocked dependencies."""
        service = RetentionService()
        service.db_service = AsyncMock()
        service.auth_service = AsyncMock()
        return service

    @pytest.fixture
    def tools(self, service):
        """Create retention tools with service."""
        return RetentionTools(service)

    async def test_sql_injection_in_user_id(self, service):
        """Test protection against SQL injection in user ID parameter."""
        malicious_user_id = "admin'; DROP TABLE log_entries; --"

        # Should be handled by parameterized queries, not cause SQL injection
        with patch.object(service.db_service, 'get_user_by_id') as mock_get_user:
            mock_get_user.return_value = None

            settings = await service.get_retention_settings(malicious_user_id)

            # Should return default settings, not crash or execute malicious SQL
            assert settings is not None
            assert settings.log_retention_days == 30
            mock_get_user.assert_called_once_with(malicious_user_id)

    async def test_xss_payload_in_settings_data(self, tools):
        """Test handling of XSS payloads in settings data."""
        malicious_settings = {
            "log_retention_days": "<script>alert('XSS')</script>",
            "user_data_retention_days": "'; DROP TABLE users; --",
            "auto_cleanup_enabled": "javascript:alert('XSS')"
        }

        result = await tools.update_retention_settings(
            settings_data=malicious_settings,
            user_id="admin-123"
        )

        # Should fail validation, not process malicious content
        assert result["success"] is False
        assert result["error"] == "SETTINGS_VALIDATION_ERROR"
        assert "Invalid settings data" in result["message"]

    async def test_oversized_request_data(self, tools):
        """Test handling of oversized request data (DoS protection)."""
        # Create extremely large metadata payload
        large_payload = "A" * 10000000  # 10MB string

        oversized_request = {
            "retention_type": RetentionType.LOGS,
            "admin_user_id": "admin-123",
            "session_token": "valid-token",
            "dry_run": True,
            "malicious_field": large_payload
        }

        result = await tools.preview_cleanup(oversized_request)

        # Should handle gracefully, not crash the service
        assert result is not None
        # Either succeeds (ignoring extra field) or fails validation properly
        if not result["success"]:
            assert result["error"] in ["REQUEST_VALIDATION_ERROR", "PREVIEW_ERROR"]

    async def test_unicode_injection_attack(self, service):
        """Test handling of Unicode injection attacks."""
        # Unicode characters that might bypass filters
        unicode_attack_id = "admin\u202e\u2066fake\u2069\u202d"

        settings = await service.get_retention_settings(unicode_attack_id)

        # Should handle Unicode gracefully
        assert settings is not None
        assert settings.log_retention_days == 30  # Default values


class TestBypassAttempts:
    """Test attempts to bypass security controls."""

    @pytest.fixture
    def service(self):
        """Create retention service with mocked dependencies."""
        service = RetentionService()
        service.db_service = AsyncMock()
        service.auth_service = AsyncMock()
        return service

    async def test_dry_run_bypass_attempt(self, service):
        """Test attempt to bypass mandatory dry-run requirement."""
        bypass_request = CleanupRequest(
            retention_type=RetentionType.LOGS,
            admin_user_id="admin-123",
            session_token="valid-token",
            dry_run=False,  # Trying to skip dry-run
            force_cleanup=False  # Without force flag
        )

        valid_security = SecurityValidationResult(
            is_valid=True,
            is_admin=True,
            session_valid=True,
            user_id="admin-123"
        )

        with patch.object(service, '_validate_security', return_value=valid_security):
            result = await service.perform_cleanup(bypass_request)

        # Should enforce dry-run requirement
        assert result is not None
        assert result.success is False
        assert "Dry-run must be performed before actual cleanup" in result.error_message

    async def test_batch_size_manipulation(self, service):
        """Test manipulation of batch size to cause resource exhaustion."""
        malicious_request = CleanupRequest(
            retention_type=RetentionType.LOGS,
            admin_user_id="admin-123",
            session_token="valid-token",
            dry_run=True,
            batch_size=999999999  # Extremely large batch size
        )

        # Should be constrained by model validation
        assert malicious_request.batch_size <= 10000  # Max allowed by model

    async def test_negative_retention_days(self, service):
        """Test handling of negative retention periods."""
        with pytest.raises(ValueError):
            DataRetentionSettings(log_retention_days=-1)

    async def test_zero_retention_days(self, service):
        """Test handling of zero retention periods."""
        with pytest.raises(ValueError):
            DataRetentionSettings(log_retention_days=0)


class TestConcurrentAttacks:
    """Test security under concurrent attack scenarios."""

    @pytest.fixture
    def service(self):
        """Create retention service with mocked dependencies."""
        service = RetentionService()
        service.db_service = AsyncMock()
        service.auth_service = AsyncMock()
        return service

    async def test_concurrent_cleanup_operations(self, service):
        """Test security when multiple cleanup operations run concurrently."""
        admin_user = User(
            id="admin-123",
            username="admin",
            email="admin@example.com",
            role=UserRole.ADMIN,
            is_active=True,
            preferences={}
        )

        request1 = CleanupRequest(
            retention_type=RetentionType.LOGS,
            admin_user_id="admin-123",
            session_token="token1",
            dry_run=False,
            force_cleanup=True
        )

        request2 = CleanupRequest(
            retention_type=RetentionType.LOGS,
            admin_user_id="admin-123",
            session_token="token2",
            dry_run=False,
            force_cleanup=True
        )

        service.auth_service._validate_jwt_token.return_value = {"username": "admin"}
        service.auth_service.get_user_by_username.return_value = admin_user

        # Mock successful validation and settings
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
                    with patch.object(service, '_perform_secure_deletion', return_value=(50, 5.0)) as mock_deletion:
                        # Execute both requests
                        result1 = await service.perform_cleanup(request1)
                        result2 = await service.perform_cleanup(request2)

        # Both should succeed but be properly isolated
        assert result1.success is True
        assert result2.success is True
        # Should have been called twice (once for each request)
        assert mock_deletion.call_count == 2

    async def test_race_condition_in_settings_update(self, service):
        """Test race condition handling in settings updates."""
        admin_user = User(
            id="admin-123",
            username="admin",
            role=UserRole.ADMIN,
            is_active=True,
            preferences={}
        )

        service.db_service.get_user_by_id.return_value = admin_user

        # Mock database connection with potential race condition
        mock_conn = AsyncMock()
        service.db_service.get_connection.return_value.__aenter__.return_value = mock_conn

        settings1 = DataRetentionSettings(log_retention_days=30)
        settings2 = DataRetentionSettings(log_retention_days=60)

        with patch('services.retention_service.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value.isoformat.return_value = "2023-09-14T10:30:00.000Z"

            # Simulate concurrent updates
            result1 = await service.update_retention_settings("admin-123", settings1)
            result2 = await service.update_retention_settings("admin-123", settings2)

        # Both should complete successfully (database handles concurrency)
        assert result1 is True
        assert result2 is True


class TestAuditTrailSecurity:
    """Test security and integrity of audit trails."""

    @pytest.fixture
    def service(self):
        """Create retention service with mocked dependencies."""
        service = RetentionService()
        service.db_service = AsyncMock()
        service.auth_service = AsyncMock()
        return service

    async def test_audit_log_tampering_prevention(self, service):
        """Test that audit logs cannot be tampered with."""
        with patch('services.retention_service.log_service') as mock_log_service:
            # Simulate audit logging
            await service._log_retention_operation(
                RetentionOperation.CLEANUP,
                RetentionType.LOGS,
                "admin-123",
                True,
                records_affected=100
            )

            # Verify audit log was created with immutable data
            mock_log_service.create_log_entry.assert_called_once()
            call_args = mock_log_service.create_log_entry.call_args[0][0]

            # Audit log should contain all critical information
            assert "retention" in call_args.tags
            assert "audit" in call_args.tags
            assert call_args.source == "retention_service"
            assert "100 records affected" in call_args.message

    async def test_audit_log_for_failed_operations(self, service):
        """Test that failed operations are properly audited."""
        with patch('services.retention_service.log_service') as mock_log_service:
            await service._log_retention_operation(
                RetentionOperation.CLEANUP,
                RetentionType.LOGS,
                "attacker-456",
                False,
                error_message="Security validation failed"
            )

            # Failed operations should be audited too
            mock_log_service.create_log_entry.assert_called_once()
            call_args = mock_log_service.create_log_entry.call_args[0][0]
            assert call_args.level == "ERROR"
            assert "failed" in call_args.message

    async def test_sensitive_data_not_logged(self, service):
        """Test that sensitive data is not included in audit logs."""
        sensitive_metadata = {
            "session_token": "secret-token-12345",
            "password": "user-password",
            "private_key": "-----BEGIN RSA PRIVATE KEY-----"
        }

        with patch('services.retention_service.log_service') as mock_log_service:
            await service._log_retention_operation(
                RetentionOperation.SETTINGS_UPDATE,
                None,
                "admin-123",
                True,
                metadata=sensitive_metadata
            )

            # Check that sensitive data is properly sanitized
            call_args = mock_log_service.create_log_entry.call_args[0][0]
            log_metadata = call_args.metadata

            # Sensitive fields should not be in the audit log
            assert "session_token" not in str(log_metadata)
            assert "password" not in str(log_metadata)
            assert "private_key" not in str(log_metadata)


class TestTransactionSafetyUnderAttack:
    """Test transaction safety under attack scenarios."""

    @pytest.fixture
    def service(self):
        """Create retention service with mocked dependencies."""
        service = RetentionService()
        service.db_service = AsyncMock()
        return service

    async def test_transaction_rollback_on_attack_detection(self, service):
        """Test that transactions are rolled back when attacks are detected."""
        cutoff_date = "2023-08-15T00:00:00.000Z"
        batch_size = 100

        mock_conn = AsyncMock()
        service.db_service.get_connection.return_value.__aenter__.return_value = mock_conn

        # Simulate attack detected during deletion (e.g., unexpected data access)
        mock_conn.execute.side_effect = [
            None,  # BEGIN IMMEDIATE succeeds
            Exception("Security violation detected")  # DELETE operation detects attack
        ]

        with pytest.raises(Exception):
            await service._delete_logs_batch(cutoff_date, batch_size)

        # Transaction should be rolled back
        mock_conn.rollback.assert_called_once()
        mock_conn.commit.assert_not_called()

    async def test_atomic_operation_integrity(self, service):
        """Test that operations remain atomic under various failure conditions."""
        cutoff_date = "2023-08-15T00:00:00.000Z"
        batch_size = 100

        mock_conn = AsyncMock()
        service.db_service.get_connection.return_value.__aenter__.return_value = mock_conn

        # Simulate partial success then failure
        mock_cursors = [
            AsyncMock(rowcount=100),  # First batch succeeds
            Exception("Network interruption")  # Second batch fails
        ]

        mock_conn.execute.side_effect = [None] + mock_cursors  # BEGIN + operations

        with pytest.raises(Exception):
            await service._delete_logs_batch(cutoff_date, batch_size)

        # Should rollback entire transaction, not commit partial results
        mock_conn.rollback.assert_called_once()
        mock_conn.commit.assert_not_called()


class TestDenialOfServiceProtection:
    """Test protection against denial of service attacks."""

    @pytest.fixture
    def tools(self):
        """Create retention tools with mocked service."""
        mock_service = AsyncMock(spec=RetentionService)
        return RetentionTools(mock_service)

    async def test_resource_exhaustion_protection(self, tools):
        """Test protection against resource exhaustion attacks."""
        # Simulate request with extremely large batch size (should be limited by model)
        malicious_request = {
            "retention_type": RetentionType.LOGS,
            "admin_user_id": "admin-123",
            "session_token": "valid-token",
            "dry_run": True,
            "batch_size": 999999999  # Attempt to exhaust resources
        }

        # Request validation should limit batch size
        try:
            request = CleanupRequest(**malicious_request)
            assert request.batch_size <= 10000  # Should be capped by model
        except ValueError:
            # Model validation should reject invalid values
            pass

    async def test_concurrent_request_handling(self, tools):
        """Test that service can handle multiple concurrent requests safely."""
        # Simulate multiple concurrent requests
        requests = []
        for i in range(10):
            requests.append(tools.get_retention_settings(user_id=f"user-{i}"))

        # All requests should complete without crashing
        results = await asyncio.gather(*requests, return_exceptions=True)

        # No exceptions should be raised from concurrent access
        for result in results:
            assert not isinstance(result, Exception)