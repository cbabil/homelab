"""
Unit tests for services/agent_packager.py

Tests for packaging agent code for remote deployment.
"""

import base64
import tarfile
import tempfile
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

import pytest

from services.agent_packager import AgentPackager, AGENT_SOURCE_DIR


class TestAgentPackagerInit:
    """Tests for AgentPackager initialization."""

    def test_init_with_default_agent_dir(self):
        """Should use AGENT_SOURCE_DIR when no agent_dir provided."""
        packager = AgentPackager()

        assert packager.agent_dir == AGENT_SOURCE_DIR

    def test_init_with_custom_agent_dir(self):
        """Should use provided agent_dir."""
        custom_dir = Path("/custom/agent/dir")
        packager = AgentPackager(agent_dir=custom_dir)

        assert packager.agent_dir == custom_dir

    def test_init_with_none_uses_default(self):
        """Should use default when None is explicitly passed."""
        packager = AgentPackager(agent_dir=None)

        assert packager.agent_dir == AGENT_SOURCE_DIR


class TestAgentPackagerGetVersion:
    """Tests for get_version method."""

    def test_get_version_from_init_file(self):
        """Should extract version from __init__.py."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_dir = Path(tmpdir)
            src_dir = agent_dir / "src"
            src_dir.mkdir()
            init_file = src_dir / "__init__.py"
            init_file.write_text('__version__ = "1.2.3"\n')

            packager = AgentPackager(agent_dir=agent_dir)
            version = packager.get_version()

            assert version == "1.2.3"

    def test_get_version_with_single_quotes(self):
        """Should handle single-quoted version string."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_dir = Path(tmpdir)
            src_dir = agent_dir / "src"
            src_dir.mkdir()
            init_file = src_dir / "__init__.py"
            init_file.write_text("__version__ = '2.0.0'\n")

            packager = AgentPackager(agent_dir=agent_dir)
            version = packager.get_version()

            assert version == "2.0.0"

    def test_get_version_with_other_content(self):
        """Should find version among other content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_dir = Path(tmpdir)
            src_dir = agent_dir / "src"
            src_dir.mkdir()
            init_file = src_dir / "__init__.py"
            init_file.write_text(
                '"""Agent module."""\n'
                '__author__ = "Test"\n'
                '__version__ = "3.1.4"\n'
                "__all__ = []\n"
            )

            packager = AgentPackager(agent_dir=agent_dir)
            version = packager.get_version()

            assert version == "3.1.4"

    def test_get_version_no_init_file(self):
        """Should return 'dev' when __init__.py doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_dir = Path(tmpdir)
            (agent_dir / "src").mkdir()

            packager = AgentPackager(agent_dir=agent_dir)
            version = packager.get_version()

            assert version == "dev"

    def test_get_version_no_src_dir(self):
        """Should return 'dev' when src directory doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_dir = Path(tmpdir)

            packager = AgentPackager(agent_dir=agent_dir)
            version = packager.get_version()

            assert version == "dev"

    def test_get_version_no_version_in_file(self):
        """Should return 'dev' when no __version__ in file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_dir = Path(tmpdir)
            src_dir = agent_dir / "src"
            src_dir.mkdir()
            init_file = src_dir / "__init__.py"
            init_file.write_text('"""No version here."""\n')

            packager = AgentPackager(agent_dir=agent_dir)
            version = packager.get_version()

            assert version == "dev"


class TestAgentPackagerPackage:
    """Tests for package method."""

    def test_package_creates_base64_tarball(self):
        """Should create base64-encoded tarball."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_dir = Path(tmpdir)
            src_dir = agent_dir / "src"
            src_dir.mkdir()
            (src_dir / "__init__.py").write_text('__version__ = "1.0.0"')
            (src_dir / "main.py").write_text("print('hello')")

            packager = AgentPackager(agent_dir=agent_dir)
            encoded = packager.package()

            # Should be valid base64
            decoded = base64.b64decode(encoded)

            # Should be valid tarball
            buffer = BytesIO(decoded)
            with tarfile.open(fileobj=buffer, mode="r:gz") as tar:
                names = tar.getnames()
                assert "src/__init__.py" in names
                assert "src/main.py" in names

    def test_package_raises_on_missing_directory(self):
        """Should raise FileNotFoundError for non-existent directory."""
        packager = AgentPackager(agent_dir=Path("/nonexistent/agent/dir"))

        with pytest.raises(FileNotFoundError) as exc_info:
            packager.package()

        assert "Agent directory not found" in str(exc_info.value)

    def test_package_excludes_pycache(self):
        """Should exclude __pycache__ directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_dir = Path(tmpdir)
            src_dir = agent_dir / "src"
            src_dir.mkdir()
            (src_dir / "__init__.py").write_text("")

            # Create __pycache__ with a file
            pycache = src_dir / "__pycache__"
            pycache.mkdir()
            (pycache / "cached.pyc").write_text("cached")

            packager = AgentPackager(agent_dir=agent_dir)
            encoded = packager.package()

            decoded = base64.b64decode(encoded)
            buffer = BytesIO(decoded)
            with tarfile.open(fileobj=buffer, mode="r:gz") as tar:
                names = tar.getnames()
                assert not any("__pycache__" in name for name in names)

    def test_package_excludes_pyc_files(self):
        """Should exclude .pyc files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_dir = Path(tmpdir)
            src_dir = agent_dir / "src"
            src_dir.mkdir()
            (src_dir / "__init__.py").write_text("")
            (src_dir / "module.pyc").write_text("compiled")

            packager = AgentPackager(agent_dir=agent_dir)
            encoded = packager.package()

            decoded = base64.b64decode(encoded)
            buffer = BytesIO(decoded)
            with tarfile.open(fileobj=buffer, mode="r:gz") as tar:
                names = tar.getnames()
                assert not any(name.endswith(".pyc") for name in names)

    def test_package_excludes_dotfiles(self):
        """Should exclude files starting with dot."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_dir = Path(tmpdir)
            src_dir = agent_dir / "src"
            src_dir.mkdir()
            (src_dir / "__init__.py").write_text("")
            (src_dir / ".hidden").write_text("secret")
            (src_dir / ".gitignore").write_text("*.pyc")

            packager = AgentPackager(agent_dir=agent_dir)
            encoded = packager.package()

            decoded = base64.b64decode(encoded)
            buffer = BytesIO(decoded)
            with tarfile.open(fileobj=buffer, mode="r:gz") as tar:
                names = tar.getnames()
                assert not any(
                    Path(name).name.startswith(".") for name in names
                )

    def test_package_includes_nested_directories(self):
        """Should include files from nested directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_dir = Path(tmpdir)
            src_dir = agent_dir / "src"
            nested_dir = src_dir / "utils" / "helpers"
            nested_dir.mkdir(parents=True)
            (nested_dir / "helper.py").write_text("def help(): pass")

            packager = AgentPackager(agent_dir=agent_dir)
            encoded = packager.package()

            decoded = base64.b64decode(encoded)
            buffer = BytesIO(decoded)
            with tarfile.open(fileobj=buffer, mode="r:gz") as tar:
                names = tar.getnames()
                assert "src/utils/helpers/helper.py" in names

    def test_package_logs_info(self):
        """Should log packaging information."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_dir = Path(tmpdir)
            src_dir = agent_dir / "src"
            src_dir.mkdir()
            (src_dir / "__init__.py").write_text('__version__ = "1.0.0"')

            packager = AgentPackager(agent_dir=agent_dir)

            with patch("services.agent_packager.logger") as mock_logger:
                packager.package()

                mock_logger.info.assert_called_once()
                call_kwargs = mock_logger.info.call_args[1]
                assert call_kwargs["version"] == "1.0.0"
                assert "size_bytes" in call_kwargs
                assert "encoded_size" in call_kwargs


class TestAgentPackagerGetFileList:
    """Tests for get_file_list method."""

    def test_get_file_list_returns_sorted_files(self):
        """Should return sorted list of files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_dir = Path(tmpdir)
            src_dir = agent_dir / "src"
            src_dir.mkdir()
            (src_dir / "zebra.py").write_text("")
            (src_dir / "alpha.py").write_text("")
            (src_dir / "middle.py").write_text("")

            packager = AgentPackager(agent_dir=agent_dir)
            files = packager.get_file_list()

            assert files == ["src/alpha.py", "src/middle.py", "src/zebra.py"]

    def test_get_file_list_excludes_pycache(self):
        """Should exclude __pycache__ directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_dir = Path(tmpdir)
            src_dir = agent_dir / "src"
            src_dir.mkdir()
            (src_dir / "main.py").write_text("")

            pycache = src_dir / "__pycache__"
            pycache.mkdir()
            (pycache / "main.cpython-311.pyc").write_text("")

            packager = AgentPackager(agent_dir=agent_dir)
            files = packager.get_file_list()

            assert not any("__pycache__" in f for f in files)

    def test_get_file_list_excludes_pyc_files(self):
        """Should exclude .pyc files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_dir = Path(tmpdir)
            src_dir = agent_dir / "src"
            src_dir.mkdir()
            (src_dir / "main.py").write_text("")
            (src_dir / "main.pyc").write_text("")

            packager = AgentPackager(agent_dir=agent_dir)
            files = packager.get_file_list()

            assert "src/main.py" in files
            assert "src/main.pyc" not in files

    def test_get_file_list_excludes_dotfiles(self):
        """Should exclude files starting with dot."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_dir = Path(tmpdir)
            src_dir = agent_dir / "src"
            src_dir.mkdir()
            (src_dir / "main.py").write_text("")
            (src_dir / ".env").write_text("")
            (src_dir / ".gitignore").write_text("")

            packager = AgentPackager(agent_dir=agent_dir)
            files = packager.get_file_list()

            assert "src/main.py" in files
            assert not any(Path(f).name.startswith(".") for f in files)

    def test_get_file_list_includes_nested_files(self):
        """Should include files from nested directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_dir = Path(tmpdir)
            src_dir = agent_dir / "src"
            utils_dir = src_dir / "utils"
            utils_dir.mkdir(parents=True)
            (utils_dir / "helper.py").write_text("")

            packager = AgentPackager(agent_dir=agent_dir)
            files = packager.get_file_list()

            assert "src/utils/helper.py" in files

    def test_get_file_list_empty_directory(self):
        """Should return empty list for empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_dir = Path(tmpdir)

            packager = AgentPackager(agent_dir=agent_dir)
            files = packager.get_file_list()

            assert files == []
