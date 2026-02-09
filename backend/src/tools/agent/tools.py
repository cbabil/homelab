"""
Agent Management Tools

Provides agent installation, status, lifecycle, and command capabilities
for the MCP server. Delegates to lifecycle and status sub-modules.
"""

import re
import shlex
from typing import Any

import structlog

from services.agent_lifecycle import AgentLifecycleManager
from services.agent_manager import AgentManager
from services.agent_packager import AgentPackager
from services.agent_service import AgentService
from services.server_service import ServerService
from services.ssh_service import SSHService
from tools.agent import lifecycle as lifecycle_ops
from tools.agent import status as status_ops
from tools.agent.constants import (
    AGENT_CONTAINER_NAME,
    AGENT_IMAGE_NAME,
    AGENT_TAGS,
    get_server_url,
)

logger = structlog.get_logger("agent_tools")


class AgentTools:
    """Agent management tools for the MCP server."""

    def __init__(
        self,
        agent_service: AgentService,
        agent_manager: AgentManager,
        ssh_service: SSHService,
        server_service: ServerService,
        agent_packager: AgentPackager | None = None,
        agent_lifecycle: AgentLifecycleManager | None = None,
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
        return get_server_url()

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
        dangerous_chars = [
            ";",
            "|",
            "`",
            "$",
            "(",
            ")",
            "<",
            ">",
            "\\",
            "\n",
            "\r",
            "'",
            '"',
        ]
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
            logger.error(
                "Invalid registration code format",
                code_preview=code[:10] if code else "empty",
            )
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

    # --- Lifecycle operations (delegated to lifecycle module) ---

    async def install_agent(self, server_id: str) -> dict[str, Any]:
        """Install an agent on a server via SSH.

        Args:
            server_id: Server identifier to install agent on.

        Returns:
            Dict containing agent_id, server_id, and installation status.
        """
        return await lifecycle_ops.install_agent(
            server_id=server_id,
            agent_service=self.agent_service,
            ssh_service=self.ssh_service,
            server_service=self.server_service,
            agent_packager=self.agent_packager,
            build_deploy_script=self._build_deploy_script,
        )

    async def revoke_agent_token(self, server_id: str) -> dict[str, Any]:
        """Revoke an agent's authentication token.

        Args:
            server_id: Server identifier to revoke agent token for.

        Returns:
            Dict containing success status of the token revocation.
        """
        return await lifecycle_ops.revoke_agent_token(
            server_id=server_id,
            agent_service=self.agent_service,
            agent_manager=self.agent_manager,
        )

    async def uninstall_agent(self, server_id: str) -> dict[str, Any]:
        """Uninstall agent from a server.

        Args:
            server_id: Server identifier to uninstall agent from.

        Returns:
            Dict containing success status of the uninstallation.
        """
        return await lifecycle_ops.uninstall_agent(
            server_id=server_id,
            agent_service=self.agent_service,
            agent_manager=self.agent_manager,
            ssh_service=self.ssh_service,
            server_service=self.server_service,
        )

    async def rotate_agent_token(self, server_id: str) -> dict[str, Any]:
        """Rotate an agent's authentication token.

        Args:
            server_id: Server identifier to rotate agent token for.

        Returns:
            Dict containing success status and rotation details.
        """
        return await lifecycle_ops.rotate_agent_token(
            server_id=server_id,
            agent_service=self.agent_service,
            agent_manager=self.agent_manager,
        )

    # --- Status and monitoring operations (delegated to status module) ---

    async def get_agent_status(self, server_id: str) -> dict[str, Any]:
        """Get agent status for a server.

        Args:
            server_id: Server identifier to check agent status for.

        Returns:
            Dict containing agent info or None if no agent exists.
        """
        return await status_ops.get_agent_status(
            server_id=server_id,
            agent_service=self.agent_service,
            agent_manager=self.agent_manager,
        )

    async def send_agent_command(
        self,
        server_id: str,
        method: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Send a command to an agent via WebSocket.

        Args:
            server_id: Server identifier whose agent should receive command.
            method: JSON-RPC method name to invoke.
            params: Optional parameters for the method.

        Returns:
            Dict containing the command result or error.
        """
        return await status_ops.send_agent_command(
            server_id=server_id,
            method=method,
            agent_service=self.agent_service,
            agent_manager=self.agent_manager,
            params=params,
        )

    async def check_agent_health(self, server_id: str) -> dict[str, Any]:
        """Check comprehensive health status of an agent.

        Args:
            server_id: Server identifier to check agent health for.

        Returns:
            Dict containing agent health information.
        """
        return await status_ops.check_agent_health(
            server_id=server_id,
            agent_service=self.agent_service,
            agent_manager=self.agent_manager,
            lifecycle=self.lifecycle,
        )

    async def ping_agent(
        self, server_id: str, timeout: float = 5.0
    ) -> dict[str, Any]:
        """Ping an agent to verify connectivity.

        Args:
            server_id: Server identifier of agent to ping.
            timeout: Response timeout in seconds.

        Returns:
            Dict containing ping result and latency.
        """
        return await status_ops.ping_agent(
            server_id=server_id,
            agent_service=self.agent_service,
            agent_manager=self.agent_manager,
            timeout=timeout,
        )

    async def check_agent_version(self, server_id: str) -> dict[str, Any]:
        """Check if an agent needs updating.

        Args:
            server_id: Server identifier to check agent version for.

        Returns:
            Dict containing version comparison information.
        """
        return await status_ops.check_agent_version(
            server_id=server_id,
            agent_service=self.agent_service,
            lifecycle=self.lifecycle,
        )

    async def trigger_agent_update(self, server_id: str) -> dict[str, Any]:
        """Trigger an agent update.

        Args:
            server_id: Server identifier of agent to update.

        Returns:
            Dict containing update trigger result.
        """
        return await status_ops.trigger_agent_update(
            server_id=server_id,
            agent_service=self.agent_service,
            agent_manager=self.agent_manager,
            lifecycle=self.lifecycle,
        )

    async def list_stale_agents(self) -> dict[str, Any]:
        """List all agents that have missed heartbeats.

        Returns:
            Dict containing list of stale agents.
        """
        return await status_ops.list_stale_agents(
            agent_manager=self.agent_manager,
            lifecycle=self.lifecycle,
        )

    async def list_agents(self) -> dict[str, Any]:
        """List all registered agents.

        Returns:
            Dict containing list of agents.
        """
        return await status_ops.list_agents(
            agent_service=self.agent_service,
        )

    async def reset_agent_status(
        self, server_id: str | None = None
    ) -> dict[str, Any]:
        """Reset stale or pending agent status to disconnected.

        Args:
            server_id: Optional server identifier to reset specific agent.

        Returns:
            Dict containing reset count and status.
        """
        return await status_ops.reset_agent_status(
            agent_service=self.agent_service,
            agent_manager=self.agent_manager,
            server_id=server_id,
        )
