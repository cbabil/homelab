"""
Unit tests for services/deployment/scripts.py

Tests shell script generation functions for Docker operations.
These scripts are designed to run in a single SSH connection to prevent
overwhelming sshd with many rapid connections.
"""

from services.deployment.scripts import (
    background_pull_script,
    cleanup_container_script,
    cleanup_failed_deployment_script,
    cleanup_pull_job_script,
    create_container_script,
    health_check_script,
    poll_pull_status_script,
    preflight_check_script,
    status_check_script,
    uninstall_script,
)


class TestCleanupContainerScript:
    """Tests for cleanup_container_script function."""

    def test_basic_cleanup(self):
        """Script should stop and remove container."""
        script = cleanup_container_script("my-container")

        assert "docker stop my-container" in script
        assert "docker rm -v my-container" in script
        assert "CLEANUP_DONE" in script

    def test_cleanup_with_image(self):
        """Script should include image removal when image is provided."""
        script = cleanup_container_script("test-app", "nginx:latest")

        assert "docker stop test-app" in script
        assert "docker rm -v test-app" in script
        assert "docker rmi nginx:latest" in script
        assert "CLEANUP_DONE" in script

    def test_cleanup_without_image(self):
        """Script should not include image removal when image is None."""
        script = cleanup_container_script("test-app", None)

        assert "docker stop test-app" in script
        assert "docker rm -v test-app" in script
        assert "docker rmi" not in script

    def test_cleanup_errors_suppressed(self):
        """Script should suppress errors with || true."""
        script = cleanup_container_script("my-container")

        assert "2>/dev/null || true" in script

    def test_cleanup_special_characters_in_name(self):
        """Script should handle container names with special characters."""
        script = cleanup_container_script("my-app_v1.2.3")

        assert "docker stop my-app_v1.2.3" in script
        assert "docker rm -v my-app_v1.2.3" in script


class TestCreateContainerScript:
    """Tests for create_container_script function."""

    def test_basic_creation(self):
        """Script should prune images and run container."""
        run_cmd = "docker run -d --name test nginx:latest"
        script = create_container_script(run_cmd)

        assert "docker image prune -f" in script
        assert run_cmd in script

    def test_captures_container_id(self):
        """Script should capture and output container ID on success."""
        script = create_container_script("docker run -d test")

        assert "CONTAINER_ID=$(" in script
        assert "SUCCESS:$CONTAINER_ID" in script

    def test_captures_exit_code(self):
        """Script should capture exit code."""
        script = create_container_script("docker run -d test")

        assert "EXIT_CODE=$?" in script

    def test_reports_failure(self):
        """Script should report failure with exit code."""
        script = create_container_script("docker run -d test")

        assert "FAILED:$EXIT_CODE" in script
        assert "if [ $EXIT_CODE -eq 0 ]" in script

    def test_complex_run_command(self):
        """Script should handle complex docker run commands."""
        run_cmd = (
            "docker run -d --name webapp -p 8080:80 -v /data:/app/data "
            "-e DB_HOST=localhost --restart unless-stopped nginx:alpine"
        )
        script = create_container_script(run_cmd)

        assert run_cmd in script


class TestStatusCheckScript:
    """Tests for status_check_script function."""

    def test_checks_container_status(self):
        """Script should check container status."""
        script = status_check_script("abc123")

        assert "docker inspect" in script
        assert "abc123" in script
        assert "STATUS:" in script

    def test_checks_health_status(self):
        """Script should check health status."""
        script = status_check_script("container-id")

        assert ".State.Health.Status" in script
        assert "HEALTH:" in script

    def test_checks_restart_count(self):
        """Script should check restart count."""
        script = status_check_script("container-id")

        assert ".RestartCount" in script
        assert "RESTARTS:" in script

    def test_outputs_logs_on_failure(self):
        """Script should output logs when container fails."""
        script = status_check_script("container-id")

        assert "docker logs --tail 10" in script
        assert "LOGS:" in script

    def test_checks_multiple_failure_conditions(self):
        """Script should check exited, dead, restarting, and unhealthy."""
        script = status_check_script("test-container")

        assert '"exited"' in script
        assert '"dead"' in script
        assert '"restarting"' in script
        assert '"unhealthy"' in script

    def test_handles_unknown_status(self):
        """Script should handle unknown container with fallback."""
        script = status_check_script("unknown-container")

        assert '|| echo "unknown"' in script
        assert '|| echo "none"' in script
        assert '|| echo "0"' in script


class TestUninstallScript:
    """Tests for uninstall_script function."""

    def test_basic_uninstall(self):
        """Script should stop and remove container."""
        script = uninstall_script("my-app")

        assert "docker stop my-app" in script
        assert "docker rm my-app" in script
        assert "CLEANUP_COMPLETE" in script

    def test_gets_container_info(self):
        """Script should get image, volumes, and networks."""
        script = uninstall_script("test-container")

        assert "IMAGE_NAME=$(docker inspect" in script
        assert "VOLUMES=$(docker inspect" in script
        assert "NETWORKS=$(docker inspect" in script

    def test_outputs_container_info(self):
        """Script should output IMAGE, VOLUMES, NETWORKS."""
        script = uninstall_script("test-app")

        assert 'echo "IMAGE:$IMAGE_NAME"' in script
        assert 'echo "VOLUMES:$VOLUMES"' in script
        assert 'echo "NETWORKS:$NETWORKS"' in script

    def test_removes_volumes_by_default(self):
        """Script should remove unused volumes by default."""
        script = uninstall_script("my-app", remove_data=True)

        assert "docker volume rm" in script
        assert "for VOL in $VOLUMES" in script
        assert "REMOVED:volume:" in script

    def test_skips_volumes_in_use(self):
        """Script should skip volumes in use."""
        script = uninstall_script("my-app")

        assert "USERS=$(docker ps -a --filter volume=" in script
        assert "SKIPPED:volume:" in script

    def test_removes_unused_networks(self):
        """Script should remove unused custom networks."""
        script = uninstall_script("my-app")

        assert "docker network rm" in script
        assert "for NET in $NETWORKS" in script
        assert "REMOVED:network:" in script

    def test_skips_builtin_networks(self):
        """Script should skip bridge, host, and none networks."""
        script = uninstall_script("my-app")

        assert '"bridge"' in script
        assert '"host"' in script
        assert '"none"' in script

    def test_skips_networks_in_use(self):
        """Script should skip networks with containers."""
        script = uninstall_script("my-app")

        assert "docker network inspect" in script
        assert "SKIPPED:network:" in script

    def test_removes_unused_image(self):
        """Script should remove image if unused."""
        script = uninstall_script("my-app")

        assert "docker rmi $IMAGE_NAME" in script
        assert "REMOVED:image:" in script

    def test_skips_image_in_use(self):
        """Script should skip image if other containers use it."""
        script = uninstall_script("my-app")

        assert "--filter ancestor=$IMAGE_NAME" in script
        assert "SKIPPED:image:" in script

    def test_no_volume_removal_when_disabled(self):
        """Script should not remove volumes when remove_data=False."""
        script = uninstall_script("my-app", remove_data=False)

        assert "for VOL in $VOLUMES" not in script
        assert "docker volume rm" not in script

    def test_network_removal_even_without_data(self):
        """Script should remove networks even when remove_data=False."""
        script = uninstall_script("my-app", remove_data=False)

        assert "for NET in $NETWORKS" in script
        assert "docker network rm" in script

    def test_script_uses_shebang(self):
        """Script should start with bash shebang."""
        script = uninstall_script("test")

        assert script.strip().startswith("#!/bin/bash")

    def test_script_uses_set_e(self):
        """Script should use set -e for error handling."""
        script = uninstall_script("test")

        assert "set -e" in script

    def test_includes_delay_after_removal(self):
        """Script should include delay after container removal."""
        script = uninstall_script("my-app")

        assert "sleep 1" in script


class TestCleanupFailedDeploymentScript:
    """Tests for cleanup_failed_deployment_script function."""

    def test_basic_cleanup(self):
        """Script should clean up container."""
        script = cleanup_failed_deployment_script("failed-container")

        assert "docker stop failed-container" in script
        assert "docker rm -f failed-container" in script
        assert "CLEANUP_DONE" in script

    def test_with_image(self):
        """Script should remove unused image when provided."""
        script = cleanup_failed_deployment_script("test-app", "nginx:latest")

        assert "docker rmi nginx:latest" in script
        assert "IMAGE_REMOVED" in script

    def test_without_image(self):
        """Script should not include image removal when not provided."""
        script = cleanup_failed_deployment_script("test-app", None)

        assert "docker rmi" not in script

    def test_checks_image_in_use(self):
        """Script should check if image is used by other containers."""
        script = cleanup_failed_deployment_script("app", "myimage:v1")

        assert "--filter ancestor=myimage:v1" in script
        assert "USERS=$(docker ps -a" in script

    def test_reports_container_removed(self):
        """Script should report when container is removed."""
        script = cleanup_failed_deployment_script("my-container")

        assert "CONTAINER_REMOVED" in script

    def test_includes_delay(self):
        """Script should include delay after container removal."""
        script = cleanup_failed_deployment_script("my-container")

        assert "sleep 1" in script

    def test_empty_container_name(self):
        """Script should handle empty container name gracefully."""
        script = cleanup_failed_deployment_script("")

        # Should still produce valid script with CLEANUP_DONE
        assert "CLEANUP_DONE" in script
        # Should not include container stop/rm for empty name
        assert "docker stop " not in script or "docker stop  " not in script

    def test_script_starts_with_shebang(self):
        """Script should start with bash shebang."""
        script = cleanup_failed_deployment_script("test")

        assert script.startswith("#!/bin/bash")


class TestBackgroundPullScript:
    """Tests for background_pull_script function."""

    def test_creates_work_directory(self):
        """Script should create /tmp/tomo work directory."""
        script = background_pull_script("nginx:latest", "job-123")

        assert 'WORK_DIR="/tmp/tomo"' in script
        assert 'mkdir -p "$WORK_DIR"' in script

    def test_checks_existing_image(self):
        """Script should check if image already exists locally."""
        script = background_pull_script("nginx:latest", "job-123")

        assert "docker image inspect nginx:latest" in script
        assert "IMAGE_EXISTS" in script

    def test_skips_pull_if_image_exists(self):
        """Script should skip pull and return immediately if image exists."""
        script = background_pull_script("myapp:v1", "job-abc")

        assert "exit 0" in script
        assert "Image already exists" in script

    def test_checks_already_running(self):
        """Script should check if job is already running."""
        script = background_pull_script("nginx:latest", "job-123")

        assert 'if [ -f "$WORK_DIR/job-123.pid" ]' in script
        assert "ALREADY_RUNNING:" in script

    def test_uses_nohup_for_background(self):
        """Script should use nohup to survive SSH disconnect."""
        script = background_pull_script("nginx:latest", "job-123")

        assert "nohup /bin/bash -c" in script

    def test_applies_resource_limits(self):
        """Script should limit memory and CPU priority."""
        script = background_pull_script("nginx:latest", "job-123")

        assert "ulimit -v" in script
        assert "ionice -c 3" in script
        assert "nice -n 19" in script

    def test_creates_status_files(self):
        """Script should create PID and status files."""
        script = background_pull_script("nginx:latest", "job-id")

        assert "job-id.pid" in script
        assert "job-id.status" in script
        assert "job-id.log" in script

    def test_outputs_started_with_pid(self):
        """Script should output STARTED with PID."""
        script = background_pull_script("nginx:latest", "job-123")

        assert "STARTED:" in script
        assert "cat $WORK_DIR/job-123.pid" in script

    def test_docker_pull_command(self):
        """Script should include docker pull command."""
        script = background_pull_script("myregistry.io/app:v2.0", "job-xyz")

        assert "docker pull myregistry.io/app:v2.0" in script

    def test_script_uses_shebang(self):
        """Script should start with bash shebang."""
        script = background_pull_script("nginx:latest", "job-1")

        assert script.strip().startswith("#!/bin/bash")


class TestPollPullStatusScript:
    """Tests for poll_pull_status_script function."""

    def test_checks_pid_file_exists(self):
        """Script should check if PID file exists."""
        script = poll_pull_status_script("job-123")

        assert 'PID_FILE="$WORK_DIR/job-123.pid"' in script
        assert 'if [ ! -f "$PID_FILE" ]' in script

    def test_returns_not_found_without_pid(self):
        """Script should return not_found status if no PID file."""
        script = poll_pull_status_script("job-123")

        assert "STATUS:not_found" in script

    def test_checks_status_file(self):
        """Script should check for status file."""
        script = poll_pull_status_script("job-abc")

        assert 'STATUS_FILE="$WORK_DIR/job-abc.status"' in script
        assert 'if [ -f "$STATUS_FILE" ]' in script

    def test_reports_completed_on_success(self):
        """Script should report completed when exit code is 0."""
        script = poll_pull_status_script("job-123")

        assert '"$EXIT_CODE" = "0"' in script
        assert "STATUS:completed" in script

    def test_reports_failed_on_error(self):
        """Script should report failed when exit code is non-zero."""
        script = poll_pull_status_script("job-123")

        assert "STATUS:failed" in script

    def test_checks_if_process_running(self):
        """Script should check if process is still running."""
        script = poll_pull_status_script("job-123")

        assert "kill -0" in script
        assert "STATUS:running" in script

    def test_outputs_exit_code(self):
        """Script should output exit code."""
        script = poll_pull_status_script("job-123")

        assert "EXIT_CODE:" in script

    def test_outputs_pid_when_running(self):
        """Script should output PID when process is running."""
        script = poll_pull_status_script("job-123")

        assert "PID:$PID" in script

    def test_includes_log_output(self):
        """Script should include last 30 lines of log."""
        script = poll_pull_status_script("job-123")

        assert "tail -n 30" in script
        assert 'LOG_FILE="$WORK_DIR/job-123.log"' in script
        assert "LOG_START" in script
        assert "LOG_END" in script

    def test_reports_failed_if_process_died(self):
        """Script should report failed with -1 if process died without status."""
        script = poll_pull_status_script("job-123")

        assert "EXIT_CODE:-1" in script

    def test_script_uses_shebang(self):
        """Script should start with bash shebang."""
        script = poll_pull_status_script("job-1")

        assert script.strip().startswith("#!/bin/bash")


class TestCleanupPullJobScript:
    """Tests for cleanup_pull_job_script function."""

    def test_removes_all_job_files(self):
        """Script should remove PID, status, and log files."""
        script = cleanup_pull_job_script("job-123")

        assert "job-123.pid" in script
        assert "job-123.status" in script
        assert "job-123.log" in script
        assert "rm -f" in script

    def test_uses_work_directory(self):
        """Script should use /tmp/tomo work directory."""
        script = cleanup_pull_job_script("job-abc")

        assert 'WORK_DIR="/tmp/tomo"' in script

    def test_outputs_cleaned_confirmation(self):
        """Script should output CLEANED on completion."""
        script = cleanup_pull_job_script("job-123")

        assert 'echo "CLEANED"' in script

    def test_script_uses_shebang(self):
        """Script should start with bash shebang."""
        script = cleanup_pull_job_script("job-1")

        assert script.strip().startswith("#!/bin/bash")

    def test_handles_special_characters_in_job_id(self):
        """Script should handle job IDs with special characters."""
        script = cleanup_pull_job_script("job_test-123.abc")

        assert "job_test-123.abc.pid" in script


class TestPreflightCheckScript:
    """Tests for preflight_check_script function."""

    def test_checks_docker_daemon(self):
        """Script should check if Docker daemon is responding."""
        script = preflight_check_script()

        assert "docker info" in script
        assert "ERROR:DOCKER:" in script
        assert "Docker daemon not responding" in script

    def test_checks_disk_space(self):
        """Script should check available disk space."""
        script = preflight_check_script(min_disk_gb=10)

        assert "df " in script
        assert "AVAIL_GB" in script
        assert "ERROR:DISK:" in script

    def test_default_disk_requirement(self):
        """Script should use default 5GB disk requirement."""
        script = preflight_check_script()

        assert "-lt 5" in script or "5GB" in script

    def test_custom_disk_requirement(self):
        """Script should use custom disk requirement."""
        script = preflight_check_script(min_disk_gb=20)

        assert "20" in script

    def test_checks_memory(self):
        """Script should check available memory."""
        script = preflight_check_script(min_memory_mb=512)

        assert "free -m" in script
        assert "AVAIL_MB" in script
        assert "ERROR:MEMORY:" in script

    def test_default_memory_requirement(self):
        """Script should use default 256MB memory requirement."""
        script = preflight_check_script()

        assert "256" in script

    def test_custom_memory_requirement(self):
        """Script should use custom memory requirement."""
        script = preflight_check_script(min_memory_mb=1024)

        assert "1024" in script

    def test_uses_docker_root_dir(self):
        """Script should check disk space in Docker root directory."""
        script = preflight_check_script()

        assert "docker info --format" in script
        assert "DockerRootDir" in script

    def test_outputs_ok_on_success(self):
        """Script should output OK with disk and memory info on success."""
        script = preflight_check_script()

        assert "OK:" in script
        assert "disk=" in script
        assert "memory=" in script

    def test_exits_on_docker_error(self):
        """Script should exit 1 when Docker is not available."""
        script = preflight_check_script()

        assert "exit 1" in script

    def test_script_uses_shebang(self):
        """Script should start with bash shebang."""
        script = preflight_check_script()

        assert script.strip().startswith("#!/bin/bash")


class TestHealthCheckScript:
    """Tests for health_check_script function."""

    def test_gets_container_status(self):
        """Script should get container status."""
        script = health_check_script("my-container")

        assert "docker inspect --format" in script
        assert ".State.Status" in script
        assert "STATUS:" in script

    def test_handles_not_found_container(self):
        """Script should handle container not found."""
        script = health_check_script("unknown")

        assert "not_found" in script

    def test_gets_restart_count(self):
        """Script should get restart count."""
        script = health_check_script("test-container")

        assert ".RestartCount" in script
        assert "RESTARTS:" in script

    def test_gets_port_mappings(self):
        """Script should get port mappings."""
        script = health_check_script("webapp")

        assert "docker port webapp" in script
        assert "PORTS:" in script

    def test_gets_recent_logs(self):
        """Script should get recent container logs."""
        script = health_check_script("my-app")

        assert "docker logs --tail 20 my-app" in script
        assert "LOGS_START" in script
        assert "LOGS_END" in script

    def test_limits_log_output(self):
        """Script should limit log output to 2000 characters."""
        script = health_check_script("test")

        assert "head -c 2000" in script

    def test_script_uses_shebang(self):
        """Script should start with bash shebang."""
        script = health_check_script("test")

        assert script.strip().startswith("#!/bin/bash")

    def test_uses_container_name_in_all_commands(self):
        """Script should use container name consistently."""
        container_name = "my-special-container"
        script = health_check_script(container_name)

        # Count occurrences of container name
        assert script.count(container_name) >= 4  # inspect, port, logs, etc.


class TestScriptIntegration:
    """Integration tests verifying script consistency and patterns."""

    def test_all_scripts_return_strings(self):
        """All script functions should return strings."""
        assert isinstance(cleanup_container_script("test"), str)
        assert isinstance(create_container_script("cmd"), str)
        assert isinstance(status_check_script("id"), str)
        assert isinstance(uninstall_script("app"), str)
        assert isinstance(cleanup_failed_deployment_script("app"), str)
        assert isinstance(background_pull_script("img", "job"), str)
        assert isinstance(poll_pull_status_script("job"), str)
        assert isinstance(cleanup_pull_job_script("job"), str)
        assert isinstance(preflight_check_script(), str)
        assert isinstance(health_check_script("container"), str)

    def test_scripts_have_meaningful_output(self):
        """All scripts should produce non-trivial output."""
        scripts = [
            cleanup_container_script("test"),
            create_container_script("docker run test"),
            status_check_script("abc123"),
            uninstall_script("myapp"),
            cleanup_failed_deployment_script("failed"),
            background_pull_script("nginx:latest", "job1"),
            poll_pull_status_script("job1"),
            cleanup_pull_job_script("job1"),
            preflight_check_script(),
            health_check_script("container"),
        ]

        for script in scripts:
            # Each script should have meaningful content
            assert len(script) > 50
            # Each script should contain shell commands
            assert "echo" in script or "docker" in script

    def test_scripts_use_proper_error_handling(self):
        """Scripts should handle errors gracefully."""
        # These scripts should use || true or 2>/dev/null
        cleanup = cleanup_container_script("test")
        assert "|| true" in cleanup

        uninstall = uninstall_script("test")
        assert "2>/dev/null" in uninstall

    def test_background_and_poll_scripts_use_same_paths(self):
        """Background pull and poll scripts should use consistent file paths."""
        job_id = "test-job-123"
        pull_script = background_pull_script("nginx:latest", job_id)
        poll_script = poll_pull_status_script(job_id)
        cleanup_script = cleanup_pull_job_script(job_id)

        # All should reference same work directory
        assert '/tmp/tomo"' in pull_script or "/tmp/tomo'" in pull_script
        assert '/tmp/tomo"' in poll_script or "/tmp/tomo'" in poll_script
        assert '/tmp/tomo"' in cleanup_script

        # All should reference same file names
        assert f"{job_id}.pid" in pull_script
        assert f"{job_id}.pid" in poll_script
        assert f"{job_id}.pid" in cleanup_script
