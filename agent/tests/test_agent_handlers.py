"""Tests for agent-specific RPC handlers.

Tests config.update, metrics.get, and agent.rotate_token handlers.
"""

from unittest.mock import MagicMock, patch

from rpc.agent_handlers import (
    create_config_update_handler,
    create_metrics_handler,
    create_rotate_token_handler,
    setup_agent_handlers,
)
from rpc.handler import RPCHandler
from config import AgentConfig, AgentState


class TestCreateConfigUpdateHandler:
    """Tests for create_config_update_handler."""

    def test_returns_callable(self):
        """Should return a callable handler."""

        def get_config():
            return AgentConfig()

        def set_config(c):
            return None

        handler = create_config_update_handler(get_config, set_config)

        assert callable(handler)

    def test_updates_config(self):
        """Should update config with provided values."""
        current_config = AgentConfig(metrics_interval=30)
        updated_config = None

        def set_config(c):
            nonlocal updated_config
            updated_config = c

        handler = create_config_update_handler(
            get_config=lambda: current_config,
            set_config=set_config,
        )

        result = handler(metrics_interval=60)

        assert result == {"status": "ok"}
        assert updated_config is not None
        assert updated_config.metrics_interval == 60

    def test_returns_ok_status(self):
        """Should return ok status."""
        handler = create_config_update_handler(
            get_config=lambda: AgentConfig(),
            set_config=lambda c: None,
        )

        result = handler(health_interval=45)

        assert result["status"] == "ok"

    def test_handles_empty_update(self):
        """Should handle empty update kwargs."""
        handler = create_config_update_handler(
            get_config=lambda: AgentConfig(),
            set_config=lambda c: None,
        )

        result = handler()

        assert result["status"] == "ok"


class TestCreateMetricsHandler:
    """Tests for create_metrics_handler."""

    def test_returns_callable(self):
        """Should return a callable handler."""

        def get_agent_id():
            return "test-id"

        handler = create_metrics_handler(get_agent_id)

        assert callable(handler)

    def test_returns_agent_id(self):
        """Should include agent ID in response."""
        handler = create_metrics_handler(get_agent_id=lambda: "agent-123")

        result = handler()

        assert result["agent_id"] == "agent-123"

    def test_returns_version(self):
        """Should include version in response."""
        handler = create_metrics_handler(get_agent_id=lambda: "id")

        result = handler()

        assert "version" in result
        assert isinstance(result["version"], str)

    def test_returns_connected_status(self):
        """Should return connected status."""
        handler = create_metrics_handler(get_agent_id=lambda: "id")

        result = handler()

        assert result["status"] == "connected"

    def test_handles_none_agent_id(self):
        """Should handle None agent ID."""
        handler = create_metrics_handler(get_agent_id=lambda: None)

        result = handler()

        assert result["agent_id"] is None


class TestSetupAgentHandlers:
    """Tests for setup_agent_handlers."""

    def test_registers_config_update(self):
        """Should register config.update handler."""
        rpc_handler = MagicMock()

        def get_config():
            return AgentConfig()

        def set_config(c):
            return None

        def get_agent_id():
            return "id"

        setup_agent_handlers(
            rpc_handler=rpc_handler,
            get_config=get_config,
            set_config=set_config,
            get_agent_id=get_agent_id,
        )

        # Check config.update was registered
        calls = rpc_handler.register.call_args_list
        config_update_call = [c for c in calls if c[0][0] == "config.update"]
        assert len(config_update_call) == 1

    def test_registers_metrics_get(self):
        """Should register metrics.get handler."""
        rpc_handler = MagicMock()

        def get_config():
            return AgentConfig()

        def set_config(c):
            return None

        def get_agent_id():
            return "id"

        setup_agent_handlers(
            rpc_handler=rpc_handler,
            get_config=get_config,
            set_config=set_config,
            get_agent_id=get_agent_id,
        )

        calls = rpc_handler.register.call_args_list
        metrics_get_call = [c for c in calls if c[0][0] == "metrics.get"]
        assert len(metrics_get_call) == 1

    def test_registers_all_handlers(self):
        """Should register all three handlers."""
        rpc_handler = MagicMock()

        def get_config():
            return AgentConfig()

        def set_config(c):
            return None

        def get_agent_id():
            return "id"

        setup_agent_handlers(
            rpc_handler=rpc_handler,
            get_config=get_config,
            set_config=set_config,
            get_agent_id=get_agent_id,
        )

        assert rpc_handler.register.call_count == 3

    def test_registers_rotate_token(self):
        """Should register agent.rotate_token handler."""
        rpc_handler = MagicMock()

        setup_agent_handlers(
            rpc_handler=rpc_handler,
            get_config=lambda: AgentConfig(),
            set_config=lambda c: None,
            get_agent_id=lambda: "id",
        )

        calls = rpc_handler.register.call_args_list
        rotate_call = [c for c in calls if c[0][0] == "agent.rotate_token"]
        assert len(rotate_call) == 1

    def test_registered_config_handler_works(self):
        """Should register a working config handler."""
        rpc_handler = RPCHandler()
        config_updated = None

        def set_config(c):
            nonlocal config_updated
            config_updated = c

        setup_agent_handlers(
            rpc_handler=rpc_handler,
            get_config=lambda: AgentConfig(),
            set_config=set_config,
            get_agent_id=lambda: "id",
        )

        # Call the registered handler
        handler = rpc_handler._methods.get("config.update")
        assert handler is not None

        result = handler(health_interval=120)
        assert result["status"] == "ok"
        assert config_updated.health_interval == 120

    def test_registered_metrics_handler_works(self):
        """Should register a working metrics handler."""
        rpc_handler = RPCHandler()

        setup_agent_handlers(
            rpc_handler=rpc_handler,
            get_config=lambda: AgentConfig(),
            set_config=lambda c: None,
            get_agent_id=lambda: "test-agent",
        )

        handler = rpc_handler._methods.get("metrics.get")
        assert handler is not None

        result = handler()
        assert result["agent_id"] == "test-agent"
        assert result["status"] == "connected"


class TestCreateRotateTokenHandler:
    """Tests for create_rotate_token_handler."""

    def test_returns_callable(self):
        """Should return a callable handler."""
        handler = create_rotate_token_handler()
        assert callable(handler)

    @patch("rpc.agent_handlers.load_state")
    @patch("rpc.agent_handlers.save_state")
    def test_rotates_token_successfully(self, mock_save, mock_load):
        """Should save new token and return ok status."""
        mock_load.return_value = AgentState(
            agent_id="agent-123",
            token="old-token",
            server_url="http://localhost:8000",
            registered_at="2024-01-01T00:00:00Z",
        )

        handler = create_rotate_token_handler()
        result = handler(new_token="new-secret-token", grace_period_seconds=300)

        assert result["status"] == "ok"
        assert "rotated_at" in result
        mock_save.assert_called_once()

        # Verify new state has the new token
        saved_state = mock_save.call_args[0][0]
        assert saved_state.token == "new-secret-token"
        assert saved_state.agent_id == "agent-123"

    @patch("rpc.agent_handlers.load_state")
    def test_fails_when_no_existing_state(self, mock_load):
        """Should return error when no existing state found."""
        mock_load.return_value = None

        handler = create_rotate_token_handler()
        result = handler(new_token="new-token", grace_period_seconds=300)

        assert result["status"] == "error"
        assert "No existing state" in result["error"]

    @patch("rpc.agent_handlers.load_state")
    @patch("rpc.agent_handlers.save_state")
    def test_preserves_agent_id_and_server_url(self, mock_save, mock_load):
        """Should preserve agent_id and server_url when rotating."""
        mock_load.return_value = AgentState(
            agent_id="my-agent",
            token="old-token",
            server_url="https://server.example.com",
            registered_at="2024-01-15T12:00:00Z",
        )

        handler = create_rotate_token_handler()
        handler(new_token="rotated-token", grace_period_seconds=60)

        saved_state = mock_save.call_args[0][0]
        assert saved_state.agent_id == "my-agent"
        assert saved_state.server_url == "https://server.example.com"
        assert saved_state.registered_at == "2024-01-15T12:00:00Z"

    @patch("rpc.agent_handlers.load_state")
    @patch("rpc.agent_handlers.save_state")
    def test_handles_save_error(self, mock_save, mock_load):
        """Should return error when save fails."""
        mock_load.return_value = AgentState(
            agent_id="agent-123",
            token="old-token",
            server_url="http://localhost:8000",
            registered_at="2024-01-01T00:00:00Z",
        )
        mock_save.side_effect = IOError("Disk full")

        handler = create_rotate_token_handler()
        result = handler(new_token="new-token", grace_period_seconds=300)

        assert result["status"] == "error"
        assert "Disk full" in result["error"]

    @patch("rpc.agent_handlers.load_state")
    @patch("rpc.agent_handlers.save_state")
    def test_uses_default_grace_period(self, mock_save, mock_load):
        """Should accept default grace period parameter."""
        mock_load.return_value = AgentState(
            agent_id="agent-123",
            token="old-token",
            server_url="http://localhost:8000",
            registered_at="2024-01-01T00:00:00Z",
        )

        handler = create_rotate_token_handler()
        # Call without grace_period_seconds to use default
        result = handler(new_token="new-token")

        assert result["status"] == "ok"
