"""
Unit tests for services/marketplace_service.py - Repository operations.

Tests add_repo, get_repos, get_repo, remove_repo, and toggle_repo methods.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.marketplace import (
    MarketplaceRepoTable,
    RepoStatus,
    RepoType,
)
from services.marketplace_service import MarketplaceService


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


@pytest.fixture
def service_with_mocks(mock_db_session):
    """Create MarketplaceService with mocked dependencies."""
    _, context_manager = mock_db_session

    with (
        patch("services.marketplace_service.logger"),
        patch("services.marketplace_service.db_manager") as mock_db,
        patch("services.marketplace_service.initialize_marketplace_database"),
    ):
        mock_db.get_session.return_value = context_manager
        service = MarketplaceService()
        service._initialized = True  # Skip initialization
        yield service, mock_db, context_manager


class TestAddRepo:
    """Tests for add_repo method."""

    @pytest.mark.asyncio
    async def test_add_repo_creates_repository(self, mock_db_session):
        """add_repo should create a new repository."""
        session, context_manager = mock_db_session
        session.add = MagicMock()
        session.flush = AsyncMock()

        with (
            patch("services.marketplace_service.logger") as mock_logger,
            patch("services.marketplace_service.db_manager") as mock_db,
            patch("services.marketplace_service.initialize_marketplace_database"),
        ):
            mock_db.get_session.return_value = context_manager
            service = MarketplaceService()
            service._initialized = True

            result = await service.add_repo(
                name="My Repo",
                url="https://github.com/user/repo",
                repo_type=RepoType.COMMUNITY,
                branch="main",
            )

            assert result.name == "My Repo"
            assert result.url == "https://github.com/user/repo"
            assert result.repo_type == RepoType.COMMUNITY
            assert result.branch == "main"
            assert result.enabled is True
            assert result.status == RepoStatus.ACTIVE
            session.add.assert_called_once()
            mock_logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_add_repo_generates_unique_id(self, mock_db_session):
        """add_repo should generate a unique repo ID."""
        session, context_manager = mock_db_session
        session.add = MagicMock()
        session.flush = AsyncMock()

        with (
            patch("services.marketplace_service.logger"),
            patch("services.marketplace_service.db_manager") as mock_db,
            patch("services.marketplace_service.initialize_marketplace_database"),
        ):
            mock_db.get_session.return_value = context_manager
            service = MarketplaceService()
            service._initialized = True

            result = await service.add_repo(
                name="My Repo",
                url="https://github.com/user/repo",
                repo_type=RepoType.PERSONAL,
            )

            assert result.id is not None
            assert len(result.id) == 8  # uuid.uuid4().hex[:8]

    @pytest.mark.asyncio
    async def test_add_repo_with_custom_branch(self, mock_db_session):
        """add_repo should respect custom branch parameter."""
        session, context_manager = mock_db_session
        session.add = MagicMock()
        session.flush = AsyncMock()

        with (
            patch("services.marketplace_service.logger"),
            patch("services.marketplace_service.db_manager") as mock_db,
            patch("services.marketplace_service.initialize_marketplace_database"),
        ):
            mock_db.get_session.return_value = context_manager
            service = MarketplaceService()
            service._initialized = True

            result = await service.add_repo(
                name="My Repo",
                url="https://github.com/user/repo",
                repo_type=RepoType.COMMUNITY,
                branch="develop",
            )

            assert result.branch == "develop"


class TestGetRepos:
    """Tests for get_repos method."""

    @pytest.mark.asyncio
    async def test_get_repos_returns_all(self, mock_db_session, mock_repo_table):
        """get_repos should return all repositories."""
        session, context_manager = mock_db_session
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_repo_table]
        session.execute = AsyncMock(return_value=mock_result)

        with (
            patch("services.marketplace_service.logger") as mock_logger,
            patch("services.marketplace_service.db_manager") as mock_db,
            patch("services.marketplace_service.initialize_marketplace_database"),
        ):
            mock_db.get_session.return_value = context_manager
            service = MarketplaceService()
            service._initialized = True

            result = await service.get_repos()

            assert len(result) == 1
            assert result[0].id == "test-repo"
            mock_logger.debug.assert_called_with(
                "Fetched repositories", count=1, enabled_only=False
            )

    @pytest.mark.asyncio
    async def test_get_repos_enabled_only(self, mock_db_session, mock_repo_table):
        """get_repos should filter enabled repos when requested."""
        session, context_manager = mock_db_session
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_repo_table]
        session.execute = AsyncMock(return_value=mock_result)

        with (
            patch("services.marketplace_service.logger") as mock_logger,
            patch("services.marketplace_service.db_manager") as mock_db,
            patch("services.marketplace_service.initialize_marketplace_database"),
        ):
            mock_db.get_session.return_value = context_manager
            service = MarketplaceService()
            service._initialized = True

            result = await service.get_repos(enabled_only=True)

            assert len(result) == 1
            mock_logger.debug.assert_called_with(
                "Fetched repositories", count=1, enabled_only=True
            )

    @pytest.mark.asyncio
    async def test_get_repos_returns_empty_list(self, mock_db_session):
        """get_repos should return empty list when no repos exist."""
        session, context_manager = mock_db_session
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=mock_result)

        with (
            patch("services.marketplace_service.logger"),
            patch("services.marketplace_service.db_manager") as mock_db,
            patch("services.marketplace_service.initialize_marketplace_database"),
        ):
            mock_db.get_session.return_value = context_manager
            service = MarketplaceService()
            service._initialized = True

            result = await service.get_repos()

            assert result == []


class TestGetRepo:
    """Tests for get_repo method."""

    @pytest.mark.asyncio
    async def test_get_repo_returns_repo(self, mock_db_session, mock_repo_table):
        """get_repo should return repository when found."""
        session, context_manager = mock_db_session
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_repo_table
        session.execute = AsyncMock(return_value=mock_result)

        with (
            patch("services.marketplace_service.logger") as mock_logger,
            patch("services.marketplace_service.db_manager") as mock_db,
            patch("services.marketplace_service.initialize_marketplace_database"),
        ):
            mock_db.get_session.return_value = context_manager
            service = MarketplaceService()
            service._initialized = True

            result = await service.get_repo("test-repo")

            assert result is not None
            assert result.id == "test-repo"
            mock_logger.debug.assert_called_with(
                "Retrieved repository", repo_id="test-repo"
            )

    @pytest.mark.asyncio
    async def test_get_repo_returns_none_when_not_found(self, mock_db_session):
        """get_repo should return None when repository not found."""
        session, context_manager = mock_db_session
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute = AsyncMock(return_value=mock_result)

        with (
            patch("services.marketplace_service.logger") as mock_logger,
            patch("services.marketplace_service.db_manager") as mock_db,
            patch("services.marketplace_service.initialize_marketplace_database"),
        ):
            mock_db.get_session.return_value = context_manager
            service = MarketplaceService()
            service._initialized = True

            result = await service.get_repo("nonexistent")

            assert result is None
            mock_logger.warning.assert_called_with(
                "Repository not found", repo_id="nonexistent"
            )


class TestRemoveRepo:
    """Tests for remove_repo method."""

    @pytest.mark.asyncio
    async def test_remove_repo_deletes_repo_and_apps(self, mock_db_session):
        """remove_repo should delete repository and associated apps."""
        session, context_manager = mock_db_session
        mock_result = MagicMock()
        mock_result.rowcount = 1
        session.execute = AsyncMock(return_value=mock_result)

        with (
            patch("services.marketplace_service.logger") as mock_logger,
            patch("services.marketplace_service.db_manager") as mock_db,
            patch("services.marketplace_service.initialize_marketplace_database"),
        ):
            mock_db.get_session.return_value = context_manager
            service = MarketplaceService()
            service._initialized = True

            result = await service.remove_repo("test-repo")

            assert result is True
            # Should be called twice: once for apps, once for repo
            assert session.execute.call_count == 2
            mock_logger.info.assert_called_with(
                "Repository removed", repo_id="test-repo"
            )

    @pytest.mark.asyncio
    async def test_remove_repo_returns_false_when_not_found(self, mock_db_session):
        """remove_repo should return False when repository not found."""
        session, context_manager = mock_db_session
        mock_result = MagicMock()
        mock_result.rowcount = 0
        session.execute = AsyncMock(return_value=mock_result)

        with (
            patch("services.marketplace_service.logger") as mock_logger,
            patch("services.marketplace_service.db_manager") as mock_db,
            patch("services.marketplace_service.initialize_marketplace_database"),
        ):
            mock_db.get_session.return_value = context_manager
            service = MarketplaceService()
            service._initialized = True

            result = await service.remove_repo("nonexistent")

            assert result is False
            mock_logger.warning.assert_called_with(
                "Repository not found for removal", repo_id="nonexistent"
            )


class TestToggleRepo:
    """Tests for toggle_repo method."""

    @pytest.mark.asyncio
    async def test_toggle_repo_enables_repository(self, mock_db_session):
        """toggle_repo should enable repository."""
        session, context_manager = mock_db_session
        mock_result = MagicMock()
        mock_result.rowcount = 1
        session.execute = AsyncMock(return_value=mock_result)

        with (
            patch("services.marketplace_service.logger") as mock_logger,
            patch("services.marketplace_service.db_manager") as mock_db,
            patch("services.marketplace_service.initialize_marketplace_database"),
        ):
            mock_db.get_session.return_value = context_manager
            service = MarketplaceService()
            service._initialized = True

            result = await service.toggle_repo("test-repo", enabled=True)

            assert result is True
            mock_logger.info.assert_called_with(
                "Repository enabled", repo_id="test-repo"
            )

    @pytest.mark.asyncio
    async def test_toggle_repo_disables_repository(self, mock_db_session):
        """toggle_repo should disable repository."""
        session, context_manager = mock_db_session
        mock_result = MagicMock()
        mock_result.rowcount = 1
        session.execute = AsyncMock(return_value=mock_result)

        with (
            patch("services.marketplace_service.logger") as mock_logger,
            patch("services.marketplace_service.db_manager") as mock_db,
            patch("services.marketplace_service.initialize_marketplace_database"),
        ):
            mock_db.get_session.return_value = context_manager
            service = MarketplaceService()
            service._initialized = True

            result = await service.toggle_repo("test-repo", enabled=False)

            assert result is True
            mock_logger.info.assert_called_with(
                "Repository disabled", repo_id="test-repo"
            )

    @pytest.mark.asyncio
    async def test_toggle_repo_returns_false_when_not_found(self, mock_db_session):
        """toggle_repo should return False when repository not found."""
        session, context_manager = mock_db_session
        mock_result = MagicMock()
        mock_result.rowcount = 0
        session.execute = AsyncMock(return_value=mock_result)

        with (
            patch("services.marketplace_service.logger") as mock_logger,
            patch("services.marketplace_service.db_manager") as mock_db,
            patch("services.marketplace_service.initialize_marketplace_database"),
        ):
            mock_db.get_session.return_value = context_manager
            service = MarketplaceService()
            service._initialized = True

            result = await service.toggle_repo("nonexistent", enabled=True)

            assert result is False
            mock_logger.warning.assert_called_with(
                "Repository not found for toggle", repo_id="nonexistent"
            )
