"""
Unit tests for marketplace MCP tools.

Following TDD: Write tests first, verify they fail, then implement.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from tools.marketplace.tools import MarketplaceTools
from models.marketplace import (
    MarketplaceRepo,
    MarketplaceApp,
    AppRating,
    RepoType,
    RepoStatus,
    DockerConfig,
    AppRequirements,
    AppPort,
)


@pytest.fixture
def mock_marketplace_service():
    """Create a mock marketplace service."""
    service = AsyncMock()
    return service


@pytest.fixture
def marketplace_tools(mock_marketplace_service):
    """Create marketplace tools with mocked service."""
    return MarketplaceTools(mock_marketplace_service)


# ─────────────────────────────────────────────────────────────
# Repository Management Tools
# ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_repos_success(marketplace_tools, mock_marketplace_service):
    """Test list_repos returns all repositories."""
    # Arrange
    mock_repos = [
        MarketplaceRepo(
            id="repo-1",
            name="Official Apps",
            url="https://github.com/tomo/apps",
            branch="main",
            repo_type=RepoType.OFFICIAL,
            enabled=True,
            status=RepoStatus.ACTIVE,
            app_count=5,
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
        )
    ]
    mock_marketplace_service.get_repos.return_value = mock_repos

    # Act
    result = await marketplace_tools.list_repos()

    # Assert
    assert result["success"] is True
    assert len(result["data"]) == 1
    assert result["data"][0]["id"] == "repo-1"
    assert result["data"][0]["name"] == "Official Apps"


@pytest.mark.asyncio
async def test_list_repos_error(marketplace_tools, mock_marketplace_service):
    """Test list_repos handles errors gracefully."""
    # Arrange
    mock_marketplace_service.get_repos.side_effect = Exception("Database error")

    # Act
    result = await marketplace_tools.list_repos()

    # Assert
    assert result["success"] is False
    assert "Database error" in result["error"]


@pytest.mark.asyncio
async def test_add_repo_success(marketplace_tools, mock_marketplace_service):
    """Test add_repo creates a new repository."""
    # Arrange
    new_repo = MarketplaceRepo(
        id="repo-2",
        name="My Apps",
        url="https://github.com/user/apps",
        branch="main",
        repo_type=RepoType.PERSONAL,
        enabled=True,
        status=RepoStatus.ACTIVE,
        app_count=0,
        created_at="2024-01-01T00:00:00",
        updated_at="2024-01-01T00:00:00",
    )
    mock_marketplace_service.add_repo.return_value = new_repo

    # Act
    result = await marketplace_tools.add_repo(
        name="My Apps",
        url="https://github.com/user/apps",
        repo_type="personal",
        branch="main"
    )

    # Assert
    assert result["success"] is True
    assert result["data"]["id"] == "repo-2"
    assert result["data"]["name"] == "My Apps"
    assert "added successfully" in result["message"]


@pytest.mark.asyncio
async def test_add_repo_error(marketplace_tools, mock_marketplace_service):
    """Test add_repo handles errors."""
    # Arrange
    mock_marketplace_service.add_repo.side_effect = Exception("Invalid URL")

    # Act
    result = await marketplace_tools.add_repo(
        name="Test",
        url="invalid-url",
        repo_type="community"
    )

    # Assert
    assert result["success"] is False
    assert "Invalid URL" in result["error"]


@pytest.mark.asyncio
async def test_remove_repo_success(marketplace_tools, mock_marketplace_service):
    """Test remove_repo deletes a repository."""
    # Arrange
    mock_marketplace_service.remove_repo.return_value = True

    # Act
    result = await marketplace_tools.remove_repo(repo_id="repo-1")

    # Assert
    assert result["success"] is True
    assert "removed" in result["message"].lower()


@pytest.mark.asyncio
async def test_remove_repo_not_found(marketplace_tools, mock_marketplace_service):
    """Test remove_repo when repository not found."""
    # Arrange
    mock_marketplace_service.remove_repo.return_value = False

    # Act
    result = await marketplace_tools.remove_repo(repo_id="nonexistent")

    # Assert
    assert result["success"] is False
    assert "not found" in result["message"].lower()


@pytest.mark.asyncio
async def test_sync_repo_success(marketplace_tools, mock_marketplace_service):
    """Test sync_repo syncs apps from repository."""
    # Arrange
    mock_apps = [
        MarketplaceApp(
            id="app-1",
            name="Test App",
            description="A test app",
            version="1.0.0",
            category="utility",
            repo_id="repo-1",
            docker=DockerConfig(
                image="test/app:latest",
                ports=[AppPort(container=8080, host=8080, protocol="tcp")],
                volumes=[],
                environment=[],
                restart_policy="unless-stopped",
                privileged=False,
                capabilities=[],
            ),
            requirements=AppRequirements(architectures=["amd64", "arm64"]),
            tags=[],
            author="Test",
            license="MIT",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
        )
    ]
    mock_marketplace_service.sync_repo.return_value = mock_apps

    # Act
    result = await marketplace_tools.sync_repo(repo_id="repo-1")

    # Assert
    assert result["success"] is True
    assert result["data"]["app_count"] == 1
    assert "Synced 1 apps" in result["message"]


@pytest.mark.asyncio
async def test_sync_repo_error(marketplace_tools, mock_marketplace_service):
    """Test sync_repo handles sync errors."""
    # Arrange
    mock_marketplace_service.sync_repo.side_effect = Exception("Git clone failed")

    # Act
    result = await marketplace_tools.sync_repo(repo_id="repo-1")

    # Assert
    assert result["success"] is False
    assert "Git clone failed" in result["error"]


# ─────────────────────────────────────────────────────────────
# App Search and Discovery Tools
# ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_search_marketplace_success(marketplace_tools, mock_marketplace_service):
    """Test search_marketplace finds apps."""
    # Arrange
    mock_apps = [
        MarketplaceApp(
            id="app-1",
            name="Jellyfin",
            description="Media server",
            version="10.8.0",
            category="media",
            repo_id="repo-1",
            docker=DockerConfig(
                image="jellyfin/jellyfin:latest",
                ports=[],
                volumes=[],
                environment=[],
                restart_policy="unless-stopped",
                privileged=False,
                capabilities=[],
            ),
            requirements=AppRequirements(architectures=["amd64"]),
            tags=["streaming"],
            author="Community",
            license="GPL",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
        )
    ]
    mock_marketplace_service.search_apps.return_value = mock_apps

    # Act
    result = await marketplace_tools.search_marketplace(category="media", limit=10)

    # Assert
    assert result["success"] is True
    assert result["data"]["total"] == 1
    assert len(result["data"]["apps"]) == 1
    assert result["data"]["apps"][0]["name"] == "Jellyfin"


@pytest.mark.asyncio
async def test_search_marketplace_with_all_filters(marketplace_tools, mock_marketplace_service):
    """Test search_marketplace with all filter options."""
    # Arrange
    mock_marketplace_service.search_apps.return_value = []

    # Act
    result = await marketplace_tools.search_marketplace(
        search="media",
        category="entertainment",
        tags=["streaming", "movies"],
        featured=True,
        sort_by="rating",
        limit=20
    )

    # Assert
    assert result["success"] is True
    mock_marketplace_service.search_apps.assert_called_once_with(
        search="media",
        category="entertainment",
        tags=["streaming", "movies"],
        featured=True,
        sort_by="rating",
        limit=20
    )


@pytest.mark.asyncio
async def test_get_marketplace_app_success(marketplace_tools, mock_marketplace_service):
    """Test get_marketplace_app retrieves app details."""
    # Arrange
    mock_app = MarketplaceApp(
        id="jellyfin",
        name="Jellyfin",
        description="Free media server",
        version="10.8.0",
        category="media",
        repo_id="repo-1",
        docker=DockerConfig(
            image="jellyfin/jellyfin:latest",
            ports=[],
            volumes=[],
            environment=[],
            restart_policy="unless-stopped",
            privileged=False,
            capabilities=[],
        ),
        requirements=AppRequirements(architectures=["amd64", "arm64"]),
        tags=[],
        author="Jellyfin",
        license="GPL",
        created_at="2024-01-01T00:00:00",
        updated_at="2024-01-01T00:00:00",
    )
    mock_marketplace_service.get_app.return_value = mock_app

    # Act
    result = await marketplace_tools.get_marketplace_app(app_id="jellyfin")

    # Assert
    assert result["success"] is True
    assert result["data"]["id"] == "jellyfin"
    assert result["data"]["name"] == "Jellyfin"


@pytest.mark.asyncio
async def test_get_marketplace_app_not_found(marketplace_tools, mock_marketplace_service):
    """Test get_marketplace_app when app not found."""
    # Arrange
    mock_marketplace_service.get_app.return_value = None

    # Act
    result = await marketplace_tools.get_marketplace_app(app_id="nonexistent")

    # Assert
    assert result["success"] is False
    assert "not found" in result["error"].lower()


# ─────────────────────────────────────────────────────────────
# Rating Tools
# ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_rate_marketplace_app_success(marketplace_tools, mock_marketplace_service):
    """Test rate_marketplace_app creates a rating."""
    # Arrange
    mock_rating = AppRating(
        id="rating-1",
        app_id="jellyfin",
        user_id="user-123",
        rating=5,
        created_at="2024-01-01T00:00:00",
        updated_at="2024-01-01T00:00:00",
    )
    mock_marketplace_service.rate_app.return_value = mock_rating

    # Act
    result = await marketplace_tools.rate_marketplace_app(
        app_id="jellyfin",
        user_id="user-123",
        rating=5
    )

    # Assert
    assert result["success"] is True
    assert result["data"]["rating"] == 5
    assert "5 stars" in result["message"]


@pytest.mark.asyncio
async def test_rate_marketplace_app_invalid_rating(marketplace_tools, mock_marketplace_service):
    """Test rate_marketplace_app with invalid rating value."""
    # Arrange
    mock_marketplace_service.rate_app.side_effect = ValueError("Rating must be between 1 and 5")

    # Act
    result = await marketplace_tools.rate_marketplace_app(
        app_id="jellyfin",
        user_id="user-123",
        rating=6
    )

    # Assert
    assert result["success"] is False
    assert "Rating must be between 1 and 5" in result["error"]


# ─────────────────────────────────────────────────────────────
# Additional Discovery Tools
# ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_marketplace_categories_success(marketplace_tools, mock_marketplace_service):
    """Test get_marketplace_categories returns category list."""
    # Arrange
    mock_categories = [
        {"id": "media", "name": "Media", "count": 5},
        {"id": "utility", "name": "Utility", "count": 10},
    ]
    mock_marketplace_service.get_categories.return_value = mock_categories

    # Act
    result = await marketplace_tools.get_marketplace_categories()

    # Assert
    assert result["success"] is True
    assert len(result["data"]) == 2
    assert result["data"][0]["id"] == "media"
    assert result["data"][0]["count"] == 5


@pytest.mark.asyncio
async def test_get_featured_apps_success(marketplace_tools, mock_marketplace_service):
    """Test get_featured_apps returns featured apps."""
    # Arrange
    mock_apps = [
        MarketplaceApp(
            id="featured-app",
            name="Featured App",
            description="A featured app",
            version="1.0.0",
            category="utility",
            repo_id="repo-1",
            docker=DockerConfig(
                image="featured/app:latest",
                ports=[],
                volumes=[],
                environment=[],
                restart_policy="unless-stopped",
                privileged=False,
                capabilities=[],
            ),
            requirements=AppRequirements(architectures=["amd64"]),
            tags=[],
            author="Featured",
            license="MIT",
            featured=True,
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
        )
    ]
    mock_marketplace_service.get_featured_apps.return_value = mock_apps

    # Act
    result = await marketplace_tools.get_featured_apps(limit=5)

    # Assert
    assert result["success"] is True
    assert len(result["data"]) == 1
    assert result["data"][0]["id"] == "featured-app"
    mock_marketplace_service.get_featured_apps.assert_called_once_with(5)


@pytest.mark.asyncio
async def test_get_trending_apps_success(marketplace_tools, mock_marketplace_service):
    """Test get_trending_apps returns trending apps."""
    # Arrange
    mock_apps = [
        MarketplaceApp(
            id="trending-app",
            name="Trending App",
            description="A trending app",
            version="1.0.0",
            category="utility",
            repo_id="repo-1",
            docker=DockerConfig(
                image="trending/app:latest",
                ports=[],
                volumes=[],
                environment=[],
                restart_policy="unless-stopped",
                privileged=False,
                capabilities=[],
            ),
            requirements=AppRequirements(architectures=["amd64"]),
            tags=[],
            author="Trending",
            license="MIT",
            install_count=100,
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
        )
    ]
    mock_marketplace_service.get_trending_apps.return_value = mock_apps

    # Act
    result = await marketplace_tools.get_trending_apps(limit=10)

    # Assert
    assert result["success"] is True
    assert len(result["data"]) == 1
    assert result["data"][0]["id"] == "trending-app"
    mock_marketplace_service.get_trending_apps.assert_called_once_with(10)
