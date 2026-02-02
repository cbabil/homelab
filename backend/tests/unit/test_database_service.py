"""
Unit tests for services/database_service.py

Tests for DatabaseService facade that delegates to specialized database services.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import services.database_service as db_module
from models.auth import UserRole
from services.database_service import DatabaseService


@pytest.fixture
def mock_db_connection():
    """Create mock DatabaseConnection."""
    return MagicMock()


@pytest.fixture
def mock_services():
    """Create mock specialized services."""
    return {
        "user": AsyncMock(),
        "server": AsyncMock(),
        "session": AsyncMock(),
        "app": AsyncMock(),
        "metrics": AsyncMock(),
        "system": AsyncMock(),
        "export": AsyncMock(),
        "schema": AsyncMock(),
    }


@pytest.fixture
def database_service(mock_db_connection, mock_services):
    """Create DatabaseService with mocked dependencies."""
    with patch.object(
        db_module, "DatabaseConnection", return_value=mock_db_connection
    ), patch.object(
        db_module, "UserDatabaseService", return_value=mock_services["user"]
    ), patch.object(
        db_module, "ServerDatabaseService", return_value=mock_services["server"]
    ), patch.object(
        db_module, "SessionDatabaseService", return_value=mock_services["session"]
    ), patch.object(
        db_module, "AppDatabaseService", return_value=mock_services["app"]
    ), patch.object(
        db_module, "MetricsDatabaseService", return_value=mock_services["metrics"]
    ), patch.object(
        db_module, "SystemDatabaseService", return_value=mock_services["system"]
    ), patch.object(
        db_module, "ExportDatabaseService", return_value=mock_services["export"]
    ), patch.object(
        db_module, "SchemaInitializer", return_value=mock_services["schema"]
    ):
        service = DatabaseService(db_path="/tmp/test.db")
        service._mock_services = mock_services
        return service


class TestDatabaseServiceInit:
    """Tests for DatabaseService initialization."""

    def test_init_creates_connection(self):
        """Should create database connection."""
        with patch.object(db_module, "DatabaseConnection") as mock_conn_cls, patch.object(
            db_module, "UserDatabaseService"
        ), patch.object(db_module, "ServerDatabaseService"), patch.object(
            db_module, "SessionDatabaseService"
        ), patch.object(db_module, "AppDatabaseService"), patch.object(
            db_module, "MetricsDatabaseService"
        ), patch.object(db_module, "SystemDatabaseService"), patch.object(
            db_module, "ExportDatabaseService"
        ), patch.object(db_module, "SchemaInitializer"):
            DatabaseService(db_path="/test/path.db")

            mock_conn_cls.assert_called_once_with("/test/path.db", None)

    def test_init_with_data_directory(self):
        """Should pass data_directory to connection."""
        with patch.object(db_module, "DatabaseConnection") as mock_conn_cls, patch.object(
            db_module, "UserDatabaseService"
        ), patch.object(db_module, "ServerDatabaseService"), patch.object(
            db_module, "SessionDatabaseService"
        ), patch.object(db_module, "AppDatabaseService"), patch.object(
            db_module, "MetricsDatabaseService"
        ), patch.object(db_module, "SystemDatabaseService"), patch.object(
            db_module, "ExportDatabaseService"
        ), patch.object(db_module, "SchemaInitializer"):
            DatabaseService(data_directory="/data/dir")

            mock_conn_cls.assert_called_once_with(None, "/data/dir")

    def test_init_creates_specialized_services(self):
        """Should create all specialized services."""
        with patch.object(
            db_module, "DatabaseConnection"
        ) as mock_conn_cls, patch.object(
            db_module, "UserDatabaseService"
        ) as mock_user, patch.object(
            db_module, "ServerDatabaseService"
        ) as mock_server, patch.object(
            db_module, "SessionDatabaseService"
        ) as mock_session, patch.object(
            db_module, "AppDatabaseService"
        ) as mock_app, patch.object(
            db_module, "MetricsDatabaseService"
        ) as mock_metrics, patch.object(
            db_module, "SystemDatabaseService"
        ) as mock_system, patch.object(
            db_module, "ExportDatabaseService"
        ) as mock_export, patch.object(
            db_module, "SchemaInitializer"
        ) as mock_schema:
            mock_conn = MagicMock()
            mock_conn_cls.return_value = mock_conn

            DatabaseService()

            mock_user.assert_called_once_with(mock_conn)
            mock_server.assert_called_once_with(mock_conn)
            mock_session.assert_called_once_with(mock_conn)
            mock_app.assert_called_once_with(mock_conn)
            mock_metrics.assert_called_once_with(mock_conn)
            mock_system.assert_called_once_with(mock_conn)
            mock_export.assert_called_once_with(mock_conn)
            mock_schema.assert_called_once_with(mock_conn)


class TestDbPathProperty:
    """Tests for db_path property."""

    def test_db_path_returns_connection_path(self, database_service, mock_db_connection):
        """Should return path from connection."""
        mock_db_connection.path = "/path/to/db.sqlite"

        result = database_service.db_path

        assert result == "/path/to/db.sqlite"


class TestGetConnection:
    """Tests for get_connection method."""

    def test_get_connection_delegates(self, database_service, mock_db_connection):
        """Should delegate to connection."""
        mock_ctx = MagicMock()
        mock_db_connection.get_connection.return_value = mock_ctx

        result = database_service.get_connection()

        assert result is mock_ctx
        mock_db_connection.get_connection.assert_called_once()


class TestUserMethods:
    """Tests for user-related methods."""

    @pytest.mark.asyncio
    async def test_get_user(self, database_service):
        """Should delegate to user service."""
        mock_user = MagicMock()
        database_service._mock_services["user"].get_user.return_value = mock_user

        result = await database_service.get_user(user_id="123", username="test")

        assert result is mock_user
        database_service._mock_services["user"].get_user.assert_called_once_with(
            "123", "test"
        )

    @pytest.mark.asyncio
    async def test_get_user_by_username(self, database_service):
        """Should delegate to user service."""
        mock_user = MagicMock()
        database_service._mock_services["user"].get_user_by_username.return_value = (
            mock_user
        )

        result = await database_service.get_user_by_username("testuser")

        assert result is mock_user

    @pytest.mark.asyncio
    async def test_get_user_by_id(self, database_service):
        """Should delegate to user service."""
        await database_service.get_user_by_id("user-123")

        database_service._mock_services["user"].get_user_by_id.assert_called_once_with(
            "user-123"
        )

    @pytest.mark.asyncio
    async def test_get_user_password_hash(self, database_service):
        """Should delegate to user service."""
        database_service._mock_services["user"].get_user_password_hash.return_value = (
            "hash123"
        )

        result = await database_service.get_user_password_hash("user1")

        assert result == "hash123"

    @pytest.mark.asyncio
    async def test_update_user_last_login(self, database_service):
        """Should delegate to user service."""
        await database_service.update_user_last_login("user1", "2024-01-01T00:00:00")

        database_service._mock_services[
            "user"
        ].update_user_last_login.assert_called_once_with("user1", "2024-01-01T00:00:00")

    @pytest.mark.asyncio
    async def test_get_all_users(self, database_service):
        """Should delegate to user service."""
        await database_service.get_all_users()

        database_service._mock_services["user"].get_all_users.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_user(self, database_service):
        """Should delegate to user service."""
        await database_service.create_user(
            username="new",
            password_hash="hash",
            email="test@example.com",
            role=UserRole.USER,
            preferences={"theme": "dark"},
        )

        database_service._mock_services["user"].create_user.assert_called_once_with(
            "new", "hash", "test@example.com", UserRole.USER, {"theme": "dark"}
        )

    @pytest.mark.asyncio
    async def test_update_user_password(self, database_service):
        """Should delegate to user service."""
        await database_service.update_user_password("user1", "newhash")

        database_service._mock_services[
            "user"
        ].update_user_password.assert_called_once_with("user1", "newhash")

    @pytest.mark.asyncio
    async def test_has_admin_user(self, database_service):
        """Should delegate to user service."""
        database_service._mock_services["user"].has_admin_user.return_value = True

        result = await database_service.has_admin_user()

        assert result is True

    @pytest.mark.asyncio
    async def test_update_user_preferences(self, database_service):
        """Should delegate to user service."""
        prefs = {"notifications": True}
        await database_service.update_user_preferences("user-123", prefs)

        database_service._mock_services[
            "user"
        ].update_user_preferences.assert_called_once_with("user-123", prefs)

    @pytest.mark.asyncio
    async def test_update_user_avatar(self, database_service):
        """Should delegate to user service."""
        await database_service.update_user_avatar("user-123", "avatar.png")

        database_service._mock_services[
            "user"
        ].update_user_avatar.assert_called_once_with("user-123", "avatar.png")


class TestSystemMethods:
    """Tests for system-related methods."""

    @pytest.mark.asyncio
    async def test_get_system_info(self, database_service):
        """Should delegate to system service."""
        mock_info = {"version": "1.0"}
        database_service._mock_services["system"].get_system_info.return_value = (
            mock_info
        )

        result = await database_service.get_system_info()

        assert result == mock_info

    @pytest.mark.asyncio
    async def test_is_system_setup(self, database_service):
        """Should delegate to system service."""
        database_service._mock_services["system"].is_system_setup.return_value = True

        result = await database_service.is_system_setup()

        assert result is True

    @pytest.mark.asyncio
    async def test_mark_system_setup_complete(self, database_service):
        """Should delegate to system service."""
        await database_service.mark_system_setup_complete("admin-123")

        database_service._mock_services[
            "system"
        ].mark_system_setup_complete.assert_called_once_with("admin-123")

    @pytest.mark.asyncio
    async def test_update_system_info(self, database_service):
        """Should delegate to system service."""
        await database_service.update_system_info(version="2.0", name="test")

        database_service._mock_services[
            "system"
        ].update_system_info.assert_called_once_with(version="2.0", name="test")

    @pytest.mark.asyncio
    async def test_verify_database_connection(self, database_service):
        """Should delegate to system service."""
        database_service._mock_services[
            "system"
        ].verify_database_connection.return_value = True

        result = await database_service.verify_database_connection()

        assert result is True

    @pytest.mark.asyncio
    async def test_get_component_versions(self, database_service):
        """Should delegate to system service."""
        await database_service.get_component_versions()

        database_service._mock_services[
            "system"
        ].get_component_versions.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_component_version(self, database_service):
        """Should delegate to system service."""
        await database_service.get_component_version("backend")

        database_service._mock_services[
            "system"
        ].get_component_version.assert_called_once_with("backend")

    @pytest.mark.asyncio
    async def test_update_component_version(self, database_service):
        """Should delegate to system service."""
        await database_service.update_component_version("frontend", "1.2.3")

        database_service._mock_services[
            "system"
        ].update_component_version.assert_called_once_with("frontend", "1.2.3")


class TestServerMethods:
    """Tests for server-related methods."""

    @pytest.mark.asyncio
    async def test_create_server(self, database_service):
        """Should delegate to server service."""
        await database_service.create_server(
            id="srv-1",
            name="Server 1",
            host="192.168.1.1",
            port=22,
            username="root",
            auth_type="password",
            encrypted_credentials="encrypted",
        )

        database_service._mock_services["server"].create_server.assert_called_once_with(
            "srv-1",
            "Server 1",
            "192.168.1.1",
            22,
            "root",
            "password",
            "encrypted",
        )

    @pytest.mark.asyncio
    async def test_get_server_by_id(self, database_service):
        """Should delegate to server service."""
        await database_service.get_server_by_id("srv-123")

        database_service._mock_services[
            "server"
        ].get_server_by_id.assert_called_once_with("srv-123")

    @pytest.mark.asyncio
    async def test_get_server_by_connection(self, database_service):
        """Should delegate to server service."""
        await database_service.get_server_by_connection("host", 22, "user")

        database_service._mock_services[
            "server"
        ].get_server_by_connection.assert_called_once_with("host", 22, "user")

    @pytest.mark.asyncio
    async def test_get_all_servers_from_db(self, database_service):
        """Should delegate to server service."""
        await database_service.get_all_servers_from_db()

        database_service._mock_services[
            "server"
        ].get_all_servers_from_db.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_server_credentials(self, database_service):
        """Should delegate to server service."""
        await database_service.get_server_credentials("srv-1")

        database_service._mock_services[
            "server"
        ].get_server_credentials.assert_called_once_with("srv-1")

    @pytest.mark.asyncio
    async def test_update_server_credentials(self, database_service):
        """Should delegate to server service."""
        await database_service.update_server_credentials("srv-1", "new_creds")

        database_service._mock_services[
            "server"
        ].update_server_credentials.assert_called_once_with("srv-1", "new_creds")

    @pytest.mark.asyncio
    async def test_update_server(self, database_service):
        """Should delegate to server service."""
        await database_service.update_server("srv-1", name="New Name", port=2222)

        database_service._mock_services["server"].update_server.assert_called_once_with(
            "srv-1", name="New Name", port=2222
        )

    @pytest.mark.asyncio
    async def test_delete_server(self, database_service):
        """Should delegate to server service."""
        await database_service.delete_server("srv-1")

        database_service._mock_services["server"].delete_server.assert_called_once_with(
            "srv-1"
        )


class TestInstallationMethods:
    """Tests for installation-related methods."""

    @pytest.mark.asyncio
    async def test_create_installation(self, database_service):
        """Should delegate to app service."""
        await database_service.create_installation(
            id="inst-1",
            server_id="srv-1",
            app_id="app-1",
            container_name="container",
            status="running",
            config={"port": 8080},
            installed_at="2024-01-01",
        )

        database_service._mock_services[
            "app"
        ].create_installation.assert_called_once_with(
            "inst-1",
            "srv-1",
            "app-1",
            "container",
            "running",
            {"port": 8080},
            "2024-01-01",
        )

    @pytest.mark.asyncio
    async def test_update_installation(self, database_service):
        """Should delegate to app service."""
        await database_service.update_installation("inst-1", status="stopped")

        database_service._mock_services[
            "app"
        ].update_installation.assert_called_once_with("inst-1", status="stopped")

    @pytest.mark.asyncio
    async def test_get_installation(self, database_service):
        """Should delegate to app service."""
        await database_service.get_installation("srv-1", "app-1")

        database_service._mock_services["app"].get_installation.assert_called_once_with(
            "srv-1", "app-1"
        )

    @pytest.mark.asyncio
    async def test_get_installation_by_id(self, database_service):
        """Should delegate to app service."""
        await database_service.get_installation_by_id("inst-1")

        database_service._mock_services[
            "app"
        ].get_installation_by_id.assert_called_once_with("inst-1")

    @pytest.mark.asyncio
    async def test_get_installations(self, database_service):
        """Should delegate to app service."""
        await database_service.get_installations("srv-1")

        database_service._mock_services["app"].get_installations.assert_called_once_with(
            "srv-1"
        )

    @pytest.mark.asyncio
    async def test_get_all_installations(self, database_service):
        """Should delegate to app service."""
        await database_service.get_all_installations()

        database_service._mock_services[
            "app"
        ].get_all_installations.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_installation(self, database_service):
        """Should delegate to app service."""
        await database_service.delete_installation("srv-1", "app-1")

        database_service._mock_services[
            "app"
        ].delete_installation.assert_called_once_with("srv-1", "app-1")


class TestMetricsMethods:
    """Tests for metrics-related methods."""

    @pytest.mark.asyncio
    async def test_save_server_metrics(self, database_service):
        """Should delegate to metrics service."""
        mock_metrics = MagicMock()
        await database_service.save_server_metrics(mock_metrics)

        database_service._mock_services[
            "metrics"
        ].save_server_metrics.assert_called_once_with(mock_metrics)

    @pytest.mark.asyncio
    async def test_save_container_metrics(self, database_service):
        """Should delegate to metrics service."""
        mock_metrics = MagicMock()
        await database_service.save_container_metrics(mock_metrics)

        database_service._mock_services[
            "metrics"
        ].save_container_metrics.assert_called_once_with(mock_metrics)

    @pytest.mark.asyncio
    async def test_save_activity_log(self, database_service):
        """Should delegate to metrics service."""
        mock_log = MagicMock()
        await database_service.save_activity_log(mock_log)

        database_service._mock_services[
            "metrics"
        ].save_activity_log.assert_called_once_with(mock_log)

    @pytest.mark.asyncio
    async def test_get_server_metrics(self, database_service):
        """Should delegate to metrics service."""
        await database_service.get_server_metrics("srv-1", since="2024-01-01", limit=50)

        database_service._mock_services[
            "metrics"
        ].get_server_metrics.assert_called_once_with("srv-1", "2024-01-01", 50)

    @pytest.mark.asyncio
    async def test_get_container_metrics(self, database_service):
        """Should delegate to metrics service."""
        await database_service.get_container_metrics(
            "srv-1", container_name="web", since="2024-01-01", limit=25
        )

        database_service._mock_services[
            "metrics"
        ].get_container_metrics.assert_called_once_with("srv-1", "web", "2024-01-01", 25)

    @pytest.mark.asyncio
    async def test_get_activity_logs(self, database_service):
        """Should delegate to metrics service."""
        await database_service.get_activity_logs(
            activity_types=["login"],
            user_id="user-1",
            server_id="srv-1",
            since="2024-01-01",
            until="2024-12-31",
            limit=100,
            offset=10,
        )

        database_service._mock_services[
            "metrics"
        ].get_activity_logs.assert_called_once_with(
            ["login"], "user-1", "srv-1", "2024-01-01", "2024-12-31", 100, 10
        )

    @pytest.mark.asyncio
    async def test_count_activity_logs(self, database_service):
        """Should delegate to metrics service."""
        await database_service.count_activity_logs(
            activity_types=["deploy"], since="2024-01-01"
        )

        database_service._mock_services[
            "metrics"
        ].count_activity_logs.assert_called_once_with(["deploy"], "2024-01-01")

    @pytest.mark.asyncio
    async def test_get_log_entries_count_before_date(self, database_service):
        """Should delegate to metrics service."""
        await database_service.get_log_entries_count_before_date("2024-01-01")

        database_service._mock_services[
            "metrics"
        ].get_log_entries_count_before_date.assert_called_once_with("2024-01-01")

    @pytest.mark.asyncio
    async def test_delete_log_entries_before_date(self, database_service):
        """Should delegate to metrics service."""
        await database_service.delete_log_entries_before_date("2024-01-01", 500)

        database_service._mock_services[
            "metrics"
        ].delete_log_entries_before_date.assert_called_once_with("2024-01-01", 500)


class TestExportMethods:
    """Tests for export/import methods."""

    @pytest.mark.asyncio
    async def test_export_users(self, database_service):
        """Should delegate to export service."""
        await database_service.export_users()

        database_service._mock_services["export"].export_users.assert_called_once()

    @pytest.mark.asyncio
    async def test_export_servers(self, database_service):
        """Should delegate to export service."""
        await database_service.export_servers()

        database_service._mock_services["export"].export_servers.assert_called_once()

    @pytest.mark.asyncio
    async def test_export_settings(self, database_service):
        """Should delegate to export service."""
        await database_service.export_settings()

        database_service._mock_services["export"].export_settings.assert_called_once()

    @pytest.mark.asyncio
    async def test_import_users(self, database_service):
        """Should delegate to export service."""
        users = [{"username": "user1"}]
        await database_service.import_users(users, overwrite=True)

        database_service._mock_services["export"].import_users.assert_called_once_with(
            users, True
        )

    @pytest.mark.asyncio
    async def test_import_servers(self, database_service):
        """Should delegate to export service."""
        servers = [{"name": "srv1"}]
        await database_service.import_servers(servers, overwrite=False)

        database_service._mock_services["export"].import_servers.assert_called_once_with(
            servers, False
        )

    @pytest.mark.asyncio
    async def test_import_settings(self, database_service):
        """Should delegate to export service."""
        settings = {"theme": "dark"}
        await database_service.import_settings(settings, overwrite=True)

        database_service._mock_services["export"].import_settings.assert_called_once_with(
            settings, True
        )


class TestSchemaMethods:
    """Tests for schema initialization methods."""

    @pytest.mark.asyncio
    async def test_initialize_component_versions_table(self, database_service):
        """Should delegate to schema service."""
        await database_service.initialize_component_versions_table()

        database_service._mock_services[
            "schema"
        ].initialize_component_versions_table.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_installed_apps_migrations(self, database_service):
        """Should delegate to schema service."""
        await database_service.run_installed_apps_migrations()

        database_service._mock_services[
            "schema"
        ].run_installed_apps_migrations.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_users_migrations(self, database_service):
        """Should delegate to schema service."""
        await database_service.run_users_migrations()

        database_service._mock_services[
            "schema"
        ].run_users_migrations.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_system_info_table(self, database_service):
        """Should delegate to schema service."""
        await database_service.initialize_system_info_table()

        database_service._mock_services[
            "schema"
        ].initialize_system_info_table.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_users_table(self, database_service):
        """Should delegate to schema service."""
        await database_service.initialize_users_table()

        database_service._mock_services[
            "schema"
        ].initialize_users_table.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_sessions_table(self, database_service):
        """Should delegate to schema service."""
        await database_service.initialize_sessions_table()

        database_service._mock_services[
            "schema"
        ].initialize_sessions_table.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_account_locks_table(self, database_service):
        """Should delegate to schema service."""
        await database_service.initialize_account_locks_table()

        database_service._mock_services[
            "schema"
        ].initialize_account_locks_table.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_notifications_table(self, database_service):
        """Should delegate to schema service."""
        await database_service.initialize_notifications_table()

        database_service._mock_services[
            "schema"
        ].initialize_notifications_table.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_retention_settings_table(self, database_service):
        """Should delegate to schema service."""
        await database_service.initialize_retention_settings_table()

        database_service._mock_services[
            "schema"
        ].initialize_retention_settings_table.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_servers_table(self, database_service):
        """Should delegate to schema service."""
        await database_service.initialize_servers_table()

        database_service._mock_services[
            "schema"
        ].initialize_servers_table.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_agents_table(self, database_service):
        """Should delegate to schema service."""
        await database_service.initialize_agents_table()

        database_service._mock_services[
            "schema"
        ].initialize_agents_table.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_installed_apps_table(self, database_service):
        """Should delegate to schema service."""
        await database_service.initialize_installed_apps_table()

        database_service._mock_services[
            "schema"
        ].initialize_installed_apps_table.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_metrics_tables(self, database_service):
        """Should delegate to schema service."""
        await database_service.initialize_metrics_tables()

        database_service._mock_services[
            "schema"
        ].initialize_metrics_tables.assert_called_once()


class TestAccountLockMethods:
    """Tests for account lock methods."""

    @pytest.mark.asyncio
    async def test_is_account_locked(self, database_service):
        """Should delegate to session service."""
        await database_service.is_account_locked("user1", "username")

        database_service._mock_services[
            "session"
        ].is_account_locked.assert_called_once_with("user1", "username")

    @pytest.mark.asyncio
    async def test_record_failed_login_attempt(self, database_service):
        """Should delegate to session service."""
        await database_service.record_failed_login_attempt(
            identifier="user1",
            identifier_type="username",
            ip_address="192.168.1.1",
            user_agent="Mozilla",
            max_attempts=3,
            lock_duration_minutes=30,
        )

        database_service._mock_services[
            "session"
        ].record_failed_login_attempt.assert_called_once_with(
            "user1", "username", "192.168.1.1", "Mozilla", 3, 30
        )

    @pytest.mark.asyncio
    async def test_clear_failed_attempts(self, database_service):
        """Should delegate to session service."""
        await database_service.clear_failed_attempts("user1", "username")

        database_service._mock_services[
            "session"
        ].clear_failed_attempts.assert_called_once_with("user1", "username")

    @pytest.mark.asyncio
    async def test_get_locked_accounts(self, database_service):
        """Should delegate to session service."""
        await database_service.get_locked_accounts(
            include_expired=True, include_unlocked=True
        )

        database_service._mock_services[
            "session"
        ].get_locked_accounts.assert_called_once_with(True, True)

    @pytest.mark.asyncio
    async def test_unlock_account(self, database_service):
        """Should delegate to session service."""
        await database_service.unlock_account("lock-1", "admin", "Unlocking")

        database_service._mock_services[
            "session"
        ].unlock_account.assert_called_once_with("lock-1", "admin", "Unlocking")

    @pytest.mark.asyncio
    async def test_lock_account(self, database_service):
        """Should delegate to session service."""
        await database_service.lock_account("lock-1", "admin", "Manual lock", 60)

        database_service._mock_services["session"].lock_account.assert_called_once_with(
            "lock-1", "admin", "Manual lock", 60
        )

    @pytest.mark.asyncio
    async def test_get_lock_by_id(self, database_service):
        """Should delegate to session service."""
        await database_service.get_lock_by_id("lock-1")

        database_service._mock_services["session"].get_lock_by_id.assert_called_once_with(
            "lock-1"
        )
