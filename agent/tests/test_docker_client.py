"""Tests for Docker client singleton.

Tests the shared Docker client management.
"""

from unittest.mock import MagicMock, patch

from rpc.methods.docker_client import get_client, reset_client


class TestGetClient:
    """Tests for get_client function."""

    def test_returns_docker_client(self):
        """Should return a Docker client."""
        mock_client = MagicMock()

        # Reset before test
        reset_client()

        with patch("docker.from_env", return_value=mock_client):
            result = get_client()

        assert result is mock_client
        reset_client()

    def test_creates_client_once(self):
        """Should create client only once (singleton)."""
        mock_client = MagicMock()

        reset_client()

        with patch("docker.from_env", return_value=mock_client) as mock_from_env:
            # Call twice
            client1 = get_client()
            client2 = get_client()

            # Should only call from_env once
            mock_from_env.assert_called_once()

        # Both should return the same client
        assert client1 is client2
        reset_client()

    def test_reuses_existing_client(self):
        """Should reuse existing client if already created."""
        existing_client = MagicMock()

        import rpc.methods.docker_client as dc

        reset_client()

        # Set existing client
        with dc._client_lock:
            dc._client = existing_client

        try:
            with patch("docker.from_env") as mock_from_env:
                result = get_client()

            # Should not call from_env since client already exists
            mock_from_env.assert_not_called()
            assert result is existing_client
        finally:
            reset_client()

    def test_thread_safe_initialization(self):
        """Should safely initialize client from multiple threads."""
        import threading

        mock_client = MagicMock()
        reset_client()

        results = []
        errors = []

        def get_client_thread():
            try:
                client = get_client()
                results.append(client)
            except Exception as e:
                errors.append(e)

        with patch("docker.from_env", return_value=mock_client) as mock_from_env:
            threads = [threading.Thread(target=get_client_thread) for _ in range(10)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

        # All threads should get the same client
        assert len(errors) == 0
        assert len(results) == 10
        assert all(r is mock_client for r in results)
        # from_env should only be called once despite concurrent access
        assert mock_from_env.call_count == 1
        reset_client()


class TestResetClient:
    """Tests for reset_client function."""

    def test_resets_client_to_none(self):
        """Should reset the client to None."""
        import rpc.methods.docker_client as dc

        mock_client = MagicMock()

        with dc._client_lock:
            dc._client = mock_client

        reset_client()

        assert dc._client is None
