"""Tests for catalog service."""
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from services.catalog_service import CatalogService
from models.app_catalog import AppCategory


class TestCatalogService:
    """Tests for CatalogService."""

    @pytest.fixture
    def catalog_service(self, tmp_path):
        """Create catalog service with temp directory."""
        return CatalogService(catalog_dirs=[str(tmp_path)])

    def test_parse_app_definition(self, catalog_service, tmp_path):
        """Should parse YAML app definition."""
        yaml_content = """
id: test-app
name: Test App
description: A test application
category: utility
image: test:latest
ports:
  - container: 80
    host: 8080
"""
        app_file = tmp_path / "test-app.yaml"
        app_file.write_text(yaml_content)

        app = catalog_service._parse_app_file(app_file)

        assert app.id == "test-app"
        assert app.name == "Test App"
        assert app.category == AppCategory.UTILITY
        assert len(app.ports) == 1

    def test_load_catalog(self, catalog_service, tmp_path):
        """Should load all apps from catalog directory."""
        yaml1 = """
id: app1
name: App One
description: First app
category: storage
image: app1:latest
"""
        yaml2 = """
id: app2
name: App Two
description: Second app
category: media
image: app2:latest
"""
        (tmp_path / "app1.yaml").write_text(yaml1)
        (tmp_path / "app2.yaml").write_text(yaml2)

        catalog_service.load_catalog()

        assert len(catalog_service.apps) == 2
        assert "app1" in catalog_service.apps
        assert "app2" in catalog_service.apps

    def test_get_app(self, catalog_service, tmp_path):
        """Should get specific app by ID."""
        yaml_content = """
id: myapp
name: My App
description: My application
category: utility
image: myapp:latest
"""
        (tmp_path / "myapp.yaml").write_text(yaml_content)
        catalog_service.load_catalog()

        app = catalog_service.get_app("myapp")

        assert app is not None
        assert app.id == "myapp"

    def test_get_app_not_found(self, catalog_service):
        """Should return None for unknown app."""
        app = catalog_service.get_app("nonexistent")
        assert app is None

    def test_list_apps(self, catalog_service, tmp_path):
        """Should list all apps."""
        yaml1 = """
id: app1
name: App One
description: First
category: storage
image: app1:latest
"""
        (tmp_path / "app1.yaml").write_text(yaml1)
        catalog_service.load_catalog()

        apps = catalog_service.list_apps()

        assert len(apps) == 1
        assert apps[0].id == "app1"

    def test_list_apps_by_category(self, catalog_service, tmp_path):
        """Should filter apps by category."""
        yaml1 = """
id: storage1
name: Storage App
description: Storage
category: storage
image: s1:latest
"""
        yaml2 = """
id: media1
name: Media App
description: Media
category: media
image: m1:latest
"""
        (tmp_path / "storage1.yaml").write_text(yaml1)
        (tmp_path / "media1.yaml").write_text(yaml2)
        catalog_service.load_catalog()

        storage_apps = catalog_service.list_apps(category="storage")

        assert len(storage_apps) == 1
        assert storage_apps[0].id == "storage1"
