"""
Pytest Configuration and Fixtures

Shared fixtures for all tests.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

# -------------------------------------------------------------------------
# Event Loop Fixture
# -------------------------------------------------------------------------


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# -------------------------------------------------------------------------
# Mock Service Fixtures
# -------------------------------------------------------------------------


@pytest.fixture
def mock_ssh_service():
    """Mock SSH service for testing."""
    service = MagicMock()
    service.execute_command = AsyncMock(return_value=(True, "success"))
    service.execute_command_with_progress = AsyncMock(return_value=(True, "success"))
    service.test_connection = AsyncMock(
        return_value=(True, "Connected", {"os": "Linux"})
    )
    return service


@pytest.fixture
def mock_db_service():
    """Mock database service for testing."""
    service = MagicMock()
    service.get_installation = AsyncMock(return_value=None)
    service.create_installation = AsyncMock()
    service.update_installation = AsyncMock()
    service.delete_installation = AsyncMock()
    service.get_all_installations = AsyncMock(return_value=[])
    return service


@pytest.fixture
def mock_server_service():
    """Mock server service for testing."""
    service = MagicMock()
    service.get_server = AsyncMock(
        return_value=MagicMock(
            id="server-1",
            name="Test Server",
            host="192.168.1.100",
            port=22,
            username="admin",
            auth_type=MagicMock(value="key"),
        )
    )
    service.get_credentials = AsyncMock(return_value={"private_key": "test-key"})
    return service


@pytest.fixture
def mock_marketplace_service():
    """Mock marketplace service for testing."""
    service = MagicMock()
    service.get_app = AsyncMock(
        return_value=MagicMock(
            id="app-1",
            name="Test App",
            docker=MagicMock(
                image="test/app:latest",
                ports=[],
                volumes=[],
                environment=[],
                restart_policy="unless-stopped",
                network_mode=None,
                privileged=False,
                capabilities=[],
            ),
        )
    )
    return service


@pytest.fixture
def mock_agent_manager():
    """Mock agent manager for testing."""
    manager = MagicMock()
    manager.is_connected = MagicMock(return_value=True)
    manager.get_connection = MagicMock(return_value=MagicMock())
    manager.send_command = AsyncMock(return_value={"success": True, "output": "ok"})
    return manager


@pytest.fixture
def mock_agent_service():
    """Mock agent service for testing."""
    service = MagicMock()
    service.get_agent_by_server = AsyncMock(
        return_value=MagicMock(id="agent-1", server_id="server-1", status="connected")
    )
    return service


# -------------------------------------------------------------------------
# Sample Data Fixtures
# -------------------------------------------------------------------------


@pytest.fixture
def sample_server_data():
    """Sample server data for testing."""
    return {
        "id": "srv-test123",
        "name": "Test Server",
        "host": "192.168.1.100",
        "port": 22,
        "username": "admin",
        "auth_type": "key",
    }


@pytest.fixture
def sample_app_data():
    """Sample app data for testing."""
    return {
        "id": "portainer",
        "name": "Portainer",
        "version": "2.19.4",
        "category": "Management",
        "description": "Docker management UI",
    }


@pytest.fixture
def sample_installation_data():
    """Sample installation data for testing."""
    return {
        "id": "inst-abc123",
        "server_id": "srv-test123",
        "app_id": "portainer",
        "container_name": "portainer-abc1",
        "container_id": "abc123def456",
        "status": "running",
        "config": {"ports": {"9000": 9000}},
    }
