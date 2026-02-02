"""
Unit tests for models/auth.py

Tests authentication models including users, credentials, sessions, and tokens.
"""

import pytest
from pydantic import ValidationError

from models.auth import (
    UserRole,
    TokenType,
    User,
    LoginCredentials,
    RegistrationCredentials,
    SessionActivity,
    SessionWarning,
    AuthState,
    LoginResponse,
)


class TestUserRole:
    """Tests for UserRole enum."""

    def test_role_values(self):
        """Test all role enum values exist."""
        assert UserRole.ADMIN == "admin"
        assert UserRole.USER == "user"

    def test_role_is_string_enum(self):
        """Test that role values are strings."""
        assert isinstance(UserRole.ADMIN.value, str)


class TestTokenType:
    """Tests for TokenType enum."""

    def test_token_type_values(self):
        """Test all token type enum values exist."""
        assert TokenType.JWT == "JWT"
        assert TokenType.BEARER == "Bearer"

    def test_token_type_is_string_enum(self):
        """Test that token type values are strings."""
        assert isinstance(TokenType.JWT.value, str)


class TestUser:
    """Tests for User model."""

    def test_required_fields(self):
        """Test required fields."""
        user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            last_login="2024-01-15T10:00:00",
        )
        assert user.id == "user-123"
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.last_login == "2024-01-15T10:00:00"

    def test_default_values(self):
        """Test default values."""
        user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            last_login="2024-01-15T10:00:00",
        )
        assert user.role == UserRole.USER
        assert user.is_active is True
        assert user.password_changed_at is None
        assert user.preferences is None
        assert user.avatar is None
        assert user.created_at is None
        assert user.updated_at is None

    def test_all_fields(self):
        """Test all fields populated."""
        user = User(
            id="user-123",
            username="admin",
            email="admin@tomo.local",
            role=UserRole.ADMIN,
            last_login="2024-01-15T10:00:00",
            password_changed_at="2024-01-01T00:00:00",
            is_active=True,
            preferences={"theme": "dark"},
            avatar="data:image/png;base64,xyz",
            created_at="2023-01-01T00:00:00",
            updated_at="2024-01-15T10:00:00",
        )
        assert user.role == UserRole.ADMIN
        assert user.preferences == {"theme": "dark"}
        assert user.avatar == "data:image/png;base64,xyz"

    def test_username_min_length(self):
        """Test username minimum length validation."""
        with pytest.raises(ValidationError) as exc_info:
            User(
                id="user-123",
                username="ab",  # Too short
                email="test@example.com",
                last_login="2024-01-15T10:00:00",
            )
        assert "username" in str(exc_info.value)

    def test_username_max_length(self):
        """Test username maximum length validation."""
        with pytest.raises(ValidationError) as exc_info:
            User(
                id="user-123",
                username="a" * 51,  # Too long
                email="test@example.com",
                last_login="2024-01-15T10:00:00",
            )
        assert "username" in str(exc_info.value)

    def test_missing_required_fields(self):
        """Test validation error when required fields are missing."""
        with pytest.raises(ValidationError):
            User(id="user-123")


class TestLoginCredentials:
    """Tests for LoginCredentials model."""

    def test_required_fields(self):
        """Test required fields."""
        creds = LoginCredentials(
            username="testuser",
            password="password123",
        )
        assert creds.username == "testuser"
        assert creds.password == "password123"

    def test_default_remember_me(self):
        """Test default remember_me is False."""
        creds = LoginCredentials(
            username="testuser",
            password="password123",
        )
        assert creds.remember_me is False

    def test_remember_me_true(self):
        """Test remember_me can be set to True."""
        creds = LoginCredentials(
            username="testuser",
            password="password123",
            remember_me=True,
        )
        assert creds.remember_me is True

    def test_username_min_length(self):
        """Test username minimum length validation."""
        with pytest.raises(ValidationError) as exc_info:
            LoginCredentials(
                username="ab",  # Too short
                password="password123",
            )
        assert "username" in str(exc_info.value)

    def test_password_min_length(self):
        """Test password minimum length validation."""
        with pytest.raises(ValidationError) as exc_info:
            LoginCredentials(
                username="testuser",
                password="",  # Too short
            )
        assert "password" in str(exc_info.value)


class TestRegistrationCredentials:
    """Tests for RegistrationCredentials model."""

    def test_valid_registration(self):
        """Test valid registration credentials."""
        creds = RegistrationCredentials(
            username="newuser",
            email="newuser@example.com",
            password="SecurePass123",
            confirm_password="SecurePass123",
            accept_terms=True,
        )
        assert creds.username == "newuser"
        assert creds.email == "newuser@example.com"
        assert creds.password == "SecurePass123"

    def test_default_role(self):
        """Test default role is USER."""
        creds = RegistrationCredentials(
            username="newuser",
            email="newuser@example.com",
            password="SecurePass123",
            confirm_password="SecurePass123",
            accept_terms=True,
        )
        assert creds.role == UserRole.USER

    def test_admin_role(self):
        """Test admin role can be specified."""
        creds = RegistrationCredentials(
            username="newadmin",
            email="admin@example.com",
            password="SecurePass123",
            confirm_password="SecurePass123",
            accept_terms=True,
            role=UserRole.ADMIN,
        )
        assert creds.role == UserRole.ADMIN

    def test_password_too_short(self):
        """Test password minimum length validation via Field constraint."""
        with pytest.raises(ValidationError) as exc_info:
            RegistrationCredentials(
                username="newuser",
                email="newuser@example.com",
                password="short",  # Less than 8 chars
                confirm_password="short",
                accept_terms=True,
            )
        assert "password" in str(exc_info.value).lower()

    def test_password_too_long(self):
        """Test password maximum length validation via Field constraint."""
        long_password = "a" * 129  # More than 128 chars
        with pytest.raises(ValidationError) as exc_info:
            RegistrationCredentials(
                username="newuser",
                email="newuser@example.com",
                password=long_password,
                confirm_password=long_password,
                accept_terms=True,
            )
        assert "password" in str(exc_info.value).lower()

    def test_passwords_do_not_match(self):
        """Test password confirmation validation."""
        with pytest.raises(ValidationError) as exc_info:
            RegistrationCredentials(
                username="newuser",
                email="newuser@example.com",
                password="SecurePass123",
                confirm_password="DifferentPass456",
                accept_terms=True,
            )
        assert "do not match" in str(exc_info.value)

    def test_invalid_email(self):
        """Test email validation."""
        with pytest.raises(ValidationError) as exc_info:
            RegistrationCredentials(
                username="newuser",
                email="not-an-email",
                password="SecurePass123",
                confirm_password="SecurePass123",
                accept_terms=True,
            )
        assert "email" in str(exc_info.value).lower()

    def test_username_constraints(self):
        """Test username length constraints."""
        with pytest.raises(ValidationError):
            RegistrationCredentials(
                username="ab",  # Too short
                email="test@example.com",
                password="SecurePass123",
                confirm_password="SecurePass123",
                accept_terms=True,
            )

    def test_password_boundary_min(self):
        """Test password at exactly minimum length (8 chars)."""
        creds = RegistrationCredentials(
            username="newuser",
            email="test@example.com",
            password="12345678",  # Exactly 8 chars
            confirm_password="12345678",
            accept_terms=True,
        )
        assert len(creds.password) == 8

    def test_password_boundary_max(self):
        """Test password at exactly maximum length (128 chars)."""
        max_password = "a" * 128
        creds = RegistrationCredentials(
            username="newuser",
            email="test@example.com",
            password=max_password,
            confirm_password=max_password,
            accept_terms=True,
        )
        assert len(creds.password) == 128


class TestSessionActivity:
    """Tests for SessionActivity model."""

    def test_required_fields(self):
        """Test all required fields."""
        activity = SessionActivity(
            last_activity="2024-01-15T10:00:00",
            is_idle=False,
            idle_duration=0,
            activity_count=5,
        )
        assert activity.last_activity == "2024-01-15T10:00:00"
        assert activity.is_idle is False
        assert activity.idle_duration == 0
        assert activity.activity_count == 5

    def test_idle_session(self):
        """Test idle session state."""
        activity = SessionActivity(
            last_activity="2024-01-15T09:00:00",
            is_idle=True,
            idle_duration=3600000,  # 1 hour in ms
            activity_count=10,
        )
        assert activity.is_idle is True
        assert activity.idle_duration == 3600000

    def test_missing_required_fields(self):
        """Test validation error when required fields are missing."""
        with pytest.raises(ValidationError):
            SessionActivity(last_activity="2024-01-15T10:00:00")


class TestSessionWarning:
    """Tests for SessionWarning model."""

    def test_required_fields(self):
        """Test all required fields."""
        warning = SessionWarning(
            is_showing=True,
            minutes_remaining=5,
            warning_level="warning",
        )
        assert warning.is_showing is True
        assert warning.minutes_remaining == 5
        assert warning.warning_level == "warning"

    def test_not_showing(self):
        """Test warning not showing state."""
        warning = SessionWarning(
            is_showing=False,
            minutes_remaining=30,
            warning_level="info",
        )
        assert warning.is_showing is False

    def test_missing_required_fields(self):
        """Test validation error when required fields are missing."""
        with pytest.raises(ValidationError):
            SessionWarning(is_showing=True)


class TestAuthState:
    """Tests for AuthState model."""

    def test_required_fields(self):
        """Test required fields."""
        state = AuthState(
            is_authenticated=False,
            is_loading=False,
        )
        assert state.is_authenticated is False
        assert state.is_loading is False

    def test_default_values(self):
        """Test default values."""
        state = AuthState(
            is_authenticated=False,
            is_loading=False,
        )
        assert state.user is None
        assert state.error is None
        assert state.session_expiry is None
        assert state.activity is None
        assert state.warning is None
        assert state.token_type is None
        assert state.token_expiry is None

    def test_authenticated_state(self):
        """Test authenticated state with user."""
        user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            last_login="2024-01-15T10:00:00",
        )
        state = AuthState(
            user=user,
            is_authenticated=True,
            is_loading=False,
            session_expiry="2024-01-15T12:00:00",
            token_type=TokenType.JWT,
            token_expiry="2024-01-15T11:00:00",
        )
        assert state.user == user
        assert state.is_authenticated is True
        assert state.token_type == TokenType.JWT

    def test_error_state(self):
        """Test error state."""
        state = AuthState(
            is_authenticated=False,
            is_loading=False,
            error="Invalid credentials",
        )
        assert state.error == "Invalid credentials"


class TestLoginResponse:
    """Tests for LoginResponse model."""

    def test_required_fields(self):
        """Test required fields."""
        user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            last_login="2024-01-15T10:00:00",
        )
        response = LoginResponse(
            user=user,
            token="jwt-token-xyz",
            expires_in=3600,
        )
        assert response.user == user
        assert response.token == "jwt-token-xyz"
        assert response.expires_in == 3600

    def test_default_values(self):
        """Test default values."""
        user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            last_login="2024-01-15T10:00:00",
        )
        response = LoginResponse(
            user=user,
            token="jwt-token-xyz",
            expires_in=3600,
        )
        assert response.refresh_token is None
        assert response.session_id is None
        assert response.token_type == TokenType.JWT

    def test_all_fields(self):
        """Test all fields populated."""
        user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            last_login="2024-01-15T10:00:00",
        )
        response = LoginResponse(
            user=user,
            token="jwt-token-xyz",
            refresh_token="refresh-token-abc",
            expires_in=3600,
            session_id="session-123",
            token_type=TokenType.BEARER,
        )
        assert response.refresh_token == "refresh-token-abc"
        assert response.session_id == "session-123"
        assert response.token_type == TokenType.BEARER

    def test_missing_required_fields(self):
        """Test validation error when required fields are missing."""
        with pytest.raises(ValidationError):
            LoginResponse(token="jwt-token-xyz", expires_in=3600)
