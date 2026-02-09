"""
Container Operations

Mixin providing container health checks, log retrieval,
and installation status refresh.
"""

import json
from typing import Any, Protocol, runtime_checkable

import structlog

logger = structlog.get_logger("deployment")


@runtime_checkable
class _DeploymentServiceProtocol(Protocol):
    """Interface that the host class must provide for ContainerOpsMixin."""

    db_service: Any
    agent_manager: Any

    async def _get_agent_for_server(self, server_id: str) -> Any: ...

    async def _agent_inspect_container(
        self, server_id: str, name: str
    ) -> dict[str, Any]: ...

    async def _agent_get_container_status(
        self, server_id: str, container_id: str
    ) -> dict[str, Any]: ...


class ContainerOpsMixin:
    """Mixin providing container operation methods for deployment.

    The host class must satisfy ``_DeploymentServiceProtocol``.
    """

    async def refresh_installation_status(
        self, install_id: str
    ) -> dict[str, Any] | None:
        """Refresh installation status from Docker via agent."""
        try:
            installation = await self.db_service.get_installation_by_id(install_id)
            if not installation:
                return None

            if not installation.container_name:
                status = installation.status
                if hasattr(status, "value"):
                    status = status.value
                return {"status": str(status)}

            # Get live status from Docker via agent
            logger.info(
                "Refreshing installation status via agent",
                install_id=install_id,
                container_name=installation.container_name,
                server_id=installation.server_id,
            )
            inspect_result = await self._agent_inspect_container(
                installation.server_id, installation.container_name
            )

            if not inspect_result["success"] or not inspect_result.get("data"):
                logger.warning(
                    "Inspect failed, setting status to stopped",
                    error=inspect_result.get("error"),
                )
                # Update DB to stopped if container not found
                await self.db_service.update_installation(install_id, status="stopped")
                return {"status": "stopped"}

            info = inspect_result["data"]

            # Get status
            docker_status = info.get("State", {}).get("Status", "").lower()
            new_status = self._map_docker_status(docker_status)

            # Get networks and mounts
            networks, named_volumes, bind_mounts = self._parse_mount_info(info)

            # Update database
            await self.db_service.update_installation(
                install_id,
                status=new_status,
                networks=json.dumps(networks),
                named_volumes=json.dumps(named_volumes),
                bind_mounts=json.dumps(bind_mounts),
            )

            return {
                "status": new_status,
                "networks": networks,
                "named_volumes": named_volumes,
                "bind_mounts": bind_mounts,
            }

        except Exception as e:
            logger.error("Refresh installation status failed", error=str(e))
            return None

    def _map_docker_status(self, docker_status: str) -> str:
        """Map Docker container status to installation status.

        Args:
            docker_status: Docker status string (lowercase)

        Returns:
            Mapped installation status string
        """
        if docker_status == "running":
            return "running"
        elif docker_status == "exited":
            return "stopped"
        elif docker_status == "restarting":
            return "error"
        elif docker_status in ["created", "paused"]:
            return "stopped"
        else:
            return docker_status or "stopped"

    def _parse_mount_info(
        self, info: dict[str, Any]
    ) -> tuple[list, list[dict], list[dict]]:
        """Parse network and mount information from Docker inspect data.

        Args:
            info: Docker inspect result data

        Returns:
            Tuple of (networks, named_volumes, bind_mounts)
        """
        network_settings = info.get("NetworkSettings", {}).get("Networks", {})
        networks = list(network_settings.keys())

        named_volumes = []
        bind_mounts = []
        for mount in info.get("Mounts", []):
            mount_type = mount.get("Type", "")
            if mount_type == "volume":
                named_volumes.append(
                    {
                        "name": mount.get("Name", ""),
                        "destination": mount.get("Destination", ""),
                        "mode": mount.get("Mode", "rw"),
                    }
                )
            elif mount_type == "bind":
                bind_mounts.append(
                    {
                        "source": mount.get("Source", ""),
                        "destination": mount.get("Destination", ""),
                        "mode": mount.get("Mode", "rw"),
                    }
                )

        return networks, named_volumes, bind_mounts

    async def check_container_health(
        self, server_id: str, container_name: str
    ) -> dict[str, Any]:
        """Check container health via agent."""
        try:
            health = {
                "container_running": False,
                "ports_listening": [],
                "restart_count": 0,
                "recent_logs": [],
                "healthy": False,
            }

            # Get status via agent
            status_result = await self._agent_get_container_status(
                server_id, container_name
            )

            if status_result["success"] and status_result.get("data"):
                data = status_result["data"]
                health["container_running"] = data.get("running", False)
                health["container_status"] = data.get("status", "unknown")
                health["restart_count"] = data.get("restart_count", 0)

                if data.get("logs"):
                    health["recent_logs"] = data["logs"].split("\n")[-20:]

            # Get inspect for ports
            inspect_result = await self._agent_inspect_container(
                server_id, container_name
            )
            if inspect_result["success"] and inspect_result.get("data"):
                ports = (
                    inspect_result["data"].get("NetworkSettings", {}).get("Ports", {})
                )
                health["ports_listening"] = list(ports.keys())

            health["healthy"] = (
                health["container_running"] and health["restart_count"] < 3
            )

            return health

        except Exception as e:
            logger.error("Container health check failed", error=str(e))
            return {"healthy": False, "error": str(e)}

    async def get_container_logs(
        self, server_id: str, container_name: str, tail: int = 100
    ) -> dict[str, Any]:
        """Get container logs via agent."""
        try:
            agent = await self._get_agent_for_server(server_id)
            if not agent:
                return {"logs": [], "error": "Agent not connected"}

            result = await self.agent_manager.send_command(
                agent_id=agent.id,
                method="docker.containers.logs",
                params={"container": container_name, "tail": tail},
                timeout=30,
            )

            logs_text = result.get("logs", "")
            logs = []
            for line in logs_text.strip().split("\n"):
                if line:
                    logs.append({"timestamp": None, "message": line})

            return {
                "logs": logs,
                "container_name": container_name,
                "line_count": len(logs),
            }

        except Exception as e:
            logger.error("Get container logs failed", error=str(e))
            return {"logs": [], "error": str(e)}
