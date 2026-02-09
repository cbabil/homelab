"""
Unit tests for services/rate_limit_service.py

Tests database-backed rate limiting.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from services.rate_limit_service import RateLimitService


@pytest.fixture
def mock_db_service():
    """Create mock database service."""
    db = MagicMock()
    mock_conn = AsyncMock()
    mock_cursor = AsyncMock()
    mock_cursor.rowcount = 0
    mock_cursor.fetchone = AsyncMock(return_value=(0,))
    mock_conn.execute = AsyncMock(return_value=mock_cursor)
    mock_conn.commit = AsyncMock()

    ctx_manager = AsyncMock()
    ctx_manager.__aenter__ = AsyncMock(return_value=mock_conn)
    ctx_manager.__aexit__ = AsyncMock(return_value=False)
    db.get_connection = MagicMock(return_value=ctx_manager)

    return db


@pytest.fixture
def rate_limit_service(mock_db_service):
    """Create RateLimitService instance."""
    return RateLimitService(db_service=mock_db_service)


class TestIsAllowed:
    """Tests for is_allowed method."""

    @pytest.mark.asyncio
    async def test_allowed_when_under_limit(self, rate_limit_service):
        """is_allowed should return True when count is below max."""
        result = await rate_limit_service.is_allowed("login", "1.2.3.4", 5, 300)
        assert result is True

    @pytest.mark.asyncio
    async def test_denied_when_at_limit(self, rate_limit_service, mock_db_service):
        """is_allowed should return False when count reaches max."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=(5,))
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_conn.commit = AsyncMock()

        ctx_manager = AsyncMock()
        ctx_manager.__aenter__ = AsyncMock(return_value=mock_conn)
        ctx_manager.__aexit__ = AsyncMock(return_value=False)
        mock_db_service.get_connection = MagicMock(return_value=ctx_manager)

        result = await rate_limit_service.is_allowed("login", "1.2.3.4", 5, 300)
        assert result is False

    @pytest.mark.asyncio
    async def test_records_event_when_allowed(
        self, rate_limit_service, mock_db_service
    ):
        """is_allowed should record event when under limit."""
        await rate_limit_service.is_allowed("login", "1.2.3.4", 5, 300)

        # Verify INSERT was called (for recording)
        ctx_manager = mock_db_service.get_connection()
        conn = await ctx_manager.__aenter__()
        calls = conn.execute.call_args_list
        insert_calls = [
            c for c in calls if "INSERT INTO rate_limit_events" in str(c)
        ]
        assert len(insert_calls) > 0


class TestRecord:
    """Tests for record method."""

    @pytest.mark.asyncio
    async def test_record_inserts_event(self, rate_limit_service, mock_db_service):
        """record should insert event into database."""
        await rate_limit_service.record("login", "1.2.3.4")

        ctx_manager = mock_db_service.get_connection()
        conn = await ctx_manager.__aenter__()
        calls = conn.execute.call_args_list
        insert_calls = [
            c for c in calls if "INSERT INTO rate_limit_events" in str(c)
        ]
        assert len(insert_calls) > 0


class TestGetCount:
    """Tests for get_count method."""

    @pytest.mark.asyncio
    async def test_get_count_returns_count(self, rate_limit_service, mock_db_service):
        """get_count should return event count from database."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=(3,))
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)

        ctx_manager = AsyncMock()
        ctx_manager.__aenter__ = AsyncMock(return_value=mock_conn)
        ctx_manager.__aexit__ = AsyncMock(return_value=False)
        mock_db_service.get_connection = MagicMock(return_value=ctx_manager)

        count = await rate_limit_service.get_count("login", "1.2.3.4", 300)
        assert count == 3

    @pytest.mark.asyncio
    async def test_get_count_returns_zero_when_no_rows(
        self, rate_limit_service, mock_db_service
    ):
        """get_count should return 0 when no matching rows."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=None)
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)

        ctx_manager = AsyncMock()
        ctx_manager.__aenter__ = AsyncMock(return_value=mock_conn)
        ctx_manager.__aexit__ = AsyncMock(return_value=False)
        mock_db_service.get_connection = MagicMock(return_value=ctx_manager)

        count = await rate_limit_service.get_count("login", "1.2.3.4", 300)
        assert count == 0


class TestReset:
    """Tests for reset method."""

    @pytest.mark.asyncio
    async def test_reset_deletes_events(self, rate_limit_service, mock_db_service):
        """reset should delete all events for the key."""
        await rate_limit_service.reset("login", "1.2.3.4")

        ctx_manager = mock_db_service.get_connection()
        conn = await ctx_manager.__aenter__()
        calls = conn.execute.call_args_list
        delete_calls = [
            c
            for c in calls
            if "DELETE FROM rate_limit_events" in str(c)
            and "category" in str(c)
        ]
        assert len(delete_calls) > 0


class TestCleanupExpired:
    """Tests for cleanup_expired method."""

    @pytest.mark.asyncio
    async def test_cleanup_deletes_old_events(
        self, rate_limit_service, mock_db_service
    ):
        """cleanup_expired should delete events older than max window."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 10
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_conn.commit = AsyncMock()

        ctx_manager = AsyncMock()
        ctx_manager.__aenter__ = AsyncMock(return_value=mock_conn)
        ctx_manager.__aexit__ = AsyncMock(return_value=False)
        mock_db_service.get_connection = MagicMock(return_value=ctx_manager)

        count = await rate_limit_service.cleanup_expired(3600)
        assert count == 10

    @pytest.mark.asyncio
    async def test_cleanup_returns_zero_when_nothing_expired(
        self, rate_limit_service, mock_db_service
    ):
        """cleanup_expired should return 0 when nothing to clean."""
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 0
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=mock_cursor)
        mock_conn.commit = AsyncMock()

        ctx_manager = AsyncMock()
        ctx_manager.__aenter__ = AsyncMock(return_value=mock_conn)
        ctx_manager.__aexit__ = AsyncMock(return_value=False)
        mock_db_service.get_connection = MagicMock(return_value=ctx_manager)

        count = await rate_limit_service.cleanup_expired()
        assert count == 0
