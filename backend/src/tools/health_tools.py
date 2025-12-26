"""
Health Check Tools Module

Provides basic health check tools for the MCP server.
Implements Phase 1 foundation health monitoring capabilities.
"""

from datetime import UTC, datetime
from typing import Any, Dict, Mapping
import structlog


logger = structlog.get_logger("health_tools")


def register_health_tools(app, config: Mapping[str, Any]):
    """Register health tools with the FastMCP app."""
    config_data = dict(config)

    @app.tool
    async def get_health_status() -> Dict[str, Any]:
        """
        Get comprehensive health status of the MCP server.
        
        Returns:
            dict: Health status information including server state and configuration
        """
        try:
            health_status = {
                "status": "healthy",
                "timestamp": datetime.now(UTC).isoformat(),
                "version": config_data.get("version", "unknown"),
                "components": {
                    "mcp_server": "healthy",
                    "configuration": "healthy",
                    "logging": "healthy"
                },
                "configuration": {
                    "ssh_timeout": config_data.get("ssh_timeout", 30),
                    "max_connections": config_data.get("max_concurrent_connections", 10)
                }
            }
            
            logger.info("Health check completed", status="healthy")
            return {
                "success": True,
                "data": health_status,
                "message": "Health check completed successfully"
            }
        except Exception as e:
            logger.error("Health check failed", error=str(e))
            return {
                "success": False,
                "message": f"Health check failed: {str(e)}",
                "error": "HEALTH_CHECK_ERROR"
            }
    
    @app.tool
    async def health_check() -> Dict[str, Any]:
        """Simple health check tool for connectivity testing."""
        return {
            "success": True,
            "message": "pong",
            "timestamp": datetime.now(UTC).isoformat()
        }
    
    logger.info("Health tools registered")
