"""
Unit tests for authentication logging functionality.

Tests that security events (login success/failure) are properly logged
to the database via the log_service.
"""

import pytest
from datetime import datetime, UTC
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

import sys
from pathlib import Path
SRC_PATH = Path(__file__).resolve().parents[2] / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from models.log import LogEntry
from models.auth import User, UserRole, LoginCredentials


class TestLogSecurityEvent:
    """Test the _log_security_event method in AuthService."""

    @pytest.fixture
    def mock_log_service(self):
        """Create a mock log service."""
        mock = AsyncMock()
        mock.create_log_entry = AsyncMock(return_value=None)
        return mock

    @pytest.fixture
    def mock_db_service(self):
        """Create a mock database service."""
        mock = AsyncMock()
        mock.get_user_by_username = AsyncMock(return_value=None)
        mock.get_user_password_hash = AsyncMock(return_value=None)
        return mock

    @pytest.fixture
    def auth_service(self, mock_db_service):
        """Create an AuthService instance with mocked dependencies."""
        from services.auth_service import AuthService
        service = AuthService(
            jwt_secret="test-secret-key-for-testing-purposes",
            db_service=mock_db_service
        )
        return service

    @pytest.mark.asyncio
    async def test_log_security_event_success(self, auth_service, mock_log_service):
        """Test that successful login events are logged correctly."""
        with patch('services.auth_service.log_service', mock_log_service):
            await auth_service._log_security_event(
                event_type="LOGIN",
                username="admin",
                success=True,
                client_ip="127.0.0.1",
                user_agent="Mozilla/5.0"
            )

            # Verify log_service.create_log_entry was called
            mock_log_service.create_log_entry.assert_called_once()

            # Get the LogEntry that was passed
            call_args = mock_log_service.create_log_entry.call_args
            log_entry = call_args[0][0]

            # Verify the log entry properties
            assert isinstance(log_entry, LogEntry)
            assert log_entry.level == "INFO"
            assert log_entry.source == "auth_service"
            assert "LOGIN successful" in log_entry.message
            assert "admin" in log_entry.message
            assert "127.0.0.1" in log_entry.message
            assert "security" in log_entry.tags
            assert "authentication" in log_entry.tags
            assert "success" in log_entry.tags
            assert log_entry.metadata["username"] == "admin"
            assert log_entry.metadata["success"] is True
            assert log_entry.metadata["client_ip"] == "127.0.0.1"

    @pytest.mark.asyncio
    async def test_log_security_event_failure(self, auth_service, mock_log_service):
        """Test that failed login events are logged correctly."""
        with patch('services.auth_service.log_service', mock_log_service):
            await auth_service._log_security_event(
                event_type="LOGIN",
                username="baduser",
                success=False,
                client_ip="192.168.1.100",
                user_agent="curl/7.68.0"
            )

            # Verify log_service.create_log_entry was called
            mock_log_service.create_log_entry.assert_called_once()

            # Get the LogEntry that was passed
            call_args = mock_log_service.create_log_entry.call_args
            log_entry = call_args[0][0]

            # Verify the log entry properties
            assert log_entry.level == "WARNING"
            assert "LOGIN failed" in log_entry.message
            assert "baduser" in log_entry.message
            assert "192.168.1.100" in log_entry.message
            assert "failure" in log_entry.tags

    @pytest.mark.asyncio
    async def test_log_security_event_without_ip(self, auth_service, mock_log_service):
        """Test that logging works without IP address."""
        with patch('services.auth_service.log_service', mock_log_service):
            await auth_service._log_security_event(
                event_type="LOGIN",
                username="testuser",
                success=True
            )

            mock_log_service.create_log_entry.assert_called_once()
            call_args = mock_log_service.create_log_entry.call_args
            log_entry = call_args[0][0]

            # IP should not be in message when not provided
            assert "from" not in log_entry.message or log_entry.metadata["client_ip"] == "unknown"

    @pytest.mark.asyncio
    async def test_log_security_event_exception_handling(self, auth_service, mock_log_service):
        """Test that exceptions in logging don't crash the auth service."""
        mock_log_service.create_log_entry.side_effect = Exception("Database error")

        with patch('services.auth_service.log_service', mock_log_service):
            # Should not raise an exception
            await auth_service._log_security_event(
                event_type="LOGIN",
                username="admin",
                success=True
            )
            # The method should complete without raising


class TestLogServiceIntegration:
    """Test the log_service.create_log_entry directly."""

    @pytest.fixture
    def mock_db_manager(self):
        """Create a mock database manager."""
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.close = AsyncMock()

        # Create a context manager mock
        mock_cm = AsyncMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_session)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        mock_manager = MagicMock()
        mock_manager.get_session = MagicMock(return_value=mock_cm)

        return mock_manager, mock_session

    @pytest.mark.asyncio
    async def test_create_log_entry_calls_session_add(self, mock_db_manager):
        """Test that create_log_entry adds the entry to the session."""
        mock_manager, mock_session = mock_db_manager

        with patch('services.service_log.db_manager', mock_manager):
            with patch('services.service_log.initialize_logs_database', AsyncMock()):
                from services.service_log import LogService

                service = LogService()
                service._initialized = True  # Skip initialization

                log_entry = LogEntry(
                    id=f"log-{uuid.uuid4().hex[:8]}",
                    timestamp=datetime.now(UTC),
                    level="INFO",
                    source="test",
                    message="Test message",
                    tags=["test"],
                    metadata={"key": "value"}
                )

                # Mock the table model conversion
                with patch.object(log_entry, 'to_table_model') as mock_to_table:
                    mock_table_entry = MagicMock()
                    mock_to_table.return_value = mock_table_entry

                    await service.create_log_entry(log_entry)

                    # Verify session.add was called
                    mock_session.add.assert_called_once_with(mock_table_entry)
                    mock_session.flush.assert_called_once()


class TestAuthenticateUserLogging:
    """Test that authenticate_user properly logs security events."""

    @pytest.fixture
    def mock_db_service(self):
        """Create a mock database service with a valid user."""
        mock = AsyncMock()

        # Create a valid user
        user = User(
            id="user-123",
            username="admin",
            email="admin@homelab.local",
            role=UserRole.ADMIN,
            last_login=datetime.now(UTC).isoformat(),
            is_active=True
        )

        mock.get_user_by_username = AsyncMock(return_value=user)
        mock.get_user_password_hash = AsyncMock(return_value="$2b$12$hashedpassword")
        mock.update_user_last_login = AsyncMock()
        return mock

    @pytest.fixture
    def auth_service(self, mock_db_service):
        """Create an AuthService instance."""
        from services.auth_service import AuthService
        return AuthService(
            jwt_secret="test-secret-key-for-testing-purposes",
            db_service=mock_db_service
        )

    @pytest.mark.asyncio
    async def test_authenticate_user_logs_success(self, auth_service, mock_db_service):
        """Test that successful authentication logs a success event."""
        mock_log_service = AsyncMock()
        mock_log_service.create_log_entry = AsyncMock()

        with patch('services.auth_service.log_service', mock_log_service):
            with patch('services.auth_service.verify_password', return_value=True):
                with patch('services.auth_service.generate_jwt_token', return_value="fake-token"):
                    credentials = LoginCredentials(
                        username="admin",
                        password="correctpassword"
                    )

                    result = await auth_service.authenticate_user(
                        credentials,
                        client_ip="127.0.0.1"
                    )

                    # Should have logged a success event
                    assert mock_log_service.create_log_entry.called
                    call_args = mock_log_service.create_log_entry.call_args
                    log_entry = call_args[0][0]

                    assert log_entry.level == "INFO"
                    assert "successful" in log_entry.message
                    assert log_entry.metadata["success"] is True

    @pytest.mark.asyncio
    async def test_authenticate_user_logs_failure_invalid_password(self, auth_service, mock_db_service):
        """Test that failed authentication (wrong password) logs a failure event."""
        mock_log_service = AsyncMock()
        mock_log_service.create_log_entry = AsyncMock()

        with patch('services.auth_service.log_service', mock_log_service):
            with patch('services.auth_service.verify_password', return_value=False):
                credentials = LoginCredentials(
                    username="admin",
                    password="wrongpassword"
                )

                result = await auth_service.authenticate_user(
                    credentials,
                    client_ip="127.0.0.1"
                )

                assert result is None
                assert mock_log_service.create_log_entry.called

                call_args = mock_log_service.create_log_entry.call_args
                log_entry = call_args[0][0]

                assert log_entry.level == "WARNING"
                assert "failed" in log_entry.message
                assert log_entry.metadata["success"] is False

    @pytest.mark.asyncio
    async def test_authenticate_user_logs_failure_user_not_found(self, auth_service, mock_db_service):
        """Test that failed authentication (user not found) logs a failure event."""
        mock_db_service.get_user_by_username = AsyncMock(return_value=None)

        mock_log_service = AsyncMock()
        mock_log_service.create_log_entry = AsyncMock()

        with patch('services.auth_service.log_service', mock_log_service):
            credentials = LoginCredentials(
                username="nonexistent",
                password="somepassword"
            )

            result = await auth_service.authenticate_user(
                credentials,
                client_ip="127.0.0.1"
            )

            assert result is None
            assert mock_log_service.create_log_entry.called

            call_args = mock_log_service.create_log_entry.call_args
            log_entry = call_args[0][0]

            assert "failed" in log_entry.message
            assert log_entry.metadata["success"] is False


class TestLogServiceDatabasePath:
    """Test that log_service uses the correct database path."""

    @pytest.mark.asyncio
    async def test_log_service_database_path_matches_data_directory(self):
        """Verify log_service writes to the same database as auth_service."""
        from database.connection import db_manager
        from services.service_log import log_service

        # The log_service should use db_manager which should have the correct path
        expected_path = db_manager.database_path

        # Verify it's pointing to the expected location
        assert "homelab.db" in expected_path

    @pytest.mark.asyncio
    async def test_log_entries_table_exists(self):
        """Test that the log_entries table can be created and used."""
        import tempfile
        import os
        from database.connection import DatabaseManager
        from sqlalchemy import text

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test database manager
            test_manager = DatabaseManager(data_directory=tmpdir)
            await test_manager.initialize()

            # Create the log_entries table
            from database.connection import Base
            async with test_manager.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            # Verify table exists
            async with test_manager.get_session() as session:
                result = await session.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table' AND name='log_entries'")
                )
                tables = result.fetchall()
                assert len(tables) == 1
                assert tables[0][0] == "log_entries"

            await test_manager.engine.dispose()
