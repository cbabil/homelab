"""
Deployment Service Status Sync Unit Tests

Tests for refresh_installation_status method and Docker status edge cases.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestRefreshInstallationStatus:
    """Tests for refresh_installation_status method."""

    @pytest.fixture
    def deployment_service(
        self,
        mock_ssh_service,
        mock_server_service,
        mock_marketplace_service,
        mock_db_service,
        mock_agent_manager,
        mock_agent_service,
    ):
        """Create deployment service with mocked dependencies."""
        from services.deployment import DeploymentService

        return DeploymentService(
            ssh_service=mock_ssh_service,
            server_service=mock_server_service,
            marketplace_service=mock_marketplace_service,
            db_service=mock_db_service,
            activity_service=None,
            agent_manager=mock_agent_manager,
            agent_service=mock_agent_service,
        )

    @pytest.mark.asyncio
    async def test_refresh_status_docker_created(
        self, deployment_service, mock_db_service
    ):
        """Test refresh status when Docker status is 'created' (line 1022-1023)."""
        mock_installation = MagicMock()
        mock_installation.container_name = "test-container"
        mock_installation.server_id = "server-1"
        mock_db_service.get_installation_by_id = AsyncMock(
            return_value=mock_installation
        )

        with patch.object(
            deployment_service, "_agent_inspect_container", new_callable=AsyncMock
        ) as mock_inspect:
            mock_inspect.return_value = {
                "success": True,
                "data": {
                    "State": {"Status": "created"},
                    "NetworkSettings": {"Networks": {}},
                    "Mounts": [],
                },
            }

            result = await deployment_service.refresh_installation_status("inst-1")

        assert result["status"] == "stopped"

    @pytest.mark.asyncio
    async def test_refresh_status_docker_paused(
        self, deployment_service, mock_db_service
    ):
        """Test refresh status when Docker status is 'paused' (line 1022-1023)."""
        mock_installation = MagicMock()
        mock_installation.container_name = "test-container"
        mock_installation.server_id = "server-1"
        mock_db_service.get_installation_by_id = AsyncMock(
            return_value=mock_installation
        )

        with patch.object(
            deployment_service, "_agent_inspect_container", new_callable=AsyncMock
        ) as mock_inspect:
            mock_inspect.return_value = {
                "success": True,
                "data": {
                    "State": {"Status": "paused"},
                    "NetworkSettings": {"Networks": {}},
                    "Mounts": [],
                },
            }

            result = await deployment_service.refresh_installation_status("inst-1")

        assert result["status"] == "stopped"

    @pytest.mark.asyncio
    async def test_refresh_status_docker_unknown_status(
        self, deployment_service, mock_db_service
    ):
        """Test refresh status when Docker has unknown status (line 1024-1025)."""
        mock_installation = MagicMock()
        mock_installation.container_name = "test-container"
        mock_installation.server_id = "server-1"
        mock_db_service.get_installation_by_id = AsyncMock(
            return_value=mock_installation
        )

        with patch.object(
            deployment_service, "_agent_inspect_container", new_callable=AsyncMock
        ) as mock_inspect:
            mock_inspect.return_value = {
                "success": True,
                "data": {
                    "State": {"Status": "dead"},
                    "NetworkSettings": {"Networks": {}},
                    "Mounts": [],
                },
            }

            result = await deployment_service.refresh_installation_status("inst-1")

        # Unknown status is passed through
        assert result["status"] == "dead"

    @pytest.mark.asyncio
    async def test_refresh_status_docker_empty_status(
        self, deployment_service, mock_db_service
    ):
        """Test refresh status when Docker status is empty (line 1025 fallback)."""
        mock_installation = MagicMock()
        mock_installation.container_name = "test-container"
        mock_installation.server_id = "server-1"
        mock_db_service.get_installation_by_id = AsyncMock(
            return_value=mock_installation
        )

        with patch.object(
            deployment_service, "_agent_inspect_container", new_callable=AsyncMock
        ) as mock_inspect:
            mock_inspect.return_value = {
                "success": True,
                "data": {
                    "State": {"Status": ""},
                    "NetworkSettings": {"Networks": {}},
                    "Mounts": [],
                },
            }

            result = await deployment_service.refresh_installation_status("inst-1")

        # Empty status falls back to "stopped"
        assert result["status"] == "stopped"

    @pytest.mark.asyncio
    async def test_refresh_status_no_container_name(
        self, deployment_service, mock_db_service
    ):
        """Test refresh status when installation has no container name (line 989)."""
        from models.app_catalog import InstallationStatus

        mock_installation = MagicMock()
        mock_installation.container_name = None
        mock_installation.status = InstallationStatus.PENDING
        mock_db_service.get_installation_by_id = AsyncMock(
            return_value=mock_installation
        )

        result = await deployment_service.refresh_installation_status("inst-1")

        assert result["status"] == "pending"

    @pytest.mark.asyncio
    async def test_refresh_status_not_found(self, deployment_service, mock_db_service):
        """Test refresh status when installation not found."""
        mock_db_service.get_installation_by_id = AsyncMock(return_value=None)

        result = await deployment_service.refresh_installation_status("inst-1")

        assert result is None

    @pytest.mark.asyncio
    async def test_refresh_status_docker_running(
        self, deployment_service, mock_db_service
    ):
        """Test refresh status when Docker status is 'running'."""
        mock_installation = MagicMock()
        mock_installation.container_name = "test-container"
        mock_installation.server_id = "server-1"
        mock_db_service.get_installation_by_id = AsyncMock(
            return_value=mock_installation
        )

        with patch.object(
            deployment_service, "_agent_inspect_container", new_callable=AsyncMock
        ) as mock_inspect:
            mock_inspect.return_value = {
                "success": True,
                "data": {
                    "State": {"Status": "running"},
                    "NetworkSettings": {"Networks": {"bridge": {}}},
                    "Mounts": [
                        {
                            "Type": "volume",
                            "Name": "vol1",
                            "Destination": "/data",
                            "Mode": "rw",
                        },
                        {
                            "Type": "bind",
                            "Source": "/host",
                            "Destination": "/container",
                            "Mode": "ro",
                        },
                    ],
                },
            }

            result = await deployment_service.refresh_installation_status("inst-1")

        assert result["status"] == "running"
        assert "bridge" in result["networks"]

    @pytest.mark.asyncio
    async def test_refresh_status_docker_exited(
        self, deployment_service, mock_db_service
    ):
        """Test refresh status when Docker status is 'exited'."""
        mock_installation = MagicMock()
        mock_installation.container_name = "test-container"
        mock_installation.server_id = "server-1"
        mock_db_service.get_installation_by_id = AsyncMock(
            return_value=mock_installation
        )

        with patch.object(
            deployment_service, "_agent_inspect_container", new_callable=AsyncMock
        ) as mock_inspect:
            mock_inspect.return_value = {
                "success": True,
                "data": {
                    "State": {"Status": "exited"},
                    "NetworkSettings": {"Networks": {}},
                    "Mounts": [],
                },
            }

            result = await deployment_service.refresh_installation_status("inst-1")

        assert result["status"] == "stopped"

    @pytest.mark.asyncio
    async def test_refresh_status_docker_restarting(
        self, deployment_service, mock_db_service
    ):
        """Test refresh status when Docker status is 'restarting'."""
        mock_installation = MagicMock()
        mock_installation.container_name = "test-container"
        mock_installation.server_id = "server-1"
        mock_db_service.get_installation_by_id = AsyncMock(
            return_value=mock_installation
        )

        with patch.object(
            deployment_service, "_agent_inspect_container", new_callable=AsyncMock
        ) as mock_inspect:
            mock_inspect.return_value = {
                "success": True,
                "data": {
                    "State": {"Status": "restarting"},
                    "NetworkSettings": {"Networks": {}},
                    "Mounts": [],
                },
            }

            result = await deployment_service.refresh_installation_status("inst-1")

        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_refresh_status_inspect_failed(
        self, deployment_service, mock_db_service
    ):
        """Test refresh status when container inspect fails."""
        mock_installation = MagicMock()
        mock_installation.container_name = "test-container"
        mock_installation.server_id = "server-1"
        mock_db_service.get_installation_by_id = AsyncMock(
            return_value=mock_installation
        )

        with patch.object(
            deployment_service, "_agent_inspect_container", new_callable=AsyncMock
        ) as mock_inspect:
            mock_inspect.return_value = {
                "success": False,
                "error": "Container not found",
            }

            result = await deployment_service.refresh_installation_status("inst-1")

        assert result["status"] == "stopped"
        mock_db_service.update_installation.assert_called()
