"""Tests for backup CLI commands."""
import pytest
import tempfile
import os
from unittest.mock import AsyncMock, MagicMock, patch
from click.testing import CliRunner


class TestBackupCLI:
    """Tests for backup CLI commands."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    @pytest.fixture
    def mock_backup_service(self):
        """Create mock backup service."""
        svc = MagicMock()
        svc.export_backup = AsyncMock(return_value={
            "success": True,
            "path": "/tmp/backup.enc",
            "checksum": "abc123"
        })
        svc.import_backup = AsyncMock(return_value={
            "success": True,
            "users_imported": 1,
            "servers_imported": 2
        })
        return svc

    def test_export_command(self, runner, mock_backup_service):
        """Should export backup."""
        from cli import export_backup

        with patch('cli.get_backup_service', return_value=mock_backup_service):
            result = runner.invoke(export_backup, [
                '--output', '/tmp/test.enc',
                '--password', 'testpass'
            ])

        assert result.exit_code == 0 or "success" in result.output.lower()

    def test_import_command(self, runner, mock_backup_service):
        """Should import backup."""
        from cli import import_backup

        # Create a dummy file
        with tempfile.NamedTemporaryFile(suffix='.enc', delete=False) as f:
            f.write(b"dummy")
            temp_path = f.name

        try:
            with patch('cli.get_backup_service', return_value=mock_backup_service):
                result = runner.invoke(import_backup, [
                    '--input', temp_path,
                    '--password', 'testpass'
                ])

            assert result.exit_code == 0 or "success" in result.output.lower()
        finally:
            os.unlink(temp_path)
