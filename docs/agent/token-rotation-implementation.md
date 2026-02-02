# Agent Token Rotation - Implementation Plan

**Related Documents:**
- [Token Rotation Plan](token-rotation-plan.md)
- [Task List](token-rotation-tasks.md)
- [Authentication System](authentication.md)

---

## Phase 1: Schema Updates

### 1.1 Update Agent Model

**File:** `backend/src/models/agent.py`

Add new fields to `Agent` model:

```python
class Agent(BaseModel):
    # ... existing fields ...

    # Token rotation fields
    pending_token_hash: Optional[str] = None
    token_issued_at: Optional[datetime] = None
    token_expires_at: Optional[datetime] = None
```

### 1.2 Update Database Schema

**File:** `backend/src/init_db/schema_agents.py`

Add migration to add columns:

```python
def migrate_add_token_rotation_fields(conn: sqlite3.Connection):
    """Add token rotation fields to agents table."""
    cursor = conn.cursor()

    # Check if columns exist
    cursor.execute("PRAGMA table_info(agents)")
    columns = {row[1] for row in cursor.fetchall()}

    if "pending_token_hash" not in columns:
        cursor.execute("""
            ALTER TABLE agents
            ADD COLUMN pending_token_hash TEXT
        """)

    if "token_issued_at" not in columns:
        cursor.execute("""
            ALTER TABLE agents
            ADD COLUMN token_issued_at TEXT
        """)

    if "token_expires_at" not in columns:
        cursor.execute("""
            ALTER TABLE agents
            ADD COLUMN token_expires_at TEXT
        """)

    conn.commit()
```

### 1.3 Update Settings Model

**File:** `backend/src/models/settings.py`

Add rotation settings:

```python
class SecuritySettings(BaseModel):
    # ... existing fields ...

    # Agent token rotation
    agent_token_rotation_days: int = Field(
        default=7,
        ge=1,
        le=365,
        description="Days before agent token rotation"
    )
    agent_token_grace_period_minutes: int = Field(
        default=5,
        ge=1,
        le=60,
        description="Minutes to accept old token during rotation"
    )
```

---

## Phase 2: Backend Service Updates

### 2.1 Token Rotation Methods

**File:** `backend/src/services/agent_service.py`

Add rotation methods:

```python
def initiate_rotation(self, agent_id: str) -> Optional[str]:
    """Generate new token and store as pending.

    Returns new token (plaintext) or None if agent not found.
    """
    agent = self.get_agent(agent_id)
    if not agent or not agent.token_hash:
        return None

    # Generate new token
    new_token = secrets.token_urlsafe(32)
    pending_hash = self._hash_token(new_token)

    # Calculate expiry for grace period
    settings = self._get_security_settings()
    grace_minutes = settings.agent_token_grace_period_minutes

    # Store pending token
    self._update_agent(agent_id, {
        "pending_token_hash": pending_hash,
    })

    logger.info("Token rotation initiated", agent_id=agent_id)
    return new_token


def complete_rotation(self, agent_id: str) -> bool:
    """Promote pending token to current, clear old.

    Called when agent acknowledges rotation.
    """
    agent = self.get_agent(agent_id)
    if not agent or not agent.pending_token_hash:
        return False

    settings = self._get_security_settings()
    rotation_days = settings.agent_token_rotation_days

    now = datetime.now(UTC)
    expires_at = now + timedelta(days=rotation_days)

    self._update_agent(agent_id, {
        "token_hash": agent.pending_token_hash,
        "pending_token_hash": None,
        "token_issued_at": now.isoformat(),
        "token_expires_at": expires_at.isoformat(),
    })

    logger.info("Token rotation completed", agent_id=agent_id)
    return True


def cancel_rotation(self, agent_id: str) -> bool:
    """Cancel pending rotation (on error/timeout)."""
    self._update_agent(agent_id, {
        "pending_token_hash": None,
    })
    logger.warning("Token rotation cancelled", agent_id=agent_id)
    return True
```

### 2.2 Update Token Validation

**File:** `backend/src/services/agent_service.py`

Modify `validate_token` to check both tokens:

```python
def validate_token(self, token: str) -> Optional[Agent]:
    """Validate token, checking both current and pending."""
    token_hash = self._hash_token(token)

    # Check current token
    agent = self._find_agent_by_token_hash(token_hash)
    if agent:
        self._update_last_seen(agent.id)
        return agent

    # Check pending token (during rotation)
    agent = self._find_agent_by_pending_token_hash(token_hash)
    if agent:
        # Agent is using new token, complete rotation
        self.complete_rotation(agent.id)
        self._update_last_seen(agent.id)
        return agent

    return None


def _find_agent_by_pending_token_hash(self, token_hash: str) -> Optional[Agent]:
    """Find agent by pending token hash."""
    # Query: SELECT * FROM agents WHERE pending_token_hash = ?
    pass
```

### 2.3 Update Registration to Set Expiry

**File:** `backend/src/services/agent_service.py`

Update `complete_registration`:

```python
def complete_registration(self, agent_id: str, code: str) -> Optional[str]:
    # ... existing validation ...

    token = secrets.token_urlsafe(32)
    token_hash = self._hash_token(token)

    settings = self._get_security_settings()
    rotation_days = settings.agent_token_rotation_days

    now = datetime.now(UTC)
    expires_at = now + timedelta(days=rotation_days)

    self._update_agent(agent_id, {
        "token_hash": token_hash,
        "token_issued_at": now.isoformat(),
        "token_expires_at": expires_at.isoformat(),
        "registration_code": None,
        "status": AgentStatus.CONNECTED,
    })

    return token
```

---

## Phase 3: WebSocket Handler

### 3.1 Rotation Message Handler

**File:** `backend/src/services/agent_websocket.py`

Add rotation initiation:

```python
async def send_rotation_request(
    self,
    agent_id: str,
    new_token: str,
    grace_period_seconds: int
) -> bool:
    """Send rotation request to connected agent."""
    ws = self._get_agent_connection(agent_id)
    if not ws:
        return False

    message = {
        "jsonrpc": "2.0",
        "method": "agent.rotate_token",
        "params": {
            "new_token": new_token,
            "grace_period_seconds": grace_period_seconds,
        },
        "id": str(uuid.uuid4()),
    }

    try:
        await asyncio.wait_for(
            ws.send(json.dumps(message)),
            timeout=10.0
        )
        return True
    except asyncio.TimeoutError:
        logger.error("Rotation request timeout", agent_id=agent_id)
        return False
```

### 3.2 Handle Rotation Acknowledgment

**File:** `backend/src/services/agent_websocket.py`

Handle agent's response:

```python
async def handle_message(self, agent_id: str, message: dict):
    method = message.get("method")

    if method == "agent.rotation_complete":
        # Agent confirms it saved the new token
        self.agent_service.complete_rotation(agent_id)
        return {"status": "ok"}

    elif method == "agent.rotation_failed":
        # Agent failed to save new token
        self.agent_service.cancel_rotation(agent_id)
        return {"status": "error", "retry": True}

    # ... other handlers ...
```

---

## Phase 4: Agent Updates

### 4.1 Handle Rotation Request

**File:** `agent/src/auth.py`

Add rotation handler:

```python
async def handle_rotation_request(self, params: dict) -> dict:
    """Handle server-initiated token rotation."""
    new_token = params.get("new_token")
    grace_period = params.get("grace_period_seconds", 300)

    if not new_token:
        return {"error": "No token provided"}

    try:
        # Save new token to state file
        self._save_state(new_token)

        logger.info("Token rotation complete")
        return {"status": "rotated"}

    except Exception as e:
        logger.error("Token rotation failed", error=str(e))
        return {"error": str(e)}
```

### 4.2 Update Message Router

**File:** `agent/src/auth.py` or `agent/src/main.py`

Route rotation messages:

```python
async def handle_server_message(self, message: dict):
    method = message.get("method")

    if method == "agent.rotate_token":
        result = await self.handle_rotation_request(message.get("params", {}))
        # Send acknowledgment
        await self.ws.send(json.dumps({
            "jsonrpc": "2.0",
            "method": "agent.rotation_complete" if "status" in result else "agent.rotation_failed",
            "params": result,
            "id": message.get("id"),
        }))
```

---

## Phase 5: MCP Tool

### 5.1 Create Rotation Tool

**File:** `backend/src/tools/agent/rotate_token_tool.py`

```python
from mcp.server.fastmcp import Context
from models.agent import Agent
from services.agent_service import AgentService

async def rotate_agent_token(
    ctx: Context,
    agent_id: str
) -> dict:
    """Manually trigger token rotation for an agent.

    Args:
        agent_id: The agent ID to rotate token for

    Returns:
        Status of rotation initiation
    """
    agent_service: AgentService = ctx.server.agent_service

    # Check agent exists and is connected
    agent = agent_service.get_agent(agent_id)
    if not agent:
        return {"error": "Agent not found", "agent_id": agent_id}

    if agent.status != "connected":
        return {"error": "Agent not connected", "status": agent.status}

    # Initiate rotation
    new_token = agent_service.initiate_rotation(agent_id)
    if not new_token:
        return {"error": "Failed to generate new token"}

    # Send to agent via WebSocket
    ws_service = ctx.server.websocket_service
    settings = agent_service._get_security_settings()
    grace_seconds = settings.agent_token_grace_period_minutes * 60

    success = await ws_service.send_rotation_request(
        agent_id, new_token, grace_seconds
    )

    if success:
        return {
            "status": "rotation_initiated",
            "agent_id": agent_id,
            "grace_period_seconds": grace_seconds,
        }
    else:
        agent_service.cancel_rotation(agent_id)
        return {"error": "Failed to send rotation request to agent"}
```

### 5.2 Register Tool

**File:** `backend/src/tools/agent/__init__.py`

```python
from .rotate_token_tool import rotate_agent_token

__all__ = [
    # ... existing exports ...
    "rotate_agent_token",
]
```

---

## Phase 6: Automatic Rotation

### 6.1 Background Task

**File:** `backend/src/services/agent_lifecycle.py`

Add periodic rotation check:

```python
async def check_token_expiry(self):
    """Check for agents needing token rotation."""
    now = datetime.now(UTC)

    agents = self.agent_service.get_agents_needing_rotation(now)

    for agent in agents:
        if agent.status == "connected":
            try:
                await self.rotate_agent_token(agent.id)
            except Exception as e:
                logger.error(
                    "Auto-rotation failed",
                    agent_id=agent.id,
                    error=str(e)
                )


async def start_rotation_scheduler(self):
    """Start background task for automatic rotation."""
    while True:
        await self.check_token_expiry()
        await asyncio.sleep(3600)  # Check every hour
```

### 6.2 Query for Expiring Tokens

**File:** `backend/src/services/agent_service.py`

```python
def get_agents_needing_rotation(self, as_of: datetime) -> List[Agent]:
    """Get agents with expired or expiring tokens."""
    # Query: SELECT * FROM agents
    #        WHERE token_expires_at < ?
    #        AND token_hash IS NOT NULL
    #        AND pending_token_hash IS NULL
    pass
```

---

## File Summary

| Phase | File | Action |
|-------|------|--------|
| 1 | `backend/src/models/agent.py` | Add fields |
| 1 | `backend/src/init_db/schema_agents.py` | Add migration |
| 1 | `backend/src/models/settings.py` | Add settings |
| 2 | `backend/src/services/agent_service.py` | Add rotation methods |
| 3 | `backend/src/services/agent_websocket.py` | Add message handlers |
| 4 | `agent/src/auth.py` | Handle rotation |
| 5 | `backend/src/tools/agent/rotate_token_tool.py` | Create tool |
| 5 | `backend/src/tools/agent/__init__.py` | Export tool |
| 6 | `backend/src/services/agent_lifecycle.py` | Add scheduler |

---

## Testing Checkpoints

### After Phase 1
- [ ] Database migration runs successfully
- [ ] Agent model accepts new fields
- [ ] Settings model validates rotation settings

### After Phase 2
- [ ] `initiate_rotation()` generates new token
- [ ] `validate_token()` accepts both tokens
- [ ] `complete_rotation()` promotes pending token
- [ ] Registration sets token expiry

### After Phase 3
- [ ] WebSocket sends rotation request
- [ ] WebSocket receives acknowledgment

### After Phase 4
- [ ] Agent handles rotation message
- [ ] Agent saves new token to state
- [ ] Agent sends acknowledgment

### After Phase 5
- [ ] MCP tool triggers rotation
- [ ] Tool returns appropriate status

### After Phase 6
- [ ] Scheduler detects expired tokens
- [ ] Automatic rotation triggers correctly
