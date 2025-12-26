"""
Preparation Data Models

Defines models for server preparation workflow and logging.
"""

from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


class PreparationStatus(str, Enum):
    """Preparation workflow status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class PreparationStep(str, Enum):
    """Preparation workflow steps."""
    DETECT_OS = "detect_os"
    UPDATE_PACKAGES = "update_packages"
    INSTALL_DEPENDENCIES = "install_dependencies"
    INSTALL_DOCKER = "install_docker"
    START_DOCKER = "start_docker"
    CONFIGURE_USER = "configure_user"
    VERIFY_DOCKER = "verify_docker"


# Step order for sequential execution
PREPARATION_STEPS = [
    PreparationStep.DETECT_OS,
    PreparationStep.UPDATE_PACKAGES,
    PreparationStep.INSTALL_DEPENDENCIES,
    PreparationStep.INSTALL_DOCKER,
    PreparationStep.START_DOCKER,
    PreparationStep.CONFIGURE_USER,
    PreparationStep.VERIFY_DOCKER,
]


class PreparationLog(BaseModel):
    """Log entry for a preparation step."""
    id: str = Field(..., description="Unique log entry ID")
    server_id: str = Field(..., description="Server being prepared")
    step: PreparationStep = Field(..., description="Preparation step")
    status: PreparationStatus = Field(..., description="Step status")
    message: str = Field(..., description="Log message")
    output: Optional[str] = Field(None, description="Command output")
    error: Optional[str] = Field(None, description="Error message if failed")
    timestamp: str = Field(..., description="Log timestamp")


class ServerPreparation(BaseModel):
    """Server preparation state."""
    id: str = Field(..., description="Preparation ID")
    server_id: str = Field(..., description="Server being prepared")
    status: PreparationStatus = Field(default=PreparationStatus.PENDING)
    current_step: Optional[PreparationStep] = Field(None, description="Current step")
    detected_os: Optional[str] = Field(None, description="Detected OS type")
    started_at: Optional[str] = Field(None, description="Start timestamp")
    completed_at: Optional[str] = Field(None, description="Completion timestamp")
    error_message: Optional[str] = Field(None, description="Error if failed")
    logs: List[PreparationLog] = Field(default_factory=list)
