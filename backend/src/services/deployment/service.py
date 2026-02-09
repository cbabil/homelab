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
from services.deployment.agent_rpc import AgentRPCMixin
from services.deployment.container_ops import ContainerOpsMixin
from services.deployment.ssh_executor import SSHExecutor
from services.deployment.status import StatusManager
from services.deployment.validation import DeploymentValidator

logger = structlog.get_logger("deployment")


class DeploymentError(Exception):
    """Exception raised when deployment fails."""

    pass


class DeploymentService(AgentRPCMixin, ContainerOpsMixin):
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
            await self._prepare_app_volumes(server_id, app_id, app)

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
                        logger.debug(
                            "Failed to remove image during cleanup", error=str(exc)
                        )

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

    # -------------------------------------------------------------------------
    # Private Helpers
    # -------------------------------------------------------------------------

    async def _prepare_app_volumes(self, server_id: str, app_id: str, app) -> None:
        """Prepare volume directories with correct ownership.

        Normalizes paths to use allowed data directories for security.

        Args:
            server_id: Target server ID
            app_id: App identifier for path normalization
            app: App object with docker volume configuration
        """
        if not app.docker.volumes:
            return

        logger.info("Preparing volume directories", volumes=len(app.docker.volumes))
        volume_configs = []
        for v in app.docker.volumes:
            host_path = v.host_path
            # Normalize paths to allowed directories
            if host_path.startswith("/"):
                # Check if already in allowed path
                if not (
                    host_path.startswith("/DATA") or host_path.startswith("/opt/tomo")
                ):
                    # Map to /DATA/AppData/<app_id>/<original_path>
                    normalized_path = f"/DATA/AppData/{app_id}{host_path}"
                    logger.info(
                        "Normalizing volume path for security",
                        original=host_path,
                        normalized=normalized_path,
                    )
                    host_path = normalized_path
                volume_configs.append({"host": host_path, "uid": 1000, "gid": 1000})

        if volume_configs:
            prep_result = await self._agent_prepare_volumes(server_id, volume_configs)
            if not prep_result["success"]:
                logger.warning(
                    "Volume preparation failed, continuing anyway",
                    error=prep_result.get("error"),
                )
            else:
                logger.info("Volume directories prepared successfully")

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
