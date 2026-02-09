"""
Agent RPC Methods

Mixin providing Docker RPC methods that communicate with remote agents
via the agent manager.
"""

from typing import Any, Protocol, runtime_checkable

import structlog

logger = structlog.get_logger("deployment")


@runtime_checkable
class _DeploymentServiceProtocol(Protocol):
    """Interface that the host class must provide for AgentRPCMixin."""

    agent_manager: Any
    agent_service: Any


class AgentRPCMixin:
    """Mixin providing agent Docker RPC methods for deployment.

    The host class must satisfy ``_DeploymentServiceProtocol``.
    """

    async def _get_agent_for_server(self, server_id: str):
        """Get connected agent for a server."""
        if not self.agent_service or not self.agent_manager:
            return None
        agent = await self.agent_service.get_agent_by_server(server_id)
        if agent and self.agent_manager.is_connected(agent.id):
            return agent
        return None

    async def _agent_pull_image(self, server_id: str, image: str) -> dict[str, Any]:
        """Pull Docker image via agent RPC.

        Args:
            server_id: Target server ID
            image: Docker image to pull (e.g., "n8nio/n8n:latest")

        Returns:
            Dict with success status and image info
        """
        agent = await self._get_agent_for_server(server_id)
        if not agent:
            return {"success": False, "error": "Agent not connected"}

        # Parse image:tag
        if ":" in image:
            img_name, tag = image.rsplit(":", 1)
        else:
            img_name, tag = image, "latest"

        try:
            result = await self.agent_manager.send_command(
                agent_id=agent.id,
                method="docker.images.pull",
                params={"image": img_name, "tag": tag},
                timeout=600,  # Image pulls can take a while
            )
            logger.info("Image pulled via agent", image=image, result=result)
            return {"success": True, "data": result}
        except Exception as e:
            logger.error("Agent image pull failed", image=image, error=str(e))
            return {"success": False, "error": str(e)}

    async def _agent_run_container(
        self,
        server_id: str,
        image: str,
        name: str,
        ports: dict[str, int] = None,
        env: dict[str, str] = None,
        volumes: list[dict[str, str]] = None,
        restart_policy: str = None,
        network_mode: str = None,
        privileged: bool = False,
        capabilities: list[str] = None,
    ) -> dict[str, Any]:
        """Run Docker container via agent RPC.

        Args:
            server_id: Target server ID
            image: Docker image to run
            name: Container name
            ports: Port mappings {host_port: container_port/protocol}
            env: Environment variables
            volumes: Volume mounts [{host: path, container: path, mode: rw/ro}]
            restart_policy: Restart policy string (e.g. "unless-stopped")
            network_mode: Docker network mode
            privileged: Run in privileged mode
            capabilities: Additional Linux capabilities

        Returns:
            Dict with success status and container info
        """
        agent = await self._get_agent_for_server(server_id)
        if not agent:
            return {"success": False, "error": "Agent not connected"}

        try:
            result = await self.agent_manager.send_command(
                agent_id=agent.id,
                method="docker.containers.run",
                params={
                    "image": image,
                    "name": name,
                    "ports": ports,
                    "env": env,
                    "volumes": volumes,
                    "restart_policy": restart_policy,
                    "network_mode": network_mode,
                    "privileged": privileged,
                    "capabilities": capabilities,
                },
                timeout=120,
            )
            logger.info("Container created via agent", name=name, result=result)
            return {"success": True, "data": result}
        except Exception as e:
            logger.error("Agent container run failed", name=name, error=str(e))
            return {"success": False, "error": str(e)}

    def _build_container_params(
        self,
        docker_config,
        container_name: str,
        user_config: dict[str, Any],
        restart_policy: str = None,
    ) -> dict[str, Any]:
        """Build container parameters from app docker config and user overrides.

        Args:
            docker_config: DockerConfig from marketplace app
            container_name: Name for the container
            user_config: User-provided configuration overrides
            restart_policy: Override restart policy (default: use docker config)

        Returns:
            Dict with all container parameters for agent RPC
        """
        # Port mappings: {host_port: "container_port/protocol"}
        ports = {}
        for port in docker_config.ports:
            host_port = user_config.get("ports", {}).get(str(port.container), port.host)
            ports[str(host_port)] = f"{port.container}/{port.protocol}"

        # Environment variables from user config
        env = user_config.get("env", {})

        # Volume mappings
        volumes = []
        for volume in docker_config.volumes:
            host_path = user_config.get("volumes", {}).get(
                volume.container_path, volume.host_path
            )
            volumes.append(
                {
                    "host": host_path,
                    "container": volume.container_path,
                    "mode": "ro" if volume.readonly else "rw",
                }
            )

        # Restart policy - use override or default from config
        policy = (
            restart_policy
            if restart_policy is not None
            else docker_config.restart_policy
        )

        return {
            "image": docker_config.image,
            "name": container_name,
            "ports": ports,
            "env": env,
            "volumes": volumes,
            "restart_policy": policy,
            "network_mode": docker_config.network_mode,
            "privileged": docker_config.privileged,
            "capabilities": docker_config.capabilities,
        }

    def _parse_agent_inspect_result(self, data: dict[str, Any]) -> dict[str, Any]:
        """Parse agent container inspect result.

        Args:
            data: Raw inspect data from agent

        Returns:
            Dict with networks, named_volumes, and bind_mounts
        """
        result = {"networks": [], "named_volumes": [], "bind_mounts": []}

        try:
            # Handle case where agent returns inspect data directly
            # or wrapped in container info
            info = data if isinstance(data, dict) else {}
            if isinstance(data, list) and data:
                info = data[0]

            # Get networks
            network_settings = info.get("NetworkSettings", {}).get("Networks", {})
            if not network_settings:
                network_settings = info.get("networks", {})
            result["networks"] = list(network_settings.keys())

            # Get mounts
            mounts = info.get("Mounts", []) or info.get("mounts", [])
            for mount in mounts:
                mount_type = mount.get("Type", "") or mount.get("type", "")
                if mount_type == "volume":
                    result["named_volumes"].append(
                        {
                            "name": mount.get("Name", "") or mount.get("name", ""),
                            "destination": mount.get("Destination", "")
                            or mount.get("destination", ""),
                            "mode": mount.get("Mode", "rw") or mount.get("mode", "rw"),
                        }
                    )
                elif mount_type == "bind":
                    result["bind_mounts"].append(
                        {
                            "source": mount.get("Source", "")
                            or mount.get("source", ""),
                            "destination": mount.get("Destination", "")
                            or mount.get("destination", ""),
                            "mode": mount.get("Mode", "rw") or mount.get("mode", "rw"),
                        }
                    )

        except Exception as exc:
            logger.debug("Failed to parse agent inspect result", error=str(exc))

        return result

    async def _agent_stop_container(self, server_id: str, name: str) -> dict[str, Any]:
        """Stop container via agent RPC."""
        agent = await self._get_agent_for_server(server_id)
        if not agent:
            return {"success": False, "error": "Agent not connected"}

        try:
            result = await self.agent_manager.send_command(
                agent_id=agent.id,
                method="docker.containers.stop",
                params={"container": name},
                timeout=30,
            )
            return {"success": True, "data": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _agent_remove_container(
        self, server_id: str, name: str, force: bool = False
    ) -> dict[str, Any]:
        """Remove container via agent RPC."""
        agent = await self._get_agent_for_server(server_id)
        if not agent:
            return {"success": False, "error": "Agent not connected"}

        try:
            result = await self.agent_manager.send_command(
                agent_id=agent.id,
                method="docker.containers.remove",
                params={"container": name, "force": force},
                timeout=30,
            )
            return {"success": True, "data": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _agent_update_restart_policy(
        self, server_id: str, name: str, policy: str
    ) -> dict[str, Any]:
        """Update container restart policy via agent RPC."""
        agent = await self._get_agent_for_server(server_id)
        if not agent:
            return {"success": False, "error": "Agent not connected"}

        try:
            result = await self.agent_manager.send_command(
                agent_id=agent.id,
                method="docker.containers.update",
                params={"container": name, "restart_policy": policy},
                timeout=30,
            )
            return {"success": True, "data": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _agent_inspect_container(
        self, server_id: str, name: str
    ) -> dict[str, Any]:
        """Inspect container via agent RPC."""
        agent = await self._get_agent_for_server(server_id)
        if not agent:
            return {"success": False, "error": "Agent not connected"}

        try:
            result = await self.agent_manager.send_command(
                agent_id=agent.id,
                method="docker.containers.inspect",
                params={"container": name},
                timeout=30,
            )
            return {"success": True, "data": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _agent_get_container_status(
        self, server_id: str, container_id: str
    ) -> dict[str, Any]:
        """Get container status via agent RPC.

        Returns:
            Dict with status, health, restart_count, logs
        """
        agent = await self._get_agent_for_server(server_id)
        if not agent:
            return {"success": False, "error": "Agent not connected"}

        try:
            result = await self.agent_manager.send_command(
                agent_id=agent.id,
                method="docker.containers.status",
                params={"container": container_id, "include_logs": True},
                timeout=30,
            )
            return {"success": True, "data": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _agent_get_container_logs(
        self, server_id: str, name: str, tail: int = 50
    ) -> dict[str, Any]:
        """Get container logs via agent RPC."""
        agent = await self._get_agent_for_server(server_id)
        if not agent:
            return {"success": False, "error": "Agent not connected"}

        try:
            result = await self.agent_manager.send_command(
                agent_id=agent.id,
                method="docker.containers.logs",
                params={"container": name, "tail": tail},
                timeout=30,
            )
            return {"success": True, "data": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _agent_preflight_check(
        self, server_id: str, min_disk_gb: int = 3, min_memory_mb: int = 256
    ) -> dict[str, Any]:
        """Run preflight checks via agent RPC.

        Args:
            server_id: Target server ID
            min_disk_gb: Minimum required disk space
            min_memory_mb: Minimum required free memory

        Returns:
            Dict with success status and details
        """
        agent = await self._get_agent_for_server(server_id)
        if not agent:
            return {"success": False, "errors": ["Agent not connected"]}

        try:
            result = await self.agent_manager.send_command(
                agent_id=agent.id,
                method="system.preflight_check",
                params={"min_disk_gb": min_disk_gb, "min_memory_mb": min_memory_mb},
                timeout=30,
            )
            return result
        except Exception as e:
            return {"success": False, "errors": [str(e)]}

    async def _agent_prepare_volumes(
        self,
        server_id: str,
        volumes: list[dict[str, Any]],
        default_uid: int = 1000,
        default_gid: int = 1000,
    ) -> dict[str, Any]:
        """Prepare volume directories with correct ownership via agent.

        Args:
            server_id: Target server
            volumes: List of volume configs with 'host' paths
            default_uid: Default UID for ownership
            default_gid: Default GID for ownership

        Returns:
            Dict with success status and details
        """
        agent = await self._get_agent_for_server(server_id)
        if not agent:
            return {"success": False, "error": "Agent not connected"}

        # Convert volume format for agent
        agent_volumes = []
        for vol in volumes:
            host_path = vol.get("host", "")
            if host_path and host_path.startswith("/"):
                agent_volumes.append(
                    {
                        "host": host_path,
                        "uid": vol.get("uid", default_uid),
                        "gid": vol.get("gid", default_gid),
                    }
                )

        if not agent_volumes:
            return {
                "success": True,
                "results": [],
                "message": "No bind mounts to prepare",
            }

        try:
            result = await self.agent_manager.send_command(
                agent_id=agent.id,
                method="system.prepare_volumes",
                params={
                    "volumes": agent_volumes,
                    "default_uid": default_uid,
                    "default_gid": default_gid,
                },
                timeout=60,
            )
            return {"success": result.get("success", False), "data": result}
        except Exception as e:
            logger.error("Failed to prepare volumes", error=str(e))
            return {"success": False, "error": str(e)}
