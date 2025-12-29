"""Settings-related MCP tools."""

from __future__ import annotations

from datetime import datetime, UTC
from typing import Any, Dict, List, Optional, Tuple
import uuid

import structlog
from fastmcp import Context

from models.settings import SettingCategory, SettingsRequest, SettingsUpdateRequest
from models.log import LogEntry
from services.settings_service import SettingsService
from services.service_log import log_service

logger = structlog.get_logger("settings_tools")


async def _log_settings_event(level: str, message: str, metadata: Dict[str, Any] = None):
    """Helper to log settings events to the database."""
    try:
        entry = LogEntry(
            id=f"set-{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now(UTC),
            level=level,
            source="set",
            message=message,
            tags=["settings", "configuration"],
            metadata=metadata or {}
        )
        await log_service.create_log_entry(entry)
    except Exception as e:
        logger.error("Failed to create log entry", error=str(e))


class SettingsTools:
    """Exposes settings management operations as FastMCP tools."""

    def __init__(self, settings_service: SettingsService) -> None:
        self._settings_service = settings_service

    async def _verify_authentication(self, ctx: Optional[Context]) -> Optional[str]:
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

    async def _extract_client_info(self, ctx: Optional[Context]) -> Tuple[str, str]:
        """Extract client IP and user agent metadata."""
        client_ip = "unknown"
        user_agent = "unknown"
        try:
            if ctx and hasattr(ctx, "meta") and ctx.meta:
                client_ip = ctx.meta.get("clientIp", client_ip)
                user_agent = ctx.meta.get("userAgent", user_agent)
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning("Failed to extract client info", error=str(exc))
        return client_ip, user_agent

    async def get_settings(
        self,
        user_id: Optional[str] = None,
        category: Optional[str] = None,
        setting_keys: Optional[List[str]] = None,
        include_system_defaults: bool = True,
        include_user_overrides: bool = True,
        ctx: Optional[Context] = None,
    ) -> Dict[str, Any]:
        """Return settings for the current or provided user."""
        try:
            logger.info("Getting settings", category=category, keys=setting_keys)

            authenticated_user = await self._verify_authentication(ctx)
            active_user_id = authenticated_user or user_id
            if not active_user_id:
                return {
                    "success": False,
                    "message": "Authentication required",
                    "error": "AUTHENTICATION_REQUIRED",
                }

            parsed_category: Optional[SettingCategory] = None
            if category:
                try:
                    parsed_category = SettingCategory(category)
                except ValueError:
                    return {
                        "success": False,
                        "message": f"Invalid category: {category}",
                        "error": "INVALID_CATEGORY",
                    }

            if setting_keys:
                for key in setting_keys:
                    if not isinstance(key, str) or not key.strip():
                        return {
                            "success": False,
                            "message": "Invalid setting key format",
                            "error": "INVALID_SETTING_KEY",
                        }

            request = SettingsRequest(
                user_id=active_user_id,
                category=parsed_category,
                setting_keys=setting_keys,
                include_system_defaults=include_system_defaults,
                include_user_overrides=include_user_overrides,
            )
            response = await self._settings_service.get_settings(request)
            return {
                "success": response.success,
                "message": response.message,
                "data": response.data,
                "error": response.error,
                "checksum": response.checksum,
            }
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Failed to get settings", error=str(exc))
            return {
                "success": False,
                "message": f"Failed to get settings: {exc}",
                "error": "GET_SETTINGS_ERROR",
            }

    async def update_settings(
        self,
        settings: Dict[str, Any],
        user_id: Optional[str] = None,
        change_reason: Optional[str] = None,
        validate_only: bool = False,
        ctx: Optional[Context] = None,
    ) -> Dict[str, Any]:
        """Update settings with validation and auditing."""
        try:
            logger.info(
                "Updating settings",
                setting_count=len(settings) if settings else 0,
                validate_only=validate_only,
            )

            authenticated_user = await self._verify_authentication(ctx)
            active_user_id = authenticated_user or user_id
            if not active_user_id:
                return {
                    "success": False,
                    "message": "Authentication required",
                    "error": "AUTHENTICATION_REQUIRED",
                }

            if validate_only:
                validation = await self._settings_service.validate_settings(
                    settings, active_user_id
                )
                return {
                    "success": validation.is_valid,
                    "message": "Settings validation completed",
                    "data": validation.model_dump(),
                }

            client_ip, user_agent = await self._extract_client_info(ctx)
            request = SettingsUpdateRequest(
                user_id=active_user_id,
                settings=settings,
                change_reason=change_reason,
                client_ip=client_ip,
                user_agent=user_agent,
            )
            response = await self._settings_service.update_settings(request)

            if response.success:
                await _log_settings_event("INFO", f"Settings updated by user: {active_user_id}", {
                    "user_id": active_user_id,
                    "setting_count": len(settings) if settings else 0,
                    "change_reason": change_reason,
                    "client_ip": client_ip
                })
            else:
                await _log_settings_event("WARNING", f"Settings update failed for user: {active_user_id}", {
                    "user_id": active_user_id,
                    "error": response.error
                })

            return {
                "success": response.success,
                "message": response.message,
                "data": response.data,
                "error": response.error,
                "checksum": response.checksum,
            }
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Failed to update settings", error=str(exc))
            await _log_settings_event("ERROR", "Settings update error", {"error": str(exc)})
            return {
                "success": False,
                "message": f"Failed to update settings: {exc}",
                "error": "UPDATE_SETTINGS_ERROR",
            }

    async def validate_settings(
        self,
        settings: Dict[str, Any],
        user_id: Optional[str] = None,
        ctx: Optional[Context] = None,
    ) -> Dict[str, Any]:
        """Validate settings without persisting changes."""
        try:
            authenticated_user = await self._verify_authentication(ctx)
            active_user_id = authenticated_user or user_id
            if not active_user_id:
                return {
                    "success": False,
                    "message": "Authentication required",
                    "error": "AUTHENTICATION_REQUIRED",
                }

            validation = await self._settings_service.validate_settings(
                settings, active_user_id
            )
            return {
                "success": validation.is_valid,
                "message": "Settings validation completed",
                "data": validation.model_dump(),
            }
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Failed to validate settings", error=str(exc))
            return {
                "success": False,
                "message": f"Failed to validate settings: {exc}",
                "error": "VALIDATE_SETTINGS_ERROR",
            }

    async def reset_user_settings(
        self,
        user_id: Optional[str] = None,
        ctx: Optional[Context] = None,
    ) -> Dict[str, Any]:
        """Reset user settings to system defaults (not yet implemented)."""
        authenticated_user = await self._verify_authentication(ctx)
        active_user_id = authenticated_user or user_id
        if not active_user_id:
            return {
                "success": False,
                "message": "Authentication required",
                "error": "AUTHENTICATION_REQUIRED",
            }

        logger.warning(
            "reset_user_settings invoked but not implemented", user_id=active_user_id
        )
        await _log_settings_event("WARNING", f"Settings reset attempted (not implemented): {active_user_id}", {
            "user_id": active_user_id
        })
        return {
            "success": False,
            "message": "Reset user settings is not implemented yet",
            "error": "NOT_IMPLEMENTED",
        }

    async def get_settings_audit(
        self,
        setting_key: Optional[str] = None,
        limit: int = 100,
        ctx: Optional[Context] = None,
    ) -> Dict[str, Any]:
        """Return settings audit entries for the authenticated user."""
        try:
            logger.info("Getting settings audit", key=setting_key, limit=limit)

            user_id = await self._verify_authentication(ctx)
            if not user_id:
                return {
                    "success": False,
                    "message": "Authentication required",
                    "error": "AUTHENTICATION_REQUIRED",
                }

            response = await self._settings_service.get_settings_audit(
                user_id=user_id,
                setting_key=setting_key,
                limit=limit,
            )
            return {
                "success": response.success,
                "message": response.message,
                "entries": response.entries,
                "error": response.error,
            }
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Failed to get settings audit", error=str(exc))
            return {
                "success": False,
                "message": f"Failed to get settings audit: {exc}",
                "error": "GET_SETTINGS_AUDIT_ERROR",
            }

    async def get_settings_schema(
        self,
        ctx: Optional[Context] = None,
    ) -> Dict[str, Any]:
        """Return settings schema for the authenticated user."""
        try:
            logger.info("Getting settings schema")

            user_id = await self._verify_authentication(ctx)
            if not user_id:
                return {
                    "success": False,
                    "message": "Authentication required",
                    "error": "AUTHENTICATION_REQUIRED",
                }

            response = await self._settings_service.get_settings_schema()
            return {
                "success": response.success,
                "message": response.message,
                "schema": response.schema,
                "error": response.error,
            }
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Failed to get settings schema", error=str(exc))
            return {
                "success": False,
                "message": f"Failed to get settings schema: {exc}",
                "error": "GET_SETTINGS_SCHEMA_ERROR",
            }


def register_settings_tools(app, settings_service: SettingsService, auth_service: Any = None) -> None:
    """Register all settings tools with the FastMCP application."""
    if auth_service is not None:
        logger.debug("register_settings_tools received auth_service", auth_service_type=type(auth_service).__name__)
    tools = SettingsTools(settings_service)
    app.tool(tools.get_settings)
    app.tool(tools.update_settings)
    app.tool(tools.validate_settings)
    app.tool(tools.reset_user_settings)
    app.tool(tools.get_settings_schema)
    app.tool(tools.get_settings_audit)
