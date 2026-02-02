"""RPC method modules."""

try:
    from .docker_containers import ContainerMethods
    from .docker_images import ImageMethods
    from .docker_volumes import VolumeMethods
    from .docker_networks import NetworkMethods
except ImportError:
    from rpc.methods.docker_containers import ContainerMethods
    from rpc.methods.docker_images import ImageMethods
    from rpc.methods.docker_volumes import VolumeMethods
    from rpc.methods.docker_networks import NetworkMethods

__all__ = ["ContainerMethods", "ImageMethods", "VolumeMethods", "NetworkMethods"]
