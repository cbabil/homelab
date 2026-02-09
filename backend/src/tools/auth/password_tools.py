"""
Password Management Tools

Handles password reset and change operations.
Part of the authentication tools module.
"""

import contextlib
from typing import Any

import structlog
from fastmcp import Context

from services.auth_service import AuthService
from services.rate_limit_service import RateLimitService

logger = structlog.get_logger("password_tools")


class PasswordTools:
    """Password management tools for the MCP server."""

    _MAX_ATTEMPTS = 5
    _LOCKOUT_MINUTES = 15
    _LOCKOUT_SECONDS = _LOCKOUT_MINUTES * 60

    def __init__(
        self,
        auth_service: AuthService,
        rate_limit_service: RateLimitService | None = None,
    ):
        """Initialize password tools with auth service.

        Args:
            auth_service: Authentication service instance.
            rate_limit_service: Optional DB-backed rate limit service.
        """
        self.auth_service = auth_service
        self.rate_limit_service = rate_limit_service
        # In-memory fallback (used when rate_limit_service is None)
        self._password_change_attempts: dict[str, dict[str, Any]] = {}

    async def reset_user_password(
        self, params: dict[str, Any], ctx: Context = None
    ) -> dict[str, Any]:
        """Reset a user's password.

        SECURITY: Requires admin authentication.

        Args:
            params: Dictionary containing:
                - token: JWT token for authentication (must be admin)
                - username: The username to reset password for
                - password: The new password

        Returns:
            Dictionary with success status.
        """
        try:
            token = params.get("token")
            username = params.get("username")
            password = params.get("password")

            # Validate authentication token
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

            admin_user_id = payload.get("user_id")
            admin_user = (
                await self.auth_service.get_user_by_id(admin_user_id)
                if admin_user_id
                else None
            )

            if not admin_user or not admin_user.is_active:
                return {
                    "success": False,
                    "message": "User not found or inactive",
                    "error": "USER_INACTIVE",
                }

            if admin_user.role.value != "admin":
                logger.warning(
                    "Non-admin user attempted password reset",
                    username=admin_user.username,
                    role=admin_user.role.value,
                )
                return {
                    "success": False,
                    "message": "Admin privileges required",
                    "error": "ADMIN_REQUIRED",
                }

            if not username:
                return {
                    "success": False,
                    "message": "Username is required",
                    "error": "MISSING_USERNAME",
                }

            if not password:
                return {
                    "success": False,
                    "message": "Password is required",
                    "error": "MISSING_PASSWORD",
                }

            # Use NIST password validation
            from lib.security import validate_password_strength

            pwd_check = validate_password_strength(password)
            if not pwd_check["valid"]:
                return {
                    "success": False,
                    "message": "; ".join(pwd_check["errors"]),
                    "error": "WEAK_PASSWORD",
                }

            # Get user
            user = await self.auth_service.db_service.get_user_by_username(username)
            if not user:
                return {
                    "success": False,
                    "message": "User not found",
                    "error": "NOT_FOUND",
                }

            # Hash new password
            from lib.auth_helpers import hash_password

            password_hash = hash_password(password)

            # Update password
            success = await self.auth_service.db_service.update_user_password(
                username, password_hash
            )

            if not success:
                return {
                    "success": False,
                    "message": "Failed to update password",
                    "error": "UPDATE_FAILED",
                }

            logger.info(
                "Password reset successfully",
                username=username,
                admin=admin_user.username,
            )
            return {
                "success": True,
                "message": "Password reset successfully",
                "data": {"username": username},
            }

        except Exception as e:
            logger.error(
                "Failed to reset password",
                username=params.get("username"),
                error=str(e),
            )
            return {
                "success": False,
                "message": f"Failed to reset password: {str(e)}",
                "error": "RESET_ERROR",
            }

    async def change_password(
        self, params: dict[str, Any], ctx: Context = None
    ) -> dict[str, Any]:
        """Change password for the authenticated user.

        SECURITY FEATURES:
        - Requires valid JWT token for authentication
        - Verifies current password before allowing change
        - Rate limiting: 5 failed attempts triggers 15-minute lockout
        - Strong password requirements (min 12 chars, complexity)
        - All attempts logged as security events

        Args:
            params: Dictionary containing:
                - token: JWT token for authentication
                - current_password: User's current password
                - new_password: The new password (min 12 chars)

        Returns:
            Dictionary with success status.
        """
        from datetime import UTC, datetime, timedelta

        client_ip = "unknown"
        user_agent = "unknown"
        username = "unknown"

        try:
            # Extract client metadata from context
            if ctx and hasattr(ctx, "meta"):
                client_ip = ctx.meta.get("clientIp", "unknown")
                user_agent = ctx.meta.get("userAgent", "unknown")

            token = params.get("token")
            current_password = params.get("current_password")
            new_password = params.get("new_password")

            # Validate required fields
            if not token:
                return {
                    "success": False,
                    "message": "Authentication token is required",
                    "error": "MISSING_TOKEN",
                }

            if not current_password:
                return {
                    "success": False,
                    "message": "Current password is required",
                    "error": "MISSING_CURRENT_PASSWORD",
                }

            if not new_password:
                return {
                    "success": False,
                    "message": "New password is required",
                    "error": "MISSING_NEW_PASSWORD",
                }

            # Validate JWT token and get user
            payload = self.auth_service._validate_jwt_token(token)
            if not payload:
                logger.warning(
                    "Password change attempt with invalid token",
                    client_ip=client_ip,
                )
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
                logger.warning(
                    "Password change attempt for invalid/inactive user",
                    user_id=user_id,
                    client_ip=client_ip,
                )
                return {
                    "success": False,
                    "message": "User not found or inactive",
                    "error": "USER_INACTIVE",
                }

            username = user.username

            # Check rate limiting / lockout
            now = datetime.now(UTC)
            attempt_key = f"{username}:{client_ip}"

            if self.rate_limit_service:
                count = await self.rate_limit_service.get_count(
                    "password_change", attempt_key, self._LOCKOUT_SECONDS
                )
                if count >= self._MAX_ATTEMPTS:
                    logger.warning(
                        "Password change blocked - account locked",
                        username=username,
                        client_ip=client_ip,
                    )
                    await self.auth_service._log_security_event(
                        "PASSWORD_CHANGE_BLOCKED",
                        username,
                        False,
                        client_ip=client_ip,
                        user_agent=user_agent,
                    )
                    return {
                        "success": False,
                        "message": (
                            "Too many failed attempts. "
                            f"Try again in {self._LOCKOUT_MINUTES} minutes."
                        ),
                        "error": "RATE_LIMITED",
                    }
            elif attempt_key in self._password_change_attempts:
                attempt_data = self._password_change_attempts[attempt_key]
                lockout_until = attempt_data.get("lockout_until")

                if lockout_until and now < lockout_until:
                    remaining = int((lockout_until - now).total_seconds() / 60) + 1
                    logger.warning(
                        "Password change blocked - account locked",
                        username=username,
                        client_ip=client_ip,
                        remaining_minutes=remaining,
                    )
                    await self.auth_service._log_security_event(
                        "PASSWORD_CHANGE_BLOCKED",
                        username,
                        False,
                        client_ip=client_ip,
                        user_agent=user_agent,
                    )
                    return {
                        "success": False,
                        "message": (
                            "Too many failed attempts. "
                            f"Try again in {remaining} minutes."
                        ),
                        "error": "RATE_LIMITED",
                    }

            # Verify current password
            stored_hash = (
                await self.auth_service.db_service.get_user_password_hash(username)
            )
            if not stored_hash:
                logger.error("No password hash found for user", username=username)
                return {
                    "success": False,
                    "message": "Unable to verify current password",
                    "error": "VERIFICATION_ERROR",
                }

            from lib.auth_helpers import verify_password

            if not verify_password(current_password, stored_hash):
                # Track failed attempt
                if self.rate_limit_service:
                    await self.rate_limit_service.record(
                        "password_change", attempt_key
                    )
                    attempt_count = await self.rate_limit_service.get_count(
                        "password_change",
                        attempt_key,
                        self._LOCKOUT_SECONDS,
                    )
                else:
                    if attempt_key not in self._password_change_attempts:
                        self._password_change_attempts[attempt_key] = {
                            "count": 0,
                            "first_attempt": now,
                        }
                    self._password_change_attempts[attempt_key]["count"] += 1
                    attempt_count = self._password_change_attempts[attempt_key][
                        "count"
                    ]
                    if attempt_count >= self._MAX_ATTEMPTS:
                        self._password_change_attempts[attempt_key][
                            "lockout_until"
                        ] = now + timedelta(minutes=self._LOCKOUT_MINUTES)

                if attempt_count >= self._MAX_ATTEMPTS:
                    logger.warning(
                        "Password change lockout triggered",
                        username=username,
                        client_ip=client_ip,
                        attempts=attempt_count,
                    )

                await self.auth_service._log_security_event(
                    "PASSWORD_CHANGE_FAILED",
                    username,
                    False,
                    client_ip=client_ip,
                    user_agent=user_agent,
                )

                remaining_attempts = self._MAX_ATTEMPTS - attempt_count
                if remaining_attempts > 0:
                    return {
                        "success": False,
                        "message": (
                            "Current password is incorrect. "
                            f"{remaining_attempts} attempts remaining."
                        ),
                        "error": "INVALID_CURRENT_PASSWORD",
                    }
                else:
                    return {
                        "success": False,
                        "message": (
                            "Too many failed attempts. "
                            f"Account locked for {self._LOCKOUT_MINUTES} minutes."
                        ),
                        "error": "RATE_LIMITED",
                    }

            # Validate new password strength (same rules as setup/reset)
            from lib.security import validate_password_strength

            pwd_check = validate_password_strength(new_password)
            if not pwd_check["valid"]:
                return {
                    "success": False,
                    "message": "; ".join(pwd_check["errors"]),
                    "error": "WEAK_PASSWORD",
                }

            # Check new password is different from current
            if current_password == new_password:
                return {
                    "success": False,
                    "message": "New password must be different from current password",
                    "error": "SAME_PASSWORD",
                }

            # Hash and update password
            from lib.auth_helpers import hash_password

            new_hash = hash_password(new_password)

            success = await self.auth_service.db_service.update_user_password(
                username, new_hash
            )

            if not success:
                logger.error(
                    "Failed to update password in database", username=username
                )
                return {
                    "success": False,
                    "message": "Failed to update password",
                    "error": "UPDATE_FAILED",
                }

            # Clear rate limiting on success
            if self.rate_limit_service:
                await self.rate_limit_service.reset(
                    "password_change", attempt_key
                )
            elif attempt_key in self._password_change_attempts:
                del self._password_change_attempts[attempt_key]

            # Log successful password change
            await self.auth_service._log_security_event(
                "PASSWORD_CHANGED",
                username,
                True,
                client_ip=client_ip,
                user_agent=user_agent,
            )

            logger.info(
                "Password changed successfully",
                username=username,
                client_ip=client_ip,
            )

            return {"success": True, "message": "Password changed successfully"}

        except Exception as e:
            logger.error(
                "Password change error",
                username=username,
                error=str(e),
                error_type=type(e).__name__,
            )

            # Log failed attempt
            with contextlib.suppress(Exception):
                await self.auth_service._log_security_event(
                    "PASSWORD_CHANGE_ERROR",
                    username,
                    False,
                    client_ip=client_ip,
                    user_agent=user_agent,
                )

            return {
                "success": False,
                "message": "An error occurred while changing password",
                "error": "CHANGE_ERROR",
            }
