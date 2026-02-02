"""Agent configuration management."""

import json
import logging
import os
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

try:
    from .lib.encryption import encrypt_token, decrypt_token
except ImportError:
    from lib.encryption import encrypt_token, decrypt_token

logger = logging.getLogger(__name__)


class AgentConfig(BaseModel):
    """Agent runtime configuration."""

    server_url: str = Field(default="")
    register_code: Optional[str] = None
    metrics_interval: int = Field(default=30)
    health_interval: int = Field(default=60)
    reconnect_timeout: int = Field(default=30)


class AgentState(BaseModel):
    """Persisted agent state."""

    agent_id: str
    token: str
    server_url: str
    registered_at: str


DATA_DIR = Path("/data")
STATE_FILE = DATA_DIR / "agent.json"


def load_config() -> AgentConfig:
    """Load configuration from environment."""
    return AgentConfig(
        server_url=os.environ.get("SERVER_URL", ""),
        register_code=os.environ.get("REGISTER_CODE"),
    )


def load_state() -> Optional[AgentState]:
    """Load persisted state from disk.

    The token is stored encrypted at rest and decrypted when loaded.
    """
    if not STATE_FILE.exists():
        return None
    try:
        data = json.loads(STATE_FILE.read_text())

        # Decrypt token if it's encrypted (starts with gAAA for Fernet)
        token = data.get("token", "")
        if token.startswith("gAAA"):
            try:
                data["token"] = decrypt_token(token)
            except Exception as e:
                logger.error(f"Failed to decrypt token: {e}")
                return None

        return AgentState(**data)
    except Exception as e:
        logger.error(f"Failed to load agent state: {e}")
        return None


def save_state(state: AgentState) -> None:
    """Save state to disk with encrypted token.

    The token is encrypted before storage to protect it at rest.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    os.chmod(DATA_DIR, 0o700)

    data = state.model_dump()

    # Encrypt token before storage
    if data.get("token"):
        try:
            data["token"] = encrypt_token(data["token"])
        except Exception as e:
            logger.error(f"Failed to encrypt token: {e}")
            raise

    STATE_FILE.write_text(json.dumps(data, indent=2))
    os.chmod(STATE_FILE, 0o600)  # Restrict file permissions


def update_config(config: AgentConfig, updates: dict) -> AgentConfig:
    """Update config with server-sent values."""
    return config.model_copy(update=updates)
