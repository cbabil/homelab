"""Tests for session service idle detection."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from services.session_service import SessionService, DEFAULT_IDLE_TIMEOUT_SECONDS
from models.session import SessionStatus


class TestSessionServiceIdleDetection:
    """Tests for SessionService idle detection functionality."""

    @pytest.fixture
    def mock_db_service(self):
        """Create mock database service."""
        db = MagicMock()
        return db

    @pytest.fixture
    def session_service(self, mock_db_service):
        """Create session service with mocks."""
        return SessionService(db_service=mock_db_service)

    @pytest.mark.asyncio
    async def test_get_idle_timeout_returns_default_when_no_settings_table(
        self, session_service, mock_db_service
    ):
        """Should return default timeout when settings table doesn't exist."""
        # Mock connection that raises an error (no table)
        mock_conn = AsyncMock()
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)
        mock_conn.execute = AsyncMock(side_effect=Exception("no such table: system_settings"))
        mock_db_service.get_connection.return_value = mock_conn

        timeout = await session_service.get_idle_timeout_seconds()

        assert timeout == DEFAULT_IDLE_TIMEOUT_SECONDS

    @pytest.mark.asyncio
    async def test_get_idle_timeout_returns_setting_value(
        self, session_service, mock_db_service
    ):
        """Should return timeout from settings when available."""
        # Mock connection with a row result
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value={"setting_value": "1800"})

        mock_conn = AsyncMock()
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)
        mock_conn.row_factory = None
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_db_service.get_connection.return_value = mock_conn

        timeout = await session_service.get_idle_timeout_seconds()

        assert timeout == 1800

    @pytest.mark.asyncio
    async def test_mark_idle_sessions_updates_inactive_sessions(
        self, session_service, mock_db_service
    ):
        """Should mark sessions as idle when inactive beyond timeout."""
        # Mock get_idle_timeout_seconds
        with patch.object(
            session_service, 'get_idle_timeout_seconds',
            new_callable=AsyncMock, return_value=900
        ):
            mock_cursor = AsyncMock()
            mock_cursor.rowcount = 3

            mock_conn = AsyncMock()
            mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_conn.__aexit__ = AsyncMock(return_value=None)
            mock_conn.execute = AsyncMock(return_value=mock_cursor)
            mock_conn.commit = AsyncMock()
            mock_db_service.get_connection.return_value = mock_conn

            count = await session_service.mark_idle_sessions()

            assert count == 3
            mock_conn.execute.assert_called_once()
            # Verify the SQL updates to IDLE status
            call_args = mock_conn.execute.call_args[0]
            assert SessionStatus.IDLE.value in call_args[1]
            assert SessionStatus.ACTIVE.value in call_args[1]

    @pytest.mark.asyncio
    async def test_mark_idle_sessions_returns_zero_when_none_idle(
        self, session_service, mock_db_service
    ):
        """Should return 0 when no sessions are idle."""
        with patch.object(
            session_service, 'get_idle_timeout_seconds',
            new_callable=AsyncMock, return_value=900
        ):
            mock_cursor = AsyncMock()
            mock_cursor.rowcount = 0

            mock_conn = AsyncMock()
            mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_conn.__aexit__ = AsyncMock(return_value=None)
            mock_conn.execute = AsyncMock(return_value=mock_cursor)
            mock_conn.commit = AsyncMock()
            mock_db_service.get_connection.return_value = mock_conn

            count = await session_service.mark_idle_sessions()

            assert count == 0

    @pytest.mark.asyncio
    async def test_list_sessions_calls_mark_idle_sessions(
        self, session_service, mock_db_service
    ):
        """Should call mark_idle_sessions before listing sessions."""
        with patch.object(
            session_service, 'mark_idle_sessions',
            new_callable=AsyncMock, return_value=1
        ) as mock_mark_idle:
            # Mock connection for the list query
            mock_cursor = AsyncMock()
            mock_cursor.fetchall = AsyncMock(return_value=[])

            mock_conn = AsyncMock()
            mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_conn.__aexit__ = AsyncMock(return_value=None)
            mock_conn.row_factory = None
            mock_conn.execute = AsyncMock(return_value=mock_cursor)
            mock_db_service.get_connection.return_value = mock_conn

            await session_service.list_sessions()

            mock_mark_idle.assert_called_once()


class TestSessionServiceIdleTimeoutDefault:
    """Tests for default idle timeout constant."""

    def test_default_idle_timeout_is_15_minutes(self):
        """Default idle timeout should be 15 minutes (900 seconds)."""
        assert DEFAULT_IDLE_TIMEOUT_SECONDS == 900
