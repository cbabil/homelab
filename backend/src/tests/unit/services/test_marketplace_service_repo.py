"""
Unit tests for services/marketplace_service.py - Repository operations.

Tests add_repo, get_repos, get_repo, remove_repo, and toggle_repo methods.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.marketplace import (
    RepoStatus,
    RepoType,
)
from services.marketplace_service import MarketplaceService


@pytest.fixture
def mock_db_conn():
    """Create mock DatabaseConnection with async context manager."""
    mock_aiosqlite_conn = AsyncMock()
    mock_connection = MagicMock()
    ctx = AsyncMock()
    ctx.__aenter__.return_value = mock_aiosqlite_conn
    ctx.__aexit__.return_value = None
    mock_connection.get_connection.return_value = ctx
    return mock_connection, mock_aiosqlite_conn


def make_repo_row(**overrides):
    """Create a dict row for marketplace repo."""
    row = {
        "id": "test-repo",
        "name": "Test Repo",
        "url": "https://github.com/test/repo",
        "branch": "main",
        "repo_type": "community",
        "enabled": 1,
        "status": "active",
        "last_synced": "2024-01-15T00:00:00",
        "app_count": 10,
        "error_message": None,
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-15T00:00:00",
    }
    row.update(overrides)
    return row


class TestAddRepo:
    """Tests for add_repo method."""

    @pytest.mark.asyncio
    async def test_add_repo_creates_repository(self, mock_db_conn):
        """add_repo should create a new repository."""
        mock_conn, mock_aiosqlite = mock_db_conn

        # add_repo: INSERT then SELECT * WHERE id = ?
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = make_repo_row(
            name="My Repo",
            url="https://github.com/user/repo",
            repo_type="community",
            last_synced=None,
            app_count=0,
        )
        mock_aiosqlite.execute.return_value = mock_cursor
        mock_aiosqlite.commit = AsyncMock()

        with patch("services.marketplace_service.logger") as mock_logger:
            service = MarketplaceService(connection=mock_conn)
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
            mock_logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_add_repo_generates_unique_id(self, mock_db_conn):
        """add_repo should generate a unique repo ID."""
        mock_conn, mock_aiosqlite = mock_db_conn

        # Capture the INSERT params to get the generated ID
        captured_ids = []

        async def capture_execute(sql, params=None):
            if params and "INSERT" in str(sql):
                captured_ids.append(params[0])
            cursor = AsyncMock()
            cursor.fetchone.return_value = make_repo_row(
                id=captured_ids[0] if captured_ids else "abcd1234",
                name="My Repo",
                url="https://github.com/user/repo",
                repo_type="personal",
                last_synced=None,
                app_count=0,
            )
            return cursor

        mock_aiosqlite.execute = capture_execute
        mock_aiosqlite.commit = AsyncMock()

        with patch("services.marketplace_service.logger"):
            service = MarketplaceService(connection=mock_conn)
            service._initialized = True

            result = await service.add_repo(
                name="My Repo",
                url="https://github.com/user/repo",
                repo_type=RepoType.PERSONAL,
            )

            assert result.id is not None
            assert len(result.id) == 8  # uuid.uuid4().hex[:8]

    @pytest.mark.asyncio
    async def test_add_repo_with_custom_branch(self, mock_db_conn):
        """add_repo should respect custom branch parameter."""
        mock_conn, mock_aiosqlite = mock_db_conn

        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = make_repo_row(
            branch="develop",
            name="My Repo",
            url="https://github.com/user/repo",
            last_synced=None,
            app_count=0,
        )
        mock_aiosqlite.execute.return_value = mock_cursor
        mock_aiosqlite.commit = AsyncMock()

        with patch("services.marketplace_service.logger"):
            service = MarketplaceService(connection=mock_conn)
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
    async def test_get_repos_returns_all(self, mock_db_conn):
        """get_repos should return all repositories."""
        mock_conn, mock_aiosqlite = mock_db_conn
        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = [make_repo_row()]
        mock_aiosqlite.execute.return_value = mock_cursor

        with patch("services.marketplace_service.logger") as mock_logger:
            service = MarketplaceService(connection=mock_conn)
            service._initialized = True

            result = await service.get_repos()

            assert len(result) == 1
            assert result[0].id == "test-repo"
            mock_logger.debug.assert_called_with(
                "Fetched repositories", count=1, enabled_only=False
            )

    @pytest.mark.asyncio
    async def test_get_repos_enabled_only(self, mock_db_conn):
        """get_repos should filter enabled repos when requested."""
        mock_conn, mock_aiosqlite = mock_db_conn
        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = [make_repo_row()]
        mock_aiosqlite.execute.return_value = mock_cursor

        with patch("services.marketplace_service.logger") as mock_logger:
            service = MarketplaceService(connection=mock_conn)
            service._initialized = True

            result = await service.get_repos(enabled_only=True)

            assert len(result) == 1
            mock_logger.debug.assert_called_with(
                "Fetched repositories", count=1, enabled_only=True
            )

    @pytest.mark.asyncio
    async def test_get_repos_returns_empty_list(self, mock_db_conn):
        """get_repos should return empty list when no repos exist."""
        mock_conn, mock_aiosqlite = mock_db_conn
        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = []
        mock_aiosqlite.execute.return_value = mock_cursor

        with patch("services.marketplace_service.logger"):
            service = MarketplaceService(connection=mock_conn)
            service._initialized = True

            result = await service.get_repos()

            assert result == []


class TestGetRepo:
    """Tests for get_repo method."""

    @pytest.mark.asyncio
    async def test_get_repo_returns_repo(self, mock_db_conn):
        """get_repo should return repository when found."""
        mock_conn, mock_aiosqlite = mock_db_conn
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = make_repo_row()
        mock_aiosqlite.execute.return_value = mock_cursor

        with patch("services.marketplace_service.logger") as mock_logger:
            service = MarketplaceService(connection=mock_conn)
            service._initialized = True

            result = await service.get_repo("test-repo")

            assert result is not None
            assert result.id == "test-repo"
            mock_logger.debug.assert_called_with(
                "Retrieved repository", repo_id="test-repo"
            )

    @pytest.mark.asyncio
    async def test_get_repo_returns_none_when_not_found(self, mock_db_conn):
        """get_repo should return None when repository not found."""
        mock_conn, mock_aiosqlite = mock_db_conn
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = None
        mock_aiosqlite.execute.return_value = mock_cursor

        with patch("services.marketplace_service.logger") as mock_logger:
            service = MarketplaceService(connection=mock_conn)
            service._initialized = True

            result = await service.get_repo("nonexistent")

            assert result is None
            mock_logger.warning.assert_called_with(
                "Repository not found", repo_id="nonexistent"
            )


class TestRemoveRepo:
    """Tests for remove_repo method."""

    @pytest.mark.asyncio
    async def test_remove_repo_deletes_repo_and_apps(self, mock_db_conn):
        """remove_repo should delete repository and associated apps."""
        mock_conn, mock_aiosqlite = mock_db_conn

        # The last execute (DELETE repo) needs rowcount > 0
        call_count = [0]

        async def mock_execute(sql, params=None):
            call_count[0] += 1
            cursor = AsyncMock()
            cursor.rowcount = 1
            return cursor

        mock_aiosqlite.execute = mock_execute
        mock_aiosqlite.commit = AsyncMock()

        with patch("services.marketplace_service.logger") as mock_logger:
            service = MarketplaceService(connection=mock_conn)
            service._initialized = True

            result = await service.remove_repo("test-repo")

            assert result is True
            # 3 execute calls: DELETE ratings, DELETE apps, DELETE repo
            assert call_count[0] == 3
            mock_logger.info.assert_called_with(
                "Repository removed", repo_id="test-repo"
            )

    @pytest.mark.asyncio
    async def test_remove_repo_returns_false_when_not_found(
        self, mock_db_conn
    ):
        """remove_repo should return False when repository not found."""
        mock_conn, mock_aiosqlite = mock_db_conn

        async def mock_execute(sql, params=None):
            cursor = AsyncMock()
            cursor.rowcount = 0
            return cursor

        mock_aiosqlite.execute = mock_execute
        mock_aiosqlite.commit = AsyncMock()

        with patch("services.marketplace_service.logger") as mock_logger:
            service = MarketplaceService(connection=mock_conn)
            service._initialized = True

            result = await service.remove_repo("nonexistent")

            assert result is False
            mock_logger.warning.assert_called_with(
                "Repository not found for removal", repo_id="nonexistent"
            )


class TestToggleRepo:
    """Tests for toggle_repo method."""

    @pytest.mark.asyncio
    async def test_toggle_repo_enables_repository(self, mock_db_conn):
        """toggle_repo should enable repository."""
        mock_conn, mock_aiosqlite = mock_db_conn
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 1
        mock_aiosqlite.execute.return_value = mock_cursor
        mock_aiosqlite.commit = AsyncMock()

        with patch("services.marketplace_service.logger") as mock_logger:
            service = MarketplaceService(connection=mock_conn)
            service._initialized = True

            result = await service.toggle_repo("test-repo", enabled=True)

            assert result is True
            mock_logger.info.assert_called_with(
                "Repository enabled", repo_id="test-repo"
            )

    @pytest.mark.asyncio
    async def test_toggle_repo_disables_repository(self, mock_db_conn):
        """toggle_repo should disable repository."""
        mock_conn, mock_aiosqlite = mock_db_conn
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 1
        mock_aiosqlite.execute.return_value = mock_cursor
        mock_aiosqlite.commit = AsyncMock()

        with patch("services.marketplace_service.logger") as mock_logger:
            service = MarketplaceService(connection=mock_conn)
            service._initialized = True

            result = await service.toggle_repo("test-repo", enabled=False)

            assert result is True
            mock_logger.info.assert_called_with(
                "Repository disabled", repo_id="test-repo"
            )

    @pytest.mark.asyncio
    async def test_toggle_repo_returns_false_when_not_found(
        self, mock_db_conn
    ):
        """toggle_repo should return False when repository not found."""
        mock_conn, mock_aiosqlite = mock_db_conn
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 0
        mock_aiosqlite.execute.return_value = mock_cursor
        mock_aiosqlite.commit = AsyncMock()

        with patch("services.marketplace_service.logger") as mock_logger:
            service = MarketplaceService(connection=mock_conn)
            service._initialized = True

            result = await service.toggle_repo("nonexistent", enabled=True)

            assert result is False
            mock_logger.warning.assert_called_with(
                "Repository not found for toggle", repo_id="nonexistent"
            )
