"""Token encryption at rest.

Provides secure encryption for storing tokens using machine-derived keys.
"""

import base64
import logging
import os
import secrets

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


class TokenEncryption:
    """Handles encryption of tokens at rest."""

    # Salt for key derivation (can be stored openly)
    SALT_FILE = "/data/.token_salt"
    KEY_ITERATIONS = 480000  # OWASP recommended for PBKDF2

    def __init__(self) -> None:
        """Initialize encryption with machine-derived key."""
        self._fernet: Fernet | None = None

    def _get_machine_id(self) -> bytes:
        """Get a stable machine identifier for key derivation."""
        # Try multiple sources for machine identity
        sources = [
            "/etc/machine-id",
            "/var/lib/dbus/machine-id",
            "/host/etc/machine-id",
        ]

        for source in sources:
            try:
                with open(source, "r") as f:
                    return f.read().strip().encode()
            except (FileNotFoundError, PermissionError):
                continue

        # Fallback to hostname + container ID
        hostname = os.uname().nodename.encode()
        container_id = os.environ.get("HOSTNAME", "unknown").encode()
        return hostname + container_id

    def _get_or_create_salt(self) -> bytes:
        """Get or create the salt for key derivation."""
        try:
            with open(self.SALT_FILE, "rb") as f:
                return f.read()
        except FileNotFoundError:
            salt = secrets.token_bytes(32)
            os.makedirs(os.path.dirname(self.SALT_FILE), exist_ok=True)
            with open(self.SALT_FILE, "wb") as f:
                f.write(salt)
            os.chmod(self.SALT_FILE, 0o600)
            return salt

    def _get_fernet(self) -> Fernet:
        """Get or create the Fernet instance."""
        if self._fernet is None:
            machine_id = self._get_machine_id()
            salt = self._get_or_create_salt()

            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=self.KEY_ITERATIONS,
            )
            key = base64.urlsafe_b64encode(kdf.derive(machine_id))
            self._fernet = Fernet(key)

        return self._fernet

    def encrypt(self, data: str) -> str:
        """Encrypt a string.

        Args:
            data: Plaintext string to encrypt.

        Returns:
            Base64-encoded encrypted data.
        """
        fernet = self._get_fernet()
        return fernet.encrypt(data.encode()).decode()

    def decrypt(self, encrypted: str) -> str:
        """Decrypt an encrypted string.

        Args:
            encrypted: Base64-encoded encrypted data.

        Returns:
            Decrypted plaintext string.
        """
        fernet = self._get_fernet()
        return fernet.decrypt(encrypted.encode()).decode()


# Global encryption instance
_token_encryption = TokenEncryption()


def encrypt_token(token: str) -> str:
    """Encrypt a token for storage."""
    return _token_encryption.encrypt(token)


def decrypt_token(encrypted: str) -> str:
    """Decrypt a stored token."""
    return _token_encryption.decrypt(encrypted)
