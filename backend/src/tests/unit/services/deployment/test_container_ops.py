"""
Unit tests for services/deployment/container_ops.py

Tests for ContainerOpsMixin helper methods: _map_docker_status
and _parse_mount_info.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.deployment.container_ops import ContainerOpsMixin


class ConcreteContainerOps(ContainerOpsMixin):
    """Concrete class for testing the mixin."""

    def __init__(self):
        self.db_service = MagicMock()
        self.agent_manager = MagicMock()

    async def _get_agent_for_server(self, server_id):
        return None

    async def _agent_inspect_container(self, server_id, name):
        return {"success": False}

    async def _agent_get_container_status(self, server_id, container_id):
        return {"success": False}


@pytest.fixture
def ops():
    """Create a ConcreteContainerOps instance."""
    return ConcreteContainerOps()


class TestMapDockerStatus:
    """Tests for _map_docker_status method."""

    def test_running_maps_to_running(self, ops):
        assert ops._map_docker_status("running") == "running"

    def test_exited_maps_to_stopped(self, ops):
        assert ops._map_docker_status("exited") == "stopped"

    def test_restarting_maps_to_error(self, ops):
        assert ops._map_docker_status("restarting") == "error"

    def test_created_maps_to_stopped(self, ops):
        assert ops._map_docker_status("created") == "stopped"

    def test_paused_maps_to_stopped(self, ops):
        assert ops._map_docker_status("paused") == "stopped"

    def test_unknown_status_returned_as_is(self, ops):
        assert ops._map_docker_status("removing") == "removing"

    def test_empty_string_maps_to_stopped(self, ops):
        assert ops._map_docker_status("") == "stopped"


class TestParseMountInfo:
    """Tests for _parse_mount_info method."""

    def test_empty_info(self, ops):
        networks, volumes, binds = ops._parse_mount_info({})
        assert networks == []
        assert volumes == []
        assert binds == []

    def test_networks_extracted(self, ops):
        info = {
            "NetworkSettings": {"Networks": {"bridge": {}, "host": {}}},
            "Mounts": [],
        }
        networks, volumes, binds = ops._parse_mount_info(info)
        assert sorted(networks) == ["bridge", "host"]

    def test_volume_mounts_parsed(self, ops):
        info = {
            "NetworkSettings": {"Networks": {}},
            "Mounts": [
                {
                    "Type": "volume",
                    "Name": "my-vol",
                    "Destination": "/data",
                    "Mode": "rw",
                }
            ],
        }
        networks, volumes, binds = ops._parse_mount_info(info)
        assert len(volumes) == 1
        assert volumes[0]["name"] == "my-vol"
        assert volumes[0]["destination"] == "/data"
        assert volumes[0]["mode"] == "rw"

    def test_bind_mounts_parsed(self, ops):
        info = {
            "NetworkSettings": {"Networks": {}},
            "Mounts": [
                {
                    "Type": "bind",
                    "Source": "/host/path",
                    "Destination": "/container/path",
                    "Mode": "ro",
                }
            ],
        }
        networks, volumes, binds = ops._parse_mount_info(info)
        assert len(binds) == 1
        assert binds[0]["source"] == "/host/path"
        assert binds[0]["destination"] == "/container/path"
        assert binds[0]["mode"] == "ro"

    def test_mixed_mounts(self, ops):
        info = {
            "NetworkSettings": {"Networks": {"bridge": {}}},
            "Mounts": [
                {
                    "Type": "volume",
                    "Name": "db-data",
                    "Destination": "/var/lib/db",
                    "Mode": "rw",
                },
                {
                    "Type": "bind",
                    "Source": "/etc/config",
                    "Destination": "/config",
                    "Mode": "ro",
                },
                {
                    "Type": "tmpfs",
                    "Source": "",
                    "Destination": "/tmp",
                    "Mode": "",
                },
            ],
        }
        networks, volumes, binds = ops._parse_mount_info(info)
        assert networks == ["bridge"]
        assert len(volumes) == 1
        assert len(binds) == 1

    def test_no_mounts_key(self, ops):
        info = {"NetworkSettings": {"Networks": {"bridge": {}}}}
        networks, volumes, binds = ops._parse_mount_info(info)
        assert networks == ["bridge"]
        assert volumes == []
        assert binds == []

    def test_missing_mount_fields_default(self, ops):
        info = {
            "NetworkSettings": {"Networks": {}},
            "Mounts": [{"Type": "volume"}, {"Type": "bind"}],
        }
        networks, volumes, binds = ops._parse_mount_info(info)
        assert len(volumes) == 1
        assert volumes[0]["name"] == ""
        assert volumes[0]["mode"] == "rw"
        assert len(binds) == 1
        assert binds[0]["source"] == ""
        assert binds[0]["mode"] == "rw"
