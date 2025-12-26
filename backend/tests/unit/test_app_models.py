"""Tests for app catalog models."""
import pytest
from models.app_catalog import (
    AppDefinition,
    AppPort,
    AppVolume,
    AppEnvVar,
    AppCategory,
    InstallationStatus,
    InstalledApp
)


class TestAppModels:
    """Tests for app catalog data models."""

    def test_app_category_enum(self):
        """Should have correct category values."""
        assert AppCategory.STORAGE.value == "storage"
        assert AppCategory.MEDIA.value == "media"
        assert AppCategory.NETWORKING.value == "networking"
        assert AppCategory.MONITORING.value == "monitoring"
        assert AppCategory.UTILITY.value == "utility"

    def test_installation_status_enum(self):
        """Should have correct status values."""
        assert InstallationStatus.PENDING.value == "pending"
        assert InstallationStatus.PULLING.value == "pulling"
        assert InstallationStatus.RUNNING.value == "running"
        assert InstallationStatus.STOPPED.value == "stopped"
        assert InstallationStatus.ERROR.value == "error"

    def test_app_port_model(self):
        """Should create valid port mapping."""
        port = AppPort(container=80, host=8080, protocol="tcp")
        assert port.container == 80
        assert port.host == 8080
        assert port.protocol == "tcp"

    def test_app_volume_model(self):
        """Should create valid volume mapping."""
        volume = AppVolume(
            host_path="/var/data",
            container_path="/app/data",
            readonly=False
        )
        assert volume.host_path == "/var/data"
        assert volume.container_path == "/app/data"

    def test_app_env_var_model(self):
        """Should create valid env var."""
        env = AppEnvVar(name="DB_HOST", required=True, default=None)
        assert env.name == "DB_HOST"
        assert env.required is True

    def test_app_definition_model(self):
        """Should create valid app definition."""
        app = AppDefinition(
            id="nextcloud",
            name="Nextcloud",
            description="Personal cloud storage",
            category=AppCategory.STORAGE,
            image="nextcloud:latest",
            ports=[AppPort(container=80, host=8080)],
            volumes=[],
            env_vars=[]
        )
        assert app.id == "nextcloud"
        assert app.category == AppCategory.STORAGE

    def test_installed_app_model(self):
        """Should create valid installed app."""
        installed = InstalledApp(
            id="inst-123",
            server_id="server-456",
            app_id="nextcloud",
            container_id="abc123",
            status=InstallationStatus.RUNNING,
            config={"ports": {"80": 8080}},
            installed_at="2025-01-01T00:00:00Z"
        )
        assert installed.status == InstallationStatus.RUNNING
        assert installed.container_id == "abc123"
