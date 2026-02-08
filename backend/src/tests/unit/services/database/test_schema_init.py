"""
Unit tests for services/database/schema_init.py.

Tests SchemaInitializer methods.
"""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.database.schema_init import SchemaInitializer


@pytest.fixture
def mock_connection():
    """Create mock DatabaseConnection."""
    return MagicMock()


@pytest.fixture
def initializer(mock_connection):
    """Create SchemaInitializer instance."""
    return SchemaInitializer(mock_connection)


def create_mock_context(mock_conn):
    """Create async context manager for database connection."""

    @asynccontextmanager
    async def context():
        yield mock_conn

    return context()


class TestSchemaInitializerInit:
    """Tests for SchemaInitializer initialization."""

    def test_init_stores_connection(self, mock_connection):
        """Initializer should store connection reference."""
        initializer = SchemaInitializer(mock_connection)
        assert initializer._conn is mock_connection


class TestInitializeAllTables:
    """Tests for initialize_all_tables method."""

    @pytest.mark.asyncio
    async def test_initialize_all_tables_success(self, initializer, mock_connection):
        """initialize_all_tables should return True when all succeed."""
        mock_conn = AsyncMock()
        # Each call should return a fresh context
        mock_connection.get_connection.side_effect = lambda: create_mock_context(
            mock_conn
        )

        with patch("services.database.schema_init.logger"):
            result = await initializer.initialize_all_tables()

        assert result is True

    @pytest.mark.asyncio
    async def test_initialize_all_tables_partial_failure(
        self, initializer, mock_connection
    ):
        """initialize_all_tables should return False if any fails."""
        call_count = [0]

        def side_effect():
            call_count[0] += 1
            if call_count[0] == 3:
                raise Exception("Third table failed")
            return create_mock_context(AsyncMock())

        mock_connection.get_connection.side_effect = side_effect

        with patch("services.database.schema_init.logger"):
            result = await initializer.initialize_all_tables()

        assert result is False


class TestInitializeSystemInfoTable:
    """Tests for initialize_system_info_table method."""

    @pytest.mark.asyncio
    async def test_initialize_success(self, initializer, mock_connection):
        """initialize_system_info_table should return True on success."""
        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.schema_init.logger"):
            result = await initializer.initialize_system_info_table()

        assert result is True
        mock_conn.executescript.assert_called_once()
        mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_exception(self, initializer, mock_connection):
        """initialize_system_info_table should return False on exception."""
        mock_connection.get_connection.side_effect = Exception("DB error")

        with patch("services.database.schema_init.logger"):
            result = await initializer.initialize_system_info_table()

        assert result is False


class TestInitializeUsersTable:
    """Tests for initialize_users_table method."""

    @pytest.mark.asyncio
    async def test_initialize_success(self, initializer, mock_connection):
        """initialize_users_table should return True on success."""
        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.schema_init.logger"):
            result = await initializer.initialize_users_table()

        assert result is True
        mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_exception(self, initializer, mock_connection):
        """initialize_users_table should return False on exception."""
        mock_connection.get_connection.side_effect = Exception("DB error")

        with patch("services.database.schema_init.logger"):
            result = await initializer.initialize_users_table()

        assert result is False


class TestInitializeSessionsTable:
    """Tests for initialize_sessions_table method."""

    @pytest.mark.asyncio
    async def test_initialize_success(self, initializer, mock_connection):
        """initialize_sessions_table should return True on success."""
        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.schema_init.logger"):
            result = await initializer.initialize_sessions_table()

        assert result is True
        mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_exception(self, initializer, mock_connection):
        """initialize_sessions_table should return False on exception."""
        mock_connection.get_connection.side_effect = Exception("DB error")

        with patch("services.database.schema_init.logger"):
            result = await initializer.initialize_sessions_table()

        assert result is False


class TestInitializeAccountLocksTable:
    """Tests for initialize_account_locks_table method."""

    @pytest.mark.asyncio
    async def test_initialize_success(self, initializer, mock_connection):
        """initialize_account_locks_table should return True on success."""
        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.schema_init.logger"):
            result = await initializer.initialize_account_locks_table()

        assert result is True
        mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_exception(self, initializer, mock_connection):
        """initialize_account_locks_table should return False on exception."""
        mock_connection.get_connection.side_effect = Exception("DB error")

        with patch("services.database.schema_init.logger"):
            result = await initializer.initialize_account_locks_table()

        assert result is False


class TestInitializeNotificationsTable:
    """Tests for initialize_notifications_table method."""

    @pytest.mark.asyncio
    async def test_initialize_success(self, initializer, mock_connection):
        """initialize_notifications_table should return True on success."""
        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.schema_init.logger"):
            result = await initializer.initialize_notifications_table()

        assert result is True
        mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_exception(self, initializer, mock_connection):
        """initialize_notifications_table should return False on exception."""
        mock_connection.get_connection.side_effect = Exception("DB error")

        with patch("services.database.schema_init.logger"):
            result = await initializer.initialize_notifications_table()

        assert result is False


class TestInitializeRetentionSettingsTable:
    """Tests for initialize_retention_settings_table method."""

    @pytest.mark.asyncio
    async def test_initialize_success(self, initializer, mock_connection):
        """initialize_retention_settings_table should return True on success."""
        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.schema_init.logger"):
            result = await initializer.initialize_retention_settings_table()

        assert result is True
        mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_exception(self, initializer, mock_connection):
        """initialize_retention_settings_table should return False on exception."""
        mock_connection.get_connection.side_effect = Exception("DB error")

        with patch("services.database.schema_init.logger"):
            result = await initializer.initialize_retention_settings_table()

        assert result is False


class TestInitializeComponentVersionsTable:
    """Tests for initialize_component_versions_table method."""

    @pytest.mark.asyncio
    async def test_initialize_success(self, initializer, mock_connection):
        """initialize_component_versions_table should return True on success."""
        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.schema_init.logger"):
            result = await initializer.initialize_component_versions_table()

        assert result is True
        mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_exception(self, initializer, mock_connection):
        """initialize_component_versions_table should return False on exception."""
        mock_connection.get_connection.side_effect = Exception("DB error")

        with patch("services.database.schema_init.logger"):
            result = await initializer.initialize_component_versions_table()

        assert result is False


class TestInitializeServersTable:
    """Tests for initialize_servers_table method."""

    @pytest.mark.asyncio
    async def test_initialize_success(self, initializer, mock_connection):
        """initialize_servers_table should return True on success."""
        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.schema_init.logger"):
            result = await initializer.initialize_servers_table()

        assert result is True
        mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_exception(self, initializer, mock_connection):
        """initialize_servers_table should return False on exception."""
        mock_connection.get_connection.side_effect = Exception("DB error")

        with patch("services.database.schema_init.logger"):
            result = await initializer.initialize_servers_table()

        assert result is False


class TestInitializeAgentsTable:
    """Tests for initialize_agents_table method."""

    @pytest.mark.asyncio
    async def test_initialize_success(self, initializer, mock_connection):
        """initialize_agents_table should return True on success."""
        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.schema_init.logger"):
            result = await initializer.initialize_agents_table()

        assert result is True
        mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_exception(self, initializer, mock_connection):
        """initialize_agents_table should return False on exception."""
        mock_connection.get_connection.side_effect = Exception("DB error")

        with patch("services.database.schema_init.logger"):
            result = await initializer.initialize_agents_table()

        assert result is False


class TestInitializeInstalledAppsTable:
    """Tests for initialize_installed_apps_table method."""

    @pytest.mark.asyncio
    async def test_initialize_success(self, initializer, mock_connection):
        """initialize_installed_apps_table should return True on success."""
        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.schema_init.logger"):
            result = await initializer.initialize_installed_apps_table()

        assert result is True
        mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_exception(self, initializer, mock_connection):
        """initialize_installed_apps_table should return False on exception."""
        mock_connection.get_connection.side_effect = Exception("DB error")

        with patch("services.database.schema_init.logger"):
            result = await initializer.initialize_installed_apps_table()

        assert result is False


class TestInitializeMetricsTables:
    """Tests for initialize_metrics_tables method."""

    @pytest.mark.asyncio
    async def test_initialize_success(self, initializer, mock_connection):
        """initialize_metrics_tables should return True on success."""
        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.schema_init.logger"):
            result = await initializer.initialize_metrics_tables()

        assert result is True
        mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_exception(self, initializer, mock_connection):
        """initialize_metrics_tables should return False on exception."""
        mock_connection.get_connection.side_effect = Exception("DB error")

        with patch("services.database.schema_init.logger"):
            result = await initializer.initialize_metrics_tables()

        assert result is False


class TestRunAllMigrations:
    """Tests for run_all_migrations method."""

    @pytest.mark.asyncio
    async def test_run_all_migrations_success(self, initializer, mock_connection):
        """run_all_migrations should call both migration methods."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=[])
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.schema_init.logger"):
            await initializer.run_all_migrations()

        # Should have called execute for PRAGMA queries
        assert mock_conn.execute.call_count >= 2


class TestRunInstalledAppsMigrations:
    """Tests for run_installed_apps_migrations method."""

    @pytest.mark.asyncio
    async def test_run_migrations_no_missing_columns(
        self, initializer, mock_connection
    ):
        """run_installed_apps_migrations should skip existing columns."""
        # All columns exist
        existing_cols = [
            (0, "id", "TEXT", 0, None, 1),
            (1, "step_durations", "TEXT", 0, None, 0),
            (2, "step_started_at", "TEXT", 0, None, 0),
            (3, "networks", "TEXT", 0, None, 0),
            (4, "named_volumes", "TEXT", 0, None, 0),
            (5, "bind_mounts", "TEXT", 0, None, 0),
        ]
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=existing_cols)
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.schema_init.logger"):
            await initializer.run_installed_apps_migrations()

        # Should only call execute once for PRAGMA
        assert mock_conn.execute.call_count == 1

    @pytest.mark.asyncio
    async def test_run_migrations_adds_missing_columns(
        self, initializer, mock_connection
    ):
        """run_installed_apps_migrations should add missing columns."""
        # Only id column exists
        existing_cols = [(0, "id", "TEXT", 0, None, 1)]
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=existing_cols)
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.schema_init.logger"):
            await initializer.run_installed_apps_migrations()

        # Should call execute for PRAGMA + 5 ALTER TABLE statements
        assert mock_conn.execute.call_count == 6

    @pytest.mark.asyncio
    async def test_run_migrations_handles_alter_error(
        self, initializer, mock_connection
    ):
        """run_installed_apps_migrations should handle ALTER errors gracefully."""
        existing_cols = [(0, "id", "TEXT", 0, None, 1)]
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=existing_cols)
        mock_conn = AsyncMock()

        call_count = [0]

        async def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_cursor
            raise Exception("Column already exists")

        mock_conn.execute = AsyncMock(side_effect=side_effect)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.schema_init.logger"):
            await initializer.run_installed_apps_migrations()

        # Should not raise, should log and continue

    @pytest.mark.asyncio
    async def test_run_migrations_outer_exception(self, initializer, mock_connection):
        """run_installed_apps_migrations should handle outer exception."""
        mock_connection.get_connection.side_effect = Exception("Connection failed")

        with patch("services.database.schema_init.logger"):
            await initializer.run_installed_apps_migrations()

        # Should not raise, should log error


class TestRunUsersMigrations:
    """Tests for run_users_migrations method."""

    @pytest.mark.asyncio
    async def test_run_migrations_no_missing_columns(
        self, initializer, mock_connection
    ):
        """run_users_migrations should skip existing columns."""
        existing_cols = [
            (0, "id", "TEXT", 0, None, 1),
            (1, "avatar", "TEXT", 0, None, 0),
        ]
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=existing_cols)
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.schema_init.logger"):
            await initializer.run_users_migrations()

        # Should only call execute once for PRAGMA
        assert mock_conn.execute.call_count == 1

    @pytest.mark.asyncio
    async def test_run_migrations_adds_avatar_column(
        self, initializer, mock_connection
    ):
        """run_users_migrations should add avatar column if missing."""
        existing_cols = [(0, "id", "TEXT", 0, None, 1)]
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=existing_cols)
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.schema_init.logger"):
            await initializer.run_users_migrations()

        # Should call execute for PRAGMA + 1 ALTER TABLE
        assert mock_conn.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_run_migrations_handles_alter_error(
        self, initializer, mock_connection
    ):
        """run_users_migrations should handle ALTER errors gracefully."""
        existing_cols = [(0, "id", "TEXT", 0, None, 1)]
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=existing_cols)
        mock_conn = AsyncMock()

        call_count = [0]

        async def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_cursor
            raise Exception("Column already exists")

        mock_conn.execute = AsyncMock(side_effect=side_effect)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.schema_init.logger"):
            await initializer.run_users_migrations()

        # Should not raise

    @pytest.mark.asyncio
    async def test_run_migrations_outer_exception(self, initializer, mock_connection):
        """run_users_migrations should handle outer exception."""
        mock_connection.get_connection.side_effect = Exception("Connection failed")

        with patch("services.database.schema_init.logger"):
            await initializer.run_users_migrations()

        # Should not raise
