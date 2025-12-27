"""
Backup Service

Export and import encrypted backups of all application data.
"""

import json
import os
import hashlib
from datetime import datetime, UTC
from typing import Dict, Any
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import structlog

logger = structlog.get_logger("backup_service")

BACKUP_VERSION = "1.0"
REQUIRED_FIELDS = ["version", "timestamp", "users", "servers", "settings"]


class BackupService:
    """Service for backup and restore operations."""

    def __init__(self, db_service):
        """Initialize backup service."""
        self.db_service = db_service
        logger.info("Backup service initialized")

    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """Derive encryption key from password."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))

    def _encrypt_data(self, data: Dict[str, Any], password: str) -> bytes:
        """Encrypt backup data with password."""
        # Generate random salt
        salt = os.urandom(16)

        # Derive key from password
        key = self._derive_key(password, salt)
        fernet = Fernet(key)

        # Serialize and encrypt
        json_data = json.dumps(data, indent=2).encode('utf-8')
        encrypted = fernet.encrypt(json_data)

        # Prepend salt to encrypted data
        return salt + encrypted

    def _decrypt_data(self, encrypted: bytes, password: str) -> Dict[str, Any]:
        """Decrypt backup data with password."""
        # Extract salt and encrypted data
        salt = encrypted[:16]
        data = encrypted[16:]

        # Derive key from password
        key = self._derive_key(password, salt)
        fernet = Fernet(key)

        # Decrypt and deserialize
        try:
            decrypted = fernet.decrypt(data)
            return json.loads(decrypted.decode('utf-8'))
        except InvalidToken:
            raise ValueError("Invalid password or corrupted backup")

    def _validate_backup(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate backup data structure."""
        missing = [f for f in REQUIRED_FIELDS if f not in data]
        if missing:
            return {
                "valid": False,
                "error": f"Missing required fields: {', '.join(missing)}"
            }

        # Check version compatibility
        version = data.get("version", "0.0")
        if version > BACKUP_VERSION:
            return {
                "valid": False,
                "error": f"Backup version {version} is newer than supported {BACKUP_VERSION}"
            }

        return {"valid": True}

    async def _collect_backup_data(self) -> Dict[str, Any]:
        """Collect all data for backup."""
        users = await self.db_service.export_users()
        servers = await self.db_service.export_servers()
        settings = await self.db_service.export_settings()

        return {
            "version": BACKUP_VERSION,
            "timestamp": datetime.now(UTC).isoformat(),
            "users": users,
            "servers": servers,
            "settings": settings,
            "app_configs": [],  # Future: installed app configurations
        }

    async def export_backup(
        self,
        output_path: str,
        password: str
    ) -> Dict[str, Any]:
        """Export encrypted backup to file."""
        try:
            # Collect data
            data = await self._collect_backup_data()

            # Encrypt
            encrypted = self._encrypt_data(data, password)

            # Write to file
            with open(output_path, 'wb') as f:
                f.write(encrypted)

            # Calculate checksum
            checksum = hashlib.sha256(encrypted).hexdigest()[:16]

            logger.info("Backup exported", path=output_path, checksum=checksum)
            return {
                "success": True,
                "path": output_path,
                "size": len(encrypted),
                "checksum": checksum,
                "timestamp": data["timestamp"]
            }

        except Exception as e:
            logger.error("Export failed", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }

    async def import_backup(
        self,
        input_path: str,
        password: str,
        overwrite: bool = False
    ) -> Dict[str, Any]:
        """Import backup from encrypted file."""
        try:
            # Read file
            with open(input_path, 'rb') as f:
                encrypted = f.read()

            # Decrypt
            data = self._decrypt_data(encrypted, password)

            # Validate
            validation = self._validate_backup(data)
            if not validation["valid"]:
                return {"success": False, "error": validation["error"]}

            # Import data
            await self.db_service.import_users(data["users"], overwrite=overwrite)
            await self.db_service.import_servers(data["servers"], overwrite=overwrite)
            await self.db_service.import_settings(data["settings"], overwrite=overwrite)

            logger.info("Backup imported", path=input_path, timestamp=data["timestamp"])
            return {
                "success": True,
                "version": data["version"],
                "timestamp": data["timestamp"],
                "users_imported": len(data["users"]),
                "servers_imported": len(data["servers"])
            }

        except ValueError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error("Import failed", error=str(e))
            return {"success": False, "error": str(e)}
