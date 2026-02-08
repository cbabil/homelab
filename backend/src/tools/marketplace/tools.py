"""
Marketplace MCP Tools

Provides MCP tools for managing marketplace repositories and apps.
"""

from typing import Any

import structlog

from models.marketplace import RepoType
from services.marketplace_service import MarketplaceService
from tools.common import log_event

logger = structlog.get_logger("marketplace_tools")

MARKETPLACE_TAGS = ["marketplace"]


class MarketplaceTools:
    """Marketplace tools for the MCP server."""

    def __init__(self, marketplace_service: MarketplaceService, app_service=None):
        """Initialize marketplace tools.

        Args:
            marketplace_service: MarketplaceService instance for data operations
            app_service: AppService instance for local catalog operations
        """
        self.marketplace_service = marketplace_service
        self.app_service = app_service
        logger.info("Marketplace tools initialized")

    # ─────────────────────────────────────────────────────────────
    # Repository Management Tools
    # ─────────────────────────────────────────────────────────────

    async def list_repos(self) -> dict[str, Any]:
        """List all marketplace repositories.

        Returns all configured marketplace repositories with their status,
        app counts, and sync information.

        Returns:
            Dict with success status and repository data
        """
        try:
            repos = await self.marketplace_service.get_repos()
            return {
                "success": True,
                "data": [repo.model_dump(by_alias=True) for repo in repos],
            }
        except Exception as e:
            logger.error("List repos error", error=str(e))
            return {"success": False, "error": str(e)}

    async def add_repo(
        self, name: str, url: str, repo_type: str = "community", branch: str = "main"
    ) -> dict[str, Any]:
        """Add a new marketplace repository.

        Adds a Git repository as a marketplace source. The repository should
        contain app definitions in YAML format.

        Args:
            name: Display name for the repository
            url: Git repository URL (https)
            repo_type: Repository type (official, community, personal)
            branch: Git branch to sync from (default: main)

        Returns:
            Dict with success status and created repository data
        """
        try:
            await log_event(
                "marketplace",
                "INFO",
                f"Adding repository: {name}",
                MARKETPLACE_TAGS,
                {"url": url, "type": repo_type},
            )
            repo = await self.marketplace_service.add_repo(
                name=name, url=url, repo_type=RepoType(repo_type), branch=branch
            )
            await log_event(
                "marketplace",
                "INFO",
                f"Repository added: {name}",
                MARKETPLACE_TAGS,
                {"repo_id": repo.id},
            )
            return {
                "success": True,
                "data": repo.model_dump(by_alias=True),
                "message": f"Repository '{name}' added successfully",
            }
        except Exception as e:
            logger.error("Add repo error", error=str(e))
            await log_event(
                "marketplace",
                "ERROR",
                f"Failed to add repository: {name}",
                MARKETPLACE_TAGS,
                {"error": str(e)},
            )
            return {"success": False, "error": str(e)}

    async def remove_repo(self, repo_id: str) -> dict[str, Any]:
        """Remove a marketplace repository.

        Removes a repository and all its associated apps from the marketplace.
        This operation cannot be undone.

        Args:
            repo_id: Repository identifier

        Returns:
            Dict with success status and message
        """
        try:
            await log_event(
                "marketplace",
                "INFO",
                f"Removing repository: {repo_id}",
                MARKETPLACE_TAGS,
            )
            removed = await self.marketplace_service.remove_repo(repo_id)
            if removed:
                await log_event(
                    "marketplace",
                    "INFO",
                    f"Repository removed: {repo_id}",
                    MARKETPLACE_TAGS,
                )
            return {
                "success": removed,
                "message": "Repository removed" if removed else "Repository not found",
            }
        except Exception as e:
            logger.error("Remove repo error", error=str(e))
            await log_event(
                "marketplace",
                "ERROR",
                f"Failed to remove repository: {repo_id}",
                MARKETPLACE_TAGS,
                {"error": str(e)},
            )
            return {"success": False, "error": str(e)}

    async def sync_repo(self, repo_id: str) -> dict[str, Any]:
        """Sync apps from a repository.

        Clones or pulls the repository and syncs all app definitions.
        This updates the marketplace with the latest app information.

        Args:
            repo_id: Repository identifier

        Returns:
            Dict with success status and sync results
        """
        try:
            await log_event(
                "marketplace",
                "INFO",
                f"Syncing repository: {repo_id}",
                MARKETPLACE_TAGS,
            )
            apps = await self.marketplace_service.sync_repo(repo_id)
            await log_event(
                "marketplace",
                "INFO",
                f"Repository synced: {repo_id}",
                MARKETPLACE_TAGS,
                {"app_count": len(apps)},
            )
            return {
                "success": True,
                "data": {"appCount": len(apps)},
                "message": f"Synced {len(apps)} apps",
            }
        except Exception as e:
            logger.error("Sync repo error", error=str(e))
            await log_event(
                "marketplace",
                "ERROR",
                f"Failed to sync repository: {repo_id}",
                MARKETPLACE_TAGS,
                {"error": str(e)},
            )
            return {"success": False, "error": str(e)}

    async def toggle_repo(self, repo_id: str, enabled: bool) -> dict[str, Any]:
        """Enable or disable a marketplace repository.

        When disabled, the repository's apps will not appear in search results.

        Args:
            repo_id: Repository identifier
            enabled: True to enable, False to disable

        Returns:
            Dict with success status and message
        """
        try:
            action = "Enabling" if enabled else "Disabling"
            await log_event(
                "marketplace",
                "INFO",
                f"{action} repository: {repo_id}",
                MARKETPLACE_TAGS,
            )
            updated = await self.marketplace_service.toggle_repo(repo_id, enabled)
            if updated:
                action_done = "enabled" if enabled else "disabled"
                await log_event(
                    "marketplace",
                    "INFO",
                    f"Repository {action_done}: {repo_id}",
                    MARKETPLACE_TAGS,
                )
            return {
                "success": updated,
                "data": {"enabled": enabled},
                "message": f"Repository {'enabled' if enabled else 'disabled'}"
                if updated
                else "Repository not found",
            }
        except Exception as e:
            logger.error("Toggle repo error", error=str(e))
            await log_event(
                "marketplace",
                "ERROR",
                f"Failed to toggle repository: {repo_id}",
                MARKETPLACE_TAGS,
                {"error": str(e)},
            )
            return {"success": False, "error": str(e)}

    # ─────────────────────────────────────────────────────────────
    # App Search and Discovery Tools
    # ─────────────────────────────────────────────────────────────

    async def search_marketplace(
        self,
        search: str | None = None,
        category: str | None = None,
        tags: list[str] | None = None,
        featured: bool | None = None,
        sort_by: str = "name",
        limit: int = 50,
    ) -> dict[str, Any]:
        """Search marketplace apps.

        Search and filter apps in the marketplace with various criteria.

        Args:
            search: Search term for name or description
            category: Filter by category (e.g., media, utility)
            tags: Filter by tags (all must match)
            featured: Filter by featured status
            sort_by: Sort field (name, rating, popularity, updated)
            limit: Maximum results to return

        Returns:
            Dict with success status and matching apps
        """
        try:
            apps = await self.marketplace_service.search_apps(
                search=search,
                category=category,
                tags=tags,
                featured=featured,
                sort_by=sort_by,
                limit=limit,
            )
            return {
                "success": True,
                "data": {
                    "apps": [app.model_dump(by_alias=True) for app in apps],
                    "total": len(apps),
                },
            }
        except Exception as e:
            logger.error("Search marketplace error", error=str(e))
            return {"success": False, "error": str(e)}

    async def get_marketplace_app(self, app_id: str) -> dict[str, Any]:
        """Get details of a marketplace app.

        Retrieves full details for a specific app including Docker
        configuration, requirements, and ratings.

        Args:
            app_id: Application identifier

        Returns:
            Dict with success status and app details
        """
        try:
            app = await self.marketplace_service.get_app(app_id)
            if not app:
                return {"success": False, "error": "App not found"}
            return {"success": True, "data": app.model_dump(by_alias=True)}
        except Exception as e:
            logger.error("Get marketplace app error", error=str(e))
            return {"success": False, "error": str(e)}

    async def get_marketplace_categories(self) -> dict[str, Any]:
        """Get all marketplace categories with counts.

        Returns a list of all available categories in the marketplace
        with the number of apps in each category.

        Returns:
            Dict with success status and category list
        """
        try:
            categories = await self.marketplace_service.get_categories()
            return {"success": True, "data": categories}
        except Exception as e:
            logger.error("Get categories error", error=str(e))
            return {"success": False, "error": str(e)}

    async def get_featured_apps(self, limit: int = 10) -> dict[str, Any]:
        """Get featured marketplace apps.

        Returns curated featured apps from the marketplace.

        Args:
            limit: Maximum number of apps to return

        Returns:
            Dict with success status and featured apps
        """
        try:
            apps = await self.marketplace_service.get_featured_apps(limit)
            return {
                "success": True,
                "data": [app.model_dump(by_alias=True) for app in apps],
            }
        except Exception as e:
            logger.error("Get featured apps error", error=str(e))
            return {"success": False, "error": str(e)}

    async def get_trending_apps(self, limit: int = 10) -> dict[str, Any]:
        """Get trending marketplace apps.

        Returns apps sorted by recent popularity and install count.

        Args:
            limit: Maximum number of apps to return

        Returns:
            Dict with success status and trending apps
        """
        try:
            apps = await self.marketplace_service.get_trending_apps(limit)
            return {
                "success": True,
                "data": [app.model_dump(by_alias=True) for app in apps],
            }
        except Exception as e:
            logger.error("Get trending apps error", error=str(e))
            return {"success": False, "error": str(e)}

    # ─────────────────────────────────────────────────────────────
    # Rating Tools
    # ─────────────────────────────────────────────────────────────

    async def rate_marketplace_app(
        self, app_id: str, user_id: str, rating: int
    ) -> dict[str, Any]:
        """Rate a marketplace app (1-5 stars).

        Submit or update a rating for an app. Updates the app's average
        rating and rating count.

        Args:
            app_id: Application identifier
            user_id: User identifier
            rating: Rating value (1-5 stars)

        Returns:
            Dict with success status and rating confirmation
        """
        try:
            result = await self.marketplace_service.rate_app(app_id, user_id, rating)
            await log_event(
                "marketplace",
                "INFO",
                f"App rated: {app_id}",
                MARKETPLACE_TAGS,
                {"app_id": app_id, "user_id": user_id, "rating": rating},
            )
            return {
                "success": True,
                "data": result.model_dump(by_alias=True),
                "message": f"Rated {rating} stars",
            }
        except ValueError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error("Rate app error", error=str(e))
            await log_event(
                "marketplace",
                "ERROR",
                f"Failed to rate app: {app_id}",
                MARKETPLACE_TAGS,
                {"error": str(e)},
            )
            return {"success": False, "error": str(e)}

    async def import_app(self, app_id: str, user_id: str) -> dict[str, Any]:
        """Import a marketplace app to the local applications catalog.

        Copies app definition from marketplace to local catalog for deployment.
        This action is logged for audit purposes.

        Args:
            app_id: Application identifier from marketplace
            user_id: User performing the import

        Returns:
            Dict with success status and confirmation
        """
        try:
            # Get app details from marketplace
            marketplace_app = await self.marketplace_service.get_app(app_id)
            if not marketplace_app:
                return {"success": False, "error": "App not found in marketplace"}

            # Check if app_service is available
            if not self.app_service:
                return {"success": False, "error": "App service not configured"}

            # Convert marketplace app to local catalog format
            app_data = {
                "id": marketplace_app.id,
                "name": marketplace_app.name,
                "description": marketplace_app.description,
                "long_description": marketplace_app.long_description,
                "version": marketplace_app.version,
                "category": marketplace_app.category,
                "tags": marketplace_app.tags,
                "icon": marketplace_app.icon,
                "author": marketplace_app.author,
                "license": marketplace_app.license,
                "repository": marketplace_app.repository,
                "documentation": marketplace_app.documentation,
                "requirements": {
                    "min_ram": marketplace_app.requirements.min_ram
                    if marketplace_app.requirements
                    else None,
                    "min_storage": marketplace_app.requirements.min_storage
                    if marketplace_app.requirements
                    else None,
                    "architectures": marketplace_app.requirements.architectures
                    if marketplace_app.requirements
                    else [],
                },
                "avg_rating": marketplace_app.avg_rating,
                "featured": marketplace_app.featured,
            }

            # Add to local catalog
            await self.app_service.add_app(app_data)

            # Log the import action
            await log_event(
                "marketplace",
                "INFO",
                f"App imported: {marketplace_app.name}",
                MARKETPLACE_TAGS,
                {
                    "app_id": app_id,
                    "app_name": marketplace_app.name,
                    "user_id": user_id,
                    "category": marketplace_app.category,
                    "version": marketplace_app.version,
                },
            )

            return {
                "success": True,
                "data": {
                    "app_id": app_id,
                    "app_name": marketplace_app.name,
                    "version": marketplace_app.version,
                    "category": marketplace_app.category,
                },
                "message": f"App '{marketplace_app.name}' imported successfully",
            }
        except ValueError as e:
            # Handle "already exists" error gracefully
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error("Import app error", error=str(e))
            await log_event(
                "marketplace",
                "ERROR",
                f"App import failed: {app_id}",
                MARKETPLACE_TAGS,
                {"app_id": app_id, "user_id": user_id, "error": str(e)},
            )
            return {"success": False, "error": str(e)}
