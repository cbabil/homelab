# Tomo Agent Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Python-based Docker agent that replaces SSH for server management via persistent WebSocket connection.

**Architecture:** Agent container connects to tomo backend via WebSocket, authenticates with one-time registration code, then handles all Docker/system operations locally via JSON-RPC 2.0 protocol.

**Tech Stack:** Python 3.12, websockets, docker-py, psutil, pydantic, FastMCP WebSocket extension

---

## Phase 1: Backend Infrastructure (Database & Models)

### Task 1.1: Create Agent Database Schema

**Files:**
- Create: `backend/src/init_db/schema_agents.py`

**Step 1: Create schema file**

```python
"""Agent database schema initialization."""

import logging
from .schema_base import SchemaBase

logger = logging.getLogger(__name__)


class AgentSchema(SchemaBase):
    """Schema manager for agent-related tables."""

    def initialize(self) -> None:
        """Initialize agent tables."""
        self._create_agents_table()
        self._create_agent_registration_codes_table()

    def _create_agents_table(self) -> None:
        """Create agents table."""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS agents (
                id TEXT PRIMARY KEY,
                server_id TEXT NOT NULL UNIQUE,
                token_hash TEXT,
                version TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                last_seen TIMESTAMP,
                registered_at TIMESTAMP,
                config TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE
            )
        """)
        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_agents_server_id ON agents(server_id)
        """)
        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status)
        """)
        self.connection.commit()
        logger.info("Agents table initialized")

    def _create_agent_registration_codes_table(self) -> None:
        """Create agent registration codes table."""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_registration_codes (
                id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                code TEXT NOT NULL UNIQUE,
                expires_at TIMESTAMP NOT NULL,
                used INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
            )
        """)
        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_agent_reg_codes_code ON agent_registration_codes(code)
        """)
        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_agent_reg_codes_agent_id ON agent_registration_codes(agent_id)
        """)
        self.connection.commit()
        logger.info("Agent registration codes table initialized")
```

**Step 2: Verify file created**

Run: `ls -la backend/src/init_db/schema_agents.py`
Expected: File exists

---

### Task 1.2: Create Agent Models

**Files:**
- Create: `backend/src/models/agent.py`

**Step 1: Create models file**

```python
"""Agent-related Pydantic models."""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    """Agent connection status."""
    PENDING = "pending"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    UPDATING = "updating"


class AgentConfig(BaseModel):
    """Agent configuration sent from server."""
    metrics_interval: int = Field(default=30, ge=5, le=300)
    health_interval: int = Field(default=60, ge=10, le=600)
    reconnect_timeout: int = Field(default=30, ge=5, le=120)


class Agent(BaseModel):
    """Agent database model."""
    id: str
    server_id: str
    token_hash: Optional[str] = None
    version: Optional[str] = None
    status: AgentStatus = AgentStatus.PENDING
    last_seen: Optional[datetime] = None
    registered_at: Optional[datetime] = None
    config: Optional[AgentConfig] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class AgentCreate(BaseModel):
    """Model for creating a new agent."""
    server_id: str


class AgentUpdate(BaseModel):
    """Model for updating an agent."""
    token_hash: Optional[str] = None
    version: Optional[str] = None
    status: Optional[AgentStatus] = None
    last_seen: Optional[datetime] = None
    registered_at: Optional[datetime] = None
    config: Optional[AgentConfig] = None


class RegistrationCode(BaseModel):
    """Agent registration code model."""
    id: str
    agent_id: str
    code: str
    expires_at: datetime
    used: bool = False
    created_at: Optional[datetime] = None


class AgentRegistrationRequest(BaseModel):
    """Request to register an agent with a code."""
    code: str


class AgentRegistrationResponse(BaseModel):
    """Response after successful agent registration."""
    agent_id: str
    token: str
    config: AgentConfig


class AgentInfo(BaseModel):
    """Agent info returned to frontend."""
    id: str
    server_id: str
    status: AgentStatus
    version: Optional[str] = None
    last_seen: Optional[datetime] = None
    registered_at: Optional[datetime] = None
```

**Step 2: Update models __init__.py**

Add to `backend/src/models/__init__.py`:
```python
from .agent import (
    Agent,
    AgentStatus,
    AgentConfig,
    AgentCreate,
    AgentUpdate,
    RegistrationCode,
    AgentRegistrationRequest,
    AgentRegistrationResponse,
    AgentInfo,
)
```

---

### Task 1.3: Create Agent Database Service

**Files:**
- Create: `backend/src/services/database/agent_database_service.py`

**Step 1: Create database service**

```python
"""Agent database operations."""

import json
import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

from ...models.agent import (
    Agent,
    AgentConfig,
    AgentCreate,
    AgentStatus,
    AgentUpdate,
    RegistrationCode,
)

logger = logging.getLogger(__name__)


class AgentDatabaseService:
    """Database operations for agents."""

    def __init__(self, connection, cursor):
        """Initialize with database connection."""
        self.connection = connection
        self.cursor = cursor

    def create_agent(self, data: AgentCreate) -> Agent:
        """Create a new agent record."""
        agent_id = str(uuid4())
        now = datetime.utcnow()

        self.cursor.execute(
            """
            INSERT INTO agents (id, server_id, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (agent_id, data.server_id, AgentStatus.PENDING.value, now, now),
        )
        self.connection.commit()

        return self.get_agent(agent_id)

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get agent by ID."""
        self.cursor.execute("SELECT * FROM agents WHERE id = ?", (agent_id,))
        row = self.cursor.fetchone()
        return self._row_to_agent(row) if row else None

    def get_agent_by_server(self, server_id: str) -> Optional[Agent]:
        """Get agent by server ID."""
        self.cursor.execute("SELECT * FROM agents WHERE server_id = ?", (server_id,))
        row = self.cursor.fetchone()
        return self._row_to_agent(row) if row else None

    def get_agent_by_token_hash(self, token_hash: str) -> Optional[Agent]:
        """Get agent by token hash."""
        self.cursor.execute("SELECT * FROM agents WHERE token_hash = ?", (token_hash,))
        row = self.cursor.fetchone()
        return self._row_to_agent(row) if row else None

    def update_agent(self, agent_id: str, data: AgentUpdate) -> Optional[Agent]:
        """Update agent record."""
        updates = []
        values = []

        if data.token_hash is not None:
            updates.append("token_hash = ?")
            values.append(data.token_hash)
        if data.version is not None:
            updates.append("version = ?")
            values.append(data.version)
        if data.status is not None:
            updates.append("status = ?")
            values.append(data.status.value)
        if data.last_seen is not None:
            updates.append("last_seen = ?")
            values.append(data.last_seen)
        if data.registered_at is not None:
            updates.append("registered_at = ?")
            values.append(data.registered_at)
        if data.config is not None:
            updates.append("config = ?")
            values.append(json.dumps(data.config.model_dump()))

        if not updates:
            return self.get_agent(agent_id)

        updates.append("updated_at = ?")
        values.append(datetime.utcnow())
        values.append(agent_id)

        self.cursor.execute(
            f"UPDATE agents SET {', '.join(updates)} WHERE id = ?",
            values,
        )
        self.connection.commit()

        return self.get_agent(agent_id)

    def delete_agent(self, agent_id: str) -> bool:
        """Delete agent record."""
        self.cursor.execute("DELETE FROM agents WHERE id = ?", (agent_id,))
        self.connection.commit()
        return self.cursor.rowcount > 0

    def create_registration_code(
        self, agent_id: str, expiry_minutes: int = 5
    ) -> RegistrationCode:
        """Create a registration code for an agent."""
        import secrets

        code_id = str(uuid4())
        code = secrets.token_hex(3).upper()  # 6 chars
        expires_at = datetime.utcnow() + timedelta(minutes=expiry_minutes)

        self.cursor.execute(
            """
            INSERT INTO agent_registration_codes (id, agent_id, code, expires_at)
            VALUES (?, ?, ?, ?)
            """,
            (code_id, agent_id, code, expires_at),
        )
        self.connection.commit()

        return RegistrationCode(
            id=code_id,
            agent_id=agent_id,
            code=code,
            expires_at=expires_at,
            used=False,
        )

    def get_registration_code(self, code: str) -> Optional[RegistrationCode]:
        """Get registration code by code value."""
        self.cursor.execute(
            "SELECT * FROM agent_registration_codes WHERE code = ?", (code,)
        )
        row = self.cursor.fetchone()
        if not row:
            return None

        return RegistrationCode(
            id=row["id"],
            agent_id=row["agent_id"],
            code=row["code"],
            expires_at=datetime.fromisoformat(row["expires_at"]),
            used=bool(row["used"]),
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
        )

    def mark_code_used(self, code_id: str) -> None:
        """Mark a registration code as used."""
        self.cursor.execute(
            "UPDATE agent_registration_codes SET used = 1 WHERE id = ?", (code_id,)
        )
        self.connection.commit()

    def cleanup_expired_codes(self) -> int:
        """Delete expired registration codes."""
        self.cursor.execute(
            "DELETE FROM agent_registration_codes WHERE expires_at < ?",
            (datetime.utcnow(),),
        )
        self.connection.commit()
        return self.cursor.rowcount

    def _row_to_agent(self, row) -> Agent:
        """Convert database row to Agent model."""
        config = None
        if row["config"]:
            config = AgentConfig(**json.loads(row["config"]))

        return Agent(
            id=row["id"],
            server_id=row["server_id"],
            token_hash=row["token_hash"],
            version=row["version"],
            status=AgentStatus(row["status"]),
            last_seen=datetime.fromisoformat(row["last_seen"]) if row["last_seen"] else None,
            registered_at=datetime.fromisoformat(row["registered_at"]) if row["registered_at"] else None,
            config=config,
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
            updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None,
        )
```

---

### Task 1.4: Update Schema Initializer

**Files:**
- Modify: `backend/src/services/database/schema_initializer.py`

**Step 1: Add agent schema import and initialization**

Add import at top:
```python
from ...init_db.schema_agents import AgentSchema
```

Add method call in `initialize_all()` method:
```python
AgentSchema(self.connection, self.cursor).initialize()
```

---

### Task 1.5: Add Agent Settings to Seed

**Files:**
- Modify: `backend/sql/seed_default_settings.sql`

**Step 1: Add agent settings**

Add to settings INSERT:
```sql
-- Agent settings
INSERT OR IGNORE INTO settings (key, value, category, description) VALUES
    ('agent_metrics_interval', '30', 'agent', 'Seconds between agent metrics push'),
    ('agent_health_interval', '60', 'agent', 'Seconds between agent health reports'),
    ('agent_reconnect_timeout', '30', 'agent', 'Seconds before agent reconnect attempt');
```

---

## Phase 2: Backend WebSocket Server

### Task 2.1: Create AgentManager Service

**Files:**
- Create: `backend/src/services/agent_manager.py`

**Step 1: Create agent manager**

```python
"""Agent connection manager for WebSocket handling."""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Callable, Optional
from uuid import uuid4

from ..models.agent import AgentConfig, AgentStatus, AgentUpdate

logger = logging.getLogger(__name__)


class AgentConnection:
    """Represents a connected agent."""

    def __init__(self, agent_id: str, websocket, server_id: str):
        self.agent_id = agent_id
        self.websocket = websocket
        self.server_id = server_id
        self.pending_requests: dict[str, asyncio.Future] = {}
        self.connected_at = datetime.utcnow()


class AgentManager:
    """Manages WebSocket connections to agents."""

    def __init__(self, db_service):
        self.db_service = db_service
        self.connections: dict[str, AgentConnection] = {}
        self._notification_handlers: dict[str, Callable] = {}

    def register_notification_handler(
        self, method: str, handler: Callable[[str, dict], None]
    ) -> None:
        """Register a handler for agent notifications."""
        self._notification_handlers[method] = handler

    async def register_connection(
        self, agent_id: str, websocket, server_id: str
    ) -> None:
        """Register a new agent connection."""
        # Close existing connection if any
        if agent_id in self.connections:
            await self.unregister_connection(agent_id)

        self.connections[agent_id] = AgentConnection(agent_id, websocket, server_id)

        # Update agent status in database
        self.db_service.agents.update_agent(
            agent_id,
            AgentUpdate(status=AgentStatus.CONNECTED, last_seen=datetime.utcnow()),
        )

        logger.info(f"Agent {agent_id} connected (server: {server_id})")

    async def unregister_connection(self, agent_id: str) -> None:
        """Unregister an agent connection."""
        if agent_id not in self.connections:
            return

        conn = self.connections.pop(agent_id)

        # Cancel pending requests
        for future in conn.pending_requests.values():
            if not future.done():
                future.cancel()

        # Update agent status
        self.db_service.agents.update_agent(
            agent_id,
            AgentUpdate(status=AgentStatus.DISCONNECTED, last_seen=datetime.utcnow()),
        )

        logger.info(f"Agent {agent_id} disconnected")

    def is_connected(self, agent_id: str) -> bool:
        """Check if an agent is connected."""
        return agent_id in self.connections

    def get_connection_by_server(self, server_id: str) -> Optional[AgentConnection]:
        """Get agent connection by server ID."""
        for conn in self.connections.values():
            if conn.server_id == server_id:
                return conn
        return None

    async def send_command(
        self,
        agent_id: str,
        method: str,
        params: Optional[dict] = None,
        timeout: float = 30.0,
    ) -> Any:
        """Send a command to an agent and wait for response."""
        if agent_id not in self.connections:
            raise ConnectionError(f"Agent {agent_id} not connected")

        conn = self.connections[agent_id]
        request_id = str(uuid4())

        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": request_id,
        }

        # Create future for response
        future: asyncio.Future = asyncio.get_event_loop().create_future()
        conn.pending_requests[request_id] = future

        try:
            await conn.websocket.send_text(json.dumps(request))
            result = await asyncio.wait_for(future, timeout=timeout)
            return result
        except asyncio.TimeoutError:
            raise TimeoutError(f"Agent {agent_id} did not respond in {timeout}s")
        finally:
            conn.pending_requests.pop(request_id, None)

    async def handle_message(self, agent_id: str, message: str) -> None:
        """Handle incoming message from agent."""
        if agent_id not in self.connections:
            return

        conn = self.connections[agent_id]

        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON from agent {agent_id}: {message[:100]}")
            return

        # Update last seen
        self.db_service.agents.update_agent(
            agent_id, AgentUpdate(last_seen=datetime.utcnow())
        )

        # Check if this is a response to a pending request
        if "id" in data and data["id"] in conn.pending_requests:
            future = conn.pending_requests[data["id"]]
            if not future.done():
                if "error" in data:
                    future.set_exception(
                        RuntimeError(data["error"].get("message", "Unknown error"))
                    )
                else:
                    future.set_result(data.get("result"))
            return

        # Handle notification (no id = no response expected)
        if "method" in data and "id" not in data:
            method = data["method"]
            params = data.get("params", {})

            if method in self._notification_handlers:
                try:
                    await self._notification_handlers[method](agent_id, params)
                except Exception as e:
                    logger.error(f"Error handling notification {method}: {e}")
            else:
                logger.warning(f"No handler for notification: {method}")

    async def broadcast_config_update(self, config: AgentConfig) -> None:
        """Broadcast config update to all connected agents."""
        for agent_id in list(self.connections.keys()):
            try:
                await self.send_command(
                    agent_id, "config.update", config.model_dump(), timeout=5.0
                )
            except Exception as e:
                logger.error(f"Failed to update config for agent {agent_id}: {e}")
```

---

### Task 2.2: Create AgentService

**Files:**
- Create: `backend/src/services/agent_service.py`

**Step 1: Create agent service**

```python
"""Agent lifecycle and authentication service."""

import hashlib
import logging
import secrets
from datetime import datetime
from typing import Optional, Tuple

from ..models.agent import (
    Agent,
    AgentConfig,
    AgentCreate,
    AgentRegistrationResponse,
    AgentStatus,
    AgentUpdate,
    RegistrationCode,
)

logger = logging.getLogger(__name__)


class AgentService:
    """Service for agent lifecycle management."""

    def __init__(self, db_service, settings_service):
        self.db_service = db_service
        self.settings_service = settings_service

    def create_agent(self, server_id: str) -> Tuple[Agent, RegistrationCode]:
        """Create a new agent and registration code for a server."""
        # Check if agent already exists for this server
        existing = self.db_service.agents.get_agent_by_server(server_id)
        if existing:
            # Delete existing agent to start fresh
            self.db_service.agents.delete_agent(existing.id)
            logger.info(f"Deleted existing agent {existing.id} for server {server_id}")

        # Create new agent
        agent = self.db_service.agents.create_agent(AgentCreate(server_id=server_id))

        # Create registration code
        code = self.db_service.agents.create_registration_code(agent.id)

        logger.info(f"Created agent {agent.id} with registration code for server {server_id}")
        return agent, code

    def validate_registration_code(self, code: str) -> Optional[RegistrationCode]:
        """Validate a registration code."""
        reg_code = self.db_service.agents.get_registration_code(code)

        if not reg_code:
            logger.warning(f"Registration code not found: {code}")
            return None

        if reg_code.used:
            logger.warning(f"Registration code already used: {code}")
            return None

        if reg_code.expires_at < datetime.utcnow():
            logger.warning(f"Registration code expired: {code}")
            return None

        return reg_code

    def complete_registration(
        self, code: str, agent_version: str
    ) -> Optional[AgentRegistrationResponse]:
        """Complete agent registration and return token."""
        reg_code = self.validate_registration_code(code)
        if not reg_code:
            return None

        # Generate token
        token = secrets.token_urlsafe(32)
        token_hash = self._hash_token(token)

        # Update agent
        now = datetime.utcnow()
        self.db_service.agents.update_agent(
            reg_code.agent_id,
            AgentUpdate(
                token_hash=token_hash,
                version=agent_version,
                status=AgentStatus.CONNECTED,
                registered_at=now,
                last_seen=now,
            ),
        )

        # Mark code as used
        self.db_service.agents.mark_code_used(reg_code.id)

        # Get config from settings
        config = self._get_agent_config()

        logger.info(f"Agent {reg_code.agent_id} registration completed")
        return AgentRegistrationResponse(
            agent_id=reg_code.agent_id,
            token=token,
            config=config,
        )

    def validate_token(self, token: str) -> Optional[Agent]:
        """Validate an agent token and return agent if valid."""
        token_hash = self._hash_token(token)
        agent = self.db_service.agents.get_agent_by_token_hash(token_hash)

        if not agent:
            return None

        if agent.status == AgentStatus.PENDING:
            logger.warning(f"Agent {agent.id} not yet registered")
            return None

        return agent

    def revoke_agent(self, agent_id: str) -> bool:
        """Revoke an agent's access."""
        agent = self.db_service.agents.get_agent(agent_id)
        if not agent:
            return False

        # Clear token and set status
        self.db_service.agents.update_agent(
            agent_id,
            AgentUpdate(token_hash=None, status=AgentStatus.DISCONNECTED),
        )

        logger.info(f"Agent {agent_id} revoked")
        return True

    def get_agent_by_server(self, server_id: str) -> Optional[Agent]:
        """Get agent for a server."""
        return self.db_service.agents.get_agent_by_server(server_id)

    def _get_agent_config(self) -> AgentConfig:
        """Get agent configuration from settings."""
        settings = self.settings_service.get_all_settings()
        return AgentConfig(
            metrics_interval=int(settings.get("agent_metrics_interval", 30)),
            health_interval=int(settings.get("agent_health_interval", 60)),
            reconnect_timeout=int(settings.get("agent_reconnect_timeout", 30)),
        )

    def _hash_token(self, token: str) -> str:
        """Hash a token for storage."""
        return hashlib.sha256(token.encode()).hexdigest()
```

---

### Task 2.3: Create WebSocket Endpoint

**Files:**
- Create: `backend/src/services/agent_websocket.py`

**Step 1: Create WebSocket handler**

```python
"""WebSocket endpoint for agent connections."""

import logging
from starlette.websockets import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class AgentWebSocketHandler:
    """Handles WebSocket connections from agents."""

    def __init__(self, agent_service, agent_manager):
        self.agent_service = agent_service
        self.agent_manager = agent_manager

    async def handle_connection(self, websocket: WebSocket) -> None:
        """Handle a new WebSocket connection."""
        await websocket.accept()

        agent_id = None

        try:
            # First message should be authentication
            auth_message = await websocket.receive_json()

            if auth_message.get("type") == "register":
                # Registration with code
                agent_id = await self._handle_registration(websocket, auth_message)
            elif auth_message.get("type") == "authenticate":
                # Authentication with token
                agent_id = await self._handle_authentication(websocket, auth_message)
            else:
                await websocket.send_json({
                    "error": "Invalid authentication message"
                })
                await websocket.close(code=4001)
                return

            if not agent_id:
                await websocket.close(code=4001)
                return

            # Get agent and server info
            agent = self.agent_service.db_service.agents.get_agent(agent_id)
            if not agent:
                await websocket.close(code=4001)
                return

            # Register connection
            await self.agent_manager.register_connection(
                agent_id, websocket, agent.server_id
            )

            # Message loop
            while True:
                message = await websocket.receive_text()
                await self.agent_manager.handle_message(agent_id, message)

        except WebSocketDisconnect:
            logger.info(f"Agent {agent_id} WebSocket disconnected")
        except Exception as e:
            logger.error(f"WebSocket error for agent {agent_id}: {e}")
        finally:
            if agent_id:
                await self.agent_manager.unregister_connection(agent_id)

    async def _handle_registration(
        self, websocket: WebSocket, message: dict
    ) -> str | None:
        """Handle agent registration with code."""
        code = message.get("code")
        version = message.get("version", "unknown")

        if not code:
            await websocket.send_json({"error": "Missing registration code"})
            return None

        result = self.agent_service.complete_registration(code, version)

        if not result:
            await websocket.send_json({"error": "Invalid or expired registration code"})
            return None

        await websocket.send_json({
            "type": "registered",
            "agent_id": result.agent_id,
            "token": result.token,
            "config": result.config.model_dump(),
        })

        return result.agent_id

    async def _handle_authentication(
        self, websocket: WebSocket, message: dict
    ) -> str | None:
        """Handle agent authentication with token."""
        token = message.get("token")
        version = message.get("version", "unknown")

        if not token:
            await websocket.send_json({"error": "Missing token"})
            return None

        agent = self.agent_service.validate_token(token)

        if not agent:
            await websocket.send_json({"error": "Invalid token"})
            return None

        # Update version if changed
        if agent.version != version:
            from ..models.agent import AgentUpdate
            self.agent_service.db_service.agents.update_agent(
                agent.id, AgentUpdate(version=version)
            )

        # Get current config
        config = self.agent_service._get_agent_config()

        await websocket.send_json({
            "type": "authenticated",
            "agent_id": agent.id,
            "config": config.model_dump(),
        })

        return agent.id
```

---

## Phase 3: Agent MCP Tools

### Task 3.1: Create Agent Tools

**Files:**
- Create: `backend/src/tools/agent/__init__.py`
- Create: `backend/src/tools/agent/tools.py`

**Step 1: Create __init__.py**

```python
"""Agent tools package."""

from .tools import AgentTools

__all__ = ["AgentTools"]
```

**Step 2: Create tools.py**

```python
"""MCP tools for agent management."""

import logging
from typing import Any

from ...models.agent import AgentInfo, AgentStatus
from ...services.agent_manager import AgentManager
from ...services.agent_service import AgentService

logger = logging.getLogger(__name__)


class AgentTools:
    """MCP tools for agent operations."""

    def __init__(self, agent_service: AgentService, agent_manager: AgentManager):
        self.agent_service = agent_service
        self.agent_manager = agent_manager

    async def install_agent(self, server_id: str) -> dict[str, Any]:
        """
        Create an agent for a server and return registration code.

        Args:
            server_id: The server to install agent on

        Returns:
            Registration code and deployment command
        """
        agent, code = self.agent_service.create_agent(server_id)

        # TODO: Get actual server URL from settings
        server_url = "wss://localhost:8000/ws/agent"

        deploy_command = (
            f"docker run -d "
            f"--name tomo-agent "
            f"--restart unless-stopped "
            f"-v /var/run/docker.sock:/var/run/docker.sock "
            f"-v /:/host:ro "
            f"-v tomo-agent-data:/data "
            f"-e REGISTER_CODE={code.code} "
            f"-e SERVER_URL={server_url} "
            f"ghcr.io/tomo/agent:latest"
        )

        return {
            "agent_id": agent.id,
            "registration_code": code.code,
            "expires_at": code.expires_at.isoformat(),
            "deploy_command": deploy_command,
        }

    async def get_agent_status(self, server_id: str) -> dict[str, Any] | None:
        """
        Get agent status for a server.

        Args:
            server_id: The server ID

        Returns:
            Agent info or None if no agent
        """
        agent = self.agent_service.get_agent_by_server(server_id)
        if not agent:
            return None

        return AgentInfo(
            id=agent.id,
            server_id=agent.server_id,
            status=agent.status,
            version=agent.version,
            last_seen=agent.last_seen,
            registered_at=agent.registered_at,
        ).model_dump()

    async def revoke_agent(self, server_id: str) -> dict[str, Any]:
        """
        Revoke agent access for a server.

        Args:
            server_id: The server ID

        Returns:
            Success status
        """
        agent = self.agent_service.get_agent_by_server(server_id)
        if not agent:
            return {"success": False, "error": "No agent found for server"}

        # Disconnect if connected
        if self.agent_manager.is_connected(agent.id):
            await self.agent_manager.unregister_connection(agent.id)

        # Revoke token
        self.agent_service.revoke_agent(agent.id)

        return {"success": True}

    async def send_agent_command(
        self, server_id: str, method: str, params: dict | None = None
    ) -> Any:
        """
        Send a command to an agent.

        Args:
            server_id: The server ID
            method: JSON-RPC method name
            params: Method parameters

        Returns:
            Command result
        """
        agent = self.agent_service.get_agent_by_server(server_id)
        if not agent:
            raise ValueError("No agent found for server")

        if not self.agent_manager.is_connected(agent.id):
            raise ConnectionError("Agent not connected")

        return await self.agent_manager.send_command(agent.id, method, params)
```

---

## Phase 4: Agent Container - Core

### Task 4.1: Create Agent Project Structure

**Files:**
- Create: `agent/Dockerfile`
- Create: `agent/requirements.txt`
- Create: `agent/src/__init__.py`

**Step 1: Create Dockerfile**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy agent code
COPY src/ ./src/

# Data volume for token persistence
VOLUME /data

ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["python", "-m", "src.main"]
```

**Step 2: Create requirements.txt**

```
websockets>=12.0
docker>=7.0
psutil>=5.9
pydantic>=2.0
```

**Step 3: Create src/__init__.py**

```python
"""Tomo Agent package."""

__version__ = "1.0.0"
```

---

### Task 4.2: Implement Agent Config

**Files:**
- Create: `agent/src/config.py`

```python
"""Agent configuration management."""

import json
import os
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class AgentConfig(BaseModel):
    """Agent runtime configuration."""

    # From environment
    server_url: str = Field(default="")
    register_code: Optional[str] = None

    # From server (persisted)
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
    """Load persisted state from disk."""
    if not STATE_FILE.exists():
        return None

    try:
        data = json.loads(STATE_FILE.read_text())
        return AgentState(**data)
    except Exception:
        return None


def save_state(state: AgentState) -> None:
    """Save state to disk."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state.model_dump(), indent=2))


def update_config(config: AgentConfig, updates: dict) -> AgentConfig:
    """Update config with server-sent values."""
    return config.model_copy(update=updates)
```

---

### Task 4.3: Implement Agent Auth

**Files:**
- Create: `agent/src/auth.py`

```python
"""Agent authentication and registration."""

import json
import logging
from datetime import datetime
from typing import Optional, Tuple

from websockets import WebSocketClientProtocol

from . import __version__
from .config import AgentConfig, AgentState, load_state, save_state

logger = logging.getLogger(__name__)


async def authenticate(
    websocket: WebSocketClientProtocol,
    config: AgentConfig,
) -> Tuple[Optional[str], Optional[AgentConfig]]:
    """
    Authenticate with the server.

    Returns:
        Tuple of (agent_id, updated_config) or (None, None) on failure
    """
    # Try existing token first
    state = load_state()

    if state:
        return await _authenticate_with_token(websocket, state)

    # Fall back to registration code
    if config.register_code:
        return await _register_with_code(websocket, config)

    logger.error("No token or registration code available")
    return None, None


async def _authenticate_with_token(
    websocket: WebSocketClientProtocol,
    state: AgentState,
) -> Tuple[Optional[str], Optional[AgentConfig]]:
    """Authenticate using existing token."""
    await websocket.send(json.dumps({
        "type": "authenticate",
        "token": state.token,
        "version": __version__,
    }))

    response = json.loads(await websocket.recv())

    if response.get("type") == "authenticated":
        logger.info(f"Authenticated as agent {response['agent_id']}")
        config = AgentConfig(**response.get("config", {}))
        return response["agent_id"], config

    logger.error(f"Authentication failed: {response.get('error')}")
    return None, None


async def _register_with_code(
    websocket: WebSocketClientProtocol,
    config: AgentConfig,
) -> Tuple[Optional[str], Optional[AgentConfig]]:
    """Register using registration code."""
    await websocket.send(json.dumps({
        "type": "register",
        "code": config.register_code,
        "version": __version__,
    }))

    response = json.loads(await websocket.recv())

    if response.get("type") == "registered":
        agent_id = response["agent_id"]
        token = response["token"]

        # Persist state
        state = AgentState(
            agent_id=agent_id,
            token=token,
            server_url=config.server_url,
            registered_at=datetime.utcnow().isoformat(),
        )
        save_state(state)

        logger.info(f"Registered as agent {agent_id}")
        updated_config = AgentConfig(**response.get("config", {}))
        return agent_id, updated_config

    logger.error(f"Registration failed: {response.get('error')}")
    return None, None
```

---

### Task 4.4: Implement JSON-RPC Handler

**Files:**
- Create: `agent/src/rpc/__init__.py`
- Create: `agent/src/rpc/handler.py`

**Step 1: Create __init__.py**

```python
"""RPC package."""
```

**Step 2: Create handler.py**

```python
"""JSON-RPC request handler."""

import asyncio
import logging
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class RPCError(Exception):
    """JSON-RPC error."""

    def __init__(self, code: int, message: str, data: Any = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(message)


class RPCHandler:
    """Handles JSON-RPC method dispatch."""

    # Standard JSON-RPC error codes
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603

    def __init__(self):
        self._methods: Dict[str, Callable] = {}

    def register(self, name: str, handler: Callable) -> None:
        """Register a method handler."""
        self._methods[name] = handler

    def register_module(self, prefix: str, module: object) -> None:
        """Register all public methods from a module with a prefix."""
        for name in dir(module):
            if name.startswith("_"):
                continue
            attr = getattr(module, name)
            if callable(attr):
                self._methods[f"{prefix}.{name}"] = attr

    async def handle(self, request: dict) -> Optional[dict]:
        """
        Handle a JSON-RPC request.

        Returns response dict, or None for notifications.
        """
        request_id = request.get("id")

        # Notifications have no id
        is_notification = request_id is None

        try:
            method = request.get("method")
            if not method:
                raise RPCError(self.INVALID_REQUEST, "Missing method")

            if method not in self._methods:
                raise RPCError(self.METHOD_NOT_FOUND, f"Method not found: {method}")

            params = request.get("params", {})
            handler = self._methods[method]

            # Call handler
            if asyncio.iscoroutinefunction(handler):
                result = await handler(**params) if isinstance(params, dict) else await handler(*params)
            else:
                result = handler(**params) if isinstance(params, dict) else handler(*params)

            if is_notification:
                return None

            return {
                "jsonrpc": "2.0",
                "result": result,
                "id": request_id,
            }

        except RPCError as e:
            if is_notification:
                logger.error(f"Notification error: {e.message}")
                return None
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": e.code,
                    "message": e.message,
                    "data": e.data,
                },
                "id": request_id,
            }
        except Exception as e:
            logger.exception(f"Internal error handling {request.get('method')}")
            if is_notification:
                return None
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": self.INTERNAL_ERROR,
                    "message": str(e),
                },
                "id": request_id,
            }
```

---

### Task 4.5: Implement Main Entry Point

**Files:**
- Create: `agent/src/main.py`

```python
"""Tomo Agent main entry point."""

import asyncio
import json
import logging
import signal
import sys
from typing import Optional

import websockets
from websockets import WebSocketClientProtocol

from . import __version__
from .auth import authenticate
from .config import AgentConfig, load_config, load_state, update_config
from .rpc.handler import RPCHandler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


class Agent:
    """Main agent class."""

    def __init__(self):
        self.config = load_config()
        self.agent_id: Optional[str] = None
        self.websocket: Optional[WebSocketClientProtocol] = None
        self.rpc_handler = RPCHandler()
        self.running = True
        self._setup_handlers()

    def _setup_handlers(self):
        """Set up RPC method handlers."""
        # Import and register method modules
        from .rpc.methods import agent, docker, system

        self.rpc_handler.register_module("docker.containers", docker.ContainerMethods())
        self.rpc_handler.register_module("docker.images", docker.ImageMethods())
        self.rpc_handler.register_module("docker.volumes", docker.VolumeMethods())
        self.rpc_handler.register_module("docker.networks", docker.NetworkMethods())
        self.rpc_handler.register_module("system", system.SystemMethods())
        self.rpc_handler.register_module("agent", agent.AgentMethods(self))
        self.rpc_handler.register("metrics.get", system.SystemMethods().get_metrics)
        self.rpc_handler.register("config.update", self._handle_config_update)

    def _handle_config_update(self, **kwargs) -> dict:
        """Handle config update from server."""
        self.config = update_config(self.config, kwargs)
        logger.info(f"Config updated: {kwargs}")
        return {"status": "ok"}

    async def connect(self) -> bool:
        """Connect to the tomo server."""
        # Get server URL from state or config
        state = load_state()
        server_url = state.server_url if state else self.config.server_url

        if not server_url:
            logger.error("No server URL configured")
            return False

        try:
            logger.info(f"Connecting to {server_url}")
            self.websocket = await websockets.connect(server_url)

            # Authenticate
            self.agent_id, updated_config = await authenticate(
                self.websocket, self.config
            )

            if not self.agent_id:
                await self.websocket.close()
                return False

            if updated_config:
                self.config = update_config(self.config, updated_config.model_dump())

            return True

        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False

    async def run(self) -> None:
        """Main run loop."""
        backoff = 1
        max_backoff = 60

        while self.running:
            if await self.connect():
                backoff = 1  # Reset backoff on successful connection
                await self._message_loop()

            if not self.running:
                break

            logger.info(f"Reconnecting in {backoff}s...")
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, max_backoff)

    async def _message_loop(self) -> None:
        """Handle incoming messages."""
        try:
            async for message in self.websocket:
                try:
                    request = json.loads(message)
                    response = await self.rpc_handler.handle(request)

                    if response:
                        await self.websocket.send(json.dumps(response))

                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON: {message[:100]}")
                except Exception as e:
                    logger.exception(f"Error handling message: {e}")

        except websockets.ConnectionClosed:
            logger.info("Connection closed")
        except Exception as e:
            logger.error(f"Message loop error: {e}")

    async def shutdown(self) -> None:
        """Graceful shutdown."""
        logger.info("Shutting down...")
        self.running = False

        if self.websocket:
            await self.websocket.close()


async def main():
    """Main entry point."""
    logger.info(f"Tomo Agent v{__version__} starting")

    agent = Agent()

    # Handle signals
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(agent.shutdown()))

    await agent.run()
    logger.info("Agent stopped")


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Phase 5: Agent Capabilities

### Task 5.1: Implement Docker Methods

**Files:**
- Create: `agent/src/rpc/methods/__init__.py`
- Create: `agent/src/rpc/methods/docker.py`

**Step 1: Create __init__.py**

```python
"""RPC method modules."""
```

**Step 2: Create docker.py**

```python
"""Docker RPC methods."""

import logging
from typing import Any, Dict, List, Optional

import docker
from docker.errors import NotFound, APIError

logger = logging.getLogger(__name__)

# Shared Docker client
_client: Optional[docker.DockerClient] = None


def get_client() -> docker.DockerClient:
    """Get or create Docker client."""
    global _client
    if _client is None:
        _client = docker.from_env()
    return _client


class ContainerMethods:
    """Container management methods."""

    def list(self, all: bool = False) -> List[Dict[str, Any]]:
        """List containers."""
        client = get_client()
        containers = client.containers.list(all=all)
        return [
            {
                "id": c.id[:12],
                "name": c.name,
                "image": c.image.tags[0] if c.image.tags else c.image.id[:12],
                "status": c.status,
                "created": c.attrs.get("Created"),
            }
            for c in containers
        ]

    def run(
        self,
        image: str,
        name: str,
        ports: Optional[Dict[str, int]] = None,
        env: Optional[Dict[str, str]] = None,
        volumes: Optional[Dict[str, Dict]] = None,
        network: Optional[str] = None,
        restart_policy: Optional[Dict] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Run a new container."""
        client = get_client()
        container = client.containers.run(
            image=image,
            name=name,
            ports=ports,
            environment=env,
            volumes=volumes,
            network=network,
            restart_policy=restart_policy or {"Name": "unless-stopped"},
            detach=True,
            **kwargs,
        )
        return {"id": container.id[:12], "name": container.name}

    def start(self, container: str) -> Dict[str, str]:
        """Start a container."""
        client = get_client()
        c = client.containers.get(container)
        c.start()
        return {"status": "started"}

    def stop(self, container: str, timeout: int = 10) -> Dict[str, str]:
        """Stop a container."""
        client = get_client()
        c = client.containers.get(container)
        c.stop(timeout=timeout)
        return {"status": "stopped"}

    def remove(self, container: str, force: bool = False) -> Dict[str, str]:
        """Remove a container."""
        client = get_client()
        c = client.containers.get(container)
        c.remove(force=force)
        return {"status": "removed"}

    def restart(self, container: str) -> Dict[str, str]:
        """Restart a container."""
        client = get_client()
        c = client.containers.get(container)
        c.restart()
        return {"status": "restarted"}

    def logs(
        self, container: str, tail: int = 100, follow: bool = False
    ) -> Dict[str, Any]:
        """Get container logs."""
        client = get_client()
        c = client.containers.get(container)
        logs = c.logs(tail=tail, timestamps=True).decode("utf-8")
        return {"logs": logs}

    def inspect(self, container: str) -> Dict[str, Any]:
        """Get container details."""
        client = get_client()
        c = client.containers.get(container)
        return c.attrs

    def stats(self, container: str) -> Dict[str, Any]:
        """Get container resource stats."""
        client = get_client()
        c = client.containers.get(container)
        stats = c.stats(stream=False)
        return {
            "cpu_percent": self._calc_cpu_percent(stats),
            "memory_usage": stats["memory_stats"].get("usage", 0),
            "memory_limit": stats["memory_stats"].get("limit", 0),
            "network_rx": sum(
                v.get("rx_bytes", 0) for v in stats.get("networks", {}).values()
            ),
            "network_tx": sum(
                v.get("tx_bytes", 0) for v in stats.get("networks", {}).values()
            ),
        }

    def _calc_cpu_percent(self, stats: dict) -> float:
        """Calculate CPU percentage from stats."""
        cpu_delta = (
            stats["cpu_stats"]["cpu_usage"]["total_usage"]
            - stats["precpu_stats"]["cpu_usage"]["total_usage"]
        )
        system_delta = (
            stats["cpu_stats"]["system_cpu_usage"]
            - stats["precpu_stats"]["system_cpu_usage"]
        )
        if system_delta > 0:
            cpu_count = stats["cpu_stats"]["online_cpus"]
            return (cpu_delta / system_delta) * cpu_count * 100
        return 0.0


class ImageMethods:
    """Image management methods."""

    def list(self) -> List[Dict[str, Any]]:
        """List images."""
        client = get_client()
        images = client.images.list()
        return [
            {
                "id": img.id[:19],
                "tags": img.tags,
                "size": img.attrs.get("Size", 0),
                "created": img.attrs.get("Created"),
            }
            for img in images
        ]

    def pull(self, image: str, tag: str = "latest") -> Dict[str, str]:
        """Pull an image."""
        client = get_client()
        client.images.pull(image, tag=tag)
        return {"status": "pulled", "image": f"{image}:{tag}"}

    def remove(self, image: str, force: bool = False) -> Dict[str, str]:
        """Remove an image."""
        client = get_client()
        client.images.remove(image, force=force)
        return {"status": "removed"}

    def prune(self) -> Dict[str, Any]:
        """Remove unused images."""
        client = get_client()
        result = client.images.prune()
        return {
            "deleted": result.get("ImagesDeleted", []),
            "space_reclaimed": result.get("SpaceReclaimed", 0),
        }


class VolumeMethods:
    """Volume management methods."""

    def list(self) -> List[Dict[str, Any]]:
        """List volumes."""
        client = get_client()
        volumes = client.volumes.list()
        return [
            {
                "name": v.name,
                "driver": v.attrs.get("Driver"),
                "mountpoint": v.attrs.get("Mountpoint"),
            }
            for v in volumes
        ]

    def create(self, name: str, driver: str = "local") -> Dict[str, str]:
        """Create a volume."""
        client = get_client()
        client.volumes.create(name=name, driver=driver)
        return {"status": "created", "name": name}

    def remove(self, name: str, force: bool = False) -> Dict[str, str]:
        """Remove a volume."""
        client = get_client()
        v = client.volumes.get(name)
        v.remove(force=force)
        return {"status": "removed"}


class NetworkMethods:
    """Network management methods."""

    def list(self) -> List[Dict[str, Any]]:
        """List networks."""
        client = get_client()
        networks = client.networks.list()
        return [
            {
                "id": n.id[:12],
                "name": n.name,
                "driver": n.attrs.get("Driver"),
                "scope": n.attrs.get("Scope"),
            }
            for n in networks
        ]

    def create(self, name: str, driver: str = "bridge") -> Dict[str, str]:
        """Create a network."""
        client = get_client()
        client.networks.create(name=name, driver=driver)
        return {"status": "created", "name": name}

    def remove(self, name: str) -> Dict[str, str]:
        """Remove a network."""
        client = get_client()
        n = client.networks.get(name)
        n.remove()
        return {"status": "removed"}
```

---

### Task 5.2: Implement System Methods

**Files:**
- Create: `agent/src/rpc/methods/system.py`

```python
"""System RPC methods."""

import asyncio
import logging
import os
import platform
import subprocess
from typing import Any, Dict, Optional

import psutil

from ..docker import get_client

logger = logging.getLogger(__name__)


class SystemMethods:
    """System information and command methods."""

    def info(self) -> Dict[str, Any]:
        """Get system information."""
        docker_version = "unknown"
        try:
            client = get_client()
            docker_version = client.version().get("Version", "unknown")
        except Exception:
            pass

        return {
            "os": self._get_os_info(),
            "kernel": platform.release(),
            "arch": platform.machine(),
            "hostname": platform.node(),
            "docker_version": docker_version,
        }

    def exec(
        self, command: str, timeout: Optional[int] = 60
    ) -> Dict[str, Any]:
        """Execute a system command."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": f"Command timed out after {timeout}s",
                "exit_code": -1,
            }
        except Exception as e:
            return {
                "stdout": "",
                "stderr": str(e),
                "exit_code": -1,
            }

    def get_metrics(self) -> Dict[str, Any]:
        """Get current system metrics."""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/host" if os.path.exists("/host") else "/")

        # Get container stats
        running = 0
        stopped = 0
        try:
            client = get_client()
            for c in client.containers.list(all=True):
                if c.status == "running":
                    running += 1
                else:
                    stopped += 1
        except Exception:
            pass

        return {
            "cpu": cpu_percent,
            "memory": {
                "used": memory.used,
                "total": memory.total,
                "percent": memory.percent,
            },
            "disk": {
                "used": disk.used,
                "total": disk.total,
                "percent": disk.percent,
            },
            "containers": {
                "running": running,
                "stopped": stopped,
            },
        }

    def _get_os_info(self) -> str:
        """Get OS information."""
        # Try to read from /host/etc/os-release first
        os_release_paths = [
            "/host/etc/os-release",
            "/etc/os-release",
        ]

        for path in os_release_paths:
            try:
                with open(path) as f:
                    for line in f:
                        if line.startswith("PRETTY_NAME="):
                            return line.split("=", 1)[1].strip().strip('"')
            except FileNotFoundError:
                continue

        return f"{platform.system()} {platform.release()}"
```

---

### Task 5.3: Implement Agent Methods

**Files:**
- Create: `agent/src/rpc/methods/agent.py`

```python
"""Agent RPC methods."""

import logging
from typing import Any, Dict, TYPE_CHECKING

from ... import __version__

if TYPE_CHECKING:
    from ...main import Agent

logger = logging.getLogger(__name__)


class AgentMethods:
    """Agent management methods."""

    def __init__(self, agent: "Agent"):
        self.agent = agent

    def ping(self) -> Dict[str, Any]:
        """Health check endpoint."""
        return {
            "status": "ok",
            "version": __version__,
            "agent_id": self.agent.agent_id,
        }

    def update(self, version: str) -> Dict[str, str]:
        """
        Trigger agent update.

        This pulls the new image and signals for container restart.
        The orchestrator (Docker restart policy) will start the new version.
        """
        from .docker import get_client

        image = f"ghcr.io/tomo/agent:{version}"

        logger.info(f"Updating agent to {version}")

        try:
            client = get_client()

            # Pull new image
            logger.info(f"Pulling {image}")
            client.images.pull("ghcr.io/tomo/agent", tag=version)

            # Signal for restart (container will be replaced by orchestrator)
            # We exit with code 0, and --restart unless-stopped will restart us
            logger.info("Update pulled, initiating restart...")

            # Schedule shutdown
            import asyncio
            asyncio.get_event_loop().call_later(
                1.0, lambda: asyncio.create_task(self.agent.shutdown())
            )

            return {"status": "updating", "version": version}

        except Exception as e:
            logger.error(f"Update failed: {e}")
            return {"status": "error", "message": str(e)}
```

---

### Task 5.4: Implement Metrics Collector

**Files:**
- Create: `agent/src/collectors/__init__.py`
- Create: `agent/src/collectors/metrics.py`

**Step 1: Create __init__.py**

```python
"""Collectors package."""
```

**Step 2: Create metrics.py**

```python
"""Metrics collection and push."""

import asyncio
import json
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..main import Agent

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collects and pushes metrics to server."""

    def __init__(self, agent: "Agent"):
        self.agent = agent
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start metrics collection."""
        self._task = asyncio.create_task(self._collection_loop())
        logger.info("Metrics collector started")

    async def stop(self) -> None:
        """Stop metrics collection."""
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Metrics collector stopped")

    async def _collection_loop(self) -> None:
        """Main collection loop."""
        from ..rpc.methods.system import SystemMethods

        system = SystemMethods()

        while True:
            try:
                interval = self.agent.config.metrics_interval
                await asyncio.sleep(interval)

                if not self.agent.websocket:
                    continue

                metrics = system.get_metrics()

                # Send as notification (no id = no response expected)
                notification = {
                    "jsonrpc": "2.0",
                    "method": "metrics.update",
                    "params": metrics,
                }

                await self.agent.websocket.send(json.dumps(notification))
                logger.debug(f"Metrics pushed: CPU={metrics['cpu']}%")

            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
```

---

### Task 5.5: Implement Health Reporter

**Files:**
- Create: `agent/src/collectors/health.py`

```python
"""Health status reporting."""

import asyncio
import json
import logging
import time
from typing import TYPE_CHECKING

from .. import __version__

if TYPE_CHECKING:
    from ..main import Agent

logger = logging.getLogger(__name__)

_start_time = time.time()


class HealthReporter:
    """Reports agent health status to server."""

    def __init__(self, agent: "Agent"):
        self.agent = agent
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start health reporting."""
        self._task = asyncio.create_task(self._report_loop())
        logger.info("Health reporter started")

    async def stop(self) -> None:
        """Stop health reporting."""
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Health reporter stopped")

    async def _report_loop(self) -> None:
        """Main reporting loop."""
        while True:
            try:
                interval = self.agent.config.health_interval
                await asyncio.sleep(interval)

                if not self.agent.websocket:
                    continue

                uptime = int(time.time() - _start_time)

                notification = {
                    "jsonrpc": "2.0",
                    "method": "health.status",
                    "params": {
                        "status": "healthy",
                        "uptime": uptime,
                        "version": __version__,
                    },
                }

                await self.agent.websocket.send(json.dumps(notification))
                logger.debug(f"Health reported: uptime={uptime}s")

            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.error(f"Health reporting error: {e}")
```

---

## Summary

This implementation plan covers:

- **Phase 1**: Database schema, models, and services for agent persistence
- **Phase 2**: WebSocket server and connection management
- **Phase 3**: MCP tools for agent operations
- **Phase 4**: Agent container core (config, auth, RPC handler, main loop)
- **Phase 5**: Agent capabilities (Docker, system, metrics, health)

**Remaining phases** (Phase 6-8) cover:
- Agent lifecycle (auto-update, graceful shutdown)
- Backend integration (routing, SSH fallback)
- Frontend integration (status display, install wizard, settings)

Each task includes exact file paths, complete code, and can be implemented independently following TDD principles.
