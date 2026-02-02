"""
Unit tests for models/agent.py - Registration and info models

Tests RegistrationCode, AgentRegistrationRequest, AgentRegistrationResponse,
AgentInfo, AgentHeartbeat, AgentVersionInfo, AgentShutdownRequest models.
"""

from datetime import datetime, UTC
import pytest
from pydantic import ValidationError

from models.agent import (
    AgentStatus,
    AgentConfig,
    RegistrationCode,
    AgentRegistrationRequest,
    AgentRegistrationResponse,
    AgentInfo,
    AgentHeartbeat,
    AgentVersionInfo,
    AgentShutdownRequest,
)


class TestRegistrationCode:
    """Tests for RegistrationCode model."""

    def test_required_fields(self):
        """Test that required fields are validated."""
        expires = datetime.now(UTC)
        code = RegistrationCode(
            id="code-123",
            agent_id="agent-456",
            code="ABC123",
            expires_at=expires,
        )
        assert code.id == "code-123"
        assert code.agent_id == "agent-456"
        assert code.code == "ABC123"
        assert code.expires_at == expires

    def test_default_values(self):
        """Test default values."""
        expires = datetime.now(UTC)
        code = RegistrationCode(
            id="code-123",
            agent_id="agent-456",
            code="ABC123",
            expires_at=expires,
        )
        assert code.used is False
        assert code.created_at is None

    def test_used_flag(self):
        """Test used flag can be set."""
        expires = datetime.now(UTC)
        code = RegistrationCode(
            id="code-123",
            agent_id="agent-456",
            code="ABC123",
            expires_at=expires,
            used=True,
        )
        assert code.used is True

    def test_missing_required_fields(self):
        """Test validation error when required fields are missing."""
        with pytest.raises(ValidationError):
            RegistrationCode(id="code-123")


class TestAgentRegistrationRequest:
    """Tests for AgentRegistrationRequest model."""

    def test_required_code(self):
        """Test that code is required."""
        request = AgentRegistrationRequest(code="ABC123")
        assert request.code == "ABC123"

    def test_missing_code(self):
        """Test validation error when code is missing."""
        with pytest.raises(ValidationError):
            AgentRegistrationRequest()


class TestAgentRegistrationResponse:
    """Tests for AgentRegistrationResponse model."""

    def test_required_fields(self):
        """Test all required fields."""
        config = AgentConfig()
        response = AgentRegistrationResponse(
            agent_id="agent-123",
            server_id="server-456",
            token="token-xyz",
            config=config,
        )
        assert response.agent_id == "agent-123"
        assert response.server_id == "server-456"
        assert response.token == "token-xyz"
        assert response.config == config

    def test_missing_required_fields(self):
        """Test validation error when required fields are missing."""
        with pytest.raises(ValidationError):
            AgentRegistrationResponse(agent_id="agent-123")


class TestAgentInfo:
    """Tests for AgentInfo model."""

    def test_required_fields(self):
        """Test required fields."""
        info = AgentInfo(
            id="agent-123",
            server_id="server-456",
            status=AgentStatus.CONNECTED,
        )
        assert info.id == "agent-123"
        assert info.server_id == "server-456"
        assert info.status == AgentStatus.CONNECTED

    def test_default_values(self):
        """Test default values."""
        info = AgentInfo(
            id="agent-123",
            server_id="server-456",
            status=AgentStatus.PENDING,
        )
        assert info.version is None
        assert info.last_seen is None
        assert info.registered_at is None
        assert info.is_stale is False

    def test_all_fields(self):
        """Test all fields populated."""
        now = datetime.now(UTC)
        info = AgentInfo(
            id="agent-123",
            server_id="server-456",
            status=AgentStatus.CONNECTED,
            version="1.0.0",
            last_seen=now,
            registered_at=now,
            is_stale=True,
        )
        assert info.version == "1.0.0"
        assert info.last_seen == now
        assert info.registered_at == now
        assert info.is_stale is True


class TestAgentHeartbeat:
    """Tests for AgentHeartbeat model."""

    def test_required_fields(self):
        """Test required fields."""
        now = datetime.now(UTC)
        heartbeat = AgentHeartbeat(
            agent_id="agent-123",
            timestamp=now,
        )
        assert heartbeat.agent_id == "agent-123"
        assert heartbeat.timestamp == now

    def test_default_values(self):
        """Test default values for optional metrics."""
        now = datetime.now(UTC)
        heartbeat = AgentHeartbeat(
            agent_id="agent-123",
            timestamp=now,
        )
        assert heartbeat.cpu_percent is None
        assert heartbeat.memory_percent is None
        assert heartbeat.uptime_seconds is None

    def test_all_fields(self):
        """Test all fields populated."""
        now = datetime.now(UTC)
        heartbeat = AgentHeartbeat(
            agent_id="agent-123",
            timestamp=now,
            cpu_percent=45.5,
            memory_percent=62.3,
            uptime_seconds=3600,
        )
        assert heartbeat.cpu_percent == 45.5
        assert heartbeat.memory_percent == 62.3
        assert heartbeat.uptime_seconds == 3600

    def test_missing_required_fields(self):
        """Test validation error when required fields are missing."""
        with pytest.raises(ValidationError):
            AgentHeartbeat(agent_id="agent-123")


class TestAgentVersionInfo:
    """Tests for AgentVersionInfo model."""

    def test_required_fields(self):
        """Test required fields."""
        version_info = AgentVersionInfo(
            current_version="1.0.0",
            latest_version="2.0.0",
            update_available=True,
        )
        assert version_info.current_version == "1.0.0"
        assert version_info.latest_version == "2.0.0"
        assert version_info.update_available is True

    def test_default_values(self):
        """Test default values for optional fields."""
        version_info = AgentVersionInfo(
            current_version="1.0.0",
            latest_version="1.0.0",
            update_available=False,
        )
        assert version_info.release_notes is None
        assert version_info.update_url is None

    def test_all_fields(self):
        """Test all fields populated."""
        version_info = AgentVersionInfo(
            current_version="1.0.0",
            latest_version="2.0.0",
            update_available=True,
            release_notes="Bug fixes and improvements",
            update_url="https://example.com/update",
        )
        assert version_info.release_notes == "Bug fixes and improvements"
        assert version_info.update_url == "https://example.com/update"

    def test_missing_required_fields(self):
        """Test validation error when required fields are missing."""
        with pytest.raises(ValidationError):
            AgentVersionInfo(current_version="1.0.0")


class TestAgentShutdownRequest:
    """Tests for AgentShutdownRequest model."""

    def test_required_fields(self):
        """Test required agent_id field."""
        request = AgentShutdownRequest(agent_id="agent-123")
        assert request.agent_id == "agent-123"

    def test_default_values(self):
        """Test default values."""
        request = AgentShutdownRequest(agent_id="agent-123")
        assert request.reason == "user_request"
        assert request.restart is False

    def test_custom_values(self):
        """Test custom values."""
        request = AgentShutdownRequest(
            agent_id="agent-123",
            reason="update_required",
            restart=True,
        )
        assert request.reason == "update_required"
        assert request.restart is True

    def test_missing_agent_id(self):
        """Test validation error when agent_id is missing."""
        with pytest.raises(ValidationError):
            AgentShutdownRequest()
