"""
Marketplace MCP Tools

Provides MCP tools for managing marketplace repositories and apps.
"""

from typing import Dict, Any, List, Optional
import structlog
from fastmcp import FastMCP
from services.marketplace_service import MarketplaceService
from models.marketplace import RepoType

logger = structlog.get_logger("marketplace_tools")


class MarketplaceTools:
    """Marketplace tools for the MCP server."""

    def __init__(self, marketplace_service: MarketplaceService):
        """Initialize marketplace tools.

        Args:
            marketplace_service: MarketplaceService instance for data operations
        """
        self.marketplace_service = marketplace_service
        logger.info("Marketplace tools initialized")

    # ─────────────────────────────────────────────────────────────
    # Repository Management Tools
    # ─────────────────────────────────────────────────────────────

    async def list_repos(self) -> Dict[str, Any]:
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
                "data": [repo.model_dump(by_alias=True) for repo in repos]
            }
        except Exception as e:
            logger.error("List repos error", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }

    async def add_repo(
        self,
        name: str,
        url: str,
        repo_type: str = "community",
        branch: str = "main"
    ) -> Dict[str, Any]:
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
            repo = await self.marketplace_service.add_repo(
                name=name,
                url=url,
                repo_type=RepoType(repo_type),
                branch=branch
            )
            return {
                "success": True,
                "data": repo.model_dump(by_alias=True),
                "message": f"Repository '{name}' added successfully"
            }
        except Exception as e:
            logger.error("Add repo error", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }

    async def remove_repo(self, repo_id: str) -> Dict[str, Any]:
        """Remove a marketplace repository.

        Removes a repository and all its associated apps from the marketplace.
        This operation cannot be undone.

        Args:
            repo_id: Repository identifier

        Returns:
            Dict with success status and message
        """
        try:
            removed = await self.marketplace_service.remove_repo(repo_id)
            return {
                "success": removed,
                "message": "Repository removed" if removed else "Repository not found"
            }
        except Exception as e:
            logger.error("Remove repo error", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }

    async def sync_repo(self, repo_id: str) -> Dict[str, Any]:
        """Sync apps from a repository.

        Clones or pulls the repository and syncs all app definitions.
        This updates the marketplace with the latest app information.

        Args:
            repo_id: Repository identifier

        Returns:
            Dict with success status and sync results
        """
        try:
            apps = await self.marketplace_service.sync_repo(repo_id)
            return {
                "success": True,
                "data": {"app_count": len(apps)},
                "message": f"Synced {len(apps)} apps"
            }
        except Exception as e:
            logger.error("Sync repo error", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }

    # ─────────────────────────────────────────────────────────────
    # App Search and Discovery Tools
    # ─────────────────────────────────────────────────────────────

    async def search_marketplace(
        self,
        search: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        featured: Optional[bool] = None,
        sort_by: str = "name",
        limit: int = 50
    ) -> Dict[str, Any]:
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
                limit=limit
            )
            return {
                "success": True,
                "data": {
                    "apps": [app.model_dump(by_alias=True) for app in apps],
                    "total": len(apps)
                }
            }
        except Exception as e:
            logger.error("Search marketplace error", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }

    async def get_marketplace_app(self, app_id: str) -> Dict[str, Any]:
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
                return {
                    "success": False,
                    "error": "App not found"
                }
            return {
                "success": True,
                "data": app.model_dump(by_alias=True)
            }
        except Exception as e:
            logger.error("Get marketplace app error", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }

    async def get_marketplace_categories(self) -> Dict[str, Any]:
        """Get all marketplace categories with counts.

        Returns a list of all available categories in the marketplace
        with the number of apps in each category.

        Returns:
            Dict with success status and category list
        """
        try:
            categories = await self.marketplace_service.get_categories()
            return {
                "success": True,
                "data": categories
            }
        except Exception as e:
            logger.error("Get categories error", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }

    async def get_featured_apps(self, limit: int = 10) -> Dict[str, Any]:
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
                "data": [app.model_dump(by_alias=True) for app in apps]
            }
        except Exception as e:
            logger.error("Get featured apps error", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }

    async def get_trending_apps(self, limit: int = 10) -> Dict[str, Any]:
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
                "data": [app.model_dump(by_alias=True) for app in apps]
            }
        except Exception as e:
            logger.error("Get trending apps error", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }

    # ─────────────────────────────────────────────────────────────
    # Rating Tools
    # ─────────────────────────────────────────────────────────────

    async def rate_marketplace_app(
        self,
        app_id: str,
        user_id: str,
        rating: int
    ) -> Dict[str, Any]:
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
            return {
                "success": True,
                "data": result.model_dump(by_alias=True),
                "message": f"Rated {rating} stars"
            }
        except ValueError as e:
            return {
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            logger.error("Rate app error", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }


def register_marketplace_tools(app: FastMCP, marketplace_service: MarketplaceService):
    """Register marketplace tools with FastMCP app.

    Args:
        app: FastMCP application instance
        marketplace_service: MarketplaceService instance
    """
    tools = MarketplaceTools(marketplace_service)

    app.tool(tools.list_repos)
    app.tool(tools.add_repo)
    app.tool(tools.remove_repo)
    app.tool(tools.sync_repo)
    app.tool(tools.search_marketplace)
    app.tool(tools.get_marketplace_app)
    app.tool(tools.get_marketplace_categories)
    app.tool(tools.get_featured_apps)
    app.tool(tools.get_trending_apps)
    app.tool(tools.rate_marketplace_app)

    logger.info("Marketplace tools registered")
