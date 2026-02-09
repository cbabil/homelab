"""
Unit tests for services/marketplace_service.py - Core functionality.

Tests initialization, ensure_initialized, and official marketplace setup.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.marketplace import (
    RepoStatus,
    RepoType,
)
from services.marketplace_service import (
    CASAOS_APPSTORE_BRANCH,
    CASAOS_APPSTORE_NAME,
    CASAOS_APPSTORE_URL,
    OFFICIAL_MARKETPLACE_BRANCH,
    OFFICIAL_MARKETPLACE_NAME,
    OFFICIAL_MARKETPLACE_URL,
    MarketplaceService,
)


@pytest.fixture
def mock_db_connection():
    """Create a mock DatabaseConnection with async context manager."""
    conn = AsyncMock()
    context_manager = AsyncMock()
    context_manager.__aenter__.return_value = conn
    context_manager.__aexit__.return_value = None

    mock_connection = MagicMock()
    mock_connection.get_connection.return_value = context_manager
    return mock_connection, conn


@pytest.fixture
def mock_repo_row():
    """Create a mock aiosqlite.Row for a marketplace repo."""
    row = {
        "id": "test-repo",
        "name": "Test Repo",
        "url": "https://github.com/test/repo",
        "branch": "main",
        "repo_type": "community",
        "enabled": 1,
        "status": "active",
        "last_synced": datetime(2024, 1, 15, tzinfo=UTC).isoformat(),
        "app_count": 10,
        "error_message": None,
        "created_at": datetime(2024, 1, 1, tzinfo=UTC).isoformat(),
        "updated_at": datetime(2024, 1, 15, tzinfo=UTC).isoformat(),
    }
    return row


class TestMarketplaceServiceInit:
    """Tests for MarketplaceService initialization."""

    def test_init_sets_not_initialized(self, mock_db_connection):
        """MarketplaceService should start uninitialized."""
        mock_connection, _ = mock_db_connection
        with patch("services.marketplace_service.logger"):
            service = MarketplaceService(connection=mock_connection)
            assert service._initialized is False

    def test_init_logs_message(self, mock_db_connection):
        """MarketplaceService should log initialization."""
        mock_connection, _ = mock_db_connection
        with patch("services.marketplace_service.logger") as mock_logger:
            MarketplaceService(connection=mock_connection)
            mock_logger.info.assert_called_once_with("Marketplace service initialized")


class TestEnsureInitialized:
    """Tests for _ensure_initialized method."""

    @pytest.mark.asyncio
    async def test_ensure_initialized_calls_ensure_official_marketplace(
        self, mock_db_connection
    ):
        """_ensure_initialized should call _ensure_official_marketplace."""
        mock_connection, _ = mock_db_connection
        with patch("services.marketplace_service.logger"):
            service = MarketplaceService(connection=mock_connection)
            with patch.object(
                service, "_ensure_official_marketplace", new_callable=AsyncMock
            ) as mock_ensure:
                await service._ensure_initialized()
                mock_ensure.assert_called_once()

    @pytest.mark.asyncio
    async def test_ensure_initialized_sets_flag(self, mock_db_connection):
        """_ensure_initialized should set _initialized to True."""
        mock_connection, _ = mock_db_connection
        with patch("services.marketplace_service.logger"):
            service = MarketplaceService(connection=mock_connection)
            with patch.object(
                service, "_ensure_official_marketplace", new_callable=AsyncMock
            ):
                await service._ensure_initialized()
            assert service._initialized is True

    @pytest.mark.asyncio
    async def test_ensure_initialized_skips_if_already_initialized(
        self, mock_db_connection
    ):
        """_ensure_initialized should skip if already initialized."""
        mock_connection, _ = mock_db_connection
        with patch("services.marketplace_service.logger"):
            service = MarketplaceService(connection=mock_connection)
            service._initialized = True
            with patch.object(
                service, "_ensure_official_marketplace", new_callable=AsyncMock
            ) as mock_ensure:
                await service._ensure_initialized()
                mock_ensure.assert_not_called()


class TestEnsureOfficialMarketplace:
    """Tests for _ensure_official_marketplace method."""

    @pytest.mark.asyncio
    async def test_adds_casaos_if_not_exists(self, mock_db_connection):
        """_ensure_official_marketplace should add CasaOS store if not present."""
        mock_connection, conn = mock_db_connection

        # Simulate CasaOS not existing (fetchone returns None)
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=None)
        conn.execute = AsyncMock(return_value=mock_cursor)
        conn.commit = AsyncMock()

        with patch("services.marketplace_service.logger") as mock_logger:
            service = MarketplaceService(connection=mock_connection)
            await service._ensure_official_marketplace()

            # Should have executed INSERT statements
            assert conn.execute.called
            mock_logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_skips_casaos_if_exists(self, mock_db_connection):
        """_ensure_official_marketplace should skip CasaOS if already present."""
        mock_connection, conn = mock_db_connection

        # First SELECT returns existing casaos, second SELECT returns None for official
        casaos_row = {"id": "casaos"}
        mock_cursor_casaos = AsyncMock()
        mock_cursor_casaos.fetchone = AsyncMock(return_value=casaos_row)

        mock_cursor_official = AsyncMock()
        mock_cursor_official.fetchone = AsyncMock(return_value=None)

        conn.execute = AsyncMock(
            side_effect=[mock_cursor_casaos, mock_cursor_official, AsyncMock(), AsyncMock()]
        )
        conn.commit = AsyncMock()

        with patch("services.marketplace_service.logger"):
            service = MarketplaceService(connection=mock_connection)
            await service._ensure_official_marketplace()

            # Should have added only official marketplace (the INSERT for official)
            # First call: SELECT for casaos
            # Second call: SELECT for official
            # Third call: INSERT for official
            # Fourth call: commit is separate
            assert conn.execute.call_count >= 2

    @pytest.mark.asyncio
    async def test_handles_insert_or_ignore_casaos(self, mock_db_connection):
        """_ensure_official_marketplace handles INSERT OR IGNORE for CasaOS."""
        mock_connection, conn = mock_db_connection

        # Both SELECTs return None (neither exists)
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=None)
        conn.execute = AsyncMock(return_value=mock_cursor)
        conn.commit = AsyncMock()

        with patch("services.marketplace_service.logger") as mock_logger:
            service = MarketplaceService(connection=mock_connection)
            await service._ensure_official_marketplace()

            # Should succeed without errors - INSERT OR IGNORE handles duplicates
            mock_logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_handles_insert_or_ignore_official(self, mock_db_connection):
        """_ensure_official_marketplace handles INSERT OR IGNORE for official."""
        mock_connection, conn = mock_db_connection

        # CasaOS exists, official does not
        casaos_row = {"id": "casaos"}

        call_count = 0

        async def side_effect_execute(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            mock_cursor = AsyncMock()
            if call_count == 1:
                # First SELECT: casaos exists
                mock_cursor.fetchone = AsyncMock(return_value=casaos_row)
            elif call_count == 2:
                # Second SELECT: official does not exist
                mock_cursor.fetchone = AsyncMock(return_value=None)
            else:
                # INSERT statements
                mock_cursor.fetchone = AsyncMock(return_value=None)
            return mock_cursor

        conn.execute = AsyncMock(side_effect=side_effect_execute)
        conn.commit = AsyncMock()

        with patch("services.marketplace_service.logger") as mock_logger:
            service = MarketplaceService(connection=mock_connection)
            await service._ensure_official_marketplace()

            # Should succeed - INSERT OR IGNORE handles duplicates gracefully
            mock_logger.info.assert_called()


class TestRepoFromRow:
    """Tests for _repo_from_row static method."""

    def test_converts_repo_row_to_model(self, mock_repo_row):
        """_repo_from_row should convert aiosqlite.Row to model."""
        result = MarketplaceService._repo_from_row(mock_repo_row)

        assert result.id == "test-repo"
        assert result.name == "Test Repo"
        assert result.url == "https://github.com/test/repo"
        assert result.branch == "main"
        assert result.repo_type == RepoType.COMMUNITY
        assert result.enabled is True
        assert result.status == RepoStatus.ACTIVE
        assert result.app_count == 10
        assert result.error_message is None

    def test_converts_repo_type_enum(self, mock_repo_row):
        """_repo_from_row should properly convert repo_type string to enum."""
        mock_repo_row["repo_type"] = "official"
        result = MarketplaceService._repo_from_row(mock_repo_row)
        assert result.repo_type == RepoType.OFFICIAL

        mock_repo_row["repo_type"] = "personal"
        result = MarketplaceService._repo_from_row(mock_repo_row)
        assert result.repo_type == RepoType.PERSONAL

    def test_converts_status_enum(self, mock_repo_row):
        """_repo_from_row should properly convert status string to enum."""
        mock_repo_row["status"] = "syncing"
        result = MarketplaceService._repo_from_row(mock_repo_row)
        assert result.status == RepoStatus.SYNCING

        mock_repo_row["status"] = "error"
        result = MarketplaceService._repo_from_row(mock_repo_row)
        assert result.status == RepoStatus.ERROR


class TestIsCasaosRepo:
    """Tests for _is_casaos_repo static method."""

    def test_detects_casaos_format(self, tmp_path):
        """_is_casaos_repo should return True for CasaOS format repos."""
        # Create Apps directory with docker-compose.yml
        apps_dir = tmp_path / "Apps"
        apps_dir.mkdir()
        app_dir = apps_dir / "TestApp"
        app_dir.mkdir()
        (app_dir / "docker-compose.yml").write_text("version: '3'")

        result = MarketplaceService._is_casaos_repo(tmp_path)
        assert result is True

    def test_rejects_non_casaos_format(self, tmp_path):
        """_is_casaos_repo should return False for non-CasaOS repos."""
        # Create apps directory (lowercase) with app.yaml
        apps_dir = tmp_path / "apps"
        apps_dir.mkdir()
        app_dir = apps_dir / "test-app"
        app_dir.mkdir()
        (app_dir / "app.yaml").write_text("name: test")

        result = MarketplaceService._is_casaos_repo(tmp_path)
        assert result is False

    def test_returns_false_for_empty_repo(self, tmp_path):
        """_is_casaos_repo should return False for empty repos."""
        result = MarketplaceService._is_casaos_repo(tmp_path)
        assert result is False

    def test_returns_false_for_apps_without_compose(self, tmp_path):
        """_is_casaos_repo should return False if Apps dir has no compose files."""
        apps_dir = tmp_path / "Apps"
        apps_dir.mkdir()
        app_dir = apps_dir / "TestApp"
        app_dir.mkdir()
        # No docker-compose.yml file

        result = MarketplaceService._is_casaos_repo(tmp_path)
        assert result is False


class TestMarketplaceConstants:
    """Tests for marketplace constants."""

    def test_casaos_appstore_constants(self):
        """CasaOS App Store constants should be defined correctly."""
        assert CASAOS_APPSTORE_URL == "https://github.com/IceWhaleTech/CasaOS-AppStore"
        assert CASAOS_APPSTORE_NAME == "CasaOS App Store"
        assert CASAOS_APPSTORE_BRANCH == "main"

    def test_official_marketplace_constants(self):
        """Official marketplace constants should be defined correctly."""
        assert OFFICIAL_MARKETPLACE_URL == "https://github.com/cbabil/tomo-marketplace"
        assert OFFICIAL_MARKETPLACE_NAME == "Tomo Marketplace"
        assert OFFICIAL_MARKETPLACE_BRANCH == "master"
