"""
Unit tests for models/app.py

Tests Pydantic models, SQLAlchemy tables, and conversion methods.
"""

import json
from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from models.app import (
    App,
    AppCategory,
    AppCategoryTable,
    AppFilter,
    AppInstallation,
    ApplicationTable,
    AppRequirements,
    AppSearchResult,
    AppStatus,
)


class TestAppStatus:
    """Tests for AppStatus enum."""

    def test_status_values(self):
        """Test all status enum values exist."""
        assert AppStatus.AVAILABLE == "available"
        assert AppStatus.INSTALLED == "installed"
        assert AppStatus.INSTALLING == "installing"
        assert AppStatus.UPDATING == "updating"
        assert AppStatus.REMOVING == "removing"
        assert AppStatus.ERROR == "error"
        assert AppStatus.DEPRECATED == "deprecated"

    def test_status_is_string_enum(self):
        """Test that status values are strings."""
        assert isinstance(AppStatus.AVAILABLE.value, str)


class TestAppRequirements:
    """Tests for AppRequirements model."""

    def test_default_values(self):
        """Test all fields default to None."""
        req = AppRequirements()
        assert req.min_ram is None
        assert req.min_storage is None
        assert req.required_ports is None
        assert req.dependencies is None
        assert req.supported_architectures is None

    def test_custom_values(self):
        """Test custom requirement values."""
        req = AppRequirements(
            min_ram="2GB",
            min_storage="10GB",
            required_ports=[80, 443],
            dependencies=["docker", "nginx"],
            supported_architectures=["amd64", "arm64"],
        )
        assert req.min_ram == "2GB"
        assert req.min_storage == "10GB"
        assert req.required_ports == [80, 443]
        assert req.dependencies == ["docker", "nginx"]
        assert req.supported_architectures == ["amd64", "arm64"]

    def test_camel_case_alias(self):
        """Test camelCase alias support."""
        req = AppRequirements(minRam="4GB", minStorage="20GB")
        assert req.min_ram == "4GB"
        assert req.min_storage == "20GB"


class TestAppCategory:
    """Tests for AppCategory model."""

    def test_required_fields(self):
        """Test required fields."""
        category = AppCategory(
            id="media",
            name="Media",
            description="Media applications",
            icon="play",
            color="blue",
        )
        assert category.id == "media"
        assert category.name == "Media"
        assert category.description == "Media applications"
        assert category.icon == "play"
        assert category.color == "blue"

    def test_missing_required_fields(self):
        """Test validation error when required fields are missing."""
        with pytest.raises(ValidationError):
            AppCategory(id="media")

    def test_from_table(self):
        """Test conversion from database table."""
        table = MagicMock(spec=AppCategoryTable)
        table.id = "utilities"
        table.name = "Utilities"
        table.description = "Utility applications"
        table.icon = "wrench"
        table.color = "gray"

        category = AppCategory.from_table(table)
        assert category.id == "utilities"
        assert category.name == "Utilities"
        assert category.description == "Utility applications"
        assert category.icon == "wrench"
        assert category.color == "gray"

    def test_to_table_model(self):
        """Test conversion to database table."""
        category = AppCategory(
            id="network",
            name="Network",
            description="Network tools",
            icon="wifi",
            color="green",
        )
        table = category.to_table_model()
        assert table.id == "network"
        assert table.name == "Network"
        assert table.description == "Network tools"
        assert table.icon == "wifi"
        assert table.color == "green"


class TestApp:
    """Tests for App model."""

    @pytest.fixture
    def sample_category(self):
        """Create a sample category for tests."""
        return AppCategory(
            id="media",
            name="Media",
            description="Media apps",
            icon="play",
            color="blue",
        )

    @pytest.fixture
    def sample_app(self, sample_category):
        """Create a sample app for tests."""
        now = datetime.now(UTC).isoformat()
        return App(
            id="plex",
            name="Plex",
            description="Media server",
            version="1.0.0",
            category=sample_category,
            author="Plex Inc",
            license="MIT",
            created_at=now,
            updated_at=now,
        )

    def test_required_fields(self, sample_category):
        """Test required fields."""
        now = datetime.now(UTC).isoformat()
        app = App(
            id="app-123",
            name="Test App",
            description="A test application",
            version="1.0.0",
            category=sample_category,
            author="Test Author",
            license="MIT",
            created_at=now,
            updated_at=now,
        )
        assert app.id == "app-123"
        assert app.name == "Test App"
        assert app.description == "A test application"
        assert app.version == "1.0.0"
        assert app.author == "Test Author"
        assert app.license == "MIT"

    def test_default_values(self, sample_category):
        """Test default values for optional fields."""
        now = datetime.now(UTC).isoformat()
        app = App(
            id="app-123",
            name="Test App",
            description="A test application",
            version="1.0.0",
            category=sample_category,
            author="Test Author",
            license="MIT",
            created_at=now,
            updated_at=now,
        )
        assert app.long_description is None
        assert app.tags == []
        assert app.icon is None
        assert app.screenshots is None
        assert app.repository is None
        assert app.documentation is None
        assert app.status == AppStatus.AVAILABLE
        assert app.install_count is None
        assert app.rating is None
        assert app.featured is False
        assert app.connected_server_id is None

    def test_name_length_validation(self, sample_category):
        """Test name length constraints."""
        now = datetime.now(UTC).isoformat()
        with pytest.raises(ValidationError):
            App(
                id="app-123",
                name="",  # Too short
                description="A test application",
                version="1.0.0",
                category=sample_category,
                author="Test Author",
                license="MIT",
                created_at=now,
                updated_at=now,
            )

    def test_description_length_validation(self, sample_category):
        """Test description length constraints."""
        now = datetime.now(UTC).isoformat()
        with pytest.raises(ValidationError):
            App(
                id="app-123",
                name="Test App",
                description="",  # Too short
                version="1.0.0",
                category=sample_category,
                author="Test Author",
                license="MIT",
                created_at=now,
                updated_at=now,
            )

    def test_rating_validation(self, sample_category):
        """Test rating range validation."""
        now = datetime.now(UTC).isoformat()
        # Valid rating
        app = App(
            id="app-123",
            name="Test App",
            description="A test application",
            version="1.0.0",
            category=sample_category,
            author="Test Author",
            license="MIT",
            created_at=now,
            updated_at=now,
            rating=4.5,
        )
        assert app.rating == 4.5

        # Invalid rating (> 5)
        with pytest.raises(ValidationError):
            App(
                id="app-123",
                name="Test App",
                description="A test application",
                version="1.0.0",
                category=sample_category,
                author="Test Author",
                license="MIT",
                created_at=now,
                updated_at=now,
                rating=6.0,
            )

    def test_from_table(self):
        """Test conversion from database tables."""
        # Mock category table
        category_row = MagicMock(spec=AppCategoryTable)
        category_row.id = "media"
        category_row.name = "Media"
        category_row.description = "Media apps"
        category_row.icon = "play"
        category_row.color = "blue"

        # Mock app table
        app_row = MagicMock(spec=ApplicationTable)
        app_row.id = "plex"
        app_row.name = "Plex"
        app_row.description = "Media server"
        app_row.long_description = "Full description"
        app_row.version = "1.0.0"
        app_row.tags = json.dumps(["media", "streaming"])
        app_row.icon = "plex-icon.png"
        app_row.screenshots = json.dumps(["screen1.png", "screen2.png"])
        app_row.author = "Plex Inc"
        app_row.repository = "https://github.com/plex"
        app_row.documentation = "https://docs.plex.tv"
        app_row.license = "MIT"
        app_row.requirements = json.dumps({"min_ram": "2GB"})
        app_row.status = "available"
        app_row.install_count = 1000
        app_row.rating = 4.5
        app_row.featured = True
        app_row.created_at = datetime(2024, 1, 1, 12, 0, 0)
        app_row.updated_at = datetime(2024, 1, 2, 12, 0, 0)
        app_row.connected_server_id = "server-123"

        app = App.from_table(app_row, category_row)
        assert app.id == "plex"
        assert app.name == "Plex"
        assert app.description == "Media server"
        assert app.long_description == "Full description"
        assert app.tags == ["media", "streaming"]
        assert app.screenshots == ["screen1.png", "screen2.png"]
        assert app.requirements.min_ram == "2GB"
        assert app.status == AppStatus.AVAILABLE
        assert app.install_count == 1000
        assert app.rating == 4.5
        assert app.featured is True
        assert app.connected_server_id == "server-123"

    def test_from_table_empty_json_fields(self):
        """Test conversion handles empty JSON fields."""
        category_row = MagicMock(spec=AppCategoryTable)
        category_row.id = "media"
        category_row.name = "Media"
        category_row.description = "Media apps"
        category_row.icon = "play"
        category_row.color = "blue"

        app_row = MagicMock(spec=ApplicationTable)
        app_row.id = "app-123"
        app_row.name = "Test"
        app_row.description = "Test app"
        app_row.long_description = None
        app_row.version = "1.0.0"
        app_row.tags = None
        app_row.icon = None
        app_row.screenshots = None
        app_row.author = "Author"
        app_row.repository = None
        app_row.documentation = None
        app_row.license = "MIT"
        app_row.requirements = None
        app_row.status = "available"
        app_row.install_count = None
        app_row.rating = None
        app_row.featured = False
        app_row.created_at = datetime(2024, 1, 1)
        app_row.updated_at = datetime(2024, 1, 1)
        app_row.connected_server_id = None

        app = App.from_table(app_row, category_row)
        assert app.tags == []
        assert app.screenshots is None
        assert app.requirements.min_ram is None

    def test_to_table_model(self, sample_app):
        """Test conversion to database table."""
        table = sample_app.to_table_model()
        assert table.id == "plex"
        assert table.name == "Plex"
        assert table.description == "Media server"
        assert table.version == "1.0.0"
        assert table.category_id == "media"
        assert table.author == "Plex Inc"
        assert table.license == "MIT"
        assert table.status == "available"

    def test_to_table_model_with_json_fields(self, sample_category):
        """Test JSON field serialization."""
        now = datetime.now(UTC).isoformat()
        app = App(
            id="app-123",
            name="Test App",
            description="A test application",
            version="1.0.0",
            category=sample_category,
            author="Test Author",
            license="MIT",
            created_at=now,
            updated_at=now,
            tags=["tag1", "tag2"],
            screenshots=["screen1.png"],
            requirements=AppRequirements(min_ram="4GB"),
        )
        table = app.to_table_model()
        assert json.loads(table.tags) == ["tag1", "tag2"]
        assert json.loads(table.screenshots) == ["screen1.png"]
        assert json.loads(table.requirements)["min_ram"] == "4GB"

    def test_serialize_datetime(self):
        """Test datetime serialization."""
        dt = datetime(2024, 1, 15, 10, 30, 45, 123456)
        result = App._serialize_datetime(dt)
        assert result == "2024-01-15T10:30:45"  # microseconds removed

    def test_serialize_datetime_none(self):
        """Test datetime serialization with None."""
        result = App._serialize_datetime(None)
        # Should return current time
        assert "T" in result

    def test_parse_datetime(self):
        """Test datetime parsing."""
        result = App._parse_datetime("2024-01-15T10:30:45")
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 10
        assert result.minute == 30
        assert result.second == 45

    def test_parse_datetime_with_z_suffix(self):
        """Test datetime parsing with Z suffix."""
        result = App._parse_datetime("2024-01-15T10:30:45Z")
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15


class TestAppInstallation:
    """Tests for AppInstallation model."""

    def test_required_fields(self):
        """Test required fields."""
        now = datetime.now(UTC).isoformat()
        install = AppInstallation(
            app_id="app-123",
            status=AppStatus.INSTALLED,
            version="1.0.0",
            installed_at=now,
        )
        assert install.app_id == "app-123"
        assert install.status == AppStatus.INSTALLED
        assert install.version == "1.0.0"
        assert install.installed_at == now

    def test_default_values(self):
        """Test default values."""
        now = datetime.now(UTC).isoformat()
        install = AppInstallation(
            app_id="app-123",
            status=AppStatus.INSTALLED,
            version="1.0.0",
            installed_at=now,
        )
        assert install.last_updated is None
        assert install.config is None
        assert install.logs is None

    def test_all_fields(self):
        """Test all fields populated."""
        now = datetime.now(UTC).isoformat()
        install = AppInstallation(
            app_id="app-123",
            status=AppStatus.INSTALLED,
            version="1.0.0",
            installed_at=now,
            last_updated=now,
            config={"port": 8080},
            logs=["Installing...", "Done"],
        )
        assert install.config == {"port": 8080}
        assert install.logs == ["Installing...", "Done"]


class TestAppFilter:
    """Tests for AppFilter model."""

    def test_default_values(self):
        """Test default values."""
        filter = AppFilter()
        assert filter.category is None
        assert filter.tags is None
        assert filter.status is None
        assert filter.search is None
        assert filter.featured is None
        assert filter.sort_by == "name"
        assert filter.sort_order == "asc"

    def test_custom_values(self):
        """Test custom filter values."""
        filter = AppFilter(
            category="media",
            tags=["streaming", "video"],
            status=AppStatus.AVAILABLE,
            search="plex",
            featured=True,
            sort_by="rating",
            sort_order="desc",
        )
        assert filter.category == "media"
        assert filter.tags == ["streaming", "video"]
        assert filter.status == AppStatus.AVAILABLE
        assert filter.search == "plex"
        assert filter.featured is True
        assert filter.sort_by == "rating"
        assert filter.sort_order == "desc"


class TestAppSearchResult:
    """Tests for AppSearchResult model."""

    def test_required_fields(self, sample_app_fixture):
        """Test required fields."""
        filter = AppFilter()
        result = AppSearchResult(
            apps=[sample_app_fixture],
            total=1,
            page=1,
            limit=10,
            filters=filter,
        )
        assert len(result.apps) == 1
        assert result.total == 1
        assert result.page == 1
        assert result.limit == 10
        assert result.filters == filter

    def test_empty_results(self):
        """Test empty search results."""
        filter = AppFilter(search="nonexistent")
        result = AppSearchResult(
            apps=[],
            total=0,
            page=1,
            limit=10,
            filters=filter,
        )
        assert result.apps == []
        assert result.total == 0


@pytest.fixture
def sample_app_fixture():
    """Global fixture for sample app."""
    category = AppCategory(
        id="media",
        name="Media",
        description="Media apps",
        icon="play",
        color="blue",
    )
    now = datetime.now(UTC).isoformat()
    return App(
        id="plex",
        name="Plex",
        description="Media server",
        version="1.0.0",
        category=category,
        author="Plex Inc",
        license="MIT",
        created_at=now,
        updated_at=now,
    )
