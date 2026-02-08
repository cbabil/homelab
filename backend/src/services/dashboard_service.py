"""
Dashboard Service

Aggregates data for dashboard display.
"""

import asyncio

import structlog

from models.metrics import DashboardSummary
from models.server import ServerStatus

logger = structlog.get_logger("dashboard_service")


class DashboardService:
    """Service for dashboard data aggregation."""

    def __init__(
        self, server_service, deployment_service, metrics_service, activity_service
    ):
        """Initialize dashboard service."""
        self.server_service = server_service
        self.deployment_service = deployment_service
        self.metrics_service = metrics_service
        self.activity_service = activity_service
        logger.info("Dashboard service initialized")

    async def get_summary(self) -> DashboardSummary:
        """Get aggregated dashboard summary with parallel queries."""
        try:
            # Get server counts
            servers = await self.server_service.get_all_servers()
            total_servers = len(servers)
            online_servers = sum(
                1
                for s in servers
                if getattr(s, "status", None) == ServerStatus.CONNECTED
                or getattr(s, "status", "") == "connected"
            )
            offline_servers = total_servers - online_servers

            # Fetch app counts and metrics in parallel for all servers
            async def get_server_apps(server_id: str):
                try:
                    return await self.deployment_service.get_installed_apps(server_id)
                except Exception:
                    return []

            async def get_server_metrics_safe(server_id: str):
                try:
                    return await self.metrics_service.get_server_metrics(
                        server_id, period="1h"
                    )
                except Exception:
                    return None

            # Parallel fetch: apps for all servers, metrics for all servers, recent activities
            server_ids = [s.id for s in servers]
            apps_tasks = [get_server_apps(sid) for sid in server_ids]
            metrics_tasks = [get_server_metrics_safe(sid) for sid in server_ids]

            # Run all tasks in parallel
            (
                all_apps_results,
                all_metrics_results,
                recent_activities,
            ) = await asyncio.gather(
                asyncio.gather(*apps_tasks),
                asyncio.gather(*metrics_tasks),
                self.activity_service.get_recent_activities(limit=10),
            )

            # Count apps by status
            total_apps = 0
            running_apps = 0
            stopped_apps = 0
            error_apps = 0

            for apps in all_apps_results:
                for app in apps:
                    total_apps += 1
                    status = (
                        app.get("status", "")
                        if isinstance(app, dict)
                        else getattr(app, "status", "")
                    )
                    if status == "running":
                        running_apps += 1
                    elif status == "stopped":
                        stopped_apps += 1
                    elif status == "error":
                        error_apps += 1

            # Calculate average metrics
            cpu_values = []
            memory_values = []
            disk_values = []

            for metrics in all_metrics_results:
                if metrics:
                    latest = metrics[0]
                    cpu_values.append(latest.cpu_percent)
                    memory_values.append(latest.memory_percent)
                    disk_values.append(latest.disk_percent)

            avg_cpu = sum(cpu_values) / len(cpu_values) if cpu_values else 0.0
            avg_memory = (
                sum(memory_values) / len(memory_values) if memory_values else 0.0
            )
            avg_disk = sum(disk_values) / len(disk_values) if disk_values else 0.0

            return DashboardSummary(
                total_servers=total_servers,
                online_servers=online_servers,
                offline_servers=offline_servers,
                total_apps=total_apps,
                running_apps=running_apps,
                stopped_apps=stopped_apps,
                error_apps=error_apps,
                avg_cpu_percent=avg_cpu,
                avg_memory_percent=avg_memory,
                avg_disk_percent=avg_disk,
                recent_activities=recent_activities,
            )

        except Exception as e:
            logger.error("Failed to get dashboard summary", error=str(e))
            return DashboardSummary()
