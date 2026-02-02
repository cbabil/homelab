"""
Pytest configuration and shared fixtures.

Provides common test fixtures and configuration for all test modules.
Follows 100-line limit with focused scope.
"""

import os
import pytest
import asyncio
from unittest.mock import MagicMock
from typing import Dict, Any

from lib.encryption import CredentialManager


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_config() -> Dict[str, Any]:
    """Mock configuration data."""
    return {
        "version": "0.1.0",
        "ssh_timeout": 30,
        "max_concurrent_connections": 10,
        "encryption_enabled": True
    }


@pytest.fixture
def mock_credential_manager():
    """Mock CredentialManager for testing."""
    manager = MagicMock(spec=CredentialManager)
    manager.encrypt_credentials.return_value = "encrypted_data"
    manager.decrypt_credentials.return_value = {
        "username": "testuser",
        "password": "testpass"
    }
    return manager


@pytest.fixture
def sample_credentials():
    """Sample credential data for tests."""
    return {
        "username": "testuser",
        "password": "testpass",
        "private_key": "-----BEGIN RSA PRIVATE KEY-----\ntest_key\n-----END RSA PRIVATE KEY-----"
    }


@pytest.fixture(autouse=True)
def setup_test_env():
    """Set up test environment variables."""
    os.environ["TOMO_MASTER_PASSWORD"] = "test_password"
    os.environ["TOMO_SALT"] = "test_salt"
    os.environ["JWT_SECRET_KEY"] = "test_jwt_secret_key_for_testing_only_not_for_production_use"
    yield
    # Cleanup not needed as each test gets fresh environment
