"""Extended tests for validation module.

Tests the docker run command validation and validator callbacks.
"""

from lib.validation import (
    CommandValidator,
    CommandAllowlistEntry,
    validate_docker_run_command,
    _validate_volume_mount,
    BLOCKED_DOCKER_RUN_FLAGS,
    BLOCKED_VOLUME_PATTERNS,
)


class TestValidateDockerRunCommand:
    """Tests for validate_docker_run_command function."""

    def test_allows_basic_docker_run(self):
        """Should allow basic docker run command."""
        is_valid, error = validate_docker_run_command("docker run -d nginx:latest")
        assert is_valid is True
        assert error == ""

    def test_blocks_privileged_flag(self):
        """Should block --privileged flag."""
        is_valid, error = validate_docker_run_command("docker run --privileged nginx")
        assert is_valid is False
        assert "not allowed" in error.lower() or "privileged" in error.lower()

    def test_blocks_sys_admin_capability(self):
        """Should block SYS_ADMIN capability."""
        is_valid, error = validate_docker_run_command(
            "docker run --cap-add=SYS_ADMIN nginx"
        )
        assert is_valid is False
        assert "SYS_ADMIN" in error

    def test_blocks_all_capabilities(self):
        """Should block ALL capabilities."""
        is_valid, error = validate_docker_run_command("docker run --cap-add=ALL nginx")
        assert is_valid is False
        assert "ALL" in error

    def test_blocks_host_pid_namespace(self):
        """Should block host PID namespace."""
        is_valid, error = validate_docker_run_command("docker run --pid=host nginx")
        assert is_valid is False
        assert "host" in error.lower()

    def test_blocks_host_network(self):
        """Should block host network mode."""
        is_valid, error = validate_docker_run_command("docker run --network=host nginx")
        assert is_valid is False
        assert "host" in error.lower()

    def test_blocks_host_ipc(self):
        """Should block host IPC namespace."""
        is_valid, error = validate_docker_run_command("docker run --ipc=host nginx")
        assert is_valid is False
        assert "host" in error.lower()

    def test_blocks_device_mount(self):
        """Should block device mounts."""
        is_valid, error = validate_docker_run_command(
            "docker run --device=/dev/sda nginx"
        )
        assert is_valid is False
        assert "device" in error.lower()

    def test_blocks_unconfined_security_opt(self):
        """Should block unconfined security options."""
        is_valid, error = validate_docker_run_command(
            "docker run --security-opt=apparmor=unconfined nginx"
        )
        assert is_valid is False
        assert "security" in error.lower()

    def test_blocks_docker_socket_volume(self):
        """Should block docker socket volume mount."""
        is_valid, error = validate_docker_run_command(
            "docker run -v /var/run/docker.sock:/var/run/docker.sock nginx"
        )
        assert is_valid is False
        assert "volume" in error.lower() or "mount" in error.lower()

    def test_blocks_etc_volume(self):
        """Should block /etc volume mount."""
        is_valid, error = validate_docker_run_command(
            "docker run -v /etc/passwd:/etc/passwd nginx"
        )
        assert is_valid is False

    def test_allows_read_only_volume(self):
        """Should allow read-only volume mounts for some paths."""
        # Read-only mounts to non-critical paths should be allowed
        is_valid, error = validate_docker_run_command(
            "docker run -v /data/app:/app:ro nginx"
        )
        assert is_valid is True

    def test_blocks_proc_even_readonly(self):
        """Should block /proc even read-only."""
        is_valid, error = validate_docker_run_command(
            "docker run -v /proc:/host/proc:ro nginx"
        )
        assert is_valid is False

    def test_allows_named_volumes(self):
        """Should allow named volumes."""
        is_valid, error = validate_docker_run_command(
            "docker run -v myvolume:/data nginx"
        )
        assert is_valid is True

    def test_handles_invalid_command_syntax(self):
        """Should handle invalid shell syntax."""
        is_valid, error = validate_docker_run_command("docker run -v 'unclosed")
        assert is_valid is False
        assert "syntax" in error.lower()

    def test_case_insensitive_flag_detection(self):
        """Should detect flags case-insensitively."""
        is_valid, error = validate_docker_run_command("docker run --PRIVILEGED nginx")
        assert is_valid is False


class TestValidateVolumeMount:
    """Tests for _validate_volume_mount helper."""

    def test_allows_named_volume(self):
        """Should allow named volumes."""
        assert _validate_volume_mount("myvolume:/data") is True

    def test_blocks_docker_socket(self):
        """Should block docker socket."""
        assert _validate_volume_mount("/var/run/docker.sock:/sock") is False
        assert _validate_volume_mount("/run/docker.sock:/sock") is False

    def test_blocks_etc_path(self):
        """Should block /etc paths."""
        assert _validate_volume_mount("/etc/passwd:/etc/passwd") is False

    def test_blocks_root_path(self):
        """Should block /root path."""
        assert _validate_volume_mount("/root:/data") is False

    def test_allows_readonly_for_some_paths(self):
        """Should allow readonly for non-critical paths."""
        assert _validate_volume_mount("/var/log:/logs:ro") is True

    def test_blocks_sys_even_readonly(self):
        """Should block /sys even readonly."""
        assert _validate_volume_mount("/sys:/host/sys:ro") is False

    def test_blocks_proc_even_readonly(self):
        """Should block /proc even readonly."""
        assert _validate_volume_mount("/proc:/host/proc:ro") is False


class TestCommandValidatorCallback:
    """Tests for CommandValidator with validator callbacks."""

    def test_calls_validator_callback(self):
        """Should call validator callback for matching commands."""
        callback_called = []

        def test_validator(cmd):
            callback_called.append(cmd)
            return (True, "")

        allowlist = [
            CommandAllowlistEntry(
                pattern=r"^test\s+command$",
                description="Test command",
                validator=test_validator,
            )
        ]
        validator = CommandValidator(allowlist)

        is_valid, error = validator.validate("test command")

        assert is_valid is True
        assert len(callback_called) == 1
        assert callback_called[0] == "test command"

    def test_rejects_when_callback_returns_false(self):
        """Should reject when validator callback returns False."""

        def blocking_validator(cmd):
            return (False, "Command blocked by validator")

        allowlist = [
            CommandAllowlistEntry(
                pattern=r"^test\s+command$",
                description="Test command",
                validator=blocking_validator,
            )
        ]
        validator = CommandValidator(allowlist)

        is_valid, error = validator.validate("test command")

        assert is_valid is False
        assert "blocked by validator" in error

    def test_allows_when_no_callback(self):
        """Should allow when no validator callback is set."""
        allowlist = [
            CommandAllowlistEntry(
                pattern=r"^test\s+command$",
                description="Test command",
                validator=None,
            )
        ]
        validator = CommandValidator(allowlist)

        is_valid, error = validator.validate("test command")

        assert is_valid is True

    def test_docker_run_uses_validator_callback(self):
        """Should use validate_docker_run_command for docker run entries."""
        # The default COMMAND_ALLOWLIST has a docker run entry with validator
        from lib.validation import COMMAND_ALLOWLIST

        # Find entry for docker run (description: "Run Docker container (detached)")
        docker_run_entry = next(
            (
                e
                for e in COMMAND_ALLOWLIST
                if "docker container" in e.description.lower()
                or "run docker" in e.description.lower()
            ),
            None,
        )

        assert docker_run_entry is not None
        assert docker_run_entry.validator is validate_docker_run_command


class TestBlockedDockerRunFlags:
    """Tests for BLOCKED_DOCKER_RUN_FLAGS set."""

    def test_contains_privileged(self):
        """Should contain --privileged."""
        assert "--privileged" in BLOCKED_DOCKER_RUN_FLAGS

    def test_contains_dangerous_caps(self):
        """Should contain dangerous capabilities."""
        assert "--cap-add=ALL" in BLOCKED_DOCKER_RUN_FLAGS
        assert "--cap-add=SYS_ADMIN" in BLOCKED_DOCKER_RUN_FLAGS

    def test_contains_host_namespaces(self):
        """Should contain host namespace flags."""
        assert "--pid=host" in BLOCKED_DOCKER_RUN_FLAGS
        assert "--network=host" in BLOCKED_DOCKER_RUN_FLAGS
        assert "--ipc=host" in BLOCKED_DOCKER_RUN_FLAGS


class TestBlockedVolumePatterns:
    """Tests for BLOCKED_VOLUME_PATTERNS list."""

    def test_contains_docker_socket(self):
        """Should contain docker socket paths."""
        assert "/var/run/docker.sock" in BLOCKED_VOLUME_PATTERNS
        assert "/run/docker.sock" in BLOCKED_VOLUME_PATTERNS

    def test_contains_system_paths(self):
        """Should contain system paths."""
        assert "/etc/" in BLOCKED_VOLUME_PATTERNS
        assert "/var/" in BLOCKED_VOLUME_PATTERNS
        assert "/usr/" in BLOCKED_VOLUME_PATTERNS
        assert "/bin/" in BLOCKED_VOLUME_PATTERNS
