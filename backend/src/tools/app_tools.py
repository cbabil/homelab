"""
App Catalog and Deployment Tools

Provides MCP tools for browsing catalog and managing app deployments.
"""

from typing import Dict, Any, Optional
import structlog
from fastmcp import FastMCP
from services.catalog_service import CatalogService
from services.deployment_service import DeploymentService

logger = structlog.get_logger("app_tools")


class AppTools:
    """App tools for the MCP server."""

    def __init__(self, catalog_service: CatalogService, deployment_service: DeploymentService):
        """Initialize app tools."""
        self.catalog_service = catalog_service
        self.deployment_service = deployment_service
        logger.info("App tools initialized")

    async def list_catalog(self, category: str = None) -> Dict[str, Any]:
        """List all available apps in the catalog."""
        try:
            apps = self.catalog_service.list_apps(category=category)
            return {
                "success": True,
                "data": {
                    "apps": [
                        {
                            "id": app.id,
                            "name": app.name,
                            "description": app.description,
                            "category": app.category.value,
                            "image": app.image
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
        """Get full app definition by ID."""
        try:
            app = self.catalog_service.get_app(app_id)
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
                    "category": app.category.value,
                    "image": app.image,
                    "ports": [p.model_dump() for p in app.ports],
                    "volumes": [v.model_dump() for v in app.volumes],
                    "env_vars": [e.model_dump() for e in app.env_vars],
                    "restart_policy": app.restart_policy,
                    "privileged": app.privileged
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
                return {
                    "success": False,
                    "message": "Failed to install app",
                    "error": "INSTALL_FAILED"
                }

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
                return {
                    "success": False,
                    "message": "Failed to uninstall app",
                    "error": "UNINSTALL_FAILED"
                }

            return {
                "success": True,
                "data": {"server_id": server_id, "app_id": app_id},
                "message": f"App '{app_id}' uninstalled"
            }
        except Exception as e:
            logger.error("Uninstall app error", error=str(e))
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
                return {
                    "success": False,
                    "message": "Failed to start app",
                    "error": "START_FAILED"
                }
            return {
                "success": True,
                "data": {"server_id": server_id, "app_id": app_id},
                "message": f"App '{app_id}' started"
            }
        except Exception as e:
            logger.error("Start app error", error=str(e))
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
                return {
                    "success": False,
                    "message": "Failed to stop app",
                    "error": "STOP_FAILED"
                }
            return {
                "success": True,
                "data": {"server_id": server_id, "app_id": app_id},
                "message": f"App '{app_id}' stopped"
            }
        except Exception as e:
            logger.error("Stop app error", error=str(e))
            return {
                "success": False,
                "message": f"Failed to stop: {str(e)}",
                "error": "STOP_ERROR"
            }


def register_app_tools(app: FastMCP, catalog_service: CatalogService, deployment_service: DeploymentService):
    """Register app tools with FastMCP app."""
    tools = AppTools(catalog_service, deployment_service)

    app.tool(tools.list_catalog)
    app.tool(tools.get_app_definition)
    app.tool(tools.install_app)
    app.tool(tools.uninstall_app)
    app.tool(tools.get_installed_apps)
    app.tool(tools.start_app)
    app.tool(tools.stop_app)

    logger.info("App tools registered")
