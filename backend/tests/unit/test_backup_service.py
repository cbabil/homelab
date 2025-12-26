"""Tests for backup service."""
import pytest
import json
import tempfile
import os
from unittest.mock import AsyncMock, MagicMock, patch
from services.backup_service import BackupService


class TestBackupService:
    """Tests for BackupService."""

    @pytest.fixture
    def mock_db_service(self):
        """Create mock database service."""
        db = MagicMock()
        db.export_users = AsyncMock(return_value=[
            {"id": "u1", "username": "admin", "role": "admin"}
        ])
        db.export_servers = AsyncMock(return_value=[
            {"id": "s1", "name": "server1", "host": "192.168.1.1"}
        ])
        db.export_settings = AsyncMock(return_value={"theme": "dark"})
        db.import_users = AsyncMock()
        db.import_servers = AsyncMock()
        db.import_settings = AsyncMock()
        return db

    @pytest.fixture
    def backup_service(self, mock_db_service):
        """Create backup service with mocks."""
        return BackupService(db_service=mock_db_service)

    def test_create_backup_data(self, backup_service, mock_db_service):
        """Should create backup data structure."""
        import asyncio
        data = asyncio.get_event_loop().run_until_complete(
            backup_service._collect_backup_data()
        )

        assert "version" in data
        assert "timestamp" in data
        assert "users" in data
        assert "servers" in data

    def test_encrypt_backup(self, backup_service):
        """Should encrypt backup data."""
        data = {"test": "data"}
        password = "testpassword123"

        encrypted = backup_service._encrypt_data(data, password)

        assert encrypted != json.dumps(data).encode()
        assert len(encrypted) > 0

    def test_decrypt_backup(self, backup_service):
        """Should decrypt backup data."""
        original_data = {"test": "data", "nested": {"key": "value"}}
        password = "testpassword123"

        encrypted = backup_service._encrypt_data(original_data, password)
        decrypted = backup_service._decrypt_data(encrypted, password)

        assert decrypted == original_data

    def test_decrypt_wrong_password(self, backup_service):
        """Should fail with wrong password."""
        data = {"test": "data"}
        encrypted = backup_service._encrypt_data(data, "correct")

        with pytest.raises(Exception):
            backup_service._decrypt_data(encrypted, "wrong")

    def test_validate_backup_structure(self, backup_service):
        """Should validate backup structure."""
        valid_backup = {
            "version": "1.0",
            "timestamp": "2025-01-01T00:00:00Z",
            "users": [],
            "servers": [],
            "settings": {}
        }

        result = backup_service._validate_backup(valid_backup)
        assert result["valid"] is True

    def test_validate_backup_missing_fields(self, backup_service):
        """Should reject backup with missing fields."""
        invalid_backup = {"version": "1.0"}

        result = backup_service._validate_backup(invalid_backup)
        assert result["valid"] is False

    @pytest.mark.asyncio
    async def test_export_backup(self, backup_service):
        """Should export backup to file."""
        with tempfile.NamedTemporaryFile(suffix='.enc', delete=False) as f:
            output_path = f.name

        try:
            result = await backup_service.export_backup(
                output_path=output_path,
                password="testpassword"
            )

            assert result["success"] is True
            assert os.path.exists(output_path)
            assert os.path.getsize(output_path) > 0
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    @pytest.mark.asyncio
    async def test_import_backup(self, backup_service, mock_db_service):
        """Should import backup from file."""
        # First create a backup
        with tempfile.NamedTemporaryFile(suffix='.enc', delete=False) as f:
            output_path = f.name

        try:
            await backup_service.export_backup(output_path, "testpassword")

            result = await backup_service.import_backup(
                input_path=output_path,
                password="testpassword"
            )

            assert result["success"] is True
            mock_db_service.import_users.assert_called()
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)
