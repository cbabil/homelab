"""
Marketplace Tools Unit Tests

Tests for marketplace repository and app management tools.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from tools.marketplace.tools import MarketplaceTools


class TestMarketplaceToolsInit:
    """Tests for MarketplaceTools initialization."""

    def test_initialization(self):
        """Test MarketplaceTools is initialized correctly."""
        mock_marketplace = MagicMock()
        mock_app = MagicMock()

        with patch('tools.marketplace.tools.logger'):
            tools = MarketplaceTools(mock_marketplace, mock_app)

        assert tools.marketplace_service == mock_marketplace
        assert tools.app_service == mock_app

    def test_initialization_without_app_service(self):
        """Test initialization without app service."""
        mock_marketplace = MagicMock()

        with patch('tools.marketplace.tools.logger'):
            tools = MarketplaceTools(mock_marketplace)

        assert tools.app_service is None


class TestListRepos:
    """Tests for list_repos tool."""

    @pytest.fixture
    def mock_service(self):
        """Create mock marketplace service."""
        return MagicMock()

    @pytest.fixture
    def tools(self, mock_service):
        """Create MarketplaceTools instance."""
        with patch('tools.marketplace.tools.logger'):
            return MarketplaceTools(mock_service)

    @pytest.fixture
    def sample_repos(self):
        """Create sample repos."""
        repo = MagicMock()
        repo.model_dump.return_value = {"id": "repo-1", "name": "Official", "enabled": True}
        return [repo]

    @pytest.mark.asyncio
    async def test_list_repos_success(self, tools, mock_service, sample_repos):
        """Test successfully listing repos."""
        mock_service.get_repos = AsyncMock(return_value=sample_repos)

        result = await tools.list_repos()

        assert result["success"] is True
        assert len(result["data"]) == 1

    @pytest.mark.asyncio
    async def test_list_repos_exception(self, tools, mock_service):
        """Test handling exceptions."""
        mock_service.get_repos = AsyncMock(side_effect=Exception("Database error"))

        result = await tools.list_repos()

        assert result["success"] is False
        assert "Database error" in result["error"]


class TestAddRepo:
    """Tests for add_repo tool."""

    @pytest.fixture
    def mock_service(self):
        """Create mock marketplace service."""
        return MagicMock()

    @pytest.fixture
    def tools(self, mock_service):
        """Create MarketplaceTools instance."""
        with patch('tools.marketplace.tools.logger'):
            return MarketplaceTools(mock_service)

    @pytest.mark.asyncio
    async def test_add_repo_success(self, tools, mock_service):
        """Test successfully adding a repo."""
        repo = MagicMock()
        repo.id = "repo-new"
        repo.model_dump.return_value = {"id": "repo-new", "name": "New Repo"}
        mock_service.add_repo = AsyncMock(return_value=repo)

        with patch('tools.marketplace.tools.log_event', new_callable=AsyncMock):
            result = await tools.add_repo(
                name="New Repo",
                url="https://github.com/example/apps",
                repo_type="community",
                branch="main"
            )

        assert result["success"] is True
        assert result["data"]["id"] == "repo-new"

    @pytest.mark.asyncio
    async def test_add_repo_exception(self, tools, mock_service):
        """Test handling exceptions."""
        mock_service.add_repo = AsyncMock(side_effect=Exception("Invalid URL"))

        with patch('tools.marketplace.tools.log_event', new_callable=AsyncMock):
            result = await tools.add_repo(
                name="Bad Repo",
                url="invalid",
                repo_type="community"
            )

        assert result["success"] is False
        assert "Invalid URL" in result["error"]


class TestRemoveRepo:
    """Tests for remove_repo tool."""

    @pytest.fixture
    def mock_service(self):
        """Create mock marketplace service."""
        return MagicMock()

    @pytest.fixture
    def tools(self, mock_service):
        """Create MarketplaceTools instance."""
        with patch('tools.marketplace.tools.logger'):
            return MarketplaceTools(mock_service)

    @pytest.mark.asyncio
    async def test_remove_repo_success(self, tools, mock_service):
        """Test successfully removing a repo."""
        mock_service.remove_repo = AsyncMock(return_value=True)

        with patch('tools.marketplace.tools.log_event', new_callable=AsyncMock):
            result = await tools.remove_repo("repo-1")

        assert result["success"] is True
        assert "removed" in result["message"]

    @pytest.mark.asyncio
    async def test_remove_repo_not_found(self, tools, mock_service):
        """Test removing non-existent repo."""
        mock_service.remove_repo = AsyncMock(return_value=False)

        with patch('tools.marketplace.tools.log_event', new_callable=AsyncMock):
            result = await tools.remove_repo("repo-404")

        assert result["success"] is False
        assert "not found" in result["message"]

    @pytest.mark.asyncio
    async def test_remove_repo_exception(self, tools, mock_service):
        """Test handling exceptions."""
        mock_service.remove_repo = AsyncMock(side_effect=Exception("Database error"))

        with patch('tools.marketplace.tools.log_event', new_callable=AsyncMock):
            result = await tools.remove_repo("repo-1")

        assert result["success"] is False


class TestSyncRepo:
    """Tests for sync_repo tool."""

    @pytest.fixture
    def mock_service(self):
        """Create mock marketplace service."""
        return MagicMock()

    @pytest.fixture
    def tools(self, mock_service):
        """Create MarketplaceTools instance."""
        with patch('tools.marketplace.tools.logger'):
            return MarketplaceTools(mock_service)

    @pytest.mark.asyncio
    async def test_sync_repo_success(self, tools, mock_service):
        """Test successfully syncing a repo."""
        apps = [MagicMock(), MagicMock(), MagicMock()]
        mock_service.sync_repo = AsyncMock(return_value=apps)

        with patch('tools.marketplace.tools.log_event', new_callable=AsyncMock):
            result = await tools.sync_repo("repo-1")

        assert result["success"] is True
        assert result["data"]["appCount"] == 3

    @pytest.mark.asyncio
    async def test_sync_repo_exception(self, tools, mock_service):
        """Test handling exceptions."""
        mock_service.sync_repo = AsyncMock(side_effect=Exception("Network error"))

        with patch('tools.marketplace.tools.log_event', new_callable=AsyncMock):
            result = await tools.sync_repo("repo-1")

        assert result["success"] is False


class TestToggleRepo:
    """Tests for toggle_repo tool."""

    @pytest.fixture
    def mock_service(self):
        """Create mock marketplace service."""
        return MagicMock()

    @pytest.fixture
    def tools(self, mock_service):
        """Create MarketplaceTools instance."""
        with patch('tools.marketplace.tools.logger'):
            return MarketplaceTools(mock_service)

    @pytest.mark.asyncio
    async def test_toggle_repo_enable(self, tools, mock_service):
        """Test enabling a repo."""
        mock_service.toggle_repo = AsyncMock(return_value=True)

        with patch('tools.marketplace.tools.log_event', new_callable=AsyncMock):
            result = await tools.toggle_repo("repo-1", True)

        assert result["success"] is True
        assert result["data"]["enabled"] is True
        assert "enabled" in result["message"]

    @pytest.mark.asyncio
    async def test_toggle_repo_disable(self, tools, mock_service):
        """Test disabling a repo."""
        mock_service.toggle_repo = AsyncMock(return_value=True)

        with patch('tools.marketplace.tools.log_event', new_callable=AsyncMock):
            result = await tools.toggle_repo("repo-1", False)

        assert result["success"] is True
        assert result["data"]["enabled"] is False
        assert "disabled" in result["message"]

    @pytest.mark.asyncio
    async def test_toggle_repo_not_found(self, tools, mock_service):
        """Test toggling non-existent repo."""
        mock_service.toggle_repo = AsyncMock(return_value=False)

        with patch('tools.marketplace.tools.log_event', new_callable=AsyncMock):
            result = await tools.toggle_repo("repo-404", True)

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_toggle_repo_exception(self, tools, mock_service):
        """Test handling exceptions."""
        mock_service.toggle_repo = AsyncMock(side_effect=Exception("Database error"))

        with patch('tools.marketplace.tools.log_event', new_callable=AsyncMock):
            result = await tools.toggle_repo("repo-1", True)

        assert result["success"] is False


class TestSearchMarketplace:
    """Tests for search_marketplace tool."""

    @pytest.fixture
    def mock_service(self):
        """Create mock marketplace service."""
        return MagicMock()

    @pytest.fixture
    def tools(self, mock_service):
        """Create MarketplaceTools instance."""
        with patch('tools.marketplace.tools.logger'):
            return MarketplaceTools(mock_service)

    @pytest.fixture
    def sample_apps(self):
        """Create sample apps."""
        app = MagicMock()
        app.model_dump.return_value = {"id": "app-1", "name": "Test App"}
        return [app]

    @pytest.mark.asyncio
    async def test_search_marketplace_success(self, tools, mock_service, sample_apps):
        """Test successfully searching marketplace."""
        mock_service.search_apps = AsyncMock(return_value=sample_apps)

        result = await tools.search_marketplace(search="test")

        assert result["success"] is True
        assert result["data"]["total"] == 1

    @pytest.mark.asyncio
    async def test_search_marketplace_with_filters(
        self, tools, mock_service, sample_apps
    ):
        """Test searching with filters."""
        mock_service.search_apps = AsyncMock(return_value=sample_apps)

        result = await tools.search_marketplace(
            search="nginx",
            category="web",
            tags=["proxy"],
            featured=True,
            sort_by="rating",
            limit=10
        )

        assert result["success"] is True
        mock_service.search_apps.assert_called_with(
            search="nginx",
            category="web",
            tags=["proxy"],
            featured=True,
            sort_by="rating",
            limit=10
        )

    @pytest.mark.asyncio
    async def test_search_marketplace_exception(self, tools, mock_service):
        """Test handling exceptions."""
        mock_service.search_apps = AsyncMock(side_effect=Exception("Search error"))

        result = await tools.search_marketplace()

        assert result["success"] is False


class TestGetMarketplaceApp:
    """Tests for get_marketplace_app tool."""

    @pytest.fixture
    def mock_service(self):
        """Create mock marketplace service."""
        return MagicMock()

    @pytest.fixture
    def tools(self, mock_service):
        """Create MarketplaceTools instance."""
        with patch('tools.marketplace.tools.logger'):
            return MarketplaceTools(mock_service)

    @pytest.mark.asyncio
    async def test_get_app_success(self, tools, mock_service):
        """Test successfully getting an app."""
        app = MagicMock()
        app.model_dump.return_value = {"id": "app-1", "name": "Test App"}
        mock_service.get_app = AsyncMock(return_value=app)

        result = await tools.get_marketplace_app("app-1")

        assert result["success"] is True
        assert result["data"]["id"] == "app-1"

    @pytest.mark.asyncio
    async def test_get_app_not_found(self, tools, mock_service):
        """Test getting non-existent app."""
        mock_service.get_app = AsyncMock(return_value=None)

        result = await tools.get_marketplace_app("app-404")

        assert result["success"] is False
        assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_get_app_exception(self, tools, mock_service):
        """Test handling exceptions."""
        mock_service.get_app = AsyncMock(side_effect=Exception("Database error"))

        result = await tools.get_marketplace_app("app-1")

        assert result["success"] is False


class TestGetMarketplaceCategories:
    """Tests for get_marketplace_categories tool."""

    @pytest.fixture
    def mock_service(self):
        """Create mock marketplace service."""
        return MagicMock()

    @pytest.fixture
    def tools(self, mock_service):
        """Create MarketplaceTools instance."""
        with patch('tools.marketplace.tools.logger'):
            return MarketplaceTools(mock_service)

    @pytest.mark.asyncio
    async def test_get_categories_success(self, tools, mock_service):
        """Test successfully getting categories."""
        categories = ["database", "web", "monitoring"]
        mock_service.get_categories = AsyncMock(return_value=categories)

        result = await tools.get_marketplace_categories()

        assert result["success"] is True
        assert result["data"] == categories

    @pytest.mark.asyncio
    async def test_get_categories_exception(self, tools, mock_service):
        """Test handling exceptions."""
        mock_service.get_categories = AsyncMock(side_effect=Exception("Database error"))

        result = await tools.get_marketplace_categories()

        assert result["success"] is False


class TestGetFeaturedApps:
    """Tests for get_featured_apps tool."""

    @pytest.fixture
    def mock_service(self):
        """Create mock marketplace service."""
        return MagicMock()

    @pytest.fixture
    def tools(self, mock_service):
        """Create MarketplaceTools instance."""
        with patch('tools.marketplace.tools.logger'):
            return MarketplaceTools(mock_service)

    @pytest.fixture
    def sample_apps(self):
        """Create sample apps."""
        app = MagicMock()
        app.model_dump.return_value = {"id": "app-1", "featured": True}
        return [app]

    @pytest.mark.asyncio
    async def test_get_featured_apps_success(self, tools, mock_service, sample_apps):
        """Test successfully getting featured apps."""
        mock_service.get_featured_apps = AsyncMock(return_value=sample_apps)

        result = await tools.get_featured_apps(limit=5)

        assert result["success"] is True
        assert len(result["data"]) == 1
        mock_service.get_featured_apps.assert_called_with(5)

    @pytest.mark.asyncio
    async def test_get_featured_apps_exception(self, tools, mock_service):
        """Test handling exceptions."""
        mock_service.get_featured_apps = AsyncMock(
            side_effect=Exception("Database error")
        )

        result = await tools.get_featured_apps()

        assert result["success"] is False


class TestGetTrendingApps:
    """Tests for get_trending_apps tool."""

    @pytest.fixture
    def mock_service(self):
        """Create mock marketplace service."""
        return MagicMock()

    @pytest.fixture
    def tools(self, mock_service):
        """Create MarketplaceTools instance."""
        with patch('tools.marketplace.tools.logger'):
            return MarketplaceTools(mock_service)

    @pytest.fixture
    def sample_apps(self):
        """Create sample apps."""
        app = MagicMock()
        app.model_dump.return_value = {"id": "app-1", "name": "Trending App"}
        return [app]

    @pytest.mark.asyncio
    async def test_get_trending_apps_success(self, tools, mock_service, sample_apps):
        """Test successfully getting trending apps."""
        mock_service.get_trending_apps = AsyncMock(return_value=sample_apps)

        result = await tools.get_trending_apps(limit=5)

        assert result["success"] is True
        assert len(result["data"]) == 1

    @pytest.mark.asyncio
    async def test_get_trending_apps_exception(self, tools, mock_service):
        """Test handling exceptions."""
        mock_service.get_trending_apps = AsyncMock(
            side_effect=Exception("Database error")
        )

        result = await tools.get_trending_apps()

        assert result["success"] is False


class TestRateMarketplaceApp:
    """Tests for rate_marketplace_app tool."""

    @pytest.fixture
    def mock_service(self):
        """Create mock marketplace service."""
        return MagicMock()

    @pytest.fixture
    def tools(self, mock_service):
        """Create MarketplaceTools instance."""
        with patch('tools.marketplace.tools.logger'):
            return MarketplaceTools(mock_service)

    @pytest.mark.asyncio
    async def test_rate_app_success(self, tools, mock_service):
        """Test successfully rating an app."""
        result_obj = MagicMock()
        result_obj.model_dump.return_value = {"app_id": "app-1", "avg_rating": 4.5}
        mock_service.rate_app = AsyncMock(return_value=result_obj)

        with patch('tools.marketplace.tools.log_event', new_callable=AsyncMock):
            result = await tools.rate_marketplace_app("app-1", "user-123", 5)

        assert result["success"] is True
        assert "5 stars" in result["message"]

    @pytest.mark.asyncio
    async def test_rate_app_invalid_rating(self, tools, mock_service):
        """Test rating with invalid value."""
        mock_service.rate_app = AsyncMock(side_effect=ValueError("Rating must be 1-5"))

        result = await tools.rate_marketplace_app("app-1", "user-123", 10)

        assert result["success"] is False
        assert "1-5" in result["error"]

    @pytest.mark.asyncio
    async def test_rate_app_exception(self, tools, mock_service):
        """Test handling exceptions."""
        mock_service.rate_app = AsyncMock(side_effect=Exception("Database error"))

        with patch('tools.marketplace.tools.log_event', new_callable=AsyncMock):
            result = await tools.rate_marketplace_app("app-1", "user-123", 5)

        assert result["success"] is False


class TestImportApp:
    """Tests for import_app tool."""

    @pytest.fixture
    def mock_marketplace_service(self):
        """Create mock marketplace service."""
        return MagicMock()

    @pytest.fixture
    def mock_app_service(self):
        """Create mock app service."""
        return MagicMock()

    @pytest.fixture
    def tools(self, mock_marketplace_service, mock_app_service):
        """Create MarketplaceTools instance."""
        with patch('tools.marketplace.tools.logger'):
            return MarketplaceTools(mock_marketplace_service, mock_app_service)

    @pytest.fixture
    def sample_marketplace_app(self):
        """Create sample marketplace app."""
        app = MagicMock()
        app.id = "app-1"
        app.name = "Test App"
        app.description = "A test app"
        app.long_description = "Long description"
        app.version = "1.0.0"
        app.category = "utility"
        app.tags = ["test"]
        app.icon = "icon.png"
        app.author = "Test Author"
        app.license = "MIT"
        app.repository = "https://github.com/test/app"
        app.documentation = "https://docs.example.com"
        app.requirements = MagicMock(
            min_ram="512MB", min_storage="1GB", architectures=["amd64"]
        )
        app.avg_rating = 4.5
        app.featured = False
        return app

    @pytest.mark.asyncio
    async def test_import_app_success(
        self, tools, mock_marketplace_service, mock_app_service, sample_marketplace_app
    ):
        """Test successfully importing an app."""
        mock_marketplace_service.get_app = AsyncMock(return_value=sample_marketplace_app)
        mock_app_service.add_app = AsyncMock()

        with patch('tools.marketplace.tools.log_event', new_callable=AsyncMock):
            result = await tools.import_app("app-1", "user-123")

        assert result["success"] is True
        assert result["data"]["app_id"] == "app-1"
        assert result["data"]["app_name"] == "Test App"

    @pytest.mark.asyncio
    async def test_import_app_not_found(self, tools, mock_marketplace_service):
        """Test importing non-existent app."""
        mock_marketplace_service.get_app = AsyncMock(return_value=None)

        result = await tools.import_app("app-404", "user-123")

        assert result["success"] is False
        assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_import_app_no_app_service(self, mock_marketplace_service):
        """Test import when app service not configured."""
        with patch('tools.marketplace.tools.logger'):
            tools = MarketplaceTools(mock_marketplace_service, None)

        app = MagicMock()
        mock_marketplace_service.get_app = AsyncMock(return_value=app)

        result = await tools.import_app("app-1", "user-123")

        assert result["success"] is False
        assert "not configured" in result["error"]

    @pytest.mark.asyncio
    async def test_import_app_already_exists(
        self, tools, mock_marketplace_service, mock_app_service, sample_marketplace_app
    ):
        """Test importing app that already exists."""
        mock_marketplace_service.get_app = AsyncMock(return_value=sample_marketplace_app)
        mock_app_service.add_app = AsyncMock(side_effect=ValueError("App already exists"))

        result = await tools.import_app("app-1", "user-123")

        assert result["success"] is False
        assert "already exists" in result["error"]

    @pytest.mark.asyncio
    async def test_import_app_exception(
        self, tools, mock_marketplace_service, mock_app_service, sample_marketplace_app
    ):
        """Test handling exceptions."""
        mock_marketplace_service.get_app = AsyncMock(return_value=sample_marketplace_app)
        mock_app_service.add_app = AsyncMock(side_effect=Exception("Database error"))

        with patch('tools.marketplace.tools.log_event', new_callable=AsyncMock):
            result = await tools.import_app("app-1", "user-123")

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_import_app_without_requirements(
        self, tools, mock_marketplace_service, mock_app_service
    ):
        """Test importing app without requirements."""
        app = MagicMock()
        app.id = "app-1"
        app.name = "Simple App"
        app.description = "Simple"
        app.long_description = None
        app.version = "1.0.0"
        app.category = "utility"
        app.tags = []
        app.icon = None
        app.author = "Author"
        app.license = "MIT"
        app.repository = None
        app.documentation = None
        app.requirements = None
        app.avg_rating = 0
        app.featured = False

        mock_marketplace_service.get_app = AsyncMock(return_value=app)
        mock_app_service.add_app = AsyncMock()

        with patch('tools.marketplace.tools.log_event', new_callable=AsyncMock):
            result = await tools.import_app("app-1", "user-123")

        assert result["success"] is True
