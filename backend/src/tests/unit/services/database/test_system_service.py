"""
Unit tests for services/database/system_service.py

Tests system info and component version database operations.
"""

import pytest
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch


from services.database.system_service import SystemDatabaseService


@pytest.fixture
def mock_connection():
    """Create mock DatabaseConnection."""
    return MagicMock()


@pytest.fixture
def system_service(mock_connection):
    """Create SystemDatabaseService instance."""
    return SystemDatabaseService(mock_connection)


def create_mock_context(mock_conn):
    """Create async context manager for database connection."""

    @asynccontextmanager
    async def context():
        yield mock_conn

    return context()


class TestSystemDatabaseServiceInit:
    """Tests for SystemDatabaseService initialization."""

    def test_init_stores_connection(self, mock_connection):
        """SystemDatabaseService should store connection reference."""
        service = SystemDatabaseService(mock_connection)
        assert service._conn is mock_connection

    def test_init_with_different_connection(self):
        """SystemDatabaseService should accept any connection object."""
        custom_conn = MagicMock()
        custom_conn.db_path = "/custom/path.db"
        service = SystemDatabaseService(custom_conn)
        assert service._conn is custom_conn


class TestGetSystemInfo:
    """Tests for get_system_info method."""

    @pytest.mark.asyncio
    async def test_get_system_info_success(self, system_service, mock_connection):
        """get_system_info should return system info dict when found."""
        mock_row = {
            "id": 1,
            "app_name": "Tomo",
            "is_setup": 1,
            "setup_completed_at": "2024-01-01T00:00:00",
            "setup_by_user_id": "user123",
            "installation_id": "inst456",
            "license_type": "community",
            "license_key": None,
            "license_expires_at": None,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = mock_row

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        result = await system_service.get_system_info()

        assert result is not None
        assert result["id"] == 1
        assert result["app_name"] == "Tomo"
        assert result["is_setup"] is True
        assert result["setup_by_user_id"] == "user123"
        assert result["installation_id"] == "inst456"

    @pytest.mark.asyncio
    async def test_get_system_info_converts_is_setup_to_bool(
        self, system_service, mock_connection
    ):
        """get_system_info should convert is_setup to boolean."""
        mock_row = {
            "id": 1,
            "app_name": "Tomo",
            "is_setup": 0,
            "setup_completed_at": None,
            "setup_by_user_id": None,
            "installation_id": None,
            "license_type": None,
            "license_key": None,
            "license_expires_at": None,
            "created_at": "2024-01-01",
            "updated_at": "2024-01-01",
        }
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = mock_row

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        result = await system_service.get_system_info()

        assert result["is_setup"] is False

    @pytest.mark.asyncio
    async def test_get_system_info_not_found(self, system_service, mock_connection):
        """get_system_info should return None when no row exists."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = None

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.system_service.logger"):
            result = await system_service.get_system_info()

        assert result is None

    @pytest.mark.asyncio
    async def test_get_system_info_error_returns_none(
        self, system_service, mock_connection
    ):
        """get_system_info should return None on database error."""
        mock_conn = AsyncMock()
        mock_conn.execute.side_effect = Exception("DB error")

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.system_service.logger"):
            result = await system_service.get_system_info()

        assert result is None

    @pytest.mark.asyncio
    async def test_get_system_info_logs_error(self, system_service, mock_connection):
        """get_system_info should log error on exception."""
        mock_conn = AsyncMock()
        mock_conn.execute.side_effect = Exception("Connection failed")

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.system_service.logger") as mock_logger:
            await system_service.get_system_info()

        mock_logger.error.assert_called_once()
        assert "Connection failed" in str(mock_logger.error.call_args)


class TestIsSystemSetup:
    """Tests for is_system_setup method."""

    @pytest.mark.asyncio
    async def test_is_system_setup_true(self, system_service, mock_connection):
        """is_system_setup should return True when is_setup = 1."""
        mock_row = {"is_setup": 1}
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = mock_row

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.system_service.logger"):
            result = await system_service.is_system_setup()

        assert result is True

    @pytest.mark.asyncio
    async def test_is_system_setup_false(self, system_service, mock_connection):
        """is_system_setup should return False when is_setup = 0."""
        mock_row = {"is_setup": 0}
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = mock_row

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.system_service.logger"):
            result = await system_service.is_system_setup()

        assert result is False

    @pytest.mark.asyncio
    async def test_is_system_setup_no_row_returns_false(
        self, system_service, mock_connection
    ):
        """is_system_setup should return False when no row exists."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = None

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.system_service.logger"):
            result = await system_service.is_system_setup()

        assert result is False

    @pytest.mark.asyncio
    async def test_is_system_setup_error_returns_false(
        self, system_service, mock_connection
    ):
        """is_system_setup should return False on error."""
        mock_conn = AsyncMock()
        mock_conn.execute.side_effect = Exception("DB error")

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.system_service.logger"):
            result = await system_service.is_system_setup()

        assert result is False

    @pytest.mark.asyncio
    async def test_is_system_setup_logs_debug_when_not_found(
        self, system_service, mock_connection
    ):
        """is_system_setup should log debug message when row not found."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = None

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.system_service.logger") as mock_logger:
            await system_service.is_system_setup()

        mock_logger.debug.assert_called()


class TestMarkSystemSetupComplete:
    """Tests for mark_system_setup_complete method."""

    @pytest.mark.asyncio
    async def test_mark_setup_complete_success(self, system_service, mock_connection):
        """mark_system_setup_complete should return True on success."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 1

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.system_service.logger"):
            result = await system_service.mark_system_setup_complete("user123")

        assert result is True
        mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_mark_setup_complete_no_row_returns_false(
        self, system_service, mock_connection
    ):
        """mark_system_setup_complete should return False when no row updated."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 0

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.system_service.logger"):
            result = await system_service.mark_system_setup_complete("user123")

        assert result is False

    @pytest.mark.asyncio
    async def test_mark_setup_complete_error_returns_false(
        self, system_service, mock_connection
    ):
        """mark_system_setup_complete should return False on error."""
        mock_conn = AsyncMock()
        mock_conn.execute.side_effect = Exception("DB error")

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.system_service.logger"):
            result = await system_service.mark_system_setup_complete("user123")

        assert result is False

    @pytest.mark.asyncio
    async def test_mark_setup_complete_sets_correct_fields(
        self, system_service, mock_connection
    ):
        """mark_system_setup_complete should update is_setup, completed_at, user_id."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 1

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.system_service.logger"):
            await system_service.mark_system_setup_complete("user456")

        call_args = mock_conn.execute.call_args
        sql = call_args[0][0]
        params = call_args[0][1]

        assert "is_setup = 1" in sql
        assert "setup_completed_at" in sql
        assert "setup_by_user_id" in sql
        assert params[1] == "user456"

    @pytest.mark.asyncio
    async def test_mark_setup_complete_logs_success(
        self, system_service, mock_connection
    ):
        """mark_system_setup_complete should log on success."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 1

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.system_service.logger") as mock_logger:
            await system_service.mark_system_setup_complete("user123")

        mock_logger.info.assert_called_once()
        call_kwargs = mock_logger.info.call_args.kwargs
        assert call_kwargs["user_id"] == "user123"


class TestUpdateSystemInfo:
    """Tests for update_system_info method."""

    @pytest.mark.asyncio
    async def test_update_system_info_success(self, system_service, mock_connection):
        """update_system_info should return True on success."""
        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.system_service.logger"):
            result = await system_service.update_system_info(app_name="NewName")

        assert result is True
        mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_system_info_multiple_fields(
        self, system_service, mock_connection
    ):
        """update_system_info should handle multiple fields."""
        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.system_service.logger"):
            result = await system_service.update_system_info(
                app_name="NewApp", license_type="pro"
            )

        assert result is True
        call_args = mock_conn.execute.call_args[0]
        sql = call_args[0]
        assert "app_name = ?" in sql
        assert "license_type = ?" in sql

    @pytest.mark.asyncio
    async def test_update_system_info_empty_kwargs(
        self, system_service, mock_connection
    ):
        """update_system_info should return True when no fields to update."""
        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.system_service.logger"):
            result = await system_service.update_system_info()

        assert result is True
        mock_conn.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_system_info_none_values_skipped(
        self, system_service, mock_connection
    ):
        """update_system_info should skip None values."""
        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.system_service.logger"):
            result = await system_service.update_system_info(
                app_name=None, license_type="pro"
            )

        assert result is True
        call_args = mock_conn.execute.call_args[0]
        sql = call_args[0]
        assert "app_name" not in sql
        assert "license_type = ?" in sql

    @pytest.mark.asyncio
    async def test_update_system_info_invalid_column_raises(
        self, system_service, mock_connection
    ):
        """update_system_info should raise ValueError for invalid columns."""
        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.system_service.logger"):
            result = await system_service.update_system_info(invalid_column="value")

        assert result is False

    @pytest.mark.asyncio
    async def test_update_system_info_invalid_column_logs_warning(
        self, system_service, mock_connection
    ):
        """update_system_info should log warning for invalid columns."""
        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.system_service.logger") as mock_logger:
            await system_service.update_system_info(bad_column="value")

        mock_logger.warning.assert_called_once()
        assert "bad_column" in str(mock_logger.warning.call_args)

    @pytest.mark.asyncio
    async def test_update_system_info_db_error_returns_false(
        self, system_service, mock_connection
    ):
        """update_system_info should return False on database error."""
        mock_conn = AsyncMock()
        mock_conn.execute.side_effect = Exception("DB error")

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.system_service.logger"):
            result = await system_service.update_system_info(app_name="Test")

        assert result is False

    @pytest.mark.asyncio
    async def test_update_system_info_allowed_columns_only(
        self, system_service, mock_connection
    ):
        """update_system_info should accept all allowed columns."""
        allowed = ["app_name", "is_setup", "license_type", "license_key"]

        for col in allowed:
            mock_conn = AsyncMock()
            mock_connection.get_connection.return_value = create_mock_context(mock_conn)
            with patch("services.database.system_service.logger"):
                result = await system_service.update_system_info(**{col: "test_value"})
                assert result is True, f"Column {col} should be allowed"


class TestVerifyDatabaseConnection:
    """Tests for verify_database_connection method."""

    @pytest.mark.asyncio
    async def test_verify_connection_success(self, system_service, mock_connection):
        """verify_database_connection should return True when all checks pass."""
        mock_columns = [
            {"name": "id"},
            {"name": "username"},
            {"name": "email"},
            {"name": "password_hash"},
            {"name": "role"},
            {"name": "is_active"},
        ]
        mock_count_result = {"count": 5}

        mock_cursor_columns = AsyncMock()
        mock_cursor_columns.fetchall.return_value = mock_columns

        mock_cursor_count = AsyncMock()
        mock_cursor_count.fetchone.return_value = mock_count_result

        mock_conn = AsyncMock()
        mock_conn.execute.side_effect = [mock_cursor_columns, mock_cursor_count]

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.system_service.logger"):
            result = await system_service.verify_database_connection()

        assert result is True

    @pytest.mark.asyncio
    async def test_verify_connection_missing_columns(
        self, system_service, mock_connection
    ):
        """verify_database_connection should return False when columns missing."""
        mock_columns = [
            {"name": "id"},
            {"name": "username"},
        ]  # Missing required columns

        mock_cursor_columns = AsyncMock()
        mock_cursor_columns.fetchall.return_value = mock_columns

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor_columns

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.system_service.logger"):
            result = await system_service.verify_database_connection()

        assert result is False

    @pytest.mark.asyncio
    async def test_verify_connection_logs_missing_columns(
        self, system_service, mock_connection
    ):
        """verify_database_connection should log missing columns."""
        mock_columns = [{"name": "id"}]

        mock_cursor_columns = AsyncMock()
        mock_cursor_columns.fetchall.return_value = mock_columns

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor_columns

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.system_service.logger") as mock_logger:
            await system_service.verify_database_connection()

        mock_logger.error.assert_called_once()
        call_kwargs = mock_logger.error.call_args.kwargs
        assert "missing" in call_kwargs

    @pytest.mark.asyncio
    async def test_verify_connection_db_error_returns_false(
        self, system_service, mock_connection
    ):
        """verify_database_connection should return False on database error."""
        mock_conn = AsyncMock()
        mock_conn.execute.side_effect = Exception("Connection failed")

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.system_service.logger"):
            result = await system_service.verify_database_connection()

        assert result is False

    @pytest.mark.asyncio
    async def test_verify_connection_logs_user_count(
        self, system_service, mock_connection
    ):
        """verify_database_connection should log user count on success."""
        mock_columns = [
            {"name": "id"},
            {"name": "username"},
            {"name": "email"},
            {"name": "password_hash"},
            {"name": "role"},
            {"name": "is_active"},
        ]
        mock_count_result = {"count": 10}

        mock_cursor_columns = AsyncMock()
        mock_cursor_columns.fetchall.return_value = mock_columns

        mock_cursor_count = AsyncMock()
        mock_cursor_count.fetchone.return_value = mock_count_result

        mock_conn = AsyncMock()
        mock_conn.execute.side_effect = [mock_cursor_columns, mock_cursor_count]

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.system_service.logger") as mock_logger:
            await system_service.verify_database_connection()

        mock_logger.info.assert_called_once()
        call_kwargs = mock_logger.info.call_args.kwargs
        assert call_kwargs["user_count"] == 10
