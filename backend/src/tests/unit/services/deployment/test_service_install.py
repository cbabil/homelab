"""
Unit tests for services/deployment/service.py - Install Operations

Tests for install_app method and _wait_for_container helper.
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
    services["activity"].log_activity = AsyncMock()
    return services


@pytest.fixture
def mock_app():
    """Create mock app."""
    app = MagicMock()
    app.id = "app-1"
    app.name = "Test App"
    app.docker.image = "testapp:latest"
    app.docker.restart_policy = "unless-stopped"
    app.docker.network_mode = "bridge"
    app.docker.privileged = False
    app.docker.capabilities = []
    app.docker.ports = []
    app.docker.volumes = []
    return app


@pytest.fixture
def mock_server():
    """Create mock server."""
    server = MagicMock()
    server.id = "server-1"
    server.name = "Test Server"
    server.host = "192.168.1.100"
    return server


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


class TestInstallApp:
    """Tests for install_app method."""

    @pytest.mark.asyncio
    async def test_raises_when_app_not_found(self, deployment_service, mock_services):
        """Should raise DeploymentError when app not found."""
        from services.deployment.service import DeploymentError

        mock_services["marketplace"].get_app = AsyncMock(return_value=None)

        with pytest.raises(DeploymentError) as exc_info:
            await deployment_service.install_app("server-1", "unknown-app")

        assert "not found in marketplace" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_raises_when_server_not_found(
        self, deployment_service, mock_services, mock_app
    ):
        """Should raise DeploymentError when server not found."""
        from services.deployment.service import DeploymentError

        mock_services["marketplace"].get_app = AsyncMock(return_value=mock_app)
        mock_services["server"].get_server = AsyncMock(return_value=None)

        with pytest.raises(DeploymentError) as exc_info:
            await deployment_service.install_app("unknown-server", "app-1")

        assert "not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_raises_when_preflight_fails(
        self, deployment_service, mock_services, mock_app, mock_server
    ):
        """Should raise DeploymentError when preflight check fails."""
        from services.deployment.service import DeploymentError

        mock_services["marketplace"].get_app = AsyncMock(return_value=mock_app)
        mock_services["server"].get_server = AsyncMock(return_value=mock_server)
        mock_services["db"].get_installation = AsyncMock(return_value=None)
        mock_services["db"].create_installation = AsyncMock(
            return_value=MagicMock(id="inst-123")
        )
        mock_services["db"].update_installation = AsyncMock()
        # Return preflight failure
        mock_services["agent_manager"].send_command.return_value = {
            "success": False,
            "errors": ["Not enough disk space"],
        }

        with pytest.raises(DeploymentError) as exc_info:
            await deployment_service.install_app("server-1", "app-1")

        assert "Pre-flight check failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_raises_when_create_installation_fails(
        self, deployment_service, mock_services, mock_app, mock_server
    ):
        """Should raise DeploymentError when DB installation creation fails."""
        from services.deployment.service import DeploymentError

        mock_services["marketplace"].get_app = AsyncMock(return_value=mock_app)
        mock_services["server"].get_server = AsyncMock(return_value=mock_server)
        mock_services["db"].get_installation = AsyncMock(return_value=None)
        mock_services["db"].create_installation = AsyncMock(return_value=None)

        with pytest.raises(DeploymentError) as exc_info:
            await deployment_service.install_app("server-1", "app-1")

        assert "Failed to create installation record" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_raises_when_image_pull_fails(
        self, deployment_service, mock_services, mock_app, mock_server
    ):
        """Should raise DeploymentError when image pull fails."""
        from services.deployment.service import DeploymentError

        mock_services["marketplace"].get_app = AsyncMock(return_value=mock_app)
        mock_services["server"].get_server = AsyncMock(return_value=mock_server)
        mock_services["db"].get_installation = AsyncMock(return_value=None)
        mock_services["db"].create_installation = AsyncMock(
            return_value=MagicMock(id="inst-123")
        )
        mock_services["db"].update_installation = AsyncMock()

        # Preflight succeeds, pull fails
        mock_services["agent_manager"].send_command.side_effect = [
            {"success": True},  # preflight
            Exception("Pull failed"),  # pull
        ]

        with pytest.raises(DeploymentError) as exc_info:
            await deployment_service.install_app("server-1", "app-1")

        assert "Failed to pull image" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_raises_when_container_create_fails(
        self, deployment_service, mock_services, mock_app, mock_server
    ):
        """Should raise DeploymentError when container creation fails."""
        from services.deployment.service import DeploymentError

        mock_services["marketplace"].get_app = AsyncMock(return_value=mock_app)
        mock_services["server"].get_server = AsyncMock(return_value=mock_server)
        mock_services["db"].get_installation = AsyncMock(return_value=None)
        mock_services["db"].create_installation = AsyncMock(
            return_value=MagicMock(id="inst-123")
        )
        mock_services["db"].update_installation = AsyncMock()

        # Preflight succeeds, pull succeeds, run fails
        mock_services["agent_manager"].send_command.side_effect = [
            {"success": True},  # preflight
            {"id": "sha256:abc"},  # pull
            Exception("Container run failed"),  # run
        ]

        with pytest.raises(DeploymentError) as exc_info:
            await deployment_service.install_app("server-1", "app-1")

        assert "Failed to create container" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_cleans_up_existing_installation(
        self, deployment_service, mock_services, mock_app, mock_server
    ):
        """Should clean up existing installation before new install."""
        existing = MagicMock()
        existing.id = "existing-inst"
        existing.container_name = "old-container"
        existing.installed_at = "2024-01-01T00:00:00Z"

        mock_services["marketplace"].get_app = AsyncMock(return_value=mock_app)
        mock_services["server"].get_server = AsyncMock(return_value=mock_server)
        mock_services["db"].get_installation = AsyncMock(return_value=existing)
        mock_services["db"].delete_installation = AsyncMock()
        mock_services["db"].create_installation = AsyncMock(
            return_value=MagicMock(id="new-inst")
        )
        mock_services["db"].update_installation = AsyncMock()

        # Preflight succeeds, pull succeeds, run succeeds, status succeeds
        mock_services["agent_manager"].send_command.side_effect = [
            {},  # stop old container
            {},  # remove old container
            {"success": True},  # preflight
            {"id": "sha256:abc"},  # pull
            {"container_id": "new-container"},  # run
            {"status": "running", "health": "none", "restart_count": 0},  # status
            {},  # update restart policy
            {
                "State": {"Status": "running"},
                "NetworkSettings": {"Networks": {}},
                "Mounts": [],
            },  # inspect
        ]

        await deployment_service.install_app("server-1", "app-1")

        mock_services["db"].delete_installation.assert_called_once()

    @pytest.mark.asyncio
    async def test_handles_general_exception(
        self, deployment_service, mock_services, mock_app, mock_server
    ):
        """Should handle and re-raise general exceptions."""
        from services.deployment.service import DeploymentError

        mock_services["marketplace"].get_app = AsyncMock(
            side_effect=Exception("Unexpected error")
        )

        with pytest.raises(DeploymentError) as exc_info:
            await deployment_service.install_app("server-1", "app-1")

        assert "Deployment failed" in str(exc_info.value)


class TestInstallAppVolumeHandling:
    """Tests for volume handling during install_app."""

    @pytest.mark.asyncio
    async def test_normalizes_volume_paths(
        self, deployment_service, mock_services, mock_app, mock_server
    ):
        """Should normalize volume paths to allowed directories."""
        # Setup volume
        volume = MagicMock()
        volume.host_path = "/var/data"
        volume.container_path = "/data"
        volume.readonly = False
        mock_app.docker.volumes = [volume]

        mock_services["marketplace"].get_app = AsyncMock(return_value=mock_app)
        mock_services["server"].get_server = AsyncMock(return_value=mock_server)
        mock_services["db"].get_installation = AsyncMock(return_value=None)
        mock_services["db"].create_installation = AsyncMock(
            return_value=MagicMock(id="inst-123")
        )
        mock_services["db"].update_installation = AsyncMock()

        # Setup agent responses
        mock_services["agent_manager"].send_command.side_effect = [
            {"success": True},  # preflight
            {"success": True},  # prepare volumes
            {"id": "sha256:abc"},  # pull
            {"container_id": "container-123"},  # run
            {"status": "running", "health": "none", "restart_count": 0},  # status
            {},  # update restart policy
            {
                "State": {"Status": "running"},
                "NetworkSettings": {"Networks": {}},
                "Mounts": [],
            },  # inspect
        ]

        await deployment_service.install_app("server-1", "app-1")

        # Should have called prepare_volumes
        calls = mock_services["agent_manager"].send_command.call_args_list
        methods = [c[1]["method"] for c in calls]
        assert "system.prepare_volumes" in methods

    @pytest.mark.asyncio
    async def test_skips_volume_prep_for_allowed_paths(
        self, deployment_service, mock_services, mock_app, mock_server
    ):
        """Should skip normalization for allowed paths."""
        # Setup volume with allowed path
        volume = MagicMock()
        volume.host_path = "/DATA/apps/myapp"
        volume.container_path = "/app"
        volume.readonly = False
        mock_app.docker.volumes = [volume]

        mock_services["marketplace"].get_app = AsyncMock(return_value=mock_app)
        mock_services["server"].get_server = AsyncMock(return_value=mock_server)
        mock_services["db"].get_installation = AsyncMock(return_value=None)
        mock_services["db"].create_installation = AsyncMock(
            return_value=MagicMock(id="inst-123")
        )
        mock_services["db"].update_installation = AsyncMock()

        # Agent responses
        mock_services["agent_manager"].send_command.side_effect = [
            {"success": True},  # preflight
            {"success": True},  # prepare volumes
            {"id": "sha256:abc"},  # pull
            {"container_id": "container-123"},  # run
            {"status": "running", "health": "none", "restart_count": 0},  # status
            {},  # update restart policy
            {
                "State": {"Status": "running"},
                "NetworkSettings": {"Networks": {}},
                "Mounts": [],
            },
        ]

        # Should complete without error
        await deployment_service.install_app("server-1", "app-1")


class TestWaitForContainer:
    """Tests for _wait_for_container helper method."""

    @pytest.mark.asyncio
    async def test_completes_when_running(self, deployment_service, mock_services):
        """Should complete when container is running."""
        mock_services["db"].update_installation = AsyncMock()
        mock_services["agent_manager"].send_command.return_value = {
            "status": "running",
            "health": "none",
            "restart_count": 0,
        }

        # Should not raise
        await deployment_service._wait_for_container(
            "server-1",
            "container-123",
            "my-container",
            "inst-123",
            "Test App",
            "app-1",
            "nginx:latest",
        )

        mock_services["db"].update_installation.assert_called()

    @pytest.mark.asyncio
    async def test_raises_on_restart_loop(self, deployment_service, mock_services):
        """Should raise when container has restarted."""
        from services.deployment.service import DeploymentError

        mock_services["db"].update_installation = AsyncMock()
        mock_services["agent_manager"].send_command.side_effect = [
            {
                "status": "running",
                "health": "none",
                "restart_count": 1,
                "logs": "Error!",
            },
            {},  # stop
            {},  # remove
        ]

        with pytest.raises(DeploymentError) as exc_info:
            await deployment_service._wait_for_container(
                "server-1",
                "container-123",
                "my-container",
                "inst-123",
                "Test App",
                "app-1",
                "nginx:latest",
            )

        assert "crashed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_raises_on_unhealthy(self, deployment_service, mock_services):
        """Should raise when container becomes unhealthy."""
        from services.deployment.service import DeploymentError

        mock_services["db"].update_installation = AsyncMock()
        mock_services["agent_manager"].send_command.side_effect = [
            {
                "status": "running",
                "health": "unhealthy",
                "restart_count": 0,
                "logs": "Health check failed",
            },
            {},  # stop
            {},  # remove
        ]

        with pytest.raises(DeploymentError) as exc_info:
            await deployment_service._wait_for_container(
                "server-1",
                "container-123",
                "my-container",
                "inst-123",
                "Test App",
                "app-1",
                "nginx:latest",
            )

        assert "unhealthy" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_raises_on_exited(self, deployment_service, mock_services):
        """Should raise when container exits."""
        from services.deployment.service import DeploymentError

        mock_services["db"].update_installation = AsyncMock()
        mock_services["agent_manager"].send_command.side_effect = [
            {
                "status": "exited",
                "health": "none",
                "restart_count": 0,
                "logs": "Exit 1",
            },
            {},  # stop
            {},  # remove
        ]

        with pytest.raises(DeploymentError) as exc_info:
            await deployment_service._wait_for_container(
                "server-1",
                "container-123",
                "my-container",
                "inst-123",
                "Test App",
                "app-1",
                "nginx:latest",
            )

        assert "exited" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_updates_progress_while_starting(
        self, deployment_service, mock_services
    ):
        """Should update progress while container is starting."""
        mock_services["db"].update_installation = AsyncMock()

        # First call: starting, second call: running
        mock_services["agent_manager"].send_command.side_effect = [
            {"status": "running", "health": "starting", "restart_count": 0},
            {"status": "running", "health": "healthy", "restart_count": 0},
        ]

        with patch("asyncio.sleep", new_callable=AsyncMock):
            await deployment_service._wait_for_container(
                "server-1",
                "container-123",
                "my-container",
                "inst-123",
                "Test App",
                "app-1",
                "nginx:latest",
            )

        # Should have updated progress
        assert mock_services["db"].update_installation.call_count >= 1


class TestDeploymentError:
    """Tests for DeploymentError exception."""

    def test_deployment_error_is_exception(self):
        """Should be a valid exception class."""
        from services.deployment.service import DeploymentError

        error = DeploymentError("Test error")
        assert isinstance(error, Exception)
        assert str(error) == "Test error"
