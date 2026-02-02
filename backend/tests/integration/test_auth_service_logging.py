"""
Integration test for auth service logging.

Tests the actual _log_security_event method with a real database.
"""

import pytest
from datetime import datetime, UTC
from pathlib import Path
import sys
import os

SRC_PATH = Path(__file__).resolve().parents[2] / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


class TestAuthServiceLogging:
    """Test auth service logging with real database."""

    @pytest.mark.asyncio
    async def test_log_security_event_writes_to_database(self):
        """Test that _log_security_event actually writes to the database."""
        # Set up the database path
        os.environ["DATA_DIRECTORY"] = str(Path(__file__).resolve().parents[2] / "data")

        from database.connection import db_manager
        from services.service_log import log_service
        from services.auth_service import AuthService

        print("\n=== Testing Auth Service Logging ===")
        print(f"Database path: {db_manager.database_path}")

        # Clear any existing logs for clean test
        try:
            initial_logs = await log_service.get_logs()
            print(f"Initial log count: {len(initial_logs)}")
        except Exception as e:
            print(f"Error getting initial logs: {e}")
            initial_logs = []

        # Create auth service
        auth_service = AuthService(
            jwt_secret="test-secret-key-for-integration-testing"
        )

        # Call _log_security_event directly
        print("\nCalling _log_security_event...")
        try:
            await auth_service._log_security_event(
                event_type="LOGIN",
                username="integration_test_user",
                success=True,
                client_ip="192.168.1.100",
                user_agent="Integration Test"
            )
            print("_log_security_event completed without error")
        except Exception as e:
            print(f"_log_security_event raised exception: {e}")
            import traceback
            traceback.print_exc()
            pytest.fail(f"_log_security_event failed: {e}")

        # Check if the log was created
        print("\nRetrieving logs...")
        logs = await log_service.get_logs()
        print(f"Final log count: {len(logs)}")

        # Find our log entry (source is "auth" as set in _log_security_event)
        security_logs = [
            entry for entry in logs
            if entry.source == "auth" and "integration_test_user" in entry.message
        ]
        print(f"Security logs for integration_test_user: {len(security_logs)}")

        for log in security_logs:
            print(f"  - {log.id}: {log.message}")

        assert len(security_logs) > 0, "Security log entry was not created!"

    @pytest.mark.asyncio
    async def test_verify_log_service_instance_in_auth_service(self):
        """Verify auth_service uses the correct log_service instance."""
        from services import auth_service as auth_module
        from services.service_log import log_service

        print("\n=== Checking log_service instance ===")
        print(f"log_service in auth_service module: {auth_module.log_service}")
        print(f"global log_service: {log_service}")
        print(f"Same instance: {auth_module.log_service is log_service}")

        # They should be the same instance
        assert auth_module.log_service is log_service, "Different log_service instances!"

    @pytest.mark.asyncio
    async def test_log_entry_model_conversion(self):
        """Test that LogEntry can be properly converted to table model."""
        from models.log import LogEntry
        import uuid

        log_entry = LogEntry(
            id=f"test-{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now(UTC),
            level="INFO",
            source="auth_service",
            message="Test message",
            tags=["security", "authentication"],
            metadata={"username": "test", "success": True}
        )

        # Convert to table model
        table_model = log_entry.to_table_model()

        print("\n=== LogEntry to Table Model ===")
        print(f"id: {table_model.id}")
        print(f"timestamp: {table_model.timestamp}")
        print(f"level: {table_model.level}")
        print(f"source: {table_model.source}")
        print(f"message: {table_model.message}")
        print(f"tags: {table_model.tags}")
        print(f"extra_data: {table_model.extra_data}")

        assert table_model.id == log_entry.id
        assert table_model.message == log_entry.message
        assert table_model.tags is not None
        assert table_model.extra_data is not None

    @pytest.mark.asyncio
    async def test_database_session_commit(self):
        """Test that database sessions are properly committed."""
        os.environ["DATA_DIRECTORY"] = str(Path(__file__).resolve().parents[2] / "data")

        from database.connection import db_manager
        from sqlalchemy import text
        import uuid

        await db_manager.initialize()

        test_id = f"commit-test-{uuid.uuid4().hex[:8]}"

        print("\n=== Testing Database Commit ===")
        print(f"Test ID: {test_id}")

        # Insert directly using raw SQL
        async with db_manager.get_session() as session:
            await session.execute(
                text("""
                    INSERT INTO log_entries (id, timestamp, level, source, message, tags, extra_data, created_at)
                    VALUES (:id, :timestamp, :level, :source, :message, :tags, :extra_data, :created_at)
                """),
                {
                    "id": test_id,
                    "timestamp": datetime.now(UTC).isoformat(),
                    "level": "DEBUG",
                    "source": "commit_test",
                    "message": "Testing commit",
                    "tags": "[]",
                    "extra_data": "{}",
                    "created_at": datetime.now(UTC).isoformat()
                }
            )
            # Session should auto-commit on exit

        # Verify in a new session
        async with db_manager.get_session() as session:
            result = await session.execute(
                text("SELECT id, message FROM log_entries WHERE id = :id"),
                {"id": test_id}
            )
            row = result.fetchone()

            if row:
                print(f"Found: {row}")
            else:
                print("NOT FOUND - commit failed!")

            assert row is not None, "Entry was not committed!"
