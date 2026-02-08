"""
Credential Encryption Module

Provides AES-256-GCM encryption with Argon2id key derivation.
Maximum security implementation for sensitive credential storage.

Security features:
- AES-256-GCM: Authenticated encryption (confidentiality + integrity)
- Argon2id: Memory-hard KDF resistant to GPU/ASIC attacks
- Random salt per encryption: No salt reuse
- Random nonce per encryption: Prevents replay attacks
"""

import base64
import json
import os
import secrets

import structlog
from argon2.low_level import Type, hash_secret_raw
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

logger = structlog.get_logger("encryption")

# Argon2id parameters (OWASP recommended)
ARGON2_TIME_COST = 3  # iterations
ARGON2_MEMORY_COST = 65536  # 64 MB
ARGON2_PARALLELISM = 4  # threads
ARGON2_HASH_LEN = 32  # 256 bits for AES-256

# Crypto parameters
SALT_LENGTH = 16  # 128-bit salt
NONCE_LENGTH = 12  # 96-bit nonce (GCM standard)
AAD = b"tomo-credentials-v1"  # Associated Authenticated Data


class CredentialManager:
    """Manages encrypted credential storage with AES-256-GCM and Argon2id."""

    def __init__(self, master_password: str | None = None):
        """Initialize credential manager with master password."""
        if not master_password:
            master_password = os.getenv("TOMO_MASTER_PASSWORD", "")
            if not master_password:
                raise ValueError("Master password required for credential encryption")

        self._master_password = master_password.encode()
        logger.info("Credential manager initialized")

    def _derive_key(self, salt: bytes) -> bytes:
        """Derive 256-bit encryption key using Argon2id."""
        return hash_secret_raw(
            secret=self._master_password,
            salt=salt,
            time_cost=ARGON2_TIME_COST,
            memory_cost=ARGON2_MEMORY_COST,
            parallelism=ARGON2_PARALLELISM,
            hash_len=ARGON2_HASH_LEN,
            type=Type.ID,
        )

    def encrypt_credentials(self, credentials: dict) -> str:
        """
        Encrypt credentials dictionary to base64 string.

        Format: salt(16) + nonce(12) + ciphertext + tag(16)
        """
        try:
            salt = secrets.token_bytes(SALT_LENGTH)
            nonce = secrets.token_bytes(NONCE_LENGTH)

            key = self._derive_key(salt)
            cipher = AESGCM(key)
            plaintext = json.dumps(credentials).encode()
            ciphertext = cipher.encrypt(nonce, plaintext, AAD)

            packed = salt + nonce + ciphertext
            return base64.urlsafe_b64encode(packed).decode()
        except Exception as e:
            logger.error("Failed to encrypt credentials", error=str(e))
            raise

    def decrypt_credentials(self, encrypted_data: str) -> dict:
        """Decrypt base64 string to credentials dictionary."""
        try:
            packed = base64.urlsafe_b64decode(encrypted_data.encode())

            salt = packed[:SALT_LENGTH]
            nonce = packed[SALT_LENGTH : SALT_LENGTH + NONCE_LENGTH]
            ciphertext = packed[SALT_LENGTH + NONCE_LENGTH :]

            key = self._derive_key(salt)
            cipher = AESGCM(key)

            plaintext = cipher.decrypt(nonce, ciphertext, AAD)

            return json.loads(plaintext.decode())
        except Exception as e:
            logger.error("Failed to decrypt credentials", error=str(e))
            raise
