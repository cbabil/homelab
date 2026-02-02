"""
Authentication Service

Handles user authentication, JWT token management, and session control.
Provides secure authentication services for the tomo system.
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
from services.session_service import SessionService
from lib.auth_helpers import (
    verify_password, generate_jwt_token, validate_jwt_token,
    create_session_data
)
from datetime import timedelta


logger = structlog.get_logger("auth_service")


class AuthService:
    """Service for managing authentication and user sessions."""
    
    def __init__(
        self,
        jwt_secret: str = None,
        db_service: Optional[DatabaseService] = None,
        session_service: Optional[SessionService] = None,
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
        self.sessions: Dict[str, Dict[str, Any]] = {}  # Legacy in-memory sessions

        # Initialize database service
        self.db_service = db_service or DatabaseService()

        # Initialize session service for persistent sessions
        self.session_service = session_service or SessionService(db_service=self.db_service)

        logger.info("Authentication service initialized")
    
    async def _verify_database_connection(self) -> bool:
        """Verify database connection and setup."""
        return await self.db_service.verify_database_connection()

    async def _log_security_event(self, event_type: str, username: str, success: bool,
                                  client_ip: Optional[str] = None, user_agent: Optional[str] = None):
        """Log security events for authentication tracking."""
        try:
            ip_info = f" from {client_ip}" if client_ip else ""
            log_entry = LogEntry(
                id=f"sec-{uuid.uuid4().hex[:8]}",
                timestamp=datetime.now(UTC),
                level="INFO" if success else "WARNING",
                source="auth",
                message=f"{event_type} {'successful' if success else 'failed'} for user: {username}{ip_info}",
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
    
    # Default account locking configuration (overridden by settings)
    DEFAULT_MAX_LOGIN_ATTEMPTS = 5
    DEFAULT_LOCK_DURATION_SECONDS = 900  # 15 minutes

    async def _get_security_settings(self) -> tuple[int, int]:
        """Get security settings from database, with fallbacks to defaults."""
        max_attempts = self.DEFAULT_MAX_LOGIN_ATTEMPTS
        lock_duration_seconds = self.DEFAULT_LOCK_DURATION_SECONDS

        try:
            # Try to get from system_settings table
            async with self.db_service.get_connection() as conn:
                # Get max login attempts
                cursor = await conn.execute(
                    "SELECT setting_value FROM system_settings WHERE setting_key = ?",
                    ("security.max_login_attempts",)
                )
                row = await cursor.fetchone()
                if row:
                    import json
                    max_attempts = json.loads(row[0])

                # Get lockout duration
                cursor = await conn.execute(
                    "SELECT setting_value FROM system_settings WHERE setting_key = ?",
                    ("security.account_lockout_duration",)
                )
                row = await cursor.fetchone()
                if row:
                    import json
                    lock_duration_seconds = json.loads(row[0])

        except Exception as e:
            logger.warning("Could not load security settings, using defaults", error=str(e))

        return max_attempts, lock_duration_seconds

    async def authenticate_user(self, credentials: LoginCredentials,
                                 client_ip: Optional[str] = None,
                                 user_agent: Optional[str] = None) -> Optional[LoginResponse]:
        """Authenticate user and generate session.

        SECURITY: Implements account locking to prevent brute force attacks.
        - Locks username after max_login_attempts failed attempts (from settings)
        - Locks IP address after max_login_attempts failed attempts
        - Tracks attempts for non-existent usernames too (prevents enumeration)
        """
        logger.info("AuthService.authenticate_user called", username=credentials.username, client_ip=client_ip)
        try:
            # Get security settings from database
            max_attempts, lock_duration_seconds = await self._get_security_settings()
            lock_duration_minutes = lock_duration_seconds // 60
            # Check if username is locked
            username_locked, username_lock_info = await self.db_service.is_account_locked(
                credentials.username, "username"
            )
            if username_locked:
                lock_expires = username_lock_info.get("lock_expires_at")
                logger.warning("Login blocked: username is locked",
                             username=credentials.username, client_ip=client_ip,
                             lock_expires=lock_expires)
                await self._log_security_event("LOGIN_BLOCKED", credentials.username, False,
                                               client_ip=client_ip, user_agent=user_agent)
                return None

            # Check if IP is locked
            if client_ip and client_ip != "unknown":
                ip_locked, ip_lock_info = await self.db_service.is_account_locked(
                    client_ip, "ip"
                )
                if ip_locked:
                    lock_expires = ip_lock_info.get("lock_expires_at")
                    logger.warning("Login blocked: IP is locked",
                                 username=credentials.username, client_ip=client_ip,
                                 lock_expires=lock_expires)
                    await self._log_security_event("LOGIN_BLOCKED_IP", credentials.username, False,
                                                   client_ip=client_ip, user_agent=user_agent)
                    return None

            # Get user from database
            logger.debug("Fetching user from database", username=credentials.username)
            user = await self.db_service.get_user_by_username(credentials.username)
            logger.info("Database user lookup result", username=credentials.username, user_found=bool(user), user_active=user.is_active if user else None)
            if not user or not user.is_active:
                logger.warning("Authentication failed: user not found or inactive",
                             username=credentials.username, client_ip=client_ip)

                # Record failed attempt for username (even non-existent ones)
                is_locked, attempt_count, lock_expires = await self.db_service.record_failed_login_attempt(
                    credentials.username, "username",
                    ip_address=client_ip, user_agent=user_agent,
                    max_attempts=max_attempts,
                    lock_duration_minutes=lock_duration_minutes
                )

                # Also record for IP
                if client_ip and client_ip != "unknown":
                    await self.db_service.record_failed_login_attempt(
                        client_ip, "ip",
                        ip_address=client_ip, user_agent=user_agent,
                        max_attempts=max_attempts,
                        lock_duration_minutes=lock_duration_minutes
                    )

                if is_locked:
                    logger.warning("Account locked after failed attempts",
                                 username=credentials.username, attempts=attempt_count)
                    await self._log_security_event("ACCOUNT_LOCKED", credentials.username, False,
                                                   client_ip=client_ip, user_agent=user_agent)

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

                # Record failed attempt for username
                is_locked, attempt_count, lock_expires = await self.db_service.record_failed_login_attempt(
                    credentials.username, "username",
                    ip_address=client_ip, user_agent=user_agent,
                    max_attempts=max_attempts,
                    lock_duration_minutes=lock_duration_minutes
                )

                # Also record for IP
                if client_ip and client_ip != "unknown":
                    await self.db_service.record_failed_login_attempt(
                        client_ip, "ip",
                        ip_address=client_ip, user_agent=user_agent,
                        max_attempts=max_attempts,
                        lock_duration_minutes=lock_duration_minutes
                    )

                if is_locked:
                    logger.warning("Account locked after failed attempts",
                                 username=credentials.username, attempts=attempt_count)
                    await self._log_security_event("ACCOUNT_LOCKED", credentials.username, False,
                                                   client_ip=client_ip, user_agent=user_agent)

                # Log failed login attempt
                await self._log_security_event("LOGIN", credentials.username, False,
                                               client_ip=client_ip, user_agent=user_agent)
                return None

            # Clear failed login attempts on successful authentication
            await self.db_service.clear_failed_attempts(credentials.username, "username")
            if client_ip and client_ip != "unknown":
                await self.db_service.clear_failed_attempts(client_ip, "ip")

            # Update last login in database
            now = datetime.now(UTC).isoformat()
            logger.debug("Updating user last login", username=credentials.username)
            await self.db_service.update_user_last_login(credentials.username, now)
            user.last_login = now

            # Generate JWT token
            logger.debug("Generating JWT token", username=credentials.username, user_id=user.id)
            token = generate_jwt_token(user, self.jwt_secret, self.jwt_algorithm, self.token_expiry_hours)
            logger.debug("JWT token generated", username=credentials.username, token_length=len(token) if token else 0)

            # Create persistent database session
            expires_at = datetime.now(UTC) + timedelta(hours=self.token_expiry_hours)
            db_session = await self.session_service.create_session(
                user_id=user.id,
                expires_at=expires_at,
                ip_address=client_ip,
                user_agent=user_agent
            )
            session_id = db_session.id

            # Also store in legacy in-memory sessions for backward compatibility
            self.sessions[session_id] = create_session_data(user.id, self.token_expiry_hours)

            logger.info("User authenticated successfully", username=user.username, user_id=user.id, client_ip=client_ip, session_id=session_id)

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

    async def get_user(
        self,
        token: Optional[str] = None,
        user_id: Optional[str] = None,
        username: Optional[str] = None
    ) -> Optional[User]:
        """Get user by token, ID, or username.

        Args:
            token: JWT token (validates and extracts user_id)
            user_id: User's unique ID
            username: User's username

        Returns:
            User object if found, None otherwise.
        """
        # If token provided, validate and extract user_id
        if token:
            payload = self._validate_jwt_token(token)
            if not payload:
                return None
            user_id = payload.get("user_id")

        # Fetch from database
        return await self.db_service.get_user(user_id=user_id, username=username)

    # Backward compatibility wrappers
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username. Wrapper for get_user()."""
        return await self.get_user(username=username)

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID. Wrapper for get_user()."""
        return await self.get_user(user_id=user_id)

    async def get_all_users(self) -> list[User]:
        """Get all active users from database."""
        return await self.db_service.get_all_users()

    async def has_admin_user(self) -> bool:
        """Check if system has an active admin user."""
        return await self.db_service.has_admin_user()

    async def create_user(
        self,
        username: str,
        password: str,
        email: str = "",
        role: UserRole = UserRole.USER
    ) -> Optional[User]:
        """Create a new user in the database. Email is optional."""
        try:
            from lib.auth_helpers import hash_password
            password_hash = hash_password(password)

            user = await self.db_service.create_user(
                username=username,
                password_hash=password_hash,
                email=email,
                role=role
            )

            logger.info("User created", username=username, role=role.value)
            return user

        except Exception as e:
            logger.error("Failed to create user", username=username, error=str(e))
            return None
