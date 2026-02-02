"""
Unit tests for models/session.py

Tests session models including status, session data, and responses.
"""

from datetime import datetime, UTC, timedelta
import pytest
from pydantic import ValidationError

from models.session import (
    SessionStatus,
    Session,
    SessionCreate,
    SessionUpdate,
    SessionListResponse,
)


class TestSessionStatus:
    """Tests for SessionStatus enum."""

    def test_session_status_values(self):
        """Test all session status enum values."""
        assert SessionStatus.ACTIVE == "active"
        assert SessionStatus.IDLE == "idle"
        assert SessionStatus.EXPIRED == "expired"
        assert SessionStatus.TERMINATED == "terminated"

    def test_session_status_is_string_enum(self):
        """Test that session status values are strings."""
        for status in SessionStatus:
            assert isinstance(status.value, str)

    def test_session_status_from_value(self):
        """Test creating enum from string value."""
        assert SessionStatus("active") == SessionStatus.ACTIVE
        assert SessionStatus("idle") == SessionStatus.IDLE
        assert SessionStatus("expired") == SessionStatus.EXPIRED
        assert SessionStatus("terminated") == SessionStatus.TERMINATED


class TestSession:
    """Tests for Session model."""

    def test_required_fields(self):
        """Test required fields."""
        now = datetime.now(UTC)
        expires = now + timedelta(hours=1)
        session = Session(
            id="session-123",
            user_id="user-456",
            created_at=now,
            expires_at=expires,
            last_activity=now,
        )
        assert session.id == "session-123"
        assert session.user_id == "user-456"
        assert session.created_at == now
        assert session.expires_at == expires
        assert session.last_activity == now

    def test_default_values(self):
        """Test default values for optional fields."""
        now = datetime.now(UTC)
        expires = now + timedelta(hours=1)
        session = Session(
            id="session-123",
            user_id="user-456",
            created_at=now,
            expires_at=expires,
            last_activity=now,
        )
        assert session.ip_address is None
        assert session.user_agent is None
        assert session.status == SessionStatus.ACTIVE
        assert session.terminated_at is None
        assert session.terminated_by is None

    def test_all_fields(self):
        """Test all fields populated."""
        now = datetime.now(UTC)
        expires = now + timedelta(hours=1)
        terminated = now + timedelta(minutes=30)
        session = Session(
            id="session-789",
            user_id="user-123",
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            created_at=now,
            expires_at=expires,
            last_activity=now,
            status=SessionStatus.TERMINATED,
            terminated_at=terminated,
            terminated_by="admin-001",
        )
        assert session.ip_address == "192.168.1.100"
        assert session.user_agent == "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        assert session.status == SessionStatus.TERMINATED
        assert session.terminated_at == terminated
        assert session.terminated_by == "admin-001"

    def test_all_status_values(self):
        """Test session with each status value."""
        now = datetime.now(UTC)
        expires = now + timedelta(hours=1)
        for status in SessionStatus:
            session = Session(
                id=f"session-{status.value}",
                user_id="user-123",
                created_at=now,
                expires_at=expires,
                last_activity=now,
                status=status,
            )
            assert session.status == status

    def test_missing_required_fields(self):
        """Test validation error when required fields are missing."""
        with pytest.raises(ValidationError):
            Session(id="session-123")

    def test_missing_user_id(self):
        """Test validation error when user_id is missing."""
        now = datetime.now(UTC)
        with pytest.raises(ValidationError):
            Session(
                id="session-123",
                created_at=now,
                expires_at=now,
                last_activity=now,
            )

    def test_missing_timestamps(self):
        """Test validation error when timestamps are missing."""
        with pytest.raises(ValidationError):
            Session(
                id="session-123",
                user_id="user-456",
            )


class TestSessionCreate:
    """Tests for SessionCreate model."""

    def test_required_fields(self):
        """Test required fields."""
        expires = datetime.now(UTC) + timedelta(hours=1)
        create = SessionCreate(
            user_id="user-123",
            expires_at=expires,
        )
        assert create.user_id == "user-123"
        assert create.expires_at == expires

    def test_default_values(self):
        """Test default values for optional fields."""
        expires = datetime.now(UTC) + timedelta(hours=1)
        create = SessionCreate(
            user_id="user-123",
            expires_at=expires,
        )
        assert create.ip_address is None
        assert create.user_agent is None

    def test_all_fields(self):
        """Test all fields populated."""
        expires = datetime.now(UTC) + timedelta(hours=2)
        create = SessionCreate(
            user_id="user-456",
            ip_address="10.0.0.50",
            user_agent="Chrome/120.0",
            expires_at=expires,
        )
        assert create.ip_address == "10.0.0.50"
        assert create.user_agent == "Chrome/120.0"

    def test_missing_required_fields(self):
        """Test validation error when required fields are missing."""
        with pytest.raises(ValidationError):
            SessionCreate(user_id="user-123")

    def test_missing_user_id(self):
        """Test validation error when user_id is missing."""
        expires = datetime.now(UTC) + timedelta(hours=1)
        with pytest.raises(ValidationError):
            SessionCreate(expires_at=expires)


class TestSessionUpdate:
    """Tests for SessionUpdate model."""

    def test_empty_update(self):
        """Test update with no fields."""
        update = SessionUpdate()
        assert update.last_activity is None
        assert update.status is None

    def test_update_last_activity(self):
        """Test updating last activity."""
        now = datetime.now(UTC)
        update = SessionUpdate(last_activity=now)
        assert update.last_activity == now
        assert update.status is None

    def test_update_status(self):
        """Test updating status."""
        update = SessionUpdate(status=SessionStatus.IDLE)
        assert update.status == SessionStatus.IDLE
        assert update.last_activity is None

    def test_update_both_fields(self):
        """Test updating both fields."""
        now = datetime.now(UTC)
        update = SessionUpdate(
            last_activity=now,
            status=SessionStatus.EXPIRED,
        )
        assert update.last_activity == now
        assert update.status == SessionStatus.EXPIRED

    def test_all_status_values_in_update(self):
        """Test update with each status value."""
        for status in SessionStatus:
            update = SessionUpdate(status=status)
            assert update.status == status


class TestSessionListResponse:
    """Tests for SessionListResponse model."""

    def test_required_fields(self):
        """Test required fields."""
        response = SessionListResponse(
            id="session-123",
            user_id="user-456",
            created_at="2024-01-15T10:00:00Z",
            expires_at="2024-01-15T11:00:00Z",
            last_activity="2024-01-15T10:30:00Z",
            status="active",
        )
        assert response.id == "session-123"
        assert response.user_id == "user-456"
        assert response.created_at == "2024-01-15T10:00:00Z"
        assert response.expires_at == "2024-01-15T11:00:00Z"
        assert response.last_activity == "2024-01-15T10:30:00Z"
        assert response.status == "active"

    def test_default_values(self):
        """Test default values for optional fields."""
        response = SessionListResponse(
            id="session-123",
            user_id="user-456",
            created_at="2024-01-15T10:00:00Z",
            expires_at="2024-01-15T11:00:00Z",
            last_activity="2024-01-15T10:30:00Z",
            status="active",
        )
        assert response.username is None
        assert response.ip_address is None
        assert response.user_agent is None
        assert response.is_current is False

    def test_all_fields(self):
        """Test all fields populated."""
        response = SessionListResponse(
            id="session-789",
            user_id="user-123",
            username="admin",
            ip_address="192.168.1.50",
            user_agent="Firefox/115.0",
            created_at="2024-01-15T09:00:00Z",
            expires_at="2024-01-15T12:00:00Z",
            last_activity="2024-01-15T11:00:00Z",
            status="idle",
            is_current=True,
        )
        assert response.username == "admin"
        assert response.ip_address == "192.168.1.50"
        assert response.user_agent == "Firefox/115.0"
        assert response.is_current is True

    def test_various_status_strings(self):
        """Test with various status strings."""
        statuses = ["active", "idle", "expired", "terminated"]
        for status in statuses:
            response = SessionListResponse(
                id="session-123",
                user_id="user-456",
                created_at="2024-01-15T10:00:00Z",
                expires_at="2024-01-15T11:00:00Z",
                last_activity="2024-01-15T10:30:00Z",
                status=status,
            )
            assert response.status == status

    def test_missing_required_fields(self):
        """Test validation error when required fields are missing."""
        with pytest.raises(ValidationError):
            SessionListResponse(id="session-123")

    def test_current_session_flag(self):
        """Test is_current flag variations."""
        # Default is False
        response1 = SessionListResponse(
            id="session-1",
            user_id="user-1",
            created_at="2024-01-15T10:00:00Z",
            expires_at="2024-01-15T11:00:00Z",
            last_activity="2024-01-15T10:00:00Z",
            status="active",
        )
        assert response1.is_current is False

        # Explicitly True
        response2 = SessionListResponse(
            id="session-2",
            user_id="user-1",
            created_at="2024-01-15T10:00:00Z",
            expires_at="2024-01-15T11:00:00Z",
            last_activity="2024-01-15T10:00:00Z",
            status="active",
            is_current=True,
        )
        assert response2.is_current is True

        # Explicitly False
        response3 = SessionListResponse(
            id="session-3",
            user_id="user-1",
            created_at="2024-01-15T10:00:00Z",
            expires_at="2024-01-15T11:00:00Z",
            last_activity="2024-01-15T10:00:00Z",
            status="active",
            is_current=False,
        )
        assert response3.is_current is False
