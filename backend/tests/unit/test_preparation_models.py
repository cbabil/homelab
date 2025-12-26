"""Tests for preparation models."""
import pytest
from models.preparation import (
    PreparationStatus,
    PreparationStep,
    PreparationLog,
    ServerPreparation
)


class TestPreparationModels:
    """Tests for preparation data models."""

    def test_preparation_status_enum(self):
        """Should have correct status values."""
        assert PreparationStatus.PENDING.value == "pending"
        assert PreparationStatus.IN_PROGRESS.value == "in_progress"
        assert PreparationStatus.COMPLETED.value == "completed"
        assert PreparationStatus.FAILED.value == "failed"

    def test_preparation_step_enum(self):
        """Should have all required steps."""
        steps = [s.value for s in PreparationStep]
        assert "detect_os" in steps
        assert "update_packages" in steps
        assert "install_dependencies" in steps
        assert "install_docker" in steps
        assert "start_docker" in steps
        assert "configure_user" in steps
        assert "verify_docker" in steps

    def test_preparation_log_model(self):
        """Should create valid preparation log."""
        log = PreparationLog(
            id="log-123",
            server_id="server-456",
            step=PreparationStep.DETECT_OS,
            status=PreparationStatus.COMPLETED,
            message="Detected Ubuntu 22.04",
            timestamp="2025-01-01T00:00:00Z"
        )
        assert log.server_id == "server-456"
        assert log.step == PreparationStep.DETECT_OS

    def test_server_preparation_model(self):
        """Should create valid server preparation."""
        prep = ServerPreparation(
            id="prep-123",
            server_id="server-456",
            status=PreparationStatus.IN_PROGRESS,
            current_step=PreparationStep.INSTALL_DOCKER,
            detected_os="ubuntu",
            started_at="2025-01-01T00:00:00Z"
        )
        assert prep.current_step == PreparationStep.INSTALL_DOCKER
        assert prep.detected_os == "ubuntu"
