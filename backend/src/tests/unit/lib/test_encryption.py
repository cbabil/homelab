"""
Unit tests for lib/encryption.py

Tests credential encryption/decryption with AES-256-GCM and Argon2id.
"""

import base64
import os
from unittest.mock import patch

import pytest

from lib.encryption import (
    ARGON2_HASH_LEN,
    ARGON2_MEMORY_COST,
    ARGON2_PARALLELISM,
    ARGON2_TIME_COST,
    NONCE_LENGTH,
    SALT_LENGTH,
    CredentialManager,
)


@pytest.fixture
def clean_env():
    """Fixture to save and restore environment variables."""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)


class TestCryptoConstants:
    """Tests for cryptographic constants."""

    def test_argon2_time_cost(self):
        """ARGON2_TIME_COST should be 3 (OWASP recommended)."""
        assert ARGON2_TIME_COST == 3

    def test_argon2_memory_cost(self):
        """ARGON2_MEMORY_COST should be 64MB (65536 KB)."""
        assert ARGON2_MEMORY_COST == 65536

    def test_argon2_parallelism(self):
        """ARGON2_PARALLELISM should be 4 threads."""
        assert ARGON2_PARALLELISM == 4

    def test_argon2_hash_len(self):
        """ARGON2_HASH_LEN should be 32 bytes (256 bits for AES-256)."""
        assert ARGON2_HASH_LEN == 32

    def test_salt_length(self):
        """SALT_LENGTH should be 16 bytes (128 bits)."""
        assert SALT_LENGTH == 16

    def test_nonce_length(self):
        """NONCE_LENGTH should be 12 bytes (96 bits, GCM standard)."""
        assert NONCE_LENGTH == 12


class TestCredentialManagerInit:
    """Tests for CredentialManager initialization."""

    def test_init_with_explicit_password(self, clean_env):
        """CredentialManager should initialize with explicit password."""
        manager = CredentialManager("test_password")
        assert manager._master_password == b"test_password"

    def test_init_from_env_variable(self, clean_env):
        """CredentialManager should use TOMO_MASTER_PASSWORD from env."""
        os.environ["TOMO_MASTER_PASSWORD"] = "env_password"
        manager = CredentialManager()
        assert manager._master_password == b"env_password"

    def test_init_no_password_raises(self, clean_env):
        """CredentialManager should raise ValueError if no password."""
        os.environ.pop("TOMO_MASTER_PASSWORD", None)
        with pytest.raises(ValueError) as exc_info:
            CredentialManager()
        assert "Master password required" in str(exc_info.value)

    def test_init_empty_string_from_env_raises(self, clean_env):
        """CredentialManager should raise for empty env password."""
        os.environ["TOMO_MASTER_PASSWORD"] = ""
        with pytest.raises(ValueError) as exc_info:
            CredentialManager()
        assert "Master password required" in str(exc_info.value)

    def test_init_none_password_uses_env(self, clean_env):
        """CredentialManager with None should try env variable."""
        os.environ["TOMO_MASTER_PASSWORD"] = "from_env"
        manager = CredentialManager(None)
        assert manager._master_password == b"from_env"


class TestDeriveKey:
    """Tests for _derive_key method."""

    @pytest.fixture
    def manager(self, clean_env):
        """Create CredentialManager for testing."""
        return CredentialManager("test_master_password")

    def test_derive_key_returns_bytes(self, manager):
        """_derive_key should return bytes."""
        salt = os.urandom(SALT_LENGTH)
        key = manager._derive_key(salt)
        assert isinstance(key, bytes)

    def test_derive_key_correct_length(self, manager):
        """_derive_key should return 256-bit (32 bytes) key."""
        salt = os.urandom(SALT_LENGTH)
        key = manager._derive_key(salt)
        assert len(key) == 32

    def test_derive_key_same_salt_same_key(self, manager):
        """_derive_key should produce same key with same salt."""
        salt = os.urandom(SALT_LENGTH)
        key1 = manager._derive_key(salt)
        key2 = manager._derive_key(salt)
        assert key1 == key2

    def test_derive_key_different_salt_different_key(self, manager):
        """_derive_key should produce different keys with different salts."""
        salt1 = os.urandom(SALT_LENGTH)
        salt2 = os.urandom(SALT_LENGTH)
        key1 = manager._derive_key(salt1)
        key2 = manager._derive_key(salt2)
        assert key1 != key2

    def test_derive_key_different_password_different_key(self, clean_env):
        """Different passwords should produce different keys."""
        salt = os.urandom(SALT_LENGTH)
        manager1 = CredentialManager("password1")
        manager2 = CredentialManager("password2")
        key1 = manager1._derive_key(salt)
        key2 = manager2._derive_key(salt)
        assert key1 != key2


class TestEncryptCredentials:
    """Tests for encrypt_credentials method."""

    @pytest.fixture
    def manager(self, clean_env):
        """Create CredentialManager for testing."""
        return CredentialManager("test_master_password")

    @pytest.fixture
    def sample_credentials(self):
        """Sample credentials for testing."""
        return {
            "username": "testuser",
            "password": "secretpassword",
            "api_key": "abc123xyz",
        }

    def test_encrypt_returns_string(self, manager, sample_credentials):
        """encrypt_credentials should return a string."""
        result = manager.encrypt_credentials(sample_credentials)
        assert isinstance(result, str)

    def test_encrypt_returns_base64(self, manager, sample_credentials):
        """encrypt_credentials should return valid base64."""
        result = manager.encrypt_credentials(sample_credentials)
        # Should not raise on decode
        decoded = base64.urlsafe_b64decode(result.encode())
        assert isinstance(decoded, bytes)

    def test_encrypt_output_not_plaintext(self, manager, sample_credentials):
        """encrypt_credentials output should not contain plaintext."""
        result = manager.encrypt_credentials(sample_credentials)
        assert "testuser" not in result
        assert "secretpassword" not in result

    def test_encrypt_different_each_time(self, manager, sample_credentials):
        """encrypt_credentials should produce different output each time."""
        result1 = manager.encrypt_credentials(sample_credentials)
        result2 = manager.encrypt_credentials(sample_credentials)
        assert result1 != result2

    def test_encrypt_empty_dict(self, manager):
        """encrypt_credentials should handle empty dictionary."""
        result = manager.encrypt_credentials({})
        assert isinstance(result, str)
        assert len(result) > 0

    def test_encrypt_nested_dict(self, manager):
        """encrypt_credentials should handle nested dictionaries."""
        nested = {"level1": {"level2": {"value": "deep"}}}
        result = manager.encrypt_credentials(nested)
        decrypted = manager.decrypt_credentials(result)
        assert decrypted == nested

    def test_encrypt_special_characters(self, manager):
        """encrypt_credentials should handle special characters."""
        special = {"password": "p@$$w0rd!#%^&*()", "unicode": "пароль123"}
        result = manager.encrypt_credentials(special)
        decrypted = manager.decrypt_credentials(result)
        assert decrypted == special

    def test_encrypt_output_contains_salt_nonce(self, manager, sample_credentials):
        """encrypt_credentials output should contain salt and nonce."""
        result = manager.encrypt_credentials(sample_credentials)
        decoded = base64.urlsafe_b64decode(result.encode())
        # Output format: salt(16) + nonce(12) + ciphertext + tag(16)
        assert len(decoded) >= SALT_LENGTH + NONCE_LENGTH + 16

    def test_encrypt_exception_handling(self, manager):
        """encrypt_credentials should re-raise exceptions."""
        with patch("lib.encryption.AESGCM") as mock_aesgcm:
            mock_aesgcm.return_value.encrypt.side_effect = Exception("Encryption error")
            with pytest.raises(Exception) as exc_info:
                manager.encrypt_credentials({"key": "value"})
            assert "Encryption error" in str(exc_info.value)


class TestDecryptCredentials:
    """Tests for decrypt_credentials method."""

    @pytest.fixture
    def manager(self, clean_env):
        """Create CredentialManager for testing."""
        return CredentialManager("test_master_password")

    @pytest.fixture
    def sample_credentials(self):
        """Sample credentials for testing."""
        return {"username": "testuser", "password": "secretpassword"}

    def test_decrypt_returns_dict(self, manager, sample_credentials):
        """decrypt_credentials should return a dictionary."""
        encrypted = manager.encrypt_credentials(sample_credentials)
        result = manager.decrypt_credentials(encrypted)
        assert isinstance(result, dict)

    def test_decrypt_roundtrip(self, manager, sample_credentials):
        """decrypt_credentials should recover original data."""
        encrypted = manager.encrypt_credentials(sample_credentials)
        result = manager.decrypt_credentials(encrypted)
        assert result == sample_credentials

    def test_decrypt_wrong_password_fails(self, clean_env, sample_credentials):
        """decrypt_credentials should fail with wrong password."""
        manager1 = CredentialManager("correct_password")
        manager2 = CredentialManager("wrong_password")

        encrypted = manager1.encrypt_credentials(sample_credentials)
        with pytest.raises(Exception):
            manager2.decrypt_credentials(encrypted)

    def test_decrypt_invalid_base64_fails(self, manager):
        """decrypt_credentials should fail with invalid base64."""
        with pytest.raises(Exception):
            manager.decrypt_credentials("not_valid_base64!!!")

    def test_decrypt_truncated_data_fails(self, manager, sample_credentials):
        """decrypt_credentials should fail with truncated data."""
        encrypted = manager.encrypt_credentials(sample_credentials)
        truncated = encrypted[:20]
        with pytest.raises(Exception):
            manager.decrypt_credentials(truncated)

    def test_decrypt_modified_ciphertext_fails(self, manager, sample_credentials):
        """decrypt_credentials should fail if ciphertext is modified."""
        encrypted = manager.encrypt_credentials(sample_credentials)
        decoded = base64.urlsafe_b64decode(encrypted.encode())
        # Modify a byte in the ciphertext area
        modified = decoded[:-5] + bytes([decoded[-5] ^ 0xFF]) + decoded[-4:]
        modified_encrypted = base64.urlsafe_b64encode(modified).decode()
        with pytest.raises(Exception):
            manager.decrypt_credentials(modified_encrypted)


class TestEncryptDecryptIntegration:
    """Integration tests for encrypt/decrypt cycle."""

    @pytest.fixture
    def manager(self, clean_env):
        """Create CredentialManager for testing."""
        return CredentialManager("integration_test_password")

    def test_multiple_encrypt_decrypt_cycles(self, manager):
        """Multiple encrypt/decrypt cycles should work correctly."""
        credentials = {"key": "value"}
        for i in range(5):
            encrypted = manager.encrypt_credentials(credentials)
            decrypted = manager.decrypt_credentials(encrypted)
            assert decrypted == credentials

    def test_large_credentials(self, manager):
        """encrypt/decrypt should handle large credential objects."""
        large_creds = {f"key_{i}": f"value_{i}" * 100 for i in range(100)}
        encrypted = manager.encrypt_credentials(large_creds)
        decrypted = manager.decrypt_credentials(encrypted)
        assert decrypted == large_creds

    def test_ssh_private_key(self, manager):
        """encrypt/decrypt should handle SSH private key format."""
        ssh_key = {
            "private_key": """-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA0Z3VS5JJcds3xfn/ygWyf8Gfj1kx9+nBYfL/C5wZoWcGZcM
-----END RSA PRIVATE KEY-----"""
        }
        encrypted = manager.encrypt_credentials(ssh_key)
        decrypted = manager.decrypt_credentials(encrypted)
        assert decrypted == ssh_key

    def test_credentials_with_numbers(self, manager):
        """encrypt/decrypt should handle numeric values."""
        creds = {"port": 22, "timeout": 30.5, "count": 0}
        encrypted = manager.encrypt_credentials(creds)
        decrypted = manager.decrypt_credentials(encrypted)
        assert decrypted == creds

    def test_credentials_with_booleans(self, manager):
        """encrypt/decrypt should handle boolean values."""
        creds = {"enabled": True, "disabled": False}
        encrypted = manager.encrypt_credentials(creds)
        decrypted = manager.decrypt_credentials(encrypted)
        assert decrypted == creds

    def test_credentials_with_null(self, manager):
        """encrypt/decrypt should handle null values."""
        creds = {"value": None, "empty": ""}
        encrypted = manager.encrypt_credentials(creds)
        decrypted = manager.decrypt_credentials(encrypted)
        assert decrypted == creds

    def test_credentials_with_list(self, manager):
        """encrypt/decrypt should handle list values."""
        creds = {"hosts": ["host1", "host2", "host3"], "ports": [22, 80, 443]}
        encrypted = manager.encrypt_credentials(creds)
        decrypted = manager.decrypt_credentials(encrypted)
        assert decrypted == creds
