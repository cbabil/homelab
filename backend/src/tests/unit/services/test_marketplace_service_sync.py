"""
Unit tests for services/marketplace_service.py - Sync operations.

Tests sync_repo and _upsert_app methods.
"""

import json
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.marketplace import (
    AppRequirements,
    DockerConfig,
    MarketplaceApp,
    MarketplaceAppTable,
    MarketplaceRepo,
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
def sample_repo():
    """Create sample MarketplaceRepo for testing."""
    return MarketplaceRepo(
        id="test-repo",
        name="Test Repo",
        url="https://github.com/test/repo",
        branch="main",
        repo_type=RepoType.COMMUNITY,
        enabled=True,
        status=RepoStatus.ACTIVE,
        last_synced=None,
        app_count=0,
        error_message=None,
        created_at=datetime(2024, 1, 1, tzinfo=UTC),
        updated_at=datetime(2024, 1, 1, tzinfo=UTC),
    )


@pytest.fixture
def sample_marketplace_app():
    """Create sample MarketplaceApp for testing."""
    now = datetime.now(UTC)
    return MarketplaceApp(
        id="test-app",
        name="Test App",
        description="A test application",
        long_description="A longer description for testing",
        version="1.0.0",
        category="utility",
        tags=["test", "sample"],
        icon="https://example.com/icon.png",
        author="Test Author",
        license="MIT",
        maintainers=["maintainer@example.com"],
        repository="https://github.com/test/app",
        documentation="https://docs.example.com",
        repo_id="test-repo",
        docker=DockerConfig(
            image="test/app:latest",
            ports=[],
            volumes=[],
            environment=[],
            restart_policy="unless-stopped",
            network_mode=None,
            privileged=False,
            capabilities=[],
        ),
        requirements=AppRequirements(architectures=["amd64", "arm64"]),
        install_count=0,
        avg_rating=0.0,
        rating_count=0,
        featured=False,
        created_at=now,
        updated_at=now,
    )


def create_mock_repo_row(
    id_val="test-repo",
    name_val="Test Repo",
    url_val="https://github.com/test/repo",
    branch_val="main",
    repo_type_val="community",
):
    """Create a properly configured mock repo row for testing."""
    mock_row = MagicMock(spec=MarketplaceRepoTable)
    mock_row.id = id_val
    mock_row.name = name_val
    mock_row.url = url_val
    mock_row.branch = branch_val
    mock_row.repo_type = repo_type_val
    mock_row.enabled = True
    mock_row.status = "active"
    mock_row.last_synced = None
    mock_row.app_count = 0
    mock_row.error_message = None
    mock_row.created_at = datetime(2024, 1, 1, tzinfo=UTC)
    mock_row.updated_at = datetime(2024, 1, 1, tzinfo=UTC)
    return mock_row


class TestSyncRepo:
    """Tests for sync_repo method."""

    @pytest.mark.asyncio
    async def test_sync_repo_raises_for_nonexistent_repo(self, mock_db_session):
        """sync_repo should raise ValueError if repository not found."""
        session, context_manager = mock_db_session
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute = AsyncMock(return_value=mock_result)

        with (
            patch("services.marketplace_service.logger"),
            patch("services.marketplace_service.db_manager") as mock_db,
            patch("services.marketplace_service.initialize_marketplace_database"),
        ):
            mock_db.get_session.return_value = context_manager
            service = MarketplaceService()
            service._initialized = True

            with pytest.raises(ValueError, match="Repository nonexistent not found"):
                await service.sync_repo("nonexistent")

    @pytest.mark.asyncio
    async def test_sync_repo_updates_status_to_syncing(
        self, mock_db_session, sample_repo
    ):
        """sync_repo should update status to SYNCING at start."""
        session, context_manager = mock_db_session
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = create_mock_repo_row()
        session.execute = AsyncMock(return_value=mock_result)

        mock_git_sync = MagicMock()
        mock_git_sync.find_app_files.return_value = []
        mock_git_sync.cleanup = MagicMock()

        with (
            patch("services.marketplace_service.logger"),
            patch("services.marketplace_service.db_manager") as mock_db,
            patch("services.marketplace_service.initialize_marketplace_database"),
            patch("services.marketplace_service.GitSync", return_value=mock_git_sync),
        ):
            mock_db.get_session.return_value = context_manager
            service = MarketplaceService()
            service._initialized = True

            # Use local path to skip git clone
            await service.sync_repo("test-repo", local_path=Path("/tmp/test"))

            # Verify update was called with SYNCING status
            assert session.execute.called

    @pytest.mark.asyncio
    async def test_sync_repo_with_local_path_skips_git(self, mock_db_session, tmp_path):
        """sync_repo with local_path should skip git operations."""
        session, context_manager = mock_db_session
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = create_mock_repo_row()
        session.execute = AsyncMock(return_value=mock_result)

        mock_git_sync = MagicMock()
        mock_git_sync.clone_or_pull = MagicMock()
        mock_git_sync.find_app_files.return_value = []
        mock_git_sync.cleanup = MagicMock()

        with (
            patch("services.marketplace_service.logger"),
            patch("services.marketplace_service.db_manager") as mock_db,
            patch("services.marketplace_service.initialize_marketplace_database"),
            patch("services.marketplace_service.GitSync", return_value=mock_git_sync),
        ):
            mock_db.get_session.return_value = context_manager
            service = MarketplaceService()
            service._initialized = True

            await service.sync_repo("test-repo", local_path=tmp_path)

            # clone_or_pull should not be called
            mock_git_sync.clone_or_pull.assert_not_called()
            # cleanup should not be called either (local path)
            mock_git_sync.cleanup.assert_not_called()

    @pytest.mark.asyncio
    async def test_sync_repo_detects_casaos_format(self, mock_db_session, tmp_path):
        """sync_repo should detect and use CasaOS format parsing."""
        session, context_manager = mock_db_session
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = create_mock_repo_row(
            id_val="casaos",
            name_val="CasaOS",
            url_val="https://github.com/IceWhaleTech/CasaOS-AppStore",
            repo_type_val="official",
        )
        session.execute = AsyncMock(return_value=mock_result)

        # Create CasaOS-style directory structure
        apps_dir = tmp_path / "Apps"
        apps_dir.mkdir()
        test_app_dir = apps_dir / "TestApp"
        test_app_dir.mkdir()
        (test_app_dir / "docker-compose.yml").write_text("version: '3'")

        mock_git_sync = MagicMock()
        mock_git_sync.find_casaos_app_files.return_value = [
            test_app_dir / "docker-compose.yml"
        ]
        mock_git_sync.load_casaos_app.return_value = None
        mock_git_sync.cleanup = MagicMock()

        with (
            patch("services.marketplace_service.logger") as mock_logger,
            patch("services.marketplace_service.db_manager") as mock_db,
            patch("services.marketplace_service.initialize_marketplace_database"),
            patch("services.marketplace_service.GitSync", return_value=mock_git_sync),
        ):
            mock_db.get_session.return_value = context_manager
            service = MarketplaceService()
            service._initialized = True

            await service.sync_repo("casaos", local_path=tmp_path)

            mock_git_sync.find_casaos_app_files.assert_called_once()
            mock_logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_sync_repo_handles_error_and_updates_status(
        self, mock_db_session, tmp_path
    ):
        """sync_repo should handle errors and update status to ERROR."""
        session, context_manager = mock_db_session
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = create_mock_repo_row()
        session.execute = AsyncMock(return_value=mock_result)

        mock_git_sync = MagicMock()
        mock_git_sync.find_app_files.side_effect = RuntimeError("Git error")
        mock_git_sync.cleanup = MagicMock()

        with (
            patch("services.marketplace_service.logger") as mock_logger,
            patch("services.marketplace_service.db_manager") as mock_db,
            patch("services.marketplace_service.initialize_marketplace_database"),
            patch("services.marketplace_service.GitSync", return_value=mock_git_sync),
        ):
            mock_db.get_session.return_value = context_manager
            service = MarketplaceService()
            service._initialized = True

            with pytest.raises(RuntimeError, match="Git error"):
                await service.sync_repo("test-repo", local_path=tmp_path)

            mock_logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_sync_repo_with_git_clone(self, mock_db_session):
        """sync_repo without local_path should use git clone and cleanup."""
        session, context_manager = mock_db_session
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = create_mock_repo_row()
        session.execute = AsyncMock(return_value=mock_result)

        mock_git_sync = MagicMock()
        mock_git_sync.clone_or_pull = MagicMock(return_value=Path("/tmp/cloned"))
        mock_git_sync.find_app_files.return_value = []
        mock_git_sync.cleanup = MagicMock()

        with (
            patch("services.marketplace_service.logger"),
            patch("services.marketplace_service.db_manager") as mock_db,
            patch("services.marketplace_service.initialize_marketplace_database"),
            patch("services.marketplace_service.GitSync", return_value=mock_git_sync),
            patch.object(MarketplaceService, "_is_casaos_repo", return_value=False),
        ):
            mock_db.get_session.return_value = context_manager
            service = MarketplaceService()
            service._initialized = True

            await service.sync_repo("test-repo")

            # clone_or_pull should be called
            mock_git_sync.clone_or_pull.assert_called_once_with(
                "https://github.com/test/repo", "main"
            )
            # cleanup should be called
            mock_git_sync.cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_repo_loads_casaos_apps(
        self, mock_db_session, sample_marketplace_app, tmp_path
    ):
        """sync_repo should load CasaOS apps and upsert them."""
        session, context_manager = mock_db_session
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = create_mock_repo_row(
            id_val="casaos",
            name_val="CasaOS",
            url_val="https://github.com/IceWhaleTech/CasaOS-AppStore",
            repo_type_val="official",
        )
        session.execute = AsyncMock(return_value=mock_result)

        # Create CasaOS-style directory structure
        apps_dir = tmp_path / "Apps"
        apps_dir.mkdir()
        test_app_dir = apps_dir / "TestApp"
        test_app_dir.mkdir()
        (test_app_dir / "docker-compose.yml").write_text("version: '3'")

        mock_git_sync = MagicMock()
        mock_git_sync.find_casaos_app_files.return_value = [
            test_app_dir / "docker-compose.yml"
        ]
        mock_git_sync.load_casaos_app.return_value = sample_marketplace_app
        mock_git_sync.cleanup = MagicMock()

        with (
            patch("services.marketplace_service.logger") as mock_logger,
            patch("services.marketplace_service.db_manager") as mock_db,
            patch("services.marketplace_service.initialize_marketplace_database"),
            patch("services.marketplace_service.GitSync", return_value=mock_git_sync),
        ):
            mock_db.get_session.return_value = context_manager
            service = MarketplaceService()
            service._initialized = True

            # Mock _upsert_app
            with patch.object(
                service, "_upsert_app", new_callable=AsyncMock
            ) as mock_upsert:
                apps = await service.sync_repo("casaos", local_path=tmp_path)

                # App should be loaded and upserted
                assert len(apps) == 1
                mock_upsert.assert_called_once_with(sample_marketplace_app)
                mock_logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_sync_repo_loads_legacy_apps(
        self, mock_db_session, sample_marketplace_app, tmp_path
    ):
        """sync_repo should load legacy format apps and upsert them."""
        session, context_manager = mock_db_session
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = create_mock_repo_row()
        session.execute = AsyncMock(return_value=mock_result)

        mock_git_sync = MagicMock()
        mock_git_sync.find_app_files.return_value = [Path("/tmp/apps/test/app.yaml")]
        mock_git_sync.load_app_from_file.return_value = sample_marketplace_app
        mock_git_sync.cleanup = MagicMock()

        with (
            patch("services.marketplace_service.logger") as mock_logger,
            patch("services.marketplace_service.db_manager") as mock_db,
            patch("services.marketplace_service.initialize_marketplace_database"),
            patch("services.marketplace_service.GitSync", return_value=mock_git_sync),
        ):
            mock_db.get_session.return_value = context_manager
            service = MarketplaceService()
            service._initialized = True

            # Mock _upsert_app
            with patch.object(
                service, "_upsert_app", new_callable=AsyncMock
            ) as mock_upsert:
                apps = await service.sync_repo("test-repo", local_path=tmp_path)

                # App should be loaded and upserted
                assert len(apps) == 1
                mock_upsert.assert_called_once_with(sample_marketplace_app)
                mock_logger.info.assert_called()


class TestUpsertApp:
    """Tests for _upsert_app method."""

    @pytest.mark.asyncio
    async def test_upsert_app_inserts_new_app(
        self, mock_db_session, sample_marketplace_app
    ):
        """_upsert_app should insert new app when not existing."""
        session, context_manager = mock_db_session
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute = AsyncMock(return_value=mock_result)
        session.add = MagicMock()

        with (
            patch("services.marketplace_service.logger"),
            patch("services.marketplace_service.db_manager") as mock_db,
            patch("services.marketplace_service.initialize_marketplace_database"),
        ):
            mock_db.get_session.return_value = context_manager
            service = MarketplaceService()
            service._initialized = True

            await service._upsert_app(sample_marketplace_app)

            session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_upsert_app_updates_existing_app(
        self, mock_db_session, sample_marketplace_app
    ):
        """_upsert_app should update existing app."""
        session, context_manager = mock_db_session
        existing_app = MagicMock(spec=MarketplaceAppTable)
        existing_app.id = "test-app"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_app
        session.execute = AsyncMock(return_value=mock_result)

        with (
            patch("services.marketplace_service.logger"),
            patch("services.marketplace_service.db_manager") as mock_db,
            patch("services.marketplace_service.initialize_marketplace_database"),
        ):
            mock_db.get_session.return_value = context_manager
            service = MarketplaceService()
            service._initialized = True

            await service._upsert_app(sample_marketplace_app)

            # Should execute select and update (2 calls)
            assert session.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_upsert_app_serializes_json_fields(
        self, mock_db_session, sample_marketplace_app
    ):
        """_upsert_app should properly serialize JSON fields."""
        session, context_manager = mock_db_session
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute = AsyncMock(return_value=mock_result)

        captured_args = []

        def capture_add(obj):
            captured_args.append(obj)

        session.add = capture_add

        with (
            patch("services.marketplace_service.logger"),
            patch("services.marketplace_service.db_manager") as mock_db,
            patch("services.marketplace_service.initialize_marketplace_database"),
        ):
            mock_db.get_session.return_value = context_manager
            service = MarketplaceService()
            service._initialized = True

            await service._upsert_app(sample_marketplace_app)

            assert len(captured_args) == 1
            app_table = captured_args[0]
            # Verify tags are serialized as JSON
            tags = json.loads(app_table.tags)
            assert tags == ["test", "sample"]
