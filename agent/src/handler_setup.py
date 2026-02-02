"""RPC handler setup for the agent.

Registers all RPC method modules with the handler.
"""

from typing import Callable, Optional

try:
    from .rpc.agent_handlers import setup_agent_handlers
    from .rpc.handler import RPCHandler
    from .rpc.methods import (
        ContainerMethods,
        ImageMethods,
        NetworkMethods,
        VolumeMethods,
    )
    from .rpc.methods.agent import create_agent_methods
    from .rpc.methods.system import SystemMethods
except ImportError:
    from rpc.agent_handlers import setup_agent_handlers
    from rpc.handler import RPCHandler
    from rpc.methods import (
        ContainerMethods,
        ImageMethods,
        NetworkMethods,
        VolumeMethods,
    )
    from rpc.methods.agent import create_agent_methods
    from rpc.methods.system import SystemMethods


def setup_all_handlers(
    rpc_handler: RPCHandler,
    get_config: Callable,
    set_config: Callable,
    get_agent_id: Callable[[], Optional[str]],
    shutdown: Callable,
) -> None:
    """Set up all RPC method handlers.

    Args:
        rpc_handler: The RPC handler to register methods with.
        get_config: Function to get current config.
        set_config: Function to update config.
        get_agent_id: Function to get current agent ID.
        shutdown: Async function to trigger shutdown.
    """
    # Register built-in handlers (config.update, metrics.get)
    setup_agent_handlers(
        rpc_handler,
        get_config=get_config,
        set_config=set_config,
        get_agent_id=get_agent_id,
    )

    # Register Docker methods
    rpc_handler.register_module("docker.containers", ContainerMethods())
    rpc_handler.register_module("docker.images", ImageMethods())
    rpc_handler.register_module("docker.volumes", VolumeMethods())
    rpc_handler.register_module("docker.networks", NetworkMethods())

    # Register System methods
    rpc_handler.register_module("system", SystemMethods())

    # Register Agent methods
    agent_methods = create_agent_methods(
        get_agent_id=get_agent_id,
        shutdown=shutdown,
    )
    rpc_handler.register_module("agent", agent_methods)
