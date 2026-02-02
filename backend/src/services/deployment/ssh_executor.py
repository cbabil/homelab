"""
Command Executors for Deployment

SSHExecutor: Direct SSH execution (legacy, for servers without agent)
AgentExecutor: Agent-only execution (preferred for all deployments)
"""

import structlog

logger = structlog.get_logger("deployment.ssh")


class SSHExecutor:
    """Executes SSH commands on remote servers."""

    def __init__(self, ssh_service, server_service):
        """Initialize SSH executor.

        Args:
            ssh_service: SSH service for command execution
            server_service: Server service for credentials
        """
        self.ssh_service = ssh_service
        self.server_service = server_service

    async def execute(self, server_id: str, command: str, timeout: int = 120):
        """Execute SSH command on server.

        Args:
            server_id: Target server ID
            command: Command to execute
            timeout: Command timeout in seconds

        Returns:
            Tuple of (exit_code, stdout, stderr)
        """
        server = await self.server_service.get_server(server_id)
        if not server:
            logger.error("Server not found for SSH command", server_id=server_id)
            return (1, "", "Server not found")

        credentials = await self.server_service.get_credentials(server_id)
        if not credentials:
            logger.error("Could not get credentials for server", server_id=server_id)
            return (1, "", "Could not get server credentials")

        success, output = await self.ssh_service.execute_command(
            host=server.host,
            port=server.port,
            username=server.username,
            auth_type=server.auth_type.value,
            credentials=credentials,
            command=command,
            timeout=timeout,
        )

        if success:
            return (0, output, "")
        else:
            return (1, "", output)

    async def execute_with_progress(
        self, server_id: str, command: str, progress_callback=None, timeout: int = 600
    ):
        """Execute SSH command with progress streaming.

        Args:
            server_id: Target server ID
            command: Command to execute
            progress_callback: Async callback for progress updates
            timeout: Command timeout in seconds

        Returns:
            Tuple of (exit_code, stdout, stderr)
        """
        server = await self.server_service.get_server(server_id)
        if not server:
            return (1, "", "Server not found")

        credentials = await self.server_service.get_credentials(server_id)
        if not credentials:
            return (1, "", "Could not get server credentials")

        success, output = await self.ssh_service.execute_command_with_progress(
            host=server.host,
            port=server.port,
            username=server.username,
            auth_type=server.auth_type.value,
            credentials=credentials,
            command=command,
            progress_callback=progress_callback,
            timeout=timeout,
        )

        if success:
            return (0, output, "")
        else:
            return (1, "", output)


class AgentExecutor:
    """Executes commands via agent only.

    Primary executor for deployment operations. Commands are sent through
    the agent WebSocket connection. Fails with clear error if agent unavailable.
    """

    def __init__(self, command_router):
        """Initialize agent executor.

        Args:
            command_router: CommandRouter for agent execution.
        """
        self.command_router = command_router

    async def execute(
        self, server_id: str, command: str, timeout: int = 120
    ) -> tuple[int, str, str]:
        """Execute command on server via agent.

        Args:
            server_id: Target server ID.
            command: Command to execute.
            timeout: Command timeout in seconds.

        Returns:
            Tuple of (exit_code, stdout, stderr).

        Raises:
            Fails with error if agent is not connected.
        """
        # Force agent execution - no SSH fallback
        result = await self.command_router.execute(
            server_id=server_id,
            command=command,
            timeout=float(timeout),
            force_agent=True,
        )

        exit_code = (
            result.exit_code
            if result.exit_code is not None
            else (0 if result.success else 1)
        )

        if result.success:
            return (exit_code, result.output, "")
        else:
            return (exit_code, "", result.error or result.output)

    async def execute_with_progress(
        self,
        server_id: str,
        command: str,
        progress_callback=None,
        timeout: int = 600,
    ) -> tuple[int, str, str]:
        """Execute command via agent (progress callback ignored).

        Note: Progress streaming not yet implemented for agent.
        Command executes normally, callback is not used.

        Args:
            server_id: Target server ID.
            command: Command to execute.
            progress_callback: Ignored (agent streaming not implemented).
            timeout: Command timeout in seconds.

        Returns:
            Tuple of (exit_code, stdout, stderr).
        """
        # Agent doesn't support progress streaming yet - execute normally
        return await self.execute(server_id, command, timeout)
