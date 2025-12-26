"""
Authentication Service

Handles user authentication, JWT token management, and session control.
Provides secure authentication services for the homelab system.
"""

import os
from datetime import UTC, datetime
from typing import Dict, Any, Optional
import structlog
import uuid
from models.auth import User, UserRole, LoginCredentials, LoginResponse, TokenType
from models.log import LogEntry
from services.service_log import log_service
from services.database_service import DatabaseService
from lib.auth_helpers import (
    hash_password, verify_password, generate_jwt_token, validate_jwt_token,
    create_session_data, generate_session_id, create_default_admin
)


logger = structlog.get_logger("auth_service")


class AuthService:
    """Service for managing authentication and user sessions."""
    
    def __init__(
        self,
        jwt_secret: str = None,
        db_service: Optional[DatabaseService] = None,
    ):
        """Initialize authentication service with JWT configuration."""
        # Require JWT secret from environment in production
        if jwt_secret is None:
            jwt_secret = os.getenv("JWT_SECRET_KEY")
            if not jwt_secret:
                raise ValueError(
                    "JWT_SECRET_KEY environment variable must be set. "
                    "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
                )
        self.jwt_secret = jwt_secret
        self.jwt_algorithm = "HS256"
        self.token_expiry_hours = 24
        self.sessions: Dict[str, Dict[str, Any]] = {}

        # Initialize database service
        self.db_service = db_service or DatabaseService()

        logger.info("Authentication service initialized")
    
    async def _verify_database_connection(self) -> bool:
        """Verify database connection and setup."""
        return await self.db_service.verify_database_connection()

    async def _log_security_event(self, event_type: str, username: str, success: bool,
                                  client_ip: Optional[str] = None, user_agent: Optional[str] = None):
        """Log security events for authentication tracking."""
        try:
            log_entry = LogEntry(
                id=f"sec-{uuid.uuid4().hex[:8]}",
                timestamp=datetime.now(UTC),
                level="INFO" if success else "WARNING",
                source="auth_service",
                message=f"{event_type} {'successful' if success else 'failed'} for user: {username}",
                tags=["security", "authentication", event_type.lower(), "success" if success else "failure"],
                metadata={
                    "username": username,
                    "event_type": event_type,
                    "success": success,
                    "client_ip": client_ip or "unknown",
                    "user_agent": user_agent or "unknown",
                    "timestamp": datetime.now(UTC).isoformat()
                }
            )
            await log_service.create_log_entry(log_entry)
            logger.info("Security event logged", event_type=event_type, username=username, success=success)
        except Exception as e:
            logger.error("Failed to log security event", error=str(e), event_type=event_type, username=username)
    
    async def authenticate_user(self, credentials: LoginCredentials,
                                 client_ip: Optional[str] = None,
                                 user_agent: Optional[str] = None) -> Optional[LoginResponse]:
        """Authenticate user and generate session."""
        logger.info("AuthService.authenticate_user called", username=credentials.username, client_ip=client_ip)
        try:
            # Get user from database
            logger.debug("Fetching user from database", username=credentials.username)
            user = await self.db_service.get_user_by_username(credentials.username)
            logger.info("Database user lookup result", username=credentials.username, user_found=bool(user), user_active=user.is_active if user else None)
            if not user or not user.is_active:
                logger.warning("Authentication failed: user not found or inactive",
                             username=credentials.username, client_ip=client_ip)
                # Log failed login attempt
                await self._log_security_event("LOGIN", credentials.username, False,
                                               client_ip=client_ip, user_agent=user_agent)
                return None

            # Get and verify password hash from database
            logger.debug("Fetching password hash from database", username=credentials.username)
            stored_password_hash = await self.db_service.get_user_password_hash(credentials.username)
            logger.debug("Password hash retrieval result", username=credentials.username, has_hash=bool(stored_password_hash))

            password_valid = False
            if stored_password_hash:
                password_valid = verify_password(credentials.password, stored_password_hash)
                logger.debug("Password verification result", username=credentials.username, password_valid=password_valid)

            if not stored_password_hash or not password_valid:
                logger.warning("Authentication failed: invalid password",
                             username=credentials.username, client_ip=client_ip)
                # Log failed login attempt
                await self._log_security_event("LOGIN", credentials.username, False,
                                               client_ip=client_ip, user_agent=user_agent)
                return None

            # Update last login in database
            now = datetime.now(UTC).isoformat()
            logger.debug("Updating user last login", username=credentials.username)
            await self.db_service.update_user_last_login(credentials.username, now)
            user.last_login = now

            # Generate JWT token
            logger.debug("Generating JWT token", username=credentials.username, user_id=user.id)
            token = generate_jwt_token(user, self.jwt_secret, self.jwt_algorithm, self.token_expiry_hours)
            logger.debug("JWT token generated", username=credentials.username, token_length=len(token) if token else 0)

            # Create session
            session_id = generate_session_id()
            self.sessions[session_id] = create_session_data(user.id, self.token_expiry_hours)

            logger.info("User authenticated successfully", username=user.username, user_id=user.id, client_ip=client_ip)

            # Log successful login attempt
            await self._log_security_event("LOGIN", credentials.username, True,
                                           client_ip=client_ip, user_agent=user_agent)

            login_response = LoginResponse(
                user=user,
                token=token,
                expires_in=self.token_expiry_hours * 3600,
                session_id=session_id,
                token_type=TokenType.JWT
            )

            logger.info("LoginResponse created successfully", username=credentials.username, session_id=session_id, token_type=TokenType.JWT.value)
            return login_response
        except Exception as e:
            logger.error("Authentication error - exception in authenticate_user", username=credentials.username, error=str(e), error_type=type(e).__name__)
            import traceback
            logger.debug("Authentication error traceback", traceback=traceback.format_exc())
            # Log failed login attempt due to error
            await self._log_security_event("LOGIN", credentials.username, False,
                                           client_ip=client_ip, user_agent=user_agent)
            return None
    
    def _validate_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate JWT token using helper function."""
        return validate_jwt_token(token, self.jwt_secret, self.jwt_algorithm)

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username from database."""
        return await self.db_service.get_user_by_username(username)

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID from database."""
        return await self.db_service.get_user_by_id(user_id)

    async def get_all_users(self) -> list[User]:
        """Get all active users from database."""
        return await self.db_service.get_all_users()

    async def create_user(
        self,
        username: str,
        email: str,
        password: str,
        role: UserRole = UserRole.USER
    ) -> Optional[User]:
        """Create a new user in the database."""
        try:
            from lib.auth_helpers import hash_password
            password_hash = hash_password(password)

            user = await self.db_service.create_user(
                username=username,
                email=email,
                password_hash=password_hash,
                role=role
            )

            logger.info("User created", username=username, role=role.value)
            return user

        except Exception as e:
            logger.error("Failed to create user", username=username, error=str(e))
            return None
