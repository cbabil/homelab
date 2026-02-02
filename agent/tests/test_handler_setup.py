"""Tests for handler setup module.

Tests RPC handler registration and setup.
"""

from unittest.mock import AsyncMock, MagicMock, patch

from handler_setup import setup_all_handlers
from rpc.handler import RPCHandler
from config import AgentConfig


class TestSetupAllHandlers:
    """Tests for setup_all_handlers function."""

    def test_registers_agent_handlers(self):
        """Should register agent-specific handlers."""
        rpc_handler = RPCHandler()

        def get_config():
            return AgentConfig()

        def set_config(c):
            return None

        def get_agent_id():
            return "test-id"

        shutdown = AsyncMock()

        with patch("handler_setup.setup_agent_handlers") as mock_setup:
            setup_all_handlers(
                rpc_handler=rpc_handler,
                get_config=get_config,
                set_config=set_config,
                get_agent_id=get_agent_id,
                shutdown=shutdown,
            )

            mock_setup.assert_called_once_with(
                rpc_handler,
                get_config=get_config,
                set_config=set_config,
                get_agent_id=get_agent_id,
            )

    def test_registers_container_methods(self):
        """Should register Docker container methods."""
        rpc_handler = MagicMock()

        def get_config():
            return AgentConfig()

        def set_config(c):
            return None

        def get_agent_id():
            return "test-id"

        shutdown = AsyncMock()

        with patch("handler_setup.setup_agent_handlers"):
            with patch("handler_setup.ContainerMethods"):
                setup_all_handlers(
                    rpc_handler=rpc_handler,
                    get_config=get_config,
                    set_config=set_config,
                    get_agent_id=get_agent_id,
                    shutdown=shutdown,
                )

                # Check container methods were registered
                calls = rpc_handler.register_module.call_args_list
                container_call = [c for c in calls if c[0][0] == "docker.containers"]
                assert len(container_call) == 1

    def test_registers_image_methods(self):
        """Should register Docker image methods."""
        rpc_handler = MagicMock()

        def get_config():
            return AgentConfig()

        def set_config(c):
            return None

        def get_agent_id():
            return "test-id"

        shutdown = AsyncMock()

        with patch("handler_setup.setup_agent_handlers"):
            with patch("handler_setup.ImageMethods"):
                setup_all_handlers(
                    rpc_handler=rpc_handler,
                    get_config=get_config,
                    set_config=set_config,
                    get_agent_id=get_agent_id,
                    shutdown=shutdown,
                )

                calls = rpc_handler.register_module.call_args_list
                image_call = [c for c in calls if c[0][0] == "docker.images"]
                assert len(image_call) == 1

    def test_registers_volume_methods(self):
        """Should register Docker volume methods."""
        rpc_handler = MagicMock()

        def get_config():
            return AgentConfig()

        def set_config(c):
            return None

        def get_agent_id():
            return "test-id"

        shutdown = AsyncMock()

        with patch("handler_setup.setup_agent_handlers"):
            with patch("handler_setup.VolumeMethods"):
                setup_all_handlers(
                    rpc_handler=rpc_handler,
                    get_config=get_config,
                    set_config=set_config,
                    get_agent_id=get_agent_id,
                    shutdown=shutdown,
                )

                calls = rpc_handler.register_module.call_args_list
                volume_call = [c for c in calls if c[0][0] == "docker.volumes"]
                assert len(volume_call) == 1

    def test_registers_network_methods(self):
        """Should register Docker network methods."""
        rpc_handler = MagicMock()

        def get_config():
            return AgentConfig()

        def set_config(c):
            return None

        def get_agent_id():
            return "test-id"

        shutdown = AsyncMock()

        with patch("handler_setup.setup_agent_handlers"):
            with patch("handler_setup.NetworkMethods"):
                setup_all_handlers(
                    rpc_handler=rpc_handler,
                    get_config=get_config,
                    set_config=set_config,
                    get_agent_id=get_agent_id,
                    shutdown=shutdown,
                )

                calls = rpc_handler.register_module.call_args_list
                network_call = [c for c in calls if c[0][0] == "docker.networks"]
                assert len(network_call) == 1

    def test_registers_system_methods(self):
        """Should register system methods."""
        rpc_handler = MagicMock()

        def get_config():
            return AgentConfig()

        def set_config(c):
            return None

        def get_agent_id():
            return "test-id"

        shutdown = AsyncMock()

        with patch("handler_setup.setup_agent_handlers"):
            with patch("handler_setup.SystemMethods"):
                setup_all_handlers(
                    rpc_handler=rpc_handler,
                    get_config=get_config,
                    set_config=set_config,
                    get_agent_id=get_agent_id,
                    shutdown=shutdown,
                )

                calls = rpc_handler.register_module.call_args_list
                system_call = [c for c in calls if c[0][0] == "system"]
                assert len(system_call) == 1

    def test_registers_agent_methods(self):
        """Should register agent methods."""
        rpc_handler = MagicMock()

        def get_config():
            return AgentConfig()

        def set_config(c):
            return None

        def get_agent_id():
            return "test-id"

        shutdown = AsyncMock()

        with patch("handler_setup.setup_agent_handlers"):
            with patch("handler_setup.create_agent_methods") as mock_create:
                mock_create.return_value = MagicMock()
                setup_all_handlers(
                    rpc_handler=rpc_handler,
                    get_config=get_config,
                    set_config=set_config,
                    get_agent_id=get_agent_id,
                    shutdown=shutdown,
                )

                mock_create.assert_called_once_with(
                    get_agent_id=get_agent_id,
                    shutdown=shutdown,
                )

                calls = rpc_handler.register_module.call_args_list
                agent_call = [c for c in calls if c[0][0] == "agent"]
                assert len(agent_call) == 1

    def test_registers_all_modules(self):
        """Should register all expected modules."""
        rpc_handler = MagicMock()

        def get_config():
            return AgentConfig()

        def set_config(c):
            return None

        def get_agent_id():
            return "test-id"

        shutdown = AsyncMock()

        with patch("handler_setup.setup_agent_handlers"):
            setup_all_handlers(
                rpc_handler=rpc_handler,
                get_config=get_config,
                set_config=set_config,
                get_agent_id=get_agent_id,
                shutdown=shutdown,
            )

        # Should have registered 6 modules
        # docker.containers, docker.images, docker.volumes, docker.networks, system, agent
        assert rpc_handler.register_module.call_count == 6
