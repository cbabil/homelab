"""
App Catalog and Deployment Tools

Provides MCP tools for browsing catalog and managing app deployments.
"""

from typing import Any

import structlog

from models.app import AppFilter
from services.app_service import AppService
from services.deployment import DeploymentError, DeploymentService
from services.marketplace_service import MarketplaceService
from tools.app.deployment_tools import DeploymentTools
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
        self._deployment_tools = DeploymentTools(deployment_service)
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
        app_ids: list[str] = None,
        server_id: str = None,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
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
        app_ids: list[str] = None,
        config: dict[str, Any] = None,
    ) -> dict[str, Any]:
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
        app_ids: list[str] = None,
        remove_data: bool = False,
    ) -> dict[str, Any]:
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
        app_ids: list[str] = None,
        version: str = None,
    ) -> dict[str, Any]:
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

    # ─────────────────────────────────────────────────────────────
    # Delegated Deployment Pipeline Methods
    # ─────────────────────────────────────────────────────────────

    async def start_app(self, server_id: str, app_id: str) -> dict[str, Any]:
        """Start a stopped app."""
        return await self._deployment_tools.start_app(server_id, app_id)

    async def stop_app(self, server_id: str, app_id: str) -> dict[str, Any]:
        """Stop a running app."""
        return await self._deployment_tools.stop_app(server_id, app_id)

    async def get_installation_status(
        self, installation_id: str
    ) -> dict[str, Any]:
        """Get installation status by ID for polling during deployment."""
        return await self._deployment_tools.get_installation_status(installation_id)

    async def refresh_installation_status(
        self, installation_id: str
    ) -> dict[str, Any]:
        """Refresh installation status from Docker and update database."""
        return await self._deployment_tools.refresh_installation_status(
            installation_id
        )

    async def validate_deployment_config(
        self, app_id: str, config: dict[str, Any] = None
    ) -> dict[str, Any]:
        """Validate deployment configuration before install."""
        return await self._deployment_tools.validate_deployment_config(app_id, config)

    async def run_preflight_checks(
        self, server_id: str, app_id: str, config: dict[str, Any] = None
    ) -> dict[str, Any]:
        """Run pre-flight checks before deployment."""
        return await self._deployment_tools.run_preflight_checks(
            server_id, app_id, config
        )

    async def check_container_health(
        self, server_id: str, container_name: str
    ) -> dict[str, Any]:
        """Check container health after deployment."""
        return await self._deployment_tools.check_container_health(
            server_id, container_name
        )

    async def get_container_logs(
        self, server_id: str, container_name: str, tail: int = 100
    ) -> dict[str, Any]:
        """Get recent logs from a container."""
        return await self._deployment_tools.get_container_logs(
            server_id, container_name, tail
        )

    async def cleanup_failed_deployment(
        self, server_id: str, installation_id: str
    ) -> dict[str, Any]:
        """Clean up a failed deployment."""
        return await self._deployment_tools.cleanup_failed_deployment(
            server_id, installation_id
        )
