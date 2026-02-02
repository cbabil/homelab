"""
Unit tests for lib/tool_loader.py

Tests dynamic MCP tool discovery and registration.
"""

import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock, patch, PropertyMock
import pytest

from lib.tool_loader import (
    SRC_ROOT,
    DEFAULT_TOOLS_DIRECTORY,
    DEFAULT_TOOLS_PACKAGE,
    _resolve_tools_path,
    _discover_tool_packages,
    _find_tools_class,
    _instantiate_tools_class,
    _get_public_methods,
    register_all_tools,
)


class TestConstants:
    """Tests for module constants."""

    def test_src_root_is_path(self):
        """SRC_ROOT should be a Path."""
        assert isinstance(SRC_ROOT, Path)

    def test_src_root_is_absolute(self):
        """SRC_ROOT should be absolute."""
        assert SRC_ROOT.is_absolute()

    def test_default_tools_directory_is_path(self):
        """DEFAULT_TOOLS_DIRECTORY should be a Path."""
        assert isinstance(DEFAULT_TOOLS_DIRECTORY, Path)

    def test_default_tools_package_is_string(self):
        """DEFAULT_TOOLS_PACKAGE should be 'tools'."""
        assert DEFAULT_TOOLS_PACKAGE == "tools"


class TestResolveToolsPath:
    """Tests for _resolve_tools_path function."""

    def test_resolve_none_returns_default(self):
        """Should return DEFAULT_TOOLS_DIRECTORY for None."""
        result = _resolve_tools_path(None)
        assert result == DEFAULT_TOOLS_DIRECTORY

    def test_resolve_empty_returns_default(self):
        """Should return DEFAULT_TOOLS_DIRECTORY for empty string."""
        result = _resolve_tools_path("")
        assert result == DEFAULT_TOOLS_DIRECTORY

    def test_resolve_absolute_path(self, tmp_path):
        """Should return absolute path as-is."""
        result = _resolve_tools_path(str(tmp_path))
        assert result == tmp_path

    def test_resolve_relative_path(self):
        """Should resolve relative path from SRC_ROOT."""
        result = _resolve_tools_path("custom_tools")
        expected = (SRC_ROOT / "custom_tools").resolve()
        assert result == expected


class TestDiscoverToolPackages:
    """Tests for _discover_tool_packages function."""

    def test_discover_valid_packages(self, tmp_path):
        """Should discover packages with __init__.py."""
        # Create package structure
        (tmp_path / "auth").mkdir()
        (tmp_path / "auth" / "__init__.py").touch()
        (tmp_path / "server").mkdir()
        (tmp_path / "server" / "__init__.py").touch()

        result = _discover_tool_packages(tmp_path)
        assert "auth" in result
        assert "server" in result

    def test_discover_ignores_underscore_dirs(self, tmp_path):
        """Should ignore directories starting with underscore."""
        (tmp_path / "_private").mkdir()
        (tmp_path / "_private" / "__init__.py").touch()
        (tmp_path / "public").mkdir()
        (tmp_path / "public" / "__init__.py").touch()

        result = _discover_tool_packages(tmp_path)
        assert "_private" not in result
        assert "public" in result

    def test_discover_ignores_dirs_without_init(self, tmp_path):
        """Should ignore directories without __init__.py."""
        (tmp_path / "no_init").mkdir()
        (tmp_path / "with_init").mkdir()
        (tmp_path / "with_init" / "__init__.py").touch()

        result = _discover_tool_packages(tmp_path)
        assert "no_init" not in result
        assert "with_init" in result

    def test_discover_ignores_files(self, tmp_path):
        """Should ignore files, only look at directories."""
        (tmp_path / "not_a_dir.py").touch()
        (tmp_path / "valid_pkg").mkdir()
        (tmp_path / "valid_pkg" / "__init__.py").touch()

        result = _discover_tool_packages(tmp_path)
        assert "not_a_dir.py" not in result
        assert "valid_pkg" in result

    def test_discover_returns_sorted(self, tmp_path):
        """Should return sorted package names."""
        for name in ["zebra", "alpha", "middle"]:
            (tmp_path / name).mkdir()
            (tmp_path / name / "__init__.py").touch()

        result = _discover_tool_packages(tmp_path)
        assert result == sorted(result)

    def test_discover_nonexistent_raises(self, tmp_path):
        """Should raise FileNotFoundError for nonexistent directory."""
        nonexistent = tmp_path / "does_not_exist"
        with pytest.raises(FileNotFoundError) as exc_info:
            _discover_tool_packages(nonexistent)
        assert "not found" in str(exc_info.value).lower()

    def test_discover_empty_directory(self, tmp_path):
        """Should return empty list for empty directory."""
        result = _discover_tool_packages(tmp_path)
        assert result == []


class TestFindToolsClass:
    """Tests for _find_tools_class function."""

    def test_find_tools_class_success(self):
        """Should find *Tools class in module."""
        # Create a mock module with a Tools class
        module = ModuleType("test_module")
        module.__name__ = "test_module"

        class AuthTools:
            pass

        AuthTools.__module__ = "test_module"
        module.AuthTools = AuthTools

        result = _find_tools_class(module)
        assert result is not None
        assert result[0] == "AuthTools"
        assert result[1] is AuthTools

    def test_find_tools_class_none_found(self):
        """Should return None if no *Tools class found."""
        module = ModuleType("test_module")
        module.__name__ = "test_module"

        class NotAToolsClass:
            pass

        NotAToolsClass.__module__ = "test_module"
        module.NotAToolsClass = NotAToolsClass

        result = _find_tools_class(module)
        assert result is None

    def test_find_tools_class_ignores_imported(self):
        """Should ignore Tools classes from other modules."""
        module = ModuleType("test_module")
        module.__name__ = "test_module"

        class ImportedTools:
            pass

        ImportedTools.__module__ = "other_module"  # Different module
        module.ImportedTools = ImportedTools

        result = _find_tools_class(module)
        assert result is None


class TestInstantiateToolsClass:
    """Tests for _instantiate_tools_class function."""

    def test_instantiate_no_deps(self):
        """Should instantiate class with no dependencies."""
        class SimpleTools:
            def __init__(self):
                self.initialized = True

        result = _instantiate_tools_class(SimpleTools, "SimpleTools", {})
        assert result.initialized is True

    def test_instantiate_with_deps(self):
        """Should instantiate class with dependencies."""
        class ServiceTools:
            def __init__(self, auth_service, db_service):
                self.auth = auth_service
                self.db = db_service

        mock_auth = MagicMock()
        mock_db = MagicMock()
        deps = {"auth_service": mock_auth, "db_service": mock_db}

        result = _instantiate_tools_class(ServiceTools, "ServiceTools", deps)
        assert result.auth is mock_auth
        assert result.db is mock_db

    def test_instantiate_with_defaults(self):
        """Should use default values when not in dependencies."""
        class OptionalTools:
            def __init__(self, required, optional="default_value"):
                self.required = required
                self.optional = optional

        deps = {"required": "provided"}
        result = _instantiate_tools_class(OptionalTools, "OptionalTools", deps)
        assert result.required == "provided"
        assert result.optional == "default_value"

    def test_instantiate_override_defaults(self):
        """Should override defaults when in dependencies."""
        class OptionalTools:
            def __init__(self, value="default"):
                self.value = value

        deps = {"value": "overridden"}
        result = _instantiate_tools_class(OptionalTools, "OptionalTools", deps)
        assert result.value == "overridden"

    def test_instantiate_missing_required_raises(self):
        """Should raise KeyError for missing required dependency."""
        class RequiredTools:
            def __init__(self, required_service):
                self.service = required_service

        with pytest.raises(KeyError) as exc_info:
            _instantiate_tools_class(RequiredTools, "RequiredTools", {})
        assert "required_service" in str(exc_info.value)
        assert "RequiredTools" in str(exc_info.value)


class TestGetPublicMethods:
    """Tests for _get_public_methods function."""

    def test_get_public_methods_returns_methods(self):
        """Should return public methods."""
        class ToolsClass:
            def public_method(self):
                pass

            def another_public(self):
                pass

        instance = ToolsClass()
        result = _get_public_methods(instance)

        method_names = [name for name, _ in result]
        assert "public_method" in method_names
        assert "another_public" in method_names

    def test_get_public_methods_ignores_private(self):
        """Should ignore methods starting with underscore."""
        class ToolsClass:
            def public_method(self):
                pass

            def _private_method(self):
                pass

            def __dunder_method__(self):
                pass

        instance = ToolsClass()
        result = _get_public_methods(instance)

        method_names = [name for name, _ in result]
        assert "public_method" in method_names
        assert "_private_method" not in method_names
        assert "__dunder_method__" not in method_names

    def test_get_public_methods_ignores_attributes(self):
        """Should ignore non-method attributes."""
        class ToolsClass:
            def __init__(self):
                self.attribute = "value"
                self.another_attr = 42

            def real_method(self):
                pass

        instance = ToolsClass()
        result = _get_public_methods(instance)

        method_names = [name for name, _ in result]
        assert "real_method" in method_names
        assert "attribute" not in method_names
        assert "another_attr" not in method_names

    def test_get_public_methods_empty_class(self):
        """Should return empty list for class with no public methods."""
        class EmptyTools:
            def _private_only(self):
                pass

        instance = EmptyTools()
        result = _get_public_methods(instance)
        assert result == []


class TestRegisterAllTools:
    """Tests for register_all_tools function."""

    @pytest.fixture
    def mock_app(self):
        """Create mock FastMCP app."""
        app = MagicMock()
        app.tool = MagicMock()
        return app

    @pytest.fixture
    def temp_tools_dir(self, tmp_path):
        """Create temporary tools directory structure."""
        tools_dir = tmp_path / "tools"
        tools_dir.mkdir()

        # Create a valid tool package
        auth_dir = tools_dir / "auth"
        auth_dir.mkdir()
        (auth_dir / "__init__.py").touch()
        (auth_dir / "tools.py").write_text("""
class AuthTools:
    def __init__(self, auth_service):
        self.auth = auth_service

    def login(self):
        pass

    def logout(self):
        pass
""")
        return tools_dir

    def test_register_no_packages(self, mock_app, tmp_path):
        """Should handle empty tools directory."""
        tools_dir = tmp_path / "empty_tools"
        tools_dir.mkdir()

        config = {"tools_directory": str(tools_dir)}
        register_all_tools(mock_app, config, {})

        # No tools registered
        mock_app.tool.assert_not_called()

    def test_register_import_failure(self, mock_app, tmp_path):
        """Should skip modules that fail to import."""
        tools_dir = tmp_path / "tools"
        tools_dir.mkdir()
        bad_pkg = tools_dir / "bad"
        bad_pkg.mkdir()
        (bad_pkg / "__init__.py").touch()
        # No tools.py - will fail import

        config = {"tools_directory": str(tools_dir), "tools_package": "nonexistent"}
        # Should not raise, just skip
        register_all_tools(mock_app, config, {})

    def test_register_missing_dependency(self, mock_app, tmp_path):
        """Should skip classes with missing dependencies."""
        tools_dir = tmp_path / "tools"
        tools_dir.mkdir()
        pkg = tools_dir / "needs_dep"
        pkg.mkdir()
        (pkg / "__init__.py").touch()
        (pkg / "tools.py").touch()

        class NeedsDepTools:
            def __init__(self, required_service):
                self.service = required_service

            def method(self):
                pass

        NeedsDepTools.__module__ = "tools.needs_dep.tools"

        mock_module = MagicMock()
        mock_module.__name__ = "tools.needs_dep.tools"
        mock_module.NeedsDepTools = NeedsDepTools

        with patch("lib.tool_loader.importlib.import_module", return_value=mock_module):
            config = {"tools_directory": str(tools_dir), "tools_package": "tools"}
            # Should not raise, just skip
            register_all_tools(mock_app, config, {})
            # No tools registered due to missing dependency
            mock_app.tool.assert_not_called()

    def test_register_no_tools_class(self, mock_app, tmp_path):
        """Should skip modules without *Tools class."""
        tools_dir = tmp_path / "tools"
        tools_dir.mkdir()
        pkg = tools_dir / "no_class"
        pkg.mkdir()
        (pkg / "__init__.py").touch()
        (pkg / "tools.py").touch()

        # Mock module without *Tools class
        mock_module = MagicMock()
        mock_module.__name__ = "tools.no_class.tools"

        # No class ending in 'Tools'
        class NotTools:
            pass

        NotTools.__module__ = "other_module"
        mock_module.NotTools = NotTools

        with patch("lib.tool_loader.importlib.import_module", return_value=mock_module):
            config = {"tools_directory": str(tools_dir), "tools_package": "tools"}
            register_all_tools(mock_app, config, {})
            # No tools registered
            mock_app.tool.assert_not_called()

    def test_register_instantiation_error(self, mock_app, tmp_path):
        """Should raise on non-KeyError instantiation failures."""
        tools_dir = tmp_path / "tools"
        tools_dir.mkdir()
        pkg = tools_dir / "broken"
        pkg.mkdir()
        (pkg / "__init__.py").touch()
        (pkg / "tools.py").touch()

        # Mock the import and class behavior
        class BrokenTools:
            def __init__(self):
                raise RuntimeError("Instantiation failed")

        BrokenTools.__module__ = "tools.broken.tools"

        mock_module = MagicMock()
        mock_module.__name__ = "tools.broken.tools"
        mock_module.BrokenTools = BrokenTools

        with patch("lib.tool_loader.importlib.import_module", return_value=mock_module):
            config = {"tools_directory": str(tools_dir), "tools_package": "tools"}
            with pytest.raises(RuntimeError) as exc_info:
                register_all_tools(mock_app, config, {})
            assert "Instantiation failed" in str(exc_info.value)

    def test_register_tool_registration_error(self, mock_app, tmp_path):
        """Should raise on tool registration failures."""
        tools_dir = tmp_path / "tools"
        tools_dir.mkdir()
        pkg = tools_dir / "valid"
        pkg.mkdir()
        (pkg / "__init__.py").touch()
        (pkg / "tools.py").touch()

        class ValidTools:
            def __init__(self):
                pass

            def method(self):
                pass

        ValidTools.__module__ = "tools.valid.tools"

        mock_module = MagicMock()
        mock_module.__name__ = "tools.valid.tools"
        mock_module.ValidTools = ValidTools

        # Make app.tool raise
        mock_app.tool.side_effect = ValueError("Registration failed")

        with patch("lib.tool_loader.importlib.import_module", return_value=mock_module):
            config = {"tools_directory": str(tools_dir), "tools_package": "tools"}
            with pytest.raises(ValueError) as exc_info:
                register_all_tools(mock_app, config, {})
            assert "Registration failed" in str(exc_info.value)

    def test_register_successful(self, mock_app, tmp_path):
        """Should successfully register tools."""
        tools_dir = tmp_path / "tools"
        tools_dir.mkdir()
        pkg = tools_dir / "simple"
        pkg.mkdir()
        (pkg / "__init__.py").touch()
        (pkg / "tools.py").touch()

        class SimpleTools:
            def __init__(self):
                pass

            def tool_one(self):
                pass

            def tool_two(self):
                pass

        SimpleTools.__module__ = "tools.simple.tools"

        mock_module = MagicMock()
        mock_module.__name__ = "tools.simple.tools"
        mock_module.SimpleTools = SimpleTools

        with patch("lib.tool_loader.importlib.import_module", return_value=mock_module):
            config = {"tools_directory": str(tools_dir), "tools_package": "tools"}
            register_all_tools(mock_app, config, {})

            # Should have registered 2 tools
            assert mock_app.tool.call_count == 2

    def test_register_uses_default_package(self, mock_app, tmp_path):
        """Should use default tools package when not in config."""
        tools_dir = tmp_path / "tools"
        tools_dir.mkdir()

        config = {"tools_directory": str(tools_dir)}
        # Should not raise
        register_all_tools(mock_app, config, {})
