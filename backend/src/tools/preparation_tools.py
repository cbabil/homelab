"""
Server Preparation Tools

Provides MCP tools for server preparation workflow.
"""

from datetime import datetime, UTC
from typing import Dict, Any
import uuid
import structlog
from fastmcp import FastMCP
from services.preparation_service import PreparationService
from services.service_log import log_service
from models.log import LogEntry


logger = structlog.get_logger("preparation_tools")


async def _log_preparation_event(level: str, message: str, metadata: Dict[str, Any] = None):
    """Helper to log preparation events to the database."""
    try:
        entry = LogEntry(
            id=f"prp-{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now(UTC),
            level=level,
            source="prp",
            message=message,
            tags=["preparation", "infrastructure"],
            metadata=metadata or {}
        )
        await log_service.create_log_entry(entry)
    except Exception as e:
        logger.error("Failed to create log entry", error=str(e))


class PreparationTools:
    """Preparation tools for the MCP server."""

    def __init__(self, preparation_service: PreparationService):
        """Initialize preparation tools."""
        self.preparation_service = preparation_service
        logger.info("Preparation tools initialized")

    async def prepare_server(self, server_id: str) -> Dict[str, Any]:
        """Start server preparation to install Docker."""
        try:
            preparation = await self.preparation_service.start_preparation(server_id)

            if not preparation:
                await _log_preparation_event("ERROR", f"Server preparation failed to start: {server_id}", {
                    "server_id": server_id
                })
                return {
                    "success": False,
                    "message": "Failed to start preparation",
                    "error": "PREPARATION_START_FAILED"
                }

            await _log_preparation_event("INFO", f"Server preparation started: {server_id}", {
                "server_id": server_id,
                "preparation_id": preparation.id
            })
            logger.info("Preparation started", server_id=server_id, prep_id=preparation.id)
            return {
                "success": True,
                "data": {"preparation_id": preparation.id, "server_id": server_id},
                "message": "Preparation started"
            }
        except Exception as e:
            logger.error("Prepare server error", error=str(e))
            await _log_preparation_event("ERROR", f"Server preparation error: {server_id}", {"error": str(e)})
            return {
                "success": False,
                "message": f"Failed to prepare server: {str(e)}",
                "error": "PREPARE_SERVER_ERROR"
            }

    async def get_preparation_status(self, server_id: str) -> Dict[str, Any]:
        """Get current preparation status for a server."""
        try:
            status = await self.preparation_service.get_preparation_status(server_id)

            if not status:
                return {
                    "success": False,
                    "message": "No preparation found for server",
                    "error": "PREPARATION_NOT_FOUND"
                }

            return {
                "success": True,
                "data": status,
                "message": "Preparation status retrieved"
            }
        except Exception as e:
            logger.error("Get preparation status error", error=str(e))
            return {
                "success": False,
                "message": f"Failed to get status: {str(e)}",
                "error": "GET_STATUS_ERROR"
            }

    async def get_preparation_logs(self, server_id: str) -> Dict[str, Any]:
        """Get full preparation log history."""
        try:
            status = await self.preparation_service.get_preparation_status(server_id)

            if not status:
                return {
                    "success": False,
                    "message": "No preparation found",
                    "error": "PREPARATION_NOT_FOUND"
                }

            return {
                "success": True,
                "data": {"logs": status.get("logs", [])},
                "message": f"Retrieved {len(status.get('logs', []))} log entries"
            }
        except Exception as e:
            logger.error("Get preparation logs error", error=str(e))
            return {
                "success": False,
                "message": f"Failed to get logs: {str(e)}",
                "error": "GET_LOGS_ERROR"
            }

    async def retry_preparation(self, server_id: str) -> Dict[str, Any]:
        """Retry failed preparation from last failed step."""
        try:
            # Get current status to find failed step
            status = await self.preparation_service.get_preparation_status(server_id)

            if not status:
                return {
                    "success": False,
                    "message": "No preparation found",
                    "error": "PREPARATION_NOT_FOUND"
                }

            if status["status"] != "failed":
                return {
                    "success": False,
                    "message": "Preparation is not in failed state",
                    "error": "INVALID_STATE"
                }

            # Start new preparation (will continue from where it left off)
            preparation = await self.preparation_service.start_preparation(server_id)

            if not preparation:
                await _log_preparation_event("ERROR", f"Server preparation retry failed: {server_id}", {
                    "server_id": server_id
                })
                return {
                    "success": False,
                    "message": "Failed to retry preparation",
                    "error": "RETRY_FAILED"
                }

            await _log_preparation_event("INFO", f"Server preparation retry started: {server_id}", {
                "server_id": server_id,
                "preparation_id": preparation.id
            })
            return {
                "success": True,
                "data": {"preparation_id": preparation.id},
                "message": "Preparation retry started"
            }
        except Exception as e:
            logger.error("Retry preparation error", error=str(e))
            await _log_preparation_event("ERROR", f"Server preparation retry error: {server_id}", {"error": str(e)})
            return {
                "success": False,
                "message": f"Failed to retry: {str(e)}",
                "error": "RETRY_ERROR"
            }


def register_preparation_tools(app: FastMCP, preparation_service: PreparationService):
    """Register preparation tools with FastMCP app."""
    tools = PreparationTools(preparation_service)

    app.tool(tools.prepare_server)
    app.tool(tools.get_preparation_status)
    app.tool(tools.get_preparation_logs)
    app.tool(tools.retry_preparation)

    logger.info("Preparation tools registered")
