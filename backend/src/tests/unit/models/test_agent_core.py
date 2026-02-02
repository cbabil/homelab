"""
Unit tests for models/agent.py - Core models

Tests AgentStatus, AgentConfig, Agent, AgentCreate, AgentUpdate models.
"""

from datetime import datetime, UTC
import pytest
from pydantic import ValidationError

from models.agent import (
    AgentStatus,
    AgentConfig,
    Agent,
    AgentCreate,
    AgentUpdate,
)


class TestAgentStatus:
    """Tests for AgentStatus enum."""

    def test_status_values(self):
        """Test all status enum values exist."""
        assert AgentStatus.PENDING == "pending"
        assert AgentStatus.CONNECTED == "connected"
        assert AgentStatus.DISCONNECTED == "disconnected"
        assert AgentStatus.UPDATING == "updating"

    def test_status_is_string_enum(self):
        """Test that status values are strings."""
        assert isinstance(AgentStatus.PENDING.value, str)
        assert AgentStatus.PENDING.value == "pending"


class TestAgentConfig:
    """Tests for AgentConfig model."""

    def test_default_values(self):
        """Test default configuration values."""
        config = AgentConfig()
        assert config.metrics_interval == 30
        assert config.health_interval == 60
        assert config.reconnect_timeout == 30
        assert config.heartbeat_interval == 30
        assert config.heartbeat_timeout == 90
        assert config.auto_update is True

    def test_custom_values(self):
        """Test custom configuration values."""
        config = AgentConfig(
            metrics_interval=60,
            health_interval=120,
            reconnect_timeout=60,
            heartbeat_interval=45,
            heartbeat_timeout=120,
            auto_update=False,
        )
        assert config.metrics_interval == 60
        assert config.health_interval == 120
        assert config.reconnect_timeout == 60
        assert config.heartbeat_interval == 45
        assert config.heartbeat_timeout == 120
        assert config.auto_update is False

    def test_metrics_interval_min_validation(self):
        """Test metrics_interval minimum value validation."""
        with pytest.raises(ValidationError) as exc_info:
            AgentConfig(metrics_interval=4)
        assert "metrics_interval" in str(exc_info.value)

    def test_metrics_interval_max_validation(self):
        """Test metrics_interval maximum value validation."""
        with pytest.raises(ValidationError) as exc_info:
            AgentConfig(metrics_interval=301)
        assert "metrics_interval" in str(exc_info.value)

    def test_health_interval_min_validation(self):
        """Test health_interval minimum value validation."""
        with pytest.raises(ValidationError) as exc_info:
            AgentConfig(health_interval=9)
        assert "health_interval" in str(exc_info.value)

    def test_health_interval_max_validation(self):
        """Test health_interval maximum value validation."""
        with pytest.raises(ValidationError) as exc_info:
            AgentConfig(health_interval=601)
        assert "health_interval" in str(exc_info.value)

    def test_reconnect_timeout_min_validation(self):
        """Test reconnect_timeout minimum value validation."""
        with pytest.raises(ValidationError) as exc_info:
            AgentConfig(reconnect_timeout=4)
        assert "reconnect_timeout" in str(exc_info.value)

    def test_reconnect_timeout_max_validation(self):
        """Test reconnect_timeout maximum value validation."""
        with pytest.raises(ValidationError) as exc_info:
            AgentConfig(reconnect_timeout=121)
        assert "reconnect_timeout" in str(exc_info.value)

    def test_heartbeat_interval_min_validation(self):
        """Test heartbeat_interval minimum value validation."""
        with pytest.raises(ValidationError) as exc_info:
            AgentConfig(heartbeat_interval=9)
        assert "heartbeat_interval" in str(exc_info.value)

    def test_heartbeat_interval_max_validation(self):
        """Test heartbeat_interval maximum value validation."""
        with pytest.raises(ValidationError) as exc_info:
            AgentConfig(heartbeat_interval=121)
        assert "heartbeat_interval" in str(exc_info.value)

    def test_heartbeat_timeout_min_validation(self):
        """Test heartbeat_timeout minimum value validation."""
        with pytest.raises(ValidationError) as exc_info:
            AgentConfig(heartbeat_timeout=29)
        assert "heartbeat_timeout" in str(exc_info.value)

    def test_heartbeat_timeout_max_validation(self):
        """Test heartbeat_timeout maximum value validation."""
        with pytest.raises(ValidationError) as exc_info:
            AgentConfig(heartbeat_timeout=301)
        assert "heartbeat_timeout" in str(exc_info.value)

    def test_boundary_values_accepted(self):
        """Test that boundary values are accepted."""
        config = AgentConfig(
            metrics_interval=5,
            health_interval=10,
            reconnect_timeout=5,
            heartbeat_interval=10,
            heartbeat_timeout=30,
        )
        assert config.metrics_interval == 5
        assert config.health_interval == 10

        config_max = AgentConfig(
            metrics_interval=300,
            health_interval=600,
            reconnect_timeout=120,
            heartbeat_interval=120,
            heartbeat_timeout=300,
        )
        assert config_max.metrics_interval == 300
        assert config_max.health_interval == 600


class TestAgent:
    """Tests for Agent model."""

    def test_required_fields(self):
        """Test that id and server_id are required."""
        agent = Agent(id="agent-123", server_id="server-456")
        assert agent.id == "agent-123"
        assert agent.server_id == "server-456"

    def test_missing_required_fields(self):
        """Test validation error when required fields are missing."""
        with pytest.raises(ValidationError):
            Agent()

    def test_default_values(self):
        """Test default values for optional fields."""
        agent = Agent(id="agent-123", server_id="server-456")
        assert agent.token_hash is None
        assert agent.version is None
        assert agent.status == AgentStatus.PENDING
        assert agent.last_seen is None
        assert agent.registered_at is None
        assert agent.config is None
        assert agent.created_at is None
        assert agent.updated_at is None

    def test_all_fields(self):
        """Test agent with all fields populated."""
        now = datetime.now(UTC)
        config = AgentConfig()
        agent = Agent(
            id="agent-123",
            server_id="server-456",
            token_hash="hash123",
            version="1.0.0",
            status=AgentStatus.CONNECTED,
            last_seen=now,
            registered_at=now,
            config=config,
            created_at=now,
            updated_at=now,
        )
        assert agent.token_hash == "hash123"
        assert agent.version == "1.0.0"
        assert agent.status == AgentStatus.CONNECTED
        assert agent.last_seen == now
        assert agent.registered_at == now
        assert agent.config == config
        assert agent.created_at == now
        assert agent.updated_at == now


class TestAgentCreate:
    """Tests for AgentCreate model."""

    def test_required_server_id(self):
        """Test that server_id is required."""
        create = AgentCreate(server_id="server-123")
        assert create.server_id == "server-123"

    def test_missing_server_id(self):
        """Test validation error when server_id is missing."""
        with pytest.raises(ValidationError):
            AgentCreate()


class TestAgentUpdate:
    """Tests for AgentUpdate model."""

    def test_all_fields_optional(self):
        """Test that all fields are optional."""
        update = AgentUpdate()
        assert update.server_id is None
        assert update.token_hash is None
        assert update.version is None
        assert update.status is None
        assert update.last_seen is None
        assert update.registered_at is None
        assert update.config is None

    def test_partial_update(self):
        """Test partial update with some fields."""
        update = AgentUpdate(
            status=AgentStatus.CONNECTED,
            version="2.0.0",
        )
        assert update.status == AgentStatus.CONNECTED
        assert update.version == "2.0.0"
        assert update.server_id is None

    def test_full_update(self):
        """Test update with all fields."""
        now = datetime.now(UTC)
        config = AgentConfig(metrics_interval=60)
        update = AgentUpdate(
            server_id="new-server",
            token_hash="new-hash",
            version="3.0.0",
            status=AgentStatus.UPDATING,
            last_seen=now,
            registered_at=now,
            config=config,
        )
        assert update.server_id == "new-server"
        assert update.token_hash == "new-hash"
        assert update.version == "3.0.0"
        assert update.status == AgentStatus.UPDATING
        assert update.last_seen == now
        assert update.registered_at == now
        assert update.config.metrics_interval == 60
