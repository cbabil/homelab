"""
Agent Status and Monitoring Operations

Handles agent status checks, health monitoring, ping, version checks,
updates, and listing operations.
"""

from datetime import UTC, datetime
from typing import Any

import structlog

from models.agent import AgentInfo, AgentStatus
from services.agent_lifecycle import AgentLifecycleManager
from services.agent_manager import AgentManager
from services.agent_service import AgentService
from tools.agent.constants import AGENT_TAGS
from tools.common import log_event

logger = structlog.get_logger("agent_tools.status")


async def get_agent_status(
    server_id: str,
    agent_service: AgentService,
    agent_manager: AgentManager,
) -> dict[str, Any]:
    """Get agent status for a server.

    Returns agent information including connection status, version,
    and last seen timestamp.

    Args:
        server_id: Server identifier to check agent status for.
        agent_service: Service for agent lifecycle operations.
        agent_manager: Manager for active agent connections.

    Returns:
        Dict containing agent info or None if no agent exists.
    """
    try:
        agent = await agent_service.get_agent_by_server(server_id)

        if not agent:
            return {
                "success": True,
                "data": None,
                "message": "No agent found for server",
            }

        # Check if agent is currently connected via WebSocket
        is_connected = agent_manager.is_connected(agent.id)

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


async def send_agent_command(
    server_id: str,
    method: str,
    agent_service: AgentService,
    agent_manager: AgentManager,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Send a command to an agent via WebSocket.

    Sends a JSON-RPC command to the agent and waits for response.

    Args:
        server_id: Server identifier whose agent should receive command.
        method: JSON-RPC method name to invoke.
        agent_service: Service for agent lifecycle operations.
        agent_manager: Manager for active agent connections.
        params: Optional parameters for the method.

    Returns:
        Dict containing the command result or error.
    """
    try:
        # Get agent for this server
        agent = await agent_service.get_agent_by_server(server_id)

        if not agent:
            return {
                "success": False,
                "message": "No agent found for server",
                "error": "AGENT_NOT_FOUND",
            }

        # Check if agent is connected
        if not agent_manager.is_connected(agent.id):
            return {
                "success": False,
                "message": "Agent is not connected",
                "error": "AGENT_NOT_CONNECTED",
            }

        # Send command and wait for response
        result = await agent_manager.send_command(
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


async def check_agent_health(
    server_id: str,
    agent_service: AgentService,
    agent_manager: AgentManager,
    lifecycle: AgentLifecycleManager | None = None,
) -> dict[str, Any]:
    """Check comprehensive health status of an agent.

    Returns health status including connectivity, staleness, and version.

    Args:
        server_id: Server identifier to check agent health for.
        agent_service: Service for agent lifecycle operations.
        agent_manager: Manager for active agent connections.
        lifecycle: Optional lifecycle manager for health tracking.

    Returns:
        Dict containing agent health information.
    """
    try:
        agent = await agent_service.get_agent_by_server(server_id)

        if not agent:
            return {
                "success": False,
                "message": "No agent found for server",
                "error": "AGENT_NOT_FOUND",
            }

        is_connected = agent_manager.is_connected(agent.id)
        is_stale = (
            lifecycle.is_agent_stale(agent.id)
            if lifecycle and is_connected
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


async def ping_agent(
    server_id: str,
    agent_service: AgentService,
    agent_manager: AgentManager,
    timeout: float = 5.0,
) -> dict[str, Any]:
    """Ping an agent to verify connectivity.

    Sends a ping request and measures response latency.

    Args:
        server_id: Server identifier of agent to ping.
        agent_service: Service for agent lifecycle operations.
        agent_manager: Manager for active agent connections.
        timeout: Response timeout in seconds.

    Returns:
        Dict containing ping result and latency.
    """
    try:
        agent = await agent_service.get_agent_by_server(server_id)

        if not agent:
            return {
                "success": False,
                "message": "No agent found for server",
                "error": "AGENT_NOT_FOUND",
            }

        if not agent_manager.is_connected(agent.id):
            return {
                "success": False,
                "message": "Agent is not connected",
                "error": "AGENT_NOT_CONNECTED",
            }

        start_time = datetime.now(UTC)
        is_responsive = await agent_manager.ping_agent(agent.id, timeout)
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


async def check_agent_version(
    server_id: str,
    agent_service: AgentService,
    lifecycle: AgentLifecycleManager | None = None,
) -> dict[str, Any]:
    """Check if an agent needs updating.

    Compares current agent version against latest available version.

    Args:
        server_id: Server identifier to check agent version for.
        agent_service: Service for agent lifecycle operations.
        lifecycle: Optional lifecycle manager for version checking.

    Returns:
        Dict containing version comparison information.
    """
    try:
        if not lifecycle:
            return {
                "success": False,
                "message": "Lifecycle manager not available",
                "error": "LIFECYCLE_UNAVAILABLE",
            }

        agent = await agent_service.get_agent_by_server(server_id)

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

        version_info = lifecycle.check_version(agent.version)

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


async def trigger_agent_update(
    server_id: str,
    agent_service: AgentService,
    agent_manager: AgentManager,
    lifecycle: AgentLifecycleManager | None = None,
) -> dict[str, Any]:
    """Trigger an agent update.

    Marks the agent for update and sends update command if connected.

    Args:
        server_id: Server identifier of agent to update.
        agent_service: Service for agent lifecycle operations.
        agent_manager: Manager for active agent connections.
        lifecycle: Optional lifecycle manager for update operations.

    Returns:
        Dict containing update trigger result.
    """
    try:
        if not lifecycle:
            return {
                "success": False,
                "message": "Lifecycle manager not available",
                "error": "LIFECYCLE_UNAVAILABLE",
            }

        agent = await agent_service.get_agent_by_server(server_id)

        if not agent:
            return {
                "success": False,
                "message": "No agent found for server",
                "error": "AGENT_NOT_FOUND",
            }

        if not agent_manager.is_connected(agent.id):
            return {
                "success": False,
                "message": "Agent must be connected to trigger update",
                "error": "AGENT_NOT_CONNECTED",
            }

        # Check if update is needed
        if agent.version:
            version_info = lifecycle.check_version(agent.version)
            if not version_info.update_available:
                return {
                    "success": False,
                    "message": "Agent is already at latest version",
                    "error": "ALREADY_LATEST",
                }

        # Mark agent for update
        success = await lifecycle.trigger_update(agent.id)
        if not success:
            return {
                "success": False,
                "message": "Failed to mark agent for update",
                "error": "UPDATE_TRIGGER_FAILED",
            }

        # Send update command to agent
        try:
            latest = lifecycle.check_version(agent.version or "0.0.0")
            await agent_manager.send_command(
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


async def list_stale_agents(
    agent_manager: AgentManager,
    lifecycle: AgentLifecycleManager | None = None,
) -> dict[str, Any]:
    """List all agents that have missed heartbeats.

    Returns list of agents that haven't responded within the
    configured heartbeat timeout.

    Args:
        agent_manager: Manager for active agent connections.
        lifecycle: Optional lifecycle manager for staleness checking.

    Returns:
        Dict containing list of stale agents.
    """
    try:
        if not lifecycle:
            return {
                "success": False,
                "message": "Lifecycle manager not available",
                "error": "LIFECYCLE_UNAVAILABLE",
            }

        stale_agent_ids = await lifecycle.get_stale_agents()

        stale_agents = []
        for agent_id in stale_agent_ids:
            info = agent_manager.get_connection_info(agent_id)
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


async def list_agents(
    agent_service: AgentService,
) -> dict[str, Any]:
    """List all registered agents.

    Returns all agents in the system with their current status.

    Args:
        agent_service: Service for agent lifecycle operations.

    Returns:
        Dict containing list of agents with id, server_id, status, version,
        last_seen, and registered_at.
    """
    try:
        agents = await agent_service.list_all_agents()

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


async def reset_agent_status(
    agent_service: AgentService,
    agent_manager: AgentManager,
    server_id: str | None = None,
) -> dict[str, Any]:
    """Reset stale or pending agent status to disconnected.

    Resets agent status for agents that are stuck in CONNECTED or PENDING
    state but are not actually connected. If server_id is provided, only
    resets that specific agent. Otherwise resets all stale agents.

    Args:
        agent_service: Service for agent lifecycle operations.
        agent_manager: Manager for active agent connections.
        server_id: Optional server identifier to reset specific agent.

    Returns:
        Dict containing reset count and status.
    """
    try:
        if server_id:
            # Reset specific agent
            agent = await agent_service.get_agent_by_server(server_id)
            if not agent:
                return {
                    "success": False,
                    "message": f"No agent found for server '{server_id}'",
                    "error": "AGENT_NOT_FOUND",
                }

            # Check if agent is actually connected
            if agent_manager.is_connected(agent.id):
                return {
                    "success": False,
                    "message": "Agent is currently connected, cannot reset",
                    "error": "AGENT_CONNECTED",
                }

            # Import here to avoid circular imports
            from models.agent import AgentUpdate

            agent_db = agent_service.get_agent_db()
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
            reset_count = await agent_service.reset_stale_agent_statuses()

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
