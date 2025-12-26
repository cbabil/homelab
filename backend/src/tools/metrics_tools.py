"""
Monitoring and Metrics MCP Tools

Provides MCP tools for server metrics, activity logs, and dashboard.
"""

from typing import Dict, Any, List
import structlog
from fastmcp import FastMCP
from services.metrics_service import MetricsService
from services.activity_service import ActivityService
from services.dashboard_service import DashboardService
from models.metrics import ActivityType

logger = structlog.get_logger("metrics_tools")


class MetricsTools:
    """Metrics tools for the MCP server."""

    def __init__(self, metrics_service: MetricsService,
                 activity_service: ActivityService,
                 dashboard_service: DashboardService):
        """Initialize metrics tools."""
        self.metrics_service = metrics_service
        self.activity_service = activity_service
        self.dashboard_service = dashboard_service
        logger.info("Metrics tools initialized")

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

    async def get_activity_logs(
        self,
        activity_types: List[str] = None,
        server_id: str = None,
        user_id: str = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get activity logs with optional filters."""
        try:
            # Convert string types to enum
            types = None
            if activity_types:
                types = [ActivityType(t) for t in activity_types]

            logs = await self.activity_service.get_activities(
                activity_types=types,
                server_id=server_id,
                user_id=user_id,
                limit=limit,
                offset=offset
            )

            total = await self.activity_service.get_activity_count(activity_types=types)

            return {
                "success": True,
                "data": {
                    "logs": [log.model_dump() for log in logs],
                    "count": len(logs),
                    "total": total,
                    "limit": limit,
                    "offset": offset
                },
                "message": f"Retrieved {len(logs)} activity logs"
            }
        except Exception as e:
            logger.error("Get activity logs error", error=str(e))
            return {
                "success": False,
                "message": f"Failed to get activity logs: {str(e)}",
                "error": "GET_LOGS_ERROR"
            }

    async def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get aggregated dashboard data."""
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
                "message": "Dashboard summary retrieved"
            }
        except Exception as e:
            logger.error("Get dashboard summary error", error=str(e))
            return {
                "success": False,
                "message": f"Failed to get dashboard summary: {str(e)}",
                "error": "GET_DASHBOARD_ERROR"
            }


def register_metrics_tools(
    app: FastMCP,
    metrics_service: MetricsService,
    activity_service: ActivityService,
    dashboard_service: DashboardService
):
    """Register metrics tools with FastMCP app."""
    tools = MetricsTools(metrics_service, activity_service, dashboard_service)

    app.tool(tools.get_server_metrics)
    app.tool(tools.get_app_metrics)
    app.tool(tools.get_activity_logs)
    app.tool(tools.get_dashboard_summary)

    logger.info("Metrics tools registered")
