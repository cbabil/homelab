"""Tests for backup MCP tools."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from tools.backup_tools import BackupTools


@pytest.fixture
def mock_backup_service():
    """Create mock backup service."""
    svc = MagicMock()
    svc.export_backup = AsyncMock(return_value={
        "success": True,
        "path": "/tmp/backup.enc",
        "checksum": "abc123",
        "size": 1024,
        "timestamp": "2025-12-26T12:00:00Z"
    })
    svc.import_backup = AsyncMock(return_value={
        "success": True,
        "version": "1.0",
        "timestamp": "2025-12-26T12:00:00Z",
        "users_imported": 1,
        "servers_imported": 2
    })
    return svc


@pytest.fixture
def backup_tools(mock_backup_service):
    """Create backup tools with mocks."""
    return BackupTools(backup_service=mock_backup_service)


class TestExportBackup:
    """Tests for export_backup tool."""

    @pytest.mark.asyncio
    async def test_export_success(self, backup_tools, mock_backup_service):
        """Should export backup successfully."""
        result = await backup_tools.export_backup(
            output_path="/tmp/backup.enc",
            password="testpass"
        )

        assert result["success"] is True
        assert "path" in result["data"]

    @pytest.mark.asyncio
    async def test_export_failure(self, backup_tools, mock_backup_service):
        """Should handle export failure."""
        mock_backup_service.export_backup.return_value = {
            "success": False,
            "error": "Disk full"
        }

        result = await backup_tools.export_backup(
            output_path="/tmp/backup.enc",
            password="testpass"
        )

        assert result["success"] is False


class TestImportBackup:
    """Tests for import_backup tool."""

    @pytest.mark.asyncio
    async def test_import_success(self, backup_tools, mock_backup_service):
        """Should import backup successfully."""
        result = await backup_tools.import_backup(
            input_path="/tmp/backup.enc",
            password="testpass"
        )

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_import_wrong_password(self, backup_tools, mock_backup_service):
        """Should handle wrong password."""
        mock_backup_service.import_backup.return_value = {
            "success": False,
            "error": "Invalid password"
        }

        result = await backup_tools.import_backup(
            input_path="/tmp/backup.enc",
            password="wrongpass"
        )

        assert result["success"] is False
