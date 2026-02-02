"""
Docker Commands Unit Tests

Comprehensive tests for the docker_commands module covering:
- build_run_command function
- parse_pull_progress function  
- parse_container_inspect function

Target: 90%+ coverage
"""

import json
import pytest
from unittest.mock import MagicMock

from services.deployment.docker_commands import (
    build_run_command,
    parse_pull_progress,
    parse_container_inspect,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def basic_docker_config():
    """Create a basic docker config mock with minimal settings."""
    config = MagicMock()
    config.image = "nginx:latest"
    config.restart_policy = "unless-stopped"
    config.ports = []
    config.volumes = []
    config.network_mode = None
    config.privileged = False
    config.capabilities = []
    return config


@pytest.fixture
def full_docker_config():
    """Create a docker config mock with all options configured."""
    config = MagicMock()
    config.image = "portainer/portainer-ce:2.19.4"
    config.restart_policy = "always"
    config.ports = [
        MagicMock(container=9000, host=9000, protocol="tcp"),
        MagicMock(container=8000, host=8000, protocol="tcp"),
    ]
    config.volumes = [
        MagicMock(
            host_path="/var/run/docker.sock",
            container_path="/var/run/docker.sock",
            readonly=False
        ),
        MagicMock(
            host_path="/opt/portainer",
            container_path="/data",
            readonly=False
        ),
    ]
    config.network_mode = "bridge"
    config.privileged = True
    config.capabilities = ["NET_ADMIN", "SYS_ADMIN"]
    return config


# ---------------------------------------------------------------------------
# Tests for build_run_command
# ---------------------------------------------------------------------------


class TestBuildRunCommandBasic:
    """Tests for basic build_run_command functionality."""

    def test_basic_command_structure(self, basic_docker_config):
        """Test that command starts with docker run -d."""
        cmd = build_run_command(basic_docker_config, "test-container", {})
        
        assert cmd.startswith("docker run -d")
        assert "--name test-container" in cmd
        assert "nginx:latest" in cmd

    def test_restart_policy_from_config(self, basic_docker_config):
        """Test restart policy comes from docker config."""
        basic_docker_config.restart_policy = "on-failure"
        
        cmd = build_run_command(basic_docker_config, "app", {})
        
        assert "--restart on-failure" in cmd

    def test_restart_policy_override(self, basic_docker_config):
        """Test restart policy can be overridden via parameter."""
        cmd = build_run_command(
            basic_docker_config, "app", {}, restart_policy="always"
        )
        
        assert "--restart always" in cmd
        assert "--restart unless-stopped" not in cmd

    def test_restart_policy_none_uses_config_default(self, basic_docker_config):
        """Test None restart_policy uses config default."""
        cmd = build_run_command(
            basic_docker_config, "app", {}, restart_policy=None
        )
        
        assert "--restart unless-stopped" in cmd

    def test_image_always_last(self, basic_docker_config):
        """Test that image is at the end of the command."""
        cmd = build_run_command(basic_docker_config, "app", {})
        
        assert cmd.endswith("nginx:latest")


class TestBuildRunCommandPorts:
    """Tests for port mapping in build_run_command."""

    def test_single_port_mapping(self, basic_docker_config):
        """Test single port mapping."""
        basic_docker_config.ports = [
            MagicMock(container=80, host=8080, protocol="tcp")
        ]
        
        cmd = build_run_command(basic_docker_config, "web", {})
        
        assert "-p 8080:80/tcp" in cmd

    def test_multiple_port_mappings(self, basic_docker_config):
        """Test multiple port mappings."""
        basic_docker_config.ports = [
            MagicMock(container=80, host=8080, protocol="tcp"),
            MagicMock(container=443, host=8443, protocol="tcp"),
            MagicMock(container=53, host=5353, protocol="udp"),
        ]
        
        cmd = build_run_command(basic_docker_config, "multi", {})
        
        assert "-p 8080:80/tcp" in cmd
        assert "-p 8443:443/tcp" in cmd
        assert "-p 5353:53/udp" in cmd

    def test_port_override_from_config(self, basic_docker_config):
        """Test port can be overridden via user config."""
        basic_docker_config.ports = [
            MagicMock(container=80, host=8080, protocol="tcp")
        ]
        
        config = {"ports": {"80": 9999}}
        cmd = build_run_command(basic_docker_config, "web", config)
        
        assert "-p 9999:80/tcp" in cmd
        assert "-p 8080:80/tcp" not in cmd

    def test_partial_port_override(self, basic_docker_config):
        """Test only specified ports are overridden."""
        basic_docker_config.ports = [
            MagicMock(container=80, host=8080, protocol="tcp"),
            MagicMock(container=443, host=8443, protocol="tcp"),
        ]
        
        config = {"ports": {"80": 9000}}
        cmd = build_run_command(basic_docker_config, "web", config)
        
        assert "-p 9000:80/tcp" in cmd
        assert "-p 8443:443/tcp" in cmd

    def test_empty_ports_config(self, basic_docker_config):
        """Test empty ports config doesn't affect mappings."""
        basic_docker_config.ports = [
            MagicMock(container=80, host=8080, protocol="tcp")
        ]
        
        config = {"ports": {}}
        cmd = build_run_command(basic_docker_config, "web", config)
        
        assert "-p 8080:80/tcp" in cmd


class TestBuildRunCommandVolumes:
    """Tests for volume mapping in build_run_command."""

    def test_single_volume_mapping(self, basic_docker_config):
        """Test single volume mapping."""
        basic_docker_config.volumes = [
            MagicMock(
                host_path="/data",
                container_path="/app/data",
                readonly=False
            )
        ]
        
        cmd = build_run_command(basic_docker_config, "app", {})
        
        assert "-v /data:/app/data" in cmd

    def test_readonly_volume(self, basic_docker_config):
        """Test readonly volume mapping."""
        basic_docker_config.volumes = [
            MagicMock(
                host_path="/config",
                container_path="/etc/config",
                readonly=True
            )
        ]
        
        cmd = build_run_command(basic_docker_config, "app", {})
        
        assert "-v /config:/etc/config:ro" in cmd

    def test_multiple_volumes_mixed_readonly(self, basic_docker_config):
        """Test multiple volumes with mixed readonly settings."""
        basic_docker_config.volumes = [
            MagicMock(
                host_path="/data",
                container_path="/data",
                readonly=False
            ),
            MagicMock(
                host_path="/config",
                container_path="/config",
                readonly=True
            ),
        ]
        
        cmd = build_run_command(basic_docker_config, "app", {})
        
        assert "-v /data:/data" in cmd
        assert ":ro" not in cmd.split("-v /data:/data")[1].split(" ")[0]
        assert "-v /config:/config:ro" in cmd

    def test_volume_path_override(self, basic_docker_config):
        """Test volume host path can be overridden."""
        basic_docker_config.volumes = [
            MagicMock(
                host_path="/default/path",
                container_path="/app/data",
                readonly=False
            )
        ]
        
        config = {"volumes": {"/app/data": "/custom/path"}}
        cmd = build_run_command(basic_docker_config, "app", config)
        
        assert "-v /custom/path:/app/data" in cmd
        assert "/default/path" not in cmd


class TestBuildRunCommandEnvironment:
    """Tests for environment variables in build_run_command."""

    def test_single_env_var(self, basic_docker_config):
        """Test single environment variable."""
        config = {"env": {"DEBUG": "true"}}
        
        cmd = build_run_command(basic_docker_config, "app", config)
        
        assert "-e DEBUG=true" in cmd

    def test_multiple_env_vars(self, basic_docker_config):
        """Test multiple environment variables."""
        config = {"env": {"DEBUG": "true", "PORT": "8080", "LOG_LEVEL": "info"}}
        
        cmd = build_run_command(basic_docker_config, "app", config)
        
        assert "-e DEBUG=true" in cmd
        assert "-e PORT=8080" in cmd
        assert "-e LOG_LEVEL=info" in cmd

    def test_no_env_vars(self, basic_docker_config):
        """Test command without environment variables."""
        cmd = build_run_command(basic_docker_config, "app", {})
        
        assert "-e " not in cmd

    def test_empty_env_dict(self, basic_docker_config):
        """Test empty env dict doesn't add flags."""
        config = {"env": {}}
        
        cmd = build_run_command(basic_docker_config, "app", config)
        
        assert "-e " not in cmd


class TestBuildRunCommandNetwork:
    """Tests for network configuration in build_run_command."""

    def test_network_mode_bridge(self, basic_docker_config):
        """Test bridge network mode."""
        basic_docker_config.network_mode = "bridge"
        
        cmd = build_run_command(basic_docker_config, "app", {})
        
        assert "--network bridge" in cmd

    def test_network_mode_host(self, basic_docker_config):
        """Test host network mode."""
        basic_docker_config.network_mode = "host"
        
        cmd = build_run_command(basic_docker_config, "app", {})
        
        assert "--network host" in cmd

    def test_network_mode_custom(self, basic_docker_config):
        """Test custom network name."""
        basic_docker_config.network_mode = "my-network"
        
        cmd = build_run_command(basic_docker_config, "app", {})
        
        assert "--network my-network" in cmd

    def test_no_network_mode(self, basic_docker_config):
        """Test no network mode when not specified."""
        basic_docker_config.network_mode = None
        
        cmd = build_run_command(basic_docker_config, "app", {})
        
        assert "--network" not in cmd


class TestBuildRunCommandPrivileged:
    """Tests for privileged mode in build_run_command."""

    def test_privileged_enabled(self, basic_docker_config):
        """Test privileged flag when enabled."""
        basic_docker_config.privileged = True
        
        cmd = build_run_command(basic_docker_config, "app", {})
        
        assert "--privileged" in cmd

    def test_privileged_disabled(self, basic_docker_config):
        """Test no privileged flag when disabled."""
        basic_docker_config.privileged = False
        
        cmd = build_run_command(basic_docker_config, "app", {})
        
        assert "--privileged" not in cmd


class TestBuildRunCommandCapabilities:
    """Tests for Linux capabilities in build_run_command."""

    def test_single_capability(self, basic_docker_config):
        """Test single capability."""
        basic_docker_config.capabilities = ["NET_ADMIN"]
        
        cmd = build_run_command(basic_docker_config, "app", {})
        
        assert "--cap-add NET_ADMIN" in cmd

    def test_multiple_capabilities(self, basic_docker_config):
        """Test multiple capabilities."""
        basic_docker_config.capabilities = ["NET_ADMIN", "SYS_ADMIN", "SYS_PTRACE"]
        
        cmd = build_run_command(basic_docker_config, "app", {})
        
        assert "--cap-add NET_ADMIN" in cmd
        assert "--cap-add SYS_ADMIN" in cmd
        assert "--cap-add SYS_PTRACE" in cmd

    def test_no_capabilities(self, basic_docker_config):
        """Test no capabilities when list is empty."""
        basic_docker_config.capabilities = []
        
        cmd = build_run_command(basic_docker_config, "app", {})
        
        assert "--cap-add" not in cmd


class TestBuildRunCommandFull:
    """Tests for full docker config with all options."""

    def test_full_config_command(self, full_docker_config):
        """Test command with all options configured."""
        config = {
            "env": {"ADMIN_PASSWORD": "secret"},
            "ports": {"9000": 9001},
            "volumes": {"/data": "/custom/data"}
        }
        
        cmd = build_run_command(full_docker_config, "portainer", config)
        
        # Basic structure
        assert cmd.startswith("docker run -d")
        assert "--name portainer" in cmd
        assert cmd.endswith("portainer/portainer-ce:2.19.4")
        
        # Restart policy
        assert "--restart always" in cmd
        
        # Ports (with override)
        assert "-p 9001:9000/tcp" in cmd
        assert "-p 8000:8000/tcp" in cmd
        
        # Volumes (with override)
        assert "-v /custom/data:/data" in cmd
        assert "-v /var/run/docker.sock:/var/run/docker.sock" in cmd
        
        # Environment
        assert "-e ADMIN_PASSWORD=secret" in cmd
        
        # Network
        assert "--network bridge" in cmd
        
        # Privileged
        assert "--privileged" in cmd
        
        # Capabilities
        assert "--cap-add NET_ADMIN" in cmd
        assert "--cap-add SYS_ADMIN" in cmd


# ---------------------------------------------------------------------------
# Tests for parse_pull_progress
# ---------------------------------------------------------------------------


class TestParsePullProgressDownloading:
    """Tests for parsing docker pull downloading progress."""

    def test_downloading_progress_basic(self):
        """Test basic downloading progress parsing."""
        layer_progress = {}

        parse_pull_progress(
            "abc123: Downloading [====>    ] 10MB/100MB",
            layer_progress
        )

        assert "abc123" in layer_progress
        assert layer_progress["abc123"] == 10

    def test_downloading_progress_50_percent(self):
        """Test 50% downloading progress."""
        layer_progress = {}

        parse_pull_progress(
            "def456: Downloading [=========>          ] 50MB/100MB",
            layer_progress
        )

        assert layer_progress["def456"] == 50

    def test_downloading_progress_with_decimal(self):
        """Test downloading progress with decimal values."""
        layer_progress = {}

        parse_pull_progress(
            "abc123: Downloading [====>    ] 10.5MB/100.5MB",
            layer_progress
        )

        assert "abc123" in layer_progress
        assert layer_progress["abc123"] == 10

    def test_downloading_progress_kilobytes(self):
        """Test downloading progress with KB values."""
        layer_progress = {}

        parse_pull_progress(
            "abc123: Downloading [====>    ] 512KB/1024KB",
            layer_progress
        )

        assert layer_progress["abc123"] == 50

    def test_downloading_progress_gigabytes(self):
        """Test downloading progress with GB values."""
        layer_progress = {}

        parse_pull_progress(
            "abc123: Downloading [====>    ] 1GB/4GB",
            layer_progress
        )

        assert layer_progress["abc123"] == 25

    def test_downloading_updates_existing_layer(self):
        """Test downloading updates existing layer progress."""
        layer_progress = {"abc123": 10}
        
        parse_pull_progress(
            "abc123: Downloading [====>    ] 50MB/100MB",
            layer_progress
        )
        
        assert layer_progress["abc123"] == 50


class TestParsePullProgressExtracting:
    """Tests for parsing docker pull extracting progress."""

    def test_extracting_progress_start(self):
        """Test extracting at start (should be 50%)."""
        layer_progress = {}
        
        parse_pull_progress(
            "abc123: Extracting [>                   ] 0MB/100MB",
            layer_progress
        )
        
        assert layer_progress["abc123"] == 50

    def test_extracting_progress_middle(self):
        """Test extracting at middle (should be 75%)."""
        layer_progress = {}
        
        parse_pull_progress(
            "abc123: Extracting [=========>          ] 50MB/100MB",
            layer_progress
        )
        
        assert layer_progress["abc123"] == 75

    def test_extracting_progress_end(self):
        """Test extracting at end (should be 100%)."""
        layer_progress = {}
        
        parse_pull_progress(
            "abc123: Extracting [===================>] 100MB/100MB",
            layer_progress
        )
        
        assert layer_progress["abc123"] == 100

    def test_extracting_with_decimal(self):
        """Test extracting progress with decimal values."""
        layer_progress = {}
        
        parse_pull_progress(
            "abc123: Extracting [=========>          ] 50.5MB/100.0MB",
            layer_progress
        )
        
        assert "abc123" in layer_progress
        # 50% of extracting = 25% of second half = 75% total
        assert layer_progress["abc123"] == 75


class TestParsePullProgressComplete:
    """Tests for parsing docker pull complete states."""

    def test_download_complete(self):
        """Test download complete status."""
        layer_progress = {"abc123": 50}
        
        parse_pull_progress("abc123: Download complete", layer_progress)
        
        assert layer_progress["abc123"] == 100

    def test_pull_complete(self):
        """Test pull complete status."""
        layer_progress = {"abc123": 75}
        
        parse_pull_progress("abc123: Pull complete", layer_progress)
        
        assert layer_progress["abc123"] == 100

    def test_already_exists(self):
        """Test already exists status."""
        layer_progress = {}
        
        parse_pull_progress("abc123: Already exists", layer_progress)
        
        assert layer_progress["abc123"] == 100


class TestParsePullProgressPulling:
    """Tests for parsing docker pull layer initialization."""

    def test_pulling_fs_layer_new(self):
        """Test pulling fs layer initializes new layer."""
        layer_progress = {}
        
        parse_pull_progress("abc123: Pulling fs layer", layer_progress)
        
        assert "abc123" in layer_progress
        assert layer_progress["abc123"] == 0

    def test_pulling_fs_layer_exists(self):
        """Test pulling fs layer doesn't reset existing layer."""
        layer_progress = {"abc123": 50}
        
        parse_pull_progress("abc123: Pulling fs layer", layer_progress)
        
        # Should not reset existing progress
        assert layer_progress["abc123"] == 50


class TestParsePullProgressOverall:
    """Tests for overall progress calculation."""

    def test_single_layer_progress(self):
        """Test overall progress with single layer."""
        layer_progress = {}
        
        progress = parse_pull_progress(
            "abc123: Downloading [====>    ] 50MB/100MB",
            layer_progress
        )
        
        assert progress == 50

    def test_multiple_layers_progress(self):
        """Test overall progress with multiple layers."""
        layer_progress = {
            "abc123": 100,
            "def456": 50,
        }

        progress = parse_pull_progress(
            "fed789: Downloading [====>    ] 25MB/100MB",
            layer_progress
        )

        # (100 + 50 + 25) / 3 = 58.33 -> 58
        assert progress == 58

    def test_empty_layer_progress(self):
        """Test overall progress with no layers."""
        layer_progress = {}
        
        progress = parse_pull_progress("Some random line", layer_progress)
        
        assert progress == 0

    def test_progress_capped_at_100(self):
        """Test layer progress doesn't exceed 100."""
        layer_progress = {}
        
        parse_pull_progress(
            "abc123: Downloading [===================>] 150MB/100MB",
            layer_progress
        )
        
        assert layer_progress["abc123"] <= 100


class TestParsePullProgressEdgeCases:
    """Tests for edge cases in parse_pull_progress."""

    def test_malformed_line(self):
        """Test handling malformed input."""
        layer_progress = {}
        
        progress = parse_pull_progress("not a valid docker line", layer_progress)
        
        assert progress == 0
        assert len(layer_progress) == 0

    def test_empty_line(self):
        """Test handling empty line."""
        layer_progress = {}
        
        progress = parse_pull_progress("", layer_progress)
        
        assert progress == 0

    def test_zero_total_bytes(self):
        """Test handling zero total bytes (division by zero)."""
        layer_progress = {}
        
        # This should not crash
        progress = parse_pull_progress(
            "abc123: Downloading [>        ] 0MB/0MB",
            layer_progress
        )
        
        # Should handle gracefully
        assert isinstance(progress, int)

    def test_none_input_handling(self):
        """Test that function handles exceptions gracefully."""
        layer_progress = {}
        
        # Force an exception by providing something that causes re.match to fail
        # Actually re.match handles None/bad input, so test with a layer_progress
        # that might cause issues
        progress = parse_pull_progress("abc123: Downloading", layer_progress)
        
        assert progress == 0

    def test_special_characters_in_layer_id(self):
        """Test layer IDs with only hex characters are matched."""
        layer_progress = {}
        
        # Valid hex layer ID
        parse_pull_progress("abcdef123456: Pull complete", layer_progress)
        assert "abcdef123456" in layer_progress

    def test_non_hex_layer_id_ignored(self):
        """Test non-hex layer IDs are not matched."""
        layer_progress = {}

        # Invalid layer ID (contains 'g' which is not hex)
        parse_pull_progress("ghijkl: Pull complete", layer_progress)
        assert "ghijkl" not in layer_progress

    def test_exception_in_progress_calculation(self):
        """Test that exceptions are caught and return 0."""
        # Create a mock that raises exception when iterated
        class BrokenDict(dict):
            def values(self):
                raise ValueError("Broken dict")

        broken_progress = BrokenDict()
        broken_progress["layer1"] = 50

        # This should trigger the exception handler
        progress = parse_pull_progress(
            "abc123: Downloading [====>    ] 50MB/100MB",
            broken_progress
        )

        assert progress == 0


# ---------------------------------------------------------------------------
# Tests for parse_container_inspect
# ---------------------------------------------------------------------------


class TestParseContainerInspectBasic:
    """Tests for basic parse_container_inspect functionality."""

    def test_empty_output(self):
        """Test handling empty JSON array."""
        result = parse_container_inspect("[]")
        
        assert result == {
            "networks": [],
            "named_volumes": [],
            "bind_mounts": []
        }

    def test_empty_string(self):
        """Test handling empty string."""
        result = parse_container_inspect("")
        
        assert result == {
            "networks": [],
            "named_volumes": [],
            "bind_mounts": []
        }

    def test_invalid_json(self):
        """Test handling invalid JSON."""
        result = parse_container_inspect("not valid json")
        
        assert result == {
            "networks": [],
            "named_volumes": [],
            "bind_mounts": []
        }

    def test_null_json(self):
        """Test handling null JSON."""
        result = parse_container_inspect("null")
        
        assert result == {
            "networks": [],
            "named_volumes": [],
            "bind_mounts": []
        }


class TestParseContainerInspectNetworks:
    """Tests for network parsing in parse_container_inspect."""

    def test_single_network(self):
        """Test parsing single network."""
        data = [{
            "NetworkSettings": {
                "Networks": {
                    "bridge": {"NetworkID": "abc123"}
                }
            },
            "Mounts": []
        }]
        
        result = parse_container_inspect(json.dumps(data))
        
        assert result["networks"] == ["bridge"]

    def test_multiple_networks(self):
        """Test parsing multiple networks."""
        data = [{
            "NetworkSettings": {
                "Networks": {
                    "bridge": {"NetworkID": "abc123"},
                    "host": {"NetworkID": "def456"},
                    "my-network": {"NetworkID": "ghi789"}
                }
            },
            "Mounts": []
        }]
        
        result = parse_container_inspect(json.dumps(data))
        
        assert len(result["networks"]) == 3
        assert "bridge" in result["networks"]
        assert "host" in result["networks"]
        assert "my-network" in result["networks"]

    def test_no_networks(self):
        """Test container with no networks."""
        data = [{
            "NetworkSettings": {
                "Networks": {}
            },
            "Mounts": []
        }]
        
        result = parse_container_inspect(json.dumps(data))
        
        assert result["networks"] == []

    def test_missing_network_settings(self):
        """Test container with missing NetworkSettings."""
        data = [{"Mounts": []}]
        
        result = parse_container_inspect(json.dumps(data))
        
        assert result["networks"] == []


class TestParseContainerInspectVolumes:
    """Tests for volume parsing in parse_container_inspect."""

    def test_named_volume(self):
        """Test parsing named volume mount."""
        data = [{
            "NetworkSettings": {"Networks": {}},
            "Mounts": [{
                "Type": "volume",
                "Name": "my-volume",
                "Destination": "/data",
                "Mode": "rw"
            }]
        }]
        
        result = parse_container_inspect(json.dumps(data))
        
        assert len(result["named_volumes"]) == 1
        assert result["named_volumes"][0]["name"] == "my-volume"
        assert result["named_volumes"][0]["destination"] == "/data"
        assert result["named_volumes"][0]["mode"] == "rw"

    def test_multiple_named_volumes(self):
        """Test parsing multiple named volumes."""
        data = [{
            "NetworkSettings": {"Networks": {}},
            "Mounts": [
                {
                    "Type": "volume",
                    "Name": "data-volume",
                    "Destination": "/data",
                    "Mode": "rw"
                },
                {
                    "Type": "volume",
                    "Name": "config-volume",
                    "Destination": "/config",
                    "Mode": "ro"
                }
            ]
        }]
        
        result = parse_container_inspect(json.dumps(data))
        
        assert len(result["named_volumes"]) == 2

    def test_bind_mount(self):
        """Test parsing bind mount."""
        data = [{
            "NetworkSettings": {"Networks": {}},
            "Mounts": [{
                "Type": "bind",
                "Source": "/host/path",
                "Destination": "/container/path",
                "Mode": "rw"
            }]
        }]
        
        result = parse_container_inspect(json.dumps(data))
        
        assert len(result["bind_mounts"]) == 1
        assert result["bind_mounts"][0]["source"] == "/host/path"
        assert result["bind_mounts"][0]["destination"] == "/container/path"
        assert result["bind_mounts"][0]["mode"] == "rw"

    def test_mixed_mounts(self):
        """Test parsing mixed volume and bind mounts."""
        data = [{
            "NetworkSettings": {"Networks": {}},
            "Mounts": [
                {
                    "Type": "volume",
                    "Name": "my-volume",
                    "Destination": "/data",
                    "Mode": "rw"
                },
                {
                    "Type": "bind",
                    "Source": "/var/run/docker.sock",
                    "Destination": "/var/run/docker.sock",
                    "Mode": "rw"
                }
            ]
        }]
        
        result = parse_container_inspect(json.dumps(data))
        
        assert len(result["named_volumes"]) == 1
        assert len(result["bind_mounts"]) == 1

    def test_no_mounts(self):
        """Test container with no mounts."""
        data = [{
            "NetworkSettings": {"Networks": {}},
            "Mounts": []
        }]
        
        result = parse_container_inspect(json.dumps(data))
        
        assert result["named_volumes"] == []
        assert result["bind_mounts"] == []

    def test_missing_mounts_key(self):
        """Test container with missing Mounts key."""
        data = [{"NetworkSettings": {"Networks": {}}}]
        
        result = parse_container_inspect(json.dumps(data))
        
        assert result["named_volumes"] == []
        assert result["bind_mounts"] == []


class TestParseContainerInspectEdgeCases:
    """Tests for edge cases in parse_container_inspect."""

    def test_unknown_mount_type(self):
        """Test mount with unknown type is ignored."""
        data = [{
            "NetworkSettings": {"Networks": {}},
            "Mounts": [{
                "Type": "tmpfs",
                "Destination": "/tmp",
                "Mode": "rw"
            }]
        }]
        
        result = parse_container_inspect(json.dumps(data))
        
        assert result["named_volumes"] == []
        assert result["bind_mounts"] == []

    def test_missing_mount_fields(self):
        """Test mount with missing fields uses defaults."""
        data = [{
            "NetworkSettings": {"Networks": {}},
            "Mounts": [{
                "Type": "volume"
            }]
        }]
        
        result = parse_container_inspect(json.dumps(data))
        
        assert len(result["named_volumes"]) == 1
        assert result["named_volumes"][0]["name"] == ""
        assert result["named_volumes"][0]["destination"] == ""
        assert result["named_volumes"][0]["mode"] == "rw"

    def test_missing_bind_mount_fields(self):
        """Test bind mount with missing fields uses defaults."""
        data = [{
            "NetworkSettings": {"Networks": {}},
            "Mounts": [{
                "Type": "bind"
            }]
        }]
        
        result = parse_container_inspect(json.dumps(data))
        
        assert len(result["bind_mounts"]) == 1
        assert result["bind_mounts"][0]["source"] == ""
        assert result["bind_mounts"][0]["destination"] == ""
        assert result["bind_mounts"][0]["mode"] == "rw"

    def test_full_container_inspect(self):
        """Test parsing complete container inspect output."""
        data = [{
            "Id": "abc123def456",
            "Name": "/my-container",
            "State": {"Status": "running"},
            "NetworkSettings": {
                "Networks": {
                    "bridge": {
                        "NetworkID": "net123",
                        "IPAddress": "172.17.0.2"
                    }
                }
            },
            "Mounts": [
                {
                    "Type": "volume",
                    "Name": "app-data",
                    "Source": "/var/lib/docker/volumes/app-data/_data",
                    "Destination": "/data",
                    "Driver": "local",
                    "Mode": "z",
                    "RW": True,
                    "Propagation": ""
                },
                {
                    "Type": "bind",
                    "Source": "/etc/localtime",
                    "Destination": "/etc/localtime",
                    "Mode": "ro",
                    "RW": False,
                    "Propagation": "rprivate"
                }
            ]
        }]
        
        result = parse_container_inspect(json.dumps(data))
        
        assert result["networks"] == ["bridge"]
        assert len(result["named_volumes"]) == 1
        assert result["named_volumes"][0]["name"] == "app-data"
        assert len(result["bind_mounts"]) == 1
        assert result["bind_mounts"][0]["source"] == "/etc/localtime"

    def test_exception_returns_empty_result(self):
        """Test that any exception returns empty result structure."""
        # Force an exception by passing something that json.loads can parse
        # but doesn't have the expected structure
        result = parse_container_inspect('{"unexpected": "structure"}')
        
        # Should return default structure, not crash
        assert "networks" in result
        assert "named_volumes" in result
        assert "bind_mounts" in result
