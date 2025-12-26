"""
Monitoring and Logging Tools

Provides system monitoring, log management, and metrics collection for the MCP server.
Implements comprehensive observability features for homelab infrastructure.
"""

from typing import Dict, Any, Optional

from fastmcp import Context
import structlog
from services.monitoring_service import MonitoringService


logger = structlog.get_logger("monitoring_tools")


def register_monitoring_tools(app, monitoring_service: MonitoringService):
    """Register monitoring tools with the FastMCP app."""
    
    @app.tool
    async def get_system_metrics() -> Dict[str, Any]:
        """
        Get current system metrics and performance data.
        
        Returns:
            dict: System metrics including CPU, memory, disk, and network usage
        """
        try:
            metrics = monitoring_service.get_current_metrics()
            
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
    
    @app.tool
    async def get_logs(
        level: Optional[str] = None,
        source: Optional[str] = None,
        limit: Optional[int] = None,
        page: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get system and application logs with optional filtering."""
        try:
            # Build filters from individual parameters
            filters = {}
            if level:
                filters['level'] = level
            if source:
                filters['source'] = source
            if limit:
                filters['limit'] = limit
            if page:
                filters['page'] = page

            # Use the log service instead of monitoring service
            from services.service_log import log_service
            from models.log import LogFilter

            # Convert filters to LogFilter
            log_filter = LogFilter(
                level=level,
                source=source,
                limit=limit or 100,
                offset=((page or 1) - 1) * (limit or 100) if page else 0
            )

            logs = await log_service.get_logs(log_filter)

            # Convert to the format expected by frontend
            log_dicts = []
            for log in logs:
                log_dict = {
                    'id': log.id,
                    'timestamp': log.timestamp.isoformat(),
                    'level': log.level,
                    'source': log.source,
                    'message': log.message,
                    'tags': log.tags,
                    'metadata': log.metadata,
                    'session_id': log.metadata.get('session_id') if log.metadata else None,
                    'created_at': log.created_at.isoformat() if log.created_at else None
                }
                log_dicts.append(log_dict)

            logger.info("Logs retrieved", count=len(log_dicts))

            return {
                "success": True,
                "data": {
                    "logs": log_dicts,
                    "total": len(log_dicts),
                    "filtered": bool(filters)
                },
                "message": f"Retrieved {len(log_dicts)} log entries"
            }

        except Exception as e:
            logger.error("Failed to get logs", error=str(e))
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"Failed to get logs: {str(e)}",
                "error": "LOGS_ERROR"
            }

    @app.tool
    async def purge_logs() -> Dict[str, Any]:
        """Delete all log entries from the database."""
        try:
            from services.service_log import log_service

            deleted = await log_service.purge_logs()
            logger.info("Logs purged via MCP tool", deleted=deleted)

            return {
                "success": True,
                "message": f"Purged {deleted} log entries",
                "deleted": deleted
            }
        except Exception as e:
            logger.error("Failed to purge logs", error=str(e))
            return {
                "success": False,
                "message": f"Failed to purge logs: {str(e)}",
                "error": "PURGE_LOGS_ERROR"
            }
    
    logger.info("Monitoring tools registered")
