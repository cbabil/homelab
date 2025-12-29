"""
Integration tests for authentication logging.

These tests verify that logging actually works end-to-end with a real database.
"""

import pytest
import asyncio
import tempfile
import os
from datetime import datetime, UTC
from pathlib import Path
import sys

SRC_PATH = Path(__file__).resolve().parents[2] / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


class TestLogServiceRealDatabase:
    """Test log_service with a real SQLite database."""

    @pytest.fixture
    async def temp_database(self):
        """Create a temporary database for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Set the environment variable
            os.environ["DATA_DIRECTORY"] = tmpdir

            # Reset db_manager to use new path
            from database.connection import db_manager
            db_manager.set_data_directory(tmpdir)

            # Initialize the database
            await db_manager.initialize()

            # Create tables
            from database.connection import Base
            async with db_manager.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            # Reset log_service initialized flag
            from services.service_log import log_service
            log_service._initialized = False

            yield tmpdir, db_manager

            # Cleanup
            await db_manager.engine.dispose()

    @pytest.mark.asyncio
    async def test_create_and_retrieve_log_entry(self, temp_database):
        """Test that we can create and retrieve a log entry."""
        tmpdir, db_manager = temp_database

        from services.service_log import LogService
        from models.log import LogEntry
        import uuid

        # Create a fresh log service instance
        service = LogService()

        # Create a log entry
        log_entry = LogEntry(
            id=f"test-{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now(UTC),
            level="INFO",
            source="test_integration",
            message="Test log message",
            tags=["test", "integration"],
            metadata={"test_key": "test_value"}
        )

        # Create the entry
        result = await service.create_log_entry(log_entry)

        assert result is not None
        assert result.id == log_entry.id
        assert result.message == log_entry.message

        # Retrieve all logs
        logs = await service.get_logs()

        assert len(logs) >= 1
        found = next((l for l in logs if l.id == log_entry.id), None)
        assert found is not None
        assert found.message == "Test log message"

    @pytest.mark.asyncio
    async def test_security_event_logging_full_flow(self, temp_database):
        """Test the full security event logging flow."""
        tmpdir, db_manager = temp_database

        from services.service_log import log_service
        from models.log import LogEntry
        import uuid

        # Simulate what _log_security_event does
        log_entry = LogEntry(
            id=f"sec-{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now(UTC),
            level="INFO",
            source="auth_service",
            message="LOGIN successful for user: testuser from 127.0.0.1",
            tags=["security", "authentication", "login", "success"],
            metadata={
                "username": "testuser",
                "event_type": "LOGIN",
                "success": True,
                "client_ip": "127.0.0.1",
                "user_agent": "test",
                "timestamp": datetime.now(UTC).isoformat()
            }
        )

        # Create the log entry
        await log_service.create_log_entry(log_entry)

        # Verify it was stored
        logs = await log_service.get_logs()

        security_logs = [l for l in logs if "security" in l.tags]
        assert len(security_logs) >= 1

        found = next((l for l in logs if l.id == log_entry.id), None)
        assert found is not None
        assert "LOGIN successful" in found.message

    @pytest.mark.asyncio
    async def test_verify_database_paths_match(self, temp_database):
        """Verify that log_service and db_manager use the same database."""
        tmpdir, db_manager = temp_database

        from services.service_log import log_service
        from database.connection import db_manager as global_db_manager

        # Both should point to the same database
        print(f"db_manager path: {db_manager.database_path}")
        print(f"global_db_manager path: {global_db_manager.database_path}")
        print(f"temp dir: {tmpdir}")

        assert db_manager.database_path == global_db_manager.database_path
        assert tmpdir in db_manager.database_path


class TestDatabasePathConfiguration:
    """Test that database paths are configured correctly."""

    def test_data_directory_environment_variable(self):
        """Test that DATA_DIRECTORY env var is respected."""
        import tempfile
        from database.connection import DatabaseManager

        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ["DATA_DIRECTORY"] = tmpdir

            manager = DatabaseManager()
            # Should use the env var path
            assert tmpdir in manager.database_path

            del os.environ["DATA_DIRECTORY"]

    def test_set_data_directory(self):
        """Test that set_data_directory updates paths correctly."""
        import tempfile
        from database.connection import DatabaseManager

        manager = DatabaseManager()
        original_path = manager.database_path

        with tempfile.TemporaryDirectory() as tmpdir:
            manager.set_data_directory(tmpdir)

            assert tmpdir in manager.database_path
            assert manager.database_path != original_path


class TestProductionDatabasePath:
    """Test the actual production database path configuration."""

    def test_production_data_directory(self):
        """Check what database path would be used in production."""
        from database.connection import db_manager

        print(f"\n=== Production Database Configuration ===")
        print(f"Data directory: {db_manager.data_directory}")
        print(f"Database path: {db_manager.database_path}")
        print(f"Database URL: {db_manager.database_url}")

        # Verify the path exists or can be created
        data_dir = Path(db_manager.data_directory)
        print(f"Data directory exists: {data_dir.exists()}")

        if data_dir.exists():
            db_file = Path(db_manager.database_path)
            print(f"Database file exists: {db_file.exists()}")

            if db_file.exists():
                # Check tables in the database
                import sqlite3
                conn = sqlite3.connect(str(db_file))
                cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                conn.close()
                print(f"Tables in database: {tables}")

                # Check if log_entries table exists
                assert "log_entries" in tables, f"log_entries table missing! Tables: {tables}"

    @pytest.mark.asyncio
    async def test_log_service_writes_to_production_db(self):
        """Verify log_service can write to the production database."""
        # Only run this if the production database exists
        from database.connection import db_manager

        db_path = Path(db_manager.database_path)
        if not db_path.exists():
            pytest.skip("Production database does not exist")

        from services.service_log import log_service
        from models.log import LogEntry
        import uuid

        # Create a test entry
        test_id = f"test-{uuid.uuid4().hex[:8]}"
        log_entry = LogEntry(
            id=test_id,
            timestamp=datetime.now(UTC),
            level="DEBUG",
            source="integration_test",
            message="Integration test log entry",
            tags=["test"],
            metadata={"test": True}
        )

        try:
            result = await log_service.create_log_entry(log_entry)
            print(f"\nCreated log entry: {result.id}")

            # Verify it was stored
            logs = await log_service.get_logs()
            print(f"Total logs: {len(logs)}")

            found = next((l for l in logs if l.id == test_id), None)
            assert found is not None, f"Log entry {test_id} not found in database"
            print(f"Found log entry: {found.id} - {found.message}")

        except Exception as e:
            pytest.fail(f"Failed to write log entry: {e}")
