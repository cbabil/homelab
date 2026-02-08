"""
Unit tests for services/agent_packager.py

Tests agent packaging functionality for remote deployment.
"""

import base64
import io
import tarfile
from unittest.mock import patch

import pytest

from services.agent_packager import AGENT_SOURCE_DIR, AgentPackager


class TestAgentPackagerInit:
    """Tests for AgentPackager initialization."""

    def test_init_default_agent_dir(self):
        """AgentPackager should use default AGENT_SOURCE_DIR."""
        packager = AgentPackager()
        assert packager.agent_dir == AGENT_SOURCE_DIR

    def test_init_custom_agent_dir(self, tmp_path):
        """AgentPackager should accept custom agent directory."""
        custom_dir = tmp_path / "custom_agent"
        custom_dir.mkdir()
        packager = AgentPackager(agent_dir=custom_dir)
        assert packager.agent_dir == custom_dir


class TestGetVersion:
    """Tests for get_version method."""

    def test_get_version_from_init_file(self, tmp_path):
        """get_version should extract version from __init__.py."""
        agent_dir = tmp_path / "agent"
        src_dir = agent_dir / "src"
        src_dir.mkdir(parents=True)
        init_file = src_dir / "__init__.py"
        init_file.write_text('__version__ = "1.2.3"\n')

        packager = AgentPackager(agent_dir=agent_dir)
        assert packager.get_version() == "1.2.3"

    def test_get_version_double_quotes(self, tmp_path):
        """get_version should handle double-quoted version."""
        agent_dir = tmp_path / "agent"
        src_dir = agent_dir / "src"
        src_dir.mkdir(parents=True)
        init_file = src_dir / "__init__.py"
        init_file.write_text('__version__ = "2.0.0"')

        packager = AgentPackager(agent_dir=agent_dir)
        assert packager.get_version() == "2.0.0"

    def test_get_version_single_quotes(self, tmp_path):
        """get_version should handle single-quoted version."""
        agent_dir = tmp_path / "agent"
        src_dir = agent_dir / "src"
        src_dir.mkdir(parents=True)
        init_file = src_dir / "__init__.py"
        init_file.write_text("__version__ = '3.0.0'")

        packager = AgentPackager(agent_dir=agent_dir)
        assert packager.get_version() == "3.0.0"

    def test_get_version_with_other_content(self, tmp_path):
        """get_version should find version among other content."""
        agent_dir = tmp_path / "agent"
        src_dir = agent_dir / "src"
        src_dir.mkdir(parents=True)
        init_file = src_dir / "__init__.py"
        init_file.write_text('''"""Agent package."""
__author__ = "Test"
__version__ = "4.5.6"
__all__ = ["main"]
''')

        packager = AgentPackager(agent_dir=agent_dir)
        assert packager.get_version() == "4.5.6"

    def test_get_version_no_init_file(self, tmp_path):
        """get_version should return 'dev' if no __init__.py."""
        agent_dir = tmp_path / "agent"
        agent_dir.mkdir()

        packager = AgentPackager(agent_dir=agent_dir)
        assert packager.get_version() == "dev"

    def test_get_version_no_version_line(self, tmp_path):
        """get_version should return 'dev' if no version in file."""
        agent_dir = tmp_path / "agent"
        src_dir = agent_dir / "src"
        src_dir.mkdir(parents=True)
        init_file = src_dir / "__init__.py"
        init_file.write_text('"""Empty module."""\n')

        packager = AgentPackager(agent_dir=agent_dir)
        assert packager.get_version() == "dev"


class TestPackage:
    """Tests for package method."""

    def test_package_creates_base64_tarball(self, tmp_path):
        """package should return base64-encoded tarball."""
        agent_dir = tmp_path / "agent"
        agent_dir.mkdir()
        (agent_dir / "main.py").write_text("print('hello')")

        packager = AgentPackager(agent_dir=agent_dir)
        result = packager.package()

        # Verify it's valid base64
        decoded = base64.b64decode(result)
        # Verify it's a valid tarball
        buffer = io.BytesIO(decoded)
        with tarfile.open(fileobj=buffer, mode="r:gz") as tar:
            names = tar.getnames()
            assert "main.py" in names

    def test_package_includes_files(self, tmp_path):
        """package should include all non-excluded files."""
        agent_dir = tmp_path / "agent"
        src_dir = agent_dir / "src"
        src_dir.mkdir(parents=True)
        (agent_dir / "main.py").write_text("main")
        (src_dir / "module.py").write_text("module")

        packager = AgentPackager(agent_dir=agent_dir)
        result = packager.package()

        decoded = base64.b64decode(result)
        buffer = io.BytesIO(decoded)
        with tarfile.open(fileobj=buffer, mode="r:gz") as tar:
            names = tar.getnames()
            assert "main.py" in names
            assert "src/module.py" in names

    def test_package_skips_pycache(self, tmp_path):
        """package should skip __pycache__ directories."""
        agent_dir = tmp_path / "agent"
        cache_dir = agent_dir / "__pycache__"
        cache_dir.mkdir(parents=True)
        (agent_dir / "main.py").write_text("main")
        (cache_dir / "main.cpython-312.pyc").write_bytes(b"cached")

        packager = AgentPackager(agent_dir=agent_dir)
        result = packager.package()

        decoded = base64.b64decode(result)
        buffer = io.BytesIO(decoded)
        with tarfile.open(fileobj=buffer, mode="r:gz") as tar:
            names = tar.getnames()
            assert "main.py" in names
            assert not any("__pycache__" in n for n in names)

    def test_package_skips_pyc_files(self, tmp_path):
        """package should skip .pyc files."""
        agent_dir = tmp_path / "agent"
        agent_dir.mkdir()
        (agent_dir / "main.py").write_text("main")
        (agent_dir / "compiled.pyc").write_bytes(b"bytecode")

        packager = AgentPackager(agent_dir=agent_dir)
        result = packager.package()

        decoded = base64.b64decode(result)
        buffer = io.BytesIO(decoded)
        with tarfile.open(fileobj=buffer, mode="r:gz") as tar:
            names = tar.getnames()
            assert "main.py" in names
            assert "compiled.pyc" not in names

    def test_package_skips_dotfiles(self, tmp_path):
        """package should skip files starting with dot."""
        agent_dir = tmp_path / "agent"
        agent_dir.mkdir()
        (agent_dir / "main.py").write_text("main")
        (agent_dir / ".gitignore").write_text("*.pyc")
        (agent_dir / ".env").write_text("SECRET=123")

        packager = AgentPackager(agent_dir=agent_dir)
        result = packager.package()

        decoded = base64.b64decode(result)
        buffer = io.BytesIO(decoded)
        with tarfile.open(fileobj=buffer, mode="r:gz") as tar:
            names = tar.getnames()
            assert "main.py" in names
            assert ".gitignore" not in names
            assert ".env" not in names

    def test_package_raises_if_dir_not_found(self, tmp_path):
        """package should raise FileNotFoundError if directory missing."""
        missing_dir = tmp_path / "nonexistent"
        packager = AgentPackager(agent_dir=missing_dir)

        with pytest.raises(FileNotFoundError) as exc_info:
            packager.package()
        assert "nonexistent" in str(exc_info.value)

    def test_package_logs_info(self, tmp_path):
        """package should log package info."""
        agent_dir = tmp_path / "agent"
        agent_dir.mkdir()
        (agent_dir / "main.py").write_text("print('hello')")

        packager = AgentPackager(agent_dir=agent_dir)

        with patch("services.agent_packager.logger") as mock_logger:
            packager.package()
            mock_logger.info.assert_called_once()
            call_kwargs = mock_logger.info.call_args.kwargs
            assert "version" in call_kwargs
            assert "size_bytes" in call_kwargs
            assert "encoded_size" in call_kwargs


class TestGetFileList:
    """Tests for get_file_list method."""

    def test_get_file_list_returns_sorted(self, tmp_path):
        """get_file_list should return sorted file list."""
        agent_dir = tmp_path / "agent"
        agent_dir.mkdir()
        (agent_dir / "zebra.py").write_text("z")
        (agent_dir / "alpha.py").write_text("a")
        (agent_dir / "main.py").write_text("m")

        packager = AgentPackager(agent_dir=agent_dir)
        files = packager.get_file_list()

        assert files == ["alpha.py", "main.py", "zebra.py"]

    def test_get_file_list_includes_subdirectories(self, tmp_path):
        """get_file_list should include files from subdirectories."""
        agent_dir = tmp_path / "agent"
        src_dir = agent_dir / "src"
        src_dir.mkdir(parents=True)
        (agent_dir / "main.py").write_text("main")
        (src_dir / "module.py").write_text("module")

        packager = AgentPackager(agent_dir=agent_dir)
        files = packager.get_file_list()

        assert "main.py" in files
        assert "src/module.py" in files

    def test_get_file_list_skips_pycache(self, tmp_path):
        """get_file_list should skip __pycache__ directories."""
        agent_dir = tmp_path / "agent"
        cache_dir = agent_dir / "__pycache__"
        cache_dir.mkdir(parents=True)
        (agent_dir / "main.py").write_text("main")
        (cache_dir / "main.cpython-312.pyc").write_bytes(b"cached")

        packager = AgentPackager(agent_dir=agent_dir)
        files = packager.get_file_list()

        assert "main.py" in files
        assert not any("__pycache__" in f for f in files)

    def test_get_file_list_skips_pyc_files(self, tmp_path):
        """get_file_list should skip .pyc files."""
        agent_dir = tmp_path / "agent"
        agent_dir.mkdir()
        (agent_dir / "main.py").write_text("main")
        (agent_dir / "compiled.pyc").write_bytes(b"bytecode")

        packager = AgentPackager(agent_dir=agent_dir)
        files = packager.get_file_list()

        assert "main.py" in files
        assert "compiled.pyc" not in files

    def test_get_file_list_skips_dotfiles(self, tmp_path):
        """get_file_list should skip files starting with dot."""
        agent_dir = tmp_path / "agent"
        agent_dir.mkdir()
        (agent_dir / "main.py").write_text("main")
        (agent_dir / ".gitignore").write_text("*.pyc")

        packager = AgentPackager(agent_dir=agent_dir)
        files = packager.get_file_list()

        assert "main.py" in files
        assert ".gitignore" not in files

    def test_get_file_list_empty_dir(self, tmp_path):
        """get_file_list should return empty list for empty directory."""
        agent_dir = tmp_path / "agent"
        agent_dir.mkdir()

        packager = AgentPackager(agent_dir=agent_dir)
        files = packager.get_file_list()

        assert files == []
