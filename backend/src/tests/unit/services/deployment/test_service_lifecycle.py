"""
Unit tests for services/deployment/service.py - Lifecycle Operations

Tests for uninstall_app, start_app, stop_app, and cleanup methods.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def mock_services():
    """Create mock services for DeploymentService."""
    services = {
        "ssh": MagicMock(),
        "server": MagicMock(),
        "marketplace": MagicMock(),
        "db": MagicMock(),
        "activity": MagicMock(),
        "agent_manager": MagicMock(),
        "agent_service": MagicMock(),
    }
    # Setup connected agent by default
    agent = MagicMock()
    agent.id = "agent-123"
    services["agent_service"].get_agent_by_server = AsyncMock(return_value=agent)
    services["agent_manager"].is_connected.return_value = True
    services["agent_manager"].send_command = AsyncMock(return_value={})
    return services


@pytest.fixture
def deployment_service(mock_services):
    """Create DeploymentService instance."""
    from services.deployment.service import DeploymentService

    with patch("services.deployment.service.logger"):
        return DeploymentService(
            ssh_service=mock_services["ssh"],
            server_service=mock_services["server"],
            marketplace_service=mock_services["marketplace"],
            db_service=mock_services["db"],
            activity_service=mock_services["activity"],
            agent_manager=mock_services["agent_manager"],
            agent_service=mock_services["agent_service"],
        )


@pytest.fixture
def sample_installation():
    """Create sample installation mock."""
    inst = MagicMock()
    inst.id = "inst-123"
    inst.app_id = "app-1"
    inst.server_id = "server-1"
    inst.container_name = "test-container"
    inst.container_id = "abc123"
    inst.status = "running"
    return inst


class TestUninstallApp:
    """Tests for uninstall_app method."""

    @pytest.mark.asyncio
    async def test_returns_false_when_installation_not_found(
        self, deployment_service, mock_services
    ):
        """Should return False when installation not found."""
        mock_services["db"].get_installation = AsyncMock(return_value=None)

        result = await deployment_service.uninstall_app("server-1", "app-1")

        assert result is False

    @pytest.mark.asyncio
    async def test_stops_and_removes_container(
        self, deployment_service, mock_services, sample_installation
    ):
        """Should stop and remove container via agent."""
        mock_services["db"].get_installation = AsyncMock(
            return_value=sample_installation
        )
        mock_services["db"].delete_installation = AsyncMock()
        mock_services["activity"].log_activity = AsyncMock()

        result = await deployment_service.uninstall_app("server-1", "app-1")

        assert result is True
        # Should have called agent commands
        calls = mock_services["agent_manager"].send_command.call_args_list
        methods = [c[1]["method"] for c in calls]
        assert "docker.containers.stop" in methods
        assert "docker.containers.remove" in methods

    @pytest.mark.asyncio
    async def test_removes_volumes_when_requested(
        self, deployment_service, mock_services, sample_installation
    ):
        """Should remove volumes when remove_data is True."""
        mock_services["db"].get_installation = AsyncMock(
            return_value=sample_installation
        )
        mock_services["db"].delete_installation = AsyncMock()
        mock_services["activity"].log_activity = AsyncMock()

        await deployment_service.uninstall_app("server-1", "app-1", remove_data=True)

        calls = mock_services["agent_manager"].send_command.call_args_list
        methods = [c[1]["method"] for c in calls]
        assert "docker.volumes.prune" in methods

    @pytest.mark.asyncio
    async def test_deletes_database_record(
        self, deployment_service, mock_services, sample_installation
    ):
        """Should delete database record."""
        mock_services["db"].get_installation = AsyncMock(
            return_value=sample_installation
        )
        mock_services["db"].delete_installation = AsyncMock()
        mock_services["activity"].log_activity = AsyncMock()

        await deployment_service.uninstall_app("server-1", "app-1")

        mock_services["db"].delete_installation.assert_called_once_with(
            "server-1", "app-1"
        )

    @pytest.mark.asyncio
    async def test_logs_activity(
        self, deployment_service, mock_services, sample_installation
    ):
        """Should log uninstall activity."""
        mock_services["db"].get_installation = AsyncMock(
            return_value=sample_installation
        )
        mock_services["db"].delete_installation = AsyncMock()
        mock_services["activity"].log_activity = AsyncMock()

        await deployment_service.uninstall_app("server-1", "app-1")

        mock_services["activity"].log_activity.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_false_on_exception(self, deployment_service, mock_services):
        """Should return False on exception."""
        mock_services["db"].get_installation = AsyncMock(
            side_effect=Exception("DB error")
        )

        result = await deployment_service.uninstall_app("server-1", "app-1")

        assert result is False


class TestStartApp:
    """Tests for start_app method."""

    @pytest.mark.asyncio
    async def test_returns_false_when_installation_not_found(
        self, deployment_service, mock_services
    ):
        """Should return False when installation not found."""
        mock_services["db"].get_installation = AsyncMock(return_value=None)

        result = await deployment_service.start_app("server-1", "app-1")

        assert result is False

    @pytest.mark.asyncio
    async def test_returns_false_when_agent_not_connected(
        self, deployment_service, mock_services, sample_installation
    ):
        """Should return False when agent not connected."""
        mock_services["db"].get_installation = AsyncMock(
            return_value=sample_installation
        )
        mock_services["agent_service"].get_agent_by_server.return_value = None

        result = await deployment_service.start_app("server-1", "app-1")

        assert result is False

    @pytest.mark.asyncio
    async def test_starts_container(
        self, deployment_service, mock_services, sample_installation
    ):
        """Should start container via agent."""
        mock_services["db"].get_installation = AsyncMock(
            return_value=sample_installation
        )
        mock_services["db"].update_installation = AsyncMock()
        mock_services["agent_manager"].send_command.return_value = True

        result = await deployment_service.start_app("server-1", "app-1")

        assert result is True
        call_kwargs = mock_services["agent_manager"].send_command.call_args[1]
        assert call_kwargs["method"] == "docker.containers.start"
        assert call_kwargs["params"]["container"] == "test-container"

    @pytest.mark.asyncio
    async def test_updates_installation_status(
        self, deployment_service, mock_services, sample_installation
    ):
        """Should update installation status to running."""
        mock_services["db"].get_installation = AsyncMock(
            return_value=sample_installation
        )
        mock_services["db"].update_installation = AsyncMock()
        mock_services["agent_manager"].send_command.return_value = True

        await deployment_service.start_app("server-1", "app-1")

        mock_services["db"].update_installation.assert_called()
        call_args = mock_services["db"].update_installation.call_args
        assert call_args[1]["status"] == "running"

    @pytest.mark.asyncio
    async def test_returns_false_when_start_fails(
        self, deployment_service, mock_services, sample_installation
    ):
        """Should return False when start command returns falsy."""
        mock_services["db"].get_installation = AsyncMock(
            return_value=sample_installation
        )
        mock_services["agent_manager"].send_command.return_value = None

        result = await deployment_service.start_app("server-1", "app-1")

        assert result is False

    @pytest.mark.asyncio
    async def test_returns_false_on_exception(self, deployment_service, mock_services):
        """Should return False on exception."""
        mock_services["db"].get_installation = AsyncMock(side_effect=Exception("Error"))

        result = await deployment_service.start_app("server-1", "app-1")

        assert result is False


class TestStopApp:
    """Tests for stop_app method."""

    @pytest.mark.asyncio
    async def test_returns_false_when_installation_not_found(
        self, deployment_service, mock_services
    ):
        """Should return False when installation not found."""
        mock_services["db"].get_installation = AsyncMock(return_value=None)

        result = await deployment_service.stop_app("server-1", "app-1")

        assert result is False

    @pytest.mark.asyncio
    async def test_stops_container(
        self, deployment_service, mock_services, sample_installation
    ):
        """Should stop container via agent."""
        mock_services["db"].get_installation = AsyncMock(
            return_value=sample_installation
        )
        mock_services["db"].update_installation = AsyncMock()

        result = await deployment_service.stop_app("server-1", "app-1")

        assert result is True

    @pytest.mark.asyncio
    async def test_updates_installation_status(
        self, deployment_service, mock_services, sample_installation
    ):
        """Should update installation status to stopped."""
        mock_services["db"].get_installation = AsyncMock(
            return_value=sample_installation
        )
        mock_services["db"].update_installation = AsyncMock()

        await deployment_service.stop_app("server-1", "app-1")

        mock_services["db"].update_installation.assert_called()
        call_args = mock_services["db"].update_installation.call_args
        assert call_args[1]["status"] == "stopped"

    @pytest.mark.asyncio
    async def test_returns_false_when_stop_fails(
        self, deployment_service, mock_services, sample_installation
    ):
        """Should return False when stop fails."""
        mock_services["db"].get_installation = AsyncMock(
            return_value=sample_installation
        )
        mock_services["agent_service"].get_agent_by_server.return_value = None

        result = await deployment_service.stop_app("server-1", "app-1")

        assert result is False

    @pytest.mark.asyncio
    async def test_returns_false_on_exception(self, deployment_service, mock_services):
        """Should return False on exception."""
        mock_services["db"].get_installation = AsyncMock(side_effect=Exception("Error"))

        result = await deployment_service.stop_app("server-1", "app-1")

        assert result is False


class TestCleanupFailedDeployment:
    """Tests for cleanup_failed_deployment method."""

    @pytest.mark.asyncio
    async def test_returns_error_when_installation_not_found(
        self, deployment_service, mock_services
    ):
        """Should return error when installation not found."""
        mock_services["db"].get_installation_by_id = AsyncMock(return_value=None)

        result = await deployment_service.cleanup_failed_deployment(
            "server-1", "inst-123"
        )

        assert result["container_removed"] is False
        assert "Installation record not found" in result["errors"]

    @pytest.mark.asyncio
    async def test_removes_container(
        self, deployment_service, mock_services, sample_installation
    ):
        """Should remove container."""
        mock_services["db"].get_installation_by_id = AsyncMock(
            return_value=sample_installation
        )
        mock_services["marketplace"].get_app = AsyncMock(return_value=None)
        mock_services["db"].delete_installation = AsyncMock()

        result = await deployment_service.cleanup_failed_deployment(
            "server-1", "inst-123"
        )

        assert result["container_removed"] is True

    @pytest.mark.asyncio
    async def test_removes_image_when_app_found(
        self, deployment_service, mock_services, sample_installation
    ):
        """Should remove image when app is found."""
        mock_services["db"].get_installation_by_id = AsyncMock(
            return_value=sample_installation
        )
        app = MagicMock()
        app.docker.image = "nginx:latest"
        mock_services["marketplace"].get_app = AsyncMock(return_value=app)
        mock_services["db"].delete_installation = AsyncMock()
        mock_services["agent_manager"].send_command.return_value = {}

        result = await deployment_service.cleanup_failed_deployment(
            "server-1", "inst-123"
        )

        assert result["image_removed"] is True

    @pytest.mark.asyncio
    async def test_deletes_installation_record(
        self, deployment_service, mock_services, sample_installation
    ):
        """Should delete installation record."""
        mock_services["db"].get_installation_by_id = AsyncMock(
            return_value=sample_installation
        )
        mock_services["marketplace"].get_app = AsyncMock(return_value=None)
        mock_services["db"].delete_installation = AsyncMock()

        result = await deployment_service.cleanup_failed_deployment(
            "server-1", "inst-123"
        )

        assert result["record_removed"] is True
        mock_services["db"].delete_installation.assert_called_once()

    @pytest.mark.asyncio
    async def test_handles_exception(self, deployment_service, mock_services):
        """Should handle exception during cleanup."""
        mock_services["db"].get_installation_by_id = AsyncMock(
            side_effect=Exception("DB error")
        )

        result = await deployment_service.cleanup_failed_deployment(
            "server-1", "inst-123"
        )

        assert "DB error" in result["errors"]


class TestCleanupContainer:
    """Tests for _cleanup_container helper method."""

    @pytest.mark.asyncio
    async def test_stops_and_removes_container(self, deployment_service, mock_services):
        """Should stop and remove container."""
        await deployment_service._cleanup_container("server-1", "my-container")

        calls = mock_services["agent_manager"].send_command.call_args_list
        methods = [c[1]["method"] for c in calls]
        assert "docker.containers.stop" in methods
        assert "docker.containers.remove" in methods

    @pytest.mark.asyncio
    async def test_removes_image_when_specified(
        self, deployment_service, mock_services
    ):
        """Should remove image when specified."""
        await deployment_service._cleanup_container(
            "server-1", "my-container", image="nginx:latest"
        )

        calls = mock_services["agent_manager"].send_command.call_args_list
        methods = [c[1]["method"] for c in calls]
        assert "docker.images.remove" in methods

    @pytest.mark.asyncio
    async def test_handles_image_removal_failure(
        self, deployment_service, mock_services
    ):
        """Should handle image removal failure gracefully."""
        mock_services["agent_manager"].send_command.side_effect = [
            {},  # stop success
            {},  # remove success
            Exception("Image in use"),  # image remove fails
        ]

        # Should not raise
        await deployment_service._cleanup_container(
            "server-1", "my-container", image="nginx:latest"
        )


class TestLogActivity:
    """Tests for _log_activity helper method."""

    @pytest.mark.asyncio
    async def test_logs_activity(self, deployment_service, mock_services):
        """Should log activity via activity service."""
        from models.metrics import ActivityType

        mock_services["activity"].log_activity = AsyncMock()

        await deployment_service._log_activity(
            ActivityType.APP_INSTALLED,
            "App installed",
            "server-1",
            "app-1",
            {"key": "value"},
        )

        mock_services["activity"].log_activity.assert_called_once()

    @pytest.mark.asyncio
    async def test_handles_logging_failure(self, deployment_service, mock_services):
        """Should handle logging failure gracefully."""
        from models.metrics import ActivityType

        mock_services["activity"].log_activity = AsyncMock(
            side_effect=Exception("Log failed")
        )

        # Should not raise
        await deployment_service._log_activity(
            ActivityType.APP_INSTALLED,
            "App installed",
            "server-1",
            "app-1",
            {},
        )

    @pytest.mark.asyncio
    async def test_skips_logging_when_no_service(self, mock_services):
        """Should skip logging when activity service is None."""
        from models.metrics import ActivityType
        from services.deployment.service import DeploymentService

        with patch("services.deployment.service.logger"):
            service = DeploymentService(
                ssh_service=mock_services["ssh"],
                server_service=mock_services["server"],
                marketplace_service=mock_services["marketplace"],
                db_service=mock_services["db"],
            )

        # Should not raise
        await service._log_activity(
            ActivityType.APP_INSTALLED,
            "App installed",
            "server-1",
            "app-1",
            {},
        )
