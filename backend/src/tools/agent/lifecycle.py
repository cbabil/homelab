"""
Agent Lifecycle Operations

Handles agent installation, uninstallation, token revocation,
and token rotation operations.
"""

from typing import Any

import structlog

from services.agent_manager import AgentManager
from services.agent_service import AgentService
from services.server_service import ServerService
from services.ssh_service import SSHService
from tools.agent.constants import AGENT_TAGS, get_server_url
from tools.common import log_event

logger = structlog.get_logger("agent_tools.lifecycle")

AGENT_CONTAINER_NAME = "tomo-agent"


async def install_agent(
    server_id: str,
    agent_service: AgentService,
    ssh_service: SSHService,
    server_service: ServerService,
    agent_packager: Any,
    build_deploy_script: Any,
) -> dict[str, Any]:
    """Install an agent on a server via SSH.

    Creates a new agent record, generates a registration code, and
    deploys the agent container on the target server via SSH.

    Args:
        server_id: Server identifier to install agent on.
        agent_service: Service for agent lifecycle operations.
        ssh_service: Service for SSH command execution.
        server_service: Service for server management.
        agent_packager: Packager for agent source code deployment.
        build_deploy_script: Callable to build deployment script.

    Returns:
        Dict containing agent_id, server_id, and installation status.
    """
    server_name = None  # Track for error logging
    try:
        # Get server details for SSH connection
        server = await server_service.get_server(server_id)
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
                {
                    "server_id": server_id,
                    "server_name": server.name,
                    "error": "DOCKER_NOT_INSTALLED",
                },
            )
            return {
                "success": False,
                "message": "Docker is required but not installed on this server",
                "error": "DOCKER_NOT_INSTALLED",
            }

        # Get credentials for SSH connection (check before creating agent)
        credentials = await server_service.get_credentials(server_id)
        if not credentials:
            await log_event(
                "agent",
                "ERROR",
                f"Agent install failed: credentials not found for server '{server.name}'",
                AGENT_TAGS,
                {
                    "server_id": server_id,
                    "server_name": server.name,
                    "error": "CREDENTIALS_NOT_FOUND",
                },
            )
            return {
                "success": False,
                "message": "Server credentials not found",
                "error": "CREDENTIALS_NOT_FOUND",
            }

        # Create agent record and registration code
        agent, registration_code = await agent_service.create_agent(server_id)
        server_url = get_server_url()
        agent_version = agent_packager.get_version()

        logger.info(
            "Deploying agent via SSH",
            agent_id=agent.id,
            server_id=server_id,
            host=server.host,
            version=agent_version,
        )

        # Build script to deploy agent from source
        deploy_script = build_deploy_script(
            registration_code.code,
            server_url,
        )

        # Execute deployment via SSH
        success, output = await ssh_service.execute_command(
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
            await server_service.update_server_system_info(
                server_id, updated_info
            )

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


async def revoke_agent_token(
    server_id: str,
    agent_service: AgentService,
    agent_manager: AgentManager,
) -> dict[str, Any]:
    """Revoke an agent's authentication token.

    Disconnects the agent WebSocket connection and invalidates
    its authentication token. The agent container remains running
    on the server but can no longer authenticate.

    Args:
        server_id: Server identifier to revoke agent token for.
        agent_service: Service for agent lifecycle operations.
        agent_manager: Manager for active agent connections.

    Returns:
        Dict containing success status of the token revocation.
    """
    try:
        agent = await agent_service.get_agent_by_server(server_id)

        if not agent:
            return {
                "success": False,
                "message": "No agent found for server",
                "error": "AGENT_NOT_FOUND",
            }

        # Disconnect WebSocket if connected
        if agent_manager.is_connected(agent.id):
            await agent_manager.unregister_connection(agent.id)

        # Revoke agent token
        success = await agent_service.revoke_agent_token(agent.id)

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


async def uninstall_agent(
    server_id: str,
    agent_service: AgentService,
    agent_manager: AgentManager,
    ssh_service: SSHService,
    server_service: ServerService,
) -> dict[str, Any]:
    """Uninstall agent from a server.

    Stops and removes the agent container via SSH, then removes
    the agent record from the database. Works even if no DB record
    exists (cleans up orphaned containers).

    Args:
        server_id: Server identifier to uninstall agent from.
        agent_service: Service for agent lifecycle operations.
        agent_manager: Manager for active agent connections.
        ssh_service: Service for SSH command execution.
        server_service: Service for server management.

    Returns:
        Dict containing success status of the uninstallation.
    """
    server_name = None  # Track for error logging
    try:
        # Get agent record if exists (may be None for orphaned containers)
        agent = await agent_service.get_agent_by_server(server_id)

        # Disconnect WebSocket if connected
        if agent and agent_manager.is_connected(agent.id):
            await agent_manager.unregister_connection(agent.id)

        # Get server and credentials for SSH
        server = await server_service.get_server(server_id)
        if server:
            server_name = server.name
        if not server:
            await log_event(
                "agent",
                "ERROR",
                "Agent uninstall failed: server not found",
                AGENT_TAGS,
                {
                    "server_id": server_id,
                    "agent_id": agent.id if agent else None,
                    "error": "SERVER_NOT_FOUND",
                },
            )
            return {
                "success": False,
                "message": "Server not found",
                "error": "SERVER_NOT_FOUND",
            }

        credentials = await server_service.get_credentials(server_id)
        if not credentials:
            await log_event(
                "agent",
                "ERROR",
                f"Agent uninstall failed: credentials not found for '{server.name}'",
                AGENT_TAGS,
                {
                    "server_id": server_id,
                    "server_name": server.name,
                    "agent_id": agent.id if agent else None,
                    "error": "CREDENTIALS_NOT_FOUND",
                },
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
        success, output = await ssh_service.execute_command(
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
            deleted = await agent_service.delete_agent(agent.id)
            if not deleted:
                logger.warning(
                    "Failed to delete agent record",
                    agent_id=agent.id,
                    server_id=server_id,
                )

        # Update server system_info to reflect agent is no longer running
        if server.system_info:
            updated_info = (
                dict(server.system_info)
                if hasattr(server.system_info, "__iter__")
                else {}
            )
            if hasattr(server.system_info, "model_dump"):
                updated_info = server.system_info.model_dump()
            updated_info["agent_status"] = "not running"
            updated_info["agent_version"] = ""
            await server_service.update_server_system_info(
                server_id, updated_info
            )

        await log_event(
            "agent",
            "INFO",
            f"Agent uninstalled from server: {server.name}",
            AGENT_TAGS,
            {
                "agent_id": agent_id,
                "server_id": server_id,
                "server_name": server.name,
            },
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


async def rotate_agent_token(
    server_id: str,
    agent_service: AgentService,
    agent_manager: AgentManager,
) -> dict[str, Any]:
    """Rotate an agent's authentication token.

    Generates a new token for the agent and sends it via WebSocket.
    The agent will save the new token and use it for future auth.
    Both old and new tokens are valid during the grace period.

    Args:
        server_id: Server identifier to rotate agent token for.
        agent_service: Service for agent lifecycle operations.
        agent_manager: Manager for active agent connections.

    Returns:
        Dict containing success status and rotation details.
    """
    try:
        agent = await agent_service.get_agent_by_server(server_id)

        if not agent:
            return {
                "success": False,
                "message": "No agent found for server",
                "error": "AGENT_NOT_FOUND",
            }

        # Agent must be connected to receive the new token
        if not agent_manager.is_connected(agent.id):
            return {
                "success": False,
                "message": "Agent must be connected to rotate token",
                "error": "AGENT_NOT_CONNECTED",
            }

        # Initiate rotation - generates pending token
        new_token = await agent_service.initiate_rotation(agent.id)
        if not new_token:
            return {
                "success": False,
                "message": "Failed to initiate token rotation",
                "error": "ROTATION_INIT_FAILED",
            }

        # Get grace period from settings
        _, grace_minutes = await agent_service.get_token_rotation_settings()
        grace_seconds = grace_minutes * 60

        # Send new token to agent via WebSocket
        try:
            await agent_manager.send_command(
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
            await agent_service.cancel_rotation(agent.id)
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


