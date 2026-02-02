"""Tests for agent configuration module.

Tests configuration loading, state persistence, and config updates.
"""

import json
import os
from unittest.mock import patch

import pytest

from config import (
    AgentConfig,
    AgentState,
    load_config,
    load_state,
    save_state,
    update_config,
)


class TestAgentConfig:
    """Tests for AgentConfig model."""

    def test_default_values(self):
        """Should have correct default values."""
        config = AgentConfig()
        assert config.server_url == ""
        assert config.register_code is None
        assert config.metrics_interval == 30
        assert config.health_interval == 60
        assert config.reconnect_timeout == 30

    def test_custom_values(self):
        """Should accept custom values."""
        config = AgentConfig(
            server_url="wss://example.com/agent",
            register_code="ABC123",
            metrics_interval=60,
            health_interval=120,
        )
        assert config.server_url == "wss://example.com/agent"
        assert config.register_code == "ABC123"
        assert config.metrics_interval == 60
        assert config.health_interval == 120


class TestAgentState:
    """Tests for AgentState model."""

    def test_required_fields(self):
        """Should require all fields."""
        state = AgentState(
            agent_id="agent-123",
            token="secret-token",
            server_url="wss://example.com",
            registered_at="2024-01-01T00:00:00Z",
        )
        assert state.agent_id == "agent-123"
        assert state.token == "secret-token"
        assert state.server_url == "wss://example.com"
        assert state.registered_at == "2024-01-01T00:00:00Z"

    def test_missing_field_raises(self):
        """Should raise on missing required fields."""
        with pytest.raises(Exception):
            AgentState(agent_id="agent-123")


class TestLoadConfig:
    """Tests for load_config function."""

    def test_loads_from_environment(self):
        """Should load configuration from environment variables."""
        with patch.dict(
            os.environ,
            {
                "SERVER_URL": "wss://test.example.com",
                "REGISTER_CODE": "TEST-CODE",
            },
        ):
            config = load_config()
            assert config.server_url == "wss://test.example.com"
            assert config.register_code == "TEST-CODE"

    def test_defaults_when_no_env(self):
        """Should use defaults when env vars not set."""
        with patch.dict(os.environ, {}, clear=True):
            config = load_config()
            assert config.server_url == ""
            assert config.register_code is None


class TestLoadState:
    """Tests for load_state function."""

    def test_returns_none_when_file_missing(self, tmp_path):
        """Should return None when state file doesn't exist."""
        with patch("config.STATE_FILE", tmp_path / "nonexistent.json"):
            result = load_state()
            assert result is None

    def test_loads_state_from_file(self, tmp_path):
        """Should load state from file."""
        state_file = tmp_path / "agent.json"
        state_data = {
            "agent_id": "agent-456",
            "token": "plain-token",
            "server_url": "wss://server.example.com",
            "registered_at": "2024-06-01T12:00:00Z",
        }
        state_file.write_text(json.dumps(state_data))

        with patch("config.STATE_FILE", state_file):
            result = load_state()
            assert result is not None
            assert result.agent_id == "agent-456"
            assert result.token == "plain-token"
            assert result.server_url == "wss://server.example.com"

    def test_decrypts_encrypted_token(self, tmp_path):
        """Should decrypt token that starts with gAAA."""
        state_file = tmp_path / "agent.json"
        state_data = {
            "agent_id": "agent-789",
            "token": "gAAA_encrypted_token",
            "server_url": "wss://encrypted.example.com",
            "registered_at": "2024-06-01T12:00:00Z",
        }
        state_file.write_text(json.dumps(state_data))

        with patch("config.STATE_FILE", state_file):
            with patch(
                "config.decrypt_token", return_value="decrypted-token"
            ) as mock_decrypt:
                result = load_state()
                assert result is not None
                assert result.token == "decrypted-token"
                mock_decrypt.assert_called_once_with("gAAA_encrypted_token")

    def test_returns_none_on_decrypt_failure(self, tmp_path):
        """Should return None when token decryption fails."""
        state_file = tmp_path / "agent.json"
        state_data = {
            "agent_id": "agent-bad",
            "token": "gAAA_invalid_encrypted",
            "server_url": "wss://fail.example.com",
            "registered_at": "2024-06-01T12:00:00Z",
        }
        state_file.write_text(json.dumps(state_data))

        with patch("config.STATE_FILE", state_file):
            with patch("config.decrypt_token", side_effect=Exception("Decrypt failed")):
                result = load_state()
                assert result is None

    def test_returns_none_on_invalid_json(self, tmp_path):
        """Should return None when file contains invalid JSON."""
        state_file = tmp_path / "agent.json"
        state_file.write_text("not valid json")

        with patch("config.STATE_FILE", state_file):
            result = load_state()
            assert result is None


class TestSaveState:
    """Tests for save_state function."""

    def test_saves_state_to_file(self, tmp_path):
        """Should save state to file with encrypted token."""
        data_dir = tmp_path / "data"
        state_file = data_dir / "agent.json"

        state = AgentState(
            agent_id="save-agent",
            token="my-secret-token",
            server_url="wss://save.example.com",
            registered_at="2024-07-01T00:00:00Z",
        )

        with patch("config.DATA_DIR", data_dir):
            with patch("config.STATE_FILE", state_file):
                with patch(
                    "config.encrypt_token", return_value="encrypted_xyz"
                ) as mock_encrypt:
                    save_state(state)

                    # Verify file was created
                    assert state_file.exists()

                    # Verify content
                    saved_data = json.loads(state_file.read_text())
                    assert saved_data["agent_id"] == "save-agent"
                    assert saved_data["token"] == "encrypted_xyz"
                    assert saved_data["server_url"] == "wss://save.example.com"

                    mock_encrypt.assert_called_once_with("my-secret-token")

    def test_creates_data_directory(self, tmp_path):
        """Should create data directory if it doesn't exist."""
        data_dir = tmp_path / "new_data_dir"
        state_file = data_dir / "agent.json"

        state = AgentState(
            agent_id="new-agent",
            token="token",
            server_url="wss://new.example.com",
            registered_at="2024-07-01T00:00:00Z",
        )

        with patch("config.DATA_DIR", data_dir):
            with patch("config.STATE_FILE", state_file):
                with patch("config.encrypt_token", return_value="enc"):
                    save_state(state)
                    assert data_dir.exists()

    def test_raises_on_encryption_failure(self, tmp_path):
        """Should raise when encryption fails."""
        data_dir = tmp_path / "fail_data"
        state_file = data_dir / "agent.json"

        state = AgentState(
            agent_id="fail-agent",
            token="token",
            server_url="wss://fail.example.com",
            registered_at="2024-07-01T00:00:00Z",
        )

        with patch("config.DATA_DIR", data_dir):
            with patch("config.STATE_FILE", state_file):
                with patch(
                    "config.encrypt_token", side_effect=Exception("Encrypt failed")
                ):
                    with pytest.raises(Exception, match="Encrypt failed"):
                        save_state(state)


class TestUpdateConfig:
    """Tests for update_config function."""

    def test_updates_config_with_new_values(self):
        """Should update config with provided values."""
        original = AgentConfig(
            server_url="wss://original.com",
            metrics_interval=30,
        )

        updated = update_config(original, {"metrics_interval": 60})

        assert updated.metrics_interval == 60
        assert updated.server_url == "wss://original.com"  # Unchanged

    def test_returns_new_config_instance(self):
        """Should return a new config, not mutate original."""
        original = AgentConfig(metrics_interval=30)

        updated = update_config(original, {"metrics_interval": 90})

        assert original.metrics_interval == 30  # Original unchanged
        assert updated.metrics_interval == 90  # New has updated value

    def test_handles_multiple_updates(self):
        """Should handle multiple field updates."""
        original = AgentConfig()

        updated = update_config(
            original,
            {
                "server_url": "wss://new.com",
                "metrics_interval": 45,
                "health_interval": 90,
            },
        )

        assert updated.server_url == "wss://new.com"
        assert updated.metrics_interval == 45
        assert updated.health_interval == 90
