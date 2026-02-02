"""
Health Check Tools Module

Provides basic health check tools for the MCP server.
Implements Phase 1 foundation health monitoring capabilities.
"""

from datetime import UTC, datetime
from typing import Any, Dict, Mapping
import structlog


logger = structlog.get_logger("health_tools")


class HealthTools:
    """Health check tools for the MCP server."""

    def __init__(self, config: Mapping[str, Any]):
        """Initialize health tools.

        Args:
            config: Application configuration mapping.
        """
        self.config = dict(config)
        logger.info("Health tools initialized")

    async def health_check(self, detailed: bool = False) -> Dict[str, Any]:
        """
        Check MCP server health status.

        Args:
            detailed: If True, returns comprehensive status with components and config.
                     If False (default), returns a simple ping response.

        Returns:
            dict: Health status information
        """
        try:
            timestamp = datetime.now(UTC).isoformat()

            if not detailed:
                return {
                    "success": True,
                    "message": "pong",
                    "timestamp": timestamp
                }

            health_status = {
                "status": "healthy",
                "timestamp": timestamp,
                "version": self.config.get("version", "unknown"),
                "components": {
                    "mcp_server": "healthy",
                    "configuration": "healthy",
                    "logging": "healthy"
                },
                "configuration": {
                    "ssh_timeout": self.config.get("ssh_timeout", 30),
                    "max_connections": self.config.get("max_concurrent_connections", 10)
                }
            }

            logger.info("Health check completed", status="healthy", detailed=detailed)
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
