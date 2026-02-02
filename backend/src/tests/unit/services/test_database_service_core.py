"""
Unit tests for services/database_service.py - Core initialization and delegation.

Tests initialization, property access, and delegation to specialized services.
"""

import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def mock_connection():
    """Create mock DatabaseConnection."""
    conn = MagicMock()
    conn.path = "/path/to/tomo.db"
    return conn


@pytest.fixture
def mock_services():
    """Create mocks for all specialized services."""
    return {
        "user": MagicMock(),
        "server": MagicMock(),
        "session": MagicMock(),
        "app": MagicMock(),
        "metrics": MagicMock(),
        "system": MagicMock(),
        "export": MagicMock(),
        "schema": MagicMock(),
    }


class TestDatabaseServiceInit:
    """Tests for DatabaseService initialization."""

    def test_init_without_arguments(self):
        """DatabaseService should initialize with default path."""
        with patch("services.database_service.DatabaseConnection") as MockConn, \
             patch("services.database_service.UserDatabaseService"), \
             patch("services.database_service.ServerDatabaseService"), \
             patch("services.database_service.SessionDatabaseService"), \
             patch("services.database_service.AppDatabaseService"), \
             patch("services.database_service.MetricsDatabaseService"), \
             patch("services.database_service.SystemDatabaseService"), \
             patch("services.database_service.ExportDatabaseService"), \
             patch("services.database_service.SchemaInitializer"):
            from services.database_service import DatabaseService
            DatabaseService()
            MockConn.assert_called_once_with(None, None)

    def test_init_with_db_path(self, tmp_path):
        """DatabaseService should accept db_path."""
        db_file = tmp_path / "test.db"
        with patch("services.database_service.DatabaseConnection") as MockConn, \
             patch("services.database_service.UserDatabaseService"), \
             patch("services.database_service.ServerDatabaseService"), \
             patch("services.database_service.SessionDatabaseService"), \
             patch("services.database_service.AppDatabaseService"), \
             patch("services.database_service.MetricsDatabaseService"), \
             patch("services.database_service.SystemDatabaseService"), \
             patch("services.database_service.ExportDatabaseService"), \
             patch("services.database_service.SchemaInitializer"):
            from services.database_service import DatabaseService
            DatabaseService(db_path=db_file)
            MockConn.assert_called_once_with(db_file, None)

    def test_init_with_data_directory(self, tmp_path):
        """DatabaseService should accept data_directory."""
        with patch("services.database_service.DatabaseConnection") as MockConn, \
             patch("services.database_service.UserDatabaseService"), \
             patch("services.database_service.ServerDatabaseService"), \
             patch("services.database_service.SessionDatabaseService"), \
             patch("services.database_service.AppDatabaseService"), \
             patch("services.database_service.MetricsDatabaseService"), \
             patch("services.database_service.SystemDatabaseService"), \
             patch("services.database_service.ExportDatabaseService"), \
             patch("services.database_service.SchemaInitializer"):
            from services.database_service import DatabaseService
            DatabaseService(data_directory=tmp_path)
            MockConn.assert_called_once_with(None, tmp_path)

    def test_init_creates_all_services(self):
        """DatabaseService should create all specialized services."""
        with patch("services.database_service.DatabaseConnection") as MockConn, \
             patch("services.database_service.UserDatabaseService") as MockUser, \
             patch("services.database_service.ServerDatabaseService") as MockServer, \
             patch("services.database_service.SessionDatabaseService") as MockSession, \
             patch("services.database_service.AppDatabaseService") as MockApp, \
             patch("services.database_service.MetricsDatabaseService") as MockMetrics, \
             patch("services.database_service.SystemDatabaseService") as MockSystem, \
             patch("services.database_service.ExportDatabaseService") as MockExport, \
             patch("services.database_service.SchemaInitializer") as MockSchema:
            from services.database_service import DatabaseService

            mock_conn = MagicMock()
            MockConn.return_value = mock_conn

            db_service = DatabaseService()

            MockUser.assert_called_once_with(mock_conn)
            MockServer.assert_called_once_with(mock_conn)
            MockSession.assert_called_once_with(mock_conn)
            MockApp.assert_called_once_with(mock_conn)
            MockMetrics.assert_called_once_with(mock_conn)
            MockSystem.assert_called_once_with(mock_conn)
            MockExport.assert_called_once_with(mock_conn)
            MockSchema.assert_called_once_with(mock_conn)

            assert db_service._user is MockUser.return_value
            assert db_service._server is MockServer.return_value
            assert db_service._session is MockSession.return_value
            assert db_service._app is MockApp.return_value
            assert db_service._metrics is MockMetrics.return_value
            assert db_service._system is MockSystem.return_value
            assert db_service._export is MockExport.return_value
            assert db_service._schema is MockSchema.return_value


class TestDbPathProperty:
    """Tests for db_path property."""

    def test_db_path_returns_connection_path(self):
        """db_path should return connection's path."""
        with patch("services.database_service.DatabaseConnection") as MockConn, \
             patch("services.database_service.UserDatabaseService"), \
             patch("services.database_service.ServerDatabaseService"), \
             patch("services.database_service.SessionDatabaseService"), \
             patch("services.database_service.AppDatabaseService"), \
             patch("services.database_service.MetricsDatabaseService"), \
             patch("services.database_service.SystemDatabaseService"), \
             patch("services.database_service.ExportDatabaseService"), \
             patch("services.database_service.SchemaInitializer"):
            from services.database_service import DatabaseService

            mock_conn = MagicMock()
            mock_conn.path = "/test/path/tomo.db"
            MockConn.return_value = mock_conn

            db_service = DatabaseService()
            assert db_service.db_path == "/test/path/tomo.db"


class TestGetConnection:
    """Tests for get_connection method."""

    def test_get_connection_delegates(self):
        """get_connection should delegate to connection manager."""
        with patch("services.database_service.DatabaseConnection") as MockConn, \
             patch("services.database_service.UserDatabaseService"), \
             patch("services.database_service.ServerDatabaseService"), \
             patch("services.database_service.SessionDatabaseService"), \
             patch("services.database_service.AppDatabaseService"), \
             patch("services.database_service.MetricsDatabaseService"), \
             patch("services.database_service.SystemDatabaseService"), \
             patch("services.database_service.ExportDatabaseService"), \
             patch("services.database_service.SchemaInitializer"):
            from services.database_service import DatabaseService

            mock_conn = MagicMock()
            mock_context = MagicMock()
            mock_conn.get_connection.return_value = mock_context
            MockConn.return_value = mock_conn

            db_service = DatabaseService()
            result = db_service.get_connection()

            mock_conn.get_connection.assert_called_once()
            assert result is mock_context


class TestModuleExports:
    """Tests for module-level exports."""

    def test_exports_database_service(self):
        """Module should export DatabaseService."""
        from services.database_service import DatabaseService
        assert DatabaseService is not None

    def test_exports_allowed_server_columns(self):
        """Module should export ALLOWED_SERVER_COLUMNS."""
        from services.database_service import ALLOWED_SERVER_COLUMNS
        assert isinstance(ALLOWED_SERVER_COLUMNS, frozenset)

    def test_exports_allowed_installation_columns(self):
        """Module should export ALLOWED_INSTALLATION_COLUMNS."""
        from services.database_service import ALLOWED_INSTALLATION_COLUMNS
        assert isinstance(ALLOWED_INSTALLATION_COLUMNS, frozenset)

    def test_exports_allowed_system_info_columns(self):
        """Module should export ALLOWED_SYSTEM_INFO_COLUMNS."""
        from services.database_service import ALLOWED_SYSTEM_INFO_COLUMNS
        assert isinstance(ALLOWED_SYSTEM_INFO_COLUMNS, frozenset)

    def test_all_exports(self):
        """Module __all__ should list expected exports."""
        from services import database_service
        assert "DatabaseService" in database_service.__all__
        assert "ALLOWED_SERVER_COLUMNS" in database_service.__all__
        assert "ALLOWED_INSTALLATION_COLUMNS" in database_service.__all__
        assert "ALLOWED_SYSTEM_INFO_COLUMNS" in database_service.__all__
