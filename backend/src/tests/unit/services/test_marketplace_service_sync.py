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
        "last_synced": None,
        "app_count": 0,
        "error_message": None,
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
    }
    row.update(overrides)
    return row


class TestSyncRepo:
    """Tests for sync_repo method."""

    @pytest.mark.asyncio
    async def test_sync_repo_raises_for_nonexistent_repo(self, mock_db_conn):
        """sync_repo should raise ValueError if repository not found."""
        mock_conn, mock_aiosqlite = mock_db_conn
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = None
        mock_aiosqlite.execute.return_value = mock_cursor

        with patch("services.marketplace_service.logger"):
            service = MarketplaceService(connection=mock_conn)
            service._initialized = True

            with pytest.raises(
                ValueError, match="Repository nonexistent not found"
            ):
                await service.sync_repo("nonexistent")

    @pytest.mark.asyncio
    async def test_sync_repo_updates_status_to_syncing(self, mock_db_conn):
        """sync_repo should update status to SYNCING at start."""
        mock_conn, mock_aiosqlite = mock_db_conn
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = make_repo_row()
        mock_aiosqlite.execute.return_value = mock_cursor

        mock_git_sync = MagicMock()
        mock_git_sync.find_app_files.return_value = []
        mock_git_sync.cleanup = MagicMock()

        with (
            patch("services.marketplace_service.logger"),
            patch(
                "services.marketplace_service.GitSync",
                return_value=mock_git_sync,
            ),
        ):
            service = MarketplaceService(connection=mock_conn)
            service._initialized = True

            # Use local path to skip git clone
            await service.sync_repo("test-repo", local_path=Path("/tmp/test"))

            # Verify execute was called (includes SYNCING status update)
            assert mock_aiosqlite.execute.called

    @pytest.mark.asyncio
    async def test_sync_repo_with_local_path_skips_git(
        self, mock_db_conn, tmp_path
    ):
        """sync_repo with local_path should skip git operations."""
        mock_conn, mock_aiosqlite = mock_db_conn
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = make_repo_row()
        mock_aiosqlite.execute.return_value = mock_cursor

        mock_git_sync = MagicMock()
        mock_git_sync.clone_or_pull = MagicMock()
        mock_git_sync.find_app_files.return_value = []
        mock_git_sync.cleanup = MagicMock()

        with (
            patch("services.marketplace_service.logger"),
            patch(
                "services.marketplace_service.GitSync",
                return_value=mock_git_sync,
            ),
        ):
            service = MarketplaceService(connection=mock_conn)
            service._initialized = True

            await service.sync_repo("test-repo", local_path=tmp_path)

            # clone_or_pull should not be called
            mock_git_sync.clone_or_pull.assert_not_called()
            # cleanup should not be called either (local path)
            mock_git_sync.cleanup.assert_not_called()

    @pytest.mark.asyncio
    async def test_sync_repo_detects_casaos_format(
        self, mock_db_conn, tmp_path
    ):
        """sync_repo should detect and use CasaOS format parsing."""
        mock_conn, mock_aiosqlite = mock_db_conn
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = make_repo_row(
            id="casaos",
            name="CasaOS",
            url="https://github.com/IceWhaleTech/CasaOS-AppStore",
            repo_type="official",
        )
        mock_aiosqlite.execute.return_value = mock_cursor

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
            patch(
                "services.marketplace_service.GitSync",
                return_value=mock_git_sync,
            ),
        ):
            service = MarketplaceService(connection=mock_conn)
            service._initialized = True

            await service.sync_repo("casaos", local_path=tmp_path)

            mock_git_sync.find_casaos_app_files.assert_called_once()
            mock_logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_sync_repo_handles_error_and_updates_status(
        self, mock_db_conn, tmp_path
    ):
        """sync_repo should handle errors and update status to ERROR."""
        mock_conn, mock_aiosqlite = mock_db_conn
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = make_repo_row()
        mock_aiosqlite.execute.return_value = mock_cursor

        mock_git_sync = MagicMock()
        mock_git_sync.find_app_files.side_effect = RuntimeError("Git error")
        mock_git_sync.cleanup = MagicMock()

        with (
            patch("services.marketplace_service.logger") as mock_logger,
            patch(
                "services.marketplace_service.GitSync",
                return_value=mock_git_sync,
            ),
        ):
            service = MarketplaceService(connection=mock_conn)
            service._initialized = True

            with pytest.raises(RuntimeError, match="Git error"):
                await service.sync_repo("test-repo", local_path=tmp_path)

            mock_logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_sync_repo_with_git_clone(self, mock_db_conn):
        """sync_repo without local_path should use git clone and cleanup."""
        mock_conn, mock_aiosqlite = mock_db_conn
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = make_repo_row()
        mock_aiosqlite.execute.return_value = mock_cursor

        mock_git_sync = MagicMock()
        mock_git_sync.clone_or_pull = MagicMock(
            return_value=Path("/tmp/cloned")
        )
        mock_git_sync.find_app_files.return_value = []
        mock_git_sync.cleanup = MagicMock()

        with (
            patch("services.marketplace_service.logger"),
            patch(
                "services.marketplace_service.GitSync",
                return_value=mock_git_sync,
            ),
            patch.object(
                MarketplaceService, "_is_casaos_repo", return_value=False
            ),
        ):
            service = MarketplaceService(connection=mock_conn)
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
        self, mock_db_conn, sample_marketplace_app, tmp_path
    ):
        """sync_repo should load CasaOS apps and upsert them."""
        mock_conn, mock_aiosqlite = mock_db_conn
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = make_repo_row(
            id="casaos",
            name="CasaOS",
            url="https://github.com/IceWhaleTech/CasaOS-AppStore",
            repo_type="official",
        )
        mock_aiosqlite.execute.return_value = mock_cursor

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
            patch(
                "services.marketplace_service.GitSync",
                return_value=mock_git_sync,
            ),
        ):
            service = MarketplaceService(connection=mock_conn)
            service._initialized = True

            # Mock _upsert_app
            with patch.object(
                service, "_upsert_app", new_callable=AsyncMock
            ) as mock_upsert:
                apps = await service.sync_repo(
                    "casaos", local_path=tmp_path
                )

                # App should be loaded and upserted
                assert len(apps) == 1
                mock_upsert.assert_called_once_with(sample_marketplace_app)
                mock_logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_sync_repo_loads_legacy_apps(
        self, mock_db_conn, sample_marketplace_app, tmp_path
    ):
        """sync_repo should load legacy format apps and upsert them."""
        mock_conn, mock_aiosqlite = mock_db_conn
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = make_repo_row()
        mock_aiosqlite.execute.return_value = mock_cursor

        mock_git_sync = MagicMock()
        mock_git_sync.find_app_files.return_value = [
            Path("/tmp/apps/test/app.yaml")
        ]
        mock_git_sync.load_app_from_file.return_value = (
            sample_marketplace_app
        )
        mock_git_sync.cleanup = MagicMock()

        with (
            patch("services.marketplace_service.logger") as mock_logger,
            patch(
                "services.marketplace_service.GitSync",
                return_value=mock_git_sync,
            ),
        ):
            service = MarketplaceService(connection=mock_conn)
            service._initialized = True

            # Mock _upsert_app
            with patch.object(
                service, "_upsert_app", new_callable=AsyncMock
            ) as mock_upsert:
                apps = await service.sync_repo(
                    "test-repo", local_path=tmp_path
                )

                # App should be loaded and upserted
                assert len(apps) == 1
                mock_upsert.assert_called_once_with(sample_marketplace_app)
                mock_logger.info.assert_called()


class TestUpsertApp:
    """Tests for _upsert_app method."""

    @pytest.mark.asyncio
    async def test_upsert_app_inserts_new_app(
        self, mock_db_conn, sample_marketplace_app
    ):
        """_upsert_app should insert new app when not existing."""
        mock_conn, mock_aiosqlite = mock_db_conn
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = None
        mock_aiosqlite.execute.return_value = mock_cursor

        with patch("services.marketplace_service.logger"):
            service = MarketplaceService(connection=mock_conn)
            service._initialized = True

            await service._upsert_app(sample_marketplace_app)

            # Should call execute at least twice: SELECT check + INSERT
            assert mock_aiosqlite.execute.call_count >= 2
            mock_aiosqlite.commit.assert_called()

    @pytest.mark.asyncio
    async def test_upsert_app_updates_existing_app(
        self, mock_db_conn, sample_marketplace_app
    ):
        """_upsert_app should update existing app."""
        mock_conn, mock_aiosqlite = mock_db_conn
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = {"id": "test-app"}
        mock_aiosqlite.execute.return_value = mock_cursor

        with patch("services.marketplace_service.logger"):
            service = MarketplaceService(connection=mock_conn)
            service._initialized = True

            await service._upsert_app(sample_marketplace_app)

            # Should call execute: SELECT check + UPDATE
            assert mock_aiosqlite.execute.call_count >= 2
            mock_aiosqlite.commit.assert_called()

    @pytest.mark.asyncio
    async def test_upsert_app_serializes_json_fields(
        self, mock_db_conn, sample_marketplace_app
    ):
        """_upsert_app should properly serialize JSON fields."""
        mock_conn, mock_aiosqlite = mock_db_conn
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = None
        mock_aiosqlite.execute.return_value = mock_cursor

        with patch("services.marketplace_service.logger"):
            service = MarketplaceService(connection=mock_conn)
            service._initialized = True

            await service._upsert_app(sample_marketplace_app)

            # Verify the INSERT was called with serialized data
            # The second execute call is the INSERT
            insert_call = mock_aiosqlite.execute.call_args_list[1]
            insert_params = insert_call[0][1]

            # tags should be serialized as JSON string
            tags_json = insert_params[6]
            assert json.loads(tags_json) == ["test", "sample"]
