"""
App Catalog and Deployment Tools

Provides MCP tools for browsing catalog and managing app deployments.
"""

from datetime import datetime, UTC
from typing import Dict, Any, Optional, List
import uuid
import structlog
from fastmcp import FastMCP
from services.app_service import AppService
from services.marketplace_service import MarketplaceService
from services.deployment_service import DeploymentService
from services.service_log import log_service
from models.log import LogEntry
from models.app import AppFilter

logger = structlog.get_logger("app_tools")


async def _log_app_event(level: str, message: str, metadata: Dict[str, Any] = None):
    """Helper to log app events to the database."""
    try:
        entry = LogEntry(
            id=f"app-{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now(UTC),
            level=level,
            source="app",
            message=message,
            tags=["app", "deployment"],
            metadata=metadata or {}
        )
        await log_service.create_log_entry(entry)
    except Exception as e:
        logger.error("Failed to create log entry", error=str(e))


class AppTools:
    """App tools for the MCP server."""

    def __init__(self, app_service: AppService, marketplace_service: MarketplaceService, deployment_service: DeploymentService):
        """Initialize app tools."""
        self.app_service = app_service
        self.marketplace_service = marketplace_service
        self.deployment_service = deployment_service
        logger.info("App tools initialized")

    async def search_apps(
        self,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Search applications in the catalog.

        Args:
            filters: Optional filter criteria (category, status, search, tags, etc.)

        Returns:
            Dict with success status and matching applications
        """
        try:
            # Build filter from dict
            filter_obj = AppFilter()
            if filters:
                filter_obj = AppFilter(
                    category=filters.get("category"),
                    status=filters.get("status"),
                    search=filters.get("search"),
                    featured=filters.get("featured"),
                    tags=filters.get("tags"),
                    sort_by=filters.get("sort_by"),
                    sort_order=filters.get("sort_order")
                )

            result = await self.app_service.search_apps(filter_obj)

            return {
                "success": True,
                "data": {
                    "apps": [app.model_dump(by_alias=True) for app in result.apps],
                    "total": result.total,
                    "page": result.page,
                    "limit": result.limit,
                    "filters": result.filters.model_dump(by_alias=True) if result.filters else {}
                },
                "message": f"Found {result.total} applications"
            }
        except Exception as e:
            logger.error("Search apps error", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to search applications"
            }

    async def remove_app(self, app_id: str) -> Dict[str, Any]:
        """Remove an application from the catalog.

        Only allows removing apps that are not installed.

        Args:
            app_id: Application ID to remove

        Returns:
            Dict with success status
        """
        try:
            success = await self.app_service.remove_app(app_id)
            if success:
                await _log_app_event("INFO", f"App removed from catalog: {app_id}", {"app_id": app_id})
                return {
                    "success": True,
                    "message": f"Application '{app_id}' removed from catalog"
                }
            return {
                "success": False,
                "error": "App not found",
                "message": f"Application '{app_id}' not found"
            }
        except ValueError as e:
            return {
                "success": False,
                "error": str(e),
                "message": str(e)
            }
        except Exception as e:
            logger.error("Remove app error", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to remove application"
            }

    async def remove_apps_bulk(self, app_ids: List[str]) -> Dict[str, Any]:
        """Remove multiple applications from the catalog.

        Only removes apps that are not installed. Skips installed apps.

        Args:
            app_ids: List of application IDs to remove

        Returns:
            Dict with removed and skipped counts
        """
        try:
            result = await self.app_service.remove_apps_bulk(app_ids)
            if result["removed_count"] > 0:
                await _log_app_event("INFO", f"Bulk removed {result['removed_count']} apps", {
                    "removed": result["removed"],
                    "skipped_count": result["skipped_count"]
                })
            return {
                "success": True,
                "data": result,
                "message": f"Removed {result['removed_count']} apps, skipped {result['skipped_count']}"
            }
        except Exception as e:
            logger.error("Bulk remove apps error", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to remove applications"
            }

    async def mark_app_uninstalled(self, app_id: str) -> Dict[str, Any]:
        """Mark an application as uninstalled without server interaction.

        Updates the app status to 'available' and clears the connected server.

        Args:
            app_id: Application ID to mark as uninstalled

        Returns:
            Dict with success status
        """
        try:
            success = await self.app_service.mark_app_uninstalled(app_id)
            if success:
                await _log_app_event("INFO", f"App marked as uninstalled: {app_id}", {"app_id": app_id})
                return {
                    "success": True,
                    "message": f"Application '{app_id}' marked as uninstalled"
                }
            return {
                "success": False,
                "error": "App not found",
                "message": f"Application '{app_id}' not found"
            }
        except Exception as e:
            logger.error("Mark app uninstalled error", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to mark application as uninstalled"
            }

    async def mark_apps_uninstalled_bulk(self, app_ids: List[str]) -> Dict[str, Any]:
        """Mark multiple applications as uninstalled.

        Args:
            app_ids: List of application IDs to uninstall

        Returns:
            Dict with uninstalled and skipped counts
        """
        try:
            result = await self.app_service.mark_apps_uninstalled_bulk(app_ids)
            if result["uninstalled_count"] > 0:
                await _log_app_event("INFO", f"Bulk uninstalled {result['uninstalled_count']} apps", {
                    "uninstalled": result["uninstalled"],
                    "skipped_count": result["skipped_count"]
                })
            return {
                "success": True,
                "data": result,
                "message": f"Uninstalled {result['uninstalled_count']} apps, skipped {result['skipped_count']}"
            }
        except Exception as e:
            logger.error("Bulk uninstall apps error", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to uninstall applications"
            }

    async def list_catalog(self, category: str = None) -> Dict[str, Any]:
        """List all available apps in the marketplace catalog."""
        try:
            apps = await self.marketplace_service.search_apps(category=category)
            return {
                "success": True,
                "data": {
                    "apps": [
                        {
                            "id": app.id,
                            "name": app.name,
                            "description": app.description,
                            "category": app.category,
                            "image": app.docker.image
                        }
                        for app in apps
                    ],
                    "count": len(apps)
                },
                "message": f"Found {len(apps)} apps"
            }
        except Exception as e:
            logger.error("List catalog error", error=str(e))
            return {
                "success": False,
                "message": f"Failed to list catalog: {str(e)}",
                "error": "LIST_CATALOG_ERROR"
            }

    async def get_app_definition(self, app_id: str) -> Dict[str, Any]:
        """Get full app definition by ID from marketplace."""
        try:
            app = await self.marketplace_service.get_app(app_id)
            if not app:
                return {
                    "success": False,
                    "message": f"App '{app_id}' not found",
                    "error": "APP_NOT_FOUND"
                }

            return {
                "success": True,
                "data": {
                    "id": app.id,
                    "name": app.name,
                    "description": app.description,
                    "category": app.category,
                    "image": app.docker.image,
                    "ports": [p.model_dump() for p in app.docker.ports],
                    "volumes": [v.model_dump() for v in app.docker.volumes],
                    "env_vars": [e.model_dump() for e in app.docker.environment],
                    "restart_policy": app.docker.restart_policy,
                    "privileged": app.docker.privileged
                },
                "message": "App definition retrieved"
            }
        except Exception as e:
            logger.error("Get app definition error", error=str(e))
            return {
                "success": False,
                "message": f"Failed to get app: {str(e)}",
                "error": "GET_APP_ERROR"
            }

    async def install_app(
        self,
        server_id: str,
        app_id: str,
        config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Install an app on a server."""
        try:
            installation = await self.deployment_service.install_app(
                server_id=server_id,
                app_id=app_id,
                config=config or {}
            )

            if not installation:
                await _log_app_event("ERROR", f"App installation failed: {app_id}", {
                    "app_id": app_id,
                    "server_id": server_id
                })
                return {
                    "success": False,
                    "message": "Failed to install app",
                    "error": "INSTALL_FAILED"
                }

            await _log_app_event("INFO", f"App installed: {app_id}", {
                "app_id": app_id,
                "server_id": server_id,
                "installation_id": installation.id
            })
            return {
                "success": True,
                "data": {
                    "installation_id": installation.id,
                    "server_id": server_id,
                    "app_id": app_id
                },
                "message": f"App '{app_id}' installation started"
            }
        except Exception as e:
            logger.error("Install app error", error=str(e))
            await _log_app_event("ERROR", f"App install error: {app_id}", {"error": str(e)})
            return {
                "success": False,
                "message": f"Failed to install: {str(e)}",
                "error": "INSTALL_ERROR"
            }

    async def uninstall_app(
        self,
        server_id: str,
        app_id: str,
        remove_data: bool = False
    ) -> Dict[str, Any]:
        """Uninstall an app from a server."""
        try:
            success = await self.deployment_service.uninstall_app(
                server_id=server_id,
                app_id=app_id,
                remove_data=remove_data
            )

            if not success:
                await _log_app_event("ERROR", f"App uninstall failed: {app_id}", {
                    "app_id": app_id,
                    "server_id": server_id
                })
                return {
                    "success": False,
                    "message": "Failed to uninstall app",
                    "error": "UNINSTALL_FAILED"
                }

            await _log_app_event("INFO", f"App uninstalled: {app_id}", {
                "app_id": app_id,
                "server_id": server_id,
                "remove_data": remove_data
            })
            return {
                "success": True,
                "data": {"server_id": server_id, "app_id": app_id},
                "message": f"App '{app_id}' uninstalled"
            }
        except Exception as e:
            logger.error("Uninstall app error", error=str(e))
            await _log_app_event("ERROR", f"App uninstall error: {app_id}", {"error": str(e)})
            return {
                "success": False,
                "message": f"Failed to uninstall: {str(e)}",
                "error": "UNINSTALL_ERROR"
            }

    async def get_installed_apps(self, server_id: str) -> Dict[str, Any]:
        """Get all installed apps on a server."""
        try:
            apps = await self.deployment_service.get_installed_apps(server_id)
            return {
                "success": True,
                "data": {"apps": apps, "count": len(apps)},
                "message": f"Found {len(apps)} installed apps"
            }
        except Exception as e:
            logger.error("Get installed apps error", error=str(e))
            return {
                "success": False,
                "message": f"Failed to get installed apps: {str(e)}",
                "error": "GET_INSTALLED_ERROR"
            }

    async def start_app(self, server_id: str, app_id: str) -> Dict[str, Any]:
        """Start a stopped app."""
        try:
            success = await self.deployment_service.start_app(server_id, app_id)
            if not success:
                await _log_app_event("ERROR", f"App start failed: {app_id}", {
                    "app_id": app_id,
                    "server_id": server_id
                })
                return {
                    "success": False,
                    "message": "Failed to start app",
                    "error": "START_FAILED"
                }
            await _log_app_event("INFO", f"App started: {app_id}", {
                "app_id": app_id,
                "server_id": server_id
            })
            return {
                "success": True,
                "data": {"server_id": server_id, "app_id": app_id},
                "message": f"App '{app_id}' started"
            }
        except Exception as e:
            logger.error("Start app error", error=str(e))
            await _log_app_event("ERROR", f"App start error: {app_id}", {"error": str(e)})
            return {
                "success": False,
                "message": f"Failed to start: {str(e)}",
                "error": "START_ERROR"
            }

    async def stop_app(self, server_id: str, app_id: str) -> Dict[str, Any]:
        """Stop a running app."""
        try:
            success = await self.deployment_service.stop_app(server_id, app_id)
            if not success:
                await _log_app_event("ERROR", f"App stop failed: {app_id}", {
                    "app_id": app_id,
                    "server_id": server_id
                })
                return {
                    "success": False,
                    "message": "Failed to stop app",
                    "error": "STOP_FAILED"
                }
            await _log_app_event("INFO", f"App stopped: {app_id}", {
                "app_id": app_id,
                "server_id": server_id
            })
            return {
                "success": True,
                "data": {"server_id": server_id, "app_id": app_id},
                "message": f"App '{app_id}' stopped"
            }
        except Exception as e:
            logger.error("Stop app error", error=str(e))
            await _log_app_event("ERROR", f"App stop error: {app_id}", {"error": str(e)})
            return {
                "success": False,
                "message": f"Failed to stop: {str(e)}",
                "error": "STOP_ERROR"
            }


def register_app_tools(app: FastMCP, app_service: AppService, marketplace_service: MarketplaceService, deployment_service: DeploymentService):
    """Register app tools with FastMCP app."""
    tools = AppTools(app_service, marketplace_service, deployment_service)

    app.tool(tools.search_apps)
    app.tool(tools.remove_app)
    app.tool(tools.remove_apps_bulk)
    app.tool(tools.mark_app_uninstalled)
    app.tool(tools.mark_apps_uninstalled_bulk)
    app.tool(tools.list_catalog)
    app.tool(tools.get_app_definition)
    app.tool(tools.install_app)
    app.tool(tools.uninstall_app)
    app.tool(tools.get_installed_apps)
    app.tool(tools.start_app)
    app.tool(tools.stop_app)

    logger.info("App tools registered")
