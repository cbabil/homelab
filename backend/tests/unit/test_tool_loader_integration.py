"""
Unit tests for lib/tool_loader.py - register_all_tools integration tests.

Tests for the main register_all_tools function that orchestrates
tool discovery, loading, and registration.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from lib.tool_loader import (
    register_all_tools,
    DEFAULT_TOOLS_DIRECTORY,
)


class TestRegisterAllTools:
    """Tests for register_all_tools function."""

    def test_register_all_tools_empty_directory(self):
        """Should handle empty tools directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_app = MagicMock()
            config = {"tools_directory": tmpdir}
            dependencies = {}

            # Should not raise
            register_all_tools(mock_app, config, dependencies)

            # No tools registered
            assert mock_app.tool.call_count == 0

    def test_register_all_tools_uses_default_config(self):
        """Should use default tools directory when not specified."""
        mock_app = MagicMock()
        config = {}
        dependencies = {}

        with patch("lib.tool_loader._discover_tool_packages") as mock_discover:
            mock_discover.return_value = []

            register_all_tools(mock_app, config, dependencies)

            mock_discover.assert_called_once_with(DEFAULT_TOOLS_DIRECTORY)

    def test_register_all_tools_handles_import_error(self):
        """Should skip modules that fail to import."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tools_path = Path(tmpdir)

            # Create package
            (tools_path / "broken").mkdir()
            (tools_path / "broken" / "__init__.py").touch()
            (tools_path / "broken" / "tools.py").write_text("import nonexistent")

            mock_app = MagicMock()
            config = {"tools_directory": tmpdir, "tools_package": "broken_pkg"}
            dependencies = {}

            # Should not raise, just skip
            with patch("lib.tool_loader._discover_tool_packages") as mock_discover:
                mock_discover.return_value = ["broken"]

                with patch("importlib.import_module") as mock_import:
                    mock_import.side_effect = ImportError("Module not found")

                    register_all_tools(mock_app, config, dependencies)

                    assert mock_app.tool.call_count == 0

    def test_register_all_tools_handles_no_tools_class(self):
        """Should skip modules without *Tools class."""
        mock_app = MagicMock()
        config = {}
        dependencies = {}

        mock_module = MagicMock()
        mock_module.__name__ = "tools.test.tools"

        with patch("lib.tool_loader._discover_tool_packages") as mock_discover:
            mock_discover.return_value = ["test"]

            with patch("importlib.import_module") as mock_import:
                mock_import.return_value = mock_module

                with patch("lib.tool_loader._find_tools_class") as mock_find:
                    mock_find.return_value = None

                    register_all_tools(mock_app, config, dependencies)

                    assert mock_app.tool.call_count == 0

    def test_register_all_tools_handles_missing_dependency(self):
        """Should skip classes with missing dependencies."""
        import lib.tool_loader as tool_loader_module

        mock_app = MagicMock()
        config = {}
        dependencies = {}  # Empty - missing required deps

        class RequiresDepsTools:
            def __init__(self, db_service):
                self.db_service = db_service

            def test_method(self):
                pass

        # Don't patch _instantiate_tools_class so it actually runs
        # and throws KeyError for missing dependency
        with (
            patch.object(
                tool_loader_module, "_discover_tool_packages", return_value=["test"]
            ),
            patch.object(
                tool_loader_module,
                "_find_tools_class",
                return_value=("RequiresDepsTools", RequiresDepsTools),
            ),
            patch(
                "importlib.import_module",
                return_value=MagicMock(__name__="tools.test.tools"),
            ),
        ):
            # Should not raise, just skip the class with missing dependency
            register_all_tools(mock_app, config, dependencies)

            assert mock_app.tool.call_count == 0

    def test_register_all_tools_raises_on_instantiation_error(self):
        """Should raise on non-KeyError instantiation errors."""
        import lib.tool_loader as tool_loader_module

        mock_app = MagicMock()
        config = {}
        dependencies = {}

        with (
            patch.object(
                tool_loader_module, "_discover_tool_packages", return_value=["test"]
            ),
            patch.object(
                tool_loader_module,
                "_find_tools_class",
                return_value=("Broken", MagicMock),
            ),
            patch.object(
                tool_loader_module,
                "_instantiate_tools_class",
                side_effect=ValueError("Broken"),
            ),
            patch(
                "importlib.import_module", return_value=MagicMock(__name__="tools.test")
            ),
        ):
            with pytest.raises(ValueError):
                register_all_tools(mock_app, config, dependencies)

    def test_register_all_tools_registers_methods(self):
        """Should register public methods as tools."""
        import lib.tool_loader as tool_loader_module

        mock_app = MagicMock()
        config = {}
        dependencies = {}
        mock_method = MagicMock()

        with (
            patch.object(
                tool_loader_module, "_discover_tool_packages", return_value=["test"]
            ),
            patch.object(
                tool_loader_module,
                "_find_tools_class",
                return_value=("Simple", MagicMock),
            ),
            patch.object(
                tool_loader_module, "_instantiate_tools_class", return_value=MagicMock()
            ),
            patch.object(
                tool_loader_module,
                "_get_public_methods",
                return_value=[("method_one", mock_method), ("method_two", mock_method)],
            ),
            patch(
                "importlib.import_module", return_value=MagicMock(__name__="tools.test")
            ),
        ):
            register_all_tools(mock_app, config, dependencies)
            assert mock_app.tool.call_count == 2

    def test_register_all_tools_raises_on_registration_error(self):
        """Should raise on tool registration errors."""
        import lib.tool_loader as tool_loader_module

        mock_app = MagicMock()
        mock_app.tool.side_effect = TypeError("Invalid tool")
        config = {}
        dependencies = {}
        mock_method = MagicMock()

        with (
            patch.object(
                tool_loader_module, "_discover_tool_packages", return_value=["test"]
            ),
            patch.object(
                tool_loader_module,
                "_find_tools_class",
                return_value=("Simple", MagicMock),
            ),
            patch.object(
                tool_loader_module, "_instantiate_tools_class", return_value=MagicMock()
            ),
            patch.object(
                tool_loader_module,
                "_get_public_methods",
                return_value=[("broken_tool", mock_method)],
            ),
            patch(
                "importlib.import_module", return_value=MagicMock(__name__="tools.test")
            ),
        ):
            with pytest.raises(TypeError):
                register_all_tools(mock_app, config, dependencies)

    def test_register_all_tools_custom_package_name(self):
        """Should use custom tools_package from config."""
        mock_app = MagicMock()
        config = {"tools_package": "custom_tools"}
        dependencies = {}

        with patch("lib.tool_loader._discover_tool_packages") as mock_discover:
            mock_discover.return_value = ["auth"]

            with patch("importlib.import_module") as mock_import:
                mock_import.side_effect = ImportError("Not found")

                register_all_tools(mock_app, config, dependencies)

                mock_import.assert_called_with("custom_tools.auth.tools")
