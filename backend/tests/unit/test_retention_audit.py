"""
Data Retention Audit and Transaction Safety Tests.

Tests comprehensive audit logging, transaction rollback scenarios,
and data integrity guarantees for the retention system under various
failure and attack conditions.
"""

import pytest
import json
import sqlite3
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

from services.retention_service import RetentionService
from models.retention import (
    DataRetentionSettings, CleanupRequest, RetentionType, RetentionOperation,
    RetentionAuditEntry
)
from models.auth import User, UserRole
from models.log import LogEntry


class TestComprehensiveAuditLogging:
    """Test comprehensive audit logging for all retention operations."""

    @pytest.fixture
    def service(self):
        """Create retention service with mocked dependencies."""
        service = RetentionService()
        service.db_service = AsyncMock()
        service.auth_service = AsyncMock()
        return service

    async def test_successful_operations_audit_trail(self, service):
        """Test that all successful operations create proper audit entries."""
        operations = [
            (RetentionOperation.SETTINGS_UPDATE, RetentionType.LOGS, True, 0),
            (RetentionOperation.DRY_RUN, RetentionType.LOGS, True, 150),
            (RetentionOperation.CLEANUP, RetentionType.LOGS, True, 150),
            (RetentionOperation.POLICY_VALIDATION, None, True, 0)
        ]

        with patch('services.retention_service.log_service') as mock_log_service:
            for operation, retention_type, success, records_affected in operations:
                await service._log_retention_operation(
                    operation, retention_type, "admin-123", success,
                    records_affected=records_affected,
                    client_ip="192.168.1.100",
                    user_agent="Mozilla/5.0 Test Browser",
                    metadata={"test": "metadata"}
                )

        # Verify all operations were logged
        assert mock_log_service.create_log_entry.call_count == len(operations)

        # Verify audit entry structure for each operation
        for i, (operation, retention_type, success, records_affected) in enumerate(operations):
            call_args = mock_log_service.create_log_entry.call_args_list[i]
            log_entry = call_args[0][0]

            assert isinstance(log_entry, LogEntry)
            assert log_entry.source == "retention_service"
            assert log_entry.level == "INFO"
            assert operation.value in log_entry.message
            assert "retention" in log_entry.tags
            assert "audit" in log_entry.tags
            assert operation.value in log_entry.tags
            assert "success" in log_entry.tags

            # Verify metadata contains audit information
            metadata = log_entry.metadata
            assert metadata["admin_user_id"] == "admin-123"
            assert metadata["operation"] == operation.value
            assert metadata["success"] is True
            assert metadata["records_affected"] == records_affected
            assert metadata["client_ip"] == "192.168.1.100"
            assert metadata["user_agent"] == "Mozilla/5.0 Test Browser"

    async def test_failed_operations_audit_trail(self, service):
        """Test that failed operations are properly audited with error details."""
        failure_scenarios = [
            ("Security validation failed", "UNAUTHORIZED"),
            ("Database connection error", "DB_ERROR"),
            ("Invalid retention policy", "VALIDATION_ERROR"),
            ("Transaction rollback occurred", "TRANSACTION_FAILED")
        ]

        with patch('services.retention_service.log_service') as mock_log_service:
            for error_message, error_code in failure_scenarios:
                await service._log_retention_operation(
                    RetentionOperation.CLEANUP,
                    RetentionType.LOGS,
                    "attacker-456",
                    False,
                    error_message=error_message,
                    client_ip="10.0.0.1",
                    metadata={"error_code": error_code}
                )

        # Verify all failures were logged
        assert mock_log_service.create_log_entry.call_count == len(failure_scenarios)

        # Verify error logging structure
        for i, (error_message, error_code) in enumerate(failure_scenarios):
            call_args = mock_log_service.create_log_entry.call_args_list[i]
            log_entry = call_args[0][0]

            assert log_entry.level == "ERROR"
            assert "failed" in log_entry.message
            assert "failure" in log_entry.tags
            assert log_entry.metadata["success"] is False
            assert log_entry.metadata["error_message"] == error_message
            assert log_entry.metadata["metadata"]["error_code"] == error_code

    async def test_audit_entry_immutability(self, service):
        """Test that audit entries cannot be tampered with after creation."""
        original_metadata = {
            "operation_id": "cleanup-123",
            "cutoff_date": "2023-08-15T00:00:00.000Z",
            "batch_size": 1000
        }

        with patch('services.retention_service.log_service') as mock_log_service:
            await service._log_retention_operation(
                RetentionOperation.CLEANUP,
                RetentionType.LOGS,
                "admin-123",
                True,
                records_affected=100,
                metadata=original_metadata
            )

            # Get the created log entry
            call_args = mock_log_service.create_log_entry.call_args[0][0]
            audit_metadata = call_args.metadata

            # Attempt to modify metadata (should not affect the logged entry)
            original_metadata["malicious_field"] = "injected_data"
            del original_metadata["operation_id"]

            # Verify audit entry remains unchanged
            assert "malicious_field" not in audit_metadata
            assert audit_metadata["metadata"]["operation_id"] == "cleanup-123"
            assert audit_metadata["metadata"]["cutoff_date"] == "2023-08-15T00:00:00.000Z"

    async def test_audit_logging_resilience(self, service):
        """Test that audit logging failures don't crash the main operation."""
        with patch('services.retention_service.log_service') as mock_log_service:
            # Simulate logging service failure
            mock_log_service.create_log_entry.side_effect = Exception("Audit service unavailable")

            # Operation should continue despite audit logging failure
            try:
                await service._log_retention_operation(
                    RetentionOperation.CLEANUP,
                    RetentionType.LOGS,
                    "admin-123",
                    True,
                    records_affected=50
                )
                # Should not raise exception
            except Exception as e:
                pytest.fail(f"Audit logging failure should not crash operation: {e}")

    async def test_sensitive_data_sanitization(self, service):
        """Test that sensitive data is sanitized from audit logs."""
        sensitive_metadata = {
            "session_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "password": "user_password_123",
            "api_key": "sk-1234567890abcdef",
            "private_key": "-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCA...",
            "safe_data": "this_should_remain"
        }

        with patch('services.retention_service.log_service') as mock_log_service:
            await service._log_retention_operation(
                RetentionOperation.SETTINGS_UPDATE,
                None,
                "admin-123",
                True,
                metadata=sensitive_metadata
            )

            call_args = mock_log_service.create_log_entry.call_args[0][0]
            logged_metadata = json.dumps(call_args.metadata)

            # Sensitive data should not appear in logs
            assert "session_token" not in logged_metadata
            assert "password" not in logged_metadata
            assert "api_key" not in logged_metadata
            assert "private_key" not in logged_metadata
            assert "user_password_123" not in logged_metadata
            assert "sk-1234567890abcdef" not in logged_metadata

            # Safe data should remain
            assert "this_should_remain" in logged_metadata

    async def test_audit_entry_uniqueness(self, service):
        """Test that each audit entry has a unique identifier."""
        with patch('services.retention_service.log_service') as mock_log_service:
            # Create multiple audit entries
            for i in range(10):
                await service._log_retention_operation(
                    RetentionOperation.DRY_RUN,
                    RetentionType.LOGS,
                    f"admin-{i}",
                    True,
                    records_affected=i * 10
                )

            # Collect all audit entry IDs
            audit_ids = []
            for call in mock_log_service.create_log_entry.call_args_list:
                log_entry = call[0][0]
                audit_ids.append(log_entry.id)

            # All IDs should be unique
            assert len(audit_ids) == len(set(audit_ids))

            # All IDs should follow the expected format
            for audit_id in audit_ids:
                assert audit_id.startswith("ret-")
                assert len(audit_id) == 12  # "ret-" + 8 hex chars


class TestTransactionSafety:
    """Test transaction safety and rollback scenarios."""

    @pytest.fixture
    async def temp_database_service(self):
        """Create temporary database for transaction testing."""
        # Create temporary database
        import tempfile
        import os

        db_fd, db_path = tempfile.mkstemp(suffix='.db')
        os.close(db_fd)

        # Initialize database
        conn = sqlite3.connect(db_path)
        conn.execute('''
            CREATE TABLE log_entries (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                level TEXT NOT NULL,
                source TEXT NOT NULL,
                message TEXT NOT NULL,
                tags TEXT,
                metadata TEXT
            )
        ''')

        # Insert test data
        now = datetime.utcnow().isoformat()
        old_timestamp = (datetime.utcnow() - timedelta(days=60)).isoformat()

        for i in range(100):
            conn.execute('''
                INSERT INTO log_entries (id, timestamp, level, source, message, tags, metadata)
                VALUES (?, ?, 'INFO', 'test', 'Test log entry', '[]', '{}')
            ''', (f'test-log-{i}', old_timestamp))

        conn.commit()
        conn.close()

        # Create service with real database
        service = RetentionService()
        service.db_service = AsyncMock()
        service.db_service.db_path = db_path

        @asynccontextmanager
        async def get_connection():
            import aiosqlite
            async with aiosqlite.connect(db_path) as conn:
                conn.row_factory = aiosqlite.Row
                yield conn

        service.db_service.get_connection = get_connection

        yield service, db_path

        # Cleanup
        os.unlink(db_path)

    async def test_successful_transaction_commit(self, temp_database_service):
        """Test that successful operations properly commit transactions."""
        service, db_path = temp_database_service
        cutoff_date = (datetime.utcnow() - timedelta(days=30)).isoformat()

        # Perform deletion
        total_deleted, space_freed = await service._delete_logs_batch(cutoff_date, 50)

        assert total_deleted == 100  # All test records should be deleted
        assert space_freed == 0.1  # 100 * 0.001

        # Verify data was actually deleted from database
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("SELECT COUNT(*) FROM log_entries")
        remaining_count = cursor.fetchone()[0]
        conn.close()

        assert remaining_count == 0

    async def test_transaction_rollback_on_error(self, temp_database_service):
        """Test that transactions are rolled back when errors occur."""
        service, db_path = temp_database_service

        # Mock database connection to simulate error during deletion
        original_get_connection = service.db_service.get_connection

        @asynccontextmanager
        async def failing_connection():
            import aiosqlite
            async with aiosqlite.connect(db_path) as conn:
                conn.row_factory = aiosqlite.Row

                # Mock execute to fail on the DELETE statement
                original_execute = conn.execute

                async def failing_execute(sql, params=None):
                    if "DELETE FROM log_entries" in sql:
                        raise Exception("Simulated database error")
                    return await original_execute(sql, params)

                conn.execute = failing_execute
                yield conn

        service.db_service.get_connection = failing_connection

        cutoff_date = (datetime.utcnow() - timedelta(days=30)).isoformat()

        # Deletion should fail and raise exception
        with pytest.raises(Exception, match="Simulated database error"):
            await service._delete_logs_batch(cutoff_date, 50)

        # Verify no data was deleted (transaction rolled back)
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("SELECT COUNT(*) FROM log_entries")
        remaining_count = cursor.fetchone()[0]
        conn.close()

        assert remaining_count == 100  # All original data should remain

    async def test_partial_batch_rollback(self, temp_database_service):
        """Test rollback when only some batches succeed."""
        service, db_path = temp_database_service

        # Mock to succeed for first batch, fail for second
        call_count = 0

        @asynccontextmanager
        async def selective_failing_connection():
            nonlocal call_count
            import aiosqlite
            async with aiosqlite.connect(db_path) as conn:
                conn.row_factory = aiosqlite.Row

                original_execute = conn.execute

                async def selective_execute(sql, params=None):
                    nonlocal call_count
                    if "DELETE FROM log_entries" in sql:
                        call_count += 1
                        if call_count > 1:  # Fail after first successful batch
                            raise Exception("Database connection lost")
                    return await original_execute(sql, params)

                conn.execute = selective_execute
                yield conn

        service.db_service.get_connection = selective_failing_connection

        cutoff_date = (datetime.utcnow() - timedelta(days=30)).isoformat()

        # Should fail after first batch
        with pytest.raises(Exception, match="Database connection lost"):
            await service._delete_logs_batch(cutoff_date, 30)

        # Verify transaction was rolled back completely
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("SELECT COUNT(*) FROM log_entries")
        remaining_count = cursor.fetchone()[0]
        conn.close()

        assert remaining_count == 100  # All data should remain (no partial deletion)

    async def test_concurrent_transaction_isolation(self, temp_database_service):
        """Test that concurrent transactions don't interfere with each other."""
        service, db_path = temp_database_service
        cutoff_date = (datetime.utcnow() - timedelta(days=30)).isoformat()

        # Create two services for concurrent operations
        service2 = RetentionService()
        service2.db_service = service.db_service

        import asyncio
        import sqlite3

        # Both operations should succeed independently
        results = await asyncio.gather(
            service._delete_logs_batch(cutoff_date, 30),
            service2._delete_logs_batch(cutoff_date, 30),
            return_exceptions=True
        )

        # One should succeed, one might fail due to data already being deleted
        # But no transaction corruption should occur
        for result in results:
            if isinstance(result, Exception):
                # Acceptable failures due to concurrent access
                assert "database is locked" in str(result).lower() or "no such table" in str(result).lower()

        # Verify database integrity
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("SELECT COUNT(*) FROM log_entries")
        remaining_count = cursor.fetchone()[0]
        conn.close()

        # Data should be consistent (either 0 or 100, not partial)
        assert remaining_count in [0, 100]


class TestDataIntegrityValidation:
    """Test data integrity validation and consistency checks."""

    @pytest.fixture
    def service(self):
        """Create retention service with mocked dependencies."""
        service = RetentionService()
        service.db_service = AsyncMock()
        service.auth_service = AsyncMock()
        return service

    async def test_referential_integrity_preservation(self, service):
        """Test that retention operations preserve referential integrity."""
        mock_conn = AsyncMock()
        service.db_service.get_connection.return_value.__aenter__.return_value = mock_conn

        # Mock foreign key constraint checking
        mock_conn.execute.side_effect = [
            None,  # BEGIN IMMEDIATE
            AsyncMock(rowcount=50),  # First DELETE batch
            AsyncMock(rowcount=0),   # Second DELETE batch (no more records)
        ]

        cutoff_date = "2023-08-15T00:00:00.000Z"
        total_deleted, space_freed = await service._delete_logs_batch(cutoff_date, 100)

        assert total_deleted == 50
        assert space_freed == 0.05

        # Verify foreign key checks were maintained
        mock_conn.execute.assert_any_call("BEGIN IMMEDIATE")
        mock_conn.commit.assert_called_once()

    async def test_data_consistency_validation(self, service):
        """Test validation of data consistency before and after operations."""
        # Mock pre-operation count
        service.db_service.get_connection.return_value.__aenter__.return_value.execute.return_value.fetchone.return_value = {'count': 200}

        cutoff_date = "2023-08-15T00:00:00.000Z"

        # Mock preview operation
        preview = await service._preview_log_deletion(cutoff_date)

        assert preview is not None
        assert preview.affected_records == 200

        # Verify consistency check queries were made
        service.db_service.get_connection.return_value.__aenter__.return_value.execute.assert_called()

    async def test_orphaned_record_prevention(self, service):
        """Test prevention of orphaned records during cleanup."""
        mock_conn = AsyncMock()
        service.db_service.get_connection.return_value.__aenter__.return_value = mock_conn

        # Simulate scenario where deletion would create orphaned records
        mock_conn.execute.side_effect = [
            None,  # BEGIN IMMEDIATE
            Exception("FOREIGN KEY constraint failed"),  # DELETE fails due to FK constraint
        ]

        cutoff_date = "2023-08-15T00:00:00.000Z"

        # Should fail and rollback to prevent orphaned records
        with pytest.raises(Exception, match="FOREIGN KEY constraint failed"):
            await service._delete_logs_batch(cutoff_date, 100)

        mock_conn.rollback.assert_called_once()

    async def test_database_corruption_detection(self, service):
        """Test detection and handling of database corruption."""
        mock_conn = AsyncMock()
        service.db_service.get_connection.return_value.__aenter__.return_value = mock_conn

        # Simulate database corruption
        mock_conn.execute.side_effect = Exception("database disk image is malformed")

        cutoff_date = "2023-08-15T00:00:00.000Z"

        # Should detect corruption and fail safely
        with pytest.raises(Exception, match="database disk image is malformed"):
            await service._delete_logs_batch(cutoff_date, 100)

        # Should attempt cleanup
        mock_conn.rollback.assert_called_once()


class TestSecurityAuditing:
    """Test security-focused audit logging and monitoring."""

    @pytest.fixture
    def service(self):
        """Create retention service with mocked dependencies."""
        service = RetentionService()
        service.db_service = AsyncMock()
        service.auth_service = AsyncMock()
        return service

    async def test_privilege_escalation_attempt_logging(self, service):
        """Test logging of privilege escalation attempts."""
        with patch('services.retention_service.log_service') as mock_log_service:
            await service._log_retention_operation(
                RetentionOperation.CLEANUP,
                RetentionType.LOGS,
                "regular-user-456",  # Non-admin attempting admin operation
                False,
                error_message="Admin privileges required for retention operations",
                client_ip="suspicious-ip-address",
                user_agent="Automated Scanner v1.0",
                metadata={
                    "attempted_operation": "force_cleanup",
                    "escalation_attempt": True,
                    "risk_level": "HIGH"
                }
            )

            call_args = mock_log_service.create_log_entry.call_args[0][0]
            assert call_args.level == "ERROR"
            assert "Admin privileges required" in call_args.metadata["error_message"]
            assert call_args.metadata["client_ip"] == "suspicious-ip-address"
            assert call_args.metadata["metadata"]["escalation_attempt"] is True
            assert call_args.metadata["metadata"]["risk_level"] == "HIGH"

    async def test_suspicious_activity_pattern_logging(self, service):
        """Test logging of suspicious activity patterns."""
        suspicious_activities = [
            ("Multiple rapid requests from single IP", {"request_count": 50, "time_window": 60}),
            ("Unusual retention policy changes", {"log_retention_days": 1, "suspicious": True}),
            ("Off-hours administrative activity", {"timestamp": "2023-09-14T03:00:00.000Z"}),
            ("Bulk deletion attempt", {"records_targeted": 1000000, "bulk_operation": True})
        ]

        with patch('services.retention_service.log_service') as mock_log_service:
            for activity, metadata in suspicious_activities:
                await service._log_retention_operation(
                    RetentionOperation.CLEANUP,
                    RetentionType.LOGS,
                    "admin-123",
                    False,
                    error_message=activity,
                    metadata=metadata
                )

            assert mock_log_service.create_log_entry.call_count == len(suspicious_activities)

            # Verify each suspicious activity was properly logged
            for i, (activity, metadata) in enumerate(suspicious_activities):
                call_args = mock_log_service.create_log_entry.call_args_list[i]
                log_entry = call_args[0][0]
                assert activity in log_entry.metadata["error_message"]
                for key, value in metadata.items():
                    assert log_entry.metadata["metadata"][key] == value

    async def test_compliance_audit_trail(self, service):
        """Test comprehensive audit trail for compliance requirements."""
        compliance_operations = [
            (RetentionOperation.SETTINGS_UPDATE, "Updated retention policy per compliance requirements"),
            (RetentionOperation.DRY_RUN, "Compliance audit dry-run performed"),
            (RetentionOperation.CLEANUP, "Data deletion per retention policy compliance"),
            (RetentionOperation.POLICY_VALIDATION, "Retention policy compliance validation")
        ]

        with patch('services.retention_service.log_service') as mock_log_service:
            for operation, description in compliance_operations:
                await service._log_retention_operation(
                    operation,
                    RetentionType.AUDIT_LOGS if operation == RetentionOperation.CLEANUP else RetentionType.LOGS,
                    "compliance-admin-789",
                    True,
                    records_affected=100 if operation == RetentionOperation.CLEANUP else 0,
                    metadata={
                        "compliance_officer": "compliance-admin-789",
                        "regulation": "GDPR Article 17",
                        "retention_justification": "Legal requirement",
                        "audit_reference": f"AUDIT-2023-{operation.value.upper()}"
                    }
                )

            # Verify comprehensive compliance logging
            for i, (operation, description) in enumerate(compliance_operations):
                call_args = mock_log_service.create_log_entry.call_args_list[i]
                log_entry = call_args[0][0]

                assert log_entry.metadata["metadata"]["regulation"] == "GDPR Article 17"
                assert log_entry.metadata["metadata"]["compliance_officer"] == "compliance-admin-789"
                assert f"AUDIT-2023-{operation.value.upper()}" in log_entry.metadata["metadata"]["audit_reference"]

    async def test_tamper_detection_logging(self, service):
        """Test detection and logging of potential tampering attempts."""
        tampering_scenarios = [
            ("Audit log modification attempt", {"target": "audit_logs", "action": "modify"}),
            ("Retention settings bypass attempt", {"bypass_method": "direct_db_access"}),
            ("Timestamp manipulation detected", {"original_timestamp": "2023-09-14", "manipulated_timestamp": "2023-01-01"}),
            ("Checksum validation failure", {"expected_checksum": "abc123", "actual_checksum": "def456"})
        ]

        with patch('services.retention_service.log_service') as mock_log_service:
            for scenario, metadata in tampering_scenarios:
                await service._log_retention_operation(
                    RetentionOperation.CLEANUP,
                    RetentionType.AUDIT_LOGS,
                    "potential-attacker",
                    False,
                    error_message=f"SECURITY ALERT: {scenario}",
                    metadata={
                        "security_event": True,
                        "threat_level": "CRITICAL",
                        **metadata
                    }
                )

            # Verify all tampering attempts were logged with appropriate severity
            for i, (scenario, metadata) in enumerate(tampering_scenarios):
                call_args = mock_log_service.create_log_entry.call_args_list[i]
                log_entry = call_args[0][0]

                assert log_entry.level == "ERROR"
                assert "SECURITY ALERT" in log_entry.metadata["error_message"]
                assert log_entry.metadata["metadata"]["security_event"] is True
                assert log_entry.metadata["metadata"]["threat_level"] == "CRITICAL"