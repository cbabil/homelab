"""
Backup Tools Unit Tests

Tests for backup tools: export_backup, import_backup.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tools.backup.tools import BackupTools


@pytest.fixture
def mock_backup_service():
    """Create mock backup service."""
    service = MagicMock()
    service.export_backup = AsyncMock()
    service.import_backup = AsyncMock()
    return service


@pytest.fixture
def backup_tools(mock_backup_service):
    """Create BackupTools instance."""
    return BackupTools(mock_backup_service)


class TestBackupToolsInit:
    """Tests for BackupTools initialization."""

    def test_initialization(self, mock_backup_service):
        """Test BackupTools is initialized correctly."""
        tools = BackupTools(mock_backup_service)
        assert tools.backup_service == mock_backup_service


class TestExportBackup:
    """Tests for the export_backup tool."""

    @pytest.mark.asyncio
    async def test_export_backup_success(self, mock_backup_service):
        """Test successful backup export."""
        mock_backup_service.export_backup = AsyncMock(
            return_value={
                "success": True,
                "path": "/backups/tomo-2024-01-15.enc",
                "checksum": "abc123def456",
                "size": 1024000,
                "timestamp": "2024-01-15T10:30:00Z",
            }
        )

        tools = BackupTools(mock_backup_service)

        with patch("tools.backup.tools.log_event", new_callable=AsyncMock):
            result = await tools.export_backup(
                output_path="/backups/tomo-2024-01-15.enc", password="securepass123"
            )

        assert result["success"] is True
        assert result["data"]["path"] == "/backups/tomo-2024-01-15.enc"
        assert result["data"]["checksum"] == "abc123def456"
        assert result["data"]["size"] == 1024000
        assert "Backup exported successfully" in result["message"]

    @pytest.mark.asyncio
    async def test_export_backup_logs_success(self, mock_backup_service):
        """Test that successful export is logged."""
        mock_backup_service.export_backup = AsyncMock(
            return_value={
                "success": True,
                "path": "/backups/backup.enc",
                "checksum": "abc123",
                "size": 500,
                "timestamp": "2024-01-15T10:30:00Z",
            }
        )

        tools = BackupTools(mock_backup_service)

        with patch("tools.backup.tools.log_event", new_callable=AsyncMock) as mock_log:
            await tools.export_backup(
                output_path="/backups/backup.enc", password="pass123"
            )

        mock_log.assert_called_once()
        assert mock_log.call_args[0][1] == "INFO"

    @pytest.mark.asyncio
    async def test_export_backup_service_failure(self, mock_backup_service):
        """Test backup export when service returns failure."""
        mock_backup_service.export_backup = AsyncMock(
            return_value={"success": False, "error": "Insufficient disk space"}
        )

        tools = BackupTools(mock_backup_service)

        with patch("tools.backup.tools.log_event", new_callable=AsyncMock):
            result = await tools.export_backup(
                output_path="/backups/backup.enc", password="pass123"
            )

        assert result["success"] is False
        assert result["error"] == "EXPORT_FAILED"
        assert "Insufficient disk space" in result["message"]

    @pytest.mark.asyncio
    async def test_export_backup_failure_logs_error(self, mock_backup_service):
        """Test that failed export is logged."""
        mock_backup_service.export_backup = AsyncMock(
            return_value={"success": False, "error": "Disk full"}
        )

        tools = BackupTools(mock_backup_service)

        with patch("tools.backup.tools.log_event", new_callable=AsyncMock) as mock_log:
            await tools.export_backup(
                output_path="/backups/backup.enc", password="pass123"
            )

        mock_log.assert_called_once()
        assert mock_log.call_args[0][1] == "ERROR"

    @pytest.mark.asyncio
    async def test_export_backup_exception(self, mock_backup_service):
        """Test backup export when exception occurs."""
        mock_backup_service.export_backup = AsyncMock(
            side_effect=Exception("Database connection lost")
        )

        tools = BackupTools(mock_backup_service)

        with patch("tools.backup.tools.log_event", new_callable=AsyncMock):
            result = await tools.export_backup(
                output_path="/backups/backup.enc", password="pass123"
            )

        assert result["success"] is False
        assert result["error"] == "EXPORT_ERROR"
        # Error message should be sanitized (no raw exception details)
        assert "Database connection lost" not in result["message"]
        assert "Backup export failed" in result["message"]


class TestImportBackup:
    """Tests for the import_backup tool."""

    @pytest.mark.asyncio
    async def test_import_backup_success(self, mock_backup_service):
        """Test successful backup import."""
        mock_backup_service.import_backup = AsyncMock(
            return_value={
                "success": True,
                "version": "1.0.0",
                "timestamp": "2024-01-15T10:30:00Z",
                "users_imported": 5,
                "servers_imported": 10,
            }
        )

        tools = BackupTools(mock_backup_service)

        with patch("tools.backup.tools.log_event", new_callable=AsyncMock):
            result = await tools.import_backup(
                input_path="/backups/tomo-2024-01-15.enc", password="securepass123"
            )

        assert result["success"] is True
        assert result["data"]["version"] == "1.0.0"
        assert result["data"]["users_imported"] == 5
        assert result["data"]["servers_imported"] == 10
        assert "Backup imported successfully" in result["message"]

    @pytest.mark.asyncio
    async def test_import_backup_logs_success(self, mock_backup_service):
        """Test that successful import is logged."""
        mock_backup_service.import_backup = AsyncMock(
            return_value={
                "success": True,
                "version": "1.0.0",
                "timestamp": "2024-01-15T10:30:00Z",
                "users_imported": 3,
                "servers_imported": 5,
            }
        )

        tools = BackupTools(mock_backup_service)

        with patch("tools.backup.tools.log_event", new_callable=AsyncMock) as mock_log:
            await tools.import_backup(
                input_path="/backups/backup.enc", password="pass123"
            )

        mock_log.assert_called_once()
        assert mock_log.call_args[0][1] == "INFO"

    @pytest.mark.asyncio
    async def test_import_backup_with_overwrite(self, mock_backup_service):
        """Test backup import with overwrite option."""
        mock_backup_service.import_backup = AsyncMock(
            return_value={
                "success": True,
                "version": "1.0.0",
                "timestamp": "2024-01-15T10:30:00Z",
                "users_imported": 3,
                "servers_imported": 7,
            }
        )

        tools = BackupTools(mock_backup_service)

        with patch("tools.backup.tools.log_event", new_callable=AsyncMock):
            result = await tools.import_backup(
                input_path="/backups/backup.enc", password="pass123", overwrite=True
            )

        assert result["success"] is True
        mock_backup_service.import_backup.assert_called_once_with(
            "/backups/backup.enc", "pass123", True
        )

    @pytest.mark.asyncio
    async def test_import_backup_service_failure(self, mock_backup_service):
        """Test backup import when service returns failure."""
        mock_backup_service.import_backup = AsyncMock(
            return_value={"success": False, "error": "Invalid password"}
        )

        tools = BackupTools(mock_backup_service)

        with patch("tools.backup.tools.log_event", new_callable=AsyncMock):
            result = await tools.import_backup(
                input_path="/backups/backup.enc", password="wrongpass"
            )

        assert result["success"] is False
        assert result["error"] == "IMPORT_FAILED"
        assert "Invalid password" in result["message"]

    @pytest.mark.asyncio
    async def test_import_backup_failure_logs_error(self, mock_backup_service):
        """Test that failed import is logged."""
        mock_backup_service.import_backup = AsyncMock(
            return_value={"success": False, "error": "Bad password"}
        )

        tools = BackupTools(mock_backup_service)

        with patch("tools.backup.tools.log_event", new_callable=AsyncMock) as mock_log:
            await tools.import_backup(
                input_path="/backups/backup.enc", password="wrong"
            )

        mock_log.assert_called_once()
        assert mock_log.call_args[0][1] == "ERROR"

    @pytest.mark.asyncio
    async def test_import_backup_file_not_found(self, mock_backup_service):
        """Test backup import when file doesn't exist."""
        mock_backup_service.import_backup = AsyncMock(
            return_value={"success": False, "error": "Backup file not found"}
        )

        tools = BackupTools(mock_backup_service)

        with patch("tools.backup.tools.log_event", new_callable=AsyncMock):
            result = await tools.import_backup(
                input_path="/backups/nonexistent.enc", password="pass123"
            )

        assert result["success"] is False
        assert result["error"] == "IMPORT_FAILED"
        assert "not found" in result["message"]

    @pytest.mark.asyncio
    async def test_import_backup_exception(self, mock_backup_service):
        """Test backup import when exception occurs."""
        mock_backup_service.import_backup = AsyncMock(
            side_effect=Exception("Corrupted backup file")
        )

        tools = BackupTools(mock_backup_service)

        with patch("tools.backup.tools.log_event", new_callable=AsyncMock):
            result = await tools.import_backup(
                input_path="/backups/corrupted.enc", password="pass123"
            )

        assert result["success"] is False
        assert result["error"] == "IMPORT_ERROR"
        # Error message should be sanitized (no raw exception details)
        assert "Corrupted backup file" not in result["message"]
        assert "Backup import failed" in result["message"]
