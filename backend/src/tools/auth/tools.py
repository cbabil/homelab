"""
Authentication Tools

Provides authentication capabilities for the MCP server.
Implements login, logout, and session management functionality.
"""

from typing import Any

import structlog
from fastmcp import Context

from services.auth_service import AuthService
from tools.auth.login_tool import LoginTool

logger = structlog.get_logger("auth_tools")


class AuthTools:
    """Authentication tools for the MCP server."""

    def __init__(self, auth_service: AuthService):
        """Initialize authentication tools with auth service."""
        self.auth_service = auth_service
        self.login_tool = LoginTool(auth_service)
        self._password_change_attempts: dict[str, dict[str, Any]] = {}
        logger.info("Authentication tools initialized")

    async def login(self, credentials: dict[str, Any], ctx: Context) -> dict[str, Any]:
        """Authenticate user with credentials."""
        logger.info("AuthTools.login called", credentials_keys=list(credentials.keys()))
        try:
            result = await self.login_tool.login(credentials, ctx)
            logger.info(
                "LoginTool response",
                success=result.get("success"),
                has_data=bool(result.get("data")),
                message=result.get("message"),
            )
            return result
        except Exception as e:
            logger.error(
                "AuthTools.login error", error=str(e), error_type=type(e).__name__
            )
            raise

    async def logout(
        self, session_id: str = None, username: str = None, ctx: Context = None
    ) -> dict[str, Any]:
        """Logout user and invalidate session."""
        actual_username = "unknown"
        client_ip = "unknown"
        user_agent = "unknown"

        try:
            # Try to get username from multiple sources
            # 1. From direct parameter (preferred)
            if username:
                actual_username = username

            # 2. From database session (persistent sessions)
            if actual_username == "unknown" and session_id:
                try:
                    db_session = await self.auth_service.session_service.get_session(
                        session_id
                    )
                    if db_session:
                        user_id = db_session.user_id
                        if user_id:
                            user = await self.auth_service.db_service.get_user_by_id(
                                user_id
                            )
                            if user:
                                actual_username = user.username
                                logger.info(
                                    "Username retrieved from database session",
                                    session_id=session_id,
                                    username=actual_username,
                                )
                except Exception as e:
                    logger.warning(
                        "Could not retrieve username from database session",
                        session_id=session_id,
                        error=str(e),
                    )

            # 3. From legacy in-memory session (fallback)
            if (
                actual_username == "unknown"
                and session_id
                and session_id in self.auth_service.sessions
            ):
                session_data = self.auth_service.sessions[session_id]
                user_id = session_data.get("user_id")
                if user_id:
                    try:
                        user = await self.auth_service.db_service.get_user_by_id(
                            user_id
                        )
                        if user:
                            actual_username = user.username
                    except Exception as e:
                        logger.warning(
                            "Could not retrieve username for logout logging",
                            user_id=user_id,
                            error=str(e),
                        )

            # Terminate database session (persistent sessions)
            if session_id:
                try:
                    terminated_count = (
                        await self.auth_service.session_service.delete_session(
                            session_id=session_id,
                            terminated_by=actual_username
                            if actual_username != "unknown"
                            else "system",
                        )
                    )
                    if terminated_count > 0:
                        logger.info(
                            "Database session terminated",
                            session_id=session_id,
                            username=actual_username,
                        )
                except Exception as e:
                    logger.warning(
                        "Failed to terminate database session",
                        session_id=session_id,
                        error=str(e),
                    )

            # Invalidate legacy in-memory session if it exists
            if session_id and session_id in self.auth_service.sessions:
                del self.auth_service.sessions[session_id]
                logger.info(
                    "In-memory session invalidated",
                    session_id=session_id,
                    username=actual_username,
                )
            elif session_id:
                logger.debug(
                    "Session not found in memory for logout",
                    session_id=session_id,
                    username=actual_username,
                )

            # Extract client metadata from context if available
            if ctx and hasattr(ctx, "meta"):
                client_ip = ctx.meta.get("clientIp", "unknown")
                user_agent = ctx.meta.get("userAgent", "unknown")

            # Only log logout if we have a real username (not "unknown")
            if actual_username != "unknown":
                await self.auth_service._log_security_event(
                    event_type="LOGOUT",
                    username=actual_username,
                    success=True,
                    client_ip=client_ip,
                    user_agent=user_agent,
                )
            else:
                logger.warning(
                    "Logout called without identifiable user",
                    session_id=session_id,
                    client_ip=client_ip,
                )

            return {"success": True, "message": "Logout successful"}

        except Exception as e:
            logger.error("Logout error", error=str(e), username=username)

            # Log failed logout event
            try:
                await self.auth_service._log_security_event(
                    event_type="LOGOUT",
                    username=username,
                    success=False,
                    client_ip=client_ip,
                    user_agent=user_agent,
                )
            except Exception as log_error:
                logger.error("Failed to log logout error", error=str(log_error))

            return {
                "success": False,
                "message": f"Logout failed: {str(e)}",
                "error": "LOGOUT_ERROR",
            }

    async def get_current_user(self, token: str) -> dict[str, Any]:
        """Get current user from JWT token."""
        try:
            user = await self.auth_service.get_user(token=token)

            if not user or not user.is_active:
                return {
                    "success": False,
                    "message": "Invalid token or user not found",
                    "error": "INVALID_TOKEN",
                }

            return {
                "success": True,
                "data": {"user": user.model_dump()},
                "message": "User retrieved successfully",
            }

        except Exception as e:
            logger.error("Get current user error", error=str(e))
            return {
                "success": False,
                "message": f"Failed to get user: {str(e)}",
                "error": "GET_USER_ERROR",
            }

    async def create_initial_admin(
        self, params: dict[str, Any], ctx: Context = None
    ) -> dict[str, Any]:
        """Create the first admin user during initial setup.

        This tool requires NO authentication but only works if system
        is not yet set up (is_setup = false). After setup is complete,
        this tool will always fail to prevent unauthorized admin creation.

        Also marks the system as setup complete in system_info table.
        """
        try:
            # Check if system is already set up
            is_setup = await self.auth_service.db_service.is_system_setup()
            if is_setup:
                logger.warning(
                    "Attempted to create initial admin when system is already set up"
                )
                return {
                    "success": False,
                    "error": "ALREADY_SETUP",
                    "message": "System is already set up. Use login instead.",
                }

            # Also check if admin already exists (belt and suspenders)
            if await self.auth_service.has_admin_user():
                logger.warning(
                    "Attempted to create initial admin when one already exists"
                )
                return {
                    "success": False,
                    "error": "ADMIN_EXISTS",
                    "message": "An admin user already exists. Use login instead.",
                }

            username = params.get("username")
            email = params.get("email", "")  # Email is optional
            password = params.get("password")

            # Validate required fields
            if not username or not password:
                return {
                    "success": False,
                    "error": "MISSING_FIELDS",
                    "message": "Username and password are required",
                }

            # Validate password strength
            from lib.security import validate_password_strength

            pwd_check = validate_password_strength(password)
            if not pwd_check["valid"]:
                return {
                    "success": False,
                    "error": "WEAK_PASSWORD",
                    "message": "; ".join(pwd_check["errors"]),
                }

            # Create admin user
            from models.auth import UserRole

            user = await self.auth_service.create_user(
                username=username, password=password, email=email, role=UserRole.ADMIN
            )

            if not user:
                return {
                    "success": False,
                    "error": "CREATE_FAILED",
                    "message": "Failed to create admin user",
                }

            # Mark system as setup complete
            setup_marked = (
                await self.auth_service.db_service.mark_system_setup_complete(user.id)
            )
            if not setup_marked:
                logger.warning(
                    "Failed to mark system as setup complete", user_id=user.id
                )
                # Don't fail the whole operation - admin was created successfully

            logger.info(
                "Initial admin user created and system marked as setup",
                username=username,
                user_id=user.id,
            )
            data = {"username": username}
            if email:
                data["email"] = email
            return {
                "success": True,
                "message": "Admin user created successfully",
                "data": data,
            }

        except Exception as e:
            logger.error("Failed to create initial admin", error=str(e))
            return {
                "success": False,
                "message": f"Failed to create admin: {str(e)}",
                "error": "CREATE_ERROR",
            }

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

    _MAX_ATTEMPTS = 5
    _LOCKOUT_MINUTES = 15

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
        import re
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
                    "Password change attempt with invalid token", client_ip=client_ip
                )
                return {
                    "success": False,
                    "message": "Invalid or expired authentication token",
                    "error": "INVALID_TOKEN",
                }

            user_id = payload.get("user_id")
            user = await self.auth_service.get_user_by_id(user_id) if user_id else None

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

            if attempt_key in self._password_change_attempts:
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
                        "message": f"Too many failed attempts. Try again in {remaining} minutes.",
                        "error": "RATE_LIMITED",
                    }

            # Verify current password
            stored_hash = await self.auth_service.db_service.get_user_password_hash(
                username
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
                if attempt_key not in self._password_change_attempts:
                    self._password_change_attempts[attempt_key] = {
                        "count": 0,
                        "first_attempt": now,
                    }

                self._password_change_attempts[attempt_key]["count"] += 1
                attempt_count = self._password_change_attempts[attempt_key]["count"]

                if attempt_count >= self._MAX_ATTEMPTS:
                    self._password_change_attempts[attempt_key]["lockout_until"] = (
                        now + timedelta(minutes=self._LOCKOUT_MINUTES)
                    )
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
                        "message": f"Current password is incorrect. {remaining_attempts} attempts remaining.",
                        "error": "INVALID_CURRENT_PASSWORD",
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Too many failed attempts. Account locked for {self._LOCKOUT_MINUTES} minutes.",
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
                logger.error("Failed to update password in database", username=username)
                return {
                    "success": False,
                    "message": "Failed to update password",
                    "error": "UPDATE_FAILED",
                }

            # Clear rate limiting on success
            if attempt_key in self._password_change_attempts:
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
                "Password changed successfully", username=username, client_ip=client_ip
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
            try:
                await self.auth_service._log_security_event(
                    "PASSWORD_CHANGE_ERROR",
                    username,
                    False,
                    client_ip=client_ip,
                    user_agent=user_agent,
                )
            except Exception:
                pass

            return {
                "success": False,
                "message": "An error occurred while changing password",
                "error": "CHANGE_ERROR",
            }

    # Maximum avatar size: 500KB base64 (roughly 375KB image)
    _MAX_AVATAR_SIZE = 500 * 1024

    async def update_avatar(
        self, params: dict[str, Any], ctx: Context = None
    ) -> dict[str, Any]:
        """Update the authenticated user's avatar.

        Args:
            params: Dictionary containing:
                - token: JWT token for authentication
                - avatar: Base64 data URL of the image (e.g., "data:image/png;base64,...")
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
            user = await self.auth_service.get_user_by_id(user_id) if user_id else None

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
                logger.error("Failed to update avatar in database", user_id=user_id)
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
                "Avatar update error", error=str(e), error_type=type(e).__name__
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
                - identifier: Optional - filter by username or IP (returns single match)
                - identifier_type: Optional - 'username' or 'ip' (required if identifier provided)
                - lock_id: Optional - get specific lock by ID
                - include_expired: Whether to include expired locks (default: False)
                - include_unlocked: Whether to include manually unlocked accounts (default: False)

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
            user = await self.auth_service.get_user_by_id(user_id) if user_id else None

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
                lock_info = await self.auth_service.db_service.get_lock_by_id(lock_id)
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
            locked_accounts = await self.auth_service.db_service.get_locked_accounts(
                include_expired=include_expired, include_unlocked=include_unlocked
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
                "Get locked accounts error", error=str(e), error_type=type(e).__name__
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
            user = await self.auth_service.get_user_by_id(user_id) if user_id else None

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
                    "message": f"Failed to {action[:-2]}  account",
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
                "Update account lock error", error=str(e), error_type=type(e).__name__
            )
            return {
                "success": False,
                "message": "An error occurred while updating account lock",
                "error": "UPDATE_ERROR",
            }
