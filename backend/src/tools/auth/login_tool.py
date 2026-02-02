"""
Login Authentication Tool

Handles user login authentication functionality.
Part of the authentication tools module.
"""

from datetime import datetime, UTC
from typing import Dict, Any, Optional
import structlog
from fastmcp import Context
from models.auth import LoginCredentials
from services.auth_service import AuthService
from lib.rate_limiter import RateLimiter


logger = structlog.get_logger("login_tool")

# Rate limiter for login attempts: 5 attempts per 5 minutes per IP
login_rate_limiter = RateLimiter(max_requests=5, window_seconds=300)


class LoginTool:
    """Login authentication tool."""

    def __init__(self, auth_service: AuthService):
        """Initialize login tool with auth service."""
        self.auth_service = auth_service

    def _format_lock_time_remaining(self, lock_expires_at: Optional[str]) -> str:
        """Calculate and format the remaining lock time."""
        if not lock_expires_at:
            return "permanently"

        try:
            expires = datetime.fromisoformat(lock_expires_at.replace('Z', '+00:00'))
            now = datetime.now(UTC)
            remaining = expires - now

            if remaining.total_seconds() <= 0:
                return "shortly"

            minutes = int(remaining.total_seconds() / 60)
            if minutes < 1:
                return "less than a minute"
            elif minutes == 1:
                return "1 minute"
            else:
                return f"{minutes} minutes"
        except Exception:
            return "some time"

    async def login(self, credentials: Dict[str, Any], ctx: Optional[Context] = None) -> Dict[str, Any]:
        """
        Authenticate user with credentials.

        Args:
            credentials: Login credentials (username, password, remember_me)
            ctx: Optional FastMCP context for accessing request information

        Returns:
            dict: Authentication result with token and user data
        """
        logger.info("Login attempt started", credentials_received=list(credentials.keys()))

        # Extract client IP early for rate limiting
        client_ip = "unknown"
        user_agent = None

        if ctx:
            try:
                request = ctx.get_http_request()
                client_ip = request.client.host if request.client else "unknown"
                user_agent = request.headers.get("user-agent")
            except Exception as e:
                logger.debug("Could not extract request context", error=str(e))

        # Check rate limit before processing
        if not login_rate_limiter.is_allowed(client_ip):
            remaining_seconds = 300  # Window is 5 minutes
            logger.warning("Rate limit exceeded for login", client_ip=client_ip)
            return {
                "success": False,
                "message": "Too many login attempts. Please try again in a few minutes.",
                "error": "RATE_LIMIT_EXCEEDED",
                "retry_after": remaining_seconds
            }

        try:
            # Handle nested credentials structure from frontend
            if "credentials" in credentials:
                cred_data = credentials["credentials"]
            else:
                cred_data = credentials

            username = cred_data.get("username", "")

            # Check if username is locked (before full authentication)
            username_locked, username_lock_info = await self.auth_service.db_service.is_account_locked(
                username, "username"
            )
            if username_locked:
                lock_expires = username_lock_info.get("lock_expires_at")
                logger.warning("Login blocked: username is locked",
                             username=username, client_ip=client_ip)
                return {
                    "success": False,
                    "message": "Account is disabled. Contact your administrator.",
                    "error": "ACCOUNT_LOCKED",
                    "lock_expires_at": lock_expires
                }

            # Check if IP is locked
            if client_ip and client_ip != "unknown":
                ip_locked, ip_lock_info = await self.auth_service.db_service.is_account_locked(
                    client_ip, "ip"
                )
                if ip_locked:
                    lock_expires = ip_lock_info.get("lock_expires_at")
                    logger.warning("Login blocked: IP is locked",
                                 username=username, client_ip=client_ip)
                    return {
                        "success": False,
                        "message": "Account is disabled. Contact your administrator.",
                        "error": "IP_LOCKED",
                        "lock_expires_at": lock_expires
                    }

            login_creds = LoginCredentials(**cred_data)
            logger.debug("LoginCredentials created", username=login_creds.username)

            logger.info("Calling auth_service.authenticate_user", username=login_creds.username, client_ip=client_ip)
            response = await self.auth_service.authenticate_user(
                login_creds,
                client_ip=client_ip,
                user_agent=user_agent
            )
            logger.info("Auth service response received", response_type=type(response).__name__, has_response=bool(response))

            if not response:
                logger.warning("Login failed - no response from auth service", username=login_creds.username, client_ip=client_ip)
                return {
                    "success": False,
                    "message": "Invalid username or password",
                    "error": "INVALID_CREDENTIALS"
                }

            logger.info("Login successful - preparing response", username=login_creds.username, client_ip=client_ip)

            user_data = response.user.model_dump()
            # Ensure role is serialized as string value, not enum
            if 'role' in user_data and hasattr(user_data['role'], 'value'):
                user_data['role'] = user_data['role'].value
            logger.debug("User data prepared", user_id=user_data.get('id'), user_username=user_data.get('username'), user_role=user_data.get('role'))

            final_response = {
                "success": True,
                "data": {
                    "user": user_data,
                    "token": response.token,
                    "expires_in": response.expires_in,
                    "session_id": response.session_id,
                    "token_type": response.token_type.value
                },
                "message": "Login successful"
            }

            logger.info("Final response prepared", success=final_response["success"], has_user_data=bool(final_response["data"]["user"]), message=final_response["message"])
            return final_response

        except Exception as e:
            logger.error("Login error - exception caught", error=str(e), error_type=type(e).__name__, username=credentials.get('username', 'unknown'))
            import traceback
            logger.debug("Login error traceback", traceback=traceback.format_exc())
            return {
                "success": False,
                "message": f"Login failed: {str(e)}",
                "error": "LOGIN_ERROR"
            }