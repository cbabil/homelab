"""
App Deployment Service

Handles Docker container deployment and management on remote servers.
"""

import uuid
from datetime import datetime, UTC
from typing import Dict, Any, Optional, List
import structlog
from models.app_catalog import (
    AppDefinition, InstallationStatus, InstalledApp
)

logger = structlog.get_logger("deployment_service")


class DeploymentService:
    """Service for deploying apps to servers."""

    def __init__(self, ssh_service, server_service, catalog_service, db_service):
        """Initialize deployment service."""
        self.ssh_service = ssh_service
        self.server_service = server_service
        self.catalog_service = catalog_service
        self.db_service = db_service
        logger.info("Deployment service initialized")

    def _build_docker_run_command(
        self,
        app: AppDefinition,
        container_name: str,
        config: Dict[str, Any]
    ) -> str:
        """Build docker run command for an app."""
        parts = ["docker run -d"]

        # Container name
        parts.append(f"--name {container_name}")

        # Restart policy
        parts.append(f"--restart {app.restart_policy}")

        # Port mappings
        for port in app.ports:
            host_port = config.get("ports", {}).get(str(port.container), port.host)
            parts.append(f"-p {host_port}:{port.container}/{port.protocol}")

        # Volume mappings
        for volume in app.volumes:
            host_path = config.get("volumes", {}).get(volume.container_path, volume.host_path)
            ro = ":ro" if volume.readonly else ""
            parts.append(f"-v {host_path}:{volume.container_path}{ro}")

        # Environment variables from config
        for key, value in config.get("env", {}).items():
            parts.append(f"-e {key}={value}")

        # Network mode
        if app.network_mode:
            parts.append(f"--network {app.network_mode}")

        # Privileged mode
        if app.privileged:
            parts.append("--privileged")

        # Capabilities
        for cap in app.capabilities:
            parts.append(f"--cap-add {cap}")

        # Image
        parts.append(app.image)

        return " ".join(parts)

    async def install_app(
        self,
        server_id: str,
        app_id: str,
        config: Dict[str, Any] = None
    ) -> Optional[InstalledApp]:
        """Install an app on a server."""
        config = config or {}

        try:
            # Get app definition
            app = self.catalog_service.get_app(app_id)
            if not app:
                logger.error("App not found", app_id=app_id)
                return None

            # Get server
            server = await self.server_service.get_server(server_id)
            if not server:
                logger.error("Server not found", server_id=server_id)
                return None

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
                installed_at=now
            )

            # Pull image
            await self.db_service.update_installation(
                install_id, status=InstallationStatus.PULLING.value
            )
            pull_cmd = f"docker pull {app.image}"
            exit_code, stdout, stderr = await self.ssh_service.execute_command(
                server_id, pull_cmd
            )
            if exit_code != 0:
                await self.db_service.update_installation(
                    install_id,
                    status=InstallationStatus.ERROR.value,
                    error_message=f"Failed to pull image: {stderr}"
                )
                return None

            # Run container
            await self.db_service.update_installation(
                install_id, status=InstallationStatus.CREATING.value
            )
            run_cmd = self._build_docker_run_command(app, container_name, config)
            exit_code, stdout, stderr = await self.ssh_service.execute_command(
                server_id, run_cmd
            )
            if exit_code != 0:
                await self.db_service.update_installation(
                    install_id,
                    status=InstallationStatus.ERROR.value,
                    error_message=f"Failed to create container: {stderr}"
                )
                return None

            # Get container ID
            container_id = stdout.strip()
            await self.db_service.update_installation(
                install_id,
                status=InstallationStatus.RUNNING.value,
                container_id=container_id,
                started_at=datetime.now(UTC).isoformat()
            )

            logger.info("App installed", app_id=app_id, server_id=server_id, container=container_name)
            return installation

        except Exception as e:
            logger.error("Install failed", error=str(e))
            return None

    async def uninstall_app(
        self,
        server_id: str,
        app_id: str,
        remove_data: bool = False
    ) -> bool:
        """Uninstall an app from a server."""
        try:
            installation = await self.db_service.get_installation(server_id, app_id)
            if not installation:
                logger.error("Installation not found", server_id=server_id, app_id=app_id)
                return False

            container_name = installation.container_name

            # Stop container
            stop_cmd = f"docker stop {container_name}"
            await self.ssh_service.execute_command(server_id, stop_cmd)

            # Remove container
            rm_cmd = f"docker rm {container_name}"
            if remove_data:
                rm_cmd += " -v"  # Remove volumes too
            await self.ssh_service.execute_command(server_id, rm_cmd)

            # Delete installation record
            await self.db_service.delete_installation(server_id, app_id)

            logger.info("App uninstalled", app_id=app_id, server_id=server_id)
            return True

        except Exception as e:
            logger.error("Uninstall failed", error=str(e))
            return False

    async def start_app(self, server_id: str, app_id: str) -> bool:
        """Start a stopped app."""
        try:
            installation = await self.db_service.get_installation(server_id, app_id)
            if not installation:
                return False

            cmd = f"docker start {installation.container_name}"
            exit_code, _, _ = await self.ssh_service.execute_command(server_id, cmd)

            if exit_code == 0:
                await self.db_service.update_installation(
                    installation.id,
                    status=InstallationStatus.RUNNING.value,
                    started_at=datetime.now(UTC).isoformat()
                )
                return True
            return False

        except Exception as e:
            logger.error("Start app failed", error=str(e))
            return False

    async def stop_app(self, server_id: str, app_id: str) -> bool:
        """Stop a running app."""
        try:
            installation = await self.db_service.get_installation(server_id, app_id)
            if not installation:
                return False

            cmd = f"docker stop {installation.container_name}"
            exit_code, _, _ = await self.ssh_service.execute_command(server_id, cmd)

            if exit_code == 0:
                await self.db_service.update_installation(
                    installation.id,
                    status=InstallationStatus.STOPPED.value
                )
                return True
            return False

        except Exception as e:
            logger.error("Stop app failed", error=str(e))
            return False

    async def get_app_status(self, server_id: str, app_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of an installed app."""
        try:
            installation = await self.db_service.get_installation(server_id, app_id)
            if not installation:
                return None

            # Check actual container status
            cmd = f"docker inspect --format '{{{{.State.Status}}}}' {installation.container_name}"
            exit_code, stdout, _ = await self.ssh_service.execute_command(server_id, cmd)

            container_status = stdout.strip() if exit_code == 0 else "unknown"

            return {
                "installation_id": installation.id,
                "app_id": app_id,
                "container_name": installation.container_name,
                "container_id": installation.container_id,
                "status": container_status,
                "installed_at": installation.installed_at,
                "started_at": installation.started_at
            }

        except Exception as e:
            logger.error("Get status failed", error=str(e))
            return None

    async def get_installed_apps(self, server_id: str) -> List[Dict[str, Any]]:
        """Get all installed apps for a server."""
        try:
            installations = await self.db_service.get_installations(server_id)
            return [
                {
                    "installation_id": inst.id,
                    "app_id": inst.app_id,
                    "container_name": inst.container_name,
                    "status": inst.status,
                    "installed_at": inst.installed_at
                }
                for inst in installations
            ]
        except Exception as e:
            logger.error("Get installed apps failed", error=str(e))
            return []
