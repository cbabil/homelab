"""
Deployment Status

Status queries, health checks, and installation status management.
"""

import asyncio
import json
from typing import Any

import structlog

from services.deployment.scripts import health_check_script

logger = structlog.get_logger("deployment.status")


class StatusManager:
    """Manages deployment status queries and health checks."""

    def __init__(self, ssh_executor, db_service, server_service, marketplace_service):
        """Initialize status manager.

        Args:
            ssh_executor: SSH executor for running commands
            db_service: Database service for installation records
            server_service: Server service for server info
            marketplace_service: Marketplace service for app info
        """
        self.ssh = ssh_executor
        self.db_service = db_service
        self.server_service = server_service
        self.marketplace_service = marketplace_service

    async def get_app_status(
        self, server_id: str, app_id: str
    ) -> dict[str, Any] | None:
        """Get current status of an installed app.

        Args:
            server_id: Server where app is installed
            app_id: App ID

        Returns:
            Status dict or None if not found
        """
        try:
            installation = await self.db_service.get_installation(server_id, app_id)
            if not installation:
                return None

            # Check actual container status
            cmd = f"docker inspect --format '{{{{.State.Status}}}}' {installation.container_name}"
            exit_code, stdout, _ = await self.ssh.execute(server_id, cmd)

            container_status = stdout.strip() if exit_code == 0 else "unknown"

            return {
                "installation_id": installation.id,
                "app_id": app_id,
                "container_name": installation.container_name,
                "container_id": installation.container_id,
                "status": container_status,
                "installed_at": installation.installed_at,
                "started_at": installation.started_at,
            }

        except Exception as e:
            logger.error("Get status failed", error=str(e))
            return None

    async def get_installed_apps(self, server_id: str) -> list[dict[str, Any]]:
        """Get all installed apps for a server.

        Args:
            server_id: Server to query

        Returns:
            List of installation info dicts
        """
        try:
            installations = await self.db_service.get_installations(server_id)
            return [
                {
                    "installation_id": inst.id,
                    "app_id": inst.app_id,
                    "container_name": inst.container_name,
                    "status": inst.status,
                    "installed_at": inst.installed_at,
                }
                for inst in installations
            ]
        except Exception as e:
            logger.error("Get installed apps failed", error=str(e))
            return []

    async def get_installation_status_by_id(
        self, installation_id: str
    ) -> dict[str, Any] | None:
        """Get installation status by ID (for polling during deployment).

        Args:
            installation_id: Installation ID

        Returns:
            Status dict or None if not found
        """
        try:
            installation = await self.db_service.get_installation_by_id(installation_id)
            if not installation:
                return None

            status = installation.status
            if hasattr(status, "value"):
                status = status.value
            else:
                status = str(status)

            return {
                "id": installation.id,
                "app_id": installation.app_id,
                "server_id": installation.server_id,
                "status": status,
                "container_id": installation.container_id,
                "container_name": installation.container_name,
                "error_message": installation.error_message,
                "installed_at": installation.installed_at,
                "started_at": installation.started_at,
                "progress": getattr(installation, "progress", 0) or 0,
                "step_durations": installation.step_durations,
            }
        except Exception as e:
            logger.error("Get installation status failed", error=str(e))
            return None

    async def get_all_installations_with_details(self) -> list[dict[str, Any]]:
        """Get all installations with server and app details.

        Reads from database only - no Docker calls.

        Returns:
            List of detailed installation dicts
        """
        try:
            installations = await self.db_service.get_all_installations()
            if not installations:
                return []

            # Pre-fetch all unique servers and apps in parallel
            server_ids = list(set(inst.server_id for inst in installations))
            app_ids = list(set(inst.app_id for inst in installations))

            server_tasks = [self.server_service.get_server(sid) for sid in server_ids]
            app_tasks = [self.marketplace_service.get_app(aid) for aid in app_ids]

            servers_list, apps_list = await asyncio.gather(
                asyncio.gather(*server_tasks), asyncio.gather(*app_tasks)
            )

            servers_map = {sid: server for sid, server in zip(server_ids, servers_list, strict=True)}
            apps_map = {aid: app for aid, app in zip(app_ids, apps_list, strict=True)}

            # Pre-fetch repo info
            repo_ids = list(
                set(
                    app.repo_id
                    for app in apps_map.values()
                    if app and hasattr(app, "repo_id") and app.repo_id
                )
            )
            if repo_ids:
                repo_tasks = [
                    self.marketplace_service.get_repo(rid) for rid in repo_ids
                ]
                repos_list = await asyncio.gather(*repo_tasks)
                repos_map = {rid: repo for rid, repo in zip(repo_ids, repos_list, strict=True)}
            else:
                repos_map = {}

            # Build result list
            result = []
            for inst in installations:
                server = servers_map.get(inst.server_id)
                app = apps_map.get(inst.app_id)

                app_source = "Unknown"
                if app and hasattr(app, "repo_id") and app.repo_id:
                    repo = repos_map.get(app.repo_id)
                    app_source = repo.name if repo else "Unknown"

                config = inst.config or {}
                status = inst.status
                if hasattr(status, "value"):
                    status = status.value
                else:
                    status = str(status)

                result.append(
                    {
                        "id": inst.id,
                        "app_id": inst.app_id,
                        "app_name": app.name if app else inst.app_id,
                        "app_icon": app.icon if app else None,
                        "app_version": app.version if app else "Unknown",
                        "app_description": app.description if app else "",
                        "app_category": app.category if app else "Unknown",
                        "app_source": app_source,
                        "server_id": inst.server_id,
                        "server_name": server.name if server else "Unknown",
                        "server_host": server.host if server else "",
                        "container_id": inst.container_id,
                        "container_name": inst.container_name,
                        "status": status,
                        "ports": config.get("ports", {}),
                        "env": config.get("env", {}),
                        "volumes": config.get("volumes", {}),
                        "networks": inst.networks or [],
                        "named_volumes": inst.named_volumes or [],
                        "bind_mounts": inst.bind_mounts or [],
                        "installed_at": inst.installed_at,
                        "started_at": inst.started_at,
                        "error_message": inst.error_message,
                    }
                )

            return result

        except Exception as e:
            logger.error("Get all installations with details failed", error=str(e))
            return []

    async def refresh_installation_status(
        self, install_id: str
    ) -> dict[str, Any] | None:
        """Refresh installation status from Docker and update database.

        Args:
            install_id: Installation ID

        Returns:
            Updated status dict or None
        """
        try:
            installation = await self.db_service.get_installation_by_id(install_id)
            if not installation:
                return None

            if not installation.container_name:
                status = installation.status
                if hasattr(status, "value"):
                    status = status.value
                return {"status": str(status)}

            # Get live status from Docker
            cmd = f"docker inspect {installation.container_name} 2>/dev/null"
            exit_code, stdout, _ = await self.ssh.execute(installation.server_id, cmd)

            if exit_code != 0 or not stdout.strip():
                return {"status": "stopped"}

            container_info = json.loads(stdout)
            if not container_info:
                return {"status": "stopped"}

            info = container_info[0]

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
        """Check container health comprehensively.

        Args:
            server_id: Server where container runs
            container_name: Container to check

        Returns:
            Health status dict
        """
        try:
            health = {
                "container_running": False,
                "ports_listening": [],
                "restart_count": 0,
                "recent_logs": [],
                "healthy": False,
            }

            # Use batched script for efficiency
            script = health_check_script(container_name)
            exit_code, stdout, _ = await self.ssh.execute(server_id, script, timeout=30)

            # Parse output
            lines = stdout.split("\n")
            in_logs = False
            logs = []

            for line in lines:
                if line.startswith("STATUS:"):
                    status = line[7:].strip()
                    health["container_running"] = status == "running"
                    health["container_status"] = status
                elif line.startswith("RESTARTS:"):
                    try:
                        health["restart_count"] = int(line[9:].strip())
                    except ValueError:
                        pass
                elif line.startswith("PORTS:"):
                    ports = line[6:].strip()
                    if ports:
                        health["ports_listening"] = [
                            p.strip() for p in ports.split("\n") if p.strip()
                        ]
                elif line == "LOGS_START":
                    in_logs = True
                elif line == "LOGS_END":
                    in_logs = False
                elif in_logs:
                    logs.append(line)

            health["recent_logs"] = logs[-20:]

            # Determine overall health
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
        """Get recent logs from a container.

        Args:
            server_id: Server where container runs
            container_name: Container to get logs from
            tail: Number of lines to return

        Returns:
            Dict with logs array and metadata
        """
        try:
            cmd = f"docker logs --tail {tail} --timestamps {container_name} 2>&1"
            exit_code, stdout, stderr = await self.ssh.execute(
                server_id, cmd, timeout=30
            )

            if exit_code != 0:
                # Check if container exists
                check_cmd = (
                    f"docker ps -a --filter name=^{container_name}$ "
                    "--format '{{.Names}}'"
                )
                _, check_out, _ = await self.ssh.execute(server_id, check_cmd)
                if not check_out.strip():
                    return {
                        "logs": [],
                        "error": f"Container '{container_name}' not found",
                    }
                return {"logs": [], "error": stderr or "Failed to get logs"}

            # Parse log lines
            logs = []
            for line in stdout.strip().split("\n"):
                if line:
                    parts = line.split(" ", 1)
                    if len(parts) == 2 and "T" in parts[0] and "Z" in parts[0]:
                        logs.append({"timestamp": parts[0], "message": parts[1]})
                    else:
                        logs.append({"timestamp": None, "message": line})

            return {
                "logs": logs,
                "container_name": container_name,
                "line_count": len(logs),
            }

        except Exception as e:
            logger.error(
                "Get container logs failed", error=str(e), container=container_name
            )
            return {"logs": [], "error": str(e)}
