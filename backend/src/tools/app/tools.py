"""
App Catalog and Deployment Tools

Provides MCP tools for browsing catalog and managing app deployments.
"""

from typing import Dict, Any, Optional, List
import structlog
from services.app_service import AppService
from services.marketplace_service import MarketplaceService
from services.deployment import DeploymentService, DeploymentError
from models.app import AppFilter
from tools.common import log_event

logger = structlog.get_logger("app_tools")

APP_TAGS = ["app", "deployment"]


class AppTools:
    """App tools for the MCP server."""

    def __init__(
        self,
        app_service: AppService,
        marketplace_service: MarketplaceService,
        deployment_service: DeploymentService,
    ):
        """Initialize app tools."""
        self.app_service = app_service
        self.marketplace_service = marketplace_service
        self.deployment_service = deployment_service
        logger.info("App tools initialized")

    async def _get_server_name(self, server_id: str) -> str:
        """Get server name for error messages."""
        try:
            server = await self.deployment_service.server_service.get_server(server_id)
            if server and server.name:
                return server.name
        except Exception:
            pass
        return server_id  # Fallback to ID

    # ─────────────────────────────────────────────────────────────
    # Core CRUD Operations
    # ─────────────────────────────────────────────────────────────

    async def get_app(
        self,
        app_id: str = None,
        app_ids: List[str] = None,
        server_id: str = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Get app details from catalog or installed apps.

        Args:
            app_id: Single app ID to get
            app_ids: Multiple app IDs to get (bulk)
            server_id: If provided, get installed app(s) on this server.
                       If None, get from catalog/marketplace.
            filters: Search filters (category, status, search, tags, etc.)
                     Used when no app_id/app_ids provided.

        Returns:
            Dict with app details or list of apps
        """
        try:
            # Get installed apps from server
            if server_id:
                if app_id:
                    # Single installed app
                    apps = await self.deployment_service.get_installed_apps(server_id)
                    app_data = next(
                        (a for a in apps if a.get("app_id") == app_id), None
                    )
                    if not app_data:
                        return {
                            "success": False,
                            "message": f"App '{app_id}' not installed on server",
                            "error": "APP_NOT_FOUND",
                        }
                    return {
                        "success": True,
                        "data": app_data,
                        "message": "Installed app retrieved",
                    }
                else:
                    # All installed apps on server
                    apps = await self.deployment_service.get_installed_apps(server_id)
                    return {
                        "success": True,
                        "data": {"apps": apps, "total": len(apps)},
                        "message": f"Found {len(apps)} installed apps",
                    }

            # Get all installed apps across all servers
            if not app_id and not app_ids and not filters:
                installations = (
                    await self.deployment_service.get_all_installations_with_details()
                )
                return {
                    "success": True,
                    "data": {
                        "installations": installations,
                        "total": len(installations),
                    },
                    "message": f"Found {len(installations)} installed apps",
                }

            # Get from catalog/marketplace
            if app_id:
                app = await self.marketplace_service.get_app(app_id)
                if not app:
                    return {
                        "success": False,
                        "message": f"App '{app_id}' not found",
                        "error": "APP_NOT_FOUND",
                    }
                return {
                    "success": True,
                    "data": app.model_dump(by_alias=True),
                    "message": "App retrieved",
                }

            if app_ids:
                apps = []
                for aid in app_ids:
                    app = await self.marketplace_service.get_app(aid)
                    if app:
                        apps.append(app.model_dump(by_alias=True))
                return {
                    "success": True,
                    "data": {"apps": apps, "total": len(apps)},
                    "message": f"Found {len(apps)} apps",
                }

            # Search with filters
            filter_obj = AppFilter()
            if filters:
                filter_obj = AppFilter(
                    category=filters.get("category"),
                    status=filters.get("status"),
                    search=filters.get("search"),
                    featured=filters.get("featured"),
                    tags=filters.get("tags"),
                    sort_by=filters.get("sort_by"),
                    sort_order=filters.get("sort_order"),
                )

            result = await self.app_service.search_apps(filter_obj)
            return {
                "success": True,
                "data": {
                    "apps": [app.model_dump(by_alias=True) for app in result.apps],
                    "total": result.total,
                },
                "message": f"Found {result.total} apps",
            }

        except Exception as e:
            logger.error("Get app error", error=str(e))
            return {"success": False, "error": str(e), "message": "Failed to get app"}

    async def add_app(
        self,
        server_id: str,
        app_id: str = None,
        app_ids: List[str] = None,
        config: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Deploy app(s) to a server.

        Args:
            server_id: Server to deploy to
            app_id: Single app ID to deploy
            app_ids: Multiple app IDs to deploy (bulk)
            config: Deployment configuration (ports, volumes, env vars)

        Returns:
            Dict with installation details
        """
        try:
            # Bulk deployment
            if app_ids:
                results = []
                for aid in app_ids:
                    try:
                        installation = await self.deployment_service.install_app(
                            server_id=server_id, app_id=aid, config=config or {}
                        )
                        await self.app_service.mark_app_installed(aid, server_id)
                        results.append(
                            {
                                "app_id": aid,
                                "installation_id": installation.id,
                                "success": True,
                            }
                        )
                    except Exception as e:
                        results.append(
                            {"app_id": aid, "success": False, "error": str(e)}
                        )

                succeeded = sum(1 for r in results if r["success"])
                await log_event(
                    "application",
                    "INFO",
                    f"Bulk deployed {succeeded}/{len(app_ids)} apps",
                    APP_TAGS,
                    {"server_id": server_id, "results": results},
                )
                return {
                    "success": True,
                    "data": {
                        "results": results,
                        "succeeded": succeeded,
                        "total": len(app_ids),
                    },
                    "message": f"Deployed {succeeded}/{len(app_ids)} apps",
                }

            # Single deployment
            if not app_id:
                return {
                    "success": False,
                    "message": "app_id or app_ids required",
                    "error": "MISSING_APP_ID",
                }

            installation = await self.deployment_service.install_app(
                server_id=server_id, app_id=app_id, config=config or {}
            )

            await self.app_service.mark_app_installed(app_id, server_id)

            await log_event(
                "application",
                "INFO",
                f"App deployed: {app_id}",
                APP_TAGS,
                {
                    "app_id": app_id,
                    "server_id": server_id,
                    "installation_id": installation.id,
                },
            )
            return {
                "success": True,
                "data": {
                    "installation_id": installation.id,
                    "server_id": server_id,
                    "app_id": app_id,
                },
                "message": f"App '{app_id}' deployment started",
            }
        except DeploymentError as e:
            server_name = await self._get_server_name(server_id)
            logger.error(
                "Deployment failed", app_id=app_id, server=server_name, error=str(e)
            )
            await log_event(
                "application",
                "ERROR",
                f"App deployment failed: {app_id} on {server_name}",
                APP_TAGS,
                {
                    "app_id": app_id,
                    "server_id": server_id,
                    "server_name": server_name,
                    "error": str(e),
                },
            )
            return {
                "success": False,
                "message": f"Deployment failed on {server_name}: {str(e)}",
                "error": "DEPLOYMENT_FAILED",
            }
        except Exception as e:
            server_name = await self._get_server_name(server_id)
            logger.error(
                "Add app error", app_id=app_id, server=server_name, error=str(e)
            )
            await log_event(
                "application",
                "ERROR",
                f"App deploy error: {app_id} on {server_name}",
                APP_TAGS,
                {
                    "app_id": app_id,
                    "server_id": server_id,
                    "server_name": server_name,
                    "error": str(e),
                },
            )
            return {
                "success": False,
                "message": f"Failed to deploy on {server_name}: {str(e)}",
                "error": "ADD_APP_ERROR",
            }

    async def delete_app(
        self,
        server_id: str,
        app_id: str = None,
        app_ids: List[str] = None,
        remove_data: bool = False,
    ) -> Dict[str, Any]:
        """Remove app(s) from a server.

        Args:
            server_id: Server to remove from
            app_id: Single app ID to remove
            app_ids: Multiple app IDs to remove (bulk)
            remove_data: Whether to remove persistent data (volumes)

        Returns:
            Dict with removal results
        """
        try:
            # Bulk removal
            if app_ids:
                results = []
                for aid in app_ids:
                    try:
                        success = await self.deployment_service.uninstall_app(
                            server_id=server_id, app_id=aid, remove_data=remove_data
                        )
                        if success:
                            await self.app_service.mark_app_uninstalled(aid)
                        results.append({"app_id": aid, "success": success})
                    except Exception as e:
                        results.append(
                            {"app_id": aid, "success": False, "error": str(e)}
                        )

                succeeded = sum(1 for r in results if r["success"])
                await log_event(
                    "application",
                    "INFO",
                    f"Bulk removed {succeeded}/{len(app_ids)} apps",
                    APP_TAGS,
                    {
                        "server_id": server_id,
                        "remove_data": remove_data,
                        "results": results,
                    },
                )
                return {
                    "success": True,
                    "data": {
                        "results": results,
                        "succeeded": succeeded,
                        "total": len(app_ids),
                    },
                    "message": f"Removed {succeeded}/{len(app_ids)} apps",
                }

            # Single removal
            if not app_id:
                return {
                    "success": False,
                    "message": "app_id or app_ids required",
                    "error": "MISSING_APP_ID",
                }

            success = await self.deployment_service.uninstall_app(
                server_id=server_id, app_id=app_id, remove_data=remove_data
            )

            if not success:
                await log_event(
                    "application",
                    "ERROR",
                    f"App removal failed: {app_id}",
                    APP_TAGS,
                    {"app_id": app_id, "server_id": server_id},
                )
                return {
                    "success": False,
                    "message": "Failed to remove app",
                    "error": "DELETE_FAILED",
                }

            await self.app_service.mark_app_uninstalled(app_id)

            await log_event(
                "application",
                "INFO",
                f"App removed: {app_id}",
                APP_TAGS,
                {"app_id": app_id, "server_id": server_id, "remove_data": remove_data},
            )
            return {
                "success": True,
                "data": {"server_id": server_id, "app_id": app_id},
                "message": f"App '{app_id}' removed",
            }
        except Exception as e:
            logger.error("Delete app error", error=str(e))
            await log_event(
                "application",
                "ERROR",
                f"App delete error: {app_id}",
                APP_TAGS,
                {"error": str(e)},
            )
            return {
                "success": False,
                "message": f"Failed to remove: {str(e)}",
                "error": "DELETE_APP_ERROR",
            }

    async def update_app(
        self,
        server_id: str,
        app_id: str = None,
        app_ids: List[str] = None,
        version: str = None,
    ) -> Dict[str, Any]:
        """Update app(s) to a new version.

        Args:
            server_id: Server where app is installed
            app_id: Single app ID to update
            app_ids: Multiple app IDs to update (bulk)
            version: Target version (latest if not specified)

        Returns:
            Dict with update results
        """
        try:
            # Bulk update
            if app_ids:
                results = []
                for aid in app_ids:
                    try:
                        # Get current installation
                        apps = await self.deployment_service.get_installed_apps(
                            server_id
                        )
                        current = next(
                            (a for a in apps if a.get("app_id") == aid), None
                        )
                        if not current:
                            results.append(
                                {
                                    "app_id": aid,
                                    "success": False,
                                    "error": "Not installed",
                                }
                            )
                            continue

                        # Uninstall and reinstall with new version
                        await self.deployment_service.uninstall_app(
                            server_id, aid, remove_data=False
                        )
                        config = current.get("config", {})
                        if version:
                            config["version"] = version
                        installation = await self.deployment_service.install_app(
                            server_id, aid, config
                        )
                        results.append(
                            {
                                "app_id": aid,
                                "success": True,
                                "installation_id": installation.id,
                            }
                        )
                    except Exception as e:
                        results.append(
                            {"app_id": aid, "success": False, "error": str(e)}
                        )

                succeeded = sum(1 for r in results if r["success"])
                await log_event(
                    "application",
                    "INFO",
                    f"Bulk updated {succeeded}/{len(app_ids)} apps",
                    APP_TAGS,
                    {"server_id": server_id, "version": version, "results": results},
                )
                return {
                    "success": True,
                    "data": {
                        "results": results,
                        "succeeded": succeeded,
                        "total": len(app_ids),
                    },
                    "message": f"Updated {succeeded}/{len(app_ids)} apps",
                }

            # Single update
            if not app_id:
                return {
                    "success": False,
                    "message": "app_id or app_ids required",
                    "error": "MISSING_APP_ID",
                }

            # Get current installation
            apps = await self.deployment_service.get_installed_apps(server_id)
            current = next((a for a in apps if a.get("app_id") == app_id), None)
            if not current:
                return {
                    "success": False,
                    "message": f"App '{app_id}' not installed on server",
                    "error": "APP_NOT_INSTALLED",
                }

            # Uninstall (keep data) and reinstall with new version
            await self.deployment_service.uninstall_app(
                server_id, app_id, remove_data=False
            )
            config = current.get("config", {})
            if version:
                config["version"] = version
            installation = await self.deployment_service.install_app(
                server_id, app_id, config
            )

            await log_event(
                "application",
                "INFO",
                f"App updated: {app_id}",
                APP_TAGS,
                {
                    "app_id": app_id,
                    "server_id": server_id,
                    "version": version,
                    "installation_id": installation.id,
                },
            )
            return {
                "success": True,
                "data": {
                    "installation_id": installation.id,
                    "server_id": server_id,
                    "app_id": app_id,
                    "version": version,
                },
                "message": f"App '{app_id}' update started",
            }
        except Exception as e:
            logger.error("Update app error", error=str(e))
            await log_event(
                "application",
                "ERROR",
                f"App update error: {app_id}",
                APP_TAGS,
                {"error": str(e)},
            )
            return {
                "success": False,
                "message": f"Failed to update: {str(e)}",
                "error": "UPDATE_APP_ERROR",
            }

    async def start_app(self, server_id: str, app_id: str) -> Dict[str, Any]:
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

    async def stop_app(self, server_id: str, app_id: str) -> Dict[str, Any]:
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

    # ============================================================
    # Deployment Pipeline Tools (Status, Validation, Health, Cleanup)
    # ============================================================

    async def get_installation_status(self, installation_id: str) -> Dict[str, Any]:
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

    async def refresh_installation_status(self, installation_id: str) -> Dict[str, Any]:
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

    async def validate_deployment_config(
        self, app_id: str, config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
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
        self, server_id: str, app_id: str, config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
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

    async def check_container_health(
        self, server_id: str, container_name: str
    ) -> Dict[str, Any]:
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
    ) -> Dict[str, Any]:
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

    async def cleanup_failed_deployment(
        self, server_id: str, installation_id: str
    ) -> Dict[str, Any]:
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
