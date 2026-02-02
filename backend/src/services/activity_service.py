"""
Activity Log Service

Tracks user actions and system events.
"""

import uuid
from datetime import datetime, UTC
from typing import Dict, Any, List
import structlog
from models.metrics import ActivityLog, ActivityType

logger = structlog.get_logger("activity_service")


class ActivityService:
    """Service for logging and querying activities."""

    def __init__(self, db_service):
        """Initialize activity service."""
        self.db_service = db_service
        logger.info("Activity service initialized")

    async def log_activity(
        self,
        activity_type: ActivityType,
        message: str,
        user_id: str = None,
        server_id: str = None,
        app_id: str = None,
        details: Dict[str, Any] = None
    ) -> ActivityLog:
        """Log an activity event."""
        try:
            log_entry = ActivityLog(
                id=f"act-{uuid.uuid4().hex[:8]}",
                activity_type=activity_type,
                user_id=user_id,
                server_id=server_id,
                app_id=app_id,
                message=message,
                details=details or {},
                timestamp=datetime.now(UTC).isoformat()
            )

            await self.db_service.save_activity_log(log_entry)
            logger.info(
                "Activity logged",
                type=activity_type.value,
                message=message
            )
            return log_entry

        except Exception as e:
            logger.error("Failed to log activity", error=str(e))
            raise

    async def get_recent_activities(self, limit: int = 20) -> List[ActivityLog]:
        """Get most recent activities."""
        try:
            return await self.db_service.get_activity_logs(limit=limit)
        except Exception as e:
            logger.error("Failed to get recent activities", error=str(e))
            return []

    async def get_activities(
        self,
        activity_types: List[ActivityType] = None,
        user_id: str = None,
        server_id: str = None,
        since: str = None,
        until: str = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[ActivityLog]:
        """Get activities with filters."""
        try:
            type_values = [t.value for t in activity_types] if activity_types else None

            return await self.db_service.get_activity_logs(
                activity_types=type_values,
                user_id=user_id,
                server_id=server_id,
                since=since,
                until=until,
                limit=limit,
                offset=offset
            )
        except Exception as e:
            logger.error("Failed to get activities", error=str(e))
            return []

    async def get_activity_count(
        self,
        activity_types: List[ActivityType] = None,
        since: str = None
    ) -> int:
        """Get count of activities matching filters."""
        try:
            type_values = [t.value for t in activity_types] if activity_types else None
            return await self.db_service.count_activity_logs(
                activity_types=type_values,
                since=since
            )
        except Exception as e:
            logger.error("Failed to count activities", error=str(e))
            return 0
