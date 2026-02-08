"""
Unit tests for services/database/app_service.py.

Tests AppDatabaseService methods.
"""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.app_catalog import InstallationStatus
from services.database.app_service import AppDatabaseService


@pytest.fixture
def mock_connection():
    """Create mock DatabaseConnection."""
    return MagicMock()


@pytest.fixture
def service(mock_connection):
    """Create AppDatabaseService instance."""
    return AppDatabaseService(mock_connection)


def create_mock_context(mock_conn):
    """Create async context manager for database connection."""

    @asynccontextmanager
    async def context():
        yield mock_conn

    return context()


@pytest.fixture
def sample_installation_row():
    """Create sample installation row from database."""
    return {
        "id": "install-123",
        "server_id": "server-456",
        "app_id": "nginx",
        "container_id": "abc123",
        "container_name": "nginx-container",
        "status": "running",
        "config": '{"port": 8080}',
        "installed_at": "2024-01-15T10:00:00",
        "started_at": "2024-01-15T10:01:00",
        "error_message": None,
    }


@pytest.fixture
def sample_installation_row_with_extras():
    """Create sample installation row with optional fields."""
    return {
        "id": "install-123",
        "server_id": "server-456",
        "app_id": "nginx",
        "container_id": "abc123",
        "container_name": "nginx-container",
        "status": "running",
        "config": '{"port": 8080}',
        "installed_at": "2024-01-15T10:00:00",
        "started_at": "2024-01-15T10:01:00",
        "error_message": None,
        "step_durations": '{"pull": 5, "start": 2}',
        "step_started_at": "2024-01-15T10:00:30",
        "networks": '["bridge", "custom"]',
        "named_volumes": '[{"name": "data"}]',
        "bind_mounts": '[{"source": "/host"}]',
    }


class MockRow(dict):
    """Mock row that supports keys() method."""

    def keys(self):
        return super().keys()


class TestAppDatabaseServiceInit:
    """Tests for AppDatabaseService initialization."""

    def test_init_stores_connection(self, mock_connection):
        """Service should store connection reference."""
        service = AppDatabaseService(mock_connection)
        assert service._conn is mock_connection


class TestCreateInstallation:
    """Tests for create_installation method."""

    @pytest.mark.asyncio
    async def test_create_installation_success(self, service, mock_connection):
        """create_installation should return InstalledApp on success."""
        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.app_service.logger"):
            result = await service.create_installation(
                id="install-123",
                server_id="server-456",
                app_id="nginx",
                container_name="nginx-container",
                status="pending",
                config={"port": 8080},
                installed_at="2024-01-15T10:00:00",
            )

        assert result is not None
        assert result.id == "install-123"
        assert result.status == InstallationStatus.PENDING
        mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_installation_empty_config(self, service, mock_connection):
        """create_installation should handle empty dict config."""
        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.app_service.logger"):
            result = await service.create_installation(
                id="install-123",
                server_id="server-456",
                app_id="nginx",
                container_name="nginx-container",
                status="pending",
                config={},
                installed_at="2024-01-15T10:00:00",
            )

        assert result is not None
        assert result.config == {}

    @pytest.mark.asyncio
    async def test_create_installation_exception(self, service, mock_connection):
        """create_installation should return None on exception."""
        mock_connection.get_connection.side_effect = Exception("DB error")

        with patch("services.database.app_service.logger"):
            result = await service.create_installation(
                id="install-123",
                server_id="s",
                app_id="a",
                container_name="c",
                status="s",
                config={},
                installed_at="t",
            )

        assert result is None


class TestUpdateInstallation:
    """Tests for update_installation method."""

    @pytest.mark.asyncio
    async def test_update_installation_success(self, service, mock_connection):
        """update_installation should return True on success."""
        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.app_service.logger"):
            result = await service.update_installation("install-123", status="running")

        assert result is True
        mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_installation_no_updates(self, service, mock_connection):
        """update_installation should return True when no updates provided."""
        with patch("services.database.app_service.logger"):
            result = await service.update_installation("install-123")

        assert result is True

    @pytest.mark.asyncio
    async def test_update_installation_invalid_column(self, service, mock_connection):
        """update_installation should reject invalid column names."""
        with patch("services.database.app_service.logger"):
            result = await service.update_installation(
                "install-123", invalid_col="value"
            )

        assert result is False

    @pytest.mark.asyncio
    async def test_update_installation_multiple_fields(self, service, mock_connection):
        """update_installation should handle multiple fields."""
        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.app_service.logger"):
            result = await service.update_installation(
                "install-123",
                status="running",
                container_id="new-id",
            )

        assert result is True

    @pytest.mark.asyncio
    async def test_update_installation_exception(self, service, mock_connection):
        """update_installation should return False on exception."""
        mock_connection.get_connection.side_effect = Exception("DB error")

        with patch("services.database.app_service.logger"):
            result = await service.update_installation("install-123", status="running")

        assert result is False


class TestGetInstallation:
    """Tests for get_installation method."""

    @pytest.mark.asyncio
    async def test_get_installation_found(
        self, service, mock_connection, sample_installation_row
    ):
        """get_installation should return InstalledApp when found."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=sample_installation_row)
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.app_service.logger"):
            result = await service.get_installation("server-456", "nginx")

        assert result is not None
        assert result.app_id == "nginx"

    @pytest.mark.asyncio
    async def test_get_installation_not_found(self, service, mock_connection):
        """get_installation should return None when not found."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=None)
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.app_service.logger"):
            result = await service.get_installation("server-456", "nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_installation_casaos_fallback(
        self, service, mock_connection, sample_installation_row
    ):
        """get_installation should try casaos prefix if not found."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(side_effect=[None, sample_installation_row])
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.app_service.logger"):
            result = await service.get_installation("server-456", "app")

        assert result is not None
        assert mock_conn.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_get_installation_already_casaos_prefix(
        self, service, mock_connection
    ):
        """get_installation should not try fallback if already has casaos prefix."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=None)
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.app_service.logger"):
            result = await service.get_installation("server-456", "casaos-app")

        assert result is None
        assert mock_conn.execute.call_count == 1

    @pytest.mark.asyncio
    async def test_get_installation_empty_config(
        self, service, mock_connection, sample_installation_row
    ):
        """get_installation should handle empty config."""
        row = dict(sample_installation_row)
        row["config"] = None
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=row)
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.app_service.logger"):
            result = await service.get_installation("server-456", "nginx")

        assert result.config == {}

    @pytest.mark.asyncio
    async def test_get_installation_exception(self, service, mock_connection):
        """get_installation should return None on exception."""
        mock_connection.get_connection.side_effect = Exception("DB error")

        with patch("services.database.app_service.logger"):
            result = await service.get_installation("server-456", "nginx")

        assert result is None


class TestGetInstallationById:
    """Tests for get_installation_by_id method."""

    @pytest.mark.asyncio
    async def test_get_installation_by_id_found(
        self, service, mock_connection, sample_installation_row_with_extras
    ):
        """get_installation_by_id should return InstalledApp when found."""
        row = MockRow(sample_installation_row_with_extras)
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=row)
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.app_service.logger"):
            result = await service.get_installation_by_id("install-123")

        assert result is not None
        assert result.step_durations == {"pull": 5, "start": 2}
        assert result.networks == ["bridge", "custom"]

    @pytest.mark.asyncio
    async def test_get_installation_by_id_not_found(self, service, mock_connection):
        """get_installation_by_id should return None when not found."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=None)
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.app_service.logger"):
            result = await service.get_installation_by_id("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_installation_by_id_minimal_row(
        self, service, mock_connection, sample_installation_row
    ):
        """get_installation_by_id should handle row without optional fields."""
        row = MockRow(sample_installation_row)
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=row)
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.app_service.logger"):
            result = await service.get_installation_by_id("install-123")

        assert result is not None
        assert result.step_durations is None

    @pytest.mark.asyncio
    async def test_get_installation_by_id_exception(self, service, mock_connection):
        """get_installation_by_id should return None on exception."""
        mock_connection.get_connection.side_effect = Exception("DB error")

        with patch("services.database.app_service.logger"):
            result = await service.get_installation_by_id("install-123")

        assert result is None


class TestGetInstallations:
    """Tests for get_installations method."""

    @pytest.mark.asyncio
    async def test_get_installations_success(
        self, service, mock_connection, sample_installation_row
    ):
        """get_installations should return list of installations."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=[sample_installation_row])
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.app_service.logger"):
            result = await service.get_installations("server-456")

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_installations_empty(self, service, mock_connection):
        """get_installations should return empty list when no installations."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=[])
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.app_service.logger"):
            result = await service.get_installations("server-456")

        assert result == []

    @pytest.mark.asyncio
    async def test_get_installations_exception(self, service, mock_connection):
        """get_installations should return empty list on exception."""
        mock_connection.get_connection.side_effect = Exception("DB error")

        with patch("services.database.app_service.logger"):
            result = await service.get_installations("server-456")

        assert result == []


class TestGetAllInstallations:
    """Tests for get_all_installations method."""

    @pytest.mark.asyncio
    async def test_get_all_installations_success(
        self, service, mock_connection, sample_installation_row_with_extras
    ):
        """get_all_installations should return all installations."""
        row = MockRow(sample_installation_row_with_extras)
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=[row])
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.app_service.logger"):
            result = await service.get_all_installations()

        assert len(result) == 1
        assert result[0].networks == ["bridge", "custom"]

    @pytest.mark.asyncio
    async def test_get_all_installations_empty(self, service, mock_connection):
        """get_all_installations should return empty list when none."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=[])
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.app_service.logger"):
            result = await service.get_all_installations()

        assert result == []

    @pytest.mark.asyncio
    async def test_get_all_installations_exception(self, service, mock_connection):
        """get_all_installations should return empty list on exception."""
        mock_connection.get_connection.side_effect = Exception("DB error")

        with patch("services.database.app_service.logger"):
            result = await service.get_all_installations()

        assert result == []


class TestDeleteInstallation:
    """Tests for delete_installation method."""

    @pytest.mark.asyncio
    async def test_delete_installation_success(self, service, mock_connection):
        """delete_installation should return True on success."""
        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.app_service.logger"):
            result = await service.delete_installation("server-456", "nginx")

        assert result is True
        mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_installation_exception(self, service, mock_connection):
        """delete_installation should return False on exception."""
        mock_connection.get_connection.side_effect = Exception("DB error")

        with patch("services.database.app_service.logger"):
            result = await service.delete_installation("server-456", "nginx")

        assert result is False
