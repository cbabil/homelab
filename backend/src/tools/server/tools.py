"""
Server Management Tools

Provides server connection and management capabilities for the MCP server.
Includes routed command execution through agent or SSH.
"""

import uuid
from typing import Any

import structlog

from lib.security import validate_command
from models.server import ServerStatus
from services.agent_service import AgentService
from services.command_router import CommandRouter
from services.server_service import ServerService
from services.ssh_service import SSHService
from tools.common import log_event

logger = structlog.get_logger("server_tools")

SERVER_TAGS = ["server", "infrastructure"]


class ServerTools:
    """Server management tools for the MCP server."""

    def __init__(
        self,
        ssh_service: SSHService,
        server_service: ServerService,
        agent_service: AgentService,
        command_router: CommandRouter | None = None,
    ):
        """Initialize server tools.

        Args:
            ssh_service: SSH service for direct connections.
            server_service: Server service for CRUD operations.
            agent_service: Agent service for agent lifecycle operations.
            command_router: Optional command router for agent-based execution.
        """
        self.ssh_service = ssh_service
        self.server_service = server_service
        self.agent_service = agent_service
        self.command_router = command_router
        logger.info("Server tools initialized")

    async def add_server(
        self,
        name: str,
        host: str,
        port: int,
        username: str,
        auth_type: str,
        password: str = None,
        private_key: str = None,
        server_id: str = None,
        system_info: dict[str, Any] = None,
    ) -> dict[str, Any]:
        """Add a new server with credentials and optional system info."""
        try:
            # Use provided server_id or generate a new one
            if not server_id:
                server_id = f"server-{uuid.uuid4().hex[:8]}"
            credentials = (
                {"password": password}
                if auth_type == "password"
                else {"private_key": private_key}
            )

            # Check if server with same connection details already exists
            existing = await self.server_service.get_server_by_connection(
                host, port, username
            )
            if existing:
                # Update existing server's credentials and name
                await self.server_service.update_credentials(existing.id, credentials)
                await self.server_service.update_server(
                    existing.id, name=name, auth_type=auth_type
                )
                logger.info(
                    "Updated existing server",
                    server_id=existing.id,
                    name=name,
                )
                server = await self.server_service.get_server(existing.id)
                return {
                    "success": True,
                    "data": server.model_dump() if server else None,
                    "message": f"Server '{name}' updated (existing connection)",
                    "server_id": existing.id,
                    "was_existing": True,
                }

            server = await self.server_service.add_server(
                server_id=server_id,
                name=name,
                host=host,
                port=port,
                username=username,
                auth_type=auth_type,
                credentials=credentials,
            )

            if not server:
                await log_event(
                    "server",
                    "ERROR",
                    f"Failed to add server: {name}",
                    SERVER_TAGS,
                    {"host": host},
                )
                return {
                    "success": False,
                    "message": "Failed to add server",
                    "error": "ADD_SERVER_ERROR",
                }

            # Persist system_info if provided
            if system_info:
                await self.server_service.update_server_system_info(
                    server_id, system_info
                )
                server = await self.server_service.get_server(server_id)

            docker_installed = server.docker_installed if server else False
            await log_event(
                "server",
                "INFO",
                f"Server added: {name}",
                SERVER_TAGS,
                {
                    "server_id": server_id,
                    "host": host,
                    "port": port,
                    "docker_installed": docker_installed,
                },
            )
            logger.info(
                "Server added",
                server_id=server_id,
                name=name,
                docker_installed=docker_installed,
            )
            return {
                "success": True,
                "data": server.model_dump(),
                "message": f"Server '{name}' added successfully",
            }
        except Exception as e:
            logger.error("Add server error", error=str(e))
            await log_event(
                "server",
                "ERROR",
                f"Failed to add server: {name}",
                SERVER_TAGS,
                {"error": str(e)},
            )
            from tools.common import safe_error_message

            return {
                "success": False,
                "message": safe_error_message(e, "Add server"),
                "error": "ADD_SERVER_ERROR",
            }

    async def get_server(self, server_id: str) -> dict[str, Any]:
        """Get server by ID."""
        try:
            server = await self.server_service.get_server(server_id)

            if not server:
                return {
                    "success": False,
                    "message": "Server not found",
                    "error": "SERVER_NOT_FOUND",
                }

            return {
                "success": True,
                "data": server.model_dump(),
                "message": "Server retrieved",
            }
        except Exception as e:
            logger.error("Get server error", error=str(e))
            return {
                "success": False,
                "message": f"Failed to get server: {str(e)}",
                "error": "GET_SERVER_ERROR",
            }

    async def list_servers(self) -> dict[str, Any]:
        """List all servers."""
        try:
            servers = await self.server_service.get_all_servers()

            return {
                "success": True,
                "data": {"servers": [s.model_dump() for s in servers]},
                "message": f"Retrieved {len(servers)} servers",
            }
        except Exception as e:
            logger.error("List servers error", error=str(e))
            return {
                "success": False,
                "message": f"Failed to list servers: {str(e)}",
                "error": "LIST_SERVERS_ERROR",
            }

    async def update_server(
        self,
        server_id: str,
        name: str = None,
        host: str = None,
        port: int = None,
        username: str = None,
    ) -> dict[str, Any]:
        """Update server configuration."""
        try:
            success = await self.server_service.update_server(
                server_id=server_id, name=name, host=host, port=port, username=username
            )

            if not success:
                return {
                    "success": False,
                    "message": "Server not found",
                    "error": "SERVER_NOT_FOUND",
                }

            await log_event(
                "server",
                "INFO",
                f"Server updated: {server_id}",
                SERVER_TAGS,
                {"server_id": server_id, "name": name, "host": host},
            )
            return {"success": True, "message": "Server updated successfully"}
        except Exception as e:
            logger.error("Update server error", error=str(e))
            await log_event(
                "server",
                "ERROR",
                f"Failed to update server: {server_id}",
                SERVER_TAGS,
                {"error": str(e)},
            )
            from tools.common import safe_error_message

            return {
                "success": False,
                "message": safe_error_message(e, "Update server"),
                "error": "UPDATE_SERVER_ERROR",
            }

    async def delete_server(self, server_id: str) -> dict[str, Any]:
        """Delete a server."""
        try:
            # Get server name before deletion for logging
            server = await self.server_service.get_server(server_id)
            server_name = server.name if server else server_id

            success = await self.server_service.delete_server(server_id)

            if not success:
                await log_event(
                    "server",
                    "WARNING",
                    f"Server not found for deletion: {server_name}",
                    SERVER_TAGS,
                )
                return {
                    "success": False,
                    "message": "Server not found or delete failed",
                    "error": "DELETE_SERVER_ERROR",
                }

            await log_event(
                "server",
                "INFO",
                f"Server deleted: {server_name}",
                SERVER_TAGS,
                {"server_id": server_id, "server_name": server_name},
            )
            logger.info("Server deleted", server_id=server_id, server_name=server_name)
            return {"success": True, "message": "Server deleted successfully"}
        except Exception as e:
            logger.error("Delete server error", error=str(e))
            await log_event(
                "server",
                "ERROR",
                f"Failed to delete server: {server_id}",
                SERVER_TAGS,
                {"error": str(e)},
            )
            from tools.common import safe_error_message

            return {
                "success": False,
                "message": safe_error_message(e, "Delete server"),
                "error": "DELETE_SERVER_ERROR",
            }

    async def test_connection(self, server_id: str) -> dict[str, Any]:
        """Test SSH connection to a server."""
        try:
            server = await self.server_service.get_server(server_id)
            if not server:
                return {
                    "success": False,
                    "message": "Server not found",
                    "error": "SERVER_NOT_FOUND",
                }

            credentials = await self.server_service.get_credentials(server_id)
            if not credentials:
                return {
                    "success": False,
                    "message": "Credentials not found",
                    "error": "CREDENTIALS_NOT_FOUND",
                }

            success, message, system_info = await self.ssh_service.test_connection(
                host=server.host,
                port=server.port,
                username=server.username,
                auth_type=server.auth_type.value,
                credentials=credentials,
            )

            if success:
                await self.server_service.update_server_status(
                    server_id, ServerStatus.CONNECTED
                )
                if system_info:
                    await self.server_service.update_server_system_info(
                        server_id, system_info
                    )
                docker_version = (
                    system_info.get("docker_version", "Not installed")
                    if system_info
                    else "Not installed"
                )
                docker_installed = docker_version != "Not installed"
                agent_status = (
                    system_info.get("agent_status", "not running")
                    if system_info
                    else "not running"
                )
                agent_installed = agent_status == "running"

                # Sync agent DB status with actual container state
                agent = await self.agent_service.get_agent_by_server(server_id)
                if agent:
                    from models.agent import AgentStatus as AgentStatusEnum
                    from models.agent import AgentUpdate

                    if (
                        agent_status == "running"
                        and agent.status == AgentStatusEnum.DISCONNECTED
                    ):
                        # Container running but DB says disconnected - agent will reconnect via WebSocket
                        logger.info(
                            "Agent container running, awaiting WebSocket reconnection",
                            agent_id=agent.id,
                            server_id=server_id,
                        )
                    elif (
                        agent_status != "running"
                        and agent.status != AgentStatusEnum.DISCONNECTED
                    ):
                        # Container not running but DB says connected/pending - update to disconnected
                        logger.info(
                            "Agent container not running, updating status to DISCONNECTED",
                            agent_id=agent.id,
                            server_id=server_id,
                        )
                        agent_db = self.agent_service._get_agent_db()
                        await agent_db.update_agent(
                            agent.id, AgentUpdate(status=AgentStatusEnum.DISCONNECTED)
                        )

                await log_event(
                    "server",
                    "INFO",
                    f"Connection test successful: {server.name}",
                    SERVER_TAGS,
                    {
                        "server_id": server_id,
                        "host": server.host,
                        "docker_installed": docker_installed,
                        "agent_installed": agent_installed,
                    },
                )
                return {
                    "success": True,
                    "docker_installed": docker_installed,
                    "agent_installed": agent_installed,
                    "system_info": system_info,
                    "message": "Connection successful",
                }
            else:
                await self.server_service.update_server_status(
                    server_id, ServerStatus.ERROR
                )
                await log_event(
                    "server",
                    "WARNING",
                    f"Connection test failed: {server.name}",
                    SERVER_TAGS,
                    {"server_id": server_id, "host": server.host, "error": message},
                )
                return {
                    "success": False,
                    "message": message,
                    "error": "CONNECTION_FAILED",
                }
        except Exception as e:
            logger.error("Test connection error", error=str(e))
            await log_event(
                "server",
                "ERROR",
                f"Connection test error: {server_id}",
                SERVER_TAGS,
                {"error": str(e)},
            )
            return {
                "success": False,
                "message": f"Connection test failed: {str(e)}",
                "error": "CONNECTION_TEST_ERROR",
            }

    async def execute_command(
        self,
        server_id: str,
        command: str,
        timeout: int = 120,
        force_ssh: bool = False,
        force_agent: bool = False,
    ) -> dict[str, Any]:
        """Execute a command on a server using agent or SSH.

        Routes the command through the agent if connected, otherwise
        falls back to SSH. Can force a specific method.

        Args:
            server_id: Target server identifier.
            command: Shell command to execute.
            timeout: Execution timeout in seconds.
            force_ssh: Force SSH execution even if agent available.
            force_agent: Force agent execution, fail if not connected.

        Returns:
            Dict containing execution result with method used.
        """
        try:
            # Validate command for dangerous patterns
            cmd_validation = validate_command(command)
            if not cmd_validation["valid"]:
                return {
                    "success": False,
                    "message": cmd_validation["error"],
                    "error": "DANGEROUS_COMMAND",
                }

            # Use command router if available
            if self.command_router:
                result = await self.command_router.execute(
                    server_id=server_id,
                    command=command,
                    timeout=float(timeout),
                    force_ssh=force_ssh,
                    force_agent=force_agent,
                )

                return {
                    "success": result.success,
                    "data": {
                        "output": result.output,
                        "method": result.method.value,
                        "exit_code": result.exit_code,
                        "execution_time_ms": result.execution_time_ms,
                    },
                    "message": "Command executed" if result.success else result.error,
                    "error": None if result.success else "COMMAND_FAILED",
                }

            # Fallback to direct SSH if no router
            return await self._execute_via_ssh(server_id, command, timeout)

        except Exception as e:
            logger.error("Execute command error", server_id=server_id, error=str(e))
            await log_event(
                "server",
                "ERROR",
                f"Command execution failed: {server_id}",
                SERVER_TAGS,
                {"command": command[:50], "error": str(e)},
            )
            return {
                "success": False,
                "message": f"Command execution failed: {str(e)}",
                "error": "EXECUTE_COMMAND_ERROR",
            }

    async def get_execution_methods(self, server_id: str) -> dict[str, Any]:
        """Get available command execution methods for a server.

        Returns which methods (agent, SSH) are available for executing
        commands on the specified server.

        Args:
            server_id: Server identifier to check.

        Returns:
            Dict containing list of available methods.
        """
        try:
            methods = []
            agent_available = False

            # Check if command router is available
            if self.command_router:
                available = await self.command_router.get_available_methods(server_id)
                methods = [m.value for m in available]
                agent_available = await self.command_router.is_agent_available(
                    server_id
                )
            else:
                # Only SSH available without router
                server = await self.server_service.get_server(server_id)
                if server:
                    methods = ["ssh"]

            return {
                "success": True,
                "data": {
                    "server_id": server_id,
                    "methods": methods,
                    "agent_available": agent_available,
                    "preferred_method": methods[0] if methods else None,
                },
                "message": f"{len(methods)} method(s) available",
            }

        except Exception as e:
            logger.error(
                "Get execution methods error", server_id=server_id, error=str(e)
            )
            return {
                "success": False,
                "message": f"Failed to get execution methods: {str(e)}",
                "error": "GET_METHODS_ERROR",
            }

    async def update_server_status(self, server_id: str, status: str) -> dict[str, Any]:
        """Update server connection status.

        Args:
            server_id: Server identifier.
            status: New status (connected, disconnected, error, preparing).

        Returns:
            Dict containing success status.
        """
        try:
            # Validate status
            try:
                server_status = ServerStatus(status)
            except ValueError:
                return {
                    "success": False,
                    "message": f"Invalid status: {status}",
                    "error": "INVALID_STATUS",
                }

            success = await self.server_service.update_server_status(
                server_id, server_status
            )

            if not success:
                return {
                    "success": False,
                    "message": "Server not found",
                    "error": "SERVER_NOT_FOUND",
                }

            await log_event(
                "server",
                "INFO",
                f"Server status updated: {server_id} -> {status}",
                SERVER_TAGS,
                {"server_id": server_id, "status": status},
            )
            return {"success": True, "message": f"Server status updated to {status}"}
        except Exception as e:
            logger.error("Update server status error", error=str(e))
            return {
                "success": False,
                "message": f"Failed to update server status: {str(e)}",
                "error": "UPDATE_STATUS_ERROR",
            }

    async def _execute_via_ssh(
        self, server_id: str, command: str, timeout: int
    ) -> dict[str, Any]:
        """Execute command via direct SSH (fallback when no router)."""
        server = await self.server_service.get_server(server_id)
        if not server:
            return {
                "success": False,
                "message": "Server not found",
                "error": "SERVER_NOT_FOUND",
            }

        credentials = await self.server_service.get_credentials(server_id)
        if not credentials:
            return {
                "success": False,
                "message": "Credentials not found",
                "error": "CREDENTIALS_NOT_FOUND",
            }

        success, output = await self.ssh_service.execute_command(
            host=server.host,
            port=server.port,
            username=server.username,
            auth_type=server.auth_type.value,
            credentials=credentials,
            command=command,
            timeout=timeout,
        )

        return {
            "success": success,
            "data": {
                "output": output,
                "method": "ssh",
                "exit_code": 0 if success else 1,
            },
            "message": "Command executed" if success else "Command failed",
            "error": None if success else "COMMAND_FAILED",
        }
