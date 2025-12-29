"""
Authentication Tools

Provides authentication and user management capabilities for the MCP server.
Implements login, logout, and session management functionality.
"""

from datetime import datetime, UTC
from typing import Dict, Any
import uuid
import structlog
from fastmcp import FastMCP, Context
from services.auth_service import AuthService
from services.service_log import log_service
from tools.auth.login_tool import LoginTool
from models.auth import UserRole
from models.log import LogEntry


logger = structlog.get_logger("auth_tools")


async def _log_user_event(level: str, message: str, metadata: Dict[str, Any] = None):
    """Helper to log user management events to the database."""
    try:
        entry = LogEntry(
            id=f"usr-{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now(UTC),
            level=level,
            source="usr",
            message=message,
            tags=["user", "management"],
            metadata=metadata or {}
        )
        await log_service.create_log_entry(entry)
    except Exception as e:
        logger.error("Failed to create log entry", error=str(e))


class AuthTools:
    """Authentication tools for the MCP server."""
    
    def __init__(self, auth_service: AuthService):
        """Initialize authentication tools with auth service."""
        self.auth_service = auth_service
        self.login_tool = LoginTool(auth_service)
        logger.info("Authentication tools initialized")
    
    async def login(self, credentials: Dict[str, Any], ctx: Context) -> Dict[str, Any]:
        """Authenticate user with credentials."""
        logger.info("AuthTools.login called", credentials_keys=list(credentials.keys()))
        try:
            result = await self.login_tool.login(credentials, ctx)
            logger.info("LoginTool response", success=result.get('success'), has_data=bool(result.get('data')), message=result.get('message'))
            return result
        except Exception as e:
            logger.error("AuthTools.login error", error=str(e), error_type=type(e).__name__)
            raise

    async def logout(self, session_id: str = None, username: str = None, ctx: Context = None) -> Dict[str, Any]:
        """Logout user and invalidate session."""
        actual_username = "unknown"
        client_ip = "unknown"
        user_agent = "unknown"

        try:
            # Try to get username from multiple sources
            # 1. From direct parameter (preferred)
            if username:
                actual_username = username
            # 2. From session data
            elif session_id and session_id in self.auth_service.sessions:
                session_data = self.auth_service.sessions[session_id]
                user_id = session_data.get("user_id")
                if user_id:
                    try:
                        user = await self.auth_service.db_service.get_user_by_id(user_id)
                        if user:
                            actual_username = user.username
                    except Exception as e:
                        logger.warning("Could not retrieve username for logout logging",
                                     user_id=user_id, error=str(e))

            # Invalidate session if it exists
            if session_id and session_id in self.auth_service.sessions:
                del self.auth_service.sessions[session_id]
                logger.info("Session invalidated", session_id=session_id, username=actual_username)
            elif session_id:
                logger.info("Session not found for logout", session_id=session_id, username=actual_username)

            # Extract client metadata from context if available
            if ctx and hasattr(ctx, 'meta'):
                client_ip = ctx.meta.get('clientIp', 'unknown')
                user_agent = ctx.meta.get('userAgent', 'unknown')

            # Only log logout if we have a real username (not "unknown")
            if actual_username != "unknown":
                await self.auth_service._log_security_event(
                    event_type="LOGOUT",
                    username=actual_username,
                    success=True,
                    client_ip=client_ip,
                    user_agent=user_agent
                )
            else:
                logger.warning("Logout called without identifiable user",
                             session_id=session_id, client_ip=client_ip)

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
                    user_agent=user_agent
                )
            except Exception as log_error:
                logger.error("Failed to log logout error", error=str(log_error))

            return {
                "success": False,
                "message": f"Logout failed: {str(e)}",
                "error": "LOGOUT_ERROR"
            }
    
    async def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate JWT token and return user information."""
        try:
            payload = self.auth_service._validate_jwt_token(token)
            
            if not payload:
                return {
                    "success": False,
                    "message": "Invalid or expired token",
                    "error": "INVALID_TOKEN"
                }
            
            # Get user from database for token validation
            username = payload.get("username")
            user = await self.auth_service.get_user_by_username(username) if username else None

            if not user or not user.is_active:
                return {
                    "success": False,
                    "message": "User not found or inactive",
                    "error": "USER_INACTIVE"
                }
            
            return {
                "success": True,
                "data": {
                    "user": user.model_dump(),
                    "token_valid": True,
                    "expires_at": payload.get("exp")
                },
                "message": "Token is valid"
            }
            
        except Exception as e:
            logger.error("Token validation error", error=str(e))
            return {
                "success": False,
                "message": f"Token validation failed: {str(e)}",
                "error": "TOKEN_VALIDATION_ERROR"
            }

    async def get_current_user(self, token: str) -> Dict[str, Any]:
        """Get current user from JWT token."""
        try:
            payload = self.auth_service._validate_jwt_token(token)

            if not payload:
                return {
                    "success": False,
                    "message": "Invalid or expired token",
                    "error": "INVALID_TOKEN"
                }

            user_id = payload.get("user_id")
            user = await self.auth_service.get_user_by_id(user_id) if user_id else None

            if not user or not user.is_active:
                return {
                    "success": False,
                    "message": "User not found or inactive",
                    "error": "USER_INACTIVE"
                }

            return {
                "success": True,
                "data": {"user": user.model_dump()},
                "message": "User retrieved successfully"
            }

        except Exception as e:
            logger.error("Get current user error", error=str(e))
            return {
                "success": False,
                "message": f"Failed to get user: {str(e)}",
                "error": "GET_USER_ERROR"
            }

    async def create_user(
        self,
        token: str,
        username: str,
        email: str,
        password: str,
        role: str = "user"
    ) -> Dict[str, Any]:
        """Create a new user (admin only)."""
        try:
            # Validate admin token
            payload = self.auth_service._validate_jwt_token(token)
            if not payload:
                return {"success": False, "message": "Invalid token", "error": "INVALID_TOKEN"}

            # Check if requesting user is admin
            admin_user = await self.auth_service.get_user_by_id(payload.get("user_id"))
            if not admin_user or admin_user.role != UserRole.ADMIN:
                return {
                    "success": False,
                    "message": "Admin privileges required",
                    "error": "PERMISSION_DENIED"
                }

            # Create the new user
            user_role = UserRole.ADMIN if role == "admin" else UserRole.USER

            new_user = await self.auth_service.create_user(
                username=username,
                email=email,
                password=password,
                role=user_role
            )

            if not new_user:
                await _log_user_event("ERROR", f"Failed to create user: {username}", {
                    "username": username,
                    "created_by": admin_user.username
                })
                return {
                    "success": False,
                    "message": "Failed to create user",
                    "error": "CREATE_USER_ERROR"
                }

            await _log_user_event("INFO", f"User created: {username}", {
                "username": username,
                "email": email,
                "role": role,
                "created_by": admin_user.username
            })
            return {
                "success": True,
                "data": {"user": new_user.model_dump()},
                "message": "User created successfully"
            }

        except Exception as e:
            logger.error("Create user error", error=str(e))
            await _log_user_event("ERROR", f"User creation failed: {username}", {"error": str(e)})
            return {
                "success": False,
                "message": f"Failed to create user: {str(e)}",
                "error": "CREATE_USER_ERROR"
            }

    async def list_users(self, token: str) -> Dict[str, Any]:
        """List all users (admin only)."""
        try:
            # Validate admin token
            payload = self.auth_service._validate_jwt_token(token)
            if not payload:
                return {"success": False, "message": "Invalid token", "error": "INVALID_TOKEN"}

            # Check if requesting user is admin
            admin_user = await self.auth_service.get_user_by_id(payload.get("user_id"))
            if not admin_user or admin_user.role != UserRole.ADMIN:
                return {
                    "success": False,
                    "message": "Admin privileges required",
                    "error": "PERMISSION_DENIED"
                }

            # Get all users
            users = await self.auth_service.get_all_users()

            await _log_user_event("INFO", f"User list accessed by: {admin_user.username}", {
                "accessed_by": admin_user.username,
                "user_count": len(users)
            })
            return {
                "success": True,
                "data": {"users": [u.model_dump() for u in users]},
                "message": f"Retrieved {len(users)} users"
            }

        except Exception as e:
            logger.error("List users error", error=str(e))
            await _log_user_event("ERROR", "User list access failed", {"error": str(e)})
            return {
                "success": False,
                "message": f"Failed to list users: {str(e)}",
                "error": "LIST_USERS_ERROR"
            }


def register_auth_tools(app: FastMCP, auth_service: AuthService):
    """Register authentication tools with FastMCP app."""
    auth_tools = AuthTools(auth_service)

    # Register each tool method using the @app.tool decorator pattern
    app.tool(auth_tools.login)
    app.tool(auth_tools.logout)
    app.tool(auth_tools.validate_token)
    app.tool(auth_tools.get_current_user)
    app.tool(auth_tools.create_user)
    app.tool(auth_tools.list_users)

    logger.info("Authentication tools registered")