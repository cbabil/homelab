"""
System Tools

Provides system-level information and setup capabilities for the MCP server.
Handles application metadata, setup status, and component versions.
"""

from typing import Any, Dict

import httpx
import structlog
from fastmcp import Context

from services.database_service import DatabaseService


logger = structlog.get_logger("system_tools")

# GitHub repository for checking updates
GITHUB_REPO = "tomo/tomo"
GITHUB_API_RELEASES = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


class SystemTools:
    """System tools for the MCP server."""

    def __init__(self, database_service: DatabaseService):
        """Initialize system tools with database service."""
        self.db_service = database_service
        logger.info("System tools initialized")

    async def get_system_setup(
        self, params: Dict[str, Any] = None, ctx: Context = None
    ) -> Dict[str, Any]:
        """Get system setup status.

        This tool requires NO authentication as it must be callable
        before any user exists in the system.

        Returns:
            Dictionary with:
            - needs_setup: True if system needs initial setup
            - is_setup: True if system has completed setup
            - app_name: Application name
        """
        try:
            is_setup = await self.db_service.is_system_setup()
            system_info = await self.db_service.get_system_info()

            logger.debug("System setup check", is_setup=is_setup)

            return {
                "success": True,
                "data": {
                    "needs_setup": not is_setup,
                    "is_setup": is_setup,
                    "app_name": system_info.get("app_name") if system_info else "Tomo",
                },
            }
        except Exception as e:
            logger.error("System setup check failed", error=str(e))
            return {
                "success": False,
                "message": f"Failed to check system setup: {str(e)}",
                "error": "SETUP_CHECK_ERROR",
            }

    async def get_system_info(
        self, params: Dict[str, Any] = None, ctx: Context = None
    ) -> Dict[str, Any]:
        """Get system information and metadata.

        Returns application metadata including installation ID
        and license information.

        Returns:
            Dictionary with system info fields.
        """
        try:
            system_info = await self.db_service.get_system_info()

            if not system_info:
                return {
                    "success": False,
                    "message": "System info not found",
                    "error": "NOT_FOUND",
                }

            # Don't expose sensitive fields like license_key
            safe_info = {
                "app_name": system_info.get("app_name"),
                "is_setup": system_info.get("is_setup"),
                "setup_completed_at": system_info.get("setup_completed_at"),
                "installation_id": system_info.get("installation_id"),
                "license_type": system_info.get("license_type"),
                "license_expires_at": system_info.get("license_expires_at"),
                "created_at": system_info.get("created_at"),
                "updated_at": system_info.get("updated_at"),
            }

            return {
                "success": True,
                "data": safe_info,
            }
        except Exception as e:
            logger.error("Failed to get system info", error=str(e))
            return {
                "success": False,
                "message": f"Failed to get system info: {str(e)}",
                "error": "SYSTEM_INFO_ERROR",
            }

    async def get_component_versions(
        self, params: Dict[str, Any] = None, ctx: Context = None
    ) -> Dict[str, Any]:
        """Get versions of all components (backend, frontend, api).

        Returns:
            Dictionary with component versions.
        """
        try:
            versions = await self.db_service.get_component_versions()

            # Convert to dict keyed by component name
            versions_dict = {v["component"]: v for v in versions}

            return {
                "success": True,
                "data": {
                    "components": versions_dict,
                    "backend": versions_dict.get("backend", {}).get("version", "1.0.0"),
                    "frontend": versions_dict.get("frontend", {}).get("version", "1.0.0"),
                    "api": versions_dict.get("api", {}).get("version", "1.0.0"),
                }
            }
        except Exception as e:
            logger.error("Failed to get component versions", error=str(e))
            return {
                "success": False,
                "message": f"Failed to get component versions: {str(e)}",
                "error": "VERSION_ERROR",
            }

    async def check_updates(
        self, params: Dict[str, Any] = None, ctx: Context = None
    ) -> Dict[str, Any]:
        """Check for available updates from GitHub releases.

        Compares current component versions against the latest
        GitHub release to determine if updates are available.

        Returns:
            Dictionary with:
            - components: Current versions of each component
            - latest_version: Latest available version from GitHub
            - update_available: True if a newer version exists
            - release_url: URL to the release page
            - release_notes: Release notes/body from GitHub
        """
        try:
            # Get current component versions
            versions = await self.db_service.get_component_versions()
            versions_dict = {v["component"]: v["version"] for v in versions}

            # Use backend version as the primary version for comparison
            current_version = versions_dict.get("backend", "1.0.0")

            # Fetch latest release from GitHub
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    GITHUB_API_RELEASES,
                    headers={"Accept": "application/vnd.github.v3+json"}
                )

            if response.status_code == 404:
                return {
                    "success": True,
                    "data": {
                        "components": versions_dict,
                        "latest_version": None,
                        "update_available": False,
                        "message": "No releases found on GitHub"
                    }
                }

            response.raise_for_status()
            release_data = response.json()

            latest_version = release_data.get("tag_name", "").lstrip("v")
            release_url = release_data.get("html_url", "")
            release_notes = release_data.get("body", "")

            # Compare versions
            update_available = self._compare_versions(current_version, latest_version) < 0

            logger.info(
                "Update check completed",
                current=current_version,
                latest=latest_version,
                update_available=update_available
            )

            return {
                "success": True,
                "data": {
                    "components": versions_dict,
                    "latest_version": latest_version,
                    "update_available": update_available,
                    "release_url": release_url,
                    "release_notes": release_notes[:500] if release_notes else None
                }
            }

        except httpx.HTTPError as e:
            logger.error("HTTP error checking for updates", error=str(e))
            return {
                "success": False,
                "message": f"Failed to check for updates: {str(e)}",
                "error": "UPDATE_CHECK_ERROR",
            }
        except Exception as e:
            logger.error("Failed to check for updates", error=str(e))
            return {
                "success": False,
                "message": f"Failed to check for updates: {str(e)}",
                "error": "UPDATE_CHECK_ERROR",
            }

    def _compare_versions(self, v1: str, v2: str) -> int:
        """Compare two semantic version strings.

        Args:
            v1: First version string.
            v2: Second version string.

        Returns:
            -1 if v1 < v2, 0 if v1 == v2, 1 if v1 > v2
        """
        def parse_version(v: str) -> tuple:
            v = v.lstrip("v")
            parts = v.split(".")
            result = []
            for p in parts[:3]:
                num_part = p.split("-")[0]
                try:
                    result.append(int(num_part))
                except ValueError:
                    result.append(0)
            while len(result) < 3:
                result.append(0)
            return tuple(result)

        v1_tuple = parse_version(v1)
        v2_tuple = parse_version(v2)

        if v1_tuple < v2_tuple:
            return -1
        elif v1_tuple > v2_tuple:
            return 1
        return 0
