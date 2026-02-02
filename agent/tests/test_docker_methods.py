"""Tests for Docker RPC methods.

Tests container, image, volume, and network operations.
"""

from unittest.mock import MagicMock, patch


from rpc.methods.docker_containers import ContainerMethods
from rpc.methods.docker_images import ImageMethods
from rpc.methods.docker_volumes import VolumeMethods
from rpc.methods.docker_networks import NetworkMethods


class MockContainer:
    """Mock Docker container."""

    def __init__(self, id="abc123", name="test", status="running", image_tags=None):
        self.short_id = id[:12] if len(id) > 12 else id
        self.id = id
        self.name = name
        self.status = status
        self.image = MagicMock()
        self.image.tags = image_tags or ["nginx:latest"]
        self.image.short_id = "img123"
        self.attrs = {
            "State": {
                "Status": status,
                "Running": status == "running",
                "StartedAt": "2024-01-01T00:00:00Z",
                "FinishedAt": None,
            },
            "RestartCount": 0,
        }

    def start(self):
        self.status = "running"

    def stop(self, timeout=10):
        self.status = "exited"

    def remove(self, force=False):
        pass

    def restart(self):
        pass

    def logs(self, tail=100, follow=False, timestamps=False):
        return b"container logs here"

    def reload(self):
        pass

    def stats(self, stream=False):
        return {
            "cpu_stats": {"cpu_usage": {"total_usage": 100}, "system_cpu_usage": 1000},
            "precpu_stats": {"cpu_usage": {"total_usage": 50}, "system_cpu_usage": 500},
            "memory_stats": {"usage": 1024000, "limit": 4096000},
        }

    def update(self, **kwargs):
        pass


class MockImage:
    """Mock Docker image."""

    def __init__(self, id="img123", tags=None, size=100000000):
        self.short_id = id
        self.tags = tags or ["nginx:latest"]
        self.attrs = {"Size": size}


class MockVolume:
    """Mock Docker volume."""

    def __init__(
        self, name="data", driver="local", mountpoint="/var/lib/docker/volumes/data"
    ):
        self.name = name
        self.attrs = {"Driver": driver, "Mountpoint": mountpoint}

    def remove(self, force=False):
        pass


class MockNetwork:
    """Mock Docker network."""

    def __init__(self, id="net123", name="bridge", driver="bridge"):
        self.short_id = id
        self.name = name
        self.attrs = {"Driver": driver}

    def remove(self):
        pass


class TestContainerMethodsList:
    """Tests for ContainerMethods.list()."""

    def test_lists_containers(self):
        """Should list containers."""
        mock_client = MagicMock()
        mock_client.containers.list.return_value = [
            MockContainer(id="abc123", name="web"),
            MockContainer(id="def456", name="db", status="exited"),
        ]

        methods = ContainerMethods()

        with patch(
            "rpc.methods.docker_containers.get_client", return_value=mock_client
        ):
            result = methods.list()

        assert len(result) == 2
        assert result[0]["name"] == "web"
        assert result[1]["name"] == "db"

    def test_lists_all_containers(self):
        """Should pass all=True to Docker client."""
        mock_client = MagicMock()
        mock_client.containers.list.return_value = []

        methods = ContainerMethods()

        with patch(
            "rpc.methods.docker_containers.get_client", return_value=mock_client
        ):
            methods.list(all=True)

        mock_client.containers.list.assert_called_once_with(all=True)

    def test_returns_container_details(self):
        """Should return container details."""
        container = MockContainer(id="container123", name="app", status="running")
        mock_client = MagicMock()
        mock_client.containers.list.return_value = [container]

        methods = ContainerMethods()

        with patch(
            "rpc.methods.docker_containers.get_client", return_value=mock_client
        ):
            result = methods.list()

        assert result[0]["id"] == "container123"
        assert result[0]["name"] == "app"
        assert result[0]["status"] == "running"
        assert result[0]["image"] == "nginx:latest"


class TestContainerMethodsStart:
    """Tests for ContainerMethods.start()."""

    def test_starts_container(self):
        """Should start container."""
        container = MockContainer()
        mock_client = MagicMock()
        mock_client.containers.get.return_value = container

        methods = ContainerMethods()

        with patch(
            "rpc.methods.docker_containers.get_client", return_value=mock_client
        ):
            result = methods.start("test")

        assert result["status"] == "started"
        mock_client.containers.get.assert_called_once_with("test")


class TestContainerMethodsStop:
    """Tests for ContainerMethods.stop()."""

    def test_stops_container(self):
        """Should stop container."""
        container = MockContainer()
        mock_client = MagicMock()
        mock_client.containers.get.return_value = container

        methods = ContainerMethods()

        with patch(
            "rpc.methods.docker_containers.get_client", return_value=mock_client
        ):
            result = methods.stop("test")

        assert result["status"] == "stopped"

    def test_passes_timeout(self):
        """Should pass timeout to Docker."""
        container = MagicMock()
        mock_client = MagicMock()
        mock_client.containers.get.return_value = container

        methods = ContainerMethods()

        with patch(
            "rpc.methods.docker_containers.get_client", return_value=mock_client
        ):
            methods.stop("test", timeout=30)

        container.stop.assert_called_once_with(timeout=30)


class TestContainerMethodsRemove:
    """Tests for ContainerMethods.remove()."""

    def test_removes_container(self):
        """Should remove container."""
        container = MockContainer()
        mock_client = MagicMock()
        mock_client.containers.get.return_value = container

        methods = ContainerMethods()

        with patch(
            "rpc.methods.docker_containers.get_client", return_value=mock_client
        ):
            result = methods.remove("test")

        assert result["status"] == "removed"

    def test_force_removes_container(self):
        """Should force remove container."""
        container = MagicMock()
        mock_client = MagicMock()
        mock_client.containers.get.return_value = container

        methods = ContainerMethods()

        with patch(
            "rpc.methods.docker_containers.get_client", return_value=mock_client
        ):
            methods.remove("test", force=True)

        container.remove.assert_called_once_with(force=True)


class TestContainerMethodsRestart:
    """Tests for ContainerMethods.restart()."""

    def test_restarts_container(self):
        """Should restart container."""
        container = MockContainer()
        mock_client = MagicMock()
        mock_client.containers.get.return_value = container

        methods = ContainerMethods()

        with patch(
            "rpc.methods.docker_containers.get_client", return_value=mock_client
        ):
            result = methods.restart("test")

        assert result["status"] == "restarted"


class TestContainerMethodsLogs:
    """Tests for ContainerMethods.logs()."""

    def test_gets_logs(self):
        """Should get container logs."""
        container = MockContainer()
        mock_client = MagicMock()
        mock_client.containers.get.return_value = container

        methods = ContainerMethods()

        with patch(
            "rpc.methods.docker_containers.get_client", return_value=mock_client
        ):
            result = methods.logs("test")

        assert "logs" in result
        assert "container logs here" in result["logs"]


class TestContainerMethodsInspect:
    """Tests for ContainerMethods.inspect()."""

    def test_inspects_container(self):
        """Should inspect container."""
        container = MockContainer()
        mock_client = MagicMock()
        mock_client.containers.get.return_value = container

        methods = ContainerMethods()

        with patch(
            "rpc.methods.docker_containers.get_client", return_value=mock_client
        ):
            result = methods.inspect("test")

        assert "State" in result


class TestContainerMethodsUpdate:
    """Tests for ContainerMethods.update()."""

    def test_updates_restart_policy(self):
        """Should update container restart policy."""
        container = MagicMock()
        mock_client = MagicMock()
        mock_client.containers.get.return_value = container

        methods = ContainerMethods()

        with patch(
            "rpc.methods.docker_containers.get_client", return_value=mock_client
        ):
            result = methods.update("test", restart_policy="unless-stopped")

        assert result["status"] == "updated"
        container.update.assert_called_once()


class TestContainerMethodsStatus:
    """Tests for ContainerMethods.status()."""

    def test_gets_status(self):
        """Should get container status."""
        container = MockContainer(status="running")
        mock_client = MagicMock()
        mock_client.containers.get.return_value = container

        methods = ContainerMethods()

        with patch(
            "rpc.methods.docker_containers.get_client", return_value=mock_client
        ):
            result = methods.status("test")

        assert result["status"] == "running"
        assert result["running"] is True

    def test_includes_logs_when_requested(self):
        """Should include logs when requested."""
        container = MockContainer()
        mock_client = MagicMock()
        mock_client.containers.get.return_value = container

        methods = ContainerMethods()

        with patch(
            "rpc.methods.docker_containers.get_client", return_value=mock_client
        ):
            result = methods.status("test", include_logs=True)

        assert "logs" in result


class TestContainerMethodsStats:
    """Tests for ContainerMethods.stats()."""

    def test_gets_stats(self):
        """Should get container stats."""
        container = MockContainer()
        mock_client = MagicMock()
        mock_client.containers.get.return_value = container

        methods = ContainerMethods()

        with patch(
            "rpc.methods.docker_containers.get_client", return_value=mock_client
        ):
            result = methods.stats("test")

        assert "cpu_percent" in result
        assert "memory_usage" in result
        assert "memory_limit" in result


class TestImageMethodsList:
    """Tests for ImageMethods.list()."""

    def test_lists_images(self):
        """Should list images."""
        mock_client = MagicMock()
        mock_client.images.list.return_value = [
            MockImage(id="img1", tags=["nginx:latest"]),
            MockImage(id="img2", tags=["redis:alpine"]),
        ]

        methods = ImageMethods()

        with patch("rpc.methods.docker_images.get_client", return_value=mock_client):
            result = methods.list()

        assert len(result) == 2
        assert result[0]["tags"] == ["nginx:latest"]


class TestImageMethodsPull:
    """Tests for ImageMethods.pull()."""

    def test_pulls_image(self):
        """Should pull image."""
        mock_image = MockImage()
        mock_client = MagicMock()
        mock_client.images.pull.return_value = mock_image

        methods = ImageMethods()

        with patch("rpc.methods.docker_images.get_client", return_value=mock_client):
            result = methods.pull("nginx", tag="1.21")

        mock_client.images.pull.assert_called_once_with("nginx", tag="1.21")
        assert "id" in result


class TestImageMethodsRemove:
    """Tests for ImageMethods.remove()."""

    def test_removes_image(self):
        """Should remove image."""
        mock_client = MagicMock()

        methods = ImageMethods()

        with patch("rpc.methods.docker_images.get_client", return_value=mock_client):
            result = methods.remove("nginx:latest")

        assert result["status"] == "removed"
        mock_client.images.remove.assert_called_once()


class TestImageMethodsPrune:
    """Tests for ImageMethods.prune()."""

    def test_prunes_images(self):
        """Should prune unused images."""
        mock_client = MagicMock()
        mock_client.images.prune.return_value = {
            "ImagesDeleted": [{"Untagged": "old:1.0"}],
            "SpaceReclaimed": 500000000,
        }

        methods = ImageMethods()

        with patch("rpc.methods.docker_images.get_client", return_value=mock_client):
            result = methods.prune()

        assert result["space_reclaimed"] == 500000000


class TestVolumeMethodsList:
    """Tests for VolumeMethods.list()."""

    def test_lists_volumes(self):
        """Should list volumes."""
        mock_client = MagicMock()
        mock_client.volumes.list.return_value = [
            MockVolume(name="data"),
            MockVolume(name="config"),
        ]

        methods = VolumeMethods()

        with patch("rpc.methods.docker_volumes.get_client", return_value=mock_client):
            result = methods.list()

        assert len(result) == 2
        assert result[0]["name"] == "data"


class TestVolumeMethodsCreate:
    """Tests for VolumeMethods.create()."""

    def test_creates_volume(self):
        """Should create volume."""
        mock_volume = MockVolume(name="newvol")
        mock_client = MagicMock()
        mock_client.volumes.create.return_value = mock_volume

        methods = VolumeMethods()

        with patch("rpc.methods.docker_volumes.get_client", return_value=mock_client):
            result = methods.create("newvol")

        assert result["name"] == "newvol"
        mock_client.volumes.create.assert_called_once()


class TestVolumeMethodsRemove:
    """Tests for VolumeMethods.remove()."""

    def test_removes_volume(self):
        """Should remove volume."""
        mock_volume = MockVolume()
        mock_client = MagicMock()
        mock_client.volumes.get.return_value = mock_volume

        methods = VolumeMethods()

        with patch("rpc.methods.docker_volumes.get_client", return_value=mock_client):
            result = methods.remove("data")

        assert result["status"] == "removed"


class TestVolumeMethodsPrune:
    """Tests for VolumeMethods.prune()."""

    def test_prunes_volumes(self):
        """Should prune unused volumes."""
        mock_client = MagicMock()
        mock_client.volumes.prune.return_value = {
            "VolumesDeleted": ["old_vol"],
            "SpaceReclaimed": 100000000,
        }

        methods = VolumeMethods()

        with patch("rpc.methods.docker_volumes.get_client", return_value=mock_client):
            result = methods.prune()

        assert result["space_reclaimed"] == 100000000


class TestNetworkMethodsList:
    """Tests for NetworkMethods.list()."""

    def test_lists_networks(self):
        """Should list networks."""
        mock_client = MagicMock()
        mock_client.networks.list.return_value = [
            MockNetwork(name="bridge"),
            MockNetwork(name="host"),
        ]

        methods = NetworkMethods()

        with patch("rpc.methods.docker_networks.get_client", return_value=mock_client):
            result = methods.list()

        assert len(result) == 2


class TestNetworkMethodsCreate:
    """Tests for NetworkMethods.create()."""

    def test_creates_network(self):
        """Should create network."""
        mock_network = MockNetwork(id="new123", name="mynet")
        mock_client = MagicMock()
        mock_client.networks.create.return_value = mock_network

        methods = NetworkMethods()

        with patch("rpc.methods.docker_networks.get_client", return_value=mock_client):
            result = methods.create("mynet")

        assert result["name"] == "mynet"


class TestNetworkMethodsRemove:
    """Tests for NetworkMethods.remove()."""

    def test_removes_network(self):
        """Should remove network."""
        mock_network = MockNetwork()
        mock_client = MagicMock()
        mock_client.networks.get.return_value = mock_network

        methods = NetworkMethods()

        with patch("rpc.methods.docker_networks.get_client", return_value=mock_client):
            result = methods.remove("mynet")

        assert result["status"] == "removed"
