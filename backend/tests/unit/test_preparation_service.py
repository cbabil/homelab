"""Tests for preparation service."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from services.preparation_service import PreparationService
from models.preparation import PreparationStatus, PreparationStep


class TestPreparationService:
    """Tests for PreparationService."""

    @pytest.fixture
    def mock_ssh_service(self):
        """Create mock SSH service."""
        ssh = MagicMock()
        ssh.execute_command = AsyncMock()
        return ssh

    @pytest.fixture
    def mock_server_service(self):
        """Create mock server service."""
        svc = MagicMock()
        svc.get_server = AsyncMock()
        svc.get_credentials = AsyncMock()
        return svc

    @pytest.fixture
    def mock_db_service(self):
        """Create mock database service."""
        db = MagicMock()
        db.create_preparation = AsyncMock()
        db.update_preparation = AsyncMock()
        db.add_preparation_log = AsyncMock()
        db.get_preparation = AsyncMock()
        db.get_preparation_logs = AsyncMock(return_value=[])
        return db

    @pytest.fixture
    def prep_service(self, mock_ssh_service, mock_server_service, mock_db_service):
        """Create preparation service with mocks."""
        return PreparationService(
            ssh_service=mock_ssh_service,
            server_service=mock_server_service,
            db_service=mock_db_service
        )

    def test_detect_os_ubuntu(self, prep_service):
        """Should detect Ubuntu OS."""
        os_release = "Ubuntu 22.04.3 LTS"
        result = prep_service._detect_os_type(os_release)
        assert result == "ubuntu"

    def test_detect_os_debian(self, prep_service):
        """Should detect Debian OS."""
        os_release = "Debian GNU/Linux 12 (bookworm)"
        result = prep_service._detect_os_type(os_release)
        assert result == "debian"

    def test_detect_os_rocky(self, prep_service):
        """Should detect Rocky Linux."""
        os_release = "Rocky Linux 9.3 (Blue Onyx)"
        result = prep_service._detect_os_type(os_release)
        assert result == "rhel"

    def test_detect_os_fedora(self, prep_service):
        """Should detect Fedora."""
        os_release = "Fedora Linux 39"
        result = prep_service._detect_os_type(os_release)
        assert result == "fedora"

    def test_get_docker_install_commands_ubuntu(self, prep_service):
        """Should return Ubuntu Docker commands."""
        commands = prep_service._get_docker_commands("ubuntu")
        assert "apt-get" in commands["update_packages"]
        assert "docker-ce" in commands["install_docker"]

    def test_get_docker_install_commands_rhel(self, prep_service):
        """Should return RHEL Docker commands."""
        commands = prep_service._get_docker_commands("rhel")
        assert "dnf" in commands["update_packages"]
        assert "docker-ce" in commands["install_docker"]

    @pytest.mark.asyncio
    async def test_start_preparation_creates_record(self, prep_service, mock_db_service, mock_server_service):
        """Should create preparation record."""
        mock_server_service.get_server.return_value = MagicMock(id="server-123")
        mock_db_service.create_preparation.return_value = MagicMock(id="prep-123")

        result = await prep_service.start_preparation("server-123")

        assert result is not None
        mock_db_service.create_preparation.assert_called_once()
