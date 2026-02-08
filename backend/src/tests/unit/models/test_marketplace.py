"""
Unit tests for models/marketplace.py

Tests marketplace repository and application models.
"""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from models.marketplace import (
    AppEnvVar,
    AppPort,
    AppRating,
    AppRequirements,
    AppVolume,
    DockerConfig,
    MarketplaceApp,
    MarketplaceRepo,
    RepoStatus,
    RepoType,
)


class TestRepoType:
    """Tests for RepoType enum."""

    def test_repo_type_values(self):
        """Test all repo type enum values."""
        assert RepoType.OFFICIAL == "official"
        assert RepoType.COMMUNITY == "community"
        assert RepoType.PERSONAL == "personal"

    def test_repo_type_is_string_enum(self):
        """Test that repo type values are strings."""
        assert isinstance(RepoType.OFFICIAL.value, str)


class TestRepoStatus:
    """Tests for RepoStatus enum."""

    def test_repo_status_values(self):
        """Test all repo status enum values."""
        assert RepoStatus.ACTIVE == "active"
        assert RepoStatus.SYNCING == "syncing"
        assert RepoStatus.ERROR == "error"
        assert RepoStatus.DISABLED == "disabled"

    def test_repo_status_is_string_enum(self):
        """Test that repo status values are strings."""
        assert isinstance(RepoStatus.ACTIVE.value, str)


class TestMarketplaceRepo:
    """Tests for MarketplaceRepo model."""

    @pytest.fixture
    def sample_repo(self):
        """Create sample repo for tests."""
        now = datetime.now(UTC)
        return MarketplaceRepo(
            id="repo-123",
            name="Official Apps",
            url="https://github.com/tomo/apps",
            branch="main",
            repo_type=RepoType.OFFICIAL,
            enabled=True,
            status=RepoStatus.ACTIVE,
            app_count=10,
            created_at=now,
            updated_at=now,
        )

    def test_required_fields(self, sample_repo):
        """Test required fields."""
        assert sample_repo.id == "repo-123"
        assert sample_repo.name == "Official Apps"
        assert sample_repo.url == "https://github.com/tomo/apps"
        assert sample_repo.branch == "main"
        assert sample_repo.repo_type == RepoType.OFFICIAL
        assert sample_repo.enabled is True
        assert sample_repo.status == RepoStatus.ACTIVE
        assert sample_repo.app_count == 10

    def test_optional_fields_default(self, sample_repo):
        """Test optional fields default to None."""
        assert sample_repo.last_synced is None
        assert sample_repo.error_message is None

    def test_all_fields(self):
        """Test all fields populated."""
        now = datetime.now(UTC)
        repo = MarketplaceRepo(
            id="repo-456",
            name="Community Apps",
            url="https://github.com/community/apps",
            branch="develop",
            repo_type=RepoType.COMMUNITY,
            enabled=False,
            status=RepoStatus.ERROR,
            last_synced=now,
            app_count=5,
            error_message="Sync failed",
            created_at=now,
            updated_at=now,
        )
        assert repo.last_synced == now
        assert repo.error_message == "Sync failed"

    def test_camel_case_alias(self):
        """Test camelCase alias support."""
        now = datetime.now(UTC)
        repo = MarketplaceRepo(
            id="repo-123",
            name="Test",
            url="https://example.com",
            branch="main",
            repoType=RepoType.PERSONAL,
            enabled=True,
            status=RepoStatus.ACTIVE,
            appCount=0,
            createdAt=now,
            updatedAt=now,
        )
        assert repo.repo_type == RepoType.PERSONAL
        assert repo.app_count == 0

    def test_missing_required_fields(self):
        """Test validation error when required fields are missing."""
        with pytest.raises(ValidationError):
            MarketplaceRepo(id="repo-123")


class TestAppPort:
    """Tests for AppPort model."""

    def test_required_fields(self):
        """Test required fields."""
        port = AppPort(container=8080, host=80)
        assert port.container == 8080
        assert port.host == 80

    def test_default_protocol(self):
        """Test default protocol."""
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


class TestAppVolume:
    """Tests for AppVolume model."""

    def test_required_fields(self):
        """Test required fields."""
        vol = AppVolume(host_path="/data", container_path="/app/data")
        assert vol.host_path == "/data"
        assert vol.container_path == "/app/data"

    def test_default_readonly(self):
        """Test default readonly."""
        vol = AppVolume(host_path="/data", container_path="/app/data")
        assert vol.readonly is False

    def test_readonly_true(self):
        """Test readonly true."""
        vol = AppVolume(
            host_path="/config", container_path="/app/config", readonly=True
        )
        assert vol.readonly is True

    def test_camel_case_alias(self):
        """Test camelCase alias support."""
        vol = AppVolume(hostPath="/data", containerPath="/app/data")
        assert vol.host_path == "/data"
        assert vol.container_path == "/app/data"


class TestAppEnvVar:
    """Tests for AppEnvVar model."""

    def test_required_fields(self):
        """Test required fields."""
        env = AppEnvVar(name="DATABASE_URL", required=True)
        assert env.name == "DATABASE_URL"
        assert env.required is True

    def test_default_values(self):
        """Test default values."""
        env = AppEnvVar(name="API_KEY", required=False)
        assert env.description is None
        assert env.default is None

    def test_all_fields(self):
        """Test all fields."""
        env = AppEnvVar(
            name="DB_HOST",
            description="Database hostname",
            required=True,
            default="localhost",
        )
        assert env.description == "Database hostname"
        assert env.default == "localhost"


class TestDockerConfig:
    """Tests for DockerConfig model."""

    @pytest.fixture
    def sample_docker_config(self):
        """Create sample docker config."""
        return DockerConfig(
            image="nginx:latest",
            ports=[AppPort(container=80, host=8080)],
            volumes=[AppVolume(host_path="/data", container_path="/app")],
            environment=[AppEnvVar(name="ENV", required=False)],
            restart_policy="unless-stopped",
            privileged=False,
            capabilities=[],
        )

    def test_required_fields(self, sample_docker_config):
        """Test required fields."""
        assert sample_docker_config.image == "nginx:latest"
        assert len(sample_docker_config.ports) == 1
        assert len(sample_docker_config.volumes) == 1
        assert len(sample_docker_config.environment) == 1
        assert sample_docker_config.restart_policy == "unless-stopped"
        assert sample_docker_config.privileged is False
        assert sample_docker_config.capabilities == []

    def test_optional_network_mode(self, sample_docker_config):
        """Test optional network mode defaults to None."""
        assert sample_docker_config.network_mode is None

    def test_all_fields(self):
        """Test all fields."""
        config = DockerConfig(
            image="app:1.0",
            ports=[],
            volumes=[],
            environment=[],
            restart_policy="always",
            network_mode="host",
            privileged=True,
            capabilities=["NET_ADMIN"],
        )
        assert config.network_mode == "host"
        assert config.privileged is True
        assert config.capabilities == ["NET_ADMIN"]

    def test_camel_case_alias(self):
        """Test camelCase alias support."""
        config = DockerConfig(
            image="app:1.0",
            ports=[],
            volumes=[],
            environment=[],
            restartPolicy="no",
            networkMode="bridge",
            privileged=False,
            capabilities=[],
        )
        assert config.restart_policy == "no"
        assert config.network_mode == "bridge"


class TestAppRequirements:
    """Tests for AppRequirements model."""

    def test_required_fields(self):
        """Test required fields."""
        req = AppRequirements(architectures=["amd64", "arm64"])
        assert req.architectures == ["amd64", "arm64"]

    def test_default_values(self):
        """Test default values."""
        req = AppRequirements(architectures=["amd64"])
        assert req.min_ram is None
        assert req.min_storage is None

    def test_all_fields(self):
        """Test all fields."""
        req = AppRequirements(
            min_ram=512,
            min_storage=1024,
            architectures=["amd64"],
        )
        assert req.min_ram == 512
        assert req.min_storage == 1024

    def test_camel_case_alias(self):
        """Test camelCase alias support."""
        req = AppRequirements(
            minRam=256,
            minStorage=512,
            architectures=["arm64"],
        )
        assert req.min_ram == 256
        assert req.min_storage == 512


class TestMarketplaceApp:
    """Tests for MarketplaceApp model."""

    @pytest.fixture
    def sample_app(self):
        """Create sample marketplace app."""
        now = datetime.now(UTC)
        return MarketplaceApp(
            id="nginx",
            name="Nginx",
            description="Web server",
            version="1.25.0",
            category="networking",
            tags=["web", "server"],
            author="Nginx Inc",
            license="BSD",
            repo_id="official",
            docker=DockerConfig(
                image="nginx:latest",
                ports=[AppPort(container=80, host=8080)],
                volumes=[],
                environment=[],
                restart_policy="unless-stopped",
                privileged=False,
                capabilities=[],
            ),
            requirements=AppRequirements(architectures=["amd64", "arm64"]),
            created_at=now,
            updated_at=now,
        )

    def test_required_fields(self, sample_app):
        """Test required fields."""
        assert sample_app.id == "nginx"
        assert sample_app.name == "Nginx"
        assert sample_app.description == "Web server"
        assert sample_app.version == "1.25.0"
        assert sample_app.category == "networking"
        assert sample_app.tags == ["web", "server"]
        assert sample_app.author == "Nginx Inc"
        assert sample_app.license == "BSD"
        assert sample_app.repo_id == "official"

    def test_default_values(self, sample_app):
        """Test default values."""
        assert sample_app.long_description is None
        assert sample_app.icon is None
        assert sample_app.maintainers == []
        assert sample_app.repository is None
        assert sample_app.documentation is None
        assert sample_app.install_count == 0
        assert sample_app.avg_rating == 0.0
        assert sample_app.rating_count == 0
        assert sample_app.featured is False

    def test_all_fields(self):
        """Test all fields."""
        now = datetime.now(UTC)
        app = MarketplaceApp(
            id="plex",
            name="Plex",
            description="Media server",
            long_description="Full media server for streaming",
            version="1.0.0",
            category="media",
            tags=["media", "streaming"],
            icon="https://example.com/plex.png",
            author="Plex Inc",
            license="Proprietary",
            maintainers=["maintainer@example.com"],
            repository="https://github.com/plex",
            documentation="https://docs.plex.tv",
            repo_id="official",
            docker=DockerConfig(
                image="plexinc/pms-docker",
                ports=[AppPort(container=32400, host=32400)],
                volumes=[],
                environment=[],
                restart_policy="always",
                privileged=False,
                capabilities=[],
            ),
            requirements=AppRequirements(
                min_ram=2048,
                min_storage=10240,
                architectures=["amd64"],
            ),
            install_count=1000,
            avg_rating=4.5,
            rating_count=200,
            featured=True,
            created_at=now,
            updated_at=now,
        )
        assert app.long_description == "Full media server for streaming"
        assert app.icon == "https://example.com/plex.png"
        assert app.maintainers == ["maintainer@example.com"]
        assert app.install_count == 1000
        assert app.avg_rating == 4.5
        assert app.featured is True


class TestAppRating:
    """Tests for AppRating model."""

    def test_required_fields(self):
        """Test required fields."""
        rating = AppRating(
            id="rating-123",
            app_id="nginx",
            user_id="user-456",
            rating=5,
            created_at="2024-01-15T10:00:00",
            updated_at="2024-01-15T10:00:00",
        )
        assert rating.id == "rating-123"
        assert rating.app_id == "nginx"
        assert rating.user_id == "user-456"
        assert rating.rating == 5

    def test_rating_min_validation(self):
        """Test rating minimum value validation."""
        with pytest.raises(ValidationError) as exc_info:
            AppRating(
                id="rating-123",
                app_id="nginx",
                user_id="user-456",
                rating=0,  # Below minimum
                created_at="2024-01-15T10:00:00",
                updated_at="2024-01-15T10:00:00",
            )
        assert "rating" in str(exc_info.value)

    def test_rating_max_validation(self):
        """Test rating maximum value validation."""
        with pytest.raises(ValidationError) as exc_info:
            AppRating(
                id="rating-123",
                app_id="nginx",
                user_id="user-456",
                rating=6,  # Above maximum
                created_at="2024-01-15T10:00:00",
                updated_at="2024-01-15T10:00:00",
            )
        assert "rating" in str(exc_info.value)

    def test_rating_boundary_values(self):
        """Test rating boundary values."""
        rating_min = AppRating(
            id="r1",
            app_id="app",
            user_id="user",
            rating=1,
            created_at="2024-01-15T10:00:00",
            updated_at="2024-01-15T10:00:00",
        )
        assert rating_min.rating == 1

        rating_max = AppRating(
            id="r2",
            app_id="app",
            user_id="user",
            rating=5,
            created_at="2024-01-15T10:00:00",
            updated_at="2024-01-15T10:00:00",
        )
        assert rating_max.rating == 5

    def test_camel_case_alias(self):
        """Test camelCase alias support."""
        rating = AppRating(
            id="rating-123",
            appId="nginx",
            userId="user-456",
            rating=4,
            createdAt="2024-01-15T10:00:00",
            updatedAt="2024-01-15T10:00:00",
        )
        assert rating.app_id == "nginx"
        assert rating.user_id == "user-456"
