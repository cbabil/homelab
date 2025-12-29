"""
Server Management Tools

Provides server connection and management capabilities for the MCP server.
"""

from typing import Dict, Any
from datetime import datetime, UTC
import uuid
import structlog
from fastmcp import FastMCP
from models.server import ServerConnection, ServerStatus, AuthType
from models.log import LogEntry
from services.ssh_service import SSHService
from services.server_service import ServerService
from services.service_log import log_service


logger = structlog.get_logger("server_tools")


async def _log_server_event(level: str, message: str, metadata: Dict[str, Any] = None):
    """Helper to log server events to the database."""
    try:
        entry = LogEntry(
            id=f"srv-{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now(UTC),
            level=level,
            source="srv",
            message=message,
            tags=["server", "infrastructure"],
            metadata=metadata or {}
        )
        await log_service.create_log_entry(entry)
    except Exception as e:
        logger.error("Failed to create log entry", error=str(e))


class ServerTools:
    """Server management tools for the MCP server."""

    def __init__(self, ssh_service: SSHService, server_service: ServerService):
        """Initialize server tools."""
        self.ssh_service = ssh_service
        self.server_service = server_service
        logger.info("Server tools initialized")

    async def add_server(
        self,
        name: str,
        host: str,
        port: int,
        username: str,
        auth_type: str,
        password: str = None,
        private_key: str = None
    ) -> Dict[str, Any]:
        """Add a new server with credentials."""
        try:
            server_id = f"server-{uuid.uuid4().hex[:8]}"
            credentials = {"password": password} if auth_type == "password" else {"private_key": private_key}

            server = await self.server_service.add_server(
                server_id=server_id,
                name=name,
                host=host,
                port=port,
                username=username,
                auth_type=auth_type,
                credentials=credentials
            )

            if not server:
                await _log_server_event("ERROR", f"Failed to add server: {name}", {"host": host})
                return {
                    "success": False,
                    "message": "Failed to add server",
                    "error": "ADD_SERVER_ERROR"
                }

            await _log_server_event("INFO", f"Server added: {name}", {
                "server_id": server_id,
                "host": host,
                "port": port
            })
            logger.info("Server added", server_id=server_id, name=name)
            return {
                "success": True,
                "data": server.model_dump(),
                "message": f"Server '{name}' added successfully"
            }
        except Exception as e:
            logger.error("Add server error", error=str(e))
            await _log_server_event("ERROR", f"Failed to add server: {name}", {"error": str(e)})
            return {
                "success": False,
                "message": f"Failed to add server: {str(e)}",
                "error": "ADD_SERVER_ERROR"
            }

    async def get_server(self, server_id: str) -> Dict[str, Any]:
        """Get server by ID."""
        try:
            server = await self.server_service.get_server(server_id)

            if not server:
                return {
                    "success": False,
                    "message": "Server not found",
                    "error": "SERVER_NOT_FOUND"
                }

            return {
                "success": True,
                "data": server.model_dump(),
                "message": "Server retrieved"
            }
        except Exception as e:
            logger.error("Get server error", error=str(e))
            return {
                "success": False,
                "message": f"Failed to get server: {str(e)}",
                "error": "GET_SERVER_ERROR"
            }

    async def list_servers(self) -> Dict[str, Any]:
        """List all servers."""
        try:
            servers = await self.server_service.get_all_servers()

            return {
                "success": True,
                "data": {"servers": [s.model_dump() for s in servers]},
                "message": f"Retrieved {len(servers)} servers"
            }
        except Exception as e:
            logger.error("List servers error", error=str(e))
            return {
                "success": False,
                "message": f"Failed to list servers: {str(e)}",
                "error": "LIST_SERVERS_ERROR"
            }

    async def sync_server(
        self,
        server_id: str,
        name: str,
        host: str,
        port: int,
        username: str,
        auth_type: str,
        status: str = "disconnected",
        password: str = None,
        private_key: str = None
    ) -> Dict[str, Any]:
        """Sync a server from frontend storage to database (upsert)."""
        try:
            # Check if server exists
            existing = await self.server_service.get_server(server_id)

            if existing:
                # Update existing server
                await self.server_service.update_server(
                    server_id=server_id,
                    name=name,
                    host=host,
                    port=port,
                    username=username
                )
                # Update status
                from models.server import ServerStatus
                await self.server_service.update_server_status(server_id, ServerStatus(status))
                return {
                    "success": True,
                    "message": f"Server '{name}' synced (updated)"
                }
            else:
                # Add new server
                credentials = {"password": password} if auth_type == "password" else {"private_key": private_key}
                server = await self.server_service.add_server(
                    server_id=server_id,
                    name=name,
                    host=host,
                    port=port,
                    username=username,
                    auth_type=auth_type,
                    credentials=credentials
                )

                if server:
                    # Update status after adding
                    from models.server import ServerStatus
                    await self.server_service.update_server_status(server_id, ServerStatus(status))

                return {
                    "success": True,
                    "message": f"Server '{name}' synced (added)"
                }
        except Exception as e:
            logger.error("Sync server error", error=str(e))
            return {
                "success": False,
                "message": f"Failed to sync server: {str(e)}",
                "error": "SYNC_SERVER_ERROR"
            }

    async def update_server(
        self,
        server_id: str,
        name: str = None,
        host: str = None,
        port: int = None,
        username: str = None
    ) -> Dict[str, Any]:
        """Update server configuration."""
        try:
            success = await self.server_service.update_server(
                server_id=server_id,
                name=name,
                host=host,
                port=port,
                username=username
            )

            if not success:
                return {
                    "success": False,
                    "message": "Server not found",
                    "error": "SERVER_NOT_FOUND"
                }

            await _log_server_event("INFO", f"Server updated: {server_id}", {
                "server_id": server_id,
                "name": name,
                "host": host
            })
            return {
                "success": True,
                "message": "Server updated successfully"
            }
        except Exception as e:
            logger.error("Update server error", error=str(e))
            await _log_server_event("ERROR", f"Failed to update server: {server_id}", {"error": str(e)})
            return {
                "success": False,
                "message": f"Failed to update server: {str(e)}",
                "error": "UPDATE_SERVER_ERROR"
            }

    async def delete_server(self, server_id: str) -> Dict[str, Any]:
        """Delete a server."""
        try:
            success = await self.server_service.delete_server(server_id)

            if not success:
                await _log_server_event("WARNING", f"Server not found for deletion: {server_id}")
                return {
                    "success": False,
                    "message": "Server not found or delete failed",
                    "error": "DELETE_SERVER_ERROR"
                }

            await _log_server_event("INFO", f"Server deleted: {server_id}", {"server_id": server_id})
            logger.info("Server deleted", server_id=server_id)
            return {
                "success": True,
                "message": "Server deleted successfully"
            }
        except Exception as e:
            logger.error("Delete server error", error=str(e))
            await _log_server_event("ERROR", f"Failed to delete server: {server_id}", {"error": str(e)})
            return {
                "success": False,
                "message": f"Failed to delete server: {str(e)}",
                "error": "DELETE_SERVER_ERROR"
            }

    async def test_connection(self, server_id: str) -> Dict[str, Any]:
        """Test SSH connection to a server."""
        try:
            server = await self.server_service.get_server(server_id)
            if not server:
                return {
                    "success": False,
                    "message": "Server not found",
                    "error": "SERVER_NOT_FOUND"
                }

            credentials = await self.server_service.get_credentials(server_id)
            if not credentials:
                return {
                    "success": False,
                    "message": "Credentials not found",
                    "error": "CREDENTIALS_NOT_FOUND"
                }

            success, message, system_info = await self.ssh_service.test_connection(
                host=server.host,
                port=server.port,
                username=server.username,
                auth_type=server.auth_type.value,
                credentials=credentials
            )

            if success:
                await self.server_service.update_server_status(server_id, ServerStatus.CONNECTED)
                await _log_server_event("INFO", f"Connection test successful: {server.name}", {
                    "server_id": server_id,
                    "host": server.host
                })
                return {
                    "success": True,
                    "data": {"system_info": system_info},
                    "message": "Connection successful"
                }
            else:
                await self.server_service.update_server_status(server_id, ServerStatus.ERROR)
                await _log_server_event("WARNING", f"Connection test failed: {server.name}", {
                    "server_id": server_id,
                    "host": server.host,
                    "error": message
                })
                return {
                    "success": False,
                    "message": message,
                    "error": "CONNECTION_FAILED"
                }
        except Exception as e:
            logger.error("Test connection error", error=str(e))
            await _log_server_event("ERROR", f"Connection test error: {server_id}", {"error": str(e)})
            return {
                "success": False,
                "message": f"Connection test failed: {str(e)}",
                "error": "CONNECTION_TEST_ERROR"
            }


def register_server_tools(app: FastMCP, ssh_service: SSHService, server_service: ServerService):
    """Register server tools with FastMCP app."""
    tools = ServerTools(ssh_service, server_service)

    app.tool(tools.add_server)
    app.tool(tools.get_server)
    app.tool(tools.list_servers)
    app.tool(tools.sync_server)
    app.tool(tools.update_server)
    app.tool(tools.delete_server)
    app.tool(tools.test_connection)

    logger.info("Server tools registered")
