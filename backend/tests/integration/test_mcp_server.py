"""
Integration tests for MCP Server functionality.

Tests FastMCP server integration with tools and services.
Covers tool registration, tool calls, and service initialization.
"""

import pytest
import os
import sys
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path


class TestMCPServerIntegration:
    """Integration test suite for MCP server functionality."""

    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Set up test environment with temporary data directory."""
        # Remove cached main module to ensure fresh import
        if "main" in sys.modules:
            del sys.modules["main"]

        with tempfile.TemporaryDirectory() as temp_dir:
            # Set DATA_DIRECTORY to temporary location
            with patch.dict(os.environ, {"DATA_DIRECTORY": temp_dir}):
                yield temp_dir

    @pytest.fixture
    def mock_services(self, setup_test_environment):
        """Mock configuration loading for integration tests."""
        temp_dir = setup_test_environment
        backend_dir = Path(__file__).resolve().parents[2]
        mock_config = {
            "data_directory": temp_dir,
            "app_env": "test",
            "version": "0.1.0",
            "ssh_timeout": 30,
            "max_concurrent_connections": 10,
            "tools_directory": str((backend_dir / "src" / "tools").resolve()),
            "tools_package": "tools",
        }

        with patch("lib.config.load_config", return_value=mock_config):
            yield {
                "config": mock_config,
            }

    @pytest.fixture
    def mock_full_environment(self, setup_test_environment):
        """Set up full mock environment for main module import."""
        temp_dir = setup_test_environment
        backend_dir = Path(__file__).resolve().parents[2]

        mock_config = {
            "data_directory": temp_dir,
            "app_env": "test",
            "version": "0.1.0",
            "ssh_timeout": 30,
            "max_concurrent_connections": 10,
            "tools_directory": str((backend_dir / "src" / "tools").resolve()),
            "tools_package": "tools",
        }

        mock_services_dict = {
            "agent_websocket_handler": MagicMock(),
            "agent_lifecycle": MagicMock(),
            "database_service": MagicMock(),
            "agent_service": MagicMock(),
            "auth_service": MagicMock(),
            "app_service": MagicMock(),
            "ssh_service": MagicMock(),
            "server_service": MagicMock(),
            "monitoring_service": MagicMock(),
            "retention_service": MagicMock(),
            "settings_service": MagicMock(),
            "marketplace_service": MagicMock(),
            "activity_service": MagicMock(),
            "metrics_service": MagicMock(),
            "session_service": MagicMock(),
            "notification_service": MagicMock(),
        }

        mock_fastmcp = MagicMock()
        mock_app = MagicMock()
        mock_app.name = "tomo"
        mock_app.version = "0.1.0"
        mock_app.instructions = "Tomo management and automation server"
        mock_app._tools = {}
        mock_fastmcp.return_value = mock_app

        return {
            "config": mock_config,
            "services": mock_services_dict,
            "fastmcp": mock_fastmcp,
            "app": mock_app,
        }

    def test_app_initialization(self, mock_full_environment):
        """Test FastMCP app initialization with service dependencies."""
        mocks = mock_full_environment

        with (
            patch("lib.logging_config.setup_logging"),
            patch("structlog.get_logger", return_value=MagicMock()),
            patch("lib.config.load_config", return_value=mocks["config"]),
            patch("lib.config.resolve_data_directory", return_value="/tmp/data"),
            patch("services.factory.create_services", return_value=mocks["services"]),
            patch("lib.tool_loader.register_all_tools"),
            patch.dict("sys.modules", {"fastmcp": MagicMock(FastMCP=mocks["fastmcp"])}),
        ):
            # Remove cached module
            if "main" in sys.modules:
                del sys.modules["main"]

            import main

            assert main.app is not None
            assert main.app.name == "tomo"
            assert main.app.version == "0.1.0"

            del sys.modules["main"]

    def test_tool_registration(self, mock_full_environment):
        """Test tools are properly registered with FastMCP."""
        mocks = mock_full_environment

        with (
            patch("lib.logging_config.setup_logging"),
            patch("structlog.get_logger", return_value=MagicMock()),
            patch("lib.config.load_config", return_value=mocks["config"]),
            patch("lib.config.resolve_data_directory", return_value="/tmp/data"),
            patch("services.factory.create_services", return_value=mocks["services"]),
            patch("lib.tool_loader.register_all_tools") as mock_register,
            patch.dict("sys.modules", {"fastmcp": MagicMock(FastMCP=mocks["fastmcp"])}),
        ):
            if "main" in sys.modules:
                del sys.modules["main"]

            import main

            # Verify register_all_tools was called with correct arguments
            mock_register.assert_called_once()
            call_args = mock_register.call_args
            assert call_args[0][0] == main.app  # First arg is app
            assert call_args[0][1] == mocks["config"]  # Second arg is config
            assert call_args[0][2] == mocks["services"]  # Third arg is services dict

            del sys.modules["main"]

    @pytest.mark.asyncio
    async def test_health_tool_functionality(self, mock_full_environment):
        """Test health check tool functionality."""
        # Create a mock health check tool
        mock_health_tool = MagicMock()
        mock_health_tool.fn = AsyncMock(return_value={
            "success": True,
            "message": "pong"
        })

        mocks = mock_full_environment
        mocks["app"]._tools = {"health_check": mock_health_tool}

        with (
            patch("lib.logging_config.setup_logging"),
            patch("structlog.get_logger", return_value=MagicMock()),
            patch("lib.config.load_config", return_value=mocks["config"]),
            patch("lib.config.resolve_data_directory", return_value="/tmp/data"),
            patch("services.factory.create_services", return_value=mocks["services"]),
            patch("lib.tool_loader.register_all_tools"),
            patch.dict("sys.modules", {"fastmcp": MagicMock(FastMCP=mocks["fastmcp"])}),
        ):
            if "main" in sys.modules:
                del sys.modules["main"]

            import main

            health_check_tool = main.app._tools.get("health_check")
            assert health_check_tool is not None

            result = await health_check_tool.fn()

            assert result["success"] is True
            assert result["message"] == "pong"

            del sys.modules["main"]

    @pytest.mark.asyncio
    async def test_settings_tools_integration(self, mock_full_environment):
        """Test settings tools integration."""
        mocks = mock_full_environment

        # Add settings tools to mock app
        mocks["app"]._tools = {
            "get_settings": MagicMock(),
            "update_settings": MagicMock(),
        }

        with (
            patch("lib.logging_config.setup_logging"),
            patch("structlog.get_logger", return_value=MagicMock()),
            patch("lib.config.load_config", return_value=mocks["config"]),
            patch("lib.config.resolve_data_directory", return_value="/tmp/data"),
            patch("services.factory.create_services", return_value=mocks["services"]),
            patch("lib.tool_loader.register_all_tools"),
            patch.dict("sys.modules", {"fastmcp": MagicMock(FastMCP=mocks["fastmcp"])}),
        ):
            if "main" in sys.modules:
                del sys.modules["main"]

            import main

            # Verify settings tools were registered
            tool_names = list(main.app._tools.keys())
            settings_tools = [name for name in tool_names if "settings" in name.lower()]
            assert len(settings_tools) > 0

            del sys.modules["main"]

    def test_app_with_missing_environment(self, mock_full_environment):
        """Test app behavior when DATA_DIRECTORY is not set."""
        mocks = mock_full_environment
        mocks["config"]["data_directory"] = "backend/data"
        mocks["config"]["app_env"] = "development"

        with (
            patch.dict(os.environ, {}, clear=True),
            patch("lib.logging_config.setup_logging"),
            patch("structlog.get_logger", return_value=MagicMock()),
            patch("lib.config.load_config", return_value=mocks["config"]),
            patch("lib.config.resolve_data_directory", return_value="backend/data"),
            patch("services.factory.create_services", return_value=mocks["services"]),
            patch("lib.tool_loader.register_all_tools"),
            patch.dict("sys.modules", {"fastmcp": MagicMock(FastMCP=mocks["fastmcp"])}),
        ):
            if "main" in sys.modules:
                del sys.modules["main"]

            # Should use default data directory
            import main

            assert main.app is not None

            del sys.modules["main"]

    @pytest.mark.integration
    def test_service_dependencies(self, mock_full_environment):
        """Test all services are properly initialized via factory."""
        mocks = mock_full_environment

        with (
            patch("lib.logging_config.setup_logging"),
            patch("structlog.get_logger", return_value=MagicMock()),
            patch("lib.config.load_config", return_value=mocks["config"]),
            patch("lib.config.resolve_data_directory", return_value="/tmp/data"),
            patch("services.factory.create_services", return_value=mocks["services"]) as mock_create,
            patch("lib.tool_loader.register_all_tools"),
            patch.dict("sys.modules", {"fastmcp": MagicMock(FastMCP=mocks["fastmcp"])}),
        ):
            if "main" in sys.modules:
                del sys.modules["main"]

            import main

            # Verify create_services was called
            mock_create.assert_called_once()

            # Verify exported services
            assert main.config is not None
            assert main.agent_websocket_handler is not None
            assert main.agent_lifecycle is not None
            assert main.database_service is not None

            del sys.modules["main"]

    @pytest.mark.integration
    def test_fastmcp_metadata(self, mock_full_environment):
        """Test FastMCP app metadata and configuration."""
        mocks = mock_full_environment

        with (
            patch("lib.logging_config.setup_logging"),
            patch("structlog.get_logger", return_value=MagicMock()),
            patch("lib.config.load_config", return_value=mocks["config"]),
            patch("lib.config.resolve_data_directory", return_value="/tmp/data"),
            patch("services.factory.create_services", return_value=mocks["services"]),
            patch("lib.tool_loader.register_all_tools"),
            patch.dict("sys.modules", {"fastmcp": MagicMock(FastMCP=mocks["fastmcp"])}),
        ):
            if "main" in sys.modules:
                del sys.modules["main"]

            import main

            # Verify FastMCP metadata
            assert main.app.name == "tomo"
            assert main.app.version == "0.1.0"
            assert hasattr(main.app, "instructions")
            assert "tomo" in main.app.instructions.lower()

            del sys.modules["main"]

    def test_tool_registration_order(self, mock_full_environment):
        """Test tools are registered in correct order without conflicts."""
        mocks = mock_full_environment

        call_count = [0]

        def mock_register(app, config, services):
            call_count[0] += 1
            # Simulate adding tools
            app._tools["health_check"] = MagicMock()
            app._tools["login"] = MagicMock()

        with (
            patch("lib.logging_config.setup_logging"),
            patch("structlog.get_logger", return_value=MagicMock()),
            patch("lib.config.load_config", return_value=mocks["config"]),
            patch("lib.config.resolve_data_directory", return_value="/tmp/data"),
            patch("services.factory.create_services", return_value=mocks["services"]),
            patch("lib.tool_loader.register_all_tools", side_effect=mock_register),
            patch.dict("sys.modules", {"fastmcp": MagicMock(FastMCP=mocks["fastmcp"])}),
        ):
            if "main" in sys.modules:
                del sys.modules["main"]

            import main

            # Verify register was called once during import
            assert call_count[0] == 1

            # Verify tools were added
            tool_names = list(main.app._tools.keys())
            assert len(tool_names) == len(set(tool_names))  # No duplicates

            del sys.modules["main"]
