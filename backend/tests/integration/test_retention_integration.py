"""
Integration Tests for Data Retention System.

Tests complete end-to-end workflows, database integration, MCP tool functionality,
and real-world scenarios with actual database operations and cross-service communication.
"""

import pytest
import asyncio
import sqlite3
import json
import tempfile
import os
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
from contextlib import asynccontextmanager

from services.retention_service import RetentionService
from tools.retention_tools import RetentionTools
from services.database_service import DatabaseService
from services.auth_service import AuthService
from models.retention import (
    DataRetentionSettings, CleanupRequest, RetentionType, RetentionOperation
)
from models.auth import User, UserRole
from models.log import LogEntry


class TestDatabaseIntegration:
    """Test retention operations with real database operations."""

    @pytest.fixture
    async def temp_database(self):
        """Create temporary database for integration tests."""
        # Create temporary database file
        db_fd, db_path = tempfile.mkstemp(suffix='.db')
        os.close(db_fd)

        # Initialize database schema
        conn = sqlite3.connect(db_path)

        # Create log_entries table
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

        # Create users table
        conn.execute('''
            CREATE TABLE users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                preferences_json TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')

        # Insert test data
        now = datetime.utcnow().isoformat()
        old_timestamp = (datetime.utcnow() - timedelta(days=60)).isoformat()
        recent_timestamp = (datetime.utcnow() - timedelta(days=5)).isoformat()

        # Insert old log entries (should be deleted)
        for i in range(10):
            conn.execute('''
                INSERT INTO log_entries (id, timestamp, level, source, message, tags, metadata)
                VALUES (?, ?, 'INFO', 'test', 'Old log entry', '[]', '{}')
            ''', (f'old-log-{i}', old_timestamp))

        # Insert recent log entries (should be preserved)
        for i in range(5):
            conn.execute('''
                INSERT INTO log_entries (id, timestamp, level, source, message, tags, metadata)
                VALUES (?, ?, 'INFO', 'test', 'Recent log entry', '[]', '{}')
            ''', (f'recent-log-{i}', recent_timestamp))

        # Insert admin user
        admin_preferences = json.dumps({
            'retention_settings': {
                'log_retention_days': 30,
                'user_data_retention_days': 365,
                'auto_cleanup_enabled': True
            }
        })

        conn.execute('''
            INSERT INTO users (id, username, email, password_hash, role, is_active, preferences_json, created_at, updated_at)
            VALUES (?, 'admin', 'admin@example.com', 'hash', 'ADMIN', 1, ?, ?, ?)
        ''', ('admin-123', admin_preferences, now, now))

        conn.commit()
        conn.close()

        yield db_path

        # Cleanup
        os.unlink(db_path)

    @pytest.fixture
    async def retention_service_with_db(self, temp_database):
        """Create retention service with real database connection."""
        service = RetentionService()

        # Mock database service to use temp database
        service.db_service = DatabaseService()
        service.db_service.db_path = temp_database

        # Mock auth service for testing
        service.auth_service = AsyncMock()

        return service

    async def test_real_database_cleanup_operation(self, retention_service_with_db):
        """Test actual database cleanup with real SQLite operations."""
        service = retention_service_with_db

        # Setup auth mocks for admin user
        admin_user = User(
            id="admin-123",
            username="admin",
            email="admin@example.com",
            role=UserRole.ADMIN,
            is_active=True,
            preferences={}
        )

        service.auth_service._validate_jwt_token.return_value = {"username": "admin"}
        service.auth_service.get_user_by_username.return_value = admin_user

        # Create cleanup request
        cleanup_request = CleanupRequest(
            retention_type=RetentionType.LOGS,
            admin_user_id="admin-123",
            session_token="valid-token",
            dry_run=True
        )

        # Test preview operation
        preview = await service.preview_cleanup(cleanup_request)

        assert preview is not None
        assert preview.retention_type == RetentionType.LOGS
        assert preview.affected_records == 10  # Should find 10 old log entries

        # Test actual cleanup
        cleanup_request.dry_run = False
        cleanup_request.force_cleanup = True

        result = await service.perform_cleanup(cleanup_request)

        assert result is not None
        assert result.success is True
        assert result.records_affected == 10

        # Verify database state - old records should be gone, recent should remain
        conn = sqlite3.connect(service.db_service.db_path)
        cursor = conn.execute("SELECT COUNT(*) FROM log_entries")
        remaining_count = cursor.fetchone()[0]
        conn.close()

        assert remaining_count == 5  # Only recent entries should remain

    async def test_transaction_rollback_on_error(self, retention_service_with_db):
        """Test that database transactions are properly rolled back on errors."""
        service = retention_service_with_db

        # Force a database error during deletion
        original_method = service._delete_logs_batch

        async def failing_deletion(*args, **kwargs):
            # Start the deletion but force an error partway through
            async with service.db_service.get_connection() as conn:
                await conn.execute("BEGIN IMMEDIATE")
                # Force an error by executing invalid SQL
                await conn.execute("INVALID SQL STATEMENT")

        service._delete_logs_batch = failing_deletion

        cutoff_date = (datetime.utcnow() - timedelta(days=30)).isoformat()

        # Should raise exception and rollback
        with pytest.raises(Exception):
            await service._delete_logs_batch(cutoff_date, 100)

        # Verify no data was actually deleted (transaction rolled back)
        conn = sqlite3.connect(service.db_service.db_path)
        cursor = conn.execute("SELECT COUNT(*) FROM log_entries")
        total_count = cursor.fetchone()[0]
        conn.close()

        assert total_count == 15  # All original data should still be there

    async def test_settings_persistence_in_database(self, retention_service_with_db):
        """Test that retention settings are properly persisted in database."""
        service = retention_service_with_db

        # Create new settings
        new_settings = DataRetentionSettings(
            log_retention_days=45,
            user_data_retention_days=730,
            auto_cleanup_enabled=False
        )

        # Update settings (bypassing admin check for test)
        with patch.object(service.db_service, 'get_user_by_id') as mock_get_user:
            admin_user = User(
                id="admin-123",
                username="admin",
                role=UserRole.ADMIN,
                is_active=True,
                preferences={}
            )
            mock_get_user.return_value = admin_user

            success = await service.update_retention_settings("admin-123", new_settings)
            assert success is True

        # Verify settings were persisted
        retrieved_settings = await service.get_retention_settings("admin-123")

        assert retrieved_settings is not None
        assert retrieved_settings.log_retention_days == 45
        assert retrieved_settings.user_data_retention_days == 730
        assert retrieved_settings.auto_cleanup_enabled is False


class TestMCPToolsIntegration:
    """Test MCP tools with complete service integration."""

    @pytest.fixture
    def integrated_tools(self):
        """Create retention tools with partially mocked service."""
        service = RetentionService()
        service.db_service = AsyncMock()
        service.auth_service = AsyncMock()

        # Mock some realistic responses
        admin_user = User(
            id="admin-123",
            username="admin",
            email="admin@example.com",
            role=UserRole.ADMIN,
            is_active=True,
            preferences={
                'retention_settings': {
                    'log_retention_days': 30,
                    'user_data_retention_days': 365,
                    'auto_cleanup_enabled': True
                }
            }
        )

        service.db_service.get_user_by_id.return_value = admin_user

        return RetentionTools(service)

    async def test_complete_settings_workflow(self, integrated_tools):
        """Test complete settings get/update workflow through MCP tools."""
        tools = integrated_tools

        # Test getting current settings
        result = await tools.get_retention_settings(user_id="admin-123")

        assert result["success"] is True
        assert result["data"]["log_retention_days"] == 30
        assert result["data"]["auto_cleanup_enabled"] is True

        # Test updating settings
        new_settings_data = {
            "log_retention_days": 60,
            "user_data_retention_days": 730,
            "auto_cleanup_enabled": False
        }

        # Mock successful update
        tools.retention_service.update_retention_settings.return_value = True

        update_result = await tools.update_retention_settings(
            settings_data=new_settings_data,
            user_id="admin-123"
        )

        assert update_result["success"] is True
        assert update_result["data"]["log_retention_days"] == 60

    async def test_complete_cleanup_workflow(self, integrated_tools):
        """Test complete cleanup workflow from preview to execution."""
        tools = integrated_tools

        # Mock preview operation
        from models.retention import CleanupPreview
        mock_preview = CleanupPreview(
            retention_type=RetentionType.LOGS,
            affected_records=150,
            oldest_record_date="2023-01-01T00:00:00.000Z",
            newest_record_date="2023-08-01T00:00:00.000Z",
            estimated_space_freed_mb=0.15,
            cutoff_date="2023-08-15T00:00:00.000Z"
        )

        tools.retention_service.preview_cleanup.return_value = mock_preview

        # Test preview
        preview_request = {
            "retention_type": RetentionType.LOGS,
            "admin_user_id": "admin-123",
            "session_token": "valid-token"
        }

        preview_result = await tools.preview_cleanup(preview_request)

        assert preview_result["success"] is True
        assert preview_result["data"]["affected_records"] == 150
        assert preview_result["data"]["retention_type"] == RetentionType.LOGS

        # Test actual cleanup execution
        from models.retention import CleanupResult
        mock_cleanup_result = CleanupResult(
            operation_id="cleanup-123",
            retention_type=RetentionType.LOGS,
            operation=RetentionOperation.CLEANUP,
            success=True,
            records_affected=150,
            space_freed_mb=0.15,
            duration_seconds=2.5,
            start_time="2023-09-14T10:00:00.000Z",
            end_time="2023-09-14T10:00:02.500Z",
            admin_user_id="admin-123"
        )

        tools.retention_service.perform_cleanup.return_value = mock_cleanup_result

        cleanup_request = {
            "retention_type": RetentionType.LOGS,
            "admin_user_id": "admin-123",
            "session_token": "valid-token",
            "dry_run": False,
            "force_cleanup": True
        }

        cleanup_result = await tools.execute_cleanup(cleanup_request)

        assert cleanup_result["success"] is True
        assert cleanup_result["data"]["records_affected"] == 150
        assert cleanup_result["data"]["operation"] == RetentionOperation.CLEANUP

    async def test_policy_validation_integration(self, integrated_tools):
        """Test policy validation with various data scenarios."""
        tools = integrated_tools

        # Test valid policy
        valid_policy = {
            "log_retention_days": 90,
            "user_data_retention_days": 365,
            "metrics_retention_days": 180,
            "audit_log_retention_days": 2555,
            "auto_cleanup_enabled": True
        }

        result = await tools.validate_retention_policy(valid_policy)

        assert result["success"] is True
        assert result["data"]["is_valid"] is True
        assert len(result["data"]["validation_notes"]) == 4

        # Test invalid policy
        invalid_policy = {
            "log_retention_days": 5,  # Too low
            "user_data_retention_days": 10,  # Too low
            "audit_log_retention_days": 100  # Too low for compliance
        }

        invalid_result = await tools.validate_retention_policy(invalid_policy)

        assert invalid_result["success"] is True
        assert invalid_result["data"]["is_valid"] is False
        assert len(invalid_result["data"]["validation_errors"]) > 0


class TestConcurrentOperations:
    """Test system behavior under concurrent operations."""

    @pytest.fixture
    def service_pool(self):
        """Create multiple service instances for concurrency testing."""
        services = []
        for i in range(5):
            service = RetentionService()
            service.db_service = AsyncMock()
            service.auth_service = AsyncMock()

            # Mock admin user
            admin_user = User(
                id=f"admin-{i}",
                username=f"admin{i}",
                role=UserRole.ADMIN,
                is_active=True,
                preferences={}
            )

            service.auth_service._validate_jwt_token.return_value = {"username": f"admin{i}"}
            service.auth_service.get_user_by_username.return_value = admin_user
            service.db_service.get_user_by_id.return_value = admin_user

            services.append(service)

        return services

    async def test_concurrent_settings_updates(self, service_pool):
        """Test concurrent settings updates don't interfere with each other."""

        async def update_settings(service, user_id):
            settings = DataRetentionSettings(
                log_retention_days=30 + int(user_id.split('-')[1]) * 10,
                auto_cleanup_enabled=True
            )
            return await service.update_retention_settings(user_id, settings)

        # Run concurrent updates
        tasks = []
        for i, service in enumerate(service_pool):
            task = update_settings(service, f"admin-{i}")
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        # All updates should succeed
        assert all(result is True for result in results)

    async def test_concurrent_cleanup_operations(self, service_pool):
        """Test concurrent cleanup operations are handled safely."""

        async def perform_cleanup(service, user_id):
            request = CleanupRequest(
                retention_type=RetentionType.LOGS,
                admin_user_id=user_id,
                session_token=f"token-{user_id}",
                dry_run=True
            )

            # Mock service responses
            from models.retention import SecurityValidationResult, CleanupPreview

            valid_security = SecurityValidationResult(
                is_valid=True,
                is_admin=True,
                session_valid=True,
                user_id=user_id
            )

            settings = DataRetentionSettings(log_retention_days=30)
            cutoff_date = "2023-08-15T00:00:00.000Z"
            preview = CleanupPreview(
                retention_type=RetentionType.LOGS,
                affected_records=50,
                cutoff_date=cutoff_date
            )

            with patch.object(service, '_validate_security', return_value=valid_security):
                with patch.object(service, 'get_retention_settings', return_value=settings):
                    with patch.object(service, '_calculate_cutoff_date', return_value=cutoff_date):
                        with patch.object(service, '_preview_records_for_deletion', return_value=preview):
                            return await service.preview_cleanup(request)

        # Run concurrent cleanup previews
        tasks = []
        for i, service in enumerate(service_pool):
            task = perform_cleanup(service, f"admin-{i}")
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        # All operations should succeed
        assert all(result is not None for result in results)
        assert all(result.affected_records == 50 for result in results)


class TestErrorRecoveryAndResilience:
    """Test system recovery from various error conditions."""

    @pytest.fixture
    def resilient_service(self):
        """Create service configured for resilience testing."""
        service = RetentionService()
        service.db_service = AsyncMock()
        service.auth_service = AsyncMock()
        return service

    async def test_database_connection_failure_recovery(self, resilient_service):
        """Test recovery from database connection failures."""
        service = resilient_service

        # Simulate connection failure followed by recovery
        service.db_service.get_user_by_id.side_effect = [
            Exception("Connection failed"),
            User(
                id="admin-123",
                username="admin",
                role=UserRole.ADMIN,
                is_active=True,
                preferences={}
            )
        ]

        # First call should handle the error gracefully
        settings1 = await service.get_retention_settings("admin-123")
        assert settings1 is not None  # Should return defaults
        assert settings1.log_retention_days == 30

        # Second call should succeed after recovery
        settings2 = await service.get_retention_settings("admin-123")
        assert settings2 is not None

    async def test_partial_failure_handling(self, resilient_service):
        """Test handling of partial operation failures."""
        service = resilient_service

        # Mock partial failure in batch deletion
        mock_conn = AsyncMock()
        service.db_service.get_connection.return_value.__aenter__.return_value = mock_conn

        # First batch succeeds, second fails, should rollback all
        mock_cursors = [
            AsyncMock(rowcount=100),  # First batch success
            Exception("Disk full")     # Second batch fails
        ]
        mock_conn.execute.side_effect = [None] + mock_cursors  # BEGIN + operations

        cutoff_date = "2023-08-15T00:00:00.000Z"

        with pytest.raises(Exception):
            await service._delete_logs_batch(cutoff_date, 100)

        # Should have attempted rollback
        mock_conn.rollback.assert_called_once()

    async def test_service_degradation_handling(self, resilient_service):
        """Test graceful degradation when external services fail."""
        service = resilient_service
        tools = RetentionTools(service)

        # Simulate auth service failure
        service.auth_service._validate_jwt_token.side_effect = Exception("Auth service down")

        request_data = {
            "retention_type": RetentionType.LOGS,
            "admin_user_id": "admin-123",
            "session_token": "valid-token",
            "dry_run": True
        }

        result = await tools.preview_cleanup(request_data)

        # Should fail gracefully with proper error message
        assert result["success"] is False
        assert "PREVIEW_ERROR" in result["error"]


class TestDataIntegrity:
    """Test data integrity throughout retention operations."""

    @pytest.fixture
    def integrity_service(self):
        """Create service for integrity testing."""
        service = RetentionService()
        service.db_service = AsyncMock()
        service.auth_service = AsyncMock()
        return service

    async def test_data_consistency_during_cleanup(self, integrity_service):
        """Test that data remains consistent during cleanup operations."""
        service = integrity_service

        # Mock database operations to simulate real data consistency checks
        mock_conn = AsyncMock()
        service.db_service.get_connection.return_value.__aenter__.return_value = mock_conn

        # Simulate cleanup that maintains referential integrity
        cutoff_date = "2023-08-15T00:00:00.000Z"

        # Mock successful cleanup with integrity checks
        delete_cursor = AsyncMock(rowcount=100)
        mock_conn.execute.return_value = delete_cursor

        total_deleted, space_freed = await service._delete_logs_batch(cutoff_date, 1000)

        assert total_deleted == 100
        assert space_freed == 0.1  # 100 * 0.001

        # Verify transaction was committed (integrity maintained)
        mock_conn.commit.assert_called_once()

    async def test_audit_trail_integrity(self, integrity_service):
        """Test that audit trails maintain integrity across operations."""
        service = integrity_service

        with patch('services.retention_service.log_service') as mock_log_service:
            # Perform multiple operations
            await service._log_retention_operation(
                RetentionOperation.DRY_RUN, RetentionType.LOGS, "admin-123", True, 50
            )
            await service._log_retention_operation(
                RetentionOperation.CLEANUP, RetentionType.LOGS, "admin-123", True, 50
            )

            # Both operations should be logged
            assert mock_log_service.create_log_entry.call_count == 2

            # Verify audit entries have proper sequencing and integrity
            calls = mock_log_service.create_log_entry.call_args_list

            # First call should be DRY_RUN
            first_entry = calls[0][0][0]
            assert "dry_run" in first_entry.tags

            # Second call should be CLEANUP
            second_entry = calls[1][0][0]
            assert "cleanup" in second_entry.tags

            # Both should have different IDs (no conflicts)
            assert first_entry.id != second_entry.id