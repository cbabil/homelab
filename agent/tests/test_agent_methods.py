"""Tests for agent RPC methods.

Tests agent.ping and agent.update methods.
"""

from unittest.mock import AsyncMock, MagicMock, patch


from rpc.methods.agent import AgentMethods, create_agent_methods


class TestAgentMethodsInit:
    """Tests for AgentMethods initialization."""

    def test_initializes_with_callbacks(self):
        """Should initialize with callback functions."""

        def get_id():
            return "agent-123"

        shutdown = AsyncMock()

        methods = AgentMethods(get_agent_id=get_id, shutdown=shutdown)

        assert methods._get_agent_id == get_id
        assert methods._shutdown == shutdown


class TestAgentMethodsPing:
    """Tests for AgentMethods.ping()."""

    def test_returns_status_ok(self):
        """Should return ok status."""
        methods = AgentMethods(get_agent_id=lambda: "id-1", shutdown=AsyncMock())

        result = methods.ping()

        assert result["status"] == "ok"

    def test_includes_version(self):
        """Should include agent version."""
        methods = AgentMethods(get_agent_id=lambda: "id-1", shutdown=AsyncMock())

        result = methods.ping()

        assert "version" in result
        assert isinstance(result["version"], str)

    def test_includes_agent_id(self):
        """Should include agent ID from callback."""
        methods = AgentMethods(get_agent_id=lambda: "agent-abc", shutdown=AsyncMock())

        result = methods.ping()

        assert result["agent_id"] == "agent-abc"

    def test_handles_none_agent_id(self):
        """Should handle None agent ID."""
        methods = AgentMethods(get_agent_id=lambda: None, shutdown=AsyncMock())

        result = methods.ping()

        assert result["agent_id"] is None


class TestAgentMethodsUpdate:
    """Tests for AgentMethods.update()."""

    def test_returns_updating_status_on_success(self):
        """Should return updating status on success."""
        mock_client = MagicMock()
        mock_client.images.pull.return_value = MagicMock()

        methods = AgentMethods(get_agent_id=lambda: "id-1", shutdown=AsyncMock())

        with patch("rpc.methods.docker_client.get_client", return_value=mock_client):
            with patch("asyncio.get_running_loop") as mock_loop:
                mock_loop.return_value = MagicMock()
                result = methods.update(version="2.0.0")

        assert result["status"] == "updating"
        assert result["version"] == "2.0.0"

    def test_pulls_correct_image(self):
        """Should pull the correct agent image."""
        mock_client = MagicMock()

        methods = AgentMethods(get_agent_id=lambda: "id-1", shutdown=AsyncMock())

        with patch("rpc.methods.docker_client.get_client", return_value=mock_client):
            with patch("asyncio.get_running_loop") as mock_loop:
                mock_loop.return_value = MagicMock()
                methods.update(version="1.5.0")

        mock_client.images.pull.assert_called_once_with(
            "ghcr.io/tomo/agent",
            tag="1.5.0",
        )

    def test_schedules_shutdown(self):
        """Should schedule shutdown after pull."""
        mock_client = MagicMock()
        mock_loop = MagicMock()

        methods = AgentMethods(get_agent_id=lambda: "id-1", shutdown=AsyncMock())

        with patch("rpc.methods.docker_client.get_client", return_value=mock_client):
            with patch("asyncio.get_running_loop", return_value=mock_loop):
                methods.update(version="2.0.0")

        mock_loop.call_later.assert_called_once()
        # First arg is delay (1.0)
        assert mock_loop.call_later.call_args[0][0] == 1.0

    def test_returns_error_on_pull_failure(self):
        """Should return error status on pull failure."""
        mock_client = MagicMock()
        mock_client.images.pull.side_effect = Exception("Image not found")

        methods = AgentMethods(get_agent_id=lambda: "id-1", shutdown=AsyncMock())

        with patch("rpc.methods.docker_client.get_client", return_value=mock_client):
            result = methods.update(version="invalid")

        assert result["status"] == "error"
        assert "Image not found" in result["message"]

    def test_logs_update_start(self):
        """Should log update initiation."""
        mock_client = MagicMock()

        methods = AgentMethods(get_agent_id=lambda: "id-1", shutdown=AsyncMock())

        with patch("rpc.methods.docker_client.get_client", return_value=mock_client):
            with patch("asyncio.get_running_loop") as mock_loop:
                mock_loop.return_value = MagicMock()
                with patch("rpc.methods.agent.logger") as mock_logger:
                    methods.update(version="2.0.0")

                    # Should log at least the update start
                    assert mock_logger.info.called


class TestCreateAgentMethods:
    """Tests for create_agent_methods factory."""

    def test_creates_agent_methods_instance(self):
        """Should create AgentMethods instance."""

        def get_id():
            return "test-id"

        shutdown = AsyncMock()

        result = create_agent_methods(get_agent_id=get_id, shutdown=shutdown)

        assert isinstance(result, AgentMethods)

    def test_passes_callbacks(self):
        """Should pass callbacks to instance."""

        def get_id():
            return "factory-test"

        shutdown = AsyncMock()

        result = create_agent_methods(get_agent_id=get_id, shutdown=shutdown)

        assert result._get_agent_id() == "factory-test"
        assert result._shutdown == shutdown
