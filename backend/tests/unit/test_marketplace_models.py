"""Unit tests for marketplace models."""
import pytest
from datetime import datetime
from pydantic import ValidationError

from models.marketplace import MarketplaceRepo, RepoType, RepoStatus


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
