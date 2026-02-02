"""Utilities for dynamically registering MCP tool modules.

Auto-discovers *Tools classes in the tools directory and registers
all their public methods as MCP tools.

Supports nested package structure:
    tools/
    ├── __init__.py
    ├── auth/
    │   ├── __init__.py
    │   └── tools.py  (contains AuthTools class)
    ├── server/
    │   ├── __init__.py
    │   └── tools.py  (contains ServerTools class)
    └── ...
"""

from __future__ import annotations

import importlib
import inspect
from pathlib import Path
from typing import Any, List, Mapping, Tuple, Type

import structlog


logger = structlog.get_logger("tool_loader")
SRC_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TOOLS_DIRECTORY = (SRC_ROOT / "tools").resolve()
DEFAULT_TOOLS_PACKAGE = "tools"


def _resolve_tools_path(tools_directory: str | None) -> Path:
    """Return an absolute path to the tools directory."""
    if not tools_directory:
        return DEFAULT_TOOLS_DIRECTORY

    candidate = Path(tools_directory)
    return candidate.resolve() if candidate.is_absolute() else (SRC_ROOT / candidate).resolve()


def _discover_tool_packages(tools_path: Path) -> List[str]:
    """Discover tool subpackages (directories with __init__.py).

    Args:
        tools_path: Absolute path to the tools directory.

    Returns:
        List of subpackage names (e.g., ['auth', 'server', 'docker'])
    """
    packages: List[str] = []

    if not tools_path.exists():
        raise FileNotFoundError(f"Tools directory not found: {tools_path}")

    for item in tools_path.iterdir():
        if item.is_dir() and not item.name.startswith("_"):
            init_file = item / "__init__.py"
            if init_file.exists():
                packages.append(item.name)

    return sorted(packages)


def _find_tools_class(module: Any) -> Tuple[str, Type] | None:
    """Find a *Tools class in the module.

    Args:
        module: Imported Python module.

    Returns:
        Tuple of (class_name, class) or None if not found.
    """
    for name, cls in inspect.getmembers(module, inspect.isclass):
        if name.endswith("Tools") and cls.__module__ == module.__name__:
            return (name, cls)
    return None


def _instantiate_tools_class(
    cls: Type,
    class_name: str,
    dependencies: Mapping[str, Any]
) -> Any:
    """Instantiate a Tools class with dependencies from constructor signature.

    Args:
        cls: The Tools class to instantiate.
        class_name: Name of the class (for error messages).
        dependencies: Mapping of dependency name to service instance.

    Returns:
        Instantiated tools class.
    """
    signature = inspect.signature(cls.__init__)
    kwargs = {}

    for param_name, param in signature.parameters.items():
        if param_name == "self":
            continue

        if param.default is inspect.Parameter.empty:
            if param_name not in dependencies:
                raise KeyError(
                    f"Missing dependency '{param_name}' for {class_name}.__init__"
                )
            kwargs[param_name] = dependencies[param_name]
        else:
            kwargs[param_name] = dependencies.get(param_name, param.default)

    return cls(**kwargs)


def _get_public_methods(instance: Any) -> List[Tuple[str, Any]]:
    """Get all public methods from a class instance.

    Args:
        instance: Instantiated tools class.

    Returns:
        List of (method_name, method) tuples.
    """
    methods = []
    for name in dir(instance):
        if name.startswith("_"):
            continue
        attr = getattr(instance, name)
        # Only include actual methods (bound methods), not instance attributes
        if inspect.ismethod(attr):
            methods.append((name, attr))
    return methods


def register_all_tools(
    app: Any,
    config: Mapping[str, Any],
    dependencies: Mapping[str, Any],
) -> None:
    """Discover and register all tool packages under the configured directory.

    Scans for *Tools classes in each subpackage, instantiates them with
    dependencies, and registers all their public methods as MCP tools.

    Args:
        app: FastMCP application that will own the registered tools.
        config: Configuration mapping containing optional keys.
        dependencies: Mapping of dependency name to service instance.
    """
    tools_path = _resolve_tools_path(config.get("tools_directory"))
    tools_package = config.get("tools_package", DEFAULT_TOOLS_PACKAGE)

    package_names = _discover_tool_packages(tools_path)
    total_tools = 0

    for package_name in package_names:
        full_module = f"{tools_package}.{package_name}.tools"
        try:
            module = importlib.import_module(full_module)
        except ImportError as exc:
            logger.warning(
                "Skipping tool module (import failed)",
                module=full_module,
                error=str(exc),
            )
            continue

        result = _find_tools_class(module)
        if not result:
            logger.warning(
                "No *Tools class found in module",
                module=full_module,
            )
            continue

        class_name, cls = result

        try:
            instance = _instantiate_tools_class(cls, class_name, dependencies)
        except KeyError as exc:
            logger.warning(
                "Skipping tools class (missing dependency)",
                class_name=class_name,
                error=str(exc),
            )
            continue
        except Exception as exc:
            logger.error(
                "Failed to instantiate tools class",
                class_name=class_name,
                error=str(exc),
            )
            raise

        methods = _get_public_methods(instance)
        for method_name, method in methods:
            try:
                app.tool(method)
                total_tools += 1
            except Exception as exc:
                logger.error(
                    "Failed to register tool",
                    class_name=class_name,
                    method=method_name,
                    error=str(exc),
                )
                raise

        logger.debug(
            "Registered tools from class",
            class_name=class_name,
            tool_count=len(methods),
        )

    logger.info(
        "Tool registration completed",
        modules=len(package_names),
        total_tools=total_tools,
    )


__all__ = ["register_all_tools"]
