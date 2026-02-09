"""
App Deployment Tools

Provides MCP tools for deployment pipeline operations:
start/stop, installation status, validation, preflight checks,
container health, logs, and cleanup.
"""

from typing import Any

import structlog

from services.deployment import DeploymentService
from tools.common import log_event

logger = structlog.get_logger("app_deployment_tools")

APP_TAGS = ["app", "deployment"]


class DeploymentTools:
    """Deployment-related tools for app management."""

    def __init__(self, deployment_service: DeploymentService):
        """Initialize deployment tools.

        Args:
            deployment_service: Service for deployment operations.
        """
        self.deployment_service = deployment_service

    # ─────────────────────────────────────────────────────────────
    # Start / Stop
    # ─────────────────────────────────────────────────────────────

    async def start_app(self, server_id: str, app_id: str) -> dict[str, Any]:
        """Start a stopped app."""
        try:
            success = await self.deployment_service.start_app(server_id, app_id)
            if not success:
                await log_event(
                    "application",
                    "ERROR",
                    f"App start failed: {app_id}",
                    APP_TAGS,
                    {"app_id": app_id, "server_id": server_id},
                )
                return {
                    "success": False,
                    "message": "Failed to start app",
                    "error": "START_FAILED",
                }
            await log_event(
                "application",
                "INFO",
                f"App started: {app_id}",
                APP_TAGS,
                {"app_id": app_id, "server_id": server_id},
            )
            return {
                "success": True,
                "data": {"server_id": server_id, "app_id": app_id},
                "message": f"App '{app_id}' started",
            }
        except Exception as e:
            logger.error("Start app error", error=str(e))
            await log_event(
                "application",
                "ERROR",
                f"App start error: {app_id}",
                APP_TAGS,
                {"error": str(e)},
            )
            return {
                "success": False,
                "message": f"Failed to start: {str(e)}",
                "error": "START_ERROR",
            }

    async def stop_app(self, server_id: str, app_id: str) -> dict[str, Any]:
        """Stop a running app."""
        try:
            success = await self.deployment_service.stop_app(server_id, app_id)
            if not success:
                await log_event(
                    "application",
                    "ERROR",
                    f"App stop failed: {app_id}",
                    APP_TAGS,
                    {"app_id": app_id, "server_id": server_id},
                )
                return {
                    "success": False,
                    "message": "Failed to stop app",
                    "error": "STOP_FAILED",
                }
            await log_event(
                "application",
                "INFO",
                f"App stopped: {app_id}",
                APP_TAGS,
                {"app_id": app_id, "server_id": server_id},
            )
            return {
                "success": True,
                "data": {"server_id": server_id, "app_id": app_id},
                "message": f"App '{app_id}' stopped",
            }
        except Exception as e:
            logger.error("Stop app error", error=str(e))
            await log_event(
                "application",
                "ERROR",
                f"App stop error: {app_id}",
                APP_TAGS,
                {"error": str(e)},
            )
            return {
                "success": False,
                "message": f"Failed to stop: {str(e)}",
                "error": "STOP_ERROR",
            }

    # ─────────────────────────────────────────────────────────────
    # Installation Status
    # ─────────────────────────────────────────────────────────────

    async def get_installation_status(
        self, installation_id: str
    ) -> dict[str, Any]:
        """Get installation status by ID for polling during deployment.

        Args:
            installation_id: The installation ID returned from install_app

        Returns:
            Dict with installation status, progress info, and any errors
        """
        try:
            result = await self.deployment_service.get_installation_status_by_id(
                installation_id
            )
            if not result:
                return {
                    "success": False,
                    "message": f"Installation '{installation_id}' not found",
                    "error": "INSTALLATION_NOT_FOUND",
                }
            return {
                "success": True,
                "data": result,
                "message": f"Installation status: {result.get('status', 'unknown')}",
            }
        except Exception as e:
            logger.error("Get installation status error", error=str(e))
            return {
                "success": False,
                "message": f"Failed to get status: {str(e)}",
                "error": "STATUS_ERROR",
            }

    async def refresh_installation_status(
        self, installation_id: str
    ) -> dict[str, Any]:
        """Refresh installation status from Docker and update database.

        Call this to get live Docker container status when needed.

        Args:
            installation_id: The installation ID to refresh

        Returns:
            Dict with updated status and container details
        """
        try:
            result = await self.deployment_service.refresh_installation_status(
                installation_id
            )
            if not result:
                return {
                    "success": False,
                    "message": f"Installation '{installation_id}' not found",
                    "error": "INSTALLATION_NOT_FOUND",
                }
            return {
                "success": True,
                "data": result,
                "message": f"Status refreshed: {result.get('status', 'unknown')}",
            }
        except Exception as e:
            logger.error("Refresh installation status error", error=str(e))
            return {
                "success": False,
                "message": f"Failed to refresh status: {str(e)}",
                "error": "REFRESH_ERROR",
            }

    # ─────────────────────────────────────────────────────────────
    # Validation & Preflight
    # ─────────────────────────────────────────────────────────────

    async def validate_deployment_config(
        self, app_id: str, config: dict[str, Any] = None
    ) -> dict[str, Any]:
        """Validate deployment configuration before install.

        Checks required env vars, port ranges, volume paths, etc.

        Args:
            app_id: Application ID to validate config for
            config: Configuration to validate

        Returns:
            Dict with validation result and any errors
        """
        try:
            result = await self.deployment_service.validate_deployment_config(
                app_id=app_id, config=config or {}
            )
            return {
                "success": True,
                "data": result,
                "message": "Valid"
                if result.get("valid")
                else f"Validation failed: {len(result.get('errors', []))} errors",
            }
        except Exception as e:
            logger.error("Validate config error", error=str(e))
            return {
                "success": False,
                "message": f"Validation failed: {str(e)}",
                "error": "VALIDATION_ERROR",
            }

    async def run_preflight_checks(
        self, server_id: str, app_id: str, config: dict[str, Any] = None
    ) -> dict[str, Any]:
        """Run pre-flight checks before deployment.

        Checks: Docker running, disk space, port availability, architecture.

        Args:
            server_id: Server to check
            app_id: App to deploy
            config: Optional deployment config

        Returns:
            Dict with check results and pass/fail status
        """
        try:
            result = await self.deployment_service.run_preflight_checks(
                server_id=server_id, app_id=app_id, config=config
            )
            passed = result.get("passed", False)
            check_count = len(result.get("checks", []))
            return {
                "success": True,
                "data": result,
                "message": f"Pre-flight {'passed' if passed else 'failed'}: {check_count} checks run",
            }
        except Exception as e:
            logger.error("Preflight checks error", error=str(e))
            await log_event(
                "application",
                "ERROR",
                f"Preflight checks failed: {app_id}",
                APP_TAGS,
                {"server_id": server_id, "error": str(e)},
            )
            return {
                "success": False,
                "message": f"Pre-flight checks failed: {str(e)}",
                "error": "PREFLIGHT_ERROR",
            }

    # ─────────────────────────────────────────────────────────────
    # Container Operations
    # ─────────────────────────────────────────────────────────────

    async def check_container_health(
        self, server_id: str, container_name: str
    ) -> dict[str, Any]:
        """Check container health after deployment.

        Verifies: running status, restart count, listening ports, recent logs.

        Args:
            server_id: Server where container is running
            container_name: Container name to check

        Returns:
            Dict with health status and details
        """
        try:
            result = await self.deployment_service.check_container_health(
                server_id=server_id, container_name=container_name
            )
            healthy = result.get("healthy", False)
            return {
                "success": True,
                "data": result,
                "message": f"Container {'healthy' if healthy else 'unhealthy'}",
            }
        except Exception as e:
            logger.error("Health check error", error=str(e))
            return {
                "success": False,
                "message": f"Health check failed: {str(e)}",
                "error": "HEALTH_CHECK_ERROR",
            }

    async def get_container_logs(
        self, server_id: str, container_name: str, tail: int = 100
    ) -> dict[str, Any]:
        """Get recent logs from a container.

        Args:
            server_id: Server where container is running
            container_name: Container name to get logs from
            tail: Number of lines to return (default: 100)

        Returns:
            Dict with log lines
        """
        try:
            result = await self.deployment_service.get_container_logs(
                server_id=server_id, container_name=container_name, tail=tail
            )
            return {
                "success": True,
                "data": result,
                "message": f"Retrieved {len(result.get('logs', []))} log lines",
            }
        except Exception as e:
            logger.error("Get container logs error", error=str(e))
            return {
                "success": False,
                "message": f"Failed to get logs: {str(e)}",
                "error": "LOGS_ERROR",
            }

    # ─────────────────────────────────────────────────────────────
    # Cleanup
    # ─────────────────────────────────────────────────────────────

    async def cleanup_failed_deployment(
        self, server_id: str, installation_id: str
    ) -> dict[str, Any]:
        """Clean up a failed deployment.

        Removes: container, image (if unused), database record.

        Args:
            server_id: Server where deployment failed
            installation_id: Installation ID to clean up

        Returns:
            Dict with cleanup results
        """
        try:
            result = await self.deployment_service.cleanup_failed_deployment(
                server_id=server_id, installation_id=installation_id
            )
            await log_event(
                "application",
                "INFO",
                f"Cleaned up failed deployment: {installation_id}",
                APP_TAGS,
                {
                    "server_id": server_id,
                    "installation_id": installation_id,
                    "cleanup_result": result,
                },
            )
            return {
                "success": True,
                "data": result,
                "message": f"Cleanup completed: {result.get('message', 'done')}",
            }
        except Exception as e:
            logger.error("Cleanup error", error=str(e))
            await log_event(
                "application",
                "ERROR",
                f"Cleanup failed: {installation_id}",
                APP_TAGS,
                {"error": str(e)},
            )
            return {
                "success": False,
                "message": f"Cleanup failed: {str(e)}",
                "error": "CLEANUP_ERROR",
            }
