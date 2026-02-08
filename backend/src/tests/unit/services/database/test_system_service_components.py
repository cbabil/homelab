"""
Unit tests for services/database/system_service.py - Component Versions

Tests component version database operations.
"""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

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


class TestGetComponentVersions:
    """Tests for get_component_versions method."""

    @pytest.mark.asyncio
    async def test_get_component_versions_success(
        self, system_service, mock_connection
    ):
        """get_component_versions should return list of component dicts."""
        mock_rows = [
            {
                "component": "backend",
                "version": "1.0.0",
                "updated_at": "2024-01-01",
                "created_at": "2024-01-01",
            },
            {
                "component": "frontend",
                "version": "1.0.0",
                "updated_at": "2024-01-01",
                "created_at": "2024-01-01",
            },
            {
                "component": "api",
                "version": "1.0.0",
                "updated_at": "2024-01-01",
                "created_at": "2024-01-01",
            },
        ]
        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = mock_rows

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        result = await system_service.get_component_versions()

        assert len(result) == 3
        assert result[0]["component"] == "backend"
        assert result[1]["component"] == "frontend"
        assert result[2]["component"] == "api"

    @pytest.mark.asyncio
    async def test_get_component_versions_empty(self, system_service, mock_connection):
        """get_component_versions should return empty list when no components."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = []

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        result = await system_service.get_component_versions()

        assert result == []

    @pytest.mark.asyncio
    async def test_get_component_versions_error_returns_empty(
        self, system_service, mock_connection
    ):
        """get_component_versions should return empty list on error."""
        mock_conn = AsyncMock()
        mock_conn.execute.side_effect = Exception("DB error")

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.system_service.logger"):
            result = await system_service.get_component_versions()

        assert result == []

    @pytest.mark.asyncio
    async def test_get_component_versions_orders_by_component(
        self, system_service, mock_connection
    ):
        """get_component_versions should order results by component."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = []

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        await system_service.get_component_versions()

        call_args = mock_conn.execute.call_args[0]
        sql = call_args[0]
        assert "ORDER BY component" in sql

    @pytest.mark.asyncio
    async def test_get_component_versions_logs_error(
        self, system_service, mock_connection
    ):
        """get_component_versions should log error on exception."""
        mock_conn = AsyncMock()
        mock_conn.execute.side_effect = Exception("Connection failed")

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.system_service.logger") as mock_logger:
            await system_service.get_component_versions()

        mock_logger.error.assert_called_once()
        assert "Connection failed" in str(mock_logger.error.call_args)

    @pytest.mark.asyncio
    async def test_get_component_versions_returns_correct_fields(
        self, system_service, mock_connection
    ):
        """get_component_versions should return only expected fields."""
        mock_rows = [
            {
                "component": "backend",
                "version": "2.0.0",
                "updated_at": "2024-06-01",
                "created_at": "2024-01-01",
                "extra_field": "should_not_appear",
            }
        ]
        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = mock_rows

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        result = await system_service.get_component_versions()

        assert len(result) == 1
        assert set(result[0].keys()) == {
            "component",
            "version",
            "updated_at",
            "created_at",
        }


class TestGetComponentVersion:
    """Tests for get_component_version method."""

    @pytest.mark.asyncio
    async def test_get_component_version_success(self, system_service, mock_connection):
        """get_component_version should return component dict when found."""
        mock_row = {
            "component": "backend",
            "version": "1.2.3",
            "updated_at": "2024-05-01",
            "created_at": "2024-01-01",
        }
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = mock_row

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        result = await system_service.get_component_version("backend")

        assert result is not None
        assert result["component"] == "backend"
        assert result["version"] == "1.2.3"

    @pytest.mark.asyncio
    async def test_get_component_version_not_found(
        self, system_service, mock_connection
    ):
        """get_component_version should return None when not found."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = None

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        result = await system_service.get_component_version("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_component_version_error_returns_none(
        self, system_service, mock_connection
    ):
        """get_component_version should return None on error."""
        mock_conn = AsyncMock()
        mock_conn.execute.side_effect = Exception("DB error")

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.system_service.logger"):
            result = await system_service.get_component_version("backend")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_component_version_uses_parameter(
        self, system_service, mock_connection
    ):
        """get_component_version should use parameterized query."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = None

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        await system_service.get_component_version("frontend")

        call_args = mock_conn.execute.call_args[0]
        params = call_args[1]
        assert params == ("frontend",)

    @pytest.mark.asyncio
    async def test_get_component_version_logs_error_with_component(
        self, system_service, mock_connection
    ):
        """get_component_version should log error with component name."""
        mock_conn = AsyncMock()
        mock_conn.execute.side_effect = Exception("Query failed")

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.system_service.logger") as mock_logger:
            await system_service.get_component_version("api")

        mock_logger.error.assert_called_once()
        call_kwargs = mock_logger.error.call_args.kwargs
        assert call_kwargs["component"] == "api"

    @pytest.mark.asyncio
    async def test_get_component_version_returns_correct_fields(
        self, system_service, mock_connection
    ):
        """get_component_version should return only expected fields."""
        mock_row = {
            "component": "frontend",
            "version": "3.0.0",
            "updated_at": "2024-06-15",
            "created_at": "2024-02-01",
            "extra_field": "ignored",
        }
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = mock_row

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        result = await system_service.get_component_version("frontend")

        assert set(result.keys()) == {
            "component",
            "version",
            "updated_at",
            "created_at",
        }


class TestUpdateComponentVersion:
    """Tests for update_component_version method."""

    @pytest.mark.asyncio
    async def test_update_component_version_success(
        self, system_service, mock_connection
    ):
        """update_component_version should return True on success."""
        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.system_service.logger"):
            result = await system_service.update_component_version("backend", "2.0.0")

        assert result is True
        mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_component_version_uses_parameters(
        self, system_service, mock_connection
    ):
        """update_component_version should use parameterized query."""
        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.system_service.logger"):
            await system_service.update_component_version("frontend", "3.0.0")

        call_args = mock_conn.execute.call_args[0]
        params = call_args[1]
        assert params == ("3.0.0", "frontend")

    @pytest.mark.asyncio
    async def test_update_component_version_error_returns_false(
        self, system_service, mock_connection
    ):
        """update_component_version should return False on error."""
        mock_conn = AsyncMock()
        mock_conn.execute.side_effect = Exception("Update failed")

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.system_service.logger"):
            result = await system_service.update_component_version("backend", "2.0.0")

        assert result is False

    @pytest.mark.asyncio
    async def test_update_component_version_logs_success(
        self, system_service, mock_connection
    ):
        """update_component_version should log success with details."""
        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.system_service.logger") as mock_logger:
            await system_service.update_component_version("api", "1.5.0")

        mock_logger.info.assert_called_once()
        call_kwargs = mock_logger.info.call_args.kwargs
        assert call_kwargs["component"] == "api"
        assert call_kwargs["version"] == "1.5.0"

    @pytest.mark.asyncio
    async def test_update_component_version_logs_error(
        self, system_service, mock_connection
    ):
        """update_component_version should log error on failure."""
        mock_conn = AsyncMock()
        mock_conn.execute.side_effect = Exception("Connection lost")

        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.system_service.logger") as mock_logger:
            await system_service.update_component_version("backend", "2.0.0")

        mock_logger.error.assert_called_once()
        call_kwargs = mock_logger.error.call_args.kwargs
        assert call_kwargs["component"] == "backend"
        assert "Connection lost" in call_kwargs["error"]

    @pytest.mark.asyncio
    async def test_update_component_version_executes_correct_sql(
        self, system_service, mock_connection
    ):
        """update_component_version should execute UPDATE statement."""
        mock_conn = AsyncMock()
        mock_connection.get_connection.return_value = create_mock_context(mock_conn)

        with patch("services.database.system_service.logger"):
            await system_service.update_component_version("backend", "2.0.0")

        call_args = mock_conn.execute.call_args[0]
        sql = call_args[0]
        assert "UPDATE component_versions" in sql
        assert "SET version = ?" in sql
        assert "WHERE component = ?" in sql

    @pytest.mark.asyncio
    async def test_update_component_version_different_components(
        self, system_service, mock_connection
    ):
        """update_component_version should handle different component names."""
        components = ["backend", "frontend", "api", "database"]

        for component in components:
            mock_conn = AsyncMock()
            mock_connection.get_connection.return_value = create_mock_context(mock_conn)
            with patch("services.database.system_service.logger"):
                result = await system_service.update_component_version(
                    component, "1.0.0"
                )
                assert result is True

    @pytest.mark.asyncio
    async def test_update_component_version_semver_formats(
        self, system_service, mock_connection
    ):
        """update_component_version should accept various version formats."""
        versions = [
            "1.0.0",
            "2.3.4",
            "0.1.0-alpha",
            "1.0.0-beta.1",
            "3.0.0-rc.2",
            "v1.0.0",
        ]

        for version in versions:
            mock_conn = AsyncMock()
            mock_connection.get_connection.return_value = create_mock_context(mock_conn)
            with patch("services.database.system_service.logger"):
                result = await system_service.update_component_version(
                    "backend", version
                )
                assert result is True
