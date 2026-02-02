"""
Integration Tests for MCP Server

Tests the complete integration of services, tools, and endpoints.
Ensures end-to-end functionality of the tomo MCP server.
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
            with patch.dict(os.environ, {"DATA_DIRECTORY": temp_dir}):
                yield temp_dir

    def test_main_module_imports(self):
        """Test that main module imports successfully."""
        with patch("main.setup_logging"):
            try:
                import main

                assert main.app is not None
                assert hasattr(main.app, "name")
                assert hasattr(main.app, "version")
            except Exception as e:
                pytest.fail(f"Failed to import main module: {e}")

    def test_all_services_initialize(self):
        """Test that all services initialize without errors."""
        with patch("main.setup_logging"):
            try:
                from main import config, services

                # Get services from the services dict
                app_service = services.get("app_service")
                auth_service = services.get("auth_service")
                ssh_service = services.get("ssh_service")
                server_service = services.get("server_service")
                retention_service = services.get("retention_service")
                settings_service = services.get("settings_service")

                # Basic smoke test - services should exist
                service_list = [
                    config,
                    app_service,
                    auth_service,
                    ssh_service,
                    server_service,
                    retention_service,
                    settings_service,
                ]

                for service in service_list:
                    assert service is not None

            except Exception as e:
                pytest.fail(f"Failed to initialize services: {e}")

    def test_tool_registration_completes(self):
        """Test that tool registration completed during module import."""
        with patch("main.setup_logging"):
            try:
                from main import app

                # Tools are registered during module import by register_all_tools
                # We verify tools exist via the tool manager
                tool_manager = app._tool_manager
                assert tool_manager is not None
                assert hasattr(tool_manager, "_tools")
                assert len(tool_manager._tools) > 0, "Expected tools to be registered"

            except Exception as e:
                pytest.fail(f"Failed to verify tool registration: {e}")

    def test_app_metadata_is_correct(self):
        """Test that app metadata is properly configured."""
        with patch("main.setup_logging"):
            from main import app

            assert app.name == "tomo"
            assert app.version == "0.1.0"
            assert "tomo" in app.instructions.lower()

    @pytest.mark.slow
    def test_full_server_initialization(self):
        """Test complete server initialization process."""
        with patch("main.setup_logging"):
            try:
                from main import app

                # Verify server is in a valid state after initialization
                assert app is not None
                tool_manager = app._tool_manager
                assert len(tool_manager._tools) > 0, "Expected tools to be registered"

            except Exception as e:
                pytest.fail(f"Full server initialization failed: {e}")

    def test_data_directory_configured(self):
        """Test that data directory is properly configured."""
        with patch("main.setup_logging"):
            try:
                from main import config

                # Verify config has data_directory key
                assert "data_directory" in config
                # Verify it's a valid path string
                assert isinstance(config["data_directory"], str)
                assert len(config["data_directory"]) > 0

            except Exception as e:
                pytest.fail(f"Data directory configuration error: {e}")

    def test_service_interdependencies(self):
        """Test that services with dependencies work together."""
        with patch("main.setup_logging"):
            try:
                from main import services

                auth_service = services.get("auth_service")
                settings_service = services.get("settings_service")

                # Services that depend on each other should both initialize
                assert auth_service is not None
                assert settings_service is not None

            except Exception as e:
                pytest.fail(f"Service interdependency test failed: {e}")
