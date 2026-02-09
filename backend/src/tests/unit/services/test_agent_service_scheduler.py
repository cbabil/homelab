"""
Agent Service Unit Tests - Token Rotation Scheduler

Tests for the automatic token rotation scheduler functionality.
"""

import asyncio
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.agent import Agent, AgentStatus
from services.agent_service import AgentService


class TestRotationScheduler:
    """Tests for rotation scheduler methods."""

    @pytest.fixture
    def mock_db_service(self):
        """Create mock database service."""
        return MagicMock()

    @pytest.fixture
    def mock_agent_db(self):
        """Create mock AgentDatabaseService."""
        db = AsyncMock()
        db.get_agent = AsyncMock(return_value=None)
        db.update_agent = AsyncMock(return_value=True)
        db.get_agents_with_expiring_tokens = AsyncMock(return_value=[])
        return db

    @pytest.fixture
    def mock_settings_service(self):
        """Create mock SettingsService."""
        service = MagicMock()
        service.get_setting = AsyncMock(side_effect=lambda key, default: default)
        return service

    @pytest.fixture
    def agent_service(self, mock_db_service, mock_agent_db, mock_settings_service):
        """Create AgentService with mocked dependencies."""
        with patch("services.agent_service.logger"):
            return AgentService(
                db_service=mock_db_service,
                settings_service=mock_settings_service,
                agent_db=mock_agent_db,
            )

    @pytest.mark.asyncio
    async def test_start_scheduler_sets_running_flag(
        self, agent_service, mock_agent_db
    ):
        """Test that starting scheduler sets running flag."""
        assert agent_service._rotation_running is False

        await agent_service.start_rotation_scheduler(check_interval=1)

        assert agent_service._rotation_running is True
        assert agent_service._rotation_task is not None

        # Cleanup
        await agent_service.stop_rotation_scheduler()

    @pytest.mark.asyncio
    async def test_stop_scheduler_clears_running_flag(
        self, agent_service, mock_agent_db
    ):
        """Test that stopping scheduler clears running flag."""
        await agent_service.start_rotation_scheduler(check_interval=1)

        await agent_service.stop_rotation_scheduler()

        assert agent_service._rotation_running is False
        assert agent_service._rotation_task is None

    @pytest.mark.asyncio
    async def test_start_scheduler_twice_warns(self, agent_service, mock_agent_db):
        """Test that starting scheduler twice logs warning."""
        await agent_service.start_rotation_scheduler(check_interval=1)

        with patch("services.agent_rotation.logger") as mock_logger:
            await agent_service.start_rotation_scheduler(check_interval=1)
            mock_logger.warning.assert_called_once()

        await agent_service.stop_rotation_scheduler()

    @pytest.mark.asyncio
    async def test_check_token_expiry_no_agents(self, agent_service, mock_agent_db):
        """Test check_token_expiry with no agents needing rotation."""
        mock_agent_db.get_agents_with_expiring_tokens.return_value = []

        result = await agent_service.check_token_expiry()

        assert result == 0

    @pytest.mark.asyncio
    async def test_check_token_expiry_identifies_expired_agents(
        self, agent_service, mock_agent_db
    ):
        """Test check_token_expiry finds agents with expired tokens."""
        expired_agent = Agent(
            id="agent-123",
            server_id="server-1",
            token_hash="hash",
            status=AgentStatus.CONNECTED,
            registered_at=datetime.now(UTC),
            token_issued_at=datetime.now(UTC) - timedelta(days=10),
            token_expires_at=datetime.now(UTC) - timedelta(days=3),
        )
        mock_agent_db.get_agents_with_expiring_tokens.return_value = [expired_agent]
        mock_agent_db.get_agent.return_value = expired_agent

        # Set callback to return success
        callback = AsyncMock(return_value=True)
        agent_service.set_rotation_callback(callback)

        result = await agent_service.check_token_expiry()

        assert result == 1
        callback.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_token_expiry_skips_when_no_callback(
        self, agent_service, mock_agent_db
    ):
        """Test check_token_expiry skips agents when no callback set."""
        expired_agent = Agent(
            id="agent-123",
            server_id="server-1",
            token_hash="hash",
            status=AgentStatus.CONNECTED,
            registered_at=datetime.now(UTC),
            token_expires_at=datetime.now(UTC) - timedelta(days=1),
        )
        mock_agent_db.get_agents_with_expiring_tokens.return_value = [expired_agent]

        # No callback set
        result = await agent_service.check_token_expiry()

        assert result == 0

    @pytest.mark.asyncio
    async def test_check_token_expiry_cancels_on_send_failure(
        self, agent_service, mock_agent_db
    ):
        """Test check_token_expiry cancels rotation when send fails."""
        expired_agent = Agent(
            id="agent-123",
            server_id="server-1",
            token_hash="hash",
            status=AgentStatus.CONNECTED,
            registered_at=datetime.now(UTC),
            token_expires_at=datetime.now(UTC) - timedelta(days=1),
        )
        mock_agent_db.get_agents_with_expiring_tokens.return_value = [expired_agent]
        mock_agent_db.get_agent.return_value = expired_agent

        # Callback returns failure
        callback = AsyncMock(return_value=False)
        agent_service.set_rotation_callback(callback)

        result = await agent_service.check_token_expiry()

        assert result == 0
        # Verify cancel_rotation was called
        mock_agent_db.update_agent.assert_called()

    @pytest.mark.asyncio
    async def test_check_token_expiry_handles_callback_error(
        self, agent_service, mock_agent_db
    ):
        """Test check_token_expiry handles callback exceptions."""
        expired_agent = Agent(
            id="agent-123",
            server_id="server-1",
            token_hash="hash",
            status=AgentStatus.CONNECTED,
            registered_at=datetime.now(UTC),
            token_expires_at=datetime.now(UTC) - timedelta(days=1),
        )
        mock_agent_db.get_agents_with_expiring_tokens.return_value = [expired_agent]
        mock_agent_db.get_agent.return_value = expired_agent

        # Callback raises exception
        callback = AsyncMock(side_effect=Exception("Connection error"))
        agent_service.set_rotation_callback(callback)

        # Should not raise
        result = await agent_service.check_token_expiry()

        assert result == 0

    @pytest.mark.asyncio
    async def test_set_rotation_callback_stores_callback(self, agent_service):
        """Test set_rotation_callback stores the callback."""
        callback = AsyncMock()

        agent_service.set_rotation_callback(callback)

        assert agent_service._rotation_callback is callback

    @pytest.mark.asyncio
    async def test_scheduler_uses_custom_interval(self, agent_service, mock_agent_db):
        """Test scheduler uses provided check interval."""
        await agent_service.start_rotation_scheduler(check_interval=7200)

        assert agent_service._rotation_check_interval == 7200

        await agent_service.stop_rotation_scheduler()

    @pytest.mark.asyncio
    async def test_scheduler_loop_handles_errors(self, agent_service, mock_agent_db):
        """Test scheduler loop continues after errors."""
        # Make get_agents_with_expiring_tokens raise an error first, then work
        call_count = 0

        async def side_effect(*args):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Database error")
            return []

        mock_agent_db.get_agents_with_expiring_tokens.side_effect = side_effect

        await agent_service.start_rotation_scheduler(check_interval=0.1)
        await asyncio.sleep(0.3)
        await agent_service.stop_rotation_scheduler()

        # Should have been called multiple times despite error
        assert call_count >= 2
