"""
Unit tests for services/session_service.py - Core operations.

Tests initialization, get_idle_timeout, mark_idle_sessions, create_session,
get_session, and helper methods.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.session import Session, SessionStatus
from services.session_service import DEFAULT_IDLE_TIMEOUT_SECONDS, SessionService


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
def base_session_row():
    """Base row for session tests."""
    return {
        "id": "sess_abc123def456",
        "user_id": "user-123",
        "ip_address": "192.168.1.100",
        "user_agent": "Mozilla/5.0",
        "created_at": "2024-01-15T10:00:00+00:00",
        "expires_at": "2024-01-15T22:00:00+00:00",
        "last_activity": "2024-01-15T11:00:00+00:00",
        "status": "active",
        "terminated_at": None,
        "terminated_by": None,
    }


class TestSessionServiceInit:
    """Tests for SessionService initialization."""

    def test_init_stores_db_service(self, mock_db_service):
        """SessionService should store db_service reference."""
        with patch("services.session_service.logger"):
            service = SessionService(mock_db_service)
            assert service.db_service is mock_db_service

    def test_init_creates_default_db_service(self):
        """SessionService should create default db_service if not provided."""
        with (
            patch("services.session_service.logger"),
            patch("services.session_service.DatabaseService") as MockDB,
        ):
            MockDB.return_value = MagicMock()
            service = SessionService()
            assert service.db_service is MockDB.return_value

    def test_init_logs_message(self, mock_db_service):
        """SessionService should log initialization."""
        with patch("services.session_service.logger") as mock_logger:
            SessionService(mock_db_service)
            mock_logger.info.assert_called_with("Session service initialized")


class TestGetIdleTimeoutSeconds:
    """Tests for get_idle_timeout_seconds method."""

    @pytest.mark.asyncio
    async def test_get_idle_timeout_from_settings(
        self, session_service, mock_connection
    ):
        """get_idle_timeout_seconds should return value from settings."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value={"setting_value": "1800"})
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        with patch("services.session_service.logger"):
            result = await session_service.get_idle_timeout_seconds()

        assert result == 1800

    @pytest.mark.asyncio
    async def test_get_idle_timeout_no_setting(self, session_service, mock_connection):
        """get_idle_timeout_seconds should return default when no setting."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=None)
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        with patch("services.session_service.logger"):
            result = await session_service.get_idle_timeout_seconds()

        assert result == DEFAULT_IDLE_TIMEOUT_SECONDS

    @pytest.mark.asyncio
    async def test_get_idle_timeout_empty_value(self, session_service, mock_connection):
        """get_idle_timeout_seconds should return default when value empty."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value={"setting_value": None})
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        with patch("services.session_service.logger"):
            result = await session_service.get_idle_timeout_seconds()

        assert result == DEFAULT_IDLE_TIMEOUT_SECONDS

    @pytest.mark.asyncio
    async def test_get_idle_timeout_error_returns_default(
        self, session_service, mock_connection
    ):
        """get_idle_timeout_seconds should return default on error."""
        mock_connection.execute = AsyncMock(side_effect=Exception("DB error"))

        with patch("services.session_service.logger") as mock_logger:
            result = await session_service.get_idle_timeout_seconds()

        assert result == DEFAULT_IDLE_TIMEOUT_SECONDS
        mock_logger.warning.assert_called()


class TestMarkIdleSessions:
    """Tests for mark_idle_sessions method."""

    @pytest.mark.asyncio
    async def test_mark_idle_sessions_success(self, session_service, mock_connection):
        """mark_idle_sessions should update inactive sessions."""
        # Mock get_idle_timeout_seconds
        with patch.object(
            session_service,
            "get_idle_timeout_seconds",
            new_callable=AsyncMock,
            return_value=900,
        ):
            mock_cursor = AsyncMock()
            mock_cursor.rowcount = 3
            mock_connection.execute = AsyncMock(return_value=mock_cursor)

            with patch("services.session_service.logger"):
                result = await session_service.mark_idle_sessions()

        assert result == 3
        mock_connection.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_mark_idle_sessions_none(self, session_service, mock_connection):
        """mark_idle_sessions should return 0 when no sessions to mark."""
        with patch.object(
            session_service,
            "get_idle_timeout_seconds",
            new_callable=AsyncMock,
            return_value=900,
        ):
            mock_cursor = AsyncMock()
            mock_cursor.rowcount = 0
            mock_connection.execute = AsyncMock(return_value=mock_cursor)

            with patch("services.session_service.logger"):
                result = await session_service.mark_idle_sessions()

        assert result == 0

    @pytest.mark.asyncio
    async def test_mark_idle_sessions_logs_when_marked(
        self, session_service, mock_connection
    ):
        """mark_idle_sessions should log when sessions marked."""
        with patch.object(
            session_service,
            "get_idle_timeout_seconds",
            new_callable=AsyncMock,
            return_value=900,
        ):
            mock_cursor = AsyncMock()
            mock_cursor.rowcount = 5
            mock_connection.execute = AsyncMock(return_value=mock_cursor)

            with patch("services.session_service.logger") as mock_logger:
                await session_service.mark_idle_sessions()

            mock_logger.info.assert_called()
            kwargs = mock_logger.info.call_args[1]
            assert kwargs["count"] == 5


class TestCreateSession:
    """Tests for create_session method."""

    @pytest.mark.asyncio
    async def test_create_session_success(self, session_service, mock_connection):
        """create_session should create new session."""
        expires = datetime.now(UTC) + timedelta(hours=12)

        with patch("services.session_service.logger"):
            result = await session_service.create_session(
                user_id="user-123",
                expires_at=expires,
                ip_address="192.168.1.100",
                user_agent="Mozilla/5.0",
            )

        assert isinstance(result, Session)
        assert result.user_id == "user-123"
        assert result.ip_address == "192.168.1.100"
        assert result.user_agent == "Mozilla/5.0"
        assert result.status == SessionStatus.ACTIVE
        assert result.id.startswith("sess_")
        mock_connection.execute.assert_called_once()
        mock_connection.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_session_without_optional_fields(
        self, session_service, mock_connection
    ):
        """create_session should handle missing optional fields."""
        expires = datetime.now(UTC) + timedelta(hours=12)

        with patch("services.session_service.logger"):
            result = await session_service.create_session(
                user_id="user-123", expires_at=expires
            )

        assert result.ip_address is None
        assert result.user_agent is None

    @pytest.mark.asyncio
    async def test_create_session_logs_success(self, session_service, mock_connection):
        """create_session should log creation."""
        expires = datetime.now(UTC) + timedelta(hours=12)

        with patch("services.session_service.logger") as mock_logger:
            result = await session_service.create_session(
                user_id="user-123", expires_at=expires
            )

        mock_logger.info.assert_called()
        call_kwargs = mock_logger.info.call_args[1]
        assert call_kwargs["user_id"] == "user-123"
        assert "session_id" in call_kwargs
        assert call_kwargs["session_id"] == result.id


class TestGetSession:
    """Tests for get_session method."""

    @pytest.mark.asyncio
    async def test_get_session_found(
        self, session_service, mock_connection, base_session_row
    ):
        """get_session should return session when found."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=base_session_row)
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        with patch("services.session_service.logger"):
            result = await session_service.get_session("sess_abc123def456")

        assert result is not None
        assert isinstance(result, Session)
        assert result.id == "sess_abc123def456"
        assert result.user_id == "user-123"
        assert result.status == SessionStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, session_service, mock_connection):
        """get_session should return None when not found."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=None)
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        with patch("services.session_service.logger"):
            result = await session_service.get_session("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_session_with_terminated_fields(
        self, session_service, mock_connection, base_session_row
    ):
        """get_session should parse terminated fields."""
        row = {
            **base_session_row,
            "status": "terminated",
            "terminated_at": "2024-01-15T12:00:00+00:00",
            "terminated_by": "admin-user",
        }
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=row)
        mock_connection.execute = AsyncMock(return_value=mock_cursor)

        with patch("services.session_service.logger"):
            result = await session_service.get_session("sess_abc123def456")

        assert result.status == SessionStatus.TERMINATED
        assert result.terminated_at is not None
        assert result.terminated_by == "admin-user"


class TestDictFactory:
    """Tests for _dict_factory method."""

    def test_dict_factory_converts_row(self, session_service):
        """_dict_factory should convert row to dictionary."""
        mock_cursor = MagicMock()
        mock_cursor.description = [("id",), ("user_id",), ("status",)]
        row = ("sess_123", "user-abc", "active")

        result = session_service._dict_factory(mock_cursor, row)

        assert result == {"id": "sess_123", "user_id": "user-abc", "status": "active"}

    def test_dict_factory_handles_empty_row(self, session_service):
        """_dict_factory should handle empty row."""
        mock_cursor = MagicMock()
        mock_cursor.description = []
        row = ()

        result = session_service._dict_factory(mock_cursor, row)

        assert result == {}


class TestRowToSession:
    """Tests for _row_to_session method."""

    def test_row_to_session_basic(self, session_service, base_session_row):
        """_row_to_session should convert basic row."""
        result = session_service._row_to_session(base_session_row)

        assert isinstance(result, Session)
        assert result.id == "sess_abc123def456"
        assert result.user_id == "user-123"
        assert result.status == SessionStatus.ACTIVE
        assert result.terminated_at is None
        assert result.terminated_by is None

    def test_row_to_session_with_terminated(self, session_service, base_session_row):
        """_row_to_session should parse terminated fields."""
        row = {
            **base_session_row,
            "status": "terminated",
            "terminated_at": "2024-01-15T12:00:00+00:00",
            "terminated_by": "system",
        }

        result = session_service._row_to_session(row)

        assert result.status == SessionStatus.TERMINATED
        assert result.terminated_at is not None
        assert result.terminated_by == "system"

    def test_row_to_session_all_statuses(self, session_service, base_session_row):
        """_row_to_session should handle all status types."""
        for status in SessionStatus:
            row = {**base_session_row, "status": status.value}
            result = session_service._row_to_session(row)
            assert result.status == status

    def test_row_to_session_null_optional_fields(self, session_service):
        """_row_to_session should handle null optional fields."""
        row = {
            "id": "sess_123",
            "user_id": "user-123",
            "ip_address": None,
            "user_agent": None,
            "created_at": "2024-01-15T10:00:00+00:00",
            "expires_at": "2024-01-15T22:00:00+00:00",
            "last_activity": "2024-01-15T11:00:00+00:00",
            "status": "active",
            "terminated_at": None,
            "terminated_by": None,
        }

        result = session_service._row_to_session(row)

        assert result.ip_address is None
        assert result.user_agent is None
