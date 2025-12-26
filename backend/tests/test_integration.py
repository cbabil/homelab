"""
Integration Tests for MCP Server

Tests the complete integration of services, tools, and endpoints.
Ensures end-to-end functionality of the homelab MCP server.
"""

import pytest
import os
import tempfile
from unittest.mock import patch


@pytest.mark.integration
class TestMCPServerIntegration:
    """Integration test cases for complete MCP server."""

    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Set up test environment with temporary data directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {'DATA_DIRECTORY': temp_dir}):
                yield temp_dir

    def test_main_module_imports(self):
        """Test that main module imports successfully."""
        with patch('main.setup_logging'):
            try:
                import main
                assert main.app is not None
                assert hasattr(main.app, 'name')
                assert hasattr(main.app, 'version')
            except Exception as e:
                pytest.fail(f"Failed to import main module: {e}")

    def test_all_services_initialize(self):
        """Test that all services initialize without errors."""
        with patch('main.setup_logging'):
            try:
                from main import (
                    config, app_service, auth_service,
                    ssh_service, monitoring_service, server_service,
                    retention_service, settings_service
                )

                # Basic smoke test - services should exist
                services = [
                    config, app_service, auth_service,
                    ssh_service, monitoring_service, server_service,
                    retention_service, settings_service
                ]

                for service in services:
                    assert service is not None

            except Exception as e:
                pytest.fail(f"Failed to initialize services: {e}")

    def test_tool_registration_completes(self):
        """Test that tool registration completes without errors."""
        with patch('main.setup_logging'):
            try:
                from main import app, tool_dependencies, config as app_config
                from lib.tool_loader import register_all_tools

                # Clear existing tools
                app._tools = {}

                # Register all tools
                register_all_tools(app, app_config, tool_dependencies)

                # Should have registered some tools
                assert len(app._tools) > 0

            except Exception as e:
                pytest.fail(f"Failed to register tools: {e}")

    def test_app_metadata_is_correct(self):
        """Test that app metadata is properly configured."""
        with patch('main.setup_logging'):
            from main import app

            assert app.name == "homelab-assistant"
            assert app.version == "0.1.0"
            assert "homelab" in app.instructions.lower()

    @pytest.mark.slow
    def test_full_server_initialization(self):
        """Test complete server initialization process."""
        with patch('main.setup_logging'):
            try:
                # Import and initialize everything
                from main import app, tool_dependencies, config as app_config
                from lib.tool_loader import register_all_tools

                # Should complete without errors
                register_all_tools(app, app_config, tool_dependencies)

                # Verify server is in a valid state
                assert app is not None
                assert len(app._tools) > 0

            except Exception as e:
                pytest.fail(f"Full server initialization failed: {e}")

    def test_data_directory_handling(self):
        """Test that data directory is properly handled."""
        with patch('main.setup_logging'):
            # Test with custom DATA_DIRECTORY
            with patch.dict(os.environ, {'DATA_DIRECTORY': '/tmp/test_homelab'}), \
                patch('lib.config.load_config', return_value={
                    "data_directory": '/tmp/test_homelab',
                    "app_env": "development",
                    "version": "0.1.0",
                    "ssh_timeout": 30,
                    "max_concurrent_connections": 10,
                    "tools_directory": '/tmp/test_homelab/tools',
                    "tools_package": 'tools',
                }):
                try:
                    from main import config
                    assert config["data_directory"].endswith('test_homelab')
                except Exception as e:
                    if "Read-only file system" not in str(e):
                        pytest.fail(f"Unexpected error with custom DATA_DIRECTORY: {e}")

    def test_service_interdependencies(self):
        """Test that services with dependencies work together."""
        with patch('main.setup_logging'):
            try:
                from main import auth_service, settings_service

                # Services that depend on each other should both initialize
                assert auth_service is not None
                assert settings_service is not None

            except Exception as e:
                pytest.fail(f"Service interdependency test failed: {e}")
