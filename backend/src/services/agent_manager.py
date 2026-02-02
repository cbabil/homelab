"""Agent Manager Service.

Handles WebSocket connections to agents, message routing, and request/response
correlation for JSON-RPC communication with tomo agents.
"""

import asyncio
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Callable, Optional, Protocol

if TYPE_CHECKING:
    from services.agent_lifecycle import AgentLifecycleManager
from uuid import uuid4

import structlog

from models.agent import (
    AgentConfig,
    AgentHeartbeat,
    AgentShutdownRequest,
    AgentStatus,
    AgentUpdate,
)
from services.database import AgentDatabaseService

logger = structlog.get_logger("agent_manager")

# Type alias for lifecycle manager (avoid circular import)
LifecycleManager = Any

# Security: Maximum message size to prevent memory exhaustion (1MB default)
MAX_MESSAGE_SIZE_BYTES = 1024 * 1024


class WebSocketProtocol(Protocol):
    """Protocol for WebSocket connections (compatible with any implementation)."""

    async def send_text(self, data: str) -> None:
        """Send text message over WebSocket."""
        ...

    async def close(self, code: int = 1000) -> None:
        """Close the WebSocket connection."""
        ...


@dataclass
class AgentConnection:
    """Represents an active WebSocket connection to an agent."""

    agent_id: str
    websocket: WebSocketProtocol
    server_id: str
    pending_requests: dict[str, asyncio.Future] = field(default_factory=dict)
    connected_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class AgentManager:
    """Manages WebSocket connections and message routing for agents.

    Provides request/response correlation using JSON-RPC, handles agent
    connection lifecycle, and routes notifications to registered handlers.
    """

    def __init__(
        self,
        agent_db: AgentDatabaseService,
        lifecycle_manager: Optional["AgentLifecycleManager"] = None,
    ):
        """Initialize agent manager with database service.

        Args:
            agent_db: Agent database service for persistence operations.
            lifecycle_manager: Optional lifecycle manager for health tracking.
        """
        self._agent_db = agent_db
        self._lifecycle = lifecycle_manager
        self._connections: dict[str, AgentConnection] = {}
        self._notification_handlers: dict[str, Callable] = {}
        # Locks to prevent race conditions during connection registration
        self._connection_locks: dict[str, asyncio.Lock] = {}

        # Register built-in notification handlers
        self._register_builtin_handlers()

    def set_lifecycle_manager(self, lifecycle_manager: "AgentLifecycleManager") -> None:
        """Set the lifecycle manager after construction.

        Args:
            lifecycle_manager: Lifecycle manager instance.
        """
        self._lifecycle = lifecycle_manager
        logger.debug("Lifecycle manager attached to agent manager")

    def _register_builtin_handlers(self) -> None:
        """Register built-in handlers for agent notifications."""
        self.register_notification_handler("agent.heartbeat", self._handle_heartbeat)
        self.register_notification_handler("agent.shutdown", self._handle_shutdown)
        self.register_notification_handler(
            "agent.rotation_complete", self._handle_rotation_complete
        )
        self.register_notification_handler(
            "agent.rotation_failed", self._handle_rotation_failed
        )

    def register_notification_handler(self, method: str, handler: Callable) -> None:
        """Register a handler for agent notifications.

        Args:
            method: JSON-RPC method name to handle.
            handler: Async callable to invoke when notification received.
        """
        self._notification_handlers[method] = handler
        logger.debug("Registered notification handler", method=method)

    def _get_connection_lock(self, agent_id: str) -> asyncio.Lock:
        """Get or create a lock for an agent connection.

        Args:
            agent_id: Agent identifier.

        Returns:
            Lock for the agent.
        """
        if agent_id not in self._connection_locks:
            self._connection_locks[agent_id] = asyncio.Lock()
        return self._connection_locks[agent_id]

    async def register_connection(
        self,
        agent_id: str,
        websocket: WebSocketProtocol,
        server_id: str,
    ) -> AgentConnection:
        """Register a new agent WebSocket connection.

        If an existing connection exists for this agent, it will be closed
        and replaced with the new connection. Uses locking to prevent race
        conditions when multiple connections attempt to register simultaneously.

        Args:
            agent_id: Unique agent identifier.
            websocket: WebSocketProtocol connection instance.
            server_id: Associated server identifier.

        Returns:
            The registered AgentConnection instance.
        """
        # Use lock to prevent race conditions during registration
        lock = self._get_connection_lock(agent_id)
        async with lock:
            # Close existing connection if any
            if agent_id in self._connections:
                logger.info("Closing existing connection for agent", agent_id=agent_id)
                await self.unregister_connection(agent_id)

            connection = AgentConnection(
                agent_id=agent_id,
                websocket=websocket,
                server_id=server_id,
            )
            self._connections[agent_id] = connection

            # Update agent status in database
            await self._update_agent_status(agent_id, AgentStatus.CONNECTED)

            # Register with lifecycle manager for heartbeat tracking
            if self._lifecycle:
                self._lifecycle.register_agent_connection(agent_id)

            logger.info(
                "Agent connection registered",
                agent_id=agent_id,
                server_id=server_id,
            )
            return connection

    async def unregister_connection(self, agent_id: str) -> None:
        """Unregister an agent connection and cleanup resources.

        Cancels all pending requests and updates agent status in database.

        Args:
            agent_id: Unique agent identifier.
        """
        connection = self._connections.pop(agent_id, None)
        if not connection:
            logger.warning("No connection found to unregister", agent_id=agent_id)
            return

        # Cancel all pending requests
        for request_id, future in connection.pending_requests.items():
            if not future.done():
                future.cancel()
                logger.debug(
                    "Cancelled pending request",
                    agent_id=agent_id,
                    request_id=request_id,
                )

        # Close WebSocket if still open
        try:
            await connection.websocket.close()
        except Exception as e:
            logger.debug(
                "Error closing WebSocket",
                agent_id=agent_id,
                error=str(e),
            )

        # Update agent status in database
        await self._update_agent_status(agent_id, AgentStatus.DISCONNECTED)

        # Remove from lifecycle tracking
        if self._lifecycle:
            self._lifecycle.unregister_agent_connection(agent_id)

        logger.info("Agent connection unregistered", agent_id=agent_id)

    def is_connected(self, agent_id: str) -> bool:
        """Check if an agent is currently connected.

        Args:
            agent_id: Unique agent identifier.

        Returns:
            True if agent has an active connection, False otherwise.
        """
        return agent_id in self._connections

    def get_connection_by_server(self, server_id: str) -> Optional[AgentConnection]:
        """Get agent connection by associated server ID.

        Args:
            server_id: Server identifier to look up.

        Returns:
            AgentConnection if found, None otherwise.
        """
        for connection in self._connections.values():
            if connection.server_id == server_id:
                return connection
        return None

    async def send_command(
        self,
        agent_id: str,
        method: str,
        params: Optional[dict] = None,
        timeout: float = 30.0,
    ) -> Any:
        """Send a JSON-RPC command to an agent and wait for response.

        Args:
            agent_id: Target agent identifier.
            method: JSON-RPC method name.
            params: Optional method parameters.
            timeout: Response timeout in seconds.

        Returns:
            The result from the agent's response.

        Raises:
            ValueError: If agent is not connected.
            TimeoutError: If response not received within timeout.
            RuntimeError: If agent returns an error response.
        """
        connection = self._connections.get(agent_id)
        if not connection:
            raise ValueError(f"Agent {agent_id} is not connected")

        request_id = str(uuid4())
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
        }
        if params:
            request["params"] = params

        # Create future for response (use get_running_loop for Python 3.10+ compatibility)
        future: asyncio.Future = asyncio.get_running_loop().create_future()
        connection.pending_requests[request_id] = future

        try:
            # Send request
            await connection.websocket.send_text(json.dumps(request))
            logger.debug(
                "Sent command to agent",
                agent_id=agent_id,
                method=method,
                request_id=request_id,
            )

            # Wait for response with timeout
            result = await asyncio.wait_for(future, timeout=timeout)
            return result

        except asyncio.TimeoutError:
            logger.error(
                "Command timeout",
                agent_id=agent_id,
                method=method,
                request_id=request_id,
                timeout=timeout,
            )
            raise TimeoutError(
                f"Agent {agent_id} did not respond to {method} within {timeout}s"
            )
        finally:
            # Cleanup pending request - use defensive check in case connection
            # was removed by another task during execution
            current_connection = self._connections.get(agent_id)
            if current_connection and request_id in current_connection.pending_requests:
                current_connection.pending_requests.pop(request_id, None)

    async def handle_message(self, agent_id: str, message: str) -> None:
        """Handle an incoming message from an agent.

        Routes responses to waiting futures and notifications to handlers.
        Validates message size to prevent memory exhaustion attacks.

        Args:
            agent_id: Source agent identifier.
            message: Raw JSON message string.
        """
        # Security: Check message size to prevent memory exhaustion
        message_size = len(message.encode("utf-8"))
        if message_size > MAX_MESSAGE_SIZE_BYTES:
            logger.warning(
                "Rejected oversized message from agent",
                agent_id=agent_id,
                message_size=message_size,
                max_size=MAX_MESSAGE_SIZE_BYTES,
            )
            return

        connection = self._connections.get(agent_id)
        if not connection:
            logger.warning(
                "Received message from unknown agent",
                agent_id=agent_id,
            )
            return

        try:
            data = json.loads(message)
        except json.JSONDecodeError as e:
            logger.error(
                "Failed to parse agent message",
                agent_id=agent_id,
                error=str(e),
            )
            return

        # Check if this is a response (has id) or notification (no id)
        if "id" in data:
            await self._handle_response(connection, data)
        else:
            await self._handle_notification(agent_id, data)

    async def _handle_response(
        self,
        connection: AgentConnection,
        data: dict,
    ) -> None:
        """Handle a JSON-RPC response message.

        Args:
            connection: Agent connection that sent the response.
            data: Parsed JSON-RPC response.
        """
        request_id = data.get("id")
        future = connection.pending_requests.get(request_id)

        if not future:
            logger.warning(
                "Received response for unknown request",
                agent_id=connection.agent_id,
                request_id=request_id,
            )
            return

        if "error" in data:
            error = data["error"]
            error_msg = error.get("message", "Unknown error")
            error_code = error.get("code", -1)
            logger.error(
                "Agent returned error",
                agent_id=connection.agent_id,
                request_id=request_id,
                error_code=error_code,
                error_message=error_msg,
            )
            future.set_exception(RuntimeError(f"Agent error {error_code}: {error_msg}"))
        else:
            result = data.get("result")
            logger.debug(
                "Received response from agent",
                agent_id=connection.agent_id,
                request_id=request_id,
            )
            future.set_result(result)

    async def _handle_notification(self, agent_id: str, data: dict) -> None:
        """Handle a JSON-RPC notification message.

        Args:
            agent_id: Source agent identifier.
            data: Parsed JSON-RPC notification.
        """
        method = data.get("method")
        if not method:
            logger.warning(
                "Received notification without method",
                agent_id=agent_id,
            )
            return

        handler = self._notification_handlers.get(method)
        if not handler:
            logger.debug(
                "No handler for notification",
                agent_id=agent_id,
                method=method,
            )
            return

        params = data.get("params", {})
        try:
            await handler(agent_id, params)
            logger.debug(
                "Handled notification",
                agent_id=agent_id,
                method=method,
            )
        except Exception as e:
            logger.error(
                "Error handling notification",
                agent_id=agent_id,
                method=method,
                error=str(e),
            )

    async def broadcast_config_update(self, config: AgentConfig) -> None:
        """Broadcast configuration update to all connected agents.

        Args:
            config: New agent configuration to broadcast.
        """
        if not self._connections:
            logger.debug("No agents connected for config broadcast")
            return

        config_dict = config.model_dump()
        tasks = []

        for agent_id in self._connections:
            task = self._send_config_update(agent_id, config_dict)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        success_count = sum(1 for r in results if r is True)
        logger.info(
            "Config broadcast complete",
            total=len(tasks),
            success=success_count,
        )

    async def _send_config_update(
        self,
        agent_id: str,
        config: dict,
    ) -> bool:
        """Send config update to a single agent.

        Args:
            agent_id: Target agent identifier.
            config: Configuration dictionary to send.

        Returns:
            True if successful, False otherwise.
        """
        try:
            await self.send_command(
                agent_id,
                "config.update",
                {"config": config},
                timeout=10.0,
            )
            return True
        except Exception as e:
            logger.error(
                "Failed to send config update",
                agent_id=agent_id,
                error=str(e),
            )
            return False

    async def _update_agent_status(
        self,
        agent_id: str,
        status: AgentStatus,
    ) -> None:
        """Update agent status in the database.

        Args:
            agent_id: Agent identifier.
            status: New status to set.
        """
        try:
            update = AgentUpdate(status=status, last_seen=datetime.now(UTC))
            await self._agent_db.update_agent(agent_id, update)
        except Exception as e:
            logger.error(
                "Failed to update agent status in database",
                agent_id=agent_id,
                status=status.value,
                error=str(e),
            )

    async def _handle_heartbeat(self, agent_id: str, params: dict) -> None:
        """Handle heartbeat notification from agent.

        Args:
            agent_id: Source agent identifier.
            params: Heartbeat parameters (cpu, memory, uptime).
        """
        if not self._lifecycle:
            logger.debug("No lifecycle manager, skipping heartbeat")
            return

        heartbeat = AgentHeartbeat(
            agent_id=agent_id,
            timestamp=datetime.now(UTC),
            cpu_percent=params.get("cpu_percent"),
            memory_percent=params.get("memory_percent"),
            uptime_seconds=params.get("uptime_seconds"),
        )
        await self._lifecycle.record_heartbeat(heartbeat)

    async def _handle_shutdown(self, agent_id: str, params: dict) -> None:
        """Handle graceful shutdown notification from agent.

        Args:
            agent_id: Source agent identifier.
            params: Shutdown parameters (reason, restart).
        """
        if not self._lifecycle:
            logger.debug("No lifecycle manager, skipping shutdown handling")
            return

        request = AgentShutdownRequest(
            agent_id=agent_id,
            reason=params.get("reason", "unknown"),
            restart=params.get("restart", False),
        )
        await self._lifecycle.handle_shutdown(request)

        # Unregister the connection
        await self.unregister_connection(agent_id)

    async def ping_agent(self, agent_id: str, timeout: float = 5.0) -> bool:
        """Ping an agent to check if it's responsive.

        Args:
            agent_id: Agent to ping.
            timeout: Response timeout in seconds.

        Returns:
            True if agent responds, False otherwise.
        """
        try:
            result = await self.send_command(agent_id, "ping", timeout=timeout)
            return result == "pong"
        except (ValueError, TimeoutError, RuntimeError):
            return False

    async def send_rotation_request(
        self,
        agent_id: str,
        new_token: str,
        grace_period_seconds: int,
        timeout: float = 30.0,
    ) -> bool:
        """Send a token rotation request to an agent.

        The agent will save the new token and send a rotation_complete notification.

        Args:
            agent_id: Target agent identifier.
            new_token: The new authentication token.
            grace_period_seconds: Seconds the old token remains valid.
            timeout: Response timeout in seconds.

        Returns:
            True if agent acknowledged the rotation, False otherwise.
        """
        try:
            result = await self.send_command(
                agent_id,
                "agent.rotate_token",
                {
                    "new_token": new_token,
                    "grace_period_seconds": grace_period_seconds,
                },
                timeout=timeout,
            )
            logger.info(
                "Token rotation request sent to agent",
                agent_id=agent_id,
                grace_period_seconds=grace_period_seconds,
            )
            return result.get("status") == "ok" if isinstance(result, dict) else False
        except (ValueError, TimeoutError, RuntimeError) as e:
            logger.error(
                "Token rotation request failed",
                agent_id=agent_id,
                error=str(e),
            )
            return False

    async def _handle_rotation_complete(self, agent_id: str, params: dict) -> None:
        """Handle rotation complete notification from agent.

        This notification indicates the agent has successfully saved the new token.

        Args:
            agent_id: Source agent identifier.
            params: Notification params (may include timestamp).
        """
        logger.info(
            "Agent completed token rotation",
            agent_id=agent_id,
            params=params,
        )
        # The rotation completion is handled by the agent service via validate_token
        # when the agent authenticates with the pending token

    async def _handle_rotation_failed(self, agent_id: str, params: dict) -> None:
        """Handle rotation failed notification from agent.

        This notification indicates the agent failed to save the new token.

        Args:
            agent_id: Source agent identifier.
            params: Notification params (should include error details).
        """
        error = params.get("error", "Unknown error")
        logger.error(
            "Agent failed token rotation",
            agent_id=agent_id,
            error=error,
        )

    def get_connected_agent_ids(self) -> list[str]:
        """Get list of all connected agent IDs.

        Returns:
            List of connected agent identifiers.
        """
        return list(self._connections.keys())

    def get_connection_info(self, agent_id: str) -> Optional[dict]:
        """Get connection information for an agent.

        Args:
            agent_id: Agent identifier.

        Returns:
            Connection info dict or None if not connected.
        """
        connection = self._connections.get(agent_id)
        if not connection:
            return None

        return {
            "agent_id": connection.agent_id,
            "server_id": connection.server_id,
            "connected_at": connection.connected_at.isoformat(),
            "pending_requests": len(connection.pending_requests),
        }
