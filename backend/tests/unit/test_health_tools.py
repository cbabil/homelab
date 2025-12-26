"""
Unit tests for Health Check Tools.

Tests MCP health check functionality with proper mocking.
Covers successful health checks and error handling scenarios.
"""

import asyncio
import os
import tempfile
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from tools.health_tools import register_health_tools


class TestHealthTools:
    """Test suite for health check tools functionality."""

    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Set up test environment with temporary data directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {'DATA_DIRECTORY': temp_dir}):
                yield temp_dir

    @pytest.fixture
    def config_data(self):
        """Sample configuration data for tests."""
        return {
            "version": "0.1.0",
            "ssh_timeout": 30,
            "max_concurrent_connections": 10,
        }

    @pytest.fixture
    def mock_app(self):
        """Mock FastMCP app for testing."""
        app = MagicMock()
        app._tools = {}

        def mock_tool(func):
            app._tools[func.__name__] = MagicMock(fn=func)
            return func

        app.tool = mock_tool
        return app

    def test_register_health_tools(self, mock_app, config_data):
        """Test health tools registration."""
        register_health_tools(mock_app, config_data)

        # Verify tools were registered
        assert 'get_health_status' in mock_app._tools
        assert 'health_check' in mock_app._tools

    @pytest.mark.asyncio
    async def test_get_health_status_success(self, mock_app, config_data):
        """Test successful health status check."""
        register_health_tools(mock_app, config_data)

        # Get the registered tool function
        health_tool = mock_app._tools['get_health_status']

        # Call the tool function
        result = await health_tool.fn()

        # Verify response
        assert result["success"] is True
        assert result["message"] == "Health check completed successfully"
        payload = result["data"]
        assert payload["status"] == "healthy"
        assert payload["version"] == "0.1.0"
        assert "timestamp" in payload
        assert "configuration" in payload

    @pytest.mark.asyncio
    async def test_health_check_success(self, mock_app, config_data):
        """Test simple health check endpoint."""
        register_health_tools(mock_app, config_data)

        health_check_tool = mock_app._tools['health_check']
        result = await health_check_tool.fn()

        # Verify simple health check response
        assert result["success"] is True
        assert result["message"] == "pong"
        assert "timestamp" in result

    def test_health_tools_structure(self, mock_app, config_data):
        """Test that health tools are properly structured."""
        register_health_tools(mock_app, config_data)

        # Check expected tools exist
        expected_tools = ['get_health_status', 'health_check']

        for tool_name in expected_tools:
            assert tool_name in mock_app._tools
            tool = mock_app._tools[tool_name]
            assert hasattr(tool, 'fn')
            assert callable(tool.fn)

    @pytest.mark.asyncio
    async def test_health_status_timestamp_format(self, mock_app, config_data):
        """Test health status timestamp is properly formatted."""
        register_health_tools(mock_app, config_data)

        health_tool = mock_app._tools['get_health_status']
        result = await health_tool.fn()
        payload = result["data"]

        # Verify timestamp format
        timestamp = payload["timestamp"]
        # Should be parseable as ISO format
        parsed_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        assert isinstance(parsed_time, datetime)

    @pytest.mark.asyncio
    async def test_health_status_config_content(self, mock_app, config_data):
        """Test health status includes config information."""
        expected_config = {
            "version": "0.1.0",
            "ssh_timeout": 30,
            "max_concurrent_connections": 10
        }
        register_health_tools(mock_app, expected_config)

        health_tool = mock_app._tools['get_health_status']
        result = await health_tool.fn()
        payload = result["data"]

        # Verify config is included
        assert payload["configuration"]["ssh_timeout"] == expected_config["ssh_timeout"]

    @pytest.mark.asyncio
    async def test_concurrent_health_checks(self, mock_app, config_data):
        """Test multiple concurrent health checks."""
        register_health_tools(mock_app, config_data)
        health_tool = mock_app._tools['health_check']

        # Run multiple health checks concurrently
        tasks = [health_tool.fn() for _ in range(5)]
        results = await asyncio.gather(*tasks)

        # All should succeed
        assert len(results) == 5
        for result in results:
            assert result["success"] is True
            assert result["message"] == "pong"
