"""
Notification Tools

Provides notification management capabilities for the MCP server.
Implements CRUD operations with role-based access control.
"""

from typing import Any

import structlog
from fastmcp import Context

from models.notification import NotificationType
from services.notification_service import NotificationService

logger = structlog.get_logger("notification_tools")


class NotificationTools:
    """Notification management tools for the MCP server."""

    def __init__(self, notification_service: NotificationService, auth_service=None):
        """Initialize notification tools.

        Args:
            notification_service: Notification service instance.
            auth_service: Auth service for permission checks.
        """
        self.notification_service = notification_service
        self.auth_service = auth_service
        logger.info("Notification tools initialized")

    def _get_user_context(self, ctx: Context) -> tuple:
        """Extract user context from request.

        Returns:
            Tuple of (user_id, role)
        """
        meta = getattr(ctx, "meta", {}) or {}
        user_id = meta.get("user_id", "")
        role = meta.get("role", "user")
        return user_id, role

    def _is_admin(self, role: str) -> bool:
        """Check if user has admin role."""
        return role == "admin"

    async def list_notifications(
        self, params: dict[str, Any], ctx: Context
    ) -> dict[str, Any]:
        """List notifications for the current user.

        Params:
            read: Optional - Filter by read status (true/false)
            type: Optional - Filter by notification type (info/success/warning/error)
            limit: Optional - Max notifications to return (default 50)
            offset: Optional - Pagination offset (default 0)

        Returns:
            List of notifications with counts.
        """
        try:
            user_id, _ = self._get_user_context(ctx)

            if not user_id:
                return {
                    "success": False,
                    "message": "User not authenticated",
                    "error": "AUTH_REQUIRED",
                }

            read_filter = params.get("read")
            if read_filter is not None:
                read_filter = read_filter in (True, "true", "1", 1)

            notification_type = None
            if params.get("type"):
                try:
                    notification_type = NotificationType(params["type"])
                except ValueError:
                    return {
                        "success": False,
                        "message": f"Invalid notification type: {params['type']}",
                        "error": "INVALID_TYPE",
                    }

            limit = params.get("limit", 50)
            offset = params.get("offset", 0)

            result = await self.notification_service.list_notifications(
                user_id=user_id,
                read_filter=read_filter,
                notification_type=notification_type,
                limit=limit,
                offset=offset,
            )

            return {
                "success": True,
                "data": {
                    "notifications": [n.model_dump() for n in result.notifications],
                    "total": result.total,
                    "unread_count": result.unread_count,
                },
                "message": f"Found {len(result.notifications)} notifications",
            }

        except Exception as e:
            logger.error("Failed to list notifications", error=str(e))
            return {
                "success": False,
                "message": f"Failed to list notifications: {str(e)}",
                "error": "LIST_ERROR",
            }

    async def get_notification(
        self, params: dict[str, Any], ctx: Context
    ) -> dict[str, Any]:
        """Get a single notification by ID.

        Params:
            notification_id: Required - Notification ID to retrieve

        Returns:
            Notification details.
        """
        try:
            user_id, _ = self._get_user_context(ctx)
            notification_id = params.get("notification_id")

            if not notification_id:
                return {
                    "success": False,
                    "message": "notification_id is required",
                    "error": "MISSING_PARAM",
                }

            notification = await self.notification_service.get_notification(
                notification_id
            )

            if not notification:
                return {
                    "success": False,
                    "message": "Notification not found",
                    "error": "NOT_FOUND",
                }

            # Permission check
            if notification.user_id != user_id:
                return {
                    "success": False,
                    "message": "Permission denied: cannot access other users' notifications",
                    "error": "PERMISSION_DENIED",
                }

            return {
                "success": True,
                "data": notification.model_dump(),
                "message": "Notification retrieved",
            }

        except Exception as e:
            logger.error("Failed to get notification", error=str(e))
            return {
                "success": False,
                "message": f"Failed to get notification: {str(e)}",
                "error": "GET_ERROR",
            }

    async def create_notification(
        self, params: dict[str, Any], ctx: Context
    ) -> dict[str, Any]:
        """Create a notification. Admin only or system use.

        Params:
            user_id: Required - Target user ID
            type: Required - Notification type (info/success/warning/error)
            title: Required - Notification title
            message: Required - Notification message
            source: Optional - Source of notification
            metadata: Optional - Additional data as JSON

        Returns:
            Created notification.
        """
        try:
            current_user_id, role = self._get_user_context(ctx)

            # Only admins can create notifications for other users
            target_user_id = params.get("user_id", current_user_id)
            if not self._is_admin(role) and target_user_id != current_user_id:
                return {
                    "success": False,
                    "message": "Permission denied: admin only can create notifications for others",
                    "error": "PERMISSION_DENIED",
                }

            notification_type = params.get("type")
            title = params.get("title")
            message = params.get("message")

            if not all([notification_type, title, message]):
                return {
                    "success": False,
                    "message": "type, title, and message are required",
                    "error": "MISSING_PARAM",
                }

            try:
                notif_type = NotificationType(notification_type)
            except ValueError:
                return {
                    "success": False,
                    "message": f"Invalid notification type: {notification_type}",
                    "error": "INVALID_TYPE",
                }

            notification = await self.notification_service.create_notification(
                user_id=target_user_id,
                notification_type=notif_type,
                title=title,
                message=message,
                source=params.get("source"),
                metadata=params.get("metadata"),
            )

            return {
                "success": True,
                "data": notification.model_dump(),
                "message": "Notification created",
            }

        except Exception as e:
            logger.error("Failed to create notification", error=str(e))
            return {
                "success": False,
                "message": f"Failed to create notification: {str(e)}",
                "error": "CREATE_ERROR",
            }

    async def mark_notification_read(
        self, params: dict[str, Any], ctx: Context
    ) -> dict[str, Any]:
        """Mark a notification as read.

        Params:
            notification_id: Required - Notification ID to mark as read

        Returns:
            Success status.
        """
        try:
            user_id, _ = self._get_user_context(ctx)
            notification_id = params.get("notification_id")

            if not notification_id:
                return {
                    "success": False,
                    "message": "notification_id is required",
                    "error": "MISSING_PARAM",
                }

            updated = await self.notification_service.mark_as_read(
                notification_id, user_id
            )

            return {
                "success": True,
                "data": {"updated": updated},
                "message": (
                    "Notification marked as read"
                    if updated
                    else "Notification not found or already read"
                ),
            }

        except Exception as e:
            logger.error("Failed to mark notification as read", error=str(e))
            return {
                "success": False,
                "message": f"Failed to mark notification as read: {str(e)}",
                "error": "UPDATE_ERROR",
            }

    async def mark_all_notifications_read(
        self, params: dict[str, Any], ctx: Context
    ) -> dict[str, Any]:
        """Mark all notifications as read for the current user.

        Returns:
            Count of notifications marked as read.
        """
        try:
            user_id, _ = self._get_user_context(ctx)

            if not user_id:
                return {
                    "success": False,
                    "message": "User not authenticated",
                    "error": "AUTH_REQUIRED",
                }

            count = await self.notification_service.mark_all_as_read(user_id)

            return {
                "success": True,
                "data": {"count": count},
                "message": f"Marked {count} notification(s) as read",
            }

        except Exception as e:
            logger.error("Failed to mark all notifications as read", error=str(e))
            return {
                "success": False,
                "message": f"Failed to mark all notifications as read: {str(e)}",
                "error": "UPDATE_ERROR",
            }

    async def dismiss_notification(
        self, params: dict[str, Any], ctx: Context
    ) -> dict[str, Any]:
        """Dismiss (remove) a notification.

        Params:
            notification_id: Required - Notification ID to dismiss

        Returns:
            Success status.
        """
        try:
            user_id, _ = self._get_user_context(ctx)
            notification_id = params.get("notification_id")

            if not notification_id:
                return {
                    "success": False,
                    "message": "notification_id is required",
                    "error": "MISSING_PARAM",
                }

            dismissed = await self.notification_service.dismiss_notification(
                notification_id, user_id
            )

            return {
                "success": True,
                "data": {"dismissed": dismissed},
                "message": (
                    "Notification dismissed"
                    if dismissed
                    else "Notification not found or already dismissed"
                ),
            }

        except Exception as e:
            logger.error("Failed to dismiss notification", error=str(e))
            return {
                "success": False,
                "message": f"Failed to dismiss notification: {str(e)}",
                "error": "DISMISS_ERROR",
            }

    async def dismiss_all_notifications(
        self, params: dict[str, Any], ctx: Context
    ) -> dict[str, Any]:
        """Dismiss all notifications for the current user.

        Returns:
            Count of notifications dismissed.
        """
        try:
            user_id, _ = self._get_user_context(ctx)

            if not user_id:
                return {
                    "success": False,
                    "message": "User not authenticated",
                    "error": "AUTH_REQUIRED",
                }

            count = await self.notification_service.dismiss_all(user_id)

            return {
                "success": True,
                "data": {"count": count},
                "message": f"Dismissed {count} notification(s)",
            }

        except Exception as e:
            logger.error("Failed to dismiss all notifications", error=str(e))
            return {
                "success": False,
                "message": f"Failed to dismiss all notifications: {str(e)}",
                "error": "DISMISS_ERROR",
            }

    async def get_unread_count(
        self, params: dict[str, Any], ctx: Context
    ) -> dict[str, Any]:
        """Get unread notification count for the current user.

        Returns:
            Unread count and total.
        """
        try:
            user_id, _ = self._get_user_context(ctx)

            if not user_id:
                return {
                    "success": False,
                    "message": "User not authenticated",
                    "error": "AUTH_REQUIRED",
                }

            result = await self.notification_service.get_unread_count(user_id)

            return {
                "success": True,
                "data": result.model_dump(),
                "message": f"{result.unread_count} unread notification(s)",
            }

        except Exception as e:
            logger.error("Failed to get unread count", error=str(e))
            return {
                "success": False,
                "message": f"Failed to get unread count: {str(e)}",
                "error": "COUNT_ERROR",
            }
