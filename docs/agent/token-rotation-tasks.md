# Agent Token Rotation - Task List

**Status: COMPLETE ✅**

**Related Documents:**
- [Token Rotation Plan](token-rotation-plan.md)
- [Implementation Plan](token-rotation-implementation.md)
- [Authentication System](authentication.md)

---

## Priority Legend

| Priority | Meaning |
|----------|---------|
| P0 | **Critical** - Blocking, must complete first |
| P1 | **High** - Core implementation, required |
| P2 | **Medium** - Integration & tools |
| P3 | **Low** - Automation & polish |

---

## P0: Critical (Schema & Foundation)

These must be done first. Everything else depends on them.

### Database Schema
- [x] Add `pending_token_hash` column to agents table
- [x] Add `token_issued_at` column to agents table
- [x] Add `token_expires_at` column to agents table
- [x] Create migration function in `schema_agents.py`
- [x] Test migration on fresh database
- [x] Test migration on existing database with agents

### Agent Model
- [x] Add `pending_token_hash: Optional[str]` field to Agent model
- [x] Add `token_issued_at: Optional[datetime]` field to Agent model
- [x] Add `token_expires_at: Optional[datetime]` field to Agent model
- [x] Verify model serialization/deserialization works

### Settings Model
- [x] Add `agent_token_rotation_days` field (default: 7, range: 1-365)
- [x] Add `agent_token_grace_period_minutes` field (default: 5, range: 1-60)
- [x] Add settings to default seed data
- [x] Test settings validation

---

## P1: High (Core Rotation Logic)

These implement the core rotation mechanism.

### Agent Service - Rotation Methods
- [x] Implement `initiate_rotation(agent_id)` - generate pending token
- [x] Implement `complete_rotation(agent_id)` - promote pending to current
- [x] Implement `cancel_rotation(agent_id)` - clear pending on error
- [x] Implement `get_agents_needing_rotation(as_of)` - query expired tokens
- [x] Add `_find_agent_by_pending_token_hash(hash)` query method

### Agent Service - Validation Update
- [x] Modify `validate_token()` to check pending_token_hash
- [x] Auto-complete rotation when pending token used
- [x] Update `_update_last_seen()` call location

### Agent Service - Registration Update
- [x] Set `token_issued_at` in `complete_registration()`
- [x] Set `token_expires_at` in `complete_registration()`
- [x] Read rotation_days from settings

### Unit Tests - Agent Service
- [x] Test `initiate_rotation()` generates new token
- [x] Test `initiate_rotation()` returns None for missing agent
- [x] Test `complete_rotation()` promotes pending to current
- [x] Test `complete_rotation()` clears pending_token_hash
- [x] Test `complete_rotation()` sets new expiry
- [x] Test `cancel_rotation()` clears pending without affecting current
- [x] Test `validate_token()` accepts current token
- [x] Test `validate_token()` accepts pending token
- [x] Test `validate_token()` auto-completes rotation
- [x] Test `validate_token()` rejects invalid token
- [x] Test `get_agents_needing_rotation()` returns expired agents
- [x] Test `get_agents_needing_rotation()` excludes non-expired agents
- [x] Test `get_agents_needing_rotation()` excludes agents with pending rotation

---

## P2: Medium (WebSocket & Agent)

These implement the communication layer.

### WebSocket Service - Backend
- [x] Implement `send_rotation_request(agent_id, new_token, grace_seconds)`
- [x] Handle `agent.rotation_complete` method
- [x] Handle `agent.rotation_failed` method
- [x] Add timeout handling for rotation request
- [x] Log rotation events

### Agent - Rotation Handler
- [x] Implement `handle_rotation_request(params)` in agent_handlers.py
- [x] Save new token to state file
- [x] Return success/error status (agent sends via RPC response)
- [x] Handle save errors gracefully
- [x] Register handler in setup_agent_handlers()

### Unit Tests - WebSocket
- [x] Test `send_rotation_request()` sends correct JSON-RPC
- [x] Test timeout handling
- [x] Test `rotation_complete` handler
- [x] Test `rotation_failed` handler

### Unit Tests - Agent
- [x] Test `handle_rotation_request()` saves new token
- [x] Test `handle_rotation_request()` returns success status
- [x] Test `handle_rotation_request()` handles save error
- [x] Test rotation handler registration

### Integration Tests
- [x] Test full rotation flow via WebSocket mock
- [x] Test rotation with agent offline (timeout)
- [x] Test rotation recovery on agent reconnect

---

## P3: Low (Tools, Automation & Polish)

These add manual controls and automation.

### MCP Tool - Manual Rotation
- [x] Create `rotate_agent_token` tool
- [x] Validate agent exists
- [x] Validate agent is connected
- [x] Call rotation service methods
- [x] Return appropriate status messages
- [x] Register tool in `__init__.py`
- [x] Add tool to MCP server registration

### CLI Commands
- [x] Add `rotateAgentToken()` function to `cli/src/lib/agent.ts`
- [x] Create `Rotate.tsx` component in `cli/src/commands/agent/`
- [x] Register `agent rotate <server-id>` command in `tomo.tsx`
- [x] Add rotate subcommand to interactive mode CommandRouter
- [x] Update help text in CommandRouter

### MCP Tool Tests
- [x] Test tool with valid connected agent
- [x] Test tool with non-existent agent
- [x] Test tool with disconnected agent
- [x] Test tool WebSocket send failure

### Automatic Rotation Scheduler
- [x] Create `check_token_expiry()` coroutine
- [x] Create `start_rotation_scheduler()` background task
- [x] Integrate scheduler into server startup
- [x] Add graceful shutdown handling
- [x] Configure check interval (default: 1 hour)

### Scheduler Tests
- [x] Test `check_token_expiry()` identifies expired agents
- [x] Test `check_token_expiry()` triggers rotation
- [x] Test scheduler error handling
- [x] Test scheduler skips offline agents

### Documentation & Cleanup
- [x] Update authentication.md with rotation details
- [x] Update TODO.md to mark task complete
- [x] Add rotation troubleshooting to docs
- [x] Add rotation settings to ENV_REFERENCE.md

---

## Execution Order Summary

```
P0: Critical (15 tasks) ✅
│
├─► Database Schema (6 tasks) ✅
│   └─► Agent Model (4 tasks) ✅
│       └─► Settings Model (4 tasks) ✅
│
P1: High (25 tasks) ✅
│
├─► Rotation Methods (5 tasks) ✅
│   └─► Validation Update (3 tasks) ✅
│       └─► Registration Update (3 tasks) ✅
│           └─► Unit Tests (13 tasks) ✅
│
P2: Medium (21 tasks) ✅
│
├─► WebSocket Backend (5 tasks) ✅
│   └─► Agent Handler (5 tasks) ✅
│       └─► WebSocket Tests (4 tasks) ✅
│           └─► Agent Tests (4 tasks) ✅
│               └─► Integration Tests (3 tasks) ✅
│
P3: Low (23 tasks) ✅
│
├─► MCP Tool (7 tasks) ✅
│   └─► CLI Commands (5 tasks) ✅
│       └─► Tool Tests (4 tasks) ✅
│           └─► Scheduler (5 tasks) ✅
│               └─► Scheduler Tests (4 tasks) ✅
│                   └─► Documentation (4 tasks) ✅
```

---

## Progress Tracker

| Priority | Tasks | Completed | Status |
|----------|-------|-----------|--------|
| P0: Critical | 15 | 15 | ✅ Complete |
| P1: High | 25 | 25 | ✅ Complete |
| P2: Medium | 21 | 21 | ✅ Complete |
| P3: Low | 23 | 23 | ✅ Complete |
| **Total** | **84** | **84** | **100%** |

---

## Dependencies Graph

```
                    ┌─────────────────┐
                    │  Schema Update  │
                    │     (P0)        │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
       ┌───────────┐  ┌───────────┐  ┌───────────┐
       │   Agent   │  │ Settings  │  │  Service  │
       │   Model   │  │   Model   │  │  Methods  │
       │   (P0)    │  │   (P0)    │  │   (P1)    │
       └─────┬─────┘  └─────┬─────┘  └─────┬─────┘
             │              │              │
             └──────────────┼──────────────┘
                            │
              ┌─────────────┼─────────────┐
              │             │             │
              ▼             ▼             ▼
       ┌───────────┐ ┌───────────┐ ┌───────────┐
       │ WebSocket │ │   Agent   │ │    Unit   │
       │  Backend  │ │  Handler  │ │   Tests   │
       │   (P2)    │ │   (P2)    │ │   (P1)    │
       └─────┬─────┘ └─────┬─────┘ └───────────┘
             │             │
             └──────┬──────┘
                    │
              ┌─────▼─────┐
              │ Integration│
              │   Tests    │
              │   (P2)     │
              └─────┬─────┘
                    │
         ┌──────────┼──────────┐
         │          │          │
         ▼          ▼          ▼
  ┌───────────┐ ┌───────────┐ ┌───────────┐
  │ MCP Tool  │ │ Scheduler │ │   Docs    │
  │   (P3)    │ │   (P3)    │ │   (P3)    │
  └───────────┘ └───────────┘ └───────────┘
```

---

## Verification Checklist

### After P0 Complete ✅
- [x] `pytest backend/tests/unit/test_agent_service.py` passes
- [x] Database migration adds columns without error
- [x] Existing agents still work (backward compat)

### After P1 Complete ✅
- [x] All rotation unit tests pass
- [x] Token validation accepts both current and pending
- [x] New registrations have expiry set

### After P2 Complete ✅
- [x] WebSocket rotation flow works end-to-end
- [x] Agent saves new token correctly
- [x] Integration tests pass

### After P3 Complete ✅
- [x] MCP tool can trigger manual rotation
- [x] Scheduler auto-rotates expired tokens
- [x] Documentation is complete
