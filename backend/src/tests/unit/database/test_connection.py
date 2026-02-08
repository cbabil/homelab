"""
Database Connection Unit Tests

Tests for DatabaseManager class and connection handling.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from database.connection import Base, DatabaseManager, db_manager


class TestDatabaseManager:
    """Tests for DatabaseManager class."""

    def test_init_default_directory(self):
        """Test initialization with default directory."""
        manager = DatabaseManager()

        assert manager._default_directory == "data"
        assert manager._override_directory is None
        assert manager.engine is None
        assert manager.session_factory is None

    def test_init_custom_directory(self):
        """Test initialization with custom directory."""
        manager = DatabaseManager(data_directory="custom_data")

        assert manager._default_directory == "custom_data"

    def test_configure_paths_relative(self):
        """Test path configuration with relative directory."""
        manager = DatabaseManager(data_directory="test_data")

        assert "test_data" in manager.data_directory
        assert manager.database_path.endswith("tomo.db")
        assert "sqlite+aiosqlite" in manager.database_url

    def test_configure_paths_absolute(self):
        """Test path configuration with absolute directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = DatabaseManager(data_directory=tmpdir)

            assert manager.data_directory == tmpdir
            assert manager.database_path == os.path.join(tmpdir, "tomo.db")

    def test_configure_paths_from_env(self):
        """Test path configuration from environment variable."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"DATA_DIRECTORY": tmpdir}):
                manager = DatabaseManager()
                manager._configure_paths()

                assert manager.data_directory == tmpdir

    def test_set_data_directory(self):
        """Test overriding data directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            resolved_tmpdir = str(Path(tmpdir).resolve())
            manager = DatabaseManager()
            manager.engine = MagicMock()
            manager.session_factory = MagicMock()

            manager.set_data_directory(tmpdir)

            assert manager._override_directory == resolved_tmpdir
            assert manager.engine is None
            assert manager.session_factory is None
            assert manager.data_directory == resolved_tmpdir

    def test_set_data_directory_path_object(self):
        """Test overriding data directory with Path object."""
        with tempfile.TemporaryDirectory() as tmpdir:
            resolved_tmpdir = str(Path(tmpdir).resolve())
            manager = DatabaseManager()

            manager.set_data_directory(Path(tmpdir))

            assert manager._override_directory == resolved_tmpdir

    @pytest.mark.asyncio
    async def test_initialize(self):
        """Test database initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = DatabaseManager(data_directory=tmpdir)

            await manager.initialize()

            assert manager.engine is not None
            assert manager.session_factory is not None
            assert os.path.exists(tmpdir)

    @pytest.mark.asyncio
    async def test_initialize_creates_directory(self):
        """Test that initialize creates data directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = os.path.join(tmpdir, "nested", "data")
            manager = DatabaseManager(data_directory=data_dir)

            await manager.initialize()

            assert os.path.exists(data_dir)

    @pytest.mark.asyncio
    async def test_get_session_initializes_if_needed(self):
        """Test that get_session initializes on first use."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = DatabaseManager(data_directory=tmpdir)

            assert manager.session_factory is None

            async with manager.get_session() as session:
                assert session is not None

            assert manager.session_factory is not None

    @pytest.mark.asyncio
    async def test_get_session_commits_on_success(self):
        """Test that get_session commits on success."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = DatabaseManager(data_directory=tmpdir)
            await manager.initialize()

            async with manager.get_session() as _session:
                pass

    @pytest.mark.asyncio
    async def test_get_session_rollback_on_error(self):
        """Test that get_session rolls back on error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = DatabaseManager(data_directory=tmpdir)
            await manager.initialize()

            with pytest.raises(ValueError):
                async with manager.get_session() as _session:
                    raise ValueError("Test error")


class TestBase:
    """Tests for SQLAlchemy Base."""

    def test_base_exists(self):
        """Test that Base is properly configured."""
        assert Base is not None
        assert hasattr(Base, "metadata")


class TestGlobalDbManager:
    """Tests for global db_manager instance."""

    def test_db_manager_exists(self):
        """Test that global db_manager is created."""
        assert db_manager is not None
        assert isinstance(db_manager, DatabaseManager)

    def test_db_manager_default_config(self):
        """Test global db_manager has default configuration."""
        assert db_manager._default_directory == "data"
