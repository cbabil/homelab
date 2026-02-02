# Agent Token Rotation - Plan

## Problem Statement

Currently, agent tokens are long-lived with no expiration or rotation mechanism. This creates security risks:

1. **Extended Exposure Window**: A compromised token remains valid indefinitely
2. **No Proactive Security**: No automatic rotation to limit token lifespan
3. **Manual Revocation Only**: Must manually revoke and re-register if compromise suspected

## Goals

1. Implement automatic token rotation with configurable intervals
2. Support graceful rotation without agent disconnection
3. Maintain backward compatibility with existing agents
4. Provide manual rotation trigger via API

## Design Decisions

### 1. Rotation Strategy: Overlapping Tokens

Use a dual-token approach where new and old tokens overlap briefly during rotation:

```
Timeline:
─────────────────────────────────────────────────────►

Token A:  [==========active==========][grace]
Token B:                        [==========active==========]

           ▲                    ▲        ▲
           │                    │        │
     Token A issued      Token B issued  Token A invalidated
                        (rotation)       (after grace period)
```

**Rationale**: Prevents brief disconnections during rotation. Agent can continue using old token while transitioning to new one.

### 2. Token Storage: Two Hash Fields

Add `pending_token_hash` field alongside existing `token_hash`:

| Field | Purpose |
|-------|---------|
| `token_hash` | Current active token |
| `pending_token_hash` | New token during rotation (or NULL) |
| `token_issued_at` | When current token was issued |
| `token_expires_at` | When current token should be rotated |

**Rationale**: Simple schema change, maintains single source of truth per token state.

### 3. Rotation Trigger: Server-Initiated

Server initiates rotation via WebSocket message to agent:

```json
{
  "jsonrpc": "2.0",
  "method": "agent.rotate_token",
  "params": {
    "new_token": "base64-encoded-new-token",
    "grace_period_seconds": 300
  }
}
```

Agent responds with acknowledgment and starts using new token.

**Rationale**: Server controls timing, can coordinate across fleet.

### 4. Rotation Interval: Configurable

Default rotation interval: 7 days (configurable in settings).

| Setting | Default | Range |
|---------|---------|-------|
| `agent_token_rotation_days` | 7 | 1-365 |
| `agent_token_grace_period_minutes` | 5 | 1-60 |

### 5. Validation Changes

During rotation grace period, accept either token:

```python
def validate_token(self, token: str) -> Optional[Agent]:
    token_hash = self._hash_token(token)

    # Check current token
    agent = self._find_agent_by_token_hash(token_hash)
    if agent:
        return agent

    # Check pending token (during rotation)
    agent = self._find_agent_by_pending_token_hash(token_hash)
    if agent:
        # Complete rotation: promote pending to current
        self._complete_rotation(agent)
        return agent

    return None
```

## Component Changes

### Backend

| File | Changes |
|------|---------|
| `models/agent.py` | Add `pending_token_hash`, `token_issued_at`, `token_expires_at` |
| `init_db/schema_agents.py` | Add columns to agents table |
| `services/agent_service.py` | Add `rotate_token()`, update `validate_token()` |
| `services/agent_websocket.py` | Add rotation message handler |
| `tools/agent/` | Add `rotate_agent_token` tool |

### Agent

| File | Changes |
|------|---------|
| `src/auth.py` | Handle `agent.rotate_token` message, update state file |
| `src/lib/encryption.py` | No changes needed |

### Settings

| File | Changes |
|------|---------|
| `models/settings.py` | Add rotation settings |
| `services/settings_service.py` | Add defaults |

## Sequence Diagrams

### Automatic Rotation (Server-Initiated)

```
Backend                          Agent
   │                               │
   │  (token_expires_at reached)   │
   │                               │
   ├──agent.rotate_token──────────►│
   │  {new_token, grace_period}    │
   │                               │
   │                               ├──save new token
   │                               │  to state file
   │                               │
   │◄─────────acknowledgment───────┤
   │  {status: "rotated"}          │
   │                               │
   │  (agent uses new token        │
   │   for subsequent auth)        │
   │                               │
   │  (grace period expires)       │
   │                               │
   ├──invalidate old token         │
   │                               │
```

### Manual Rotation (Admin-Triggered)

```
Admin                Backend                Agent
  │                    │                      │
  ├──rotate_token─────►│                      │
  │  {agent_id}        │                      │
  │                    ├──agent.rotate_token─►│
  │                    │                      │
  │                    │◄──acknowledgment─────┤
  │                    │                      │
  │◄──success──────────┤                      │
  │                    │                      │
```

### Rotation Failure Handling

```
Backend                          Agent
   │                               │
   ├──agent.rotate_token──────────►│
   │                               │
   │  (agent offline or error)     │
   │                               │
   │◄──────(timeout/error)─────────┤
   │                               │
   ├──keep current token valid     │
   │  retry later                  │
   │                               │
```

## Error Handling

| Scenario | Handling |
|----------|----------|
| Agent offline during rotation | Keep current token, retry on reconnect |
| Agent fails to save new token | Respond with error, server retries |
| Network interruption | Grace period ensures old token works |
| Agent crashes after receiving | On restart, re-authenticate with either token |

## Migration Strategy

1. Add new columns with NULL defaults (backward compatible)
2. Existing agents continue working with current tokens
3. New rotation only affects agents that connect after deployment
4. No forced rotation of existing tokens

## Security Considerations

### Token Generation
- Continue using `secrets.token_urlsafe(32)` (256 bits entropy)
- New token generated server-side only

### Transport Security
- Rotation message sent over existing WSS connection
- Token transmitted encrypted (TLS)

### Grace Period Risks
- Brief window where two tokens valid
- Mitigated by short grace period (5 minutes default)
- Old token invalidated after grace period

### Audit Logging
- Log all rotation events
- Log failed rotation attempts
- Track token age in agent metrics

## Testing Strategy

### Unit Tests
- Token rotation service methods
- Dual-token validation logic
- Grace period expiration
- Settings validation

### Integration Tests
- Full rotation flow via WebSocket
- Agent state file updates
- Database schema migration

### E2E Tests
- Manual rotation via MCP tool
- Automatic rotation trigger
- Rotation failure and retry

## Success Metrics

| Metric | Target |
|--------|--------|
| Rotation success rate | > 99% |
| Average rotation time | < 5 seconds |
| Failed rotation retries | < 3 attempts |
| Grace period utilization | < 10% (most complete immediately) |

## Out of Scope

- Mutual TLS (mTLS) authentication
- Certificate-based agent identity
- Multi-token per agent (only dual during rotation)
- Token refresh without rotation
