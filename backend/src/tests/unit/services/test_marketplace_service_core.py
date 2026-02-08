"""
Unit tests for services/marketplace_service.py - Core functionality.

Tests initialization, ensure_initialized, and official marketplace setup.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.marketplace import (
    MarketplaceRepoTable,
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
def mock_db_session():
    """Create mock database session with async context manager."""
    session = AsyncMock()
    context_manager = AsyncMock()
    context_manager.__aenter__.return_value = session
    context_manager.__aexit__.return_value = None
    return session, context_manager


@pytest.fixture
def mock_repo_table():
    """Create mock MarketplaceRepoTable row."""
    repo = MagicMock(spec=MarketplaceRepoTable)
    repo.id = "test-repo"
    repo.name = "Test Repo"
    repo.url = "https://github.com/test/repo"
    repo.branch = "main"
    repo.repo_type = "community"
    repo.enabled = True
    repo.status = "active"
    repo.last_synced = datetime(2024, 1, 15, tzinfo=UTC)
    repo.app_count = 10
    repo.error_message = None
    repo.created_at = datetime(2024, 1, 1, tzinfo=UTC)
    repo.updated_at = datetime(2024, 1, 15, tzinfo=UTC)
    return repo


class TestMarketplaceServiceInit:
    """Tests for MarketplaceService initialization."""

    def test_init_sets_not_initialized(self):
        """MarketplaceService should start uninitialized."""
        with patch("services.marketplace_service.logger"):
            service = MarketplaceService()
            assert service._initialized is False

    def test_init_logs_message(self):
        """MarketplaceService should log initialization."""
        with patch("services.marketplace_service.logger") as mock_logger:
            MarketplaceService()
            mock_logger.info.assert_called_once_with("Marketplace service initialized")


class TestEnsureInitialized:
    """Tests for _ensure_initialized method."""

    @pytest.mark.asyncio
    async def test_ensure_initialized_calls_init_db(self):
        """_ensure_initialized should call initialize_marketplace_database."""
        with (
            patch("services.marketplace_service.logger"),
            patch(
                "services.marketplace_service.initialize_marketplace_database"
            ) as mock_init,
        ):
            mock_init.return_value = None
            service = MarketplaceService()

            with patch.object(
                service, "_ensure_official_marketplace", new_callable=AsyncMock
            ):
                await service._ensure_initialized()

            mock_init.assert_called_once()

    @pytest.mark.asyncio
    async def test_ensure_initialized_sets_flag(self):
        """_ensure_initialized should set _initialized to True."""
        with (
            patch("services.marketplace_service.logger"),
            patch("services.marketplace_service.initialize_marketplace_database"),
        ):
            service = MarketplaceService()
            with patch.object(
                service, "_ensure_official_marketplace", new_callable=AsyncMock
            ):
                await service._ensure_initialized()
            assert service._initialized is True

    @pytest.mark.asyncio
    async def test_ensure_initialized_skips_if_already_initialized(self):
        """_ensure_initialized should skip if already initialized."""
        with (
            patch("services.marketplace_service.logger"),
            patch(
                "services.marketplace_service.initialize_marketplace_database"
            ) as mock_init,
        ):
            service = MarketplaceService()
            service._initialized = True
            await service._ensure_initialized()
            mock_init.assert_not_called()

    @pytest.mark.asyncio
    async def test_ensure_initialized_calls_ensure_official_marketplace(self):
        """_ensure_initialized should call _ensure_official_marketplace."""
        with (
            patch("services.marketplace_service.logger"),
            patch("services.marketplace_service.initialize_marketplace_database"),
        ):
            service = MarketplaceService()
            with patch.object(
                service, "_ensure_official_marketplace", new_callable=AsyncMock
            ) as mock_ensure:
                await service._ensure_initialized()
                mock_ensure.assert_called_once()


class TestEnsureOfficialMarketplace:
    """Tests for _ensure_official_marketplace method."""

    @pytest.mark.asyncio
    async def test_adds_casaos_if_not_exists(self, mock_db_session):
        """_ensure_official_marketplace should add CasaOS store if not present."""
        session, context_manager = mock_db_session

        # Simulate CasaOS not existing
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute = AsyncMock(return_value=mock_result)
        session.add = MagicMock()
        session.commit = AsyncMock()

        with (
            patch("services.marketplace_service.logger") as mock_logger,
            patch("services.marketplace_service.db_manager") as mock_db,
        ):
            mock_db.get_session.return_value = context_manager
            service = MarketplaceService()
            await service._ensure_official_marketplace()

            # Should have added repos
            assert session.add.called
            mock_logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_skips_casaos_if_exists(self, mock_db_session):
        """_ensure_official_marketplace should skip CasaOS if already present."""
        session, context_manager = mock_db_session

        # First call returns existing casaos, second returns None for official
        casaos_repo = MagicMock()
        mock_results = [
            MagicMock(scalar_one_or_none=MagicMock(return_value=casaos_repo)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),
        ]
        session.execute = AsyncMock(side_effect=mock_results)
        session.add = MagicMock()
        session.commit = AsyncMock()

        with (
            patch("services.marketplace_service.logger"),
            patch("services.marketplace_service.db_manager") as mock_db,
        ):
            mock_db.get_session.return_value = context_manager
            service = MarketplaceService()
            await service._ensure_official_marketplace()

            # Should only add official marketplace (1 call)
            assert session.add.call_count == 1

    @pytest.mark.asyncio
    async def test_handles_integrity_error_casaos(self, mock_db_session):
        """_ensure_official_marketplace should handle IntegrityError for CasaOS."""
        from sqlalchemy.exc import IntegrityError

        session, context_manager = mock_db_session
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute = AsyncMock(return_value=mock_result)
        session.add = MagicMock()
        session.commit = AsyncMock(side_effect=[IntegrityError("", None, None), None])
        session.rollback = AsyncMock()

        with (
            patch("services.marketplace_service.logger") as mock_logger,
            patch("services.marketplace_service.db_manager") as mock_db,
        ):
            mock_db.get_session.return_value = context_manager
            service = MarketplaceService()
            await service._ensure_official_marketplace()

            session.rollback.assert_called()
            mock_logger.debug.assert_called()

    @pytest.mark.asyncio
    async def test_handles_integrity_error_official(self, mock_db_session):
        """_ensure_official_marketplace should handle IntegrityError for official."""
        from sqlalchemy.exc import IntegrityError

        session, context_manager = mock_db_session

        # First check returns existing casaos, second returns None for official
        casaos_repo = MagicMock()
        mock_results = [
            MagicMock(scalar_one_or_none=MagicMock(return_value=casaos_repo)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),
        ]
        session.execute = AsyncMock(side_effect=mock_results)
        session.add = MagicMock()
        # Commit fails with IntegrityError for official marketplace
        session.commit = AsyncMock(side_effect=IntegrityError("", None, None))
        session.rollback = AsyncMock()

        with (
            patch("services.marketplace_service.logger") as mock_logger,
            patch("services.marketplace_service.db_manager") as mock_db,
        ):
            mock_db.get_session.return_value = context_manager
            service = MarketplaceService()
            await service._ensure_official_marketplace()

            session.rollback.assert_called()
            mock_logger.debug.assert_called_with("Official marketplace already exists")


class TestRepoFromTable:
    """Tests for _repo_from_table static method."""

    def test_converts_repo_table_to_model(self, mock_repo_table):
        """_repo_from_table should convert table row to model."""
        result = MarketplaceService._repo_from_table(mock_repo_table)

        assert result.id == "test-repo"
        assert result.name == "Test Repo"
        assert result.url == "https://github.com/test/repo"
        assert result.branch == "main"
        assert result.repo_type == RepoType.COMMUNITY
        assert result.enabled is True
        assert result.status == RepoStatus.ACTIVE
        assert result.app_count == 10
        assert result.error_message is None

    def test_converts_repo_type_enum(self, mock_repo_table):
        """_repo_from_table should properly convert repo_type string to enum."""
        mock_repo_table.repo_type = "official"
        result = MarketplaceService._repo_from_table(mock_repo_table)
        assert result.repo_type == RepoType.OFFICIAL

        mock_repo_table.repo_type = "personal"
        result = MarketplaceService._repo_from_table(mock_repo_table)
        assert result.repo_type == RepoType.PERSONAL

    def test_converts_status_enum(self, mock_repo_table):
        """_repo_from_table should properly convert status string to enum."""
        mock_repo_table.status = "syncing"
        result = MarketplaceService._repo_from_table(mock_repo_table)
        assert result.status == RepoStatus.SYNCING

        mock_repo_table.status = "error"
        result = MarketplaceService._repo_from_table(mock_repo_table)
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
