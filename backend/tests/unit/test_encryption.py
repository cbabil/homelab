"""
Unit tests for Encryption Utilities.

Tests credential encryption/decryption with security focus.
Covers key derivation, encryption cycles, and error handling.
"""

import pytest
import os
import json
from unittest.mock import patch
from lib.encryption import CredentialManager


class TestCredentialManager:
    """Test suite for credential encryption functionality."""

    @pytest.fixture
    def test_credentials(self):
        """Sample credentials for testing."""
        return {
            "username": "testuser",
            "password": "secretpassword",
            "private_key": "-----BEGIN RSA PRIVATE KEY-----\ntest\n-----END RSA PRIVATE KEY-----",
        }

    @pytest.fixture
    def credential_manager(self):
        """Create CredentialManager with test password."""
        return CredentialManager("test_master_password")

    def test_credential_manager_init_with_password(self):
        """Test credential manager initialization with explicit password."""
        manager = CredentialManager("test_password")
        assert manager._master_password is not None
        assert manager._master_password == b"test_password"

    def test_credential_manager_init_from_env(self):
        """Test credential manager initialization from environment."""
        with patch.dict(os.environ, {"TOMO_MASTER_PASSWORD": "env_password"}):
            manager = CredentialManager()
            assert manager._master_password is not None
            assert manager._master_password == b"env_password"

    def test_credential_manager_init_no_password(self):
        """Test credential manager initialization without password raises error."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Master password required"):
                CredentialManager()

    def test_derive_key_consistent(self, credential_manager):
        """Test key derivation produces consistent results with same salt."""
        salt = b"0123456789abcdef"  # 16 bytes
        key1 = credential_manager._derive_key(salt)
        key2 = credential_manager._derive_key(salt)
        assert key1 == key2

    def test_derive_key_different_salts(self, credential_manager):
        """Test different salts produce different keys."""
        salt1 = b"0123456789abcdef"
        salt2 = b"fedcba9876543210"
        key1 = credential_manager._derive_key(salt1)
        key2 = credential_manager._derive_key(salt2)
        assert key1 != key2

    def test_derive_key_returns_correct_length(self, credential_manager):
        """Test key derivation returns 32 bytes for AES-256."""
        salt = b"0123456789abcdef"
        key = credential_manager._derive_key(salt)
        assert key is not None
        assert len(key) == 32  # 256 bits for AES-256

    def test_encrypt_decrypt_cycle(self, credential_manager, test_credentials):
        """Test complete encrypt-decrypt cycle maintains data integrity."""
        encrypted = credential_manager.encrypt_credentials(test_credentials)
        decrypted = credential_manager.decrypt_credentials(encrypted)

        assert decrypted == test_credentials
        assert isinstance(encrypted, str)
        assert len(encrypted) > 0

    def test_encrypt_credentials_success(self, credential_manager, test_credentials):
        """Test successful credential encryption."""
        encrypted = credential_manager.encrypt_credentials(test_credentials)

        assert isinstance(encrypted, str)
        assert len(encrypted) > 0
        assert encrypted != json.dumps(test_credentials)

    def test_decrypt_credentials_success(self, credential_manager, test_credentials):
        """Test successful credential decryption."""
        encrypted = credential_manager.encrypt_credentials(test_credentials)
        decrypted = credential_manager.decrypt_credentials(encrypted)

        assert decrypted == test_credentials

    def test_encrypt_empty_credentials(self, credential_manager):
        """Test encrypting empty credentials dictionary."""
        empty_creds = {}
        encrypted = credential_manager.encrypt_credentials(empty_creds)
        decrypted = credential_manager.decrypt_credentials(encrypted)

        assert decrypted == empty_creds

    def test_decrypt_invalid_data_raises_error(self, credential_manager):
        """Test decryption of invalid data raises exception."""
        with pytest.raises(Exception):
            credential_manager.decrypt_credentials("invalid_base64_data!!!")

    def test_decrypt_wrong_password_raises_error(
        self, credential_manager, test_credentials
    ):
        """Test decryption with wrong password raises exception."""
        encrypted = credential_manager.encrypt_credentials(test_credentials)

        wrong_manager = CredentialManager("wrong_password")
        with pytest.raises(Exception):
            wrong_manager.decrypt_credentials(encrypted)

    def test_decrypt_corrupted_ciphertext_raises_error(self, credential_manager):
        """Test decryption of corrupted ciphertext raises exception."""
        import base64

        # Create a valid-looking but corrupted payload
        fake_salt = b"0123456789abcdef"  # 16 bytes
        fake_nonce = b"012345678901"  # 12 bytes
        fake_ciphertext = b"corrupted_data"
        packed = fake_salt + fake_nonce + fake_ciphertext
        corrupted = base64.urlsafe_b64encode(packed).decode()

        with pytest.raises(Exception):
            credential_manager.decrypt_credentials(corrupted)

    def test_encrypt_non_serializable_raises_error(self, credential_manager):
        """Test encryption of non-JSON-serializable data raises exception."""
        # Create non-serializable data
        non_serializable = {"func": lambda x: x}

        with pytest.raises(Exception):
            credential_manager.encrypt_credentials(non_serializable)
