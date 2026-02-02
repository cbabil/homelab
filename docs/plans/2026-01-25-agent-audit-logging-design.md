# Agent Audit Logging Design

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Add agent lifecycle events to the existing audit system so administrators can troubleshoot agent issues from the UI.

**Architecture:** Extend the existing `log_entries` table with `source='agent'` events. Add a new `get_agent_audit` backend tool. Display logs in Settings > Security and Dashboard > Agent Health.

---

## Events Captured

| Event | Level | When |
|-------|-------|------|
| `AGENT_INSTALLED` | INFO | After successful install |
| `AGENT_REGISTERED` | INFO | Agent completes registration |
| `AGENT_CONNECTED` | INFO | WebSocket connected |
| `AGENT_DISCONNECTED` | WARNING | WebSocket disconnected |
| `AGENT_REVOKED` | WARNING | Token revoked |
| `AGENT_UNINSTALLED` | INFO | Agent removed |
| `AGENT_UPDATED` | INFO | Version updated |
| `AGENT_ERROR` | ERROR | Any agent error |

---

## Data Model

Uses existing `log_entries` table with `source='agent'`:

```python
{
    "source": "agent",
    "level": "INFO" | "WARNING" | "ERROR",
    "message": "Agent connected",
    "tags": ["agent", "lifecycle"],
    "metadata": {
        "event_type": "AGENT_CONNECTED",
        "server_id": "srv-123",
        "server_name": "Docker Server",
        "agent_id": "agent-456",
        "success": True,
        "details": {}  # Event-specific data
    }
}
```

---

## Backend API

### New Tool: `get_agent_audit`

**Location:** `backend/src/tools/audit/tools.py`

```python
async def get_agent_audit(
    server_id: Optional[str] = None,
    event_type: Optional[str] = None,
    success_only: Optional[bool] = None,
    level: Optional[str] = None,  # INFO, WARNING, ERROR
    limit: int = 100,
    offset: int = 0,
) -> Dict[str, Any]
```

**Response:**
```python
{
    "success": True,
    "data": {
        "audit_entries": [
            {
                "id": "log-123",
                "timestamp": "2026-01-25T11:30:00Z",
                "level": "WARNING",
                "event_type": "AGENT_DISCONNECTED",
                "server_id": "srv-123",
                "server_name": "Docker Server",
                "agent_id": "agent-456",
                "success": False,
                "message": "Agent disconnected: connection timeout",
                "details": {"reason": "heartbeat_timeout"}
            }
        ],
        "total": 42
    }
}
```

---

## Logging Integration Points

| File | Event | Location |
|------|-------|----------|
| `agent_service.py` | `AGENT_INSTALLED` | End of `create_agent()` |
| `agent_service.py` | `AGENT_REGISTERED` | End of `register_agent()` |
| `agent_service.py` | `AGENT_REVOKED` | End of `revoke_agent()` |
| `agent_service.py` | `AGENT_UNINSTALLED` | End of `delete_agent()` |
| `agent_websocket.py` | `AGENT_CONNECTED` | On WebSocket open |
| `agent_websocket.py` | `AGENT_DISCONNECTED` | On WebSocket close |
| `agent_lifecycle.py` | `AGENT_UPDATED` | After version update |
| `agent_tools.py` | `AGENT_ERROR` | In exception handlers |

**Logging helper:**
```python
await log_event(
    "agent", "INFO",
    f"Agent registered for server {server_name}",
    ["agent", "lifecycle"],
    {
        "event_type": "AGENT_REGISTERED",
        "server_id": server_id,
        "server_name": server_name,
        "agent_id": agent.id,
        "success": True,
    }
)
```

---

## Frontend Components

### New Files

1. **`frontend/src/services/auditMcpClient.ts`** - Add `getAgentAudit()` method
2. **`frontend/src/components/audit/AgentAuditTable.tsx`** - Reusable table
3. **`frontend/src/hooks/useAgentAudit.ts`** - Data fetching with filters

### AgentAuditTable Component

- Columns: Timestamp, Server, Event, Level, Message
- Row click expands to show full details
- Color-coded level badges (green/yellow/red)

### Filter UI

```
[Server ▼] [Event Type ▼] [Level ▼] [Success ▼] [Date Range]
```

---

## UI Integration Points

| Location | Behavior |
|----------|----------|
| Settings > Security | Full table with all filters, pagination |
| Dashboard > Agent Health > "View all" | Compact table, pre-filtered to issues, 20 rows |

---

## Files to Create/Modify

### Backend
- `backend/src/tools/audit/tools.py` - Add `get_agent_audit` tool
- `backend/src/services/agent_service.py` - Add logging calls
- `backend/src/services/agent_websocket.py` - Add connect/disconnect logging
- `backend/src/services/agent_lifecycle.py` - Add update logging
- `backend/src/tools/agent/tools.py` - Add error logging

### Frontend
- `frontend/src/services/auditMcpClient.ts` - Add `getAgentAudit()` method
- `frontend/src/components/audit/AgentAuditTable.tsx` - New component
- `frontend/src/hooks/useAgentAudit.ts` - New hook
- `frontend/src/pages/settings/SecuritySettings.tsx` - Add agent audit section
- `frontend/src/pages/dashboard/DashboardStats.tsx` - Update "View all" link
- `frontend/src/i18n/locales/en.json` - Add translations
- `frontend/src/i18n/locales/fr.json` - Add translations
