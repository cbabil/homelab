"""Tests for activity log service."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from services.activity_service import ActivityService
from models.metrics import ActivityType


class TestActivityService:
    """Tests for ActivityService."""

    @pytest.fixture
    def mock_db_service(self):
        """Create mock database service."""
        db = MagicMock()
        db.save_activity_log = AsyncMock()
        db.get_activity_logs = AsyncMock(return_value=[])
        return db

    @pytest.fixture
    def activity_service(self, mock_db_service):
        """Create activity service with mocks."""
        return ActivityService(db_service=mock_db_service)

    @pytest.mark.asyncio
    async def test_log_user_login(self, activity_service, mock_db_service):
        """Should log user login activity."""
        await activity_service.log_activity(
            activity_type=ActivityType.USER_LOGIN,
            user_id="user-123",
            message="User admin logged in"
        )

        mock_db_service.save_activity_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_log_server_added(self, activity_service, mock_db_service):
        """Should log server added activity."""
        await activity_service.log_activity(
            activity_type=ActivityType.SERVER_ADDED,
            user_id="user-123",
            server_id="server-456",
            message="Server 'web-01' added"
        )

        mock_db_service.save_activity_log.assert_called_once()
        call_args = mock_db_service.save_activity_log.call_args[0][0]
        assert call_args.server_id == "server-456"

    @pytest.mark.asyncio
    async def test_log_app_installed(self, activity_service, mock_db_service):
        """Should log app installation activity."""
        await activity_service.log_activity(
            activity_type=ActivityType.APP_INSTALLED,
            user_id="user-123",
            server_id="server-456",
            app_id="portainer",
            message="Portainer installed on server web-01"
        )

        mock_db_service.save_activity_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_recent_activities(self, activity_service, mock_db_service):
        """Should get recent activities."""
        mock_db_service.get_activity_logs.return_value = [
            MagicMock(activity_type=ActivityType.USER_LOGIN, message="Login")
        ]

        result = await activity_service.get_recent_activities(limit=10)

        assert len(result) == 1
        mock_db_service.get_activity_logs.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_activities_filtered(self, activity_service, mock_db_service):
        """Should filter activities by type."""
        await activity_service.get_activities(
            activity_types=[ActivityType.USER_LOGIN, ActivityType.USER_LOGOUT],
            limit=50
        )

        mock_db_service.get_activity_logs.assert_called_once()
