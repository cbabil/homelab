"""
Backup MCP Tools

Provides MCP tools for backup and restore operations.
"""

from typing import Dict, Any
import structlog
from fastmcp import FastMCP
from services.backup_service import BackupService

logger = structlog.get_logger("backup_tools")


class BackupTools:
    """Backup tools for the MCP server."""

    def __init__(self, backup_service: BackupService):
        """Initialize backup tools."""
        self.backup_service = backup_service
        logger.info("Backup tools initialized")

    async def export_backup(
        self,
        output_path: str,
        password: str
    ) -> Dict[str, Any]:
        """Export encrypted backup to file."""
        try:
            result = await self.backup_service.export_backup(output_path, password)

            if result["success"]:
                return {
                    "success": True,
                    "data": {
                        "path": result["path"],
                        "checksum": result["checksum"],
                        "size": result["size"],
                        "timestamp": result["timestamp"]
                    },
                    "message": "Backup exported successfully"
                }
            else:
                return {
                    "success": False,
                    "message": result["error"],
                    "error": "EXPORT_FAILED"
                }

        except Exception as e:
            logger.error("Export backup error", error=str(e))
            return {
                "success": False,
                "message": f"Export failed: {str(e)}",
                "error": "EXPORT_ERROR"
            }

    async def import_backup(
        self,
        input_path: str,
        password: str,
        overwrite: bool = False
    ) -> Dict[str, Any]:
        """Import backup from encrypted file."""
        try:
            result = await self.backup_service.import_backup(
                input_path, password, overwrite
            )

            if result["success"]:
                return {
                    "success": True,
                    "data": {
                        "version": result["version"],
                        "timestamp": result["timestamp"],
                        "users_imported": result["users_imported"],
                        "servers_imported": result["servers_imported"]
                    },
                    "message": "Backup imported successfully"
                }
            else:
                return {
                    "success": False,
                    "message": result["error"],
                    "error": "IMPORT_FAILED"
                }

        except Exception as e:
            logger.error("Import backup error", error=str(e))
            return {
                "success": False,
                "message": f"Import failed: {str(e)}",
                "error": "IMPORT_ERROR"
            }


def register_backup_tools(app: FastMCP, backup_service: BackupService):
    """Register backup tools with FastMCP app."""
    tools = BackupTools(backup_service)

    app.tool(tools.export_backup)
    app.tool(tools.import_backup)

    logger.info("Backup tools registered")
