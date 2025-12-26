"""
Credential Encryption Module

Provides AES-256 encryption for sensitive credentials using PBKDF2 key derivation.
Implements security-first credential management as per architectural decisions.
"""

import os
import json
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import structlog


logger = structlog.get_logger("encryption")


class CredentialManager:
    """Manages encrypted credential storage and retrieval."""
    
    def __init__(self, master_password: str = None):
        """Initialize credential manager with master password."""
        if not master_password:
            master_password = os.getenv("HOMELAB_MASTER_PASSWORD", "")
            if not master_password:
                raise ValueError("Master password required for credential encryption")
        
        self.key = self._derive_key(master_password)
        self.cipher = Fernet(self.key)
        logger.info("Credential manager initialized")
    
    def _derive_key(self, password: str) -> bytes:
        """Derive encryption key from password using PBKDF2."""
        password_bytes = password.encode()
        salt = os.getenv("HOMELAB_SALT", "homelab-default-salt").encode()
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
        return key
    
    def encrypt_credentials(self, credentials: dict) -> str:
        """Encrypt credentials dictionary to base64 string."""
        try:
            credentials_json = json.dumps(credentials)
            encrypted_data = self.cipher.encrypt(credentials_json.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error("Failed to encrypt credentials", error=str(e))
            raise
    
    def decrypt_credentials(self, encrypted_data: str) -> dict:
        """Decrypt base64 string to credentials dictionary."""
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self.cipher.decrypt(encrypted_bytes)
            return json.loads(decrypted_data.decode())
        except Exception as e:
            logger.error("Failed to decrypt credentials", error=str(e))
            raise