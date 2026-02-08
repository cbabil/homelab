"""
Unit tests for models/app_catalog.py

Tests application catalog models including categories, installation status,
ports, volumes, environment variables, and app definitions.
"""

import pytest
from pydantic import ValidationError

from models.app_catalog import (
    AppCategory,
    AppDefinition,
    AppEnvVar,
    AppPort,
    AppVolume,
    InstallationStatus,
    InstalledApp,
)


class TestAppCategory:
    """Tests for AppCategory enum."""

    def test_category_values(self):
        """Test all category enum values exist."""
        assert AppCategory.STORAGE == "storage"
        assert AppCategory.MEDIA == "media"
        assert AppCategory.NETWORKING == "networking"
        assert AppCategory.MONITORING == "monitoring"
        assert AppCategory.UTILITY == "utility"
        assert AppCategory.DATABASE == "database"
        assert AppCategory.DEVELOPMENT == "development"

    def test_category_is_string_enum(self):
        """Test that category values are strings."""
        assert isinstance(AppCategory.STORAGE.value, str)


class TestInstallationStatus:
    """Tests for InstallationStatus enum."""

    def test_status_values(self):
        """Test all status enum values exist."""
        assert InstallationStatus.PENDING == "pending"
        assert InstallationStatus.PULLING == "pulling"
        assert InstallationStatus.CREATING == "creating"
        assert InstallationStatus.STARTING == "starting"
        assert InstallationStatus.RUNNING == "running"
        assert InstallationStatus.STOPPED == "stopped"
        assert InstallationStatus.ERROR == "error"
        assert InstallationStatus.REMOVING == "removing"

    def test_status_is_string_enum(self):
        """Test that status values are strings."""
        assert isinstance(InstallationStatus.PENDING.value, str)


class TestAppPort:
    """Tests for AppPort model."""

    def test_required_fields(self):
        """Test required fields."""
        port = AppPort(container=8080, host=80)
        assert port.container == 8080
        assert port.host == 80

    def test_default_protocol(self):
        """Test default protocol is tcp."""
        port = AppPort(container=8080, host=80)
        assert port.protocol == "tcp"

    def test_custom_protocol(self):
        """Test custom protocol."""
        port = AppPort(container=53, host=53, protocol="udp")
        assert port.protocol == "udp"

    def test_missing_required_fields(self):
        """Test validation error when required fields are missing."""
        with pytest.raises(ValidationError):
            AppPort(container=8080)
        with pytest.raises(ValidationError):
            AppPort(host=80)


class TestAppVolume:
    """Tests for AppVolume model."""

    def test_required_fields(self):
        """Test required fields."""
        volume = AppVolume(
            host_path="/data/app",
            container_path="/app/data",
        )
        assert volume.host_path == "/data/app"
        assert volume.container_path == "/app/data"

    def test_default_readonly(self):
        """Test default readonly is False."""
        volume = AppVolume(
            host_path="/data/app",
            container_path="/app/data",
        )
        assert volume.readonly is False

    def test_readonly_true(self):
        """Test readonly can be set to True."""
        volume = AppVolume(
            host_path="/data/config",
            container_path="/app/config",
            readonly=True,
        )
        assert volume.readonly is True

    def test_missing_required_fields(self):
        """Test validation error when required fields are missing."""
        with pytest.raises(ValidationError):
            AppVolume(host_path="/data/app")
        with pytest.raises(ValidationError):
            AppVolume(container_path="/app/data")


class TestAppEnvVar:
    """Tests for AppEnvVar model."""

    def test_required_fields(self):
        """Test required name field."""
        env = AppEnvVar(name="DATABASE_URL")
        assert env.name == "DATABASE_URL"

    def test_default_values(self):
        """Test default values."""
        env = AppEnvVar(name="API_KEY")
        assert env.description is None
        assert env.required is False
        assert env.default is None

    def test_all_fields(self):
        """Test all fields populated."""
        env = AppEnvVar(
            name="DATABASE_URL",
            description="PostgreSQL connection string",
            required=True,
            default="postgres://localhost:5432/app",
        )
        assert env.name == "DATABASE_URL"
        assert env.description == "PostgreSQL connection string"
        assert env.required is True
        assert env.default == "postgres://localhost:5432/app"

    def test_missing_name(self):
        """Test validation error when name is missing."""
        with pytest.raises(ValidationError):
            AppEnvVar()


class TestAppDefinition:
    """Tests for AppDefinition model."""

    def test_required_fields(self):
        """Test required fields."""
        app = AppDefinition(
            id="nginx",
            name="Nginx",
            description="Web server",
            category=AppCategory.NETWORKING,
            image="nginx:latest",
        )
        assert app.id == "nginx"
        assert app.name == "Nginx"
        assert app.description == "Web server"
        assert app.category == AppCategory.NETWORKING
        assert app.image == "nginx:latest"

    def test_default_values(self):
        """Test default values for optional fields."""
        app = AppDefinition(
            id="nginx",
            name="Nginx",
            description="Web server",
            category=AppCategory.NETWORKING,
            image="nginx:latest",
        )
        assert app.ports == []
        assert app.volumes == []
        assert app.env_vars == []
        assert app.restart_policy == "unless-stopped"
        assert app.network_mode is None
        assert app.privileged is False
        assert app.capabilities == []

    def test_all_fields(self):
        """Test all fields populated."""
        app = AppDefinition(
            id="plex",
            name="Plex Media Server",
            description="Media streaming",
            category=AppCategory.MEDIA,
            image="plexinc/pms-docker:latest",
            ports=[AppPort(container=32400, host=32400)],
            volumes=[AppVolume(host_path="/data/media", container_path="/media")],
            env_vars=[AppEnvVar(name="TZ", default="UTC")],
            restart_policy="always",
            network_mode="host",
            privileged=True,
            capabilities=["NET_ADMIN", "SYS_ADMIN"],
        )
        assert app.id == "plex"
        assert len(app.ports) == 1
        assert len(app.volumes) == 1
        assert len(app.env_vars) == 1
        assert app.restart_policy == "always"
        assert app.network_mode == "host"
        assert app.privileged is True
        assert app.capabilities == ["NET_ADMIN", "SYS_ADMIN"]

    def test_missing_required_fields(self):
        """Test validation error when required fields are missing."""
        with pytest.raises(ValidationError):
            AppDefinition(id="nginx")


class TestInstalledApp:
    """Tests for InstalledApp model."""

    def test_required_fields(self):
        """Test required fields."""
        app = InstalledApp(
            id="inst-123",
            server_id="server-456",
            app_id="nginx",
        )
        assert app.id == "inst-123"
        assert app.server_id == "server-456"
        assert app.app_id == "nginx"

    def test_default_values(self):
        """Test default values."""
        app = InstalledApp(
            id="inst-123",
            server_id="server-456",
            app_id="nginx",
        )
        assert app.container_id is None
        assert app.container_name is None
        assert app.status == InstallationStatus.PENDING
        assert app.config == {}
        assert app.installed_at is None
        assert app.started_at is None
        assert app.error_message is None
        assert app.step_durations is None
        assert app.step_started_at is None
        assert app.networks is None
        assert app.named_volumes is None
        assert app.bind_mounts is None

    def test_all_fields(self):
        """Test all fields populated."""
        app = InstalledApp(
            id="inst-123",
            server_id="server-456",
            app_id="nginx",
            container_id="abc123",
            container_name="nginx-inst-123",
            status=InstallationStatus.RUNNING,
            config={"port": 8080},
            installed_at="2024-01-15T10:00:00",
            started_at="2024-01-15T10:01:00",
            error_message=None,
            step_durations={"pulling": 30, "creating": 5, "starting": 2},
            step_started_at="2024-01-15T10:00:35",
            networks=["bridge", "app-network"],
            named_volumes=[{"name": "nginx-data", "destination": "/data"}],
            bind_mounts=[{"source": "/host/config", "destination": "/config"}],
        )
        assert app.container_id == "abc123"
        assert app.container_name == "nginx-inst-123"
        assert app.status == InstallationStatus.RUNNING
        assert app.config == {"port": 8080}
        assert app.installed_at == "2024-01-15T10:00:00"
        assert app.started_at == "2024-01-15T10:01:00"
        assert app.step_durations["pulling"] == 30
        assert len(app.networks) == 2
        assert len(app.named_volumes) == 1
        assert len(app.bind_mounts) == 1

    def test_error_status(self):
        """Test app with error status."""
        app = InstalledApp(
            id="inst-123",
            server_id="server-456",
            app_id="nginx",
            status=InstallationStatus.ERROR,
            error_message="Container failed to start: port already in use",
        )
        assert app.status == InstallationStatus.ERROR
        assert "port already in use" in app.error_message

    def test_missing_required_fields(self):
        """Test validation error when required fields are missing."""
        with pytest.raises(ValidationError):
            InstalledApp(id="inst-123")
