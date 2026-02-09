"""
Account Management Tools

Handles user account operations: lookup, avatar, and lock management.
Part of the authentication tools module.
"""

from typing import Any

import structlog
from fastmcp import Context

from services.auth_service import AuthService

logger = structlog.get_logger("account_tools")


class AccountTools:
    """Account management tools for the MCP server."""

    # Maximum avatar size: 500KB base64 (roughly 375KB image)
    _MAX_AVATAR_SIZE = 500 * 1024

    def __init__(self, auth_service: AuthService):
        """Initialize account tools with auth service."""
        self.auth_service = auth_service

    async def get_user_by_username(
        self, params: dict[str, Any], ctx: Context = None
    ) -> dict[str, Any]:
        """Get user information by username.

        SECURITY: Requires authentication.

        Args:
            params: Dictionary containing:
                - token: JWT token for authentication
                - username: The username to look up

        Returns:
            Dictionary with user info (without sensitive fields).
        """
        try:
            token = params.get("token")
            if not token:
                return {
                    "success": False,
                    "message": "Authentication token is required",
                    "error": "MISSING_TOKEN",
                }

            payload = self.auth_service._validate_jwt_token(token)
            if not payload:
                return {
                    "success": False,
                    "message": "Invalid or expired authentication token",
                    "error": "INVALID_TOKEN",
                }

            username = params.get("username")
            if not username:
                return {
                    "success": False,
                    "message": "Username is required",
                    "error": "MISSING_USERNAME",
                }

            user = await self.auth_service.db_service.get_user_by_username(username)

            if not user:
                return {
                    "success": False,
                    "message": "User not found",
                    "error": "NOT_FOUND",
                }

            # Return safe user info (no password hash)
            return {
                "success": True,
                "data": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role.value
                    if hasattr(user.role, "value")
                    else user.role,
                    "is_active": user.is_active,
                    "created_at": user.created_at.isoformat()
                    if hasattr(user.created_at, "isoformat")
                    else str(user.created_at),
                    "updated_at": user.updated_at.isoformat()
                    if hasattr(user.updated_at, "isoformat")
                    else str(user.updated_at),
                },
            }

        except Exception as e:
            logger.error(
                "Failed to get user by username",
                username=params.get("username"),
                error=str(e),
            )
            return {
                "success": False,
                "message": f"Failed to get user: {str(e)}",
                "error": "GET_USER_ERROR",
            }

    async def update_avatar(
        self, params: dict[str, Any], ctx: Context = None
    ) -> dict[str, Any]:
        """Update the authenticated user's avatar.

        Args:
            params: Dictionary containing:
                - token: JWT token for authentication
                - avatar: Base64 data URL of the image
                         or None/empty string to remove avatar

        Returns:
            Dictionary with success status.
        """
        try:
            token = params.get("token")
            avatar = params.get("avatar")

            # Validate token
            if not token:
                return {
                    "success": False,
                    "message": "Authentication token is required",
                    "error": "MISSING_TOKEN",
                }

            # Validate JWT token and get user
            payload = self.auth_service._validate_jwt_token(token)
            if not payload:
                return {
                    "success": False,
                    "message": "Invalid or expired authentication token",
                    "error": "INVALID_TOKEN",
                }

            user_id = payload.get("user_id")
            user = (
                await self.auth_service.get_user_by_id(user_id) if user_id else None
            )

            if not user or not user.is_active:
                return {
                    "success": False,
                    "message": "User not found or inactive",
                    "error": "USER_INACTIVE",
                }

            # Validate avatar data
            if avatar:
                # Check if it's a valid data URL
                if not avatar.startswith("data:image/"):
                    return {
                        "success": False,
                        "message": "Avatar must be a valid image data URL",
                        "error": "INVALID_FORMAT",
                    }

                # Check allowed image types
                allowed_types = [
                    "data:image/png;base64,",
                    "data:image/jpeg;base64,",
                    "data:image/jpg;base64,",
                    "data:image/gif;base64,",
                    "data:image/webp;base64,",
                ]
                if not any(avatar.startswith(t) for t in allowed_types):
                    return {
                        "success": False,
                        "message": "Avatar must be PNG, JPEG, GIF, or WebP",
                        "error": "INVALID_IMAGE_TYPE",
                    }

                # Check size limit
                if len(avatar) > self._MAX_AVATAR_SIZE:
                    max_kb = self._MAX_AVATAR_SIZE // 1024
                    return {
                        "success": False,
                        "message": f"Avatar is too large. Maximum size is {max_kb}KB",
                        "error": "AVATAR_TOO_LARGE",
                    }

            # Update avatar (None or empty string removes it)
            avatar_to_save = avatar if avatar else None
            success = await self.auth_service.db_service.update_user_avatar(
                user_id, avatar_to_save
            )

            if not success:
                logger.error(
                    "Failed to update avatar in database", user_id=user_id
                )
                return {
                    "success": False,
                    "message": "Failed to update avatar",
                    "error": "UPDATE_FAILED",
                }

            logger.info(
                "Avatar updated successfully",
                user_id=user_id,
                has_avatar=avatar_to_save is not None,
            )

            return {
                "success": True,
                "message": "Avatar updated successfully"
                if avatar_to_save
                else "Avatar removed successfully",
            }

        except Exception as e:
            logger.error(
                "Avatar update error",
                error=str(e),
                error_type=type(e).__name__,
            )
            return {
                "success": False,
                "message": "An error occurred while updating avatar",
                "error": "UPDATE_ERROR",
            }

    async def get_locked_accounts(
        self, params: dict[str, Any], ctx: Context = None
    ) -> dict[str, Any]:
        """Get locked accounts - either all or filtered by identifier.

        SECURITY: Requires admin authentication.

        Args:
            params: Dictionary containing:
                - token: JWT token for authentication (must be admin)
                - identifier: Optional - filter by username or IP
                - identifier_type: Optional - 'username' or 'ip'
                - lock_id: Optional - get specific lock by ID
                - include_expired: Whether to include expired locks
                - include_unlocked: Whether to include manually unlocked

        Returns:
            Dictionary with locked account(s).
        """
        try:
            token = params.get("token")
            identifier = params.get("identifier")
            identifier_type = params.get("identifier_type")
            lock_id = params.get("lock_id")
            include_expired = params.get("include_expired", False)
            include_unlocked = params.get("include_unlocked", False)

            # Validate token
            if not token:
                return {
                    "success": False,
                    "message": "Authentication token is required",
                    "error": "MISSING_TOKEN",
                }

            # Validate JWT token and check admin role
            payload = self.auth_service._validate_jwt_token(token)
            if not payload:
                return {
                    "success": False,
                    "message": "Invalid or expired authentication token",
                    "error": "INVALID_TOKEN",
                }

            user_id = payload.get("user_id")
            user = (
                await self.auth_service.get_user_by_id(user_id) if user_id else None
            )

            if not user or not user.is_active:
                return {
                    "success": False,
                    "message": "User not found or inactive",
                    "error": "USER_INACTIVE",
                }

            # Check admin role
            if user.role.value != "admin":
                logger.warning(
                    "Non-admin user attempted to get locked accounts",
                    username=user.username,
                    role=user.role.value,
                )
                return {
                    "success": False,
                    "message": "Admin privileges required",
                    "error": "ADMIN_REQUIRED",
                }

            # Get by lock_id if provided
            if lock_id:
                lock_info = await self.auth_service.db_service.get_lock_by_id(
                    lock_id
                )
                if not lock_info:
                    return {
                        "success": False,
                        "message": "Lock record not found",
                        "error": "NOT_FOUND",
                    }
                return {
                    "success": True,
                    "data": {"locked_account": lock_info, "count": 1},
                    "message": "Lock record found",
                }

            # Get by identifier if provided
            if identifier:
                if not identifier_type:
                    return {
                        "success": False,
                        "message": "identifier_type is required when identifier is provided",
                        "error": "MISSING_IDENTIFIER_TYPE",
                    }
                if identifier_type not in ("username", "ip"):
                    return {
                        "success": False,
                        "message": "identifier_type must be 'username' or 'ip'",
                        "error": "INVALID_IDENTIFIER_TYPE",
                    }

                (
                    is_locked,
                    lock_info,
                ) = await self.auth_service.db_service.is_account_locked(
                    identifier, identifier_type
                )

                if not lock_info:
                    return {
                        "success": True,
                        "data": {
                            "locked_account": None,
                            "is_locked": False,
                            "count": 0,
                        },
                        "message": f"No lock found for {identifier_type} '{identifier}'",
                    }

                return {
                    "success": True,
                    "data": {
                        "locked_account": lock_info,
                        "is_locked": is_locked,
                        "count": 1,
                    },
                    "message": f"Lock found for {identifier_type} '{identifier}'",
                }

            # Get all locked accounts
            locked_accounts = (
                await self.auth_service.db_service.get_locked_accounts(
                    include_expired=include_expired,
                    include_unlocked=include_unlocked,
                )
            )

            logger.info(
                "Retrieved locked accounts",
                count=len(locked_accounts),
                admin=user.username,
            )

            return {
                "success": True,
                "data": {
                    "locked_accounts": locked_accounts,
                    "count": len(locked_accounts),
                },
                "message": f"Found {len(locked_accounts)} locked account(s)",
            }

        except Exception as e:
            logger.error(
                "Get locked accounts error",
                error=str(e),
                error_type=type(e).__name__,
            )
            return {
                "success": False,
                "message": "An error occurred while getting locked accounts",
                "error": "GET_ERROR",
            }

    async def update_account_lock(
        self, params: dict[str, Any], ctx: Context = None
    ) -> dict[str, Any]:
        """Update account lock status (lock or unlock).

        SECURITY: Requires admin authentication.

        Args:
            params: Dictionary containing:
                - token: JWT token for authentication (must be admin)
                - lock_id: ID of the lock record to update
                - locked: Boolean - True to lock, False to unlock
                - notes: Optional notes about the action

        Returns:
            Dictionary with success status.
        """
        try:
            token = params.get("token")
            lock_id = params.get("lock_id")
            locked = params.get("locked")
            notes = params.get("notes")

            # Validate required fields
            if not token:
                return {
                    "success": False,
                    "message": "Authentication token is required",
                    "error": "MISSING_TOKEN",
                }

            if not lock_id:
                return {
                    "success": False,
                    "message": "Lock ID is required",
                    "error": "MISSING_LOCK_ID",
                }

            if locked is None:
                return {
                    "success": False,
                    "message": "locked parameter is required (true or false)",
                    "error": "MISSING_LOCKED_PARAM",
                }

            # Validate JWT token and check admin role
            payload = self.auth_service._validate_jwt_token(token)
            if not payload:
                return {
                    "success": False,
                    "message": "Invalid or expired authentication token",
                    "error": "INVALID_TOKEN",
                }

            user_id = payload.get("user_id")
            user = (
                await self.auth_service.get_user_by_id(user_id) if user_id else None
            )

            if not user or not user.is_active:
                return {
                    "success": False,
                    "message": "User not found or inactive",
                    "error": "USER_INACTIVE",
                }

            # Check admin role
            if user.role.value != "admin":
                logger.warning(
                    "Non-admin user attempted to update account lock",
                    username=user.username,
                    role=user.role.value,
                    lock_id=lock_id,
                )
                return {
                    "success": False,
                    "message": "Admin privileges required",
                    "error": "ADMIN_REQUIRED",
                }

            # Get lock info
            lock_info = await self.auth_service.db_service.get_lock_by_id(lock_id)
            if not lock_info:
                return {
                    "success": False,
                    "message": "Lock record not found",
                    "error": "LOCK_NOT_FOUND",
                }

            if locked:
                # Re-lock the account
                success = await self.auth_service.db_service.lock_account(
                    lock_id=lock_id,
                    locked_by=user.username,
                    notes=notes or f"Locked by {user.username}",
                )
                action = "locked"
                event_type = "ACCOUNT_LOCKED"
            else:
                # Unlock the account
                success = await self.auth_service.db_service.unlock_account(
                    lock_id=lock_id, unlocked_by=user.username, notes=notes
                )
                action = "unlocked"
                event_type = "ACCOUNT_UNLOCKED"

            if not success:
                return {
                    "success": False,
                    "message": f"Failed to {action[:-2]} account",
                    "error": f"{action.upper()}_FAILED",
                }

            # Log security event
            await self.auth_service._log_security_event(
                event_type=event_type,
                username=lock_info.get("identifier", "unknown"),
                success=True,
                client_ip=ctx.meta.get("clientIp", "unknown")
                if ctx and hasattr(ctx, "meta")
                else "unknown",
                user_agent=ctx.meta.get("userAgent", "unknown")
                if ctx and hasattr(ctx, "meta")
                else "unknown",
            )

            logger.info(
                f"Account {action}",
                lock_id=lock_id,
                identifier=lock_info.get("identifier"),
                identifier_type=lock_info.get("identifier_type"),
                by=user.username,
            )

            return {
                "success": True,
                "message": f"Account '{lock_info.get('identifier')}' {action} successfully",
                "data": {
                    "lock_id": lock_id,
                    "identifier": lock_info.get("identifier"),
                    "identifier_type": lock_info.get("identifier_type"),
                    "locked": locked,
                    "updated_by": user.username,
                },
            }

        except Exception as e:
            logger.error(
                "Update account lock error",
                error=str(e),
                error_type=type(e).__name__,
            )
            return {
                "success": False,
                "message": "An error occurred while updating account lock",
                "error": "UPDATE_ERROR",
            }
