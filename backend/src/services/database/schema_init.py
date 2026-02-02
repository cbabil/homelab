"""Schema Initialization Service.

Database schema initialization and migrations.
"""

import structlog

from .base import DatabaseConnection

logger = structlog.get_logger("database.schema")


class SchemaInitializer:
    """Database schema initialization and migrations."""

    def __init__(self, connection: DatabaseConnection):
        """Initialize with database connection.

        Args:
            connection: DatabaseConnection instance.
        """
        self._conn = connection

    async def initialize_all_tables(self) -> bool:
        """Initialize all tables in correct order.

        Returns:
            True if all tables initialized successfully.
        """
        success = True
        success = success and await self.initialize_system_info_table()
        success = success and await self.initialize_users_table()
        success = success and await self.initialize_sessions_table()
        success = success and await self.initialize_account_locks_table()
        success = success and await self.initialize_notifications_table()
        success = success and await self.initialize_retention_settings_table()
        success = success and await self.initialize_component_versions_table()
        success = success and await self.initialize_servers_table()
        success = success and await self.initialize_agents_table()
        success = success and await self.initialize_installed_apps_table()
        success = success and await self.initialize_metrics_tables()
        return success

    async def run_all_migrations(self) -> None:
        """Run all pending migrations."""
        await self.run_users_migrations()
        await self.run_installed_apps_migrations()

    # ========== Table Initialization Methods ==========

    async def initialize_system_info_table(self) -> bool:
        """Initialize the system_info table if it doesn't exist.

        Creates the system_info table with default values and ensures
        a single row exists with an auto-generated installation ID.

        Returns:
            True if successful, False otherwise.
        """
        try:
            async with self._conn.get_connection() as conn:
                await conn.executescript("""
                    -- System Info Table
                    -- Single row table (enforced by CHECK constraint) for application metadata
                    CREATE TABLE IF NOT EXISTS system_info (
                        id INTEGER PRIMARY KEY CHECK (id = 1),
                        app_name TEXT NOT NULL DEFAULT 'Tomo',
                        is_setup INTEGER NOT NULL DEFAULT 0 CHECK (is_setup IN (0, 1)),
                        setup_completed_at TEXT,
                        setup_by_user_id TEXT,
                        installation_id TEXT NOT NULL,
                        license_type TEXT DEFAULT 'community' CHECK (license_type IN ('community', 'pro', 'enterprise')),
                        license_key TEXT,
                        license_expires_at TEXT,
                        created_at TEXT NOT NULL DEFAULT (datetime('now')),
                        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
                    );

                    -- Ensure single row exists with auto-generated installation ID
                    INSERT OR IGNORE INTO system_info (id, installation_id)
                    VALUES (1, lower(hex(randomblob(16))));

                    -- Trigger to auto-update updated_at timestamp
                    CREATE TRIGGER IF NOT EXISTS system_info_updated_at
                    AFTER UPDATE ON system_info
                    BEGIN
                        UPDATE system_info SET updated_at = datetime('now') WHERE id = 1;
                    END;

                    -- Index on is_setup for fast lookup
                    CREATE INDEX IF NOT EXISTS idx_system_info_is_setup ON system_info(is_setup);
                """)
                await conn.commit()

            logger.info("System info table initialized successfully")
            return True

        except Exception as e:
            logger.error("Failed to initialize system info table", error=str(e))
            return False

    async def initialize_users_table(self) -> bool:
        """Initialize the users table if it doesn't exist.

        Creates the users table for authentication and user management.

        Returns:
            True if successful, False otherwise.
        """
        try:
            async with self._conn.get_connection() as conn:
                await conn.executescript("""
                    -- Users Table
                    -- Stores user accounts for authentication
                    CREATE TABLE IF NOT EXISTS users (
                        id TEXT PRIMARY KEY,
                        username TEXT NOT NULL UNIQUE,
                        email TEXT DEFAULT '',
                        password_hash TEXT NOT NULL,
                        role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('admin', 'user', 'readonly')),
                        created_at TEXT NOT NULL DEFAULT (datetime('now')),
                        last_login TEXT,
                        is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
                        preferences_json TEXT DEFAULT '{}'
                    );

                    -- Indexes for common queries
                    CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
                    CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
                    CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
                    CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);
                    CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);
                """)
                await conn.commit()

            logger.info("Users table initialized successfully")
            return True

        except Exception as e:
            logger.error("Failed to initialize users table", error=str(e))
            return False

    async def initialize_sessions_table(self) -> bool:
        """Initialize the sessions table if it doesn't exist.

        Creates the sessions table for persistent session management.

        Returns:
            True if successful, False otherwise.
        """
        try:
            async with self._conn.get_connection() as conn:
                await conn.executescript("""
                    -- Sessions Table
                    -- Stores user sessions for authentication tracking
                    CREATE TABLE IF NOT EXISTS sessions (
                        id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        ip_address TEXT,
                        user_agent TEXT,
                        created_at TEXT NOT NULL DEFAULT (datetime('now')),
                        expires_at TEXT NOT NULL,
                        last_activity TEXT NOT NULL DEFAULT (datetime('now')),
                        status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'idle', 'expired', 'terminated')),
                        terminated_at TEXT,
                        terminated_by TEXT,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                    );

                    -- Indexes for common queries
                    CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
                    CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
                    CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);
                    CREATE INDEX IF NOT EXISTS idx_sessions_last_activity ON sessions(last_activity);
                """)
                await conn.commit()

            logger.info("Sessions table initialized successfully")
            return True

        except Exception as e:
            logger.error("Failed to initialize sessions table", error=str(e))
            return False

    async def initialize_account_locks_table(self) -> bool:
        """Initialize the account_locks table if it doesn't exist.

        Creates the account_locks table for tracking failed login attempts
        and preventing brute force attacks.

        Returns:
            True if successful, False otherwise.
        """
        try:
            async with self._conn.get_connection() as conn:
                await conn.executescript("""
                    -- Account Locks Table
                    -- Tracks failed login attempts and locks accounts/IPs
                    CREATE TABLE IF NOT EXISTS account_locks (
                        id TEXT PRIMARY KEY,
                        identifier TEXT NOT NULL,
                        identifier_type TEXT NOT NULL CHECK (identifier_type IN ('username', 'ip')),
                        attempt_count INTEGER NOT NULL DEFAULT 1,
                        first_attempt_at TEXT NOT NULL DEFAULT (datetime('now')),
                        last_attempt_at TEXT NOT NULL DEFAULT (datetime('now')),
                        locked_at TEXT,
                        lock_expires_at TEXT,
                        ip_address TEXT,
                        user_agent TEXT,
                        reason TEXT DEFAULT 'too_many_attempts',
                        unlocked_at TEXT,
                        unlocked_by TEXT,
                        notes TEXT,
                        UNIQUE(identifier, identifier_type)
                    );

                    -- Indexes for common queries
                    CREATE INDEX IF NOT EXISTS idx_account_locks_identifier ON account_locks(identifier);
                    CREATE INDEX IF NOT EXISTS idx_account_locks_identifier_type ON account_locks(identifier_type);
                    CREATE INDEX IF NOT EXISTS idx_account_locks_locked_at ON account_locks(locked_at);
                    CREATE INDEX IF NOT EXISTS idx_account_locks_lock_expires_at ON account_locks(lock_expires_at);
                    CREATE INDEX IF NOT EXISTS idx_account_locks_ip_address ON account_locks(ip_address);
                """)
                await conn.commit()

            logger.info("Account locks table initialized successfully")
            return True

        except Exception as e:
            logger.error("Failed to initialize account locks table", error=str(e))
            return False

    async def initialize_notifications_table(self) -> bool:
        """Initialize the notifications table if it doesn't exist.

        Creates the notifications table for persistent notification storage.

        Returns:
            True if successful, False otherwise.
        """
        try:
            async with self._conn.get_connection() as conn:
                await conn.executescript("""
                    -- Notifications Table
                    -- Stores user notifications for alerts, events, and system messages
                    CREATE TABLE IF NOT EXISTS notifications (
                        id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        type TEXT NOT NULL CHECK (type IN ('info', 'success', 'warning', 'error')),
                        title TEXT NOT NULL,
                        message TEXT NOT NULL,
                        read INTEGER NOT NULL DEFAULT 0,
                        created_at TEXT NOT NULL DEFAULT (datetime('now')),
                        read_at TEXT,
                        dismissed_at TEXT,
                        expires_at TEXT,
                        source TEXT,
                        metadata TEXT,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                    );

                    -- Indexes for common queries
                    CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
                    CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(read);
                    CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at);
                    CREATE INDEX IF NOT EXISTS idx_notifications_type ON notifications(type);
                    CREATE INDEX IF NOT EXISTS idx_notifications_user_read ON notifications(user_id, read);
                """)
                await conn.commit()

            logger.info("Notifications table initialized successfully")
            return True

        except Exception as e:
            logger.error("Failed to initialize notifications table", error=str(e))
            return False

    async def initialize_retention_settings_table(self) -> bool:
        """Initialize the retention_settings table if it doesn't exist.

        Creates the retention_settings table with default values for
        system-wide log and data retention configuration.

        Returns:
            True if successful, False otherwise.
        """
        try:
            async with self._conn.get_connection() as conn:
                await conn.executescript("""
                    CREATE TABLE IF NOT EXISTS retention_settings (
                        id TEXT PRIMARY KEY DEFAULT 'system',
                        -- Log retention (in days)
                        audit_log_retention INTEGER NOT NULL DEFAULT 365,
                        access_log_retention INTEGER NOT NULL DEFAULT 30,
                        application_log_retention INTEGER NOT NULL DEFAULT 30,
                        server_log_retention INTEGER NOT NULL DEFAULT 90,
                        -- Data retention (in days)
                        metrics_retention INTEGER NOT NULL DEFAULT 90,
                        notification_retention INTEGER NOT NULL DEFAULT 30,
                        session_retention INTEGER NOT NULL DEFAULT 7,
                        -- Metadata
                        last_updated TEXT,
                        updated_by_user_id TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    );

                    -- Insert default values if not exists
                    INSERT OR IGNORE INTO retention_settings (id) VALUES ('system');
                """)
                await conn.commit()

            logger.info("Retention settings table initialized successfully")
            return True

        except Exception as e:
            logger.error("Failed to initialize retention settings table", error=str(e))
            return False

    async def initialize_component_versions_table(self) -> bool:
        """Initialize the component_versions table.

        Creates the table and inserts default versions for all components.

        Returns:
            True if successful, False otherwise.
        """
        try:
            async with self._conn.get_connection() as conn:
                await conn.executescript("""
                    CREATE TABLE IF NOT EXISTS component_versions (
                        component TEXT PRIMARY KEY CHECK (component IN ('backend', 'frontend', 'api')),
                        version TEXT NOT NULL DEFAULT '1.0.0',
                        updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                        created_at TEXT NOT NULL DEFAULT (datetime('now'))
                    );

                    INSERT OR IGNORE INTO component_versions (component, version) VALUES
                        ('backend', '1.0.0'),
                        ('frontend', '1.0.0'),
                        ('api', '1.0.0');

                    CREATE TRIGGER IF NOT EXISTS component_versions_updated_at
                    AFTER UPDATE ON component_versions
                    BEGIN
                        UPDATE component_versions SET updated_at = datetime('now') WHERE component = NEW.component;
                    END;
                """)
                await conn.commit()

            logger.info("Component versions table initialized")
            return True

        except Exception as e:
            logger.error("Failed to initialize component versions table", error=str(e))
            return False

    async def initialize_servers_table(self) -> bool:
        """Initialize the servers and server_credentials tables if they don't exist.

        Creates the servers table for managing remote server connections
        and the server_credentials table for storing encrypted credentials.

        Returns:
            True if successful, False otherwise.
        """
        try:
            async with self._conn.get_connection() as conn:
                await conn.executescript("""
                    -- Servers Table
                    -- Stores server connection information
                    CREATE TABLE IF NOT EXISTS servers (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        host TEXT NOT NULL,
                        port INTEGER NOT NULL DEFAULT 22,
                        username TEXT NOT NULL,
                        auth_type TEXT NOT NULL CHECK(auth_type IN ('password', 'key')),
                        status TEXT NOT NULL DEFAULT 'disconnected',
                        created_at TEXT NOT NULL,
                        last_connected TEXT,
                        system_info TEXT,
                        docker_installed INTEGER NOT NULL DEFAULT 0,
                        system_info_updated_at TEXT,
                        UNIQUE(host, port, username)
                    );

                    -- Server Credentials Table
                    -- Stores encrypted credentials separately for security
                    CREATE TABLE IF NOT EXISTS server_credentials (
                        server_id TEXT PRIMARY KEY,
                        encrypted_data TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE
                    );

                    -- Indexes for common queries
                    CREATE INDEX IF NOT EXISTS idx_servers_status ON servers(status);
                    CREATE INDEX IF NOT EXISTS idx_servers_host ON servers(host);
                    CREATE INDEX IF NOT EXISTS idx_servers_docker ON servers(docker_installed);
                """)
                await conn.commit()

            logger.info("Servers table initialized successfully")
            return True

        except Exception as e:
            logger.error("Failed to initialize servers table", error=str(e))
            return False

    async def initialize_agents_table(self) -> bool:
        """Initialize the agents and agent_registration_codes tables.

        Creates the agents table for WebSocket-based server management
        and the agent_registration_codes table for one-time registration.

        Returns:
            True if successful, False otherwise.
        """
        try:
            async with self._conn.get_connection() as conn:
                await conn.executescript("""
                    -- Agents Table
                    -- Stores agent information for WebSocket-based server management
                    CREATE TABLE IF NOT EXISTS agents (
                        id TEXT PRIMARY KEY,
                        server_id TEXT NOT NULL UNIQUE,
                        token_hash TEXT,
                        version TEXT,
                        status TEXT NOT NULL DEFAULT 'pending'
                            CHECK (status IN ('pending', 'active', 'disconnected', 'error')),
                        last_seen TEXT,
                        registered_at TEXT,
                        config TEXT,
                        created_at TEXT NOT NULL DEFAULT (datetime('now')),
                        updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                        FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE
                    );

                    -- Agent Registration Codes Table
                    -- Stores one-time registration codes for agent authentication
                    CREATE TABLE IF NOT EXISTS agent_registration_codes (
                        id TEXT PRIMARY KEY,
                        agent_id TEXT NOT NULL,
                        code TEXT NOT NULL UNIQUE,
                        expires_at TEXT NOT NULL,
                        used INTEGER NOT NULL DEFAULT 0 CHECK (used IN (0, 1)),
                        created_at TEXT NOT NULL DEFAULT (datetime('now')),
                        FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
                    );

                    -- Indexes for common queries
                    CREATE INDEX IF NOT EXISTS idx_agents_server_id ON agents(server_id);
                    CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);
                    CREATE INDEX IF NOT EXISTS idx_agent_registration_codes_code
                        ON agent_registration_codes(code);
                    CREATE INDEX IF NOT EXISTS idx_agent_registration_codes_agent_id
                        ON agent_registration_codes(agent_id);
                """)
                await conn.commit()

            logger.info("Agents table initialized successfully")
            return True

        except Exception as e:
            logger.error("Failed to initialize agents table", error=str(e))
            return False

    async def initialize_installed_apps_table(self) -> bool:
        """Initialize the installed_apps table if it doesn't exist.

        Returns:
            True if successful, False otherwise.
        """
        try:
            async with self._conn.get_connection() as conn:
                await conn.executescript("""
                    CREATE TABLE IF NOT EXISTS installed_apps (
                        id TEXT PRIMARY KEY,
                        server_id TEXT NOT NULL,
                        app_id TEXT NOT NULL,
                        container_id TEXT,
                        container_name TEXT,
                        status TEXT NOT NULL DEFAULT 'pending',
                        config TEXT,
                        installed_at TEXT,
                        started_at TEXT,
                        error_message TEXT,
                        step_durations TEXT,
                        step_started_at TEXT,
                        networks TEXT,
                        named_volumes TEXT,
                        bind_mounts TEXT,
                        FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE,
                        UNIQUE(server_id, app_id)
                    );

                    CREATE INDEX IF NOT EXISTS idx_installed_apps_server
                        ON installed_apps(server_id);
                    CREATE INDEX IF NOT EXISTS idx_installed_apps_status
                        ON installed_apps(status);
                """)
                await conn.commit()

            logger.info("Installed apps table initialized successfully")
            return True

        except Exception as e:
            logger.error("Failed to initialize installed_apps table", error=str(e))
            return False

    async def initialize_metrics_tables(self) -> bool:
        """Initialize the metrics tables if they don't exist.

        Creates server_metrics, container_metrics, and activity_logs tables.

        Returns:
            True if successful, False otherwise.
        """
        try:
            async with self._conn.get_connection() as conn:
                await conn.executescript("""
                    CREATE TABLE IF NOT EXISTS server_metrics (
                        id TEXT PRIMARY KEY,
                        server_id TEXT NOT NULL,
                        cpu_percent REAL NOT NULL,
                        memory_percent REAL NOT NULL,
                        memory_used_mb INTEGER NOT NULL,
                        memory_total_mb INTEGER NOT NULL,
                        disk_percent REAL NOT NULL,
                        disk_used_gb INTEGER NOT NULL,
                        disk_total_gb INTEGER NOT NULL,
                        network_rx_bytes INTEGER DEFAULT 0,
                        network_tx_bytes INTEGER DEFAULT 0,
                        load_average_1m REAL,
                        load_average_5m REAL,
                        load_average_15m REAL,
                        uptime_seconds INTEGER,
                        timestamp TEXT NOT NULL,
                        FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE
                    );

                    CREATE TABLE IF NOT EXISTS container_metrics (
                        id TEXT PRIMARY KEY,
                        server_id TEXT NOT NULL,
                        container_id TEXT NOT NULL,
                        container_name TEXT NOT NULL,
                        cpu_percent REAL NOT NULL,
                        memory_usage_mb INTEGER NOT NULL,
                        memory_limit_mb INTEGER NOT NULL,
                        network_rx_bytes INTEGER DEFAULT 0,
                        network_tx_bytes INTEGER DEFAULT 0,
                        status TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE
                    );

                    CREATE TABLE IF NOT EXISTS activity_logs (
                        id TEXT PRIMARY KEY,
                        activity_type TEXT NOT NULL,
                        user_id TEXT,
                        server_id TEXT,
                        app_id TEXT,
                        message TEXT NOT NULL,
                        details TEXT,
                        timestamp TEXT NOT NULL
                    );

                    CREATE INDEX IF NOT EXISTS idx_server_metrics_server
                        ON server_metrics(server_id);
                    CREATE INDEX IF NOT EXISTS idx_server_metrics_timestamp
                        ON server_metrics(timestamp);
                    CREATE INDEX IF NOT EXISTS idx_container_metrics_server
                        ON container_metrics(server_id);
                    CREATE INDEX IF NOT EXISTS idx_container_metrics_timestamp
                        ON container_metrics(timestamp);
                    CREATE INDEX IF NOT EXISTS idx_activity_logs_type
                        ON activity_logs(activity_type);
                    CREATE INDEX IF NOT EXISTS idx_activity_logs_timestamp
                        ON activity_logs(timestamp);
                    CREATE INDEX IF NOT EXISTS idx_activity_logs_user
                        ON activity_logs(user_id);
                """)
                await conn.commit()

            logger.info("Metrics tables initialized successfully")
            return True

        except Exception as e:
            logger.error("Failed to initialize metrics tables", error=str(e))
            return False

    # ========== Migration Methods ==========

    async def run_installed_apps_migrations(self) -> None:
        """Run migrations for installed_apps table to add new columns."""
        migrations = [
            (
                "step_durations",
                "ALTER TABLE installed_apps ADD COLUMN step_durations TEXT",
            ),
            (
                "step_started_at",
                "ALTER TABLE installed_apps ADD COLUMN step_started_at TEXT",
            ),
            ("networks", "ALTER TABLE installed_apps ADD COLUMN networks TEXT"),
            (
                "named_volumes",
                "ALTER TABLE installed_apps ADD COLUMN named_volumes TEXT",
            ),
            ("bind_mounts", "ALTER TABLE installed_apps ADD COLUMN bind_mounts TEXT"),
        ]
        try:
            async with self._conn.get_connection() as conn:
                cursor = await conn.execute("PRAGMA table_info(installed_apps)")
                rows = await cursor.fetchall()
                existing_columns = {row[1] for row in rows}

                for column_name, migration_sql in migrations:
                    if column_name not in existing_columns:
                        try:
                            await conn.execute(migration_sql)
                            await conn.commit()
                            logger.info(
                                "Added column to installed_apps", column=column_name
                            )
                        except Exception as e:
                            logger.debug(
                                "Migration skipped", column=column_name, error=str(e)
                            )
        except Exception as e:
            logger.error("Failed to run installed_apps migrations", error=str(e))

    async def run_users_migrations(self) -> None:
        """Run migrations for users table to add new columns."""
        migrations = [
            ("avatar", "ALTER TABLE users ADD COLUMN avatar TEXT DEFAULT NULL"),
        ]
        try:
            async with self._conn.get_connection() as conn:
                cursor = await conn.execute("PRAGMA table_info(users)")
                rows = await cursor.fetchall()
                existing_columns = {row[1] for row in rows}

                for column_name, migration_sql in migrations:
                    if column_name not in existing_columns:
                        try:
                            await conn.execute(migration_sql)
                            await conn.commit()
                            logger.info("Added column to users", column=column_name)
                        except Exception as e:
                            logger.debug(
                                "Migration skipped", column=column_name, error=str(e)
                            )
        except Exception as e:
            logger.error("Failed to run users migrations", error=str(e))
