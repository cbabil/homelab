"""Command Router Service.

Routes server commands through the agent when connected, with SSH fallback
when the agent is unavailable. Provides a unified interface for command
execution regardless of transport mechanism.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Callable, Optional

import structlog

from services.agent_manager import AgentManager
from services.agent_service import AgentService
from services.server_service import ServerService
from services.ssh_service import SSHService

logger = structlog.get_logger("command_router")


class ExecutionMethod(str, Enum):
    """Command execution method used."""

    AGENT = "agent"
    SSH = "ssh"
    NONE = "none"


@dataclass
class CommandResult:
    """Result of a routed command execution."""

    success: bool
    output: str
    method: ExecutionMethod
    exit_code: Optional[int] = None
    error: Optional[str] = None
    execution_time_ms: Optional[float] = None


class CommandRouter:
    """Routes commands to servers via agent or SSH.

    Provides a unified interface for executing commands on remote servers.
    Automatically selects the best available transport (agent WebSocket
    or direct SSH) based on connection status.
    """

    def __init__(
        self,
        agent_service: AgentService,
        agent_manager: AgentManager,
        server_service: ServerService,
        ssh_service: SSHService,
        prefer_agent: bool = True,
    ):
        """Initialize command router with required services.

        Args:
            agent_service: Service for agent operations.
            agent_manager: Manager for agent WebSocket connections.
            server_service: Service for server credentials.
            ssh_service: Service for SSH command execution.
            prefer_agent: If True, prefer agent over SSH when available.
        """
        self._agent_service = agent_service
        self._agent_manager = agent_manager
        self._server_service = server_service
        self._ssh_service = ssh_service
        self._prefer_agent = prefer_agent

    async def execute(
        self,
        server_id: str,
        command: str,
        timeout: float = 120.0,
        force_ssh: bool = False,
        force_agent: bool = False,
    ) -> CommandResult:
        """Execute a command on a server.

        Routes the command through the agent if connected, otherwise
        falls back to SSH. Can be forced to use a specific method.

        Args:
            server_id: Target server identifier.
            command: Shell command to execute.
            timeout: Execution timeout in seconds.
            force_ssh: Force SSH execution even if agent available.
            force_agent: Force agent execution, fail if not connected.

        Returns:
            CommandResult with execution details.
        """
        start_time = datetime.now(UTC)

        # Determine execution method
        method = await self._determine_method(server_id, force_ssh, force_agent)

        if method == ExecutionMethod.NONE:
            # Provide helpful error message about why agent isn't available
            error_msg = await self._get_agent_unavailable_reason(server_id)
            return CommandResult(
                success=False,
                output="",
                method=ExecutionMethod.NONE,
                error=error_msg,
            )

        # Execute via selected method
        if method == ExecutionMethod.AGENT:
            result = await self._execute_via_agent(server_id, command, timeout)
        else:
            result = await self._execute_via_ssh(server_id, command, timeout)

        # Calculate execution time
        elapsed = (datetime.now(UTC) - start_time).total_seconds() * 1000
        result.execution_time_ms = round(elapsed, 2)

        logger.info(
            "Command executed",
            server_id=server_id,
            method=result.method.value,
            success=result.success,
            execution_time_ms=result.execution_time_ms,
        )

        return result

    async def execute_with_progress(
        self,
        server_id: str,
        command: str,
        progress_callback: Callable[[str], None],
        timeout: float = 600.0,
        force_ssh: bool = False,
    ) -> CommandResult:
        """Execute a command with streaming progress output.

        For long-running commands, streams output as it becomes available.
        Currently only supported via SSH (agent streaming not implemented).

        Args:
            server_id: Target server identifier.
            command: Shell command to execute.
            progress_callback: Async callback for each output line.
            timeout: Execution timeout in seconds.
            force_ssh: Force SSH execution.

        Returns:
            CommandResult with execution details.
        """
        start_time = datetime.now(UTC)

        # Progress streaming requires SSH (agent streaming not yet implemented)
        result = await self._execute_via_ssh_with_progress(
            server_id, command, progress_callback, timeout
        )

        elapsed = (datetime.now(UTC) - start_time).total_seconds() * 1000
        result.execution_time_ms = round(elapsed, 2)

        return result

    async def is_agent_available(self, server_id: str) -> bool:
        """Check if agent is available for a server.

        Args:
            server_id: Server identifier to check.

        Returns:
            True if agent is connected and responsive.
        """
        agent = await self._agent_service.get_agent_by_server(server_id)
        if not agent:
            return False
        return self._agent_manager.is_connected(agent.id)

    async def get_available_methods(self, server_id: str) -> list[ExecutionMethod]:
        """Get list of available execution methods for a server.

        Args:
            server_id: Server identifier.

        Returns:
            List of available execution methods.
        """
        methods = []

        # Check agent availability
        if await self.is_agent_available(server_id):
            methods.append(ExecutionMethod.AGENT)

        # Check SSH availability (server exists with credentials)
        server = await self._server_service.get_server(server_id)
        if server:
            methods.append(ExecutionMethod.SSH)

        return methods

    async def _get_agent_unavailable_reason(self, server_id: str) -> str:
        """Get a user-friendly reason why the agent is not available.

        Args:
            server_id: Server identifier.

        Returns:
            Human-readable error message.
        """
        try:
            agent = await self._agent_service.get_agent_by_server(server_id)
            if not agent:
                return (
                    "Agent not installed on this server. "
                    "Please install the agent from the server settings."
                )
            if not self._agent_manager.is_connected(agent.id):
                return (
                    "Agent is installed but not connected. "
                    "Check that the agent is running on the server."
                )
        except Exception as e:
            logger.warning(
                "Failed to get agent status", server_id=server_id, error=str(e)
            )
        return "Agent is not available for this server."

    async def _determine_method(
        self,
        server_id: str,
        force_ssh: bool,
        force_agent: bool,
    ) -> ExecutionMethod:
        """Determine the execution method to use.

        Args:
            server_id: Target server identifier.
            force_ssh: Force SSH if True.
            force_agent: Force agent if True.

        Returns:
            ExecutionMethod to use.
        """
        if force_ssh and force_agent:
            logger.warning("Both force_ssh and force_agent specified, using agent")
            force_ssh = False

        if force_agent:
            if await self.is_agent_available(server_id):
                return ExecutionMethod.AGENT
            logger.warning("Agent forced but not available", server_id=server_id)
            return ExecutionMethod.NONE

        if force_ssh:
            return ExecutionMethod.SSH

        # Auto-select: prefer agent if available and configured
        if self._prefer_agent and await self.is_agent_available(server_id):
            return ExecutionMethod.AGENT

        return ExecutionMethod.SSH

    async def _execute_via_agent(
        self,
        server_id: str,
        command: str,
        timeout: float,
    ) -> CommandResult:
        """Execute command via agent WebSocket.

        Args:
            server_id: Target server identifier.
            command: Shell command to execute.
            timeout: Execution timeout in seconds.

        Returns:
            CommandResult from agent execution.
        """
        try:
            agent = await self._agent_service.get_agent_by_server(server_id)
            if not agent:
                return CommandResult(
                    success=False,
                    output="",
                    method=ExecutionMethod.AGENT,
                    error="Agent not found for server",
                )

            if not self._agent_manager.is_connected(agent.id):
                return CommandResult(
                    success=False,
                    output="",
                    method=ExecutionMethod.AGENT,
                    error="Agent not connected",
                )

            # Send command to agent using system.exec method
            result = await self._agent_manager.send_command(
                agent_id=agent.id,
                method="system.exec",
                params={"command": command, "timeout": timeout},
                timeout=timeout,
            )

            # Parse agent response (system.exec returns stdout, stderr, exit_code)
            if isinstance(result, dict):
                exit_code = result.get("exit_code", -1)
                stdout = result.get("stdout", "")
                stderr = result.get("stderr", "")
                return CommandResult(
                    success=exit_code == 0,
                    output=stdout or stderr,
                    method=ExecutionMethod.AGENT,
                    exit_code=exit_code,
                    error=stderr if exit_code != 0 else None,
                )

            return CommandResult(
                success=True,
                output=str(result) if result else "",
                method=ExecutionMethod.AGENT,
            )

        except TimeoutError:
            logger.error("Agent command timeout", server_id=server_id)
            return CommandResult(
                success=False,
                output="",
                method=ExecutionMethod.AGENT,
                error="Command timed out",
            )
        except Exception as e:
            logger.error("Agent execution error", server_id=server_id, error=str(e))
            return CommandResult(
                success=False,
                output="",
                method=ExecutionMethod.AGENT,
                error=str(e),
            )

    async def _execute_via_ssh(
        self,
        server_id: str,
        command: str,
        timeout: float,
    ) -> CommandResult:
        """Execute command via SSH.

        Args:
            server_id: Target server identifier.
            command: Shell command to execute.
            timeout: Execution timeout in seconds.

        Returns:
            CommandResult from SSH execution.
        """
        try:
            # Get server and credentials
            server = await self._server_service.get_server(server_id)
            if not server:
                return CommandResult(
                    success=False,
                    output="",
                    method=ExecutionMethod.SSH,
                    error="Server not found",
                )

            credentials = await self._server_service.get_credentials(server_id)
            if not credentials:
                return CommandResult(
                    success=False,
                    output="",
                    method=ExecutionMethod.SSH,
                    error="Failed to retrieve server credentials",
                )

            # Execute via SSH
            success, output = await self._ssh_service.execute_command(
                host=server.host,
                port=server.port,
                username=server.username,
                auth_type=server.auth_type,
                credentials=credentials,
                command=command,
                timeout=int(timeout),
            )

            return CommandResult(
                success=success,
                output=output,
                method=ExecutionMethod.SSH,
                exit_code=0 if success else 1,
            )

        except Exception as e:
            logger.error("SSH execution error", server_id=server_id, error=str(e))
            return CommandResult(
                success=False,
                output="",
                method=ExecutionMethod.SSH,
                error=str(e),
            )

    async def _execute_via_ssh_with_progress(
        self,
        server_id: str,
        command: str,
        progress_callback: Callable[[str], None],
        timeout: float,
    ) -> CommandResult:
        """Execute command via SSH with progress streaming.

        Args:
            server_id: Target server identifier.
            command: Shell command to execute.
            progress_callback: Callback for each output line.
            timeout: Execution timeout in seconds.

        Returns:
            CommandResult from SSH execution.
        """
        try:
            server = await self._server_service.get_server(server_id)
            if not server:
                return CommandResult(
                    success=False,
                    output="",
                    method=ExecutionMethod.SSH,
                    error="Server not found",
                )

            credentials = await self._server_service.get_credentials(server_id)
            if not credentials:
                return CommandResult(
                    success=False,
                    output="",
                    method=ExecutionMethod.SSH,
                    error="Failed to retrieve server credentials",
                )

            success, output = await self._ssh_service.execute_command_with_progress(
                host=server.host,
                port=server.port,
                username=server.username,
                auth_type=server.auth_type,
                credentials=credentials,
                command=command,
                progress_callback=progress_callback,
                timeout=int(timeout),
            )

            return CommandResult(
                success=success,
                output=output,
                method=ExecutionMethod.SSH,
                exit_code=0 if success else 1,
            )

        except Exception as e:
            logger.error(
                "SSH progress execution error", server_id=server_id, error=str(e)
            )
            return CommandResult(
                success=False,
                output="",
                method=ExecutionMethod.SSH,
                error=str(e),
            )
