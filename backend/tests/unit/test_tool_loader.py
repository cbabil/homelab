"""
Unit tests for lib/tool_loader.py

Tests for tool discovery, loading, and registration utilities.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from lib.tool_loader import (
    _resolve_tools_path,
    _discover_tool_packages,
    _find_tools_class,
    _instantiate_tools_class,
    _get_public_methods,
    DEFAULT_TOOLS_DIRECTORY,
    SRC_ROOT,
)


class TestResolveToolsPath:
    """Tests for _resolve_tools_path function."""

    def test_resolve_tools_path_returns_default_when_none(self):
        """Should return default tools directory when None passed."""
        result = _resolve_tools_path(None)

        assert result == DEFAULT_TOOLS_DIRECTORY

    def test_resolve_tools_path_returns_default_when_empty(self):
        """Should return default tools directory when empty string passed."""
        result = _resolve_tools_path("")

        assert result == DEFAULT_TOOLS_DIRECTORY

    def test_resolve_tools_path_handles_absolute_path(self):
        """Should return resolved absolute path."""
        result = _resolve_tools_path("/absolute/path/to/tools")

        assert result == Path("/absolute/path/to/tools")
        assert result.is_absolute()

    def test_resolve_tools_path_handles_relative_path(self):
        """Should resolve relative path from SRC_ROOT."""
        result = _resolve_tools_path("custom_tools")

        expected = (SRC_ROOT / "custom_tools").resolve()
        assert result == expected


class TestDiscoverToolPackages:
    """Tests for _discover_tool_packages function."""

    def test_discover_tool_packages_finds_packages(self):
        """Should find directories with __init__.py files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tools_path = Path(tmpdir)

            # Create package directories
            (tools_path / "auth").mkdir()
            (tools_path / "auth" / "__init__.py").touch()

            (tools_path / "server").mkdir()
            (tools_path / "server" / "__init__.py").touch()

            result = _discover_tool_packages(tools_path)

            assert "auth" in result
            assert "server" in result
            assert len(result) == 2

    def test_discover_tool_packages_ignores_underscore_dirs(self):
        """Should ignore directories starting with underscore."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tools_path = Path(tmpdir)

            # Create valid package
            (tools_path / "auth").mkdir()
            (tools_path / "auth" / "__init__.py").touch()

            # Create underscore directory (should be ignored)
            (tools_path / "__pycache__").mkdir()
            (tools_path / "__pycache__" / "__init__.py").touch()

            (tools_path / "_private").mkdir()
            (tools_path / "_private" / "__init__.py").touch()

            result = _discover_tool_packages(tools_path)

            assert result == ["auth"]

    def test_discover_tool_packages_ignores_dirs_without_init(self):
        """Should ignore directories without __init__.py."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tools_path = Path(tmpdir)

            # Create valid package
            (tools_path / "auth").mkdir()
            (tools_path / "auth" / "__init__.py").touch()

            # Create directory without __init__.py
            (tools_path / "no_init").mkdir()

            result = _discover_tool_packages(tools_path)

            assert result == ["auth"]

    def test_discover_tool_packages_returns_sorted(self):
        """Should return packages in sorted order."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tools_path = Path(tmpdir)

            for name in ["zebra", "alpha", "middle"]:
                (tools_path / name).mkdir()
                (tools_path / name / "__init__.py").touch()

            result = _discover_tool_packages(tools_path)

            assert result == ["alpha", "middle", "zebra"]

    def test_discover_tool_packages_raises_on_missing_dir(self):
        """Should raise FileNotFoundError for non-existent directory."""
        with pytest.raises(FileNotFoundError) as exc_info:
            _discover_tool_packages(Path("/nonexistent/path/tools"))

        assert "Tools directory not found" in str(exc_info.value)

    def test_discover_tool_packages_ignores_files(self):
        """Should only process directories, not files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tools_path = Path(tmpdir)

            # Create valid package
            (tools_path / "auth").mkdir()
            (tools_path / "auth" / "__init__.py").touch()

            # Create a file (should be ignored)
            (tools_path / "common.py").touch()

            result = _discover_tool_packages(tools_path)

            assert result == ["auth"]


class TestFindToolsClass:
    """Tests for _find_tools_class function."""

    def test_find_tools_class_finds_class_ending_with_tools(self):
        """Should find class with name ending in 'Tools'."""
        # Create mock module with Tools class
        mock_module = MagicMock()
        mock_module.__name__ = "test_module"

        class MockTools:
            pass

        MockTools.__module__ = "test_module"

        mock_module.MockTools = MockTools

        with patch("inspect.getmembers") as mock_getmembers:
            mock_getmembers.return_value = [
                ("MockTools", MockTools),
                ("OtherClass", type("OtherClass", (), {"__module__": "test_module"})),
            ]

            result = _find_tools_class(mock_module)

        assert result is not None
        assert result[0] == "MockTools"
        assert result[1] is MockTools

    def test_find_tools_class_returns_none_when_no_tools_class(self):
        """Should return None when no Tools class found."""
        mock_module = MagicMock()
        mock_module.__name__ = "test_module"

        with patch("inspect.getmembers") as mock_getmembers:
            mock_getmembers.return_value = [
                (
                    "RegularClass",
                    type("RegularClass", (), {"__module__": "test_module"}),
                ),
            ]

            result = _find_tools_class(mock_module)

        assert result is None

    def test_find_tools_class_ignores_imported_tools_class(self):
        """Should ignore Tools classes from other modules."""
        mock_module = MagicMock()
        mock_module.__name__ = "test_module"

        # Class from different module
        ImportedTools = type("ImportedTools", (), {"__module__": "other_module"})

        with patch("inspect.getmembers") as mock_getmembers:
            mock_getmembers.return_value = [
                ("ImportedTools", ImportedTools),
            ]

            result = _find_tools_class(mock_module)

        assert result is None


class TestInstantiateToolsClass:
    """Tests for _instantiate_tools_class function."""

    def test_instantiate_tools_class_with_required_deps(self):
        """Should instantiate class with required dependencies."""

        class TestTools:
            def __init__(self, db_service, auth_service):
                self.db_service = db_service
                self.auth_service = auth_service

        mock_db = MagicMock()
        mock_auth = MagicMock()
        dependencies = {"db_service": mock_db, "auth_service": mock_auth}

        result = _instantiate_tools_class(TestTools, "TestTools", dependencies)

        assert result.db_service is mock_db
        assert result.auth_service is mock_auth

    def test_instantiate_tools_class_with_optional_deps(self):
        """Should use default for optional dependencies not provided."""

        class TestTools:
            def __init__(self, required_service, optional_service=None):
                self.required_service = required_service
                self.optional_service = optional_service

        mock_required = MagicMock()
        dependencies = {"required_service": mock_required}

        result = _instantiate_tools_class(TestTools, "TestTools", dependencies)

        assert result.required_service is mock_required
        assert result.optional_service is None

    def test_instantiate_tools_class_uses_provided_optional(self):
        """Should use provided value for optional dependencies."""

        class TestTools:
            def __init__(self, required_service, optional_service=None):
                self.required_service = required_service
                self.optional_service = optional_service

        mock_required = MagicMock()
        mock_optional = MagicMock()
        dependencies = {
            "required_service": mock_required,
            "optional_service": mock_optional,
        }

        result = _instantiate_tools_class(TestTools, "TestTools", dependencies)

        assert result.optional_service is mock_optional

    def test_instantiate_tools_class_raises_on_missing_required(self):
        """Should raise KeyError when required dependency is missing."""

        class TestTools:
            def __init__(self, required_service):
                self.required_service = required_service

        with pytest.raises(KeyError) as exc_info:
            _instantiate_tools_class(TestTools, "TestTools", {})

        assert "required_service" in str(exc_info.value)
        assert "TestTools" in str(exc_info.value)


class TestGetPublicMethods:
    """Tests for _get_public_methods function."""

    def test_get_public_methods_returns_public_methods(self):
        """Should return all public methods."""

        class TestClass:
            def public_method(self):
                pass

            def another_public(self):
                pass

        instance = TestClass()
        result = _get_public_methods(instance)

        method_names = [name for name, _ in result]
        assert "public_method" in method_names
        assert "another_public" in method_names

    def test_get_public_methods_excludes_private(self):
        """Should exclude methods starting with underscore."""

        class TestClass:
            def public_method(self):
                pass

            def _private_method(self):
                pass

            def __dunder_method(self):
                pass

        instance = TestClass()
        result = _get_public_methods(instance)

        method_names = [name for name, _ in result]
        assert "public_method" in method_names
        assert "_private_method" not in method_names
        assert "__dunder_method" not in method_names

    def test_get_public_methods_excludes_attributes(self):
        """Should exclude non-method attributes."""

        class TestClass:
            def __init__(self):
                self.public_attr = "value"

            def public_method(self):
                pass

        instance = TestClass()
        result = _get_public_methods(instance)

        method_names = [name for name, _ in result]
        assert "public_method" in method_names
        assert "public_attr" not in method_names
