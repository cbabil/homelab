"""
Unit tests for Encryption Utilities.

Tests credential encryption/decryption with security focus.
Covers key derivation, encryption cycles, and error handling.
"""

import pytest
import os
import json
from unittest.mock import patch, MagicMock
from lib.encryption import CredentialManager


class TestCredentialManager:
    """Test suite for credential encryption functionality."""

    @pytest.fixture
    def test_credentials(self):
        """Sample credentials for testing."""
        return {
            "username": "testuser",
            "password": "secretpassword",
            "private_key": "-----BEGIN RSA PRIVATE KEY-----\ntest\n-----END RSA PRIVATE KEY-----"
        }

    @pytest.fixture
    def credential_manager(self):
        """Create CredentialManager with test password."""
        return CredentialManager("test_master_password")

    def test_credential_manager_init_with_password(self):
        """Test credential manager initialization with explicit password."""
        manager = CredentialManager("test_password")
        assert manager.key is not None
        assert manager.cipher is not None

    def test_credential_manager_init_from_env(self):
        """Test credential manager initialization from environment."""
        with patch.dict(os.environ, {"HOMELAB_MASTER_PASSWORD": "env_password"}):
            manager = CredentialManager()
            assert manager.key is not None
            assert manager.cipher is not None

    def test_credential_manager_init_no_password(self):
        """Test credential manager initialization without password raises error."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Master password required"):
                CredentialManager()

    def test_derive_key_consistent(self, credential_manager):
        """Test key derivation produces consistent results."""
        key1 = credential_manager._derive_key("test_password")
        key2 = credential_manager._derive_key("test_password")
        assert key1 == key2

    def test_derive_key_different_passwords(self, credential_manager):
        """Test different passwords produce different keys."""
        key1 = credential_manager._derive_key("password1")
        key2 = credential_manager._derive_key("password2")
        assert key1 != key2

    @patch.dict(os.environ, {"HOMELAB_SALT": "test_salt"})
    def test_derive_key_with_custom_salt(self, credential_manager):
        """Test key derivation with custom salt."""
        key = credential_manager._derive_key("test_password")
        assert key is not None
        assert len(key) > 0

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
