"""
Unit tests for tools/health/tools.py - HealthTools class.

Tests for health check functionality.
"""

from unittest.mock import patch

import pytest

from tools.health.tools import HealthTools


@pytest.fixture
def config():
    """Sample config for health tools."""
    return {"version": "1.0.0", "ssh_timeout": 30, "max_concurrent_connections": 10}


@pytest.fixture
def health_tools(config):
    """Create HealthTools instance."""
    return HealthTools(config)


class TestHealthToolsInit:
    """Tests for HealthTools initialization."""

    def test_initialization(self, config):
        """Test HealthTools is initialized correctly."""
        tools = HealthTools(config)
        assert tools.config == config
        assert tools.config["version"] == "1.0.0"

    def test_initialization_with_mapping(self):
        """Test HealthTools accepts any mapping type."""
        from collections import ChainMap

        config = ChainMap({"version": "2.0.0"}, {"ssh_timeout": 60})
        tools = HealthTools(config)
        assert tools.config["version"] == "2.0.0"
        assert tools.config["ssh_timeout"] == 60


class TestHealthCheck:
    """Tests for health_check method."""

    @pytest.mark.asyncio
    async def test_simple_health_check(self, health_tools):
        """Test simple health check returns pong."""
        result = await health_tools.health_check(detailed=False)

        assert result["success"] is True
        assert result["message"] == "pong"
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_default_is_simple(self, health_tools):
        """Test default health check is simple (not detailed)."""
        result = await health_tools.health_check()

        assert result["success"] is True
        assert result["message"] == "pong"
        assert "data" not in result

    @pytest.mark.asyncio
    async def test_detailed_health_check(self, health_tools):
        """Test detailed health check returns full status."""
        result = await health_tools.health_check(detailed=True)

        assert result["success"] is True
        assert "data" in result
        assert result["data"]["status"] == "healthy"
        assert result["data"]["version"] == "1.0.0"
        assert "components" in result["data"]
        assert result["data"]["components"]["mcp_server"] == "healthy"
        assert result["data"]["components"]["configuration"] == "healthy"
        assert result["data"]["components"]["logging"] == "healthy"

    @pytest.mark.asyncio
    async def test_detailed_health_check_config_values(self, health_tools):
        """Test detailed health check includes config values."""
        result = await health_tools.health_check(detailed=True)

        config = result["data"]["configuration"]
        assert config["ssh_timeout"] == 30
        assert config["max_connections"] == 10

    @pytest.mark.asyncio
    async def test_detailed_health_check_default_values(self):
        """Test detailed health check uses defaults for missing config."""
        tools = HealthTools({})
        result = await tools.health_check(detailed=True)

        assert result["data"]["version"] == "unknown"
        config = result["data"]["configuration"]
        assert config["ssh_timeout"] == 30
        assert config["max_connections"] == 10

    @pytest.mark.asyncio
    async def test_health_check_exception_handling(self, health_tools):
        """Test health check handles exceptions gracefully."""
        with patch.object(health_tools, "config", None):
            # This will cause an exception when trying to call .get() on None
            result = await health_tools.health_check(detailed=True)

        assert result["success"] is False
        assert result["error"] == "HEALTH_CHECK_ERROR"
        assert "Health check failed" in result["message"]
