"""
System Monitoring Tools

Provides system, server, app, dashboard, and marketplace metrics collection for the MCP server.
"""

from typing import Dict, Any

import structlog
from services.monitoring_service import MonitoringService
from services.metrics_service import MetricsService
from services.dashboard_service import DashboardService
from services.marketplace_service import MarketplaceService


logger = structlog.get_logger("monitoring_tools")


class MonitoringTools:
    """Monitoring tools for the MCP server."""

    def __init__(
        self,
        monitoring_service: MonitoringService,
        metrics_service: MetricsService,
        dashboard_service: DashboardService,
        marketplace_service: MarketplaceService
    ):
        """Initialize monitoring tools.

        Args:
            monitoring_service: Service for system monitoring.
            metrics_service: Service for metrics collection.
            dashboard_service: Service for dashboard data.
            marketplace_service: Service for marketplace data.
        """
        self.monitoring_service = monitoring_service
        self.metrics_service = metrics_service
        self.dashboard_service = dashboard_service
        self.marketplace_service = marketplace_service
        logger.info("Monitoring tools initialized")

    async def get_system_metrics(self) -> Dict[str, Any]:
        """
        Get current system metrics and performance data.

        Returns:
            dict: System metrics including CPU, memory, disk, and network usage
        """
        try:
            metrics = self.monitoring_service.get_current_metrics()

            logger.info("System metrics retrieved")

            return {
                "success": True,
                "data": metrics,
                "message": "System metrics retrieved successfully"
            }

        except Exception as e:
            logger.error("Failed to get system metrics", error=str(e))
            return {
                "success": False,
                "message": f"Failed to get metrics: {str(e)}",
                "error": "METRICS_ERROR"
            }

    async def get_server_metrics(
        self,
        server_id: str,
        period: str = "24h"
    ) -> Dict[str, Any]:
        """Get server metrics for a time period."""
        try:
            metrics = await self.metrics_service.get_server_metrics(server_id, period)

            return {
                "success": True,
                "data": {
                    "server_id": server_id,
                    "period": period,
                    "metrics": [m.model_dump() for m in metrics],
                    "count": len(metrics)
                },
                "message": f"Retrieved {len(metrics)} metric records"
            }
        except Exception as e:
            logger.error("Get server metrics error", error=str(e))
            return {
                "success": False,
                "message": f"Failed to get metrics: {str(e)}",
                "error": "GET_METRICS_ERROR"
            }

    async def get_app_metrics(
        self,
        server_id: str,
        app_id: str = None,
        period: str = "24h"
    ) -> Dict[str, Any]:
        """Get container metrics for an app."""
        try:
            metrics = await self.metrics_service.get_container_metrics(
                server_id=server_id,
                container_name=app_id,
                period=period
            )

            return {
                "success": True,
                "data": {
                    "server_id": server_id,
                    "app_id": app_id,
                    "period": period,
                    "metrics": [m.model_dump() for m in metrics],
                    "count": len(metrics)
                },
                "message": f"Retrieved {len(metrics)} container metrics"
            }
        except Exception as e:
            logger.error("Get app metrics error", error=str(e))
            return {
                "success": False,
                "message": f"Failed to get app metrics: {str(e)}",
                "error": "GET_APP_METRICS_ERROR"
            }

    async def get_dashboard_metrics(self) -> Dict[str, Any]:
        """Get aggregated dashboard metrics."""
        try:
            summary = await self.dashboard_service.get_summary()

            return {
                "success": True,
                "data": {
                    "total_servers": summary.total_servers,
                    "online_servers": summary.online_servers,
                    "offline_servers": summary.offline_servers,
                    "total_apps": summary.total_apps,
                    "running_apps": summary.running_apps,
                    "stopped_apps": summary.stopped_apps,
                    "error_apps": summary.error_apps,
                    "avg_cpu_percent": summary.avg_cpu_percent,
                    "avg_memory_percent": summary.avg_memory_percent,
                    "avg_disk_percent": summary.avg_disk_percent,
                    "recent_activities": [a.model_dump() for a in summary.recent_activities]
                },
                "message": "Dashboard metrics retrieved"
            }
        except Exception as e:
            logger.error("Get dashboard metrics error", error=str(e))
            return {
                "success": False,
                "message": f"Failed to get dashboard metrics: {str(e)}",
                "error": "GET_DASHBOARD_METRICS_ERROR"
            }

    async def get_marketplace_metrics(self) -> Dict[str, Any]:
        """Get marketplace statistics and metrics."""
        try:
            repos = await self.marketplace_service.get_repos()
            apps = await self.marketplace_service.search_apps(limit=10000)
            categories = await self.marketplace_service.get_categories()

            # Calculate aggregate statistics
            enabled_repos = [r for r in repos if r.enabled]
            synced_repos = [r for r in repos if r.last_synced is not None]

            # Apps with ratings
            rated_apps = [a for a in apps if a.rating_count > 0]
            total_ratings = sum(a.rating_count for a in apps)
            avg_rating = (
                sum(a.avg_rating * a.rating_count for a in rated_apps) / total_ratings
                if total_ratings > 0 else 0.0
            )

            # Featured apps
            featured_apps = [a for a in apps if a.featured]

            return {
                "success": True,
                "data": {
                    "total_repos": len(repos),
                    "enabled_repos": len(enabled_repos),
                    "synced_repos": len(synced_repos),
                    "total_apps": len(apps),
                    "featured_apps": len(featured_apps),
                    "categories": categories,
                    "category_count": len(categories),
                    "total_ratings": total_ratings,
                    "avg_rating": round(avg_rating, 2),
                    "rated_apps": len(rated_apps)
                },
                "message": "Marketplace metrics retrieved"
            }
        except Exception as e:
            logger.error("Get marketplace metrics error", error=str(e))
            return {
                "success": False,
                "message": f"Failed to get marketplace metrics: {str(e)}",
                "error": "GET_MARKETPLACE_METRICS_ERROR"
            }
