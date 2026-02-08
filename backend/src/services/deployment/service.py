"""
Deployment Service

Main orchestration service for app deployments.
"""

import asyncio
import json
import uuid
from datetime import UTC, datetime
from typing import Any

import structlog

from models.app_catalog import InstallationStatus, InstalledApp
from models.metrics import ActivityType
from services.deployment.ssh_executor import SSHExecutor
from services.deployment.status import StatusManager
from services.deployment.validation import DeploymentValidator

logger = structlog.get_logger("deployment")


class DeploymentError(Exception):
    """Exception raised when deployment fails."""

    pass


class DeploymentService:
    """Service for deploying apps to servers."""

    def __init__(
        self,
        ssh_service: Any,
        server_service: Any,
        marketplace_service: Any,
        db_service: Any,
        activity_service: Any | None = None,
        executor: SSHExecutor | None = None,
        agent_manager: Any | None = None,
        agent_service: Any | None = None,
    ):
        """Initialize deployment service.

        Args:
            ssh_service: SSH service for command execution
            server_service: Server service for server info/credentials
            marketplace_service: Marketplace service for app definitions
            db_service: Database service for installation records
            activity_service: Optional activity logging service
            executor: Optional command executor (SSHExecutor or RoutedSSHExecutor).
                      If not provided, falls back to direct SSH.
            agent_manager: Agent manager for Docker RPC calls
            agent_service: Agent service to get agent by server
        """
        self.ssh_service = ssh_service
        self.server_service = server_service
        self.marketplace_service = marketplace_service
        self.db_service = db_service
        self.activity_service = activity_service
        self.agent_manager = agent_manager
        self.agent_service = agent_service

        # Use provided executor or fall back to direct SSH
        self.ssh = executor or SSHExecutor(ssh_service, server_service)
        self.validator = DeploymentValidator(
            self.ssh, marketplace_service, server_service
        )
        self.status_manager = StatusManager(
            self.ssh, db_service, server_service, marketplace_service
        )

        logger.info("Deployment service initialized")

    # -------------------------------------------------------------------------
    # Agent Docker RPC Methods
    # -------------------------------------------------------------------------

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

    # -------------------------------------------------------------------------
    # Installation Operations
    # -------------------------------------------------------------------------

    async def install_app(
        self, server_id: str, app_id: str, config: dict[str, Any] = None
    ) -> InstalledApp | None:
        """Install an app on a server.

        Args:
            server_id: Target server ID
            app_id: App to install
            config: User-provided configuration

        Returns:
            InstalledApp record or raises DeploymentError
        """
        config = config or {}

        try:
            # Get app and server
            app = await self.marketplace_service.get_app(app_id)
            if not app:
                raise DeploymentError(f"App '{app_id}' not found in marketplace")

            server = await self.server_service.get_server(server_id)
            if not server:
                raise DeploymentError(f"Server '{server_id}' not found")

            # Log deployment started
            await self._log_activity(
                ActivityType.APP_DEPLOYMENT_STARTED,
                f"Started deploying {app.name} to {server.name}",
                server_id,
                app_id,
                {"app_name": app.name, "server_name": server.name},
            )

            # Clean up existing installation if any
            existing = await self.db_service.get_installation(server_id, app_id)
            original_installed_at = None
            if existing:
                original_installed_at = existing.installed_at
                logger.info(
                    "Cleaning up existing installation",
                    install_id=existing.id,
                    container=existing.container_name,
                )
                if existing.container_name:
                    await self._cleanup_container(server_id, existing.container_name)
                await self.db_service.delete_installation(server_id, app_id)

            # Create installation record
            install_id = f"inst-{uuid.uuid4().hex[:8]}"
            container_name = f"{app_id}-{install_id[-4:]}"
            now = datetime.now(UTC).isoformat()

            installation = await self.db_service.create_installation(
                id=install_id,
                server_id=server_id,
                app_id=app_id,
                container_name=container_name,
                status=InstallationStatus.PENDING.value,
                config=config,
                installed_at=original_installed_at or now,
            )

            if not installation:
                raise DeploymentError("Failed to create installation record")

            # Pre-flight checks via agent (disk space, memory, docker daemon)
            preflight_result = await self._agent_preflight_check(
                server_id, min_disk_gb=3, min_memory_mb=256
            )
            if not preflight_result.get("success", False):
                errors = preflight_result.get("errors", ["Unknown error"])
                error_msg = "; ".join(errors)
                await self._handle_install_error(
                    install_id, error_msg, 0, app.name, server_id, app_id
                )
                raise DeploymentError(f"Pre-flight check failed: {error_msg}")

            # Pull image via agent Docker RPC
            pulling_started = datetime.now(UTC)
            await self.db_service.update_installation(
                install_id,
                status=InstallationStatus.PULLING.value,
                progress=0,
                step_started_at=pulling_started.isoformat(),
            )

            logger.info("Pulling image via agent", image=app.docker.image)
            pull_result = await self._agent_pull_image(server_id, app.docker.image)

            if not pull_result["success"]:
                error_msg = (
                    f"Failed to pull image: {pull_result.get('error', 'Unknown error')}"
                )
                await self._handle_install_error(
                    install_id, error_msg, 0, app.name, server_id, app_id
                )
                raise DeploymentError(error_msg)

            logger.info("Image pulled successfully", image=app.docker.image)
            await self.db_service.update_installation(install_id, progress=100)

            # Prepare volume directories with correct ownership
            # Normalize paths to use allowed data directories for security
            if app.docker.volumes:
                logger.info(
                    "Preparing volume directories", volumes=len(app.docker.volumes)
                )
                volume_configs = []
                for v in app.docker.volumes:
                    host_path = v.host_path
                    # Normalize paths to allowed directories
                    if host_path.startswith("/"):
                        # Check if already in allowed path
                        if not (
                            host_path.startswith("/DATA")
                            or host_path.startswith("/opt/tomo")
                        ):
                            # Map to /DATA/AppData/<app_id>/<original_path>
                            normalized_path = f"/DATA/AppData/{app_id}{host_path}"
                            logger.info(
                                "Normalizing volume path for security",
                                original=host_path,
                                normalized=normalized_path,
                            )
                            host_path = normalized_path
                        volume_configs.append(
                            {"host": host_path, "uid": 1000, "gid": 1000}
                        )

                if volume_configs:
                    prep_result = await self._agent_prepare_volumes(
                        server_id, volume_configs
                    )
                    if not prep_result["success"]:
                        logger.warning(
                            "Volume preparation failed, continuing anyway",
                            error=prep_result.get("error"),
                        )
                    else:
                        logger.info("Volume directories prepared successfully")

            # Create container
            creating_started = datetime.now(UTC)
            pulling_duration = int((creating_started - pulling_started).total_seconds())
            await self.db_service.update_installation(
                install_id,
                status=InstallationStatus.CREATING.value,
                progress=0,
                step_started_at=creating_started.isoformat(),
                step_durations=json.dumps({"pulling": pulling_duration}),
            )

            # Build container params from app config and user overrides
            # Start with restart=no to prevent crash loops during startup
            container_params = self._build_container_params(
                app.docker, container_name, config, restart_policy="no"
            )

            # Create container via agent RPC
            logger.info("Creating container via agent", name=container_name)
            run_result = await self._agent_run_container(
                server_id=server_id,
                image=container_params["image"],
                name=container_params["name"],
                ports=container_params["ports"],
                env=container_params["env"],
                volumes=container_params["volumes"],
                restart_policy=container_params["restart_policy"],
                network_mode=container_params["network_mode"],
                privileged=container_params["privileged"],
                capabilities=container_params["capabilities"],
            )

            if not run_result["success"]:
                error_msg = f"Failed to create container: {run_result.get('error', 'Unknown error')}"
                await self._handle_install_error(
                    install_id, error_msg, 0, app.name, server_id, app_id
                )
                raise DeploymentError(error_msg)

            # Extract container ID from result
            container_id = run_result.get("data", {}).get("container_id", "")
            if not container_id:
                # Try alternate key names
                container_id = run_result.get("data", {}).get("id", "")
            if not container_id:
                container_id = container_name  # Fallback to name

            # Wait for container to start
            starting_started = datetime.now(UTC)
            creating_duration = int(
                (starting_started - creating_started).total_seconds()
            )
            await self.db_service.update_installation(
                install_id,
                status=InstallationStatus.STARTING.value,
                container_id=container_id,
                progress=0,
                step_started_at=starting_started.isoformat(),
                step_durations=json.dumps(
                    {"pulling": pulling_duration, "creating": creating_duration}
                ),
            )

            # Poll for ready status
            await self._wait_for_container(
                server_id,
                container_id,
                container_name,
                install_id,
                app.name,
                app_id,
                app.docker.image,
            )

            # Container is healthy - now enable the real restart policy
            if app.docker.restart_policy and app.docker.restart_policy != "no":
                update_result = await self._agent_update_restart_policy(
                    server_id, container_name, app.docker.restart_policy
                )
                if update_result["success"]:
                    logger.info(
                        "Enabled restart policy", policy=app.docker.restart_policy
                    )
                else:
                    logger.warning(
                        "Failed to update restart policy",
                        error=update_result.get("error"),
                    )

            # Get final container details via agent
            running_at = datetime.now(UTC)
            starting_duration = int((running_at - starting_started).total_seconds())

            details = {"networks": [], "named_volumes": [], "bind_mounts": []}
            inspect_result = await self._agent_inspect_container(
                server_id, container_name
            )
            if inspect_result["success"] and inspect_result.get("data"):
                details = self._parse_agent_inspect_result(inspect_result["data"])

            await self.db_service.update_installation(
                install_id,
                status=InstallationStatus.RUNNING.value,
                started_at=running_at.isoformat(),
                progress=100,
                step_durations=json.dumps(
                    {
                        "pulling": pulling_duration,
                        "creating": creating_duration,
                        "starting": starting_duration,
                    }
                ),
                networks=json.dumps(details["networks"]),
                named_volumes=json.dumps(details["named_volumes"]),
                bind_mounts=json.dumps(details["bind_mounts"]),
            )

            logger.info("App installed", app_id=app_id, server_id=server_id)

            await self._log_activity(
                ActivityType.APP_INSTALLED,
                f"Successfully deployed {app.name} to {server.name}",
                server_id,
                app_id,
                {
                    "app_name": app.name,
                    "server_name": server.name,
                    "container": container_name,
                },
            )

            return installation

        except DeploymentError:
            raise
        except Exception as e:
            logger.error("Install failed", error=str(e))
            await self._log_activity(
                ActivityType.APP_DEPLOYMENT_FAILED,
                f"Deployment failed: {str(e)}",
                server_id,
                app_id,
                {"error": str(e)},
            )
            raise DeploymentError(f"Deployment failed: {str(e)}") from e

    async def uninstall_app(
        self, server_id: str, app_id: str, remove_data: bool = True
    ) -> bool:
        """Uninstall an app from a server.

        Uses a single SSH connection with batched script.

        Args:
            server_id: Server where app is installed
            app_id: App to uninstall
            remove_data: Whether to remove volumes

        Returns:
            True if successful
        """
        try:
            installation = await self.db_service.get_installation(server_id, app_id)
            if not installation:
                logger.error(
                    "Installation not found", server_id=server_id, app_id=app_id
                )
                return False

            container_name = installation.container_name
            cleanup_summary = {"container": container_name, "removed": []}

            # Stop and remove container via agent RPC
            logger.info("Uninstalling app via agent", container=container_name)

            # Stop container
            stop_result = await self._agent_stop_container(server_id, container_name)
            if stop_result["success"]:
                cleanup_summary["removed"].append("container_stopped")

            # Remove container
            remove_result = await self._agent_remove_container(
                server_id, container_name, force=True
            )
            if remove_result["success"]:
                cleanup_summary["removed"].append(f"container:{container_name}")

            # Remove volumes if requested
            if remove_data:
                agent = await self._get_agent_for_server(server_id)
                if agent:
                    try:
                        # Remove volumes associated with the container
                        await self.agent_manager.send_command(
                            agent_id=agent.id,
                            method="docker.volumes.prune",
                            params={"filter": f"label=container={container_name}"},
                            timeout=60,
                        )
                        cleanup_summary["removed"].append("volumes")
                    except Exception as e:
                        logger.warning("Volume cleanup failed", error=str(e))

            # Delete database record
            await self.db_service.delete_installation(server_id, app_id)
            cleanup_summary["removed"].append("database_record")

            logger.info("App fully uninstalled", app_id=app_id, server_id=server_id)

            await self._log_activity(
                ActivityType.APP_UNINSTALLED,
                f"Uninstalled app {app_id}",
                server_id,
                app_id,
                cleanup_summary,
            )

            return True

        except Exception as e:
            logger.error("Uninstall failed", error=str(e))
            return False

    async def start_app(self, server_id: str, app_id: str) -> bool:
        """Start a stopped app via agent RPC."""
        try:
            installation = await self.db_service.get_installation(server_id, app_id)
            if not installation:
                return False

            agent = await self._get_agent_for_server(server_id)
            if not agent:
                logger.error("Agent not connected", server_id=server_id)
                return False

            result = await self.agent_manager.send_command(
                agent_id=agent.id,
                method="docker.containers.start",
                params={"container": installation.container_name},
                timeout=30,
            )

            if result:
                await self.db_service.update_installation(
                    installation.id,
                    status=InstallationStatus.RUNNING.value,
                    started_at=datetime.now(UTC).isoformat(),
                )
                return True
            return False

        except Exception as e:
            logger.error("Start app failed", error=str(e))
            return False

    async def stop_app(self, server_id: str, app_id: str) -> bool:
        """Stop a running app via agent RPC."""
        try:
            installation = await self.db_service.get_installation(server_id, app_id)
            if not installation:
                return False

            result = await self._agent_stop_container(
                server_id, installation.container_name
            )

            if result["success"]:
                await self.db_service.update_installation(
                    installation.id, status=InstallationStatus.STOPPED.value
                )
                return True
            return False

        except Exception as e:
            logger.error("Stop app failed", error=str(e))
            return False

    async def cleanup_failed_deployment(
        self, server_id: str, installation_id: str
    ) -> dict[str, Any]:
        """Clean up a failed deployment via agent RPC."""
        cleanup_result = {
            "container_removed": False,
            "image_removed": False,
            "record_removed": False,
            "errors": [],
        }

        try:
            installation = await self.db_service.get_installation_by_id(installation_id)
            if not installation:
                cleanup_result["errors"].append("Installation record not found")
                return cleanup_result

            container_name = installation.container_name
            app = await self.marketplace_service.get_app(installation.app_id)
            image_name = app.docker.image if app else None

            # Remove container via agent RPC
            if container_name:
                remove_result = await self._agent_remove_container(
                    server_id, container_name, force=True
                )
                cleanup_result["container_removed"] = remove_result["success"]

            # Remove image via agent RPC
            if image_name:
                agent = await self._get_agent_for_server(server_id)
                if agent:
                    try:
                        await self.agent_manager.send_command(
                            agent_id=agent.id,
                            method="docker.images.remove",
                            params={"image": image_name, "force": True},
                            timeout=30,
                        )
                        cleanup_result["image_removed"] = True
                    except Exception as exc:
                        logger.debug("Failed to remove image during cleanup", error=str(exc))

            await self.db_service.delete_installation(server_id, installation.app_id)
            cleanup_result["record_removed"] = True

            logger.info("Cleanup completed", installation_id=installation_id)
            return cleanup_result

        except Exception as e:
            logger.error("Cleanup failed", error=str(e))
            cleanup_result["errors"].append(str(e))
            return cleanup_result

    # -------------------------------------------------------------------------
    # Delegated Methods (to sub-components)
    # -------------------------------------------------------------------------

    async def validate_deployment_config(
        self, app_id: str, config: dict[str, Any]
    ) -> dict[str, Any]:
        """Validate deployment configuration."""
        return await self.validator.validate_config(app_id, config)

    async def run_preflight_checks(
        self, server_id: str, app_id: str, config: dict[str, Any] = None
    ) -> dict[str, Any]:
        """Run pre-flight validation."""
        return await self.validator.run_preflight_checks(server_id, app_id, config)

    async def get_app_status(
        self, server_id: str, app_id: str
    ) -> dict[str, Any] | None:
        """Get current status of an installed app."""
        return await self.status_manager.get_app_status(server_id, app_id)

    async def get_installed_apps(self, server_id: str) -> list[dict[str, Any]]:
        """Get all installed apps for a server."""
        return await self.status_manager.get_installed_apps(server_id)

    async def get_installation_status_by_id(
        self, installation_id: str
    ) -> dict[str, Any] | None:
        """Get installation status by ID."""
        return await self.status_manager.get_installation_status_by_id(installation_id)

    async def get_all_installations_with_details(self) -> list[dict[str, Any]]:
        """Get all installations with details."""
        return await self.status_manager.get_all_installations_with_details()

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
            if docker_status == "running":
                new_status = "running"
            elif docker_status == "exited":
                new_status = "stopped"
            elif docker_status == "restarting":
                new_status = "error"
            elif docker_status in ["created", "paused"]:
                new_status = "stopped"
            else:
                new_status = docker_status or "stopped"

            # Get networks and mounts
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

    # -------------------------------------------------------------------------
    # Private Helpers
    # -------------------------------------------------------------------------

    async def _cleanup_container(
        self, server_id: str, container_name: str, image: str = None
    ):
        """Clean up a container via agent RPC."""
        logger.info("Cleaning up container", container_name=container_name)

        # Stop container first
        await self._agent_stop_container(server_id, container_name)

        # Remove container
        await self._agent_remove_container(server_id, container_name, force=True)

        # Remove image if specified
        if image:
            agent = await self._get_agent_for_server(server_id)
            if agent:
                try:
                    await self.agent_manager.send_command(
                        agent_id=agent.id,
                        method="docker.images.remove",
                        params={"image": image, "force": True},
                        timeout=30,
                    )
                except Exception as e:
                    logger.warning("Failed to remove image", image=image, error=str(e))

        logger.info("Container cleanup completed", container_name=container_name)

    async def _wait_for_container(
        self,
        server_id: str,
        container_id: str,
        container_name: str,
        install_id: str,
        app_name: str,
        app_id: str,
        image: str,
    ):
        """Wait for container to be running and healthy."""
        max_wait = 60
        poll_interval = 3
        elapsed = 0

        while elapsed < max_wait:
            # Get container status via agent RPC
            status_result = await self._agent_get_container_status(
                server_id, container_id
            )

            container_status = ""
            health_status = "none"
            restart_count = 0
            logs = ""

            if status_result["success"] and status_result.get("data"):
                data = status_result["data"]
                container_status = str(data.get("status", "")).lower()
                health_status = str(data.get("health", "none")).lower()
                restart_count = int(data.get("restart_count", 0))
                logs = str(data.get("logs", ""))[:200]

            # Check for restart loop (container crashed and restarted)
            if restart_count > 0:
                error_msg = (
                    f"Container crashed (restarted {restart_count}x): {logs[:200]}"
                )
                await self.db_service.update_installation(
                    install_id,
                    status=InstallationStatus.ERROR.value,
                    error_message=error_msg,
                )
                await self._cleanup_container(server_id, container_name, image)
                raise DeploymentError(error_msg)

            if container_status == "running":
                if health_status in ["healthy", "none", ""]:
                    await self.db_service.update_installation(install_id, progress=100)
                    return
                elif health_status == "starting":
                    progress = min(90, int((elapsed / max_wait) * 100))
                    await self.db_service.update_installation(
                        install_id, progress=progress
                    )
                elif health_status == "unhealthy":
                    error_msg = f"Container unhealthy: {logs[:200]}"
                    await self.db_service.update_installation(
                        install_id,
                        status=InstallationStatus.ERROR.value,
                        error_message=error_msg,
                    )
                    await self._cleanup_container(server_id, container_name, image)
                    raise DeploymentError(error_msg)

            elif container_status in ["exited", "dead", "restarting"]:
                error_msg = f"Container failed ({container_status}): {logs[:200]}"
                await self.db_service.update_installation(
                    install_id,
                    status=InstallationStatus.ERROR.value,
                    error_message=error_msg,
                )
                await self._cleanup_container(server_id, container_name, image)
                raise DeploymentError(error_msg)
            else:
                progress = min(80, int((elapsed / max_wait) * 100))
                await self.db_service.update_installation(install_id, progress=progress)

            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

    async def _handle_install_error(
        self,
        install_id: str,
        error_msg: str,
        progress: int,
        app_name: str,
        server_id: str,
        app_id: str,
    ):
        """Handle installation error."""
        await self.db_service.update_installation(
            install_id,
            status=InstallationStatus.ERROR.value,
            error_message=error_msg,
            progress=progress,
        )
        await self._log_activity(
            ActivityType.APP_DEPLOYMENT_FAILED,
            f"Failed to deploy {app_name}: {error_msg}",
            server_id,
            app_id,
            {"app_name": app_name, "error": error_msg},
        )

    async def _log_activity(
        self,
        activity_type: ActivityType,
        message: str,
        server_id: str,
        app_id: str,
        details: dict[str, Any],
    ):
        """Log activity if service is available."""
        if self.activity_service:
            try:
                await self.activity_service.log_activity(
                    activity_type=activity_type,
                    message=message,
                    server_id=server_id,
                    app_id=app_id,
                    details=details,
                )
            except Exception:
                pass  # Don't fail if logging fails
