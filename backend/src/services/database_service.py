"""Database Service Facade - Backward Compatibility Layer.

Provides the original DatabaseService interface by delegating to specialized
database services. All consuming code can continue using DatabaseService
without changes.
"""

from pathlib import Path
from typing import Any

from models.app_catalog import InstalledApp
from models.auth import User, UserRole
from models.metrics import ActivityLog, ContainerMetrics, ServerMetrics
from models.server import ServerConnection
from services.database import (
    ALLOWED_INSTALLATION_COLUMNS,
    ALLOWED_SERVER_COLUMNS,
    ALLOWED_SYSTEM_INFO_COLUMNS,
    AppDatabaseService,
    DatabaseConnection,
    ExportDatabaseService,
    MetricsDatabaseService,
    SchemaInitializer,
    ServerDatabaseService,
    SessionDatabaseService,
    SystemDatabaseService,
    UserDatabaseService,
)

# Re-export column whitelists for backward compatibility
__all__ = [
    "DatabaseService",
    "ALLOWED_SERVER_COLUMNS",
    "ALLOWED_INSTALLATION_COLUMNS",
    "ALLOWED_SYSTEM_INFO_COLUMNS",
]


class DatabaseService:
    """Facade maintaining backward compatibility with existing code.

    All consuming services can continue using DatabaseService without changes.
    Methods delegate to the appropriate specialized service.
    """

    def __init__(
        self,
        db_path: str | Path | None = None,
        data_directory: str | Path | None = None,
    ):
        """Initialize database service with path to tomo.db."""
        self._connection = DatabaseConnection(db_path, data_directory)
        self._user = UserDatabaseService(self._connection)
        self._server = ServerDatabaseService(self._connection)
        self._session = SessionDatabaseService(self._connection)
        self._app = AppDatabaseService(self._connection)
        self._metrics = MetricsDatabaseService(self._connection)
        self._system = SystemDatabaseService(self._connection)
        self._export = ExportDatabaseService(self._connection)
        self._schema = SchemaInitializer(self._connection)

    @property
    def db_path(self) -> str:
        """Get the database file path."""
        return self._connection.path

    # Connection - delegate directly
    def get_connection(self):
        """Get async database connection with automatic cleanup."""
        return self._connection.get_connection()

    # ========== User Methods ==========

    async def get_user(
        self, user_id: str | None = None, username: str | None = None
    ) -> User | None:
        return await self._user.get_user(user_id, username)

    async def get_user_by_username(self, username: str) -> User | None:
        return await self._user.get_user_by_username(username)

    async def get_user_by_id(self, user_id: str) -> User | None:
        return await self._user.get_user_by_id(user_id)

    async def get_user_password_hash(self, username: str) -> str | None:
        return await self._user.get_user_password_hash(username)

    async def update_user_last_login(
        self, username: str, timestamp: str | None = None
    ) -> bool:
        return await self._user.update_user_last_login(username, timestamp)

    async def get_all_users(self) -> list[User]:
        return await self._user.get_all_users()

    async def create_user(
        self,
        username: str,
        password_hash: str,
        email: str = "",
        role: UserRole = UserRole.USER,
        preferences: dict[str, Any] | None = None,
    ) -> User | None:
        return await self._user.create_user(
            username, password_hash, email, role, preferences
        )

    async def update_user_password(self, username: str, password_hash: str) -> bool:
        return await self._user.update_user_password(username, password_hash)

    async def has_admin_user(self) -> bool:
        return await self._user.has_admin_user()

    async def update_user_preferences(
        self, user_id: str, preferences: dict[str, Any]
    ) -> bool:
        return await self._user.update_user_preferences(user_id, preferences)

    async def update_user_avatar(self, user_id: str, avatar: str | None) -> bool:
        return await self._user.update_user_avatar(user_id, avatar)

    # ========== System Info Methods ==========

    async def get_system_info(self) -> dict[str, Any] | None:
        return await self._system.get_system_info()

    async def is_system_setup(self) -> bool:
        return await self._system.is_system_setup()

    async def mark_system_setup_complete(self, user_id: str) -> bool:
        return await self._system.mark_system_setup_complete(user_id)

    async def update_system_info(self, **kwargs) -> bool:
        return await self._system.update_system_info(**kwargs)

    async def verify_database_connection(self) -> bool:
        return await self._system.verify_database_connection()

    # ========== Component Versions Methods ==========

    async def initialize_component_versions_table(self) -> bool:
        return await self._schema.initialize_component_versions_table()

    async def get_component_versions(self) -> list[dict[str, Any]]:
        return await self._system.get_component_versions()

    async def get_component_version(self, component: str) -> dict[str, Any] | None:
        return await self._system.get_component_version(component)

    async def update_component_version(self, component: str, version: str) -> bool:
        return await self._system.update_component_version(component, version)

    # ========== Log Retention Methods ==========

    async def get_log_entries_count_before_date(self, cutoff_date: str) -> int:
        return await self._metrics.get_log_entries_count_before_date(cutoff_date)

    async def delete_log_entries_before_date(
        self, cutoff_date: str, batch_size: int = 1000
    ) -> int:
        return await self._metrics.delete_log_entries_before_date(
            cutoff_date, batch_size
        )

    # ========== Server Methods ==========

    async def create_server(
        self,
        id: str,
        name: str,
        host: str,
        port: int,
        username: str,
        auth_type: str,
        encrypted_credentials: str,
    ) -> ServerConnection | None:
        return await self._server.create_server(
            id, name, host, port, username, auth_type, encrypted_credentials
        )

    async def get_server_by_id(self, server_id: str) -> ServerConnection | None:
        return await self._server.get_server_by_id(server_id)

    async def get_server_by_connection(
        self, host: str, port: int, username: str
    ) -> ServerConnection | None:
        return await self._server.get_server_by_connection(host, port, username)

    async def get_all_servers_from_db(self) -> list[ServerConnection]:
        return await self._server.get_all_servers_from_db()

    async def get_server_credentials(self, server_id: str) -> str | None:
        return await self._server.get_server_credentials(server_id)

    async def update_server_credentials(
        self, server_id: str, encrypted_credentials: str
    ) -> bool:
        return await self._server.update_server_credentials(
            server_id, encrypted_credentials
        )

    async def update_server(self, server_id: str, **kwargs) -> bool:
        return await self._server.update_server(server_id, **kwargs)

    async def delete_server(self, server_id: str) -> bool:
        return await self._server.delete_server(server_id)

    # ========== Installation Methods ==========

    async def create_installation(
        self,
        id: str,
        server_id: str,
        app_id: str,
        container_name: str,
        status: str,
        config: dict,
        installed_at: str,
    ) -> InstalledApp | None:
        return await self._app.create_installation(
            id, server_id, app_id, container_name, status, config, installed_at
        )

    async def update_installation(self, install_id: str, **kwargs) -> bool:
        return await self._app.update_installation(install_id, **kwargs)

    async def get_installation(
        self, server_id: str, app_id: str
    ) -> InstalledApp | None:
        return await self._app.get_installation(server_id, app_id)

    async def get_installation_by_id(self, install_id: str) -> InstalledApp | None:
        return await self._app.get_installation_by_id(install_id)

    async def get_installations(self, server_id: str) -> list[InstalledApp]:
        return await self._app.get_installations(server_id)

    async def get_all_installations(self) -> list[InstalledApp]:
        return await self._app.get_all_installations()

    async def delete_installation(self, server_id: str, app_id: str) -> bool:
        return await self._app.delete_installation(server_id, app_id)

    # ========== Metrics Methods ==========

    async def save_server_metrics(self, metrics: ServerMetrics) -> bool:
        return await self._metrics.save_server_metrics(metrics)

    async def save_container_metrics(self, metrics: ContainerMetrics) -> bool:
        return await self._metrics.save_container_metrics(metrics)

    async def save_activity_log(self, log: ActivityLog) -> bool:
        return await self._metrics.save_activity_log(log)

    async def get_server_metrics(
        self, server_id: str, since: str = None, limit: int = 100
    ) -> list[ServerMetrics]:
        return await self._metrics.get_server_metrics(server_id, since, limit)

    async def get_container_metrics(
        self,
        server_id: str,
        container_name: str = None,
        since: str = None,
        limit: int = 100,
    ) -> list[ContainerMetrics]:
        return await self._metrics.get_container_metrics(
            server_id, container_name, since, limit
        )

    async def get_activity_logs(
        self,
        activity_types: list = None,
        user_id: str = None,
        server_id: str = None,
        since: str = None,
        until: str = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ActivityLog]:
        return await self._metrics.get_activity_logs(
            activity_types, user_id, server_id, since, until, limit, offset
        )

    async def count_activity_logs(
        self, activity_types: list = None, since: str = None
    ) -> int:
        return await self._metrics.count_activity_logs(activity_types, since)

    # ========== Export/Import Methods ==========

    async def export_users(self) -> list[dict[str, Any]]:
        return await self._export.export_users()

    async def export_servers(self) -> list[dict[str, Any]]:
        return await self._export.export_servers()

    async def export_settings(self) -> dict[str, Any]:
        return await self._export.export_settings()

    async def import_users(self, users: list, overwrite: bool = False) -> None:
        return await self._export.import_users(users, overwrite)

    async def import_servers(self, servers: list, overwrite: bool = False) -> None:
        return await self._export.import_servers(servers, overwrite)

    async def import_settings(self, settings: dict, overwrite: bool = False) -> None:
        return await self._export.import_settings(settings, overwrite)

    # ========== Migration Methods ==========

    async def run_installed_apps_migrations(self) -> None:
        return await self._schema.run_installed_apps_migrations()

    async def run_users_migrations(self) -> None:
        return await self._schema.run_users_migrations()

    # ========== Schema Initialization Methods ==========

    async def initialize_system_info_table(self) -> bool:
        return await self._schema.initialize_system_info_table()

    async def initialize_users_table(self) -> bool:
        return await self._schema.initialize_users_table()

    async def initialize_sessions_table(self) -> bool:
        return await self._schema.initialize_sessions_table()

    async def initialize_account_locks_table(self) -> bool:
        return await self._schema.initialize_account_locks_table()

    async def initialize_notifications_table(self) -> bool:
        return await self._schema.initialize_notifications_table()

    async def initialize_retention_settings_table(self) -> bool:
        return await self._schema.initialize_retention_settings_table()

    async def initialize_servers_table(self) -> bool:
        return await self._schema.initialize_servers_table()

    async def initialize_agents_table(self) -> bool:
        return await self._schema.initialize_agents_table()

    async def initialize_installed_apps_table(self) -> bool:
        return await self._schema.initialize_installed_apps_table()

    async def initialize_metrics_tables(self) -> bool:
        return await self._schema.initialize_metrics_tables()

    # ========== Account Lock Methods ==========

    async def is_account_locked(
        self, identifier: str, identifier_type: str = "username"
    ) -> tuple[bool, dict[str, Any] | None]:
        return await self._session.is_account_locked(identifier, identifier_type)

    async def record_failed_login_attempt(
        self,
        identifier: str,
        identifier_type: str = "username",
        ip_address: str | None = None,
        user_agent: str | None = None,
        max_attempts: int = 5,
        lock_duration_minutes: int = 15,
    ) -> tuple[bool, int, str | None]:
        return await self._session.record_failed_login_attempt(
            identifier,
            identifier_type,
            ip_address,
            user_agent,
            max_attempts,
            lock_duration_minutes,
        )

    async def clear_failed_attempts(
        self, identifier: str, identifier_type: str = "username"
    ) -> bool:
        return await self._session.clear_failed_attempts(identifier, identifier_type)

    async def get_locked_accounts(
        self, include_expired: bool = False, include_unlocked: bool = False
    ) -> list[dict[str, Any]]:
        return await self._session.get_locked_accounts(
            include_expired, include_unlocked
        )

    async def unlock_account(
        self, lock_id: str, unlocked_by: str, notes: str | None = None
    ) -> bool:
        return await self._session.unlock_account(lock_id, unlocked_by, notes)

    async def lock_account(
        self,
        lock_id: str,
        locked_by: str,
        notes: str | None = None,
        lock_duration_minutes: int = 15,
    ) -> bool:
        return await self._session.lock_account(
            lock_id, locked_by, notes, lock_duration_minutes
        )

    async def get_lock_by_id(self, lock_id: str) -> dict[str, Any] | None:
        return await self._session.get_lock_by_id(lock_id)
