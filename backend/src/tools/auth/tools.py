"""
Authentication Tools

Provides authentication capabilities for the MCP server.
Implements login, logout, and session management functionality.

Delegates password operations to PasswordTools and account
management operations to AccountTools.
"""

from typing import Any

import structlog
from fastmcp import Context

from services.auth_service import AuthService
from services.rate_limit_service import RateLimitService
from tools.auth.account_tools import AccountTools
from tools.auth.login_tool import LoginTool
from tools.auth.password_tools import PasswordTools

logger = structlog.get_logger("auth_tools")


class AuthTools:
    """Authentication tools for the MCP server."""

    def __init__(
        self,
        auth_service: AuthService,
        rate_limit_service: RateLimitService = None,
    ):
        """Initialize authentication tools with auth service."""
        self.auth_service = auth_service
        self.login_tool = LoginTool(auth_service, rate_limit_service)
        self._password_tools = PasswordTools(auth_service, rate_limit_service)
        self._account_tools = AccountTools(auth_service)
        logger.info("Authentication tools initialized")

    # Class-level constants delegated from sub-tools
    _MAX_ATTEMPTS = PasswordTools._MAX_ATTEMPTS
    _LOCKOUT_MINUTES = PasswordTools._LOCKOUT_MINUTES
    _MAX_AVATAR_SIZE = AccountTools._MAX_AVATAR_SIZE

    async def login(
        self, credentials: dict[str, Any], ctx: Context
    ) -> dict[str, Any]:
        """Authenticate user with credentials."""
        logger.info(
            "AuthTools.login called",
            credentials_keys=list(credentials.keys()),
        )
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
                "AuthTools.login error",
                error=str(e),
                error_type=type(e).__name__,
            )
            raise

    async def logout(
        self,
        session_id: str = None,
        username: str = None,
        ctx: Context = None,
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
                    db_session = (
                        await self.auth_service.session_service.get_session(
                            session_id
                        )
                    )
                    if db_session:
                        user_id = db_session.user_id
                        if user_id:
                            user = (
                                await self.auth_service.db_service.get_user_by_id(
                                    user_id
                                )
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
                        user = (
                            await self.auth_service.db_service.get_user_by_id(
                                user_id
                            )
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
                logger.error(
                    "Failed to log logout error", error=str(log_error)
                )

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
                username=username,
                password=password,
                email=email,
                role=UserRole.ADMIN,
            )

            if not user:
                return {
                    "success": False,
                    "error": "CREATE_FAILED",
                    "message": "Failed to create admin user",
                }

            # Mark system as setup complete
            setup_marked = (
                await self.auth_service.db_service.mark_system_setup_complete(
                    user.id
                )
            )
            if not setup_marked:
                logger.warning(
                    "Failed to mark system as setup complete", user_id=user.id
                )
                # Don't fail the whole operation - admin was created

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

    # --- Delegated password operations ---

    async def reset_user_password(
        self, params: dict[str, Any], ctx: Context = None
    ) -> dict[str, Any]:
        """Reset a user's password. Delegates to PasswordTools."""
        return await self._password_tools.reset_user_password(params, ctx)

    async def change_password(
        self, params: dict[str, Any], ctx: Context = None
    ) -> dict[str, Any]:
        """Change password for the authenticated user. Delegates to PasswordTools."""
        return await self._password_tools.change_password(params, ctx)

    # --- Delegated account operations ---

    async def get_user_by_username(
        self, params: dict[str, Any], ctx: Context = None
    ) -> dict[str, Any]:
        """Get user information by username. Delegates to AccountTools."""
        return await self._account_tools.get_user_by_username(params, ctx)

    async def update_avatar(
        self, params: dict[str, Any], ctx: Context = None
    ) -> dict[str, Any]:
        """Update the authenticated user's avatar. Delegates to AccountTools."""
        return await self._account_tools.update_avatar(params, ctx)

    async def get_locked_accounts(
        self, params: dict[str, Any], ctx: Context = None
    ) -> dict[str, Any]:
        """Get locked accounts. Delegates to AccountTools."""
        return await self._account_tools.get_locked_accounts(params, ctx)

    async def update_account_lock(
        self, params: dict[str, Any], ctx: Context = None
    ) -> dict[str, Any]:
        """Update account lock status. Delegates to AccountTools."""
        return await self._account_tools.update_account_lock(params, ctx)
