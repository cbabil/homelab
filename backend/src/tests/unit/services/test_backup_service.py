"""
Unit tests for services/backup_service.py

Tests backup and restore operations with encryption.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.backup_service import BACKUP_VERSION, REQUIRED_FIELDS, BackupService


@pytest.fixture
def mock_db_service():
    """Create mock database service."""
    return MagicMock()


@pytest.fixture
def backup_service(mock_db_service, tmp_path):
    """Create BackupService instance with tmp_path as backup dir."""
    with patch("services.backup_service.logger"):
        return BackupService(mock_db_service, backup_directory=str(tmp_path))


class TestBackupServiceInit:
    """Tests for BackupService initialization."""

    def test_init_stores_db_service(self, mock_db_service):
        """BackupService should store db_service reference."""
        with patch("services.backup_service.logger"):
            service = BackupService(mock_db_service)
            assert service.db_service is mock_db_service

    def test_init_logs_message(self, mock_db_service, tmp_path):
        """BackupService should log initialization."""
        with patch("services.backup_service.logger") as mock_logger:
            BackupService(mock_db_service, backup_directory=str(tmp_path))
            mock_logger.info.assert_called_once()


class TestDeriveKey:
    """Tests for _derive_key method."""

    def test_derive_key_returns_bytes(self, backup_service):
        """_derive_key should return bytes."""
        salt = b"0" * 16
        result = backup_service._derive_key("password", salt)
        assert isinstance(result, bytes)

    def test_derive_key_deterministic(self, backup_service):
        """_derive_key should return same key for same inputs."""
        salt = b"0" * 16
        key1 = backup_service._derive_key("password", salt)
        key2 = backup_service._derive_key("password", salt)
        assert key1 == key2

    def test_derive_key_different_password(self, backup_service):
        """_derive_key should return different key for different password."""
        salt = b"0" * 16
        key1 = backup_service._derive_key("password1", salt)
        key2 = backup_service._derive_key("password2", salt)
        assert key1 != key2

    def test_derive_key_different_salt(self, backup_service):
        """_derive_key should return different key for different salt."""
        key1 = backup_service._derive_key("password", b"0" * 16)
        key2 = backup_service._derive_key("password", b"1" * 16)
        assert key1 != key2


class TestEncryptData:
    """Tests for _encrypt_data method."""

    def test_encrypt_data_returns_bytes(self, backup_service):
        """_encrypt_data should return bytes."""
        data = {"key": "value"}
        result = backup_service._encrypt_data(data, "password")
        assert isinstance(result, bytes)

    def test_encrypt_data_prepends_salt(self, backup_service):
        """_encrypt_data should prepend 16-byte salt."""
        data = {"key": "value"}
        result = backup_service._encrypt_data(data, "password")
        # Encrypted data should be at least 16 bytes (salt) + some ciphertext
        assert len(result) > 16

    def test_encrypt_data_different_each_time(self, backup_service):
        """_encrypt_data should produce different output each time (random salt)."""
        data = {"key": "value"}
        result1 = backup_service._encrypt_data(data, "password")
        result2 = backup_service._encrypt_data(data, "password")
        assert result1 != result2


class TestDecryptData:
    """Tests for _decrypt_data method."""

    def test_decrypt_data_roundtrip(self, backup_service):
        """_decrypt_data should decrypt what _encrypt_data encrypted."""
        original = {"key": "value", "nested": {"a": 1}}
        encrypted = backup_service._encrypt_data(original, "password")
        decrypted = backup_service._decrypt_data(encrypted, "password")
        assert decrypted == original

    def test_decrypt_data_wrong_password(self, backup_service):
        """_decrypt_data should raise ValueError for wrong password."""
        original = {"key": "value"}
        encrypted = backup_service._encrypt_data(original, "password1")

        with pytest.raises(ValueError) as exc_info:
            backup_service._decrypt_data(encrypted, "password2")
        assert "Invalid password or corrupted backup" in str(exc_info.value)


class TestValidateBackup:
    """Tests for _validate_backup method."""

    def test_validate_backup_valid(self, backup_service):
        """_validate_backup should return valid for complete data."""
        data = {
            "version": "1.0",
            "timestamp": "2024-01-01T00:00:00",
            "users": [],
            "servers": [],
            "settings": {},
        }
        result = backup_service._validate_backup(data)
        assert result == {"valid": True}

    def test_validate_backup_missing_version(self, backup_service):
        """_validate_backup should reject missing version."""
        data = {
            "timestamp": "2024-01-01T00:00:00",
            "users": [],
            "servers": [],
            "settings": {},
        }
        result = backup_service._validate_backup(data)
        assert result["valid"] is False
        assert "version" in result["error"]

    def test_validate_backup_missing_multiple_fields(self, backup_service):
        """_validate_backup should list all missing fields."""
        data = {"version": "1.0"}
        result = backup_service._validate_backup(data)
        assert result["valid"] is False
        assert "timestamp" in result["error"]
        assert "users" in result["error"]

    def test_validate_backup_newer_version(self, backup_service):
        """_validate_backup should reject newer version."""
        data = {
            "version": "2.0",
            "timestamp": "2024-01-01T00:00:00",
            "users": [],
            "servers": [],
            "settings": {},
        }
        result = backup_service._validate_backup(data)
        assert result["valid"] is False
        assert "newer" in result["error"]


class TestCollectBackupData:
    """Tests for _collect_backup_data method."""

    @pytest.mark.asyncio
    async def test_collect_backup_data_calls_db_service(
        self, backup_service, mock_db_service
    ):
        """_collect_backup_data should call db_service export methods."""
        mock_db_service.export_users = AsyncMock(return_value=[])
        mock_db_service.export_servers = AsyncMock(return_value=[])
        mock_db_service.export_settings = AsyncMock(return_value={})

        await backup_service._collect_backup_data()

        mock_db_service.export_users.assert_called_once()
        mock_db_service.export_servers.assert_called_once()
        mock_db_service.export_settings.assert_called_once()

    @pytest.mark.asyncio
    async def test_collect_backup_data_returns_structure(
        self, backup_service, mock_db_service
    ):
        """_collect_backup_data should return correct structure."""
        mock_db_service.export_users = AsyncMock(
            return_value=[{"id": "u1", "username": "admin"}]
        )
        mock_db_service.export_servers = AsyncMock(
            return_value=[{"id": "s1", "name": "Server1"}]
        )
        mock_db_service.export_settings = AsyncMock(return_value={"theme": "dark"})

        result = await backup_service._collect_backup_data()

        assert result["version"] == BACKUP_VERSION
        assert "timestamp" in result
        assert result["users"] == [{"id": "u1", "username": "admin"}]
        assert result["servers"] == [{"id": "s1", "name": "Server1"}]
        assert result["settings"] == {"theme": "dark"}
        assert result["app_configs"] == []


class TestExportBackup:
    """Tests for export_backup method."""

    @pytest.mark.asyncio
    async def test_export_backup_success(
        self, backup_service, mock_db_service, tmp_path
    ):
        """export_backup should write encrypted file."""
        mock_db_service.export_users = AsyncMock(return_value=[])
        mock_db_service.export_servers = AsyncMock(return_value=[])
        mock_db_service.export_settings = AsyncMock(return_value={})

        output_path = str(tmp_path / "backup.enc")

        with patch("services.backup_service.logger"):
            result = await backup_service.export_backup(output_path, "password123")

        assert result["success"] is True
        assert result["path"] == output_path
        assert "size" in result
        assert "checksum" in result
        assert "timestamp" in result
        assert (tmp_path / "backup.enc").exists()

    @pytest.mark.asyncio
    async def test_export_backup_creates_file(
        self, backup_service, mock_db_service, tmp_path
    ):
        """export_backup should create readable encrypted file."""
        mock_db_service.export_users = AsyncMock(return_value=[{"id": "u1"}])
        mock_db_service.export_servers = AsyncMock(return_value=[])
        mock_db_service.export_settings = AsyncMock(return_value={})

        output_path = str(tmp_path / "backup.enc")

        with patch("services.backup_service.logger"):
            await backup_service.export_backup(output_path, "password123")

        # File should exist and be readable
        with open(output_path, "rb") as f:
            data = f.read()
        assert len(data) > 16  # At least salt + some data

    @pytest.mark.asyncio
    async def test_export_backup_checksum_matches_size(
        self, backup_service, mock_db_service, tmp_path
    ):
        """export_backup checksum should be 16 chars (SHA256 truncated)."""
        mock_db_service.export_users = AsyncMock(return_value=[])
        mock_db_service.export_servers = AsyncMock(return_value=[])
        mock_db_service.export_settings = AsyncMock(return_value={})

        output_path = str(tmp_path / "backup.enc")

        with patch("services.backup_service.logger"):
            result = await backup_service.export_backup(output_path, "password123")

        assert len(result["checksum"]) == 16

    @pytest.mark.asyncio
    async def test_export_backup_failure(self, backup_service, mock_db_service):
        """export_backup should return error on failure."""
        mock_db_service.export_users = AsyncMock(side_effect=Exception("DB error"))

        with patch("services.backup_service.logger"):
            result = await backup_service.export_backup("/invalid/path", "password")

        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_export_backup_logs_success(
        self, backup_service, mock_db_service, tmp_path
    ):
        """export_backup should log success."""
        mock_db_service.export_users = AsyncMock(return_value=[])
        mock_db_service.export_servers = AsyncMock(return_value=[])
        mock_db_service.export_settings = AsyncMock(return_value={})

        output_path = str(tmp_path / "backup.enc")

        with patch("services.backup_service.logger") as mock_logger:
            await backup_service.export_backup(output_path, "password123")
            mock_logger.info.assert_called_once()
            call_kwargs = mock_logger.info.call_args.kwargs
            assert "path" in call_kwargs
            assert "checksum" in call_kwargs


class TestImportBackup:
    """Tests for import_backup method."""

    @pytest.mark.asyncio
    async def test_import_backup_success(
        self, backup_service, mock_db_service, tmp_path
    ):
        """import_backup should decrypt and import data."""
        # First export a backup
        mock_db_service.export_users = AsyncMock(
            return_value=[{"id": "u1", "username": "admin"}]
        )
        mock_db_service.export_servers = AsyncMock(
            return_value=[{"id": "s1", "name": "Server1"}]
        )
        mock_db_service.export_settings = AsyncMock(return_value={"theme": "dark"})
        mock_db_service.import_users = AsyncMock()
        mock_db_service.import_servers = AsyncMock()
        mock_db_service.import_settings = AsyncMock()

        backup_path = str(tmp_path / "backup.enc")
        with patch("services.backup_service.logger"):
            await backup_service.export_backup(backup_path, "password123")

        # Now import it
        with patch("services.backup_service.logger"):
            result = await backup_service.import_backup(backup_path, "password123")

        assert result["success"] is True
        assert result["version"] == BACKUP_VERSION
        assert "timestamp" in result
        assert result["users_imported"] == 1
        assert result["servers_imported"] == 1

    @pytest.mark.asyncio
    async def test_import_backup_calls_db_service(
        self, backup_service, mock_db_service, tmp_path
    ):
        """import_backup should call db_service import methods."""
        mock_db_service.export_users = AsyncMock(return_value=[{"id": "u1"}])
        mock_db_service.export_servers = AsyncMock(return_value=[{"id": "s1"}])
        mock_db_service.export_settings = AsyncMock(return_value={"k": "v"})
        mock_db_service.import_users = AsyncMock()
        mock_db_service.import_servers = AsyncMock()
        mock_db_service.import_settings = AsyncMock()

        backup_path = str(tmp_path / "backup.enc")
        with patch("services.backup_service.logger"):
            await backup_service.export_backup(backup_path, "password123")
            await backup_service.import_backup(backup_path, "password123")

        mock_db_service.import_users.assert_called_once()
        mock_db_service.import_servers.assert_called_once()
        mock_db_service.import_settings.assert_called_once()

    @pytest.mark.asyncio
    async def test_import_backup_with_overwrite(
        self, backup_service, mock_db_service, tmp_path
    ):
        """import_backup should pass overwrite flag."""
        mock_db_service.export_users = AsyncMock(return_value=[])
        mock_db_service.export_servers = AsyncMock(return_value=[])
        mock_db_service.export_settings = AsyncMock(return_value={})
        mock_db_service.import_users = AsyncMock()
        mock_db_service.import_servers = AsyncMock()
        mock_db_service.import_settings = AsyncMock()

        backup_path = str(tmp_path / "backup.enc")
        with patch("services.backup_service.logger"):
            await backup_service.export_backup(backup_path, "password123")
            await backup_service.import_backup(
                backup_path, "password123", overwrite=True
            )

        mock_db_service.import_users.assert_called_once_with([], overwrite=True)
        mock_db_service.import_servers.assert_called_once_with([], overwrite=True)
        mock_db_service.import_settings.assert_called_once_with({}, overwrite=True)

    @pytest.mark.asyncio
    async def test_import_backup_wrong_password(
        self, backup_service, mock_db_service, tmp_path
    ):
        """import_backup should fail with wrong password."""
        mock_db_service.export_users = AsyncMock(return_value=[])
        mock_db_service.export_servers = AsyncMock(return_value=[])
        mock_db_service.export_settings = AsyncMock(return_value={})

        backup_path = str(tmp_path / "backup.enc")
        with patch("services.backup_service.logger"):
            await backup_service.export_backup(backup_path, "password123")
            result = await backup_service.import_backup(backup_path, "wrongpassword")

        assert result["success"] is False
        assert "Invalid password" in result["error"]

    @pytest.mark.asyncio
    async def test_import_backup_file_not_found(self, backup_service):
        """import_backup should handle missing file."""
        with patch("services.backup_service.logger"):
            result = await backup_service.import_backup("/nonexistent", "password")

        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_import_backup_validation_failure(
        self, backup_service, mock_db_service, tmp_path
    ):
        """import_backup should reject invalid backup data."""
        # Create a backup with missing fields by mocking _collect_backup_data
        backup_path = str(tmp_path / "backup.enc")

        # Write corrupted backup (valid encryption but invalid data)
        invalid_data = {"version": "1.0"}  # Missing required fields
        encrypted = backup_service._encrypt_data(invalid_data, "password")
        with open(backup_path, "wb") as f:
            f.write(encrypted)

        with patch("services.backup_service.logger"):
            result = await backup_service.import_backup(backup_path, "password")

        assert result["success"] is False
        assert "Missing required fields" in result["error"]

    @pytest.mark.asyncio
    async def test_import_backup_newer_version(self, backup_service, tmp_path):
        """import_backup should reject newer version backups."""
        backup_path = str(tmp_path / "backup.enc")

        # Create backup with newer version
        data = {
            "version": "99.0",
            "timestamp": datetime.now(UTC).isoformat(),
            "users": [],
            "servers": [],
            "settings": {},
        }
        encrypted = backup_service._encrypt_data(data, "password")
        with open(backup_path, "wb") as f:
            f.write(encrypted)

        with patch("services.backup_service.logger"):
            result = await backup_service.import_backup(backup_path, "password")

        assert result["success"] is False
        assert "newer" in result["error"]

    @pytest.mark.asyncio
    async def test_import_backup_logs_success(
        self, backup_service, mock_db_service, tmp_path
    ):
        """import_backup should log success."""
        mock_db_service.export_users = AsyncMock(return_value=[])
        mock_db_service.export_servers = AsyncMock(return_value=[])
        mock_db_service.export_settings = AsyncMock(return_value={})
        mock_db_service.import_users = AsyncMock()
        mock_db_service.import_servers = AsyncMock()
        mock_db_service.import_settings = AsyncMock()

        backup_path = str(tmp_path / "backup.enc")
        with patch("services.backup_service.logger"):
            await backup_service.export_backup(backup_path, "password123")

        with patch("services.backup_service.logger") as mock_logger:
            await backup_service.import_backup(backup_path, "password123")
            mock_logger.info.assert_called_once()
            call_kwargs = mock_logger.info.call_args.kwargs
            assert "path" in call_kwargs
            assert "timestamp" in call_kwargs


class TestConstants:
    """Tests for module constants."""

    def test_backup_version_is_string(self):
        """BACKUP_VERSION should be a string."""
        assert isinstance(BACKUP_VERSION, str)

    def test_required_fields_contains_essentials(self):
        """REQUIRED_FIELDS should contain essential fields."""
        assert "version" in REQUIRED_FIELDS
        assert "timestamp" in REQUIRED_FIELDS
        assert "users" in REQUIRED_FIELDS
        assert "servers" in REQUIRED_FIELDS
        assert "settings" in REQUIRED_FIELDS
