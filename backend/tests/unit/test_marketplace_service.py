"""Unit tests for MarketplaceService."""

import pytest
from sqlalchemy import delete
from services.marketplace_service import MarketplaceService
from models.marketplace import RepoType, RepoStatus, MarketplaceRepoTable, MarketplaceAppTable
from database.connection import db_manager


@pytest.fixture
async def marketplace_service():
    """Create a MarketplaceService instance for testing."""
    service = MarketplaceService()

    # Clean up before each test
    await service._ensure_initialized()
    async with db_manager.get_session() as session:
        await session.execute(delete(MarketplaceAppTable))
        await session.execute(delete(MarketplaceRepoTable))

    return service


@pytest.mark.asyncio
async def test_add_repo_personal(marketplace_service):
    """Test adding a personal repository."""
    repo = await marketplace_service.add_repo(
        name="Test Personal Repo",
        url="https://github.com/test/apps",
        repo_type=RepoType.PERSONAL
    )
    assert repo.name == "Test Personal Repo"
    assert repo.url == "https://github.com/test/apps"
    assert repo.repo_type == RepoType.PERSONAL
    assert repo.branch == "main"
    assert repo.enabled is True
    assert repo.status == RepoStatus.ACTIVE
    assert repo.app_count == 0
    assert repo.error_message is None
    assert len(repo.id) == 8


@pytest.mark.asyncio
async def test_add_repo_with_branch(marketplace_service):
    """Test adding a repository with custom branch."""
    repo = await marketplace_service.add_repo(
        name="Test Repo",
        url="https://github.com/test/apps",
        repo_type=RepoType.COMMUNITY,
        branch="develop"
    )
    assert repo.name == "Test Repo"
    assert repo.branch == "develop"
    assert repo.repo_type == RepoType.COMMUNITY


@pytest.mark.asyncio
async def test_get_repos_empty(marketplace_service):
    """Test getting repos when none exist."""
    repos = await marketplace_service.get_repos()
    assert repos == []


@pytest.mark.asyncio
async def test_get_repos_all(marketplace_service):
    """Test getting all repositories."""
    # Add two repos
    repo1 = await marketplace_service.add_repo(
        name="Repo 1",
        url="https://github.com/test/apps1",
        repo_type=RepoType.OFFICIAL
    )
    repo2 = await marketplace_service.add_repo(
        name="Repo 2",
        url="https://github.com/test/apps2",
        repo_type=RepoType.COMMUNITY
    )

    # Get all repos
    repos = await marketplace_service.get_repos()
    assert len(repos) == 2
    assert any(r.id == repo1.id for r in repos)
    assert any(r.id == repo2.id for r in repos)


@pytest.mark.asyncio
async def test_get_repos_enabled_only(marketplace_service):
    """Test filtering for enabled repos only."""
    # Add enabled and disabled repos
    repo1 = await marketplace_service.add_repo(
        name="Enabled Repo",
        url="https://github.com/test/apps1",
        repo_type=RepoType.PERSONAL
    )
    repo2 = await marketplace_service.add_repo(
        name="Disabled Repo",
        url="https://github.com/test/apps2",
        repo_type=RepoType.PERSONAL
    )

    # Disable repo2
    await marketplace_service.toggle_repo(repo2.id, False)

    # Get only enabled repos
    enabled_repos = await marketplace_service.get_repos(enabled_only=True)
    assert len(enabled_repos) == 1
    assert enabled_repos[0].id == repo1.id
    assert enabled_repos[0].enabled is True


@pytest.mark.asyncio
async def test_get_repo_by_id(marketplace_service):
    """Test getting a single repository by ID."""
    # Add a repo
    created_repo = await marketplace_service.add_repo(
        name="Test Repo",
        url="https://github.com/test/apps",
        repo_type=RepoType.OFFICIAL
    )

    # Get it back
    retrieved_repo = await marketplace_service.get_repo(created_repo.id)
    assert retrieved_repo is not None
    assert retrieved_repo.id == created_repo.id
    assert retrieved_repo.name == "Test Repo"
    assert retrieved_repo.url == "https://github.com/test/apps"


@pytest.mark.asyncio
async def test_get_repo_not_found(marketplace_service):
    """Test getting a repository that doesn't exist."""
    repo = await marketplace_service.get_repo("nonexistent")
    assert repo is None


@pytest.mark.asyncio
async def test_toggle_repo_disable(marketplace_service):
    """Test disabling a repository."""
    # Add a repo
    repo = await marketplace_service.add_repo(
        name="Test Repo",
        url="https://github.com/test/apps",
        repo_type=RepoType.COMMUNITY
    )
    assert repo.enabled is True

    # Disable it
    success = await marketplace_service.toggle_repo(repo.id, False)
    assert success is True

    # Verify it's disabled
    updated_repo = await marketplace_service.get_repo(repo.id)
    assert updated_repo is not None
    assert updated_repo.enabled is False


@pytest.mark.asyncio
async def test_toggle_repo_enable(marketplace_service):
    """Test enabling a repository."""
    # Add and disable a repo
    repo = await marketplace_service.add_repo(
        name="Test Repo",
        url="https://github.com/test/apps",
        repo_type=RepoType.PERSONAL
    )
    await marketplace_service.toggle_repo(repo.id, False)

    # Enable it
    success = await marketplace_service.toggle_repo(repo.id, True)
    assert success is True

    # Verify it's enabled
    updated_repo = await marketplace_service.get_repo(repo.id)
    assert updated_repo is not None
    assert updated_repo.enabled is True


@pytest.mark.asyncio
async def test_toggle_repo_not_found(marketplace_service):
    """Test toggling a repository that doesn't exist."""
    success = await marketplace_service.toggle_repo("nonexistent", False)
    assert success is False


@pytest.mark.asyncio
async def test_remove_repo(marketplace_service):
    """Test removing a repository."""
    # Add a repo
    repo = await marketplace_service.add_repo(
        name="Test Repo",
        url="https://github.com/test/apps",
        repo_type=RepoType.COMMUNITY
    )

    # Remove it
    success = await marketplace_service.remove_repo(repo.id)
    assert success is True

    # Verify it's gone
    removed_repo = await marketplace_service.get_repo(repo.id)
    assert removed_repo is None


@pytest.mark.asyncio
async def test_remove_repo_not_found(marketplace_service):
    """Test removing a repository that doesn't exist."""
    success = await marketplace_service.remove_repo("nonexistent")
    assert success is False


@pytest.mark.asyncio
async def test_remove_repo_with_apps(marketplace_service):
    """Test removing a repository should remove its apps."""
    # Add a repo
    repo = await marketplace_service.add_repo(
        name="Test Repo",
        url="https://github.com/test/apps",
        repo_type=RepoType.OFFICIAL
    )

    # Note: This test verifies the deletion logic works
    # Actual app deletion will be tested when we have app creation
    success = await marketplace_service.remove_repo(repo.id)
    assert success is True
