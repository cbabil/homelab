"""Utilities for dynamically registering MCP tool modules."""

from __future__ import annotations

import importlib
import inspect
import pkgutil
from pathlib import Path
from typing import Any, Iterable, List, Mapping

import structlog


logger = structlog.get_logger("tool_loader")
SRC_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TOOLS_DIRECTORY = (SRC_ROOT / "tools").resolve()
DEFAULT_TOOLS_PACKAGE = "tools"


def _resolve_tools_path(tools_directory: str | None) -> Path:
    """Return an absolute path to the tools directory.

    Args:
        tools_directory: Path (absolute or relative) supplied via configuration.

    Returns:
        Path: Absolute path to the tool modules directory.
    """

    if not tools_directory:
        return DEFAULT_TOOLS_DIRECTORY

    candidate = Path(tools_directory)
    return candidate.resolve() if candidate.is_absolute() else (SRC_ROOT / candidate).resolve()


def _discover_tool_module_names(tools_path: Path) -> List[str]:
    """Return importable module names found within ``tools_path``.

    Args:
        tools_path: Absolute path to the directory containing tool modules.

    Raises:
        FileNotFoundError: If ``tools_path`` does not exist.

    Returns:
        List[str]: Sorted list of module names.
    """

    module_names: List[str] = []
    if not tools_path.exists():
        raise FileNotFoundError(f"Tools directory not found: {tools_path}")

    for module_info in pkgutil.iter_modules([str(tools_path)]):
        if module_info.ispkg:
            continue
        if module_info.name.startswith("_"):
            continue
        module_names.append(module_info.name)
    return sorted(module_names)


def _find_register_functions(module: Any) -> Iterable[Any]:
    """Yield register* callables defined within ``module``.

    Args:
        module: Imported module housing potential tool registration functions.

    Yields:
        Callable: Functions whose names start with ``register``.
    """

    for attribute_name in sorted(dir(module)):
        if not attribute_name.startswith("register"):
            continue
        attribute = getattr(module, attribute_name)
        if callable(attribute):
            yield attribute


def _invoke_register_function(func: Any, app: Any, dependencies: Mapping[str, Any]) -> None:
    """Invoke a tool registration function with resolved dependencies.

    Args:
        func: Registration callable discovered in a tool module.
        app: FastMCP application instance.
        dependencies: Mapping of dependency name to concrete instance.

    Raises:
        ValueError: If the function exposes no parameters.
        KeyError: If a required dependency is missing.
        TypeError: If the function signature uses unsupported parameter kinds.
    """

    signature = inspect.signature(func)
    parameters = list(signature.parameters.values())

    if not parameters:
        raise ValueError(
            f"Tool register function '{func.__module__}.{func.__name__}' must accept at least an 'app' parameter"
        )

    args: List[Any] = [app]

    for param in parameters[1:]:
        if param.kind in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        ):
            if param.default is inspect._empty:
                if param.name not in dependencies:
                    raise KeyError(
                        f"Missing dependency '{param.name}' for tool register function "
                        f"'{func.__module__}.{func.__name__}'"
                    )
                args.append(dependencies[param.name])
            else:
                args.append(dependencies.get(param.name, param.default))
        elif param.kind == inspect.Parameter.KEYWORD_ONLY:
            raise TypeError(
                f"Tool register function '{func.__module__}.{func.__name__}' should not define keyword-only parameters"
            )
        elif param.kind == inspect.Parameter.VAR_POSITIONAL:
            raise TypeError(
                f"Tool register function '{func.__module__}.{func.__name__}' should not use *args"
            )
        elif param.kind == inspect.Parameter.VAR_KEYWORD:
            raise TypeError(
                f"Tool register function '{func.__module__}.{func.__name__}' should not use **kwargs"
            )

    func(*args)


def register_all_tools(
    app: Any,
    config: Mapping[str, Any],
    dependencies: Mapping[str, Any],
) -> None:
    """Discover and register all tool modules under the configured package.

    Args:
        app: FastMCP application that will own the registered tools.
        config: Configuration mapping containing optional ``tools_directory`` and
            ``tools_package`` keys.
        dependencies: Mapping of dependency name to service instance required by
            the tool registration functions.
    """

    tools_path = _resolve_tools_path(config.get("tools_directory"))
    tools_package = config.get("tools_package", DEFAULT_TOOLS_PACKAGE)

    module_names = _discover_tool_module_names(tools_path)
    registrations = 0

    for module_name in module_names:
        module = importlib.import_module(f"{tools_package}.{module_name}")
        for register_func in _find_register_functions(module):
            try:
                _invoke_register_function(register_func, app, dependencies)
                registrations += 1
            except Exception as exc:  # pylint: disable=broad-except
                logger.error(
                    "Failed to register tool module",
                    module=module_name,
                    function=register_func.__name__,
                    error=str(exc),
                )
                raise

    logger.info(
        "Tool registration completed",
        modules=len(module_names),
        registrations=registrations,
    )


__all__ = ["register_all_tools"]
