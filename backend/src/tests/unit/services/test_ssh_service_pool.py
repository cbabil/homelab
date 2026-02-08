"""
Unit tests for SSHConnectionPool in services/ssh_service.py

Tests the connection pooling functionality for SSH connections.
"""

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from services.ssh_service import SSHConnectionPool


@pytest.fixture
def mock_ssh_client():
    """Create a mock SSH client."""
    client = MagicMock()
    transport = MagicMock()
    transport.is_active.return_value = True
    client.get_transport.return_value = transport
    return client


@pytest.fixture
def mock_dead_client():
    """Create a mock SSH client with dead transport."""
    client = MagicMock()
    transport = MagicMock()
    transport.is_active.return_value = False
    client.get_transport.return_value = transport
    return client


@pytest.fixture
def mock_no_transport_client():
    """Create a mock SSH client with no transport."""
    client = MagicMock()
    client.get_transport.return_value = None
    return client


@pytest.fixture
def connection_pool():
    """Create an SSHConnectionPool instance."""
    with patch("services.ssh_service.logger"):
        return SSHConnectionPool()


class TestMakeKey:
    """Tests for _make_key method."""

    def test_make_key_creates_unique_string(self, connection_pool):
        """_make_key should create unique identifier from host/port/username."""
        key = connection_pool._make_key("192.168.1.1", 22, "admin")
        assert key == "192.168.1.1:22:admin"

    def test_make_key_with_different_ports(self, connection_pool):
        """_make_key should differentiate by port."""
        key1 = connection_pool._make_key("host", 22, "user")
        key2 = connection_pool._make_key("host", 2222, "user")
        assert key1 != key2

    def test_make_key_with_different_users(self, connection_pool):
        """_make_key should differentiate by username."""
        key1 = connection_pool._make_key("host", 22, "user1")
        key2 = connection_pool._make_key("host", 22, "user2")
        assert key1 != key2


class TestGet:
    """Tests for get method."""

    @pytest.mark.asyncio
    async def test_get_returns_none_when_empty(self, connection_pool):
        """get should return None when pool is empty."""
        with patch("services.ssh_service.logger"):
            result = await connection_pool.get("nonexistent:22:user")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_returns_active_connection(
        self, connection_pool, mock_ssh_client
    ):
        """get should return active connection from pool."""
        key = "host:22:user"
        with patch("services.ssh_service.logger"):
            await connection_pool.put(key, mock_ssh_client)
            result = await connection_pool.get(key)

        assert result is mock_ssh_client

    @pytest.mark.asyncio
    async def test_get_marks_connection_in_use(self, connection_pool, mock_ssh_client):
        """get should mark connection as in use."""
        key = "host:22:user"
        with patch("services.ssh_service.logger"):
            await connection_pool.put(key, mock_ssh_client)
            await connection_pool.get(key)

        assert connection_pool._in_use[key] is True

    @pytest.mark.asyncio
    async def test_get_returns_none_when_in_use(self, connection_pool, mock_ssh_client):
        """get should return None when connection is already in use."""
        key = "host:22:user"
        with patch("services.ssh_service.logger"):
            await connection_pool.put(key, mock_ssh_client)
            await connection_pool.get(key)  # First get marks as in use
            result = await connection_pool.get(key)  # Second get should return None

        assert result is None

    @pytest.mark.asyncio
    async def test_get_removes_dead_connection(self, connection_pool, mock_dead_client):
        """get should remove dead connections from pool."""
        key = "host:22:user"
        with patch("services.ssh_service.logger"):
            connection_pool._connections[key] = mock_dead_client
            connection_pool._in_use[key] = False
            result = await connection_pool.get(key)

        assert result is None
        assert key not in connection_pool._connections
        mock_dead_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_removes_no_transport_connection(
        self, connection_pool, mock_no_transport_client
    ):
        """get should remove connections with no transport."""
        key = "host:22:user"
        with patch("services.ssh_service.logger"):
            connection_pool._connections[key] = mock_no_transport_client
            connection_pool._in_use[key] = False
            result = await connection_pool.get(key)

        assert result is None
        assert key not in connection_pool._connections

    @pytest.mark.asyncio
    async def test_get_handles_close_exception(self, connection_pool, mock_dead_client):
        """get should handle exceptions when closing dead connection."""
        key = "host:22:user"
        mock_dead_client.close.side_effect = Exception("Close failed")

        with patch("services.ssh_service.logger"):
            connection_pool._connections[key] = mock_dead_client
            connection_pool._in_use[key] = False
            result = await connection_pool.get(key)

        assert result is None
        assert key not in connection_pool._connections


class TestPut:
    """Tests for put method."""

    @pytest.mark.asyncio
    async def test_put_adds_connection(self, connection_pool, mock_ssh_client):
        """put should add connection to pool."""
        key = "host:22:user"
        with patch("services.ssh_service.logger"):
            await connection_pool.put(key, mock_ssh_client)

        assert connection_pool._connections[key] is mock_ssh_client

    @pytest.mark.asyncio
    async def test_put_marks_not_in_use(self, connection_pool, mock_ssh_client):
        """put should mark connection as not in use."""
        key = "host:22:user"
        with patch("services.ssh_service.logger"):
            await connection_pool.put(key, mock_ssh_client)

        assert connection_pool._in_use[key] is False

    @pytest.mark.asyncio
    async def test_put_logs_addition(self, connection_pool, mock_ssh_client):
        """put should log connection addition."""
        key = "host:22:user"
        with patch("services.ssh_service.logger") as mock_logger:
            await connection_pool.put(key, mock_ssh_client)
            mock_logger.debug.assert_called_with("Connection added to pool", key=key)


class TestRelease:
    """Tests for release method."""

    @pytest.mark.asyncio
    async def test_release_marks_not_in_use(self, connection_pool, mock_ssh_client):
        """release should mark connection as not in use."""
        key = "host:22:user"
        with patch("services.ssh_service.logger"):
            await connection_pool.put(key, mock_ssh_client)
            await connection_pool.get(key)  # Mark as in use
            await connection_pool.release(key)

        assert connection_pool._in_use[key] is False

    @pytest.mark.asyncio
    async def test_release_nonexistent_key(self, connection_pool):
        """release should handle nonexistent key gracefully."""
        with patch("services.ssh_service.logger"):
            # Should not raise
            await connection_pool.release("nonexistent:22:user")

    @pytest.mark.asyncio
    async def test_release_logs_release(self, connection_pool, mock_ssh_client):
        """release should log connection release."""
        key = "host:22:user"
        with patch("services.ssh_service.logger") as mock_logger:
            await connection_pool.put(key, mock_ssh_client)
            await connection_pool.get(key)
            await connection_pool.release(key)

            mock_logger.debug.assert_called_with("Connection released to pool", key=key)


class TestClose:
    """Tests for close method."""

    @pytest.mark.asyncio
    async def test_close_removes_connection(self, connection_pool, mock_ssh_client):
        """close should remove connection from pool."""
        key = "host:22:user"
        with patch("services.ssh_service.logger"):
            await connection_pool.put(key, mock_ssh_client)
            await connection_pool.close(key)

        assert key not in connection_pool._connections
        assert key not in connection_pool._in_use

    @pytest.mark.asyncio
    async def test_close_calls_client_close(self, connection_pool, mock_ssh_client):
        """close should close the SSH client."""
        key = "host:22:user"
        with patch("services.ssh_service.logger"):
            await connection_pool.put(key, mock_ssh_client)
            await connection_pool.close(key)

        mock_ssh_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_handles_exception(self, connection_pool, mock_ssh_client):
        """close should handle close exceptions."""
        key = "host:22:user"
        mock_ssh_client.close.side_effect = Exception("Close failed")

        with patch("services.ssh_service.logger"):
            await connection_pool.put(key, mock_ssh_client)
            await connection_pool.close(key)

        assert key not in connection_pool._connections

    @pytest.mark.asyncio
    async def test_close_nonexistent_key(self, connection_pool):
        """close should handle nonexistent key gracefully."""
        with patch("services.ssh_service.logger"):
            # Should not raise
            await connection_pool.close("nonexistent:22:user")


class TestCloseAll:
    """Tests for close_all method."""

    @pytest.mark.asyncio
    async def test_close_all_empties_pool(self, connection_pool, mock_ssh_client):
        """close_all should remove all connections from pool."""
        with patch("services.ssh_service.logger"):
            await connection_pool.put("host1:22:user", mock_ssh_client)
            await connection_pool.put("host2:22:user", MagicMock())
            await connection_pool.close_all()

        assert len(connection_pool._connections) == 0
        assert len(connection_pool._in_use) == 0

    @pytest.mark.asyncio
    async def test_close_all_closes_each_client(self, connection_pool):
        """close_all should close each SSH client."""
        client1 = MagicMock()
        client2 = MagicMock()

        with patch("services.ssh_service.logger"):
            await connection_pool.put("host1:22:user", client1)
            await connection_pool.put("host2:22:user", client2)
            await connection_pool.close_all()

        client1.close.assert_called_once()
        client2.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_all_handles_exceptions(self, connection_pool):
        """close_all should handle close exceptions."""
        client1 = MagicMock()
        client1.close.side_effect = Exception("Close failed")
        client2 = MagicMock()

        with patch("services.ssh_service.logger"):
            await connection_pool.put("host1:22:user", client1)
            await connection_pool.put("host2:22:user", client2)
            await connection_pool.close_all()

        assert len(connection_pool._connections) == 0
        client2.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_all_logs_completion(self, connection_pool):
        """close_all should log completion."""
        with patch("services.ssh_service.logger") as mock_logger:
            await connection_pool.close_all()
            mock_logger.info.assert_called_with("All pooled connections closed")


class TestConcurrency:
    """Tests for concurrent access to pool."""

    @pytest.mark.asyncio
    async def test_concurrent_get_and_release(self, connection_pool, mock_ssh_client):
        """Pool should handle concurrent get and release operations."""
        key = "host:22:user"

        with patch("services.ssh_service.logger"):
            await connection_pool.put(key, mock_ssh_client)

            async def get_and_release():
                client = await connection_pool.get(key)
                if client:
                    await asyncio.sleep(0.01)
                    await connection_pool.release(key)
                return client is not None

            # Run multiple concurrent operations
            results = await asyncio.gather(
                get_and_release(),
                get_and_release(),
                get_and_release(),
            )

            # Only one should succeed (connection is singular)
            assert sum(results) == 1
