"""
Integration tests for MCP Server functionality.

Tests FastMCP server integration with tools and services.
Covers tool registration, tool calls, and service initialization.
"""

import pytest
import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path


class TestMCPServerIntegration:
    """Integration test suite for MCP server functionality."""

    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Set up test environment with temporary data directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Set DATA_DIRECTORY to temporary location
            with patch.dict(os.environ, {'DATA_DIRECTORY': temp_dir}):
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

        with patch('lib.config.load_config', return_value=mock_config):
            yield {
                "config": mock_config,
            }

    def test_app_initialization(self, mock_services):
        """Test FastMCP app initialization with service dependencies."""
        with patch('main.setup_logging') as mock_logging:
            # Import main to trigger app creation
            from main import app

            assert app is not None
            assert hasattr(app, 'name')
            assert hasattr(app, 'version')
            assert app.name == "homelab-assistant"
            assert app.version == "0.1.0"

    def test_tool_registration(self, mock_services):
        """Test tools are properly registered with FastMCP."""
        with patch('main.setup_logging'):
            from main import app, tool_dependencies, config as app_config
            from lib.tool_loader import register_all_tools

            # Clear any existing tools
            app._tools = {}

            # Register tools
            register_all_tools(app, app_config, tool_dependencies)

            # Verify tools were registered
            assert len(app._tools) > 0

            # Check for expected tool categories
            tool_names = list(app._tools.keys())

            # Should have health tools
            health_tools = [name for name in tool_names if 'health' in name.lower()]
            assert len(health_tools) > 0

            # Should have authentication tools
            auth_tools = [name for name in tool_names if 'login' in name.lower() or 'logout' in name.lower()]
            assert len(auth_tools) > 0

    @pytest.mark.asyncio
    async def test_health_tool_functionality(self, mock_services):
        """Test health check tool functionality."""
        with patch('main.setup_logging'):
            from main import app, tool_dependencies, config as app_config
            from lib.tool_loader import register_all_tools
            # Ensure health tools available
            register_all_tools(app, app_config, tool_dependencies)

            health_check_tool = app._tools.get('health_check')
            assert health_check_tool is not None

            result = await health_check_tool.fn()

            assert result["success"] is True
            assert result["message"] == "pong"

    @pytest.mark.asyncio
    async def test_settings_tools_integration(self, mock_services):
        """Test settings tools integration."""
        with patch('main.setup_logging'), \
             patch('services.settings_service.SettingsService') as mock_settings_service, \
             patch('services.auth_service.AuthService') as mock_auth_service:

            from main import app
            from tools.settings_tools import register_settings_tools

            # Mock services
            mock_settings_instance = MagicMock()
            mock_settings_service.return_value = mock_settings_instance
            mock_auth_instance = MagicMock()
            mock_auth_service.return_value = mock_auth_instance

            # Register settings tools
            register_settings_tools(app, mock_settings_instance, mock_auth_instance)

            # Verify settings tools were registered
            tool_names = list(app._tools.keys())
            settings_tools = [name for name in tool_names if 'settings' in name.lower()]
            assert len(settings_tools) > 0

    def test_app_with_missing_environment(self):
        """Test app behavior when DATA_DIRECTORY is not set."""
        with patch.dict(os.environ, {}, clear=True), \
             patch('main.setup_logging'), \
             patch('lib.config.load_config', return_value={
                 "data_directory": "backend/data",
                 "app_env": "development",
                 "version": "0.1.0",
                 "ssh_timeout": 30,
                 "max_concurrent_connections": 10,
             }):

            # Should use default data directory
            from main import app
            assert app is not None

    @pytest.mark.integration
    def test_service_dependencies(self, mock_services):
        """Test all services are properly initialized."""
        with patch('main.setup_logging'):
            from main import (
                config, app_service, auth_service,
                ssh_service, monitoring_service, server_service,
                retention_service, settings_service
            )

            # Verify all services are initialized
            assert config is not None
            assert app_service is not None
            assert auth_service is not None
            assert ssh_service is not None
            assert monitoring_service is not None
            assert server_service is not None
            assert retention_service is not None
            assert settings_service is not None

    @pytest.mark.integration
    def test_fastmcp_metadata(self, mock_services):
        """Test FastMCP app metadata and configuration."""
        with patch('main.setup_logging'):
            from main import app

            # Verify FastMCP metadata
            assert app.name == "homelab-assistant"
            assert app.version == "0.1.0"
            assert hasattr(app, 'instructions')
            assert "homelab" in app.instructions.lower()

    def test_tool_registration_order(self, mock_services):
        """Test tools are registered in correct order without conflicts."""
        with patch('main.setup_logging'):
            from main import app, tool_dependencies, config as app_config
            from lib.tool_loader import register_all_tools

            # Clear tools
            app._tools = {}

            # Register tools multiple times to test for conflicts
            register_all_tools(app, app_config, tool_dependencies)
            initial_count = len(app._tools)

            register_all_tools(app, app_config, tool_dependencies)
            final_count = len(app._tools)

            # Should not duplicate tools
            assert final_count == initial_count

            # Verify no tool names conflict
            tool_names = list(app._tools.keys())
            assert len(tool_names) == len(set(tool_names))  # No duplicates
