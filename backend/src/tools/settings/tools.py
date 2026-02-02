"""Settings-related MCP tools."""

from typing import Any, Dict, List, Optional, Tuple

import structlog
from fastmcp import Context

from models.settings import SettingCategory, SettingsRequest, SettingsUpdateRequest
from services.settings_service import SettingsService
from tools.common import log_event

logger = structlog.get_logger("settings_tools")

SETTINGS_TAGS = ["settings", "configuration"]


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
                await log_event("settings", "INFO", f"Settings updated by user: {active_user_id}", SETTINGS_TAGS, {
                    "user_id": active_user_id,
                    "setting_count": len(settings) if settings else 0,
                    "change_reason": change_reason,
                    "client_ip": client_ip
                })
            else:
                await log_event("settings", "WARNING", f"Settings update failed for user: {active_user_id}", SETTINGS_TAGS, {
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
            await log_event("settings", "ERROR", "Settings update error", SETTINGS_TAGS, {"error": str(exc)})
            return {
                "success": False,
                "message": f"Failed to update settings: {exc}",
                "error": "UPDATE_SETTINGS_ERROR",
            }

    async def reset_user_settings(
        self,
        user_id: Optional[str] = None,
        category: Optional[str] = None,
        ctx: Optional[Context] = None,
    ) -> Dict[str, Any]:
        """Reset user settings to system defaults by deleting user overrides."""
        try:
            logger.info("Resetting user settings", category=category)

            authenticated_user = await self._verify_authentication(ctx)
            active_user_id = authenticated_user or user_id
            if not active_user_id:
                return {
                    "success": False,
                    "message": "Authentication required",
                    "error": "AUTHENTICATION_REQUIRED",
                }

            # Parse category if provided
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

            client_ip, user_agent = await self._extract_client_info(ctx)
            response = await self._settings_service.reset_user_settings(
                user_id=active_user_id,
                category=parsed_category,
                client_ip=client_ip,
                user_agent=user_agent
            )

            if response.success:
                await log_event("settings", "INFO", f"User settings reset: {active_user_id}", SETTINGS_TAGS, {
                    "user_id": active_user_id,
                    "category": category,
                    "deleted_count": response.data.get("deleted_count") if response.data else 0
                })
            else:
                await log_event("settings", "WARNING", f"User settings reset failed: {active_user_id}", SETTINGS_TAGS, {
                    "user_id": active_user_id,
                    "error": response.error
                })

            return {
                "success": response.success,
                "message": response.message,
                "data": response.data,
                "error": response.error,
            }
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Failed to reset user settings", error=str(exc))
            await log_event("settings", "ERROR", "User settings reset error", SETTINGS_TAGS, {"error": str(exc)})
            return {
                "success": False,
                "message": f"Failed to reset user settings: {exc}",
                "error": "RESET_USER_SETTINGS_ERROR",
            }

    async def reset_system_settings(
        self,
        user_id: Optional[str] = None,
        category: Optional[str] = None,
        ctx: Optional[Context] = None,
    ) -> Dict[str, Any]:
        """Reset system settings to factory defaults (admin only)."""
        try:
            logger.info("Resetting system settings to defaults", category=category)

            authenticated_user = await self._verify_authentication(ctx)
            active_user_id = authenticated_user or user_id
            if not active_user_id:
                return {
                    "success": False,
                    "message": "Authentication required",
                    "error": "AUTHENTICATION_REQUIRED",
                }

            # Parse category if provided
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

            client_ip, user_agent = await self._extract_client_info(ctx)
            response = await self._settings_service.reset_system_settings(
                user_id=active_user_id,
                category=parsed_category,
                client_ip=client_ip,
                user_agent=user_agent
            )

            if response.success:
                await log_event("settings", "INFO", f"System settings reset by: {active_user_id}", SETTINGS_TAGS, {
                    "user_id": active_user_id,
                    "category": category,
                    "reset_count": response.data.get("reset_count") if response.data else 0
                })
            else:
                await log_event("settings", "WARNING", f"System settings reset failed: {active_user_id}", SETTINGS_TAGS, {
                    "user_id": active_user_id,
                    "error": response.error
                })

            return {
                "success": response.success,
                "message": response.message,
                "data": response.data,
                "error": response.error,
            }
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Failed to reset system settings", error=str(exc))
            await log_event("settings", "ERROR", "System settings reset error", SETTINGS_TAGS, {"error": str(exc)})
            return {
                "success": False,
                "message": f"Failed to reset system settings: {exc}",
                "error": "RESET_SYSTEM_SETTINGS_ERROR",
            }

    async def get_default_settings(
        self,
        category: Optional[str] = None,
        ctx: Optional[Context] = None,
    ) -> Dict[str, Any]:
        """Get factory default settings values."""
        try:
            logger.info("Getting default settings", category=category)

            # Parse category if provided
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

            response = await self._settings_service.get_default_settings(
                category=parsed_category
            )

            return {
                "success": response.success,
                "message": response.message,
                "data": response.data,
                "error": response.error,
            }
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Failed to get default settings", error=str(exc))
            return {
                "success": False,
                "message": f"Failed to get default settings: {exc}",
                "error": "GET_DEFAULTS_ERROR",
            }
