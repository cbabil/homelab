"""Audit-related MCP tools."""

from typing import Any

import structlog
from fastmcp import Context

from models.log import LogFilter
from services.service_log import LogService
from services.settings_service import SettingsService
from tools.common import log_event

logger = structlog.get_logger("audit_tools")

AUDIT_TAGS = ["audit", "compliance"]


class AuditTools:
    """Exposes audit operations as FastMCP tools."""

    def __init__(
        self,
        settings_service: SettingsService,
        log_service: LogService | None = None,
    ) -> None:
        self._settings_service = settings_service
        self._log_service = log_service

    async def _verify_authentication(self, ctx: Context | None) -> str | None:
        """Return authenticated user id from context when present."""
        if not ctx:
            return None
        try:
            if hasattr(ctx, "meta") and ctx.meta:
                user_id = ctx.meta.get("userId")
                if user_id:
                    logger.debug("Authenticated user", user_id=user_id)
                    return user_id
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Authentication verification failed", error=str(exc))
        return None

    async def get_settings_audit(
        self,
        setting_key: str | None = None,
        filter_user_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
        user_id: str | None = None,
        ctx: Context | None = None,
    ) -> dict[str, Any]:
        """Get settings change audit trail (admin only).

        Returns a list of audit entries showing who changed what settings,
        when they changed them, and the before/after values.

        Args:
            setting_key: Optional filter for a specific setting key
            filter_user_id: Optional filter for entries made by a specific user
            limit: Maximum number of entries to return (default 100)
            offset: Number of entries to skip for pagination (default 0)
            user_id: User ID for authentication (from context or parameter)
            ctx: FastMCP context with authentication info

        Returns:
            Dict with success status and audit entries list
        """
        try:
            logger.info(
                "Getting settings audit",
                setting_key=setting_key,
                filter_user_id=filter_user_id,
                limit=limit,
                offset=offset,
            )

            authenticated_user = await self._verify_authentication(ctx)
            active_user_id = authenticated_user or user_id
            if not active_user_id:
                return {
                    "success": False,
                    "message": "Authentication required",
                    "error": "AUTHENTICATION_REQUIRED",
                }

            response = await self._settings_service.get_settings_audit(
                user_id=active_user_id,
                setting_key=setting_key,
                filter_user_id=filter_user_id,
                limit=limit,
                offset=offset,
            )

            if response.success:
                await log_event(
                    "aud",
                    "INFO",
                    f"Settings audit accessed by: {active_user_id}",
                    AUDIT_TAGS,
                    {
                        "user_id": active_user_id,
                        "setting_key": setting_key,
                        "filter_user_id": filter_user_id,
                        "limit": limit,
                        "offset": offset,
                    },
                )
            else:
                await log_event(
                    "aud",
                    "WARNING",
                    f"Settings audit access denied: {active_user_id}",
                    AUDIT_TAGS,
                    {"user_id": active_user_id, "error": response.error},
                )

            return {
                "success": response.success,
                "message": response.message,
                "data": response.data,
                "error": response.error,
            }
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Failed to get settings audit", error=str(exc))
            await log_event(
                "aud", "ERROR", "Settings audit error", AUDIT_TAGS, {"error": str(exc)}
            )
            return {
                "success": False,
                "message": f"Failed to get settings audit: {exc}",
                "error": "AUDIT_ERROR",
            }

    async def get_auth_audit(
        self,
        event_type: str | None = None,
        username: str | None = None,
        success_only: bool | None = None,
        limit: int = 100,
        offset: int = 0,
        user_id: str | None = None,
        ctx: Context | None = None,
    ) -> dict[str, Any]:
        """Get authentication audit trail (admin only).

        Returns a list of security events including login attempts,
        logouts, and other authentication events.

        Args:
            event_type: Filter by event type (LOGIN, LOGOUT, etc.)
            username: Filter by username involved in the event
            success_only: Filter by success status (True=success, False=failure, None=all)
            limit: Maximum number of entries to return (default 100)
            offset: Number of entries to skip for pagination (default 0)
            user_id: User ID for authentication (from context or parameter)
            ctx: FastMCP context with authentication info

        Returns:
            Dict with success status and audit entries list
        """
        try:
            logger.info(
                "Getting auth audit",
                event_type=event_type,
                username=username,
                limit=limit,
                offset=offset,
            )

            authenticated_user = await self._verify_authentication(ctx)
            active_user_id = authenticated_user or user_id
            if not active_user_id:
                return {
                    "success": False,
                    "message": "Authentication required",
                    "error": "AUTHENTICATION_REQUIRED",
                }

            # Check admin access via settings service
            is_admin = await self._settings_service.verify_admin_access(active_user_id)
            if not is_admin:
                await log_event(
                    "aud",
                    "WARNING",
                    f"Auth audit access denied: {active_user_id}",
                    AUDIT_TAGS,
                    {"user_id": active_user_id, "error": "ADMIN_REQUIRED"},
                )
                return {
                    "success": False,
                    "message": "Admin privileges required to access auth audit",
                    "error": "ADMIN_REQUIRED",
                }

            # Query log_entries with source='auth' for security events
            log_filter = LogFilter(source="auth", limit=limit, offset=offset)
            logs = await self._log_service.get_logs(log_filter)

            # Transform and filter logs
            audit_entries: list[dict[str, Any]] = []
            for log in logs:
                metadata = log.metadata or {}

                # Apply filters
                if event_type and metadata.get("event_type") != event_type:
                    continue
                if username and metadata.get("username") != username:
                    continue
                if success_only is not None and metadata.get("success") != success_only:
                    continue

                audit_entries.append(
                    {
                        "id": log.id,
                        "timestamp": log.timestamp.isoformat()
                        if log.timestamp
                        else None,
                        "level": log.level,
                        "event_type": metadata.get("event_type"),
                        "username": metadata.get("username"),
                        "success": metadata.get("success"),
                        "client_ip": metadata.get("client_ip"),
                        "user_agent": metadata.get("user_agent"),
                        "message": log.message,
                        "tags": log.tags,
                    }
                )

            await log_event(
                "aud",
                "INFO",
                f"Auth audit accessed by: {active_user_id}",
                AUDIT_TAGS,
                {
                    "user_id": active_user_id,
                    "event_type": event_type,
                    "username": username,
                    "limit": limit,
                    "offset": offset,
                    "count": len(audit_entries),
                },
            )

            return {
                "success": True,
                "message": f"Retrieved {len(audit_entries)} auth audit entries",
                "data": {"audit_entries": audit_entries},
            }
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Failed to get auth audit", error=str(exc))
            await log_event(
                "aud", "ERROR", "Auth audit error", AUDIT_TAGS, {"error": str(exc)}
            )
            return {
                "success": False,
                "message": f"Failed to get auth audit: {exc}",
                "error": "AUDIT_ERROR",
            }

    async def get_agent_audit(
        self,
        server_id: str | None = None,
        event_type: str | None = None,
        success_only: bool | None = None,
        level: str | None = None,
        limit: int = 100,
        offset: int = 0,
        user_id: str | None = None,
        ctx: Context | None = None,
    ) -> dict[str, Any]:
        """Get agent audit trail (admin only).

        Returns a list of agent lifecycle events including installs,
        connections, disconnections, and errors.

        Args:
            server_id: Filter by server ID
            event_type: Filter by event type (AGENT_INSTALLED, AGENT_CONNECTED, etc.)
            success_only: Filter by success status (True=success, False=failure, None=all)
            level: Filter by log level (INFO, WARNING, ERROR)
            limit: Maximum number of entries to return (default 100)
            offset: Number of entries to skip for pagination (default 0)
            user_id: User ID for authentication (from context or parameter)
            ctx: FastMCP context with authentication info

        Returns:
            Dict with success status and audit entries list
        """
        try:
            logger.info(
                "Getting agent audit",
                server_id=server_id,
                event_type=event_type,
                limit=limit,
                offset=offset,
            )

            authenticated_user = await self._verify_authentication(ctx)
            active_user_id = authenticated_user or user_id
            if not active_user_id:
                return {
                    "success": False,
                    "message": "Authentication required",
                    "error": "AUTHENTICATION_REQUIRED",
                }

            is_admin = await self._settings_service.verify_admin_access(active_user_id)
            if not is_admin:
                await log_event(
                    "aud",
                    "WARNING",
                    f"Agent audit access denied: {active_user_id}",
                    AUDIT_TAGS,
                    {"user_id": active_user_id, "error": "ADMIN_REQUIRED"},
                )
                return {
                    "success": False,
                    "message": "Admin privileges required to access agent audit",
                    "error": "ADMIN_REQUIRED",
                }

            # Get total count of agent logs in database for accurate reporting
            db_total = await self._log_service.count_logs(
                LogFilter(source="agent", level=level)
            )

            # Fetch agent logs (filtering by metadata happens in memory)
            # Use a high limit to get logs for filtering and pagination
            fetch_limit = 1000
            log_filter = LogFilter(
                source="agent", level=level, limit=fetch_limit, offset=0
            )
            logs = await self._log_service.get_logs(log_filter)

            # Apply metadata filters in memory
            filtered_entries: list[dict[str, Any]] = []
            for log in logs:
                metadata = log.metadata or {}

                if server_id and metadata.get("server_id") != server_id:
                    continue
                if event_type and metadata.get("event_type") != event_type:
                    continue
                if success_only is not None and metadata.get("success") != success_only:
                    continue

                filtered_entries.append(
                    {
                        "id": log.id,
                        "timestamp": log.timestamp.isoformat()
                        if log.timestamp
                        else None,
                        "level": log.level,
                        "event_type": metadata.get("event_type"),
                        "server_id": metadata.get("server_id"),
                        "server_name": metadata.get("server_name"),
                        "agent_id": metadata.get("agent_id"),
                        "success": metadata.get("success"),
                        "message": log.message,
                        "details": metadata.get("details", {}),
                        "tags": log.tags,
                    }
                )

            # Get total count before pagination
            total_count = len(filtered_entries)

            # Warn if results may be truncated
            truncated = db_total > fetch_limit

            # Apply pagination manually
            paginated_entries = filtered_entries[offset : offset + limit]

            await log_event(
                "aud",
                "INFO",
                f"Agent audit accessed by: {active_user_id}",
                AUDIT_TAGS,
                {
                    "user_id": active_user_id,
                    "server_id": server_id,
                    "event_type": event_type,
                    "limit": limit,
                    "offset": offset,
                    "count": len(paginated_entries),
                    "total": total_count,
                    "truncated": truncated,
                },
            )

            message = f"Retrieved {len(paginated_entries)} of {total_count} agent audit entries"
            if truncated:
                message += (
                    f" (showing most recent {fetch_limit} of {db_total} total logs)"
                )

            return {
                "success": True,
                "message": message,
                "data": {
                    "audit_entries": paginated_entries,
                    "total": total_count,
                    "truncated": truncated,
                },
            }
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Failed to get agent audit", error=str(exc))
            await log_event(
                "aud", "ERROR", "Agent audit error", AUDIT_TAGS, {"error": str(exc)}
            )
            return {
                "success": False,
                "message": f"Failed to get agent audit: {exc}",
                "error": "AUDIT_ERROR",
            }
