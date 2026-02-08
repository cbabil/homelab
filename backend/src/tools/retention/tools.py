"""
Retention Tools

Provides data retention management capabilities for the MCP server.
Implements preview and cleanup operations with CSRF protection.
"""

from typing import Any

import structlog
from fastmcp import Context

from models.retention import CleanupRequest, RetentionSettings, RetentionType
from services.csrf_service import csrf_service
from services.retention_service import RetentionService

logger = structlog.get_logger("retention_tools")


class RetentionTools:
    """Data retention management tools for the MCP server."""

    def __init__(self, retention_service: RetentionService = None, auth_service=None):
        """Initialize retention tools.

        Args:
            retention_service: Retention service instance.
            auth_service: Auth service for permission checks.
        """
        self.retention_service = retention_service or RetentionService()
        self.auth_service = auth_service
        logger.info("Retention tools initialized")

    def _get_user_context(self, ctx: Context) -> tuple:
        """Extract user context from request.

        Returns:
            Tuple of (user_id, session_id, role, session_token)
        """
        meta = getattr(ctx, "meta", {}) or {}
        user_id = meta.get("user_id", "")
        session_id = meta.get("session_id", "")
        role = meta.get("role", "user")
        session_token = meta.get("token", "")
        return user_id, session_id, role, session_token

    def _is_admin(self, role: str) -> bool:
        """Check if user has admin role."""
        return role == "admin"

    async def get_csrf_token(
        self, params: dict[str, Any], ctx: Context
    ) -> dict[str, Any]:
        """Generate a CSRF token for retention operations.

        Returns:
            CSRF token for use in cleanup operations.
        """
        try:
            user_id, session_id, role, _ = self._get_user_context(ctx)

            if not user_id:
                return {
                    "success": False,
                    "message": "User not authenticated",
                    "error": "AUTH_REQUIRED",
                }

            if not self._is_admin(role):
                return {
                    "success": False,
                    "message": "Admin privileges required",
                    "error": "PERMISSION_DENIED",
                }

            token = csrf_service.generate_token(user_id, session_id)

            return {
                "success": True,
                "data": {"csrf_token": token},
                "message": "CSRF token generated",
            }

        except Exception as e:
            logger.error("Failed to generate CSRF token", error=str(e))
            return {
                "success": False,
                "message": f"Failed to generate token: {str(e)}",
                "error": "TOKEN_ERROR",
            }

    async def preview_retention_cleanup(
        self, params: dict[str, Any], ctx: Context
    ) -> dict[str, Any]:
        """Preview cleanup operations without performing deletion (dry-run).

        Params:
            retention_type: Type of data to preview (logs, user_data, metrics, audit_logs)

        Returns:
            Preview of records that would be deleted.
        """
        try:
            user_id, session_id, role, session_token = self._get_user_context(ctx)

            if not user_id:
                return {
                    "success": False,
                    "message": "User not authenticated",
                    "error": "AUTH_REQUIRED",
                }

            if not self._is_admin(role):
                return {
                    "success": False,
                    "message": "Admin privileges required for retention operations",
                    "error": "PERMISSION_DENIED",
                }

            retention_type_str = params.get("retention_type", "logs")
            try:
                retention_type = RetentionType(retention_type_str)
            except ValueError:
                return {
                    "success": False,
                    "message": f"Invalid retention type: {retention_type_str}",
                    "error": "INVALID_TYPE",
                }

            # Create cleanup request (dry_run=True for preview)
            request = CleanupRequest(
                retention_type=retention_type,
                dry_run=True,
                admin_user_id=user_id,
                session_token=session_token,
            )

            preview = await self.retention_service.preview_cleanup(request)

            if not preview:
                return {
                    "success": False,
                    "message": "Failed to generate preview",
                    "error": "PREVIEW_ERROR",
                }

            return {
                "success": True,
                "data": {
                    "retention_type": preview.retention_type.value,
                    "affected_records": preview.affected_records,
                    "oldest_record_date": preview.oldest_record_date,
                    "newest_record_date": preview.newest_record_date,
                    "estimated_space_freed_mb": preview.estimated_space_freed_mb,
                    "cutoff_date": preview.cutoff_date,
                },
                "message": f"Preview: {preview.affected_records} records would be deleted",
            }

        except Exception as e:
            logger.error("Failed to preview cleanup", error=str(e))
            return {
                "success": False,
                "message": f"Preview failed: {str(e)}",
                "error": "PREVIEW_ERROR",
            }

    async def perform_retention_cleanup(
        self, params: dict[str, Any], ctx: Context
    ) -> dict[str, Any]:
        """Perform data cleanup with CSRF protection.

        Params:
            retention_type: Type of data to clean (logs, user_data, metrics, audit_logs)
            csrf_token: Required CSRF token for destructive operation
            batch_size: Optional batch size for deletion (default 1000)

        Returns:
            Cleanup result with records affected.
        """
        try:
            user_id, session_id, role, session_token = self._get_user_context(ctx)

            if not user_id:
                return {
                    "success": False,
                    "message": "User not authenticated",
                    "error": "AUTH_REQUIRED",
                }

            if not self._is_admin(role):
                return {
                    "success": False,
                    "message": "Admin privileges required for cleanup operations",
                    "error": "PERMISSION_DENIED",
                }

            # Validate CSRF token
            csrf_token = params.get("csrf_token")
            if not csrf_token:
                return {
                    "success": False,
                    "message": "CSRF token required for cleanup operations",
                    "error": "CSRF_REQUIRED",
                }

            is_valid, error_msg = csrf_service.validate_token(
                csrf_token, user_id, session_id, consume=True
            )
            if not is_valid:
                return {
                    "success": False,
                    "message": f"CSRF validation failed: {error_msg}",
                    "error": "CSRF_INVALID",
                }

            retention_type_str = params.get("retention_type", "logs")
            try:
                retention_type = RetentionType(retention_type_str)
            except ValueError:
                return {
                    "success": False,
                    "message": f"Invalid retention type: {retention_type_str}",
                    "error": "INVALID_TYPE",
                }

            batch_size = params.get("batch_size", 1000)

            # Create cleanup request (dry_run=False, force_cleanup=True)
            request = CleanupRequest(
                retention_type=retention_type,
                dry_run=False,
                force_cleanup=True,
                admin_user_id=user_id,
                session_token=session_token,
                csrf_token=csrf_token,
                batch_size=batch_size,
            )

            result = await self.retention_service.perform_cleanup(request)

            if not result:
                return {
                    "success": False,
                    "message": "Cleanup operation failed",
                    "error": "CLEANUP_ERROR",
                }

            if not result.success:
                return {
                    "success": False,
                    "message": result.error_message or "Cleanup failed",
                    "error": "CLEANUP_ERROR",
                }

            return {
                "success": True,
                "data": {
                    "operation_id": result.operation_id,
                    "retention_type": result.retention_type.value,
                    "records_affected": result.records_affected,
                    "space_freed_mb": result.space_freed_mb,
                    "duration_seconds": result.duration_seconds,
                    "start_time": result.start_time,
                    "end_time": result.end_time,
                },
                "message": f"Cleanup complete: {result.records_affected} records deleted, {result.space_freed_mb} MB freed",
            }

        except Exception as e:
            logger.error("Cleanup operation failed", error=str(e))
            return {
                "success": False,
                "message": f"Cleanup failed: {str(e)}",
                "error": "CLEANUP_ERROR",
            }

    async def get_retention_settings(
        self, params: dict[str, Any], ctx: Context
    ) -> dict[str, Any]:
        """Get current retention settings.

        Returns:
            Current retention settings.
        """
        try:
            user_id, _, role, _ = self._get_user_context(ctx)

            if not user_id:
                return {
                    "success": False,
                    "message": "User not authenticated",
                    "error": "AUTH_REQUIRED",
                }

            if not self._is_admin(role):
                return {
                    "success": False,
                    "message": "Admin privileges required",
                    "error": "PERMISSION_DENIED",
                }

            settings = await self.retention_service.get_retention_settings(user_id)

            if not settings:
                return {
                    "success": False,
                    "message": "Settings not found",
                    "error": "NOT_FOUND",
                }

            return {
                "success": True,
                "data": settings.model_dump(),
                "message": "Retention settings retrieved",
            }

        except Exception as e:
            logger.error("Failed to get retention settings", error=str(e))
            return {
                "success": False,
                "message": f"Failed to get settings: {str(e)}",
                "error": "GET_ERROR",
            }

    async def update_retention_settings(
        self, params: dict[str, Any], ctx: Context
    ) -> dict[str, Any]:
        """Update retention settings.

        Params:
            log_retention: Log retention settings object
            data_retention: Data retention settings object

        Returns:
            Updated retention settings.
        """
        try:
            user_id, _, role, _ = self._get_user_context(ctx)

            if not user_id:
                return {
                    "success": False,
                    "message": "User not authenticated",
                    "error": "AUTH_REQUIRED",
                }

            if not self._is_admin(role):
                return {
                    "success": False,
                    "message": "Admin privileges required",
                    "error": "PERMISSION_DENIED",
                }

            # Build settings from params
            settings_data = {}
            if "log_retention" in params:
                settings_data["log_retention"] = params["log_retention"]
            if "data_retention" in params:
                settings_data["data_retention"] = params["data_retention"]

            settings = RetentionSettings(**settings_data)

            success = await self.retention_service.update_retention_settings(
                user_id, settings
            )

            if not success:
                return {
                    "success": False,
                    "message": "Failed to update settings",
                    "error": "UPDATE_ERROR",
                }

            # Return updated settings
            updated_settings = await self.retention_service.get_retention_settings(
                user_id
            )

            return {
                "success": True,
                "data": updated_settings.model_dump()
                if updated_settings
                else settings.model_dump(),
                "message": "Retention settings updated",
            }

        except Exception as e:
            logger.error("Failed to update retention settings", error=str(e))
            return {
                "success": False,
                "message": f"Failed to update settings: {str(e)}",
                "error": "UPDATE_ERROR",
            }
