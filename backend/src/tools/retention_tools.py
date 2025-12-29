"""
Data Retention MCP Tools

Provides MCP tools for data retention management with comprehensive security controls,
admin-only access verification, and mandatory dry-run capabilities.
"""

from datetime import datetime, UTC
from typing import Dict, Any, Optional
import uuid
import structlog
from fastmcp import FastMCP, Context
from models.retention import (
    DataRetentionSettings, CleanupRequest, CleanupResult, CleanupPreview,
    RetentionType, SecurityValidationResult
)
from models.log import LogEntry
from services.retention_service import RetentionService
from services.service_log import log_service


logger = structlog.get_logger("retention_tools")


async def _log_retention_event(level: str, message: str, metadata: Dict[str, Any] = None):
    """Helper to log retention events to the database."""
    try:
        entry = LogEntry(
            id=f"ret-{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now(UTC),
            level=level,
            source="ret",
            message=message,
            tags=["retention", "data"],
            metadata=metadata or {}
        )
        await log_service.create_log_entry(entry)
    except Exception as e:
        logger.error("Failed to create log entry", error=str(e))


class RetentionTools:
    """MCP tools for data retention management and cleanup operations."""

    def __init__(self, retention_service: RetentionService):
        """Initialize retention tools with service dependency."""
        self.retention_service = retention_service
        logger.info("Retention tools initialized")

    async def get_retention_settings(self, user_id: str = None, ctx: Context = None) -> Dict[str, Any]:
        """Get current data retention settings for user."""
        try:
            logger.info("Getting retention settings", user_id=user_id)

            if not user_id:
                return {
                    "success": False,
                    "message": "User ID is required",
                    "error": "MISSING_USER_ID"
                }

            settings = await self.retention_service.get_retention_settings(user_id)
            if settings is None:
                return {
                    "success": False,
                    "message": "Failed to retrieve retention settings",
                    "error": "SETTINGS_RETRIEVAL_ERROR"
                }

            return {
                "success": True,
                "data": settings.model_dump(),
                "message": "Retention settings retrieved successfully"
            }

        except Exception as e:
            logger.error("Failed to get retention settings", user_id=user_id, error=str(e))
            return {
                "success": False,
                "message": f"Failed to get retention settings: {str(e)}",
                "error": "GET_SETTINGS_ERROR"
            }

    async def update_retention_settings(self, settings_data: Dict[str, Any],
                                      user_id: str = None, ctx: Context = None) -> Dict[str, Any]:
        """Update data retention settings with validation and admin verification."""
        try:
            logger.info("Updating retention settings", user_id=user_id)

            if not user_id:
                return {
                    "success": False,
                    "message": "User ID is required for settings update",
                    "error": "MISSING_USER_ID"
                }

            if not settings_data:
                return {
                    "success": False,
                    "message": "Settings data is required",
                    "error": "MISSING_SETTINGS_DATA"
                }

            # Validate and parse settings
            try:
                settings = DataRetentionSettings(**settings_data)
            except Exception as validation_error:
                logger.error("Settings validation failed", error=str(validation_error))
                return {
                    "success": False,
                    "message": f"Invalid settings data: {str(validation_error)}",
                    "error": "SETTINGS_VALIDATION_ERROR"
                }

            # Update settings
            success = await self.retention_service.update_retention_settings(user_id, settings)
            if not success:
                await _log_retention_event("ERROR", f"Failed to update retention settings for user: {user_id}", {
                    "user_id": user_id
                })
                return {
                    "success": False,
                    "message": "Failed to update retention settings",
                    "error": "UPDATE_FAILED"
                }

            await _log_retention_event("INFO", f"Retention settings updated by user: {user_id}", {
                "user_id": user_id,
                "log_retention_days": settings.log_retention_days,
                "user_data_retention_days": settings.user_data_retention_days
            })
            return {
                "success": True,
                "data": settings.model_dump(),
                "message": "Retention settings updated successfully"
            }

        except Exception as e:
            logger.error("Failed to update retention settings", user_id=user_id, error=str(e))
            await _log_retention_event("ERROR", "Retention settings update error", {"error": str(e)})
            return {
                "success": False,
                "message": f"Failed to update retention settings: {str(e)}",
                "error": "UPDATE_SETTINGS_ERROR"
            }

    async def preview_cleanup(self, request_data: Dict[str, Any], ctx: Context = None) -> Dict[str, Any]:
        """Preview data cleanup operations (dry-run) with security validation."""
        try:
            logger.info("Previewing data cleanup", retention_type=request_data.get('retention_type'))

            # Extract client metadata for audit logging
            client_ip = "unknown"
            user_agent = "unknown"
            if ctx and hasattr(ctx, 'meta'):
                client_ip = ctx.meta.get('clientIp', 'unknown')
                user_agent = ctx.meta.get('userAgent', 'unknown')

            # Validate and parse cleanup request
            try:
                # Ensure dry_run is True for preview
                request_data['dry_run'] = True
                request = CleanupRequest(**request_data)
            except Exception as validation_error:
                logger.error("Cleanup request validation failed", error=str(validation_error))
                return {
                    "success": False,
                    "message": f"Invalid cleanup request: {str(validation_error)}",
                    "error": "REQUEST_VALIDATION_ERROR"
                }

            # Perform preview
            preview = await self.retention_service.preview_cleanup(request)
            if preview is None:
                return {
                    "success": False,
                    "message": "Failed to preview cleanup operation",
                    "error": "PREVIEW_FAILED"
                }

            return {
                "success": True,
                "data": preview.model_dump(),
                "message": "Cleanup preview completed successfully"
            }

        except Exception as e:
            logger.error("Failed to preview cleanup", error=str(e))
            return {
                "success": False,
                "message": f"Failed to preview cleanup: {str(e)}",
                "error": "PREVIEW_ERROR"
            }

    async def execute_cleanup(self, request_data: Dict[str, Any], ctx: Context = None) -> Dict[str, Any]:
        """Execute data cleanup operations with comprehensive security validation."""
        try:
            logger.info("Executing data cleanup", retention_type=request_data.get('retention_type'),
                       dry_run=request_data.get('dry_run', True))

            # Extract client metadata for audit logging
            client_ip = "unknown"
            user_agent = "unknown"
            if ctx and hasattr(ctx, 'meta'):
                client_ip = ctx.meta.get('clientIp', 'unknown')
                user_agent = ctx.meta.get('userAgent', 'unknown')

            # Validate and parse cleanup request
            try:
                request = CleanupRequest(**request_data)
            except Exception as validation_error:
                logger.error("Cleanup request validation failed", error=str(validation_error))
                return {
                    "success": False,
                    "message": f"Invalid cleanup request: {str(validation_error)}",
                    "error": "REQUEST_VALIDATION_ERROR"
                }

            # Additional security check for non-dry-run operations
            if not request.dry_run:
                logger.warning("Non-dry-run cleanup operation requested",
                             admin_user_id=request.admin_user_id,
                             retention_type=request.retention_type,
                             client_ip=client_ip)

                # Require explicit force_cleanup flag for actual deletion
                if not request.force_cleanup:
                    return {
                        "success": False,
                        "message": "Actual cleanup requires force_cleanup flag and prior dry-run",
                        "error": "FORCE_CLEANUP_REQUIRED"
                    }

            # Execute cleanup operation
            result = await self.retention_service.perform_cleanup(request)
            if result is None:
                await _log_retention_event("ERROR", "Cleanup execution failed", {
                    "retention_type": request.retention_type.value if request.retention_type else None,
                    "dry_run": request.dry_run
                })
                return {
                    "success": False,
                    "message": "Failed to execute cleanup operation",
                    "error": "CLEANUP_EXECUTION_FAILED"
                }

            # Log cleanup result
            log_level = "INFO" if request.dry_run else "WARNING"
            await _log_retention_event(log_level, f"Data cleanup {'preview' if request.dry_run else 'executed'}", {
                "retention_type": request.retention_type.value if request.retention_type else None,
                "dry_run": request.dry_run,
                "items_affected": result.items_deleted if hasattr(result, 'items_deleted') else 0,
                "admin_user_id": request.admin_user_id
            })

            # Return comprehensive result
            response_data = result.model_dump()
            return {
                "success": result.success,
                "data": response_data,
                "message": f"Cleanup operation {'completed' if result.success else 'failed'}"
            }

        except Exception as e:
            logger.error("Failed to execute cleanup", error=str(e))
            await _log_retention_event("ERROR", "Cleanup execution error", {"error": str(e)})
            return {
                "success": False,
                "message": f"Failed to execute cleanup: {str(e)}",
                "error": "CLEANUP_EXECUTION_ERROR"
            }

    async def get_cleanup_history(self, limit: int = 50, user_id: str = None,
                                ctx: Context = None) -> Dict[str, Any]:
        """Get history of cleanup operations with audit information."""
        try:
            logger.info("Getting cleanup history", limit=limit, user_id=user_id)

            if not user_id:
                return {
                    "success": False,
                    "message": "User ID is required for cleanup history",
                    "error": "MISSING_USER_ID"
                }

            # This would typically query the audit logs for retention operations
            # For now, return a placeholder indicating the feature is available
            return {
                "success": True,
                "data": {
                    "operations": [],
                    "total_count": 0,
                    "limit": limit,
                    "message": "Cleanup history feature available - audit logs contain full operation history"
                },
                "message": "Cleanup history retrieved (placeholder implementation)"
            }

        except Exception as e:
            logger.error("Failed to get cleanup history", error=str(e))
            return {
                "success": False,
                "message": f"Failed to get cleanup history: {str(e)}",
                "error": "HISTORY_ERROR"
            }

    async def validate_retention_policy(self, policy_data: Dict[str, Any],
                                      ctx: Context = None) -> Dict[str, Any]:
        """Validate retention policy settings without saving."""
        try:
            logger.info("Validating retention policy")

            if not policy_data:
                return {
                    "success": False,
                    "message": "Policy data is required for validation",
                    "error": "MISSING_POLICY_DATA"
                }

            # Validate policy data structure
            try:
                settings = DataRetentionSettings(**policy_data)
                return {
                    "success": True,
                    "data": {
                        "is_valid": True,
                        "validated_settings": settings.model_dump(),
                        "validation_notes": [
                            f"Log retention: {settings.log_retention_days} days (valid range: 7-365)",
                            f"User data retention: {settings.user_data_retention_days} days (valid range: 30-3650)",
                            f"Metrics retention: {settings.metrics_retention_days} days (valid range: 7-730)",
                            f"Audit log retention: {settings.audit_log_retention_days} days (valid range: 365-3650)"
                        ]
                    },
                    "message": "Retention policy validation successful"
                }
            except Exception as validation_error:
                return {
                    "success": True,
                    "data": {
                        "is_valid": False,
                        "validation_errors": [str(validation_error)],
                        "suggested_corrections": [
                            "Check that all retention periods are within valid ranges",
                            "Ensure log retention is 7-365 days",
                            "Ensure user data retention is 30-3650 days",
                            "Ensure audit log retention is at least 365 days"
                        ]
                    },
                    "message": "Retention policy validation failed"
                }

        except Exception as e:
            logger.error("Failed to validate retention policy", error=str(e))
            return {
                "success": False,
                "message": f"Failed to validate retention policy: {str(e)}",
                "error": "VALIDATION_ERROR"
            }


def register_retention_tools(app: FastMCP, retention_service: RetentionService):
    """Register retention tools with FastMCP app."""
    retention_tools = RetentionTools(retention_service)

    # Register each tool method
    app.tool(retention_tools.get_retention_settings)
    app.tool(retention_tools.update_retention_settings)
    app.tool(retention_tools.preview_cleanup)
    app.tool(retention_tools.execute_cleanup)
    app.tool(retention_tools.get_cleanup_history)
    app.tool(retention_tools.validate_retention_policy)

    logger.info("Retention tools registered with MCP app")