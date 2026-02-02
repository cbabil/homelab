"""
Agent Management Tools

Provides agent installation, status, lifecycle, and command capabilities
for the MCP server.
"""

import os
import re
import shlex
from datetime import UTC, datetime
from typing import Any, Dict, Optional

import structlog

from models.agent import AgentInfo, AgentStatus
from services.agent_manager import AgentManager
from services.agent_lifecycle import AgentLifecycleManager
from services.agent_service import AgentService
from services.agent_packager import AgentPackager
from services.ssh_service import SSHService
from services.server_service import ServerService
from tools.common import log_event

logger = structlog.get_logger("agent_tools")

AGENT_TAGS = ["agent", "infrastructure"]

AGENT_CONTAINER_NAME = "tomo-agent"
AGENT_IMAGE_NAME = "tomo-agent:latest"


class AgentTools:
    """Agent management tools for the MCP server."""

    def __init__(
        self,
        agent_service: AgentService,
        agent_manager: AgentManager,
        ssh_service: SSHService,
        server_service: ServerService,
        agent_packager: Optional[AgentPackager] = None,
        agent_lifecycle: Optional[AgentLifecycleManager] = None,
    ):
        """Initialize agent tools.

        Args:
            agent_service: Service for agent lifecycle operations.
            agent_manager: Manager for active agent connections.
            ssh_service: Service for SSH command execution.
            server_service: Service for server management.
            agent_packager: Packager for agent source code deployment.
            agent_lifecycle: Optional lifecycle manager for health tracking.
        """
        self.agent_service = agent_service
        self.agent_manager = agent_manager
        self.ssh_service = ssh_service
        self.server_service = server_service
        self.agent_packager = agent_packager or AgentPackager()
        self.lifecycle = agent_lifecycle
        logger.info("Agent tools initialized")

    def _get_server_url(self) -> str:
        """Get the server URL from environment or default.

        Returns:
            Server URL for agent connections.
        """
        return os.getenv("SERVER_URL", "http://localhost:8000")

    def _validate_registration_code(self, code: str) -> bool:
        """Validate registration code format for security.

        Args:
            code: Registration code to validate.

        Returns:
            True if code is valid and safe, False otherwise.
        """
        # Registration codes are base64url-safe tokens from secrets.token_urlsafe
        # They should only contain alphanumeric chars, hyphens, and underscores
        if not code or len(code) > 100:
            return False
        return bool(re.match(r"^[A-Za-z0-9_-]+$", code))

    def _validate_server_url(self, url: str) -> bool:
        """Validate server URL format for security.

        Args:
            url: Server URL to validate.

        Returns:
            True if URL is valid and safe, False otherwise.
        """
        if not url or len(url) > 500:
            return False
        # Allow http/https/ws/wss URLs with standard characters
        # Block shell metacharacters that could be used for injection
        dangerous_chars = [';', '|', '`', '$', '(', ')', '<', '>', '\\', '\n', '\r', "'", '"']
        if any(char in url for char in dangerous_chars):
            return False
        # Must start with http(s) or ws(s)
        return bool(re.match(r"^(https?|wss?)://", url))

    def _build_deploy_script(self, code: str, server_url: str) -> str:
        """Build deployment script for agent installation.

        Creates a bash script that transfers agent code, builds the image,
        and starts the container on the target server.

        Args:
            code: Registration code for agent authentication.
            server_url: Backend server URL for agent connection.

        Returns:
            Bash script string for deployment.

        Raises:
            ValueError: If code or server_url contain invalid characters.
        """
        # Validate inputs to prevent command injection
        if not self._validate_registration_code(code):
            logger.error("Invalid registration code format", code_preview=code[:10] if code else "empty")
            raise ValueError("Invalid registration code format")
        if not self._validate_server_url(server_url):
            logger.error("Invalid server URL format", url=server_url)
            raise ValueError(f"Invalid server URL format: {server_url}")

        # Package agent code as base64 tarball
        agent_package = self.agent_packager.package()
        agent_version = self.agent_packager.get_version()

        # Use shlex.quote for additional safety even though we validated
        safe_code = shlex.quote(code)
        safe_url = shlex.quote(server_url)

        return f"""set -e
echo "Installing Tomo Agent v{agent_version}..."

# Stop and remove existing agent container if present
docker stop {AGENT_CONTAINER_NAME} 2>/dev/null || true
docker rm {AGENT_CONTAINER_NAME} 2>/dev/null || true

# Create build directory
BUILD_DIR=$(mktemp -d)
cd "$BUILD_DIR"

# Extract agent source code
echo "{agent_package}" | base64 -d | tar xzf -

# Build agent image
echo "Building agent image..."
docker build -t {AGENT_IMAGE_NAME} .

# Clean up build directory
cd /
rm -rf "$BUILD_DIR"

# Create data directories with correct ownership (UID 1000 is common for apps)
mkdir -p /DATA/AppData 2>/dev/null || true
chown -R 1000:1000 /DATA/AppData 2>/dev/null || true
mkdir -p /opt/tomo/data 2>/dev/null || true
chown -R 1000:1000 /opt/tomo/data 2>/dev/null || true

# Start agent container
# Security: Mount root read-only, only specific data paths are writable
echo "Starting agent container..."
docker run -d \\
    --name {AGENT_CONTAINER_NAME} \\
    --restart unless-stopped \\
    -v /var/run/docker.sock:/var/run/docker.sock \\
    -v /:/host:ro \\
    -v /DATA:/host/DATA \\
    -v /opt/tomo:/host/opt/tomo \\
    -v {AGENT_CONTAINER_NAME}-data:/data \\
    -e REGISTER_CODE={safe_code} \\
    -e SERVER_URL={safe_url} \\
    {AGENT_IMAGE_NAME}

# Verify container is running
sleep 2
docker ps --filter name={AGENT_CONTAINER_NAME} --format '{{{{.Status}}}}'
echo "Agent installation complete!"
"""

    async def install_agent(self, server_id: str) -> Dict[str, Any]:
        """Install an agent on a server via SSH.

        Creates a new agent record, generates a registration code, and
        deploys the agent container on the target server via SSH.

        Args:
            server_id: Server identifier to install agent on.

        Returns:
            Dict containing agent_id, server_id, and installation status.
        """
        server_name = None  # Track for error logging
        try:
            # Get server details for SSH connection
            server = await self.server_service.get_server(server_id)
            if server:
                server_name = server.name
            if not server:
                await log_event(
                    "agent",
                    "ERROR",
                    "Agent install failed: server not found",
                    AGENT_TAGS,
                    {"server_id": server_id, "error": "SERVER_NOT_FOUND"},
                )
                return {
                    "success": False,
                    "message": f"Server '{server_id}' not found",
                    "error": "SERVER_NOT_FOUND",
                }

            # Check Docker is installed
            docker_version = (
                server.system_info.docker_version if server.system_info else None
            )
            if not docker_version or docker_version.lower() == "not installed":
                await log_event(
                    "agent",
                    "ERROR",
                    f"Agent install failed: Docker not installed on server '{server.name}'",
                    AGENT_TAGS,
                    {"server_id": server_id, "server_name": server.name, "error": "DOCKER_NOT_INSTALLED"},
                )
                return {
                    "success": False,
                    "message": "Docker is required but not installed on this server",
                    "error": "DOCKER_NOT_INSTALLED",
                }

            # Get credentials for SSH connection (check before creating agent)
            credentials = await self.server_service.get_credentials(server_id)
            if not credentials:
                await log_event(
                    "agent",
                    "ERROR",
                    f"Agent install failed: credentials not found for server '{server.name}'",
                    AGENT_TAGS,
                    {"server_id": server_id, "server_name": server.name, "error": "CREDENTIALS_NOT_FOUND"},
                )
                return {
                    "success": False,
                    "message": "Server credentials not found",
                    "error": "CREDENTIALS_NOT_FOUND",
                }

            # Create agent record and registration code
            agent, registration_code = await self.agent_service.create_agent(server_id)
            server_url = self._get_server_url()
            agent_version = self.agent_packager.get_version()

            logger.info(
                "Deploying agent via SSH",
                agent_id=agent.id,
                server_id=server_id,
                host=server.host,
                version=agent_version,
            )

            # Build script to deploy agent from source
            deploy_script = self._build_deploy_script(
                registration_code.code,
                server_url,
            )

            # Execute deployment via SSH
            success, output = await self.ssh_service.execute_command(
                host=server.host,
                port=server.port,
                username=server.username,
                auth_type=server.auth_type.value,
                credentials=credentials,
                command=deploy_script,
                timeout=120,
            )

            if not success:
                logger.error(
                    "Agent deployment failed",
                    agent_id=agent.id,
                    server_id=server_id,
                    output=output,
                )
                await log_event(
                    "agent",
                    "ERROR",
                    f"Agent deployment failed via SSH on server '{server.name}'",
                    AGENT_TAGS,
                    {
                        "agent_id": agent.id,
                        "server_id": server_id,
                        "server_name": server.name,
                        "version": agent_version,
                        "error": output,
                    },
                )
                return {
                    "success": False,
                    "message": f"Failed to deploy agent container: {output}",
                    "error": "DEPLOY_FAILED",
                }

            logger.info(
                "Agent deployed successfully",
                agent_id=agent.id,
                server_id=server_id,
            )

            await log_event(
                "agent",
                "INFO",
                f"Agent installed on server: {server.name}",
                AGENT_TAGS,
                {
                    "agent_id": agent.id,
                    "server_id": server_id,
                    "server_name": server.name,
                    "version": agent_version,
                },
            )

            # Update system_info to reflect agent is now running
            if server.system_info:
                updated_info = server.system_info.model_dump()
                updated_info["agent_status"] = "running"
                updated_info["agent_version"] = agent_version
                await self.server_service.update_server_system_info(server_id, updated_info)

            return {
                "success": True,
                "data": {
                    "agent_id": agent.id,
                    "server_id": server_id,
                    "version": agent_version,
                },
                "message": f"Agent v{agent_version} deployed on server '{server_id}'",
            }

        except Exception as e:
            logger.error(
                "Install agent error",
                server_id=server_id,
                server_name=server_name,
                error=str(e),
            )
            server_display = f"'{server_name}'" if server_name else server_id
            await log_event(
                "agent",
                "ERROR",
                f"Agent install failed on server {server_display}: unexpected error",
                AGENT_TAGS,
                {"server_id": server_id, "server_name": server_name, "error": str(e)},
            )
            return {
                "success": False,
                "message": f"Failed to install agent: {str(e)}",
                "error": "INSTALL_AGENT_ERROR",
            }

    async def get_agent_status(self, server_id: str) -> Dict[str, Any]:
        """Get agent status for a server.

        Returns agent information including connection status, version,
        and last seen timestamp.

        Args:
            server_id: Server identifier to check agent status for.

        Returns:
            Dict containing agent info or None if no agent exists.
        """
        try:
            agent = await self.agent_service.get_agent_by_server(server_id)

            if not agent:
                return {
                    "success": True,
                    "data": None,
                    "message": "No agent found for server",
                }

            # Check if agent is currently connected via WebSocket
            is_connected = self.agent_manager.is_connected(agent.id)

            agent_info = AgentInfo(
                id=agent.id,
                server_id=agent.server_id,
                status=agent.status,
                version=agent.version,
                last_seen=agent.last_seen,
                registered_at=agent.registered_at,
            )

            return {
                "success": True,
                "data": {
                    **agent_info.model_dump(),
                    "is_connected": is_connected,
                },
                "message": "Agent status retrieved",
            }

        except Exception as e:
            logger.error(
                "Get agent status error",
                server_id=server_id,
                error=str(e),
            )
            return {
                "success": False,
                "message": f"Failed to get agent status: {str(e)}",
                "error": "GET_AGENT_STATUS_ERROR",
            }

    async def revoke_agent_token(self, server_id: str) -> Dict[str, Any]:
        """Revoke an agent's authentication token.

        Disconnects the agent WebSocket connection and invalidates
        its authentication token. The agent container remains running
        on the server but can no longer authenticate.

        Args:
            server_id: Server identifier to revoke agent token for.

        Returns:
            Dict containing success status of the token revocation.
        """
        try:
            agent = await self.agent_service.get_agent_by_server(server_id)

            if not agent:
                return {
                    "success": False,
                    "message": "No agent found for server",
                    "error": "AGENT_NOT_FOUND",
                }

            # Disconnect WebSocket if connected
            if self.agent_manager.is_connected(agent.id):
                await self.agent_manager.unregister_connection(agent.id)

            # Revoke agent token
            success = await self.agent_service.revoke_agent_token(agent.id)

            if not success:
                return {
                    "success": False,
                    "message": "Failed to revoke agent token",
                    "error": "REVOKE_TOKEN_ERROR",
                }

            await log_event(
                "agent",
                "INFO",
                f"Agent token revoked for server: {server_id}",
                AGENT_TAGS,
                {"agent_id": agent.id, "server_id": server_id},
            )

            logger.info(
                "Agent token revoked",
                agent_id=agent.id,
                server_id=server_id,
            )

            return {
                "success": True,
                "data": {"agent_id": agent.id},
                "message": "Agent token revoked successfully",
            }

        except Exception as e:
            logger.error(
                "Revoke agent error",
                server_id=server_id,
                error=str(e),
            )
            await log_event(
                "agent",
                "ERROR",
                f"Failed to revoke agent for server: {server_id}",
                AGENT_TAGS,
                {"error": str(e)},
            )
            return {
                "success": False,
                "message": f"Failed to revoke agent token: {str(e)}",
                "error": "REVOKE_TOKEN_ERROR",
            }

    async def uninstall_agent(self, server_id: str) -> Dict[str, Any]:
        """Uninstall agent from a server.

        Stops and removes the agent container via SSH, then removes
        the agent record from the database. Works even if no DB record
        exists (cleans up orphaned containers).

        Args:
            server_id: Server identifier to uninstall agent from.

        Returns:
            Dict containing success status of the uninstallation.
        """
        server_name = None  # Track for error logging
        try:
            # Get agent record if exists (may be None for orphaned containers)
            agent = await self.agent_service.get_agent_by_server(server_id)

            # Disconnect WebSocket if connected
            if agent and self.agent_manager.is_connected(agent.id):
                await self.agent_manager.unregister_connection(agent.id)

            # Get server and credentials for SSH
            server = await self.server_service.get_server(server_id)
            if server:
                server_name = server.name
            if not server:
                await log_event(
                    "agent",
                    "ERROR",
                    "Agent uninstall failed: server not found",
                    AGENT_TAGS,
                    {"server_id": server_id, "agent_id": agent.id if agent else None, "error": "SERVER_NOT_FOUND"},
                )
                return {
                    "success": False,
                    "message": "Server not found",
                    "error": "SERVER_NOT_FOUND",
                }

            credentials = await self.server_service.get_credentials(server_id)
            if not credentials:
                await log_event(
                    "agent",
                    "ERROR",
                    f"Agent uninstall failed: credentials not found for '{server.name}'",
                    AGENT_TAGS,
                    {"server_id": server_id, "server_name": server.name, "agent_id": agent.id if agent else None, "error": "CREDENTIALS_NOT_FOUND"},
                )
                return {
                    "success": False,
                    "message": "Server credentials not found",
                    "error": "CREDENTIALS_NOT_FOUND",
                }

            # Build uninstall script
            uninstall_script = f"""
docker stop {AGENT_CONTAINER_NAME} 2>/dev/null || true
docker rm {AGENT_CONTAINER_NAME} 2>/dev/null || true
docker volume rm {AGENT_CONTAINER_NAME}-data 2>/dev/null || true
echo "Agent uninstalled"
"""

            # Execute uninstall via SSH
            success, output = await self.ssh_service.execute_command(
                host=server.host,
                port=server.port,
                username=server.username,
                auth_type=server.auth_type.value,
                credentials=credentials,
                command=uninstall_script,
                timeout=30,
            )

            if not success:
                logger.warning(
                    "Agent uninstall SSH command failed",
                    agent_id=agent.id if agent else None,
                    server_id=server_id,
                    output=output,
                )
                # Continue anyway - container may not exist

            # Delete agent from database if record exists
            agent_id = agent.id if agent else None
            if agent:
                deleted = await self.agent_service.delete_agent(agent.id)
                if not deleted:
                    logger.warning(
                        "Failed to delete agent record",
                        agent_id=agent.id,
                        server_id=server_id,
                    )

            # Update server system_info to reflect agent is no longer running
            if server.system_info:
                updated_info = dict(server.system_info) if hasattr(server.system_info, '__iter__') else {}
                if hasattr(server.system_info, 'model_dump'):
                    updated_info = server.system_info.model_dump()
                updated_info["agent_status"] = "not running"
                updated_info["agent_version"] = ""
                await self.server_service.update_server_system_info(server_id, updated_info)

            await log_event(
                "agent",
                "INFO",
                f"Agent uninstalled from server: {server.name}",
                AGENT_TAGS,
                {"agent_id": agent_id, "server_id": server_id, "server_name": server.name},
            )

            logger.info(
                "Agent uninstalled",
                agent_id=agent_id,
                server_id=server_id,
            )

            return {
                "success": True,
                "data": {"agent_id": agent_id, "server_id": server_id},
                "message": "Agent uninstalled successfully",
            }

        except Exception as e:
            logger.error(
                "Uninstall agent error",
                server_id=server_id,
                server_name=server_name,
                error=str(e),
            )
            server_display = f"'{server_name}'" if server_name else server_id
            await log_event(
                "agent",
                "ERROR",
                f"Failed to uninstall agent from server {server_display}",
                AGENT_TAGS,
                {"server_id": server_id, "server_name": server_name, "error": str(e)},
            )
            return {
                "success": False,
                "message": f"Failed to uninstall agent: {str(e)}",
                "error": "UNINSTALL_AGENT_ERROR",
            }

    async def send_agent_command(
        self,
        server_id: str,
        method: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Send a command to an agent via WebSocket.

        Sends a JSON-RPC command to the agent and waits for response.

        Args:
            server_id: Server identifier whose agent should receive command.
            method: JSON-RPC method name to invoke.
            params: Optional parameters for the method.

        Returns:
            Dict containing the command result or error.
        """
        try:
            # Get agent for this server
            agent = await self.agent_service.get_agent_by_server(server_id)

            if not agent:
                return {
                    "success": False,
                    "message": "No agent found for server",
                    "error": "AGENT_NOT_FOUND",
                }

            # Check if agent is connected
            if not self.agent_manager.is_connected(agent.id):
                return {
                    "success": False,
                    "message": "Agent is not connected",
                    "error": "AGENT_NOT_CONNECTED",
                }

            # Send command and wait for response
            result = await self.agent_manager.send_command(
                agent_id=agent.id,
                method=method,
                params=params,
            )

            logger.debug(
                "Agent command executed",
                server_id=server_id,
                method=method,
            )

            return {
                "success": True,
                "data": result,
                "message": f"Command '{method}' executed successfully",
            }

        except TimeoutError as e:
            logger.error(
                "Agent command timeout",
                server_id=server_id,
                method=method,
                error=str(e),
            )
            return {
                "success": False,
                "message": f"Command timed out: {str(e)}",
                "error": "COMMAND_TIMEOUT",
            }

        except RuntimeError as e:
            # Agent returned an error response
            logger.error(
                "Agent command error",
                server_id=server_id,
                method=method,
                error=str(e),
            )
            return {
                "success": False,
                "message": f"Agent error: {str(e)}",
                "error": "AGENT_COMMAND_ERROR",
            }

        except Exception as e:
            logger.error(
                "Send agent command error",
                server_id=server_id,
                method=method,
                error=str(e),
            )
            return {
                "success": False,
                "message": f"Failed to send command: {str(e)}",
                "error": "SEND_COMMAND_ERROR",
            }

    async def check_agent_health(self, server_id: str) -> Dict[str, Any]:
        """Check comprehensive health status of an agent.

        Returns health status including connectivity, staleness, and version.

        Args:
            server_id: Server identifier to check agent health for.

        Returns:
            Dict containing agent health information.
        """
        try:
            agent = await self.agent_service.get_agent_by_server(server_id)

            if not agent:
                return {
                    "success": False,
                    "message": "No agent found for server",
                    "error": "AGENT_NOT_FOUND",
                }

            is_connected = self.agent_manager.is_connected(agent.id)
            is_stale = (
                self.lifecycle.is_agent_stale(agent.id)
                if self.lifecycle and is_connected
                else True
            )

            # Determine health status
            if not is_connected:
                health_status = "offline"
            elif is_stale:
                health_status = "degraded"
            else:
                health_status = "healthy"

            health_data = {
                "agent_id": agent.id,
                "server_id": server_id,
                "status": agent.status.value,
                "health": health_status,
                "is_connected": is_connected,
                "is_stale": is_stale,
                "version": agent.version,
                "last_seen": agent.last_seen.isoformat() if agent.last_seen else None,
                "registered_at": (
                    agent.registered_at.isoformat() if agent.registered_at else None
                ),
            }

            return {
                "success": True,
                "data": health_data,
                "message": f"Agent health: {health_status}",
            }

        except Exception as e:
            logger.error("Check agent health error", server_id=server_id, error=str(e))
            return {
                "success": False,
                "message": f"Failed to check agent health: {str(e)}",
                "error": "CHECK_HEALTH_ERROR",
            }

    async def ping_agent(self, server_id: str, timeout: float = 5.0) -> Dict[str, Any]:
        """Ping an agent to verify connectivity.

        Sends a ping request and measures response latency.

        Args:
            server_id: Server identifier of agent to ping.
            timeout: Response timeout in seconds.

        Returns:
            Dict containing ping result and latency.
        """
        try:
            agent = await self.agent_service.get_agent_by_server(server_id)

            if not agent:
                return {
                    "success": False,
                    "message": "No agent found for server",
                    "error": "AGENT_NOT_FOUND",
                }

            if not self.agent_manager.is_connected(agent.id):
                return {
                    "success": False,
                    "message": "Agent is not connected",
                    "error": "AGENT_NOT_CONNECTED",
                }

            start_time = datetime.now(UTC)
            is_responsive = await self.agent_manager.ping_agent(agent.id, timeout)
            latency_ms = (datetime.now(UTC) - start_time).total_seconds() * 1000

            return {
                "success": is_responsive,
                "data": {
                    "agent_id": agent.id,
                    "responsive": is_responsive,
                    "latency_ms": round(latency_ms, 2) if is_responsive else None,
                },
                "message": "Pong!" if is_responsive else "Agent did not respond",
            }

        except Exception as e:
            logger.error("Ping agent error", server_id=server_id, error=str(e))
            return {
                "success": False,
                "message": f"Failed to ping agent: {str(e)}",
                "error": "PING_ERROR",
            }

    async def check_agent_version(self, server_id: str) -> Dict[str, Any]:
        """Check if an agent needs updating.

        Compares current agent version against latest available version.

        Args:
            server_id: Server identifier to check agent version for.

        Returns:
            Dict containing version comparison information.
        """
        try:
            if not self.lifecycle:
                return {
                    "success": False,
                    "message": "Lifecycle manager not available",
                    "error": "LIFECYCLE_UNAVAILABLE",
                }

            agent = await self.agent_service.get_agent_by_server(server_id)

            if not agent:
                return {
                    "success": False,
                    "message": "No agent found for server",
                    "error": "AGENT_NOT_FOUND",
                }

            if not agent.version:
                return {
                    "success": False,
                    "message": "Agent version unknown",
                    "error": "VERSION_UNKNOWN",
                }

            version_info = self.lifecycle.check_version(agent.version)

            return {
                "success": True,
                "data": version_info.model_dump(),
                "message": (
                    "Update available"
                    if version_info.update_available
                    else "Agent is up to date"
                ),
            }

        except Exception as e:
            logger.error("Check version error", server_id=server_id, error=str(e))
            return {
                "success": False,
                "message": f"Failed to check agent version: {str(e)}",
                "error": "CHECK_VERSION_ERROR",
            }

    async def trigger_agent_update(self, server_id: str) -> Dict[str, Any]:
        """Trigger an agent update.

        Marks the agent for update and sends update command if connected.

        Args:
            server_id: Server identifier of agent to update.

        Returns:
            Dict containing update trigger result.
        """
        try:
            if not self.lifecycle:
                return {
                    "success": False,
                    "message": "Lifecycle manager not available",
                    "error": "LIFECYCLE_UNAVAILABLE",
                }

            agent = await self.agent_service.get_agent_by_server(server_id)

            if not agent:
                return {
                    "success": False,
                    "message": "No agent found for server",
                    "error": "AGENT_NOT_FOUND",
                }

            if not self.agent_manager.is_connected(agent.id):
                return {
                    "success": False,
                    "message": "Agent must be connected to trigger update",
                    "error": "AGENT_NOT_CONNECTED",
                }

            # Check if update is needed
            if agent.version:
                version_info = self.lifecycle.check_version(agent.version)
                if not version_info.update_available:
                    return {
                        "success": False,
                        "message": "Agent is already at latest version",
                        "error": "ALREADY_LATEST",
                    }

            # Mark agent for update
            success = await self.lifecycle.trigger_update(agent.id)
            if not success:
                return {
                    "success": False,
                    "message": "Failed to mark agent for update",
                    "error": "UPDATE_TRIGGER_FAILED",
                }

            # Send update command to agent
            try:
                latest = self.lifecycle.check_version(agent.version or "0.0.0")
                await self.agent_manager.send_command(
                    agent.id,
                    "agent.update",
                    {"version": latest.latest_version},
                    timeout=30.0,
                )
            except Exception as e:
                logger.warning("Update command failed", agent_id=agent.id, error=str(e))
                # Agent will still update on next restart due to UPDATING status

            await log_event(
                "agent",
                "INFO",
                f"Update triggered for agent on server: {server_id}",
                AGENT_TAGS,
                {"agent_id": agent.id, "server_id": server_id},
            )

            return {
                "success": True,
                "data": {"agent_id": agent.id, "status": AgentStatus.UPDATING.value},
                "message": "Update triggered successfully",
            }

        except Exception as e:
            logger.error("Trigger update error", server_id=server_id, error=str(e))
            return {
                "success": False,
                "message": f"Failed to trigger agent update: {str(e)}",
                "error": "TRIGGER_UPDATE_ERROR",
            }

    async def list_stale_agents(self) -> Dict[str, Any]:
        """List all agents that have missed heartbeats.

        Returns list of agents that haven't responded within the
        configured heartbeat timeout.

        Returns:
            Dict containing list of stale agents.
        """
        try:
            if not self.lifecycle:
                return {
                    "success": False,
                    "message": "Lifecycle manager not available",
                    "error": "LIFECYCLE_UNAVAILABLE",
                }

            stale_agent_ids = await self.lifecycle.get_stale_agents()

            stale_agents = []
            for agent_id in stale_agent_ids:
                info = self.agent_manager.get_connection_info(agent_id)
                if info:
                    stale_agents.append(info)

            return {
                "success": True,
                "data": {
                    "stale_count": len(stale_agents),
                    "agents": stale_agents,
                },
                "message": f"Found {len(stale_agents)} stale agent(s)",
            }

        except Exception as e:
            logger.error("List stale agents error", error=str(e))
            return {
                "success": False,
                "message": f"Failed to list stale agents: {str(e)}",
                "error": "LIST_STALE_ERROR",
            }

    async def list_agents(self) -> Dict[str, Any]:
        """List all registered agents.

        Returns all agents in the system with their current status.

        Returns:
            Dict containing list of agents with id, server_id, status, version,
            last_seen, and registered_at.
        """
        try:
            agents = await self.agent_service.list_all_agents()

            return {
                "success": True,
                "data": {
                    "agents": [
                        {
                            "id": a.id,
                            "server_id": a.server_id,
                            "status": a.status.value,
                            "version": a.version,
                            "last_seen": (
                                a.last_seen.isoformat() if a.last_seen else None
                            ),
                            "registered_at": (
                                a.registered_at.isoformat() if a.registered_at else None
                            ),
                        }
                        for a in agents
                    ],
                    "count": len(agents),
                },
                "message": f"Found {len(agents)} agent(s)",
            }

        except Exception as e:
            logger.error("List agents error", error=str(e))
            return {
                "success": False,
                "message": f"Failed to list agents: {str(e)}",
                "error": "LIST_AGENTS_ERROR",
            }

    async def rotate_agent_token(self, server_id: str) -> Dict[str, Any]:
        """Rotate an agent's authentication token.

        Generates a new token for the agent and sends it via WebSocket.
        The agent will save the new token and use it for future auth.
        Both old and new tokens are valid during the grace period.

        Args:
            server_id: Server identifier to rotate agent token for.

        Returns:
            Dict containing success status and rotation details.
        """
        try:
            agent = await self.agent_service.get_agent_by_server(server_id)

            if not agent:
                return {
                    "success": False,
                    "message": "No agent found for server",
                    "error": "AGENT_NOT_FOUND",
                }

            # Agent must be connected to receive the new token
            if not self.agent_manager.is_connected(agent.id):
                return {
                    "success": False,
                    "message": "Agent must be connected to rotate token",
                    "error": "AGENT_NOT_CONNECTED",
                }

            # Initiate rotation - generates pending token
            new_token = await self.agent_service.initiate_rotation(agent.id)
            if not new_token:
                return {
                    "success": False,
                    "message": "Failed to initiate token rotation",
                    "error": "ROTATION_INIT_FAILED",
                }

            # Get grace period from settings
            _, grace_minutes = await self.agent_service._get_token_rotation_settings()
            grace_seconds = grace_minutes * 60

            # Send new token to agent via WebSocket
            try:
                await self.agent_manager.send_command(
                    agent.id,
                    "agent.rotate_token",
                    {
                        "new_token": new_token,
                        "grace_period_seconds": grace_seconds,
                    },
                    timeout=30.0,
                )
            except Exception as e:
                # Cancel rotation if we can't reach the agent
                await self.agent_service.cancel_rotation(agent.id)
                logger.error(
                    "Failed to send rotation command",
                    agent_id=agent.id,
                    error=str(e),
                )
                return {
                    "success": False,
                    "message": f"Failed to send rotation to agent: {str(e)}",
                    "error": "ROTATION_SEND_FAILED",
                }

            await log_event(
                "agent",
                "INFO",
                f"Token rotation initiated for agent on server: {server_id}",
                AGENT_TAGS,
                {
                    "agent_id": agent.id,
                    "server_id": server_id,
                    "grace_period_seconds": grace_seconds,
                },
            )

            logger.info(
                "Token rotation initiated",
                agent_id=agent.id,
                server_id=server_id,
            )

            return {
                "success": True,
                "data": {
                    "agent_id": agent.id,
                    "server_id": server_id,
                    "grace_period_seconds": grace_seconds,
                },
                "message": "Token rotation initiated successfully",
            }

        except Exception as e:
            logger.error(
                "Rotate agent token error",
                server_id=server_id,
                error=str(e),
            )
            await log_event(
                "agent",
                "ERROR",
                f"Failed to rotate agent token for server: {server_id}",
                AGENT_TAGS,
                {"error": str(e)},
            )
            return {
                "success": False,
                "message": f"Failed to rotate agent token: {str(e)}",
                "error": "ROTATE_TOKEN_ERROR",
            }

    async def reset_agent_status(self, server_id: Optional[str] = None) -> Dict[str, Any]:
        """Reset stale or pending agent status to disconnected.

        Resets agent status for agents that are stuck in CONNECTED or PENDING
        state but are not actually connected. If server_id is provided, only
        resets that specific agent. Otherwise resets all stale agents.

        Args:
            server_id: Optional server identifier to reset specific agent.

        Returns:
            Dict containing reset count and status.
        """
        try:
            if server_id:
                # Reset specific agent
                agent = await self.agent_service.get_agent_by_server(server_id)
                if not agent:
                    return {
                        "success": False,
                        "message": f"No agent found for server '{server_id}'",
                        "error": "AGENT_NOT_FOUND",
                    }

                # Check if agent is actually connected
                if self.agent_manager.is_connected(agent.id):
                    return {
                        "success": False,
                        "message": "Agent is currently connected, cannot reset",
                        "error": "AGENT_CONNECTED",
                    }

                # Import here to avoid circular imports
                from models.agent import AgentUpdate

                agent_db = self.agent_service._get_agent_db()
                update = AgentUpdate(status=AgentStatus.DISCONNECTED)
                await agent_db.update_agent(agent.id, update)

                await log_event(
                    "agent",
                    "INFO",
                    f"Agent status reset to DISCONNECTED for server: {server_id}",
                    AGENT_TAGS,
                    {"agent_id": agent.id, "server_id": server_id},
                )

                logger.info(
                    "Agent status reset",
                    agent_id=agent.id,
                    server_id=server_id,
                )

                return {
                    "success": True,
                    "data": {"agent_id": agent.id, "reset_count": 1},
                    "message": f"Agent status reset for server '{server_id}'",
                }
            else:
                # Reset all stale agents
                reset_count = await self.agent_service.reset_stale_agent_statuses()

                await log_event(
                    "agent",
                    "INFO",
                    f"Reset {reset_count} stale agent status(es) to DISCONNECTED",
                    AGENT_TAGS,
                    {"reset_count": reset_count},
                )

                return {
                    "success": True,
                    "data": {"reset_count": reset_count},
                    "message": f"Reset {reset_count} stale agent(s) to DISCONNECTED",
                }

        except Exception as e:
            logger.error("Reset agent status error", server_id=server_id, error=str(e))
            return {
                "success": False,
                "message": f"Failed to reset agent status: {str(e)}",
                "error": "RESET_STATUS_ERROR",
            }
