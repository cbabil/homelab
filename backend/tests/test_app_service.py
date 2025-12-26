"""
Unit Tests for Application Service

Tests the application service business logic and data operations.
Ensures proper functionality of app management features.
"""

import pytest
from datetime import datetime
from models.app import AppFilter, AppStatus
from services.app_service import AppService


@pytest.mark.unit
class TestAppService:
    """Test cases for AppService class."""
    
    @pytest.fixture
    def app_service(self):
        """Create AppService instance for testing."""
        return AppService()
    
    @pytest.mark.asyncio
    async def test_search_apps_no_filter(self, app_service):
        """Test searching apps without filters returns all apps."""
        filters = AppFilter()
        result = await app_service.search_apps(filters)
        
        assert result.total > 0
        assert len(result.apps) == result.total
        assert result.page == 1
        assert result.filters == filters
    
    @pytest.mark.asyncio
    async def test_search_apps_by_name(self, app_service):
        """Test searching apps by name filter."""
        filters = AppFilter(search="portainer")
        result = await app_service.search_apps(filters)
        
        assert result.total >= 0
        if result.total > 0:
            # All results should contain search term in name or description
            for app in result.apps:
                assert ("portainer" in app.name.lower() or 
                       "portainer" in app.description.lower())
    
    @pytest.mark.asyncio
    async def test_search_apps_by_category(self, app_service):
        """Test searching apps by category filter."""
        filters = AppFilter(category="management")
        result = await app_service.search_apps(filters)
        
        if result.total > 0:
            # All results should match category
            for app in result.apps:
                assert app.category.id == "management"
    
    @pytest.mark.asyncio
    async def test_search_apps_by_status(self, app_service):
        """Test searching apps by status filter."""
        filters = AppFilter(status=AppStatus.AVAILABLE)
        result = await app_service.search_apps(filters)
        
        if result.total > 0:
            # All results should match status
            for app in result.apps:
                assert app.status == AppStatus.AVAILABLE
    
    @pytest.mark.asyncio
    async def test_get_app_by_id_existing(self, app_service):
        """Test getting existing app by ID."""
        app = await app_service.get_app_by_id("portainer")
        
        assert app is not None
        assert app.id == "portainer"
        assert app.name == "Portainer"
    
    @pytest.mark.asyncio
    async def test_get_app_by_id_nonexistent(self, app_service):
        """Test getting non-existent app by ID."""
        app = await app_service.get_app_by_id("nonexistent")
        
        assert app is None
    
    @pytest.mark.asyncio
    async def test_install_app_success(self, app_service):
        """Test successful app installation."""
        config = {"port": 9000, "env": {"ADMIN_PASSWORD": "secret"}}
        installation = await app_service.install_app("portainer", config)
        
        assert installation.app_id == "portainer"
        assert installation.status == AppStatus.INSTALLING
        assert installation.config == config
        assert installation.installed_at is not None
    
    @pytest.mark.asyncio
    async def test_install_app_nonexistent(self, app_service):
        """Test installing non-existent app raises error."""
        with pytest.raises(ValueError, match="Application nonexistent not found"):
            await app_service.install_app("nonexistent")
    
    @pytest.mark.asyncio
    async def test_search_apps_sorting_name_asc(self, app_service):
        """Test searching apps with name sorting ascending."""
        filters = AppFilter(sort_by="name", sort_order="asc")
        result = await app_service.search_apps(filters)
        
        if result.total > 1:
            # Verify ascending order
            app_names = [app.name for app in result.apps]
            assert app_names == sorted(app_names)
    
    @pytest.mark.asyncio
    async def test_search_apps_sorting_name_desc(self, app_service):
        """Test searching apps with name sorting descending."""
        filters = AppFilter(sort_by="name", sort_order="desc")
        result = await app_service.search_apps(filters)
        
        if result.total > 1:
            # Verify descending order
            app_names = [app.name for app in result.apps]
            assert app_names == sorted(app_names, reverse=True)