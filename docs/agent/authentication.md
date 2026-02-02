# Agent Authentication System

This document describes the authentication system used between Tomo agents and the backend server.

## Overview

The agent authentication system uses a two-phase approach:
1. **Registration Phase**: Agent registers with a one-time registration code
2. **Token Phase**: Agent authenticates with a long-lived token

Communication happens over WebSocket using JSON-RPC 2.0 protocol.

## Architecture

```
┌─────────────────┐                    ┌─────────────────┐
│     Agent       │                    │    Backend      │
│                 │                    │                 │
│  ┌───────────┐  │   WebSocket/TLS    │  ┌───────────┐  │
│  │ auth.py   │◄─┼────────────────────┼──│ agent_    │  │
│  │           │  │                    │  │ service.py│  │
│  └─────┬─────┘  │                    │  └─────┬─────┘  │
│        │        │                    │        │        │
│  ┌─────▼─────┐  │                    │  ┌─────▼─────┐  │
│  │encryption │  │                    │  │ SQLite DB │  │
│  │   .py     │  │                    │  │           │  │
│  └───────────┘  │                    │  └───────────┘  │
│                 │                    │                 │
│  State File:    │                    │  Stores:        │
│  - token (enc)  │                    │  - token_hash   │
│  - server_url   │                    │  - agent_id     │
└─────────────────┘                    └─────────────────┘
```

## Registration Flow

### Step 1: Generate Registration Code (Backend)

```python
# backend/src/services/agent_service.py
def generate_registration_code(self, agent_id: str) -> str:
    code = secrets.token_urlsafe(16)  # 22 chars
    expires_at = datetime.now(UTC) + timedelta(days=30)
    # Store in agents table: registration_code, registration_expires_at
    return code
```

### Step 2: Agent Registers with Code

```python
# agent/src/auth.py
async def _register_with_code(self, ws, code: str) -> str:
    # Send registration request
    await ws.send(json.dumps({
        "jsonrpc": "2.0",
        "method": "agent.register",
        "params": {"registration_code": code},
        "id": str(uuid.uuid4())
    }))

    # Receive token in response
    response = await ws.recv()
    token = response["result"]["token"]

    # Save to state file (encrypted)
    self._save_state(token)
    return token
```

### Step 3: Backend Completes Registration

```python
# backend/src/services/agent_service.py
def complete_registration(self, agent_id: str, code: str) -> Optional[str]:
    # Validate code matches and not expired
    if agent.registration_code != code:
        return None
    if agent.registration_expires_at < datetime.now(UTC):
        return None

    # Generate token
    token = secrets.token_urlsafe(32)  # 43 chars

    # Store hash (not plaintext)
    token_hash = self._hash_token(token)

    # Update agent: token_hash, status=CONNECTED, clear registration_code
    return token
```

## Token Authentication Flow

### Step 1: Agent Loads Token

```python
# agent/src/auth.py
def _load_state(self) -> Optional[str]:
    state_file = Path("~/.tomo/agent_state.json").expanduser()
    if not state_file.exists():
        return None

    data = json.loads(state_file.read_text())
    encrypted_token = data.get("token")

    # Decrypt using machine-derived key
    return decrypt_token(encrypted_token)
```

### Step 2: Agent Authenticates

```python
# agent/src/auth.py
async def _authenticate_with_token(self, ws, token: str) -> bool:
    await ws.send(json.dumps({
        "jsonrpc": "2.0",
        "method": "agent.authenticate",
        "params": {"token": token},
        "id": str(uuid.uuid4())
    }))

    response = await ws.recv()
    return response.get("result", {}).get("authenticated", False)
```

### Step 3: Backend Validates Token

```python
# backend/src/services/agent_service.py
def validate_token(self, token: str) -> Optional[Agent]:
    token_hash = self._hash_token(token)

    # Find agent with matching hash
    agent = self._find_agent_by_token_hash(token_hash)
    if agent:
        agent.status = AgentStatus.CONNECTED
        agent.last_seen = datetime.now(UTC)
    return agent
```

## Token Security

### Server-Side (Backend)

| Aspect | Implementation |
|--------|----------------|
| Storage | SHA-256 hash only (never plaintext) |
| Generation | `secrets.token_urlsafe(32)` = 256 bits entropy |
| Comparison | Hash comparison (timing-safe via SQLite lookup) |
| Revocation | Clear `token_hash`, set status to DISCONNECTED |

```python
# backend/src/services/agent_service.py
def _hash_token(self, token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

def revoke_agent_token(self, agent_id: str) -> bool:
    # Clear token_hash, set status=DISCONNECTED
    return True
```

### Client-Side (Agent)

| Aspect | Implementation |
|--------|----------------|
| Storage | Encrypted at rest using Fernet |
| Key Derivation | PBKDF2 with 480,000 iterations (OWASP 2023) |
| Key Source | Machine ID (`/etc/machine-id`) |
| Salt | Random 16 bytes, stored with ciphertext |

```python
# agent/src/lib/encryption.py
def encrypt_token(token: str) -> str:
    salt = os.urandom(16)
    key = derive_key(get_machine_key(), salt)
    fernet = Fernet(key)
    ciphertext = fernet.encrypt(token.encode())
    return base64.b64encode(salt + ciphertext).decode()

def decrypt_token(encrypted: str) -> str:
    data = base64.b64decode(encrypted)
    salt, ciphertext = data[:16], data[16:]
    key = derive_key(get_machine_key(), salt)
    fernet = Fernet(key)
    return fernet.decrypt(ciphertext).decode()

def derive_key(password: bytes, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,  # OWASP 2023 recommendation
    )
    return base64.urlsafe_b64encode(kdf.derive(password))

def get_machine_key() -> bytes:
    machine_id = Path("/etc/machine-id").read_text().strip()
    return machine_id.encode()
```

## Agent States

```python
# backend/src/models/agent.py
class AgentStatus(str, Enum):
    PENDING = "pending"         # Registered but never connected
    CONNECTED = "connected"     # Currently connected
    DISCONNECTED = "disconnected"  # Was connected, now offline
    UPDATING = "updating"       # Updating agent software
```

### State Transitions

```
                 ┌──────────────┐
                 │   PENDING    │
                 │ (created,    │
                 │  has reg code)│
                 └──────┬───────┘
                        │ register with code
                        ▼
    revoke token  ┌──────────────┐  disconnect
    ◄─────────────│  CONNECTED   │─────────────►
                  │ (has token)  │
                  └──────┬───────┘
                         │
            ┌────────────┼────────────┐
            │            │            │
            ▼            ▼            ▼
    ┌──────────────┐ ┌──────────┐ ┌──────────────┐
    │ DISCONNECTED │ │ UPDATING │ │   revoked    │
    │              │ │          │ │ (no token)   │
    └──────────────┘ └──────────┘ └──────────────┘
```

## Data Models

### Agent Table Schema

```sql
CREATE TABLE agents (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    server_id TEXT REFERENCES servers(id),

    -- Registration
    registration_code TEXT,
    registration_expires_at TEXT,  -- ISO timestamp

    -- Authentication
    token_hash TEXT,  -- SHA-256 hash, NULL if revoked

    -- State
    status TEXT DEFAULT 'pending',  -- AgentStatus enum
    last_seen TEXT,  -- ISO timestamp

    -- Metadata
    version TEXT,
    capabilities TEXT,  -- JSON array
    created_at TEXT,
    updated_at TEXT
);
```

### Agent Model (Pydantic)

```python
# backend/src/models/agent.py
class Agent(BaseModel):
    id: str
    name: str
    server_id: Optional[str]

    # Registration
    registration_code: Optional[str]
    registration_expires_at: Optional[datetime]

    # Authentication
    token_hash: Optional[str]

    # State
    status: AgentStatus = AgentStatus.PENDING
    last_seen: Optional[datetime]

    # Metadata
    version: Optional[str]
    capabilities: List[str] = []
    created_at: datetime
    updated_at: datetime
```

## Token Rotation

Token rotation provides automatic renewal of agent authentication tokens to limit exposure if a token is compromised.

### Overview

```
┌─────────────┐      initiate_rotation      ┌─────────────┐
│   Backend   │ ──────────────────────────► │    Agent    │
│             │   agent.rotate_token RPC    │             │
│             │   (new_token, grace_period) │             │
│             │                             │             │
│   Stores:   │                             │   Saves:    │
│ - token_hash│ ◄────────────────────────── │ - new token │
│ - pending_  │   uses new token on         │   to state  │
│   token_hash│   next connection           │   file      │
└─────────────┘                             └─────────────┘
```

### Rotation Flow

1. **Backend initiates rotation** - Generates new token, stores hash as `pending_token_hash`
2. **Sends to agent via WebSocket** - `agent.rotate_token` RPC with new token and grace period
3. **Agent saves new token** - Encrypts and saves to state file
4. **Grace period** - Both old and new tokens valid during grace period (default: 5 minutes)
5. **Rotation completes** - When agent uses new token, `pending_token_hash` promoted to `token_hash`

### Database Schema Additions

```sql
-- Added to agents table
pending_token_hash TEXT,        -- Hash of pending new token during rotation
token_issued_at TEXT,           -- When current token was issued
token_expires_at TEXT           -- When token expires (triggers rotation)
```

### Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `agent_token_rotation_days` | 7 | Days until token expires |
| `agent_token_grace_period_minutes` | 5 | Minutes old token remains valid |

### Automatic Rotation

A background scheduler runs hourly to:
1. Query agents with expired `token_expires_at`
2. Initiate rotation for connected agents
3. Skip disconnected agents (will rotate on reconnect)

### Manual Rotation

Use the `rotate_agent_token` MCP tool or CLI command:

```bash
# Via CLI
tomo agent rotate <server-id>
```

### Agent Handler

```python
# agent/src/rpc/agent_handlers.py
def handle_rotate_token(new_token: str, grace_period_seconds: int = 300):
    """Handle token rotation request from server."""
    current_state = load_state()
    new_state = AgentState(
        agent_id=current_state.agent_id,
        token=new_token,  # Will be encrypted
        server_url=current_state.server_url,
    )
    save_state(new_state)
    return {"status": "ok", "rotated_at": datetime.now(UTC).isoformat()}
```

## Current Limitations

### Single Token per Agent
- Each agent has exactly one active token
- During rotation, both old and new tokens valid for grace period
- If agent disconnects during rotation, can reconnect with either token

## Security Considerations

### Strengths
- Token hashing prevents plaintext leakage from DB
- Encryption at rest protects tokens on agent
- Machine-derived key ties tokens to specific hardware
- PBKDF2 with high iterations resists offline attacks

### Weaknesses
- No token rotation increases exposure window
- Machine ID is readable by any process on agent
- No mutual TLS (relies on WSS for transport security)
- Registration codes have long validity (30 days)

## Related Files

| File | Purpose |
|------|---------|
| `agent/src/auth.py` | Agent-side authentication logic |
| `agent/src/lib/encryption.py` | Token encryption at rest |
| `backend/src/services/agent_service.py` | Server-side agent management |
| `backend/src/models/agent.py` | Agent data models |
| `backend/src/init_db/schema_agents.py` | Database schema |
