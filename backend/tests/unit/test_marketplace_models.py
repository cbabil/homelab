"""Unit tests for marketplace models."""
import pytest
from datetime import datetime
from pydantic import ValidationError

from models.marketplace import (
    MarketplaceRepo, RepoType, RepoStatus,
    AppPort, AppVolume, AppEnvVar, DockerConfig,
    AppRequirements, MarketplaceApp, AppRating
)


def test_marketplace_repo_model():
    """Test MarketplaceRepo model creation and validation."""
    # Test valid repo creation
    repo = MarketplaceRepo(
        id="test-repo-1",
        name="Test Repository",
        url="https://github.com/test/repo",
        branch="main",
        repo_type=RepoType.OFFICIAL,
        enabled=True,
        status=RepoStatus.ACTIVE,
        last_synced=datetime.now(),
        app_count=10,
        error_message=None,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    assert repo.id == "test-repo-1"
    assert repo.name == "Test Repository"
    assert repo.url == "https://github.com/test/repo"
    assert repo.branch == "main"
    assert repo.repo_type == RepoType.OFFICIAL
    assert repo.enabled is True
    assert repo.status == RepoStatus.ACTIVE
    assert repo.app_count == 10
    assert repo.error_message is None


def test_marketplace_repo_type_enum():
    """Test RepoType enum values."""
    assert RepoType.OFFICIAL == "official"
    assert RepoType.COMMUNITY == "community"
    assert RepoType.PERSONAL == "personal"


def test_marketplace_repo_status_enum():
    """Test RepoStatus enum values."""
    assert RepoStatus.ACTIVE == "active"
    assert RepoStatus.SYNCING == "syncing"
    assert RepoStatus.ERROR == "error"
    assert RepoStatus.DISABLED == "disabled"


def test_marketplace_repo_camelcase_aliases():
    """Test that camelCase aliases work correctly."""
    repo_data = {
        "id": "test-repo-2",
        "name": "Test Repo",
        "url": "https://github.com/test/repo2",
        "branch": "main",
        "repoType": "community",  # camelCase
        "enabled": True,
        "status": "active",
        "lastSynced": datetime.now().isoformat(),  # camelCase
        "appCount": 5,  # camelCase
        "errorMessage": None,  # camelCase
        "createdAt": datetime.now().isoformat(),  # camelCase
        "updatedAt": datetime.now().isoformat()  # camelCase
    }

    repo = MarketplaceRepo(**repo_data)
    assert repo.repo_type == RepoType.COMMUNITY
    assert repo.app_count == 5

    # Test serialization to camelCase
    serialized = repo.model_dump(by_alias=True)
    assert "repoType" in serialized
    assert "appCount" in serialized
    assert "lastSynced" in serialized
    assert "errorMessage" in serialized
    assert "createdAt" in serialized
    assert "updatedAt" in serialized


def test_marketplace_repo_optional_fields():
    """Test that optional fields work correctly."""
    repo = MarketplaceRepo(
        id="test-repo-3",
        name="Minimal Repo",
        url="https://github.com/test/minimal",
        branch="develop",
        repo_type=RepoType.PERSONAL,
        enabled=False,
        status=RepoStatus.DISABLED,
        last_synced=None,  # Optional
        app_count=0,
        error_message=None,  # Optional
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    assert repo.last_synced is None
    assert repo.error_message is None


def test_marketplace_repo_with_error():
    """Test repo with error status and message."""
    error_time = datetime.now()
    repo = MarketplaceRepo(
        id="test-repo-4",
        name="Error Repo",
        url="https://github.com/test/error",
        branch="main",
        repo_type=RepoType.COMMUNITY,
        enabled=True,
        status=RepoStatus.ERROR,
        last_synced=error_time,
        app_count=0,
        error_message="Failed to clone repository",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    assert repo.status == RepoStatus.ERROR
    assert repo.error_message == "Failed to clone repository"


def test_marketplace_repo_validation():
    """Test that validation works for required fields."""
    with pytest.raises(ValidationError):
        MarketplaceRepo(
            # Missing required fields
            name="Incomplete Repo"
        )


# Tests for new MarketplaceApp and related models

def test_app_port_model():
    """Test AppPort model creation and defaults."""
    port = AppPort(container=8080, host=8080)
    assert port.container == 8080
    assert port.host == 8080
    assert port.protocol == "tcp"  # default

    port_udp = AppPort(container=53, host=53, protocol="udp")
    assert port_udp.protocol == "udp"


def test_app_volume_model():
    """Test AppVolume model creation and defaults."""
    volume = AppVolume(host_path="/data", container_path="/app/data")
    assert volume.host_path == "/data"
    assert volume.container_path == "/app/data"
    assert volume.readonly is False  # default

    volume_ro = AppVolume(host_path="/config", container_path="/etc/config", readonly=True)
    assert volume_ro.readonly is True


def test_app_env_var_model():
    """Test AppEnvVar model creation."""
    env = AppEnvVar(
        name="DATABASE_URL",
        description="Database connection string",
        required=True,
        default=None
    )
    assert env.name == "DATABASE_URL"
    assert env.description == "Database connection string"
    assert env.required is True
    assert env.default is None

    env_with_default = AppEnvVar(
        name="LOG_LEVEL",
        description="Logging level",
        required=False,
        default="INFO"
    )
    assert env_with_default.default == "INFO"


def test_docker_config_model():
    """Test DockerConfig model with nested models."""
    docker_config = DockerConfig(
        image="nginx:latest",
        ports=[
            AppPort(container=80, host=8080),
            AppPort(container=443, host=8443)
        ],
        volumes=[
            AppVolume(host_path="/data", container_path="/usr/share/nginx/html")
        ],
        environment=[
            AppEnvVar(name="NGINX_HOST", description="Host name", required=False, default="localhost")
        ],
        restart_policy="unless-stopped",
        network_mode="bridge",
        privileged=False,
        capabilities=["NET_ADMIN"]
    )

    assert docker_config.image == "nginx:latest"
    assert len(docker_config.ports) == 2
    assert docker_config.ports[0].container == 80
    assert len(docker_config.volumes) == 1
    assert len(docker_config.environment) == 1
    assert docker_config.restart_policy == "unless-stopped"
    assert docker_config.network_mode == "bridge"
    assert docker_config.privileged is False
    assert "NET_ADMIN" in docker_config.capabilities


def test_app_requirements_model():
    """Test AppRequirements model."""
    requirements = AppRequirements(
        min_ram=512,
        min_storage=1024,
        architectures=["amd64", "arm64"]
    )

    assert requirements.min_ram == 512
    assert requirements.min_storage == 1024
    assert len(requirements.architectures) == 2
    assert "amd64" in requirements.architectures

    # Test optional fields
    minimal_req = AppRequirements(
        min_ram=None,
        min_storage=None,
        architectures=["amd64"]
    )
    assert minimal_req.min_ram is None
    assert minimal_req.min_storage is None


def test_marketplace_app_model():
    """Test MarketplaceApp model creation with all fields."""
    now = datetime.now()

    app = MarketplaceApp(
        id="test-app-1",
        name="Test Application",
        description="A test application",
        long_description="This is a longer description of the test application",
        version="1.0.0",
        category="utilities",
        tags=["test", "demo"],
        icon="https://example.com/icon.png",
        author="Test Author",
        license="MIT",
        repository="https://github.com/test/app",
        documentation="https://docs.example.com",
        repo_id="test-repo-1",
        docker=DockerConfig(
            image="test/app:latest",
            ports=[AppPort(container=3000, host=3000)],
            volumes=[],
            environment=[],
            restart_policy="always",
            network_mode=None,
            privileged=False,
            capabilities=[]
        ),
        requirements=AppRequirements(
            min_ram=256,
            min_storage=512,
            architectures=["amd64"]
        ),
        install_count=100,
        avg_rating=4.5,
        rating_count=20,
        featured=True,
        created_at=now,
        updated_at=now
    )

    assert app.id == "test-app-1"
    assert app.name == "Test Application"
    assert app.version == "1.0.0"
    assert app.category == "utilities"
    assert len(app.tags) == 2
    assert app.repo_id == "test-repo-1"
    assert app.docker.image == "test/app:latest"
    assert app.requirements.min_ram == 256
    assert app.install_count == 100
    assert app.avg_rating == 4.5
    assert app.featured is True


def test_marketplace_app_camelcase_aliases():
    """Test MarketplaceApp camelCase field aliases."""
    now = datetime.now()
    app_data = {
        "id": "test-app-2",
        "name": "Test App",
        "description": "Short desc",
        "longDescription": "Long description",  # camelCase
        "version": "2.0.0",
        "category": "media",
        "tags": ["video"],
        "icon": "https://example.com/icon.png",
        "author": "Author Name",
        "license": "Apache-2.0",
        "repository": "https://github.com/test/app",
        "documentation": "https://docs.example.com",
        "repoId": "repo-1",  # camelCase
        "docker": {
            "image": "test/app:2.0",
            "ports": [],
            "volumes": [],
            "environment": [],
            "restartPolicy": "always",  # camelCase
            "networkMode": None,  # camelCase
            "privileged": False,
            "capabilities": []
        },
        "requirements": {
            "minRam": 512,  # camelCase
            "minStorage": 1024,  # camelCase
            "architectures": ["arm64"]
        },
        "installCount": 50,  # camelCase
        "avgRating": 4.0,  # camelCase
        "ratingCount": 10,  # camelCase
        "featured": False,
        "createdAt": now.isoformat(),  # camelCase
        "updatedAt": now.isoformat()  # camelCase
    }

    app = MarketplaceApp(**app_data)
    assert app.long_description == "Long description"
    assert app.repo_id == "repo-1"
    assert app.install_count == 50
    assert app.avg_rating == 4.0
    assert app.rating_count == 10

    # Test serialization to camelCase
    serialized = app.model_dump(by_alias=True)
    assert "longDescription" in serialized
    assert "repoId" in serialized
    assert "installCount" in serialized
    assert "avgRating" in serialized
    assert "ratingCount" in serialized
    assert "createdAt" in serialized
    assert "updatedAt" in serialized


def test_marketplace_app_validation():
    """Test MarketplaceApp validation for required fields."""
    with pytest.raises(ValidationError):
        MarketplaceApp(
            # Missing required fields
            name="Incomplete App"
        )


def test_app_rating_model():
    """Test AppRating model creation and validation."""
    rating = AppRating(
        id="rating-1",
        app_id="test-app-1",
        user_id="user-123",
        rating=5,
        created_at="2024-01-01T00:00:00Z",
        updated_at="2024-01-01T00:00:00Z"
    )

    assert rating.id == "rating-1"
    assert rating.app_id == "test-app-1"
    assert rating.user_id == "user-123"
    assert rating.rating == 5
    assert rating.created_at == "2024-01-01T00:00:00Z"
    assert rating.updated_at == "2024-01-01T00:00:00Z"


def test_app_rating_validation_range():
    """Test AppRating validates rating is between 1 and 5."""
    # Valid ratings
    for valid_rating in [1, 2, 3, 4, 5]:
        rating = AppRating(
            id=f"rating-{valid_rating}",
            app_id="test-app-1",
            user_id="user-123",
            rating=valid_rating,
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z"
        )
        assert rating.rating == valid_rating

    # Invalid ratings
    with pytest.raises(ValidationError):
        AppRating(
            id="rating-invalid-low",
            app_id="test-app-1",
            user_id="user-123",
            rating=0,  # Too low
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z"
        )

    with pytest.raises(ValidationError):
        AppRating(
            id="rating-invalid-high",
            app_id="test-app-1",
            user_id="user-123",
            rating=6,  # Too high
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z"
        )


def test_app_rating_camelcase_aliases():
    """Test AppRating camelCase field aliases."""
    rating_data = {
        "id": "rating-2",
        "appId": "test-app-2",  # camelCase
        "userId": "user-456",  # camelCase
        "rating": 4,
        "createdAt": "2024-02-01T00:00:00Z",  # camelCase
        "updatedAt": "2024-02-01T00:00:00Z"  # camelCase
    }

    rating = AppRating(**rating_data)
    assert rating.app_id == "test-app-2"
    assert rating.user_id == "user-456"
    assert rating.created_at == "2024-02-01T00:00:00Z"
    assert rating.updated_at == "2024-02-01T00:00:00Z"

    # Test serialization to camelCase
    serialized = rating.model_dump(by_alias=True)
    assert "appId" in serialized
    assert "userId" in serialized
    assert "createdAt" in serialized
    assert "updatedAt" in serialized


def test_app_rating_required_fields():
    """Test AppRating validation for required fields."""
    with pytest.raises(ValidationError):
        AppRating(
            # Missing required fields
            id="rating-incomplete"
        )
