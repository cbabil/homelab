"""
Unit tests for services/session_service.py - Operations.

Tests list_sessions, update_session, delete_session, cleanup_expired_sessions,
and validate_session methods.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.session import Session, SessionListResponse, SessionStatus
from services.session_service import SessionService


@pytest.fixture
def mock_db_service():
    """Create mock database service."""
    return MagicMock()


@pytest.fixture
def mock_connection():
    """Create mock database connection."""
    conn = AsyncMock()
    conn.row_factory = None
    conn.execute = AsyncMock()
    conn.commit = AsyncMock()
    return conn


@pytest.fixture
def session_service(mock_db_service, mock_connection):
    """Create SessionService with mocked dependencies."""
    mock_db_service.get_connection = MagicMock()
    mock_db_service.get_connection.return_value.__aenter__ = AsyncMock(
        return_value=mock_connection
    )
    mock_db_service.get_connection.return_value.__aexit__ = AsyncMock()

    with patch("services.session_service.logger"):
        return SessionService(mock_db_service)


@pytest.fixture
def base_session_list_row():
    """Base row for session list tests."""
    return {
        "id": "sess_abc123def456",
        "user_id": "user-123",
        "username": "testuser",
        "ip_address": "192.168.1.100",
        "user_agent": "Mozilla/5.0",
        "created_at": "2024-01-15T10:00:00+00:00",
        "expires_at": "2024-01-15T22:00:00+00:00",
        "last_activity": "2024-01-15T11:00:00+00:00",
        "status": "active",
    }


class TestListSessions:
    """Tests for list_sessions method."""

    @pytest.mark.asyncio
    async def test_list_sessions_success(
        self, session_service, mock_connection, base_session_list_row
    ):
        """list_sessions should return list of sessions."""
        with (
            patch.object(
                session_service,
                "mark_idle_sessions",
                new_callable=AsyncMock,
                return_value=0,
            ),
            patch.object(
                session_service,
                "cleanup_expired_sessions",
                new_callable=AsyncMock,
                return_value=0,
            ),
        ):
            mock_cursor = AsyncMock()
            mock_cursor.fetchall = AsyncMock(return_value=[base_session_list_row])
            mock_connection.execute = AsyncMock(return_value=mock_cursor)

            with patch("services.session_service.logger"):
                result = await session_service.list_sessions()

        assert len(result) == 1
        assert isinstance(result[0], SessionListResponse)
        assert result[0].id == "sess_abc123def456"
        assert result[0].username == "testuser"

    @pytest.mark.asyncio
    async def test_list_sessions_with_user_filter(
        self, session_service, mock_connection, base_session_list_row
    ):
        """list_sessions should filter by user_id."""
        with (
            patch.object(
                session_service,
                "mark_idle_sessions",
                new_callable=AsyncMock,
                return_value=0,
            ),
            patch.object(
                session_service,
                "cleanup_expired_sessions",
                new_callable=AsyncMock,
                return_value=0,
            ),
        ):
            mock_cursor = AsyncMock()
            mock_cursor.fetchall = AsyncMock(return_value=[base_session_list_row])
            mock_connection.execute = AsyncMock(return_value=mock_cursor)

            with patch("services.session_service.logger"):
                await session_service.list_sessions(user_id="user-123")

        call_args = mock_connection.execute.call_args[0]
        assert "AND s.user_id = ?" in call_args[0]
        assert "user-123" in call_args[1]

    @pytest.mark.asyncio
    async def test_list_sessions_with_status_filter(
        self, session_service, mock_connection, base_session_list_row
    ):
        """list_sessions should filter by status."""
        with (
            patch.object(
                session_service,
                "mark_idle_sessions",
                new_callable=AsyncMock,
                return_value=0,
            ),
            patch.object(
                session_service,
                "cleanup_expired_sessions",
                new_callable=AsyncMock,
                return_value=0,
            ),
        ):
            mock_cursor = AsyncMock()
            mock_cursor.fetchall = AsyncMock(return_value=[])
            mock_connection.execute = AsyncMock(return_value=mock_cursor)

            with patch("services.session_service.logger"):
                await session_service.list_sessions(status=SessionStatus.ACTIVE)

        call_args = mock_connection.execute.call_args[0]
        assert "AND s.status = ?" in call_args[0]

    @pytest.mark.asyncio
    async def test_list_sessions_calls_cleanup(self, session_service, mock_connection):
        """list_sessions should call mark_idle and cleanup first."""
        mock_mark_idle = AsyncMock(return_value=2)
        mock_cleanup = AsyncMock(return_value=1)

        with (
            patch.object(session_service, "mark_idle_sessions", mock_mark_idle),
            patch.object(session_service, "cleanup_expired_sessions", mock_cleanup),
        ):
            mock_cursor = AsyncMock()
            mock_cursor.fetchall = AsyncMock(return_value=[])
            mock_connection.execute = AsyncMock(return_value=mock_cursor)

            with patch("services.session_service.logger"):
                await session_service.list_sessions()

        mock_mark_idle.assert_called_once()
        mock_cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_sessions_no_username(self, session_service, mock_connection):
        """list_sessions should handle missing username."""
        row = {
            "id": "sess_123",
            "user_id": "user-123",
            "username": None,
            "ip_address": None,
            "user_agent": None,
            "created_at": "2024-01-15T10:00:00+00:00",
            "expires_at": "2024-01-15T22:00:00+00:00",
            "last_activity": "2024-01-15T11:00:00+00:00",
            "status": "active",
        }

        with (
            patch.object(
                session_service,
                "mark_idle_sessions",
                new_callable=AsyncMock,
                return_value=0,
            ),
            patch.object(
                session_service,
                "cleanup_expired_sessions",
                new_callable=AsyncMock,
                return_value=0,
            ),
        ):
            mock_cursor = AsyncMock()
            mock_cursor.fetchall = AsyncMock(return_value=[row])
            mock_connection.execute = AsyncMock(return_value=mock_cursor)

            with patch("services.session_service.logger"):
                result = await session_service.list_sessions()

        assert result[0].username is None


class TestUpdateSession:
    """Tests for update_session method."""

    @pytest.mark.asyncio
    async def test_update_session_success(self, session_service, mock_connection):
        """update_session should update last_activity."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 1
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        with patch("services.session_service.logger"):
            result = await session_service.update_session("sess_123")

        assert result is True
        mock_connection.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_session_not_found(self, session_service, mock_connection):
        """update_session should return False when not found."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 0
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        with patch("services.session_service.logger"):
            result = await session_service.update_session("nonexistent")

        assert result is False

    @pytest.mark.asyncio
    async def test_update_session_logs_on_success(
        self, session_service, mock_connection
    ):
        """update_session should log when updated."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 1
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        with patch("services.session_service.logger") as mock_logger:
            await session_service.update_session("sess_123")

        mock_logger.debug.assert_called()
        assert "sess_123" in str(mock_logger.debug.call_args)


class TestDeleteSession:
    """Tests for delete_session method."""

    @pytest.mark.asyncio
    async def test_delete_session_by_session_id(self, session_service, mock_connection):
        """delete_session should terminate specific session."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 1
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        with patch("services.session_service.logger"):
            result = await session_service.delete_session(
                session_id="sess_123", terminated_by="admin"
            )

        assert result == 1
        mock_connection.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_session_by_user_id(self, session_service, mock_connection):
        """delete_session should terminate all sessions for user."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 3
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        with patch("services.session_service.logger"):
            result = await session_service.delete_session(
                user_id="user-123", terminated_by="system"
            )

        assert result == 3

    @pytest.mark.asyncio
    async def test_delete_session_by_user_id_with_exclude(
        self, session_service, mock_connection
    ):
        """delete_session should exclude current session."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 2
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        with patch("services.session_service.logger"):
            result = await session_service.delete_session(
                user_id="user-123",
                terminated_by="user-123",
                exclude_session_id="sess_current",
            )

        assert result == 2
        call_args = mock_connection.execute.call_args[0]
        assert "id != ?" in call_args[0]
        assert "sess_current" in call_args[1]

    @pytest.mark.asyncio
    async def test_delete_session_no_params(self, session_service, mock_connection):
        """delete_session should return 0 without session_id or user_id."""
        with patch("services.session_service.logger") as mock_logger:
            result = await session_service.delete_session()

        assert result == 0
        mock_logger.warning.assert_called()
        mock_connection.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_session_logs_termination(
        self, session_service, mock_connection
    ):
        """delete_session should log termination."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 1
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        with patch("services.session_service.logger") as mock_logger:
            await session_service.delete_session(
                session_id="sess_123", terminated_by="admin"
            )

        mock_logger.info.assert_called()
        kwargs = mock_logger.info.call_args[1]
        assert kwargs["count"] == 1
        assert kwargs["terminated_by"] == "admin"


class TestCleanupExpiredSessions:
    """Tests for cleanup_expired_sessions method."""

    @pytest.mark.asyncio
    async def test_cleanup_expired_success(self, session_service, mock_connection):
        """cleanup_expired_sessions should mark expired sessions."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 5
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        with patch("services.session_service.logger"):
            result = await session_service.cleanup_expired_sessions()

        assert result == 5
        mock_connection.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_expired_none(self, session_service, mock_connection):
        """cleanup_expired_sessions should return 0 when no expired."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 0
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        with patch("services.session_service.logger"):
            result = await session_service.cleanup_expired_sessions()

        assert result == 0

    @pytest.mark.asyncio
    async def test_cleanup_expired_logs(self, session_service, mock_connection):
        """cleanup_expired_sessions should log result."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 3
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        with patch("services.session_service.logger") as mock_logger:
            await session_service.cleanup_expired_sessions()

        mock_logger.info.assert_called()
        kwargs = mock_logger.info.call_args[1]
        assert kwargs["count"] == 3


def _make_session(status: SessionStatus, expired: bool = False) -> Session:
    """Helper to create mock sessions."""
    now = datetime.now(UTC)
    if expired:
        expires_at = now - timedelta(hours=1)
        created_at = now - timedelta(hours=2)
    else:
        expires_at = now + timedelta(hours=1)
        created_at = now
    return Session(
        id="sess_123",
        user_id="user-123",
        ip_address=None,
        user_agent=None,
        created_at=created_at,
        expires_at=expires_at,
        last_activity=now,
        status=status,
    )


class TestValidateSession:
    """Tests for validate_session method."""

    @pytest.mark.asyncio
    async def test_validate_session_success(self, session_service):
        """validate_session should return valid session."""
        mock_session = _make_session(SessionStatus.ACTIVE)
        with patch.object(
            session_service, "get_session", AsyncMock(return_value=mock_session)
        ):
            with patch("services.session_service.logger"):
                result = await session_service.validate_session("sess_123")
        assert result is not None and result.id == "sess_123"

    @pytest.mark.asyncio
    async def test_validate_session_not_found(self, session_service):
        """validate_session should return None when session not found."""
        with patch.object(session_service, "get_session", AsyncMock(return_value=None)):
            with patch("services.session_service.logger"):
                result = await session_service.validate_session("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_validate_session_expired(self, session_service):
        """validate_session should return None and delete expired session."""
        mock_session = _make_session(SessionStatus.ACTIVE, expired=True)
        mock_delete = AsyncMock(return_value=1)
        with (
            patch.object(
                session_service, "get_session", AsyncMock(return_value=mock_session)
            ),
            patch.object(session_service, "delete_session", mock_delete),
        ):
            with patch("services.session_service.logger"):
                result = await session_service.validate_session("sess_123")
        assert result is None
        mock_delete.assert_called_once_with(
            session_id="sess_123", terminated_by="system"
        )

    @pytest.mark.asyncio
    async def test_validate_session_terminated_status(self, session_service):
        """validate_session should return None for terminated session."""
        mock_session = _make_session(SessionStatus.TERMINATED)
        with patch.object(
            session_service, "get_session", AsyncMock(return_value=mock_session)
        ):
            with patch("services.session_service.logger"):
                result = await session_service.validate_session("sess_123")
        assert result is None

    @pytest.mark.asyncio
    async def test_validate_session_expired_status(self, session_service):
        """validate_session should return None for expired status."""
        mock_session = _make_session(SessionStatus.EXPIRED)
        with patch.object(
            session_service, "get_session", AsyncMock(return_value=mock_session)
        ):
            with patch("services.session_service.logger"):
                result = await session_service.validate_session("sess_123")
        assert result is None

    @pytest.mark.asyncio
    async def test_validate_session_idle_status_valid(self, session_service):
        """validate_session should return session for idle status."""
        mock_session = _make_session(SessionStatus.IDLE)
        with patch.object(
            session_service, "get_session", AsyncMock(return_value=mock_session)
        ):
            with patch("services.session_service.logger"):
                result = await session_service.validate_session("sess_123")
        assert result is not None and result.status == SessionStatus.IDLE
