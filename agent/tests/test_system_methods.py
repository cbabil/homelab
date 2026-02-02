"""Tests for system RPC methods.

Tests system info, exec, preflight check, and metrics.
"""

from unittest.mock import MagicMock, patch


from rpc.methods.system import SystemMethods, _prepare_command


class TestPrepareCommand:
    """Tests for _prepare_command helper function."""

    def test_simple_command_uses_no_shell(self):
        """Should use shell=False for simple commands."""
        cmd_args, use_shell = _prepare_command("docker ps")
        assert use_shell is False
        assert cmd_args == ["docker", "ps"]

    def test_command_with_args_uses_no_shell(self):
        """Should use shell=False for commands with arguments."""
        cmd_args, use_shell = _prepare_command("docker run -d nginx:latest")
        assert use_shell is False
        assert cmd_args == ["docker", "run", "-d", "nginx:latest"]

    def test_command_with_redirect_uses_shell(self):
        """Should use shell=True for commands with redirects."""
        cmd_args, use_shell = _prepare_command("docker inspect foo 2>/dev/null")
        assert use_shell is True
        assert cmd_args == "docker inspect foo 2>/dev/null"

    def test_command_with_pipe_uses_shell(self):
        """Should use shell=True for commands with pipes."""
        cmd_args, use_shell = _prepare_command("docker ps | grep nginx")
        assert use_shell is True

    def test_command_with_semicolon_uses_shell(self):
        """Should use shell=True for commands with semicolons."""
        cmd_args, use_shell = _prepare_command("echo foo; echo bar")
        assert use_shell is True

    def test_command_with_ampersand_uses_shell(self):
        """Should use shell=True for commands with &&."""
        cmd_args, use_shell = _prepare_command("cd /tmp && ls")
        assert use_shell is True

    def test_command_with_backticks_uses_shell(self):
        """Should use shell=True for commands with backticks."""
        cmd_args, use_shell = _prepare_command("echo `date`")
        assert use_shell is True

    def test_command_with_dollar_paren_uses_shell(self):
        """Should use shell=True for commands with $()."""
        cmd_args, use_shell = _prepare_command("echo $(date)")
        assert use_shell is True

    def test_quoted_arguments_preserved(self):
        """Should preserve quoted arguments."""
        cmd_args, use_shell = _prepare_command("docker run --name 'my app' nginx")
        assert use_shell is False
        assert cmd_args == ["docker", "run", "--name", "my app", "nginx"]


class TestSystemMethodsInfo:
    """Tests for SystemMethods.info()."""

    def test_returns_system_info(self):
        """Should return system info dictionary."""
        mock_client = MagicMock()
        mock_client.version.return_value = {"Version": "24.0.0"}

        methods = SystemMethods()

        with patch("rpc.methods.system.get_client", return_value=mock_client):
            with patch("platform.release", return_value="5.15.0"):
                with patch("platform.machine", return_value="x86_64"):
                    with patch("platform.node", return_value="server1"):
                        result = methods.info()

        assert "os" in result
        assert result["kernel"] == "5.15.0"
        assert result["arch"] == "x86_64"
        assert result["hostname"] == "server1"
        assert result["docker_version"] == "24.0.0"

    def test_handles_docker_unavailable(self):
        """Should handle Docker being unavailable."""
        mock_client = MagicMock()
        mock_client.version.side_effect = Exception("Docker not running")

        methods = SystemMethods()

        with patch("rpc.methods.system.get_client", return_value=mock_client):
            result = methods.info()

        assert result["docker_version"] == "unknown"


class TestSystemMethodsExec:
    """Tests for SystemMethods.exec()."""

    def test_executes_allowed_command(self):
        """Should execute allowed command."""
        methods = SystemMethods()

        with patch("rpc.methods.system.validate_command", return_value=(True, None)):
            with patch(
                "rpc.methods.system.acquire_command_slot", return_value=(True, None)
            ):
                with patch("rpc.methods.system.release_command_slot"):
                    with patch("subprocess.run") as mock_run:
                        mock_run.return_value = MagicMock(
                            stdout="output",
                            stderr="",
                            returncode=0,
                        )
                        result = methods.exec("df -h")

        assert result["stdout"] == "output"
        assert result["exit_code"] == 0

    def test_blocks_disallowed_command(self):
        """Should block disallowed command."""
        methods = SystemMethods()

        with patch(
            "rpc.methods.system.validate_command",
            return_value=(False, "Command not in allowlist"),
        ):
            result = methods.exec("rm -rf /")

        assert result["exit_code"] == -1
        assert result["security_blocked"] is True
        assert "not allowed" in result["stderr"]

    def test_handles_rate_limit(self):
        """Should handle rate limiting."""
        methods = SystemMethods()

        with patch("rpc.methods.system.validate_command", return_value=(True, None)):
            with patch(
                "rpc.methods.system.acquire_command_slot",
                return_value=(False, "Too many commands"),
            ):
                result = methods.exec("df -h")

        assert result["exit_code"] == -1
        assert result["rate_limited"] is True

    def test_handles_timeout(self):
        """Should handle command timeout."""
        import subprocess

        methods = SystemMethods()

        with patch("rpc.methods.system.validate_command", return_value=(True, None)):
            with patch(
                "rpc.methods.system.acquire_command_slot", return_value=(True, None)
            ):
                with patch("rpc.methods.system.release_command_slot"):
                    with patch("subprocess.run") as mock_run:
                        mock_run.side_effect = subprocess.TimeoutExpired("cmd", 60)
                        result = methods.exec("sleep 100", timeout=60)

        assert result["exit_code"] == -1
        assert "timed out" in result["stderr"]

    def test_handles_execution_error(self):
        """Should handle execution errors."""
        methods = SystemMethods()

        with patch("rpc.methods.system.validate_command", return_value=(True, None)):
            with patch(
                "rpc.methods.system.acquire_command_slot", return_value=(True, None)
            ):
                with patch("rpc.methods.system.release_command_slot"):
                    with patch("subprocess.run") as mock_run:
                        mock_run.side_effect = Exception("Execution failed")
                        result = methods.exec("echo test")

        assert result["exit_code"] == -1
        assert "failed" in result["stderr"]


class TestSystemMethodsPreflightCheck:
    """Tests for SystemMethods.preflight_check()."""

    def test_returns_success_when_all_ok(self):
        """Should return success when all checks pass."""
        mock_client = MagicMock()
        mock_client.version.return_value = {"Version": "24.0.0"}
        mock_client.ping.return_value = True

        methods = SystemMethods()

        with patch("rpc.methods.system.get_client", return_value=mock_client):
            with patch("psutil.disk_usage") as mock_disk:
                mock_disk.return_value = MagicMock(
                    free=10 * 1024**3,  # 10GB free
                    total=100 * 1024**3,
                )
                with patch("psutil.virtual_memory") as mock_mem:
                    mock_mem.return_value = MagicMock(
                        available=500 * 1024**2,  # 500MB available (above 256MB min)
                        total=8 * 1024**3,
                    )
                    with patch("os.path.exists", return_value=False):
                        result = methods.preflight_check()

        assert result["success"] is True
        assert result["docker"]["ok"] is True
        assert len(result["errors"]) == 0

    def test_detects_docker_failure(self):
        """Should detect Docker daemon failure."""
        mock_client = MagicMock()
        mock_client.ping.side_effect = Exception("Docker not responding")

        methods = SystemMethods()

        with patch("rpc.methods.system.get_client", return_value=mock_client):
            with patch("psutil.disk_usage") as mock_disk:
                mock_disk.return_value = MagicMock(
                    free=10 * 1024**3, total=100 * 1024**3
                )
                with patch("psutil.virtual_memory") as mock_mem:
                    mock_mem.return_value = MagicMock(
                        available=2 * 1024**2, total=8 * 1024**2
                    )
                    with patch("os.path.exists", return_value=False):
                        result = methods.preflight_check()

        assert result["success"] is False
        assert result["docker"]["ok"] is False

    def test_detects_low_disk_space(self):
        """Should detect insufficient disk space."""
        mock_client = MagicMock()
        mock_client.version.return_value = {"Version": "24.0.0"}
        mock_client.ping.return_value = True

        methods = SystemMethods()

        with patch("rpc.methods.system.get_client", return_value=mock_client):
            with patch("psutil.disk_usage") as mock_disk:
                mock_disk.return_value = MagicMock(
                    free=1 * 1024**3,  # Only 1GB free
                    total=100 * 1024**3,
                )
                with patch("psutil.virtual_memory") as mock_mem:
                    mock_mem.return_value = MagicMock(
                        available=2 * 1024**2, total=8 * 1024**2
                    )
                    with patch("os.path.exists", return_value=False):
                        result = methods.preflight_check(min_disk_gb=3)

        assert result["success"] is False
        assert any("free" in e and "GB" in e for e in result["errors"])

    def test_detects_low_memory(self):
        """Should detect insufficient memory."""
        mock_client = MagicMock()
        mock_client.version.return_value = {"Version": "24.0.0"}
        mock_client.ping.return_value = True

        methods = SystemMethods()

        with patch("rpc.methods.system.get_client", return_value=mock_client):
            with patch("psutil.disk_usage") as mock_disk:
                mock_disk.return_value = MagicMock(
                    free=10 * 1024**3, total=100 * 1024**3
                )
                with patch("psutil.virtual_memory") as mock_mem:
                    mock_mem.return_value = MagicMock(
                        available=100 * 1024**2,  # Only 100MB
                        total=8 * 1024**2,
                    )
                    with patch("os.path.exists", return_value=False):
                        result = methods.preflight_check(min_memory_mb=256)

        assert result["success"] is False
        assert any("MB" in e for e in result["errors"])


class TestSystemMethodsPrepareVolumes:
    """Tests for SystemMethods.prepare_volumes()."""

    def test_skips_named_volumes(self):
        """Should skip named volumes (no leading /)."""
        methods = SystemMethods()

        result = methods.prepare_volumes([{"host": "myvolume", "container": "/data"}])

        assert result["results"][0]["status"] == "skipped"
        assert result["results"][0]["reason"] == "named volume"

    def test_skips_disallowed_paths(self):
        """Should skip paths not in allowed directories."""
        methods = SystemMethods()

        result = methods.prepare_volumes(
            [{"host": "/etc/passwd", "container": "/data"}]
        )

        assert result["results"][0]["status"] == "skipped"
        assert "not in allowed paths" in result["results"][0]["reason"]

    def test_creates_allowed_directory(self):
        """Should create directory for allowed path."""
        methods = SystemMethods()

        with patch("os.path.exists", return_value=False):
            with patch("os.makedirs") as mock_makedirs:
                with patch("os.chown"):
                    with patch("os.walk", return_value=[]):
                        result = methods.prepare_volumes(
                            [{"host": "/DATA/myapp/config", "container": "/config"}]
                        )

        assert result["success"] is True
        assert result["results"][0]["status"] == "ok"
        mock_makedirs.assert_called()

    def test_handles_permission_error(self):
        """Should handle permission errors."""
        methods = SystemMethods()

        with patch("os.path.exists", return_value=False):
            with patch("os.makedirs", side_effect=PermissionError("Access denied")):
                result = methods.prepare_volumes(
                    [{"host": "/DATA/protected", "container": "/data"}]
                )

        assert result["success"] is False
        assert result["results"][0]["status"] == "error"


class TestSystemMethodsGetMetrics:
    """Tests for SystemMethods.get_metrics()."""

    def test_returns_metrics(self):
        """Should return system metrics."""
        mock_client = MagicMock()
        mock_container = MagicMock()
        mock_container.status = "running"
        mock_client.containers.list.return_value = [mock_container]

        methods = SystemMethods()

        with patch("rpc.methods.system.get_client", return_value=mock_client):
            with patch("psutil.cpu_percent", return_value=25.5):
                with patch("psutil.virtual_memory") as mock_mem:
                    mock_mem.return_value = MagicMock(
                        used=2 * 1024**3,
                        total=8 * 1024**3,
                        percent=25.0,
                    )
                    with patch("psutil.disk_usage") as mock_disk:
                        mock_disk.return_value = MagicMock(
                            used=50 * 1024**3,
                            total=500 * 1024**3,
                            percent=10.0,
                        )
                        with patch("os.path.exists", return_value=False):
                            result = methods.get_metrics()

        assert result["cpu"] == 25.5
        assert "memory" in result
        assert "disk" in result
        assert result["containers"]["running"] == 1

    def test_handles_docker_error(self):
        """Should handle Docker errors gracefully."""
        mock_client = MagicMock()
        mock_client.containers.list.side_effect = Exception("Docker error")

        methods = SystemMethods()

        with patch("rpc.methods.system.get_client", return_value=mock_client):
            with patch("psutil.cpu_percent", return_value=10.0):
                with patch("psutil.virtual_memory") as mock_mem:
                    mock_mem.return_value = MagicMock(used=1, total=4, percent=25.0)
                    with patch("psutil.disk_usage") as mock_disk:
                        mock_disk.return_value = MagicMock(
                            used=1, total=10, percent=10.0
                        )
                        with patch("os.path.exists", return_value=False):
                            result = methods.get_metrics()

        # Should still return metrics, just with 0 containers
        assert result["containers"]["running"] == 0
        assert result["containers"]["stopped"] == 0
