# Agent Audit Logging Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Add agent lifecycle events to the existing audit system so administrators can troubleshoot agent issues from the UI.

**Architecture:** Use existing `log_entries` table with `source='agent'`. Add `get_agent_audit` backend tool. Add logging calls to agent service methods. Display in Settings > Security and Dashboard.

**Tech Stack:** Python/FastMCP (backend), React/TypeScript/MUI (frontend)

---

## Tasks

### Task 1: Add `get_agent_audit` Backend Tool

**Files:**
- Modify: `backend/src/tools/audit/tools.py`

**Step 1: Add the `get_agent_audit` method to AuditTools class**

Add after `get_auth_audit` method (around line 218):

```python
    async def get_agent_audit(
        self,
        server_id: Optional[str] = None,
        event_type: Optional[str] = None,
        success_only: Optional[bool] = None,
        level: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        user_id: Optional[str] = None,
        ctx: Optional[Context] = None,
    ) -> Dict[str, Any]:
        """Get agent audit trail (admin only).

        Returns a list of agent lifecycle events including installs,
        connections, disconnections, and errors.

        Args:
            server_id: Filter by server ID
            event_type: Filter by event type (AGENT_INSTALLED, AGENT_CONNECTED, etc.)
            success_only: Filter by success status (True=success, False=failure, None=all)
            level: Filter by log level (INFO, WARNING, ERROR)
            limit: Maximum number of entries to return (default 100)
            offset: Number of entries to skip for pagination (default 0)
            user_id: User ID for authentication (from context or parameter)
            ctx: FastMCP context with authentication info

        Returns:
            Dict with success status and audit entries list
        """
        try:
            logger.info("Getting agent audit", server_id=server_id, event_type=event_type, limit=limit, offset=offset)

            authenticated_user = await self._verify_authentication(ctx)
            active_user_id = authenticated_user or user_id
            if not active_user_id:
                return {
                    "success": False,
                    "message": "Authentication required",
                    "error": "AUTHENTICATION_REQUIRED",
                }

            # Check admin access via settings service
            is_admin = await self._settings_service.verify_admin_access(active_user_id)
            if not is_admin:
                await log_event(
                    "aud", "WARNING",
                    f"Agent audit access denied: {active_user_id}",
                    AUDIT_TAGS,
                    {"user_id": active_user_id, "error": "ADMIN_REQUIRED"}
                )
                return {
                    "success": False,
                    "message": "Admin privileges required to access agent audit",
                    "error": "ADMIN_REQUIRED",
                }

            # Query log_entries with source='agent' for agent events
            log_filter = LogFilter(source="agent", limit=limit, offset=offset)
            logs = await self._log_service.get_logs(log_filter)

            # Transform and filter logs
            audit_entries: List[Dict[str, Any]] = []
            for log in logs:
                metadata = log.metadata or {}

                # Apply filters
                if server_id and metadata.get("server_id") != server_id:
                    continue
                if event_type and metadata.get("event_type") != event_type:
                    continue
                if success_only is not None and metadata.get("success") != success_only:
                    continue
                if level and log.level != level:
                    continue

                audit_entries.append({
                    "id": log.id,
                    "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                    "level": log.level,
                    "event_type": metadata.get("event_type"),
                    "server_id": metadata.get("server_id"),
                    "server_name": metadata.get("server_name"),
                    "agent_id": metadata.get("agent_id"),
                    "success": metadata.get("success"),
                    "message": log.message,
                    "details": metadata.get("details", {}),
                    "tags": log.tags,
                })

            await log_event(
                "aud", "INFO",
                f"Agent audit accessed by: {active_user_id}",
                AUDIT_TAGS,
                {"user_id": active_user_id, "server_id": server_id, "event_type": event_type, "limit": limit, "offset": offset, "count": len(audit_entries)}
            )

            return {
                "success": True,
                "message": f"Retrieved {len(audit_entries)} agent audit entries",
                "data": {"audit_entries": audit_entries, "total": len(audit_entries)},
            }
        except Exception as exc:
            logger.error("Failed to get agent audit", error=str(exc))
            await log_event("audit", "ERROR", "Agent audit error", AUDIT_TAGS, {"error": str(exc)})
            return {
                "success": False,
                "message": f"Failed to get agent audit: {exc}",
                "error": "AUDIT_ERROR",
            }
```

**Step 2: Run backend linting**

```bash
cd backend && make lint
```

**Step 3: Commit**

```bash
git add backend/src/tools/audit/tools.py
git commit -m "feat(audit): add get_agent_audit tool"
```

---

### Task 2: Add Agent Event Logging Helper

**Files:**
- Modify: `backend/src/services/agent_service.py`

**Step 1: Add import for log_event at top of file**

After line 12 (after structlog import), add:

```python
from tools.common import log_event
```

**Step 2: Add helper method to AgentService class**

Add after `_hash_token` method (around line 63):

```python
    async def _log_agent_event(
        self,
        event_type: str,
        level: str,
        message: str,
        server_id: str,
        server_name: str = "",
        agent_id: str = "",
        success: bool = True,
        details: dict = None,
    ) -> None:
        """Log an agent lifecycle event to the audit system.

        Args:
            event_type: Type of event (AGENT_INSTALLED, AGENT_CONNECTED, etc.)
            level: Log level (INFO, WARNING, ERROR)
            message: Human-readable message
            server_id: Server identifier
            server_name: Server display name
            agent_id: Agent identifier (if available)
            success: Whether the operation succeeded
            details: Additional event-specific details
        """
        await log_event(
            "agent",
            level,
            message,
            ["agent", "lifecycle"],
            {
                "event_type": event_type,
                "server_id": server_id,
                "server_name": server_name,
                "agent_id": agent_id,
                "success": success,
                "details": details or {},
            },
        )
```

**Step 3: Commit**

```bash
git add backend/src/services/agent_service.py
git commit -m "feat(agent): add agent event logging helper"
```

---

### Task 3: Add Logging to Agent Service Methods

**Files:**
- Modify: `backend/src/services/agent_service.py`

**Step 1: Add logging to `create_agent` method**

Find the `create_agent` method. At the end, before the return statement, add:

```python
        # Log the agent creation event
        await self._log_agent_event(
            event_type="AGENT_INSTALLED",
            level="INFO",
            message=f"Agent installed for server {server_id}",
            server_id=server_id,
            agent_id=agent.id,
            success=True,
        )
```

**Step 2: Add logging to `register_agent` method**

Find the `register_agent` method. After successful registration (where agent status is updated), add:

```python
        # Log successful registration
        await self._log_agent_event(
            event_type="AGENT_REGISTERED",
            level="INFO",
            message=f"Agent registered for server {agent.server_id}",
            server_id=agent.server_id,
            agent_id=agent.id,
            success=True,
            details={"version": agent.version},
        )
```

Also add error logging in the failure cases:

```python
        # Log failed registration (add in the failure path)
        await self._log_agent_event(
            event_type="AGENT_ERROR",
            level="WARNING",
            message="Agent registration failed: invalid code",
            server_id="unknown",
            success=False,
            details={"reason": "invalid_registration_code"},
        )
```

**Step 3: Add logging to `revoke_agent` method**

Find the `revoke_agent` method. After successful revocation, add:

```python
        await self._log_agent_event(
            event_type="AGENT_REVOKED",
            level="WARNING",
            message=f"Agent token revoked for agent {agent_id}",
            server_id=agent.server_id,
            agent_id=agent_id,
            success=True,
        )
```

**Step 4: Add logging to `delete_agent` method**

Find the `delete_agent` method. After successful deletion, add:

```python
        await self._log_agent_event(
            event_type="AGENT_UNINSTALLED",
            level="INFO",
            message=f"Agent uninstalled from server {agent.server_id}",
            server_id=agent.server_id,
            agent_id=agent_id,
            success=True,
        )
```

**Step 5: Commit**

```bash
git add backend/src/services/agent_service.py
git commit -m "feat(agent): add audit logging to agent service methods"
```

---

### Task 4: Add Logging to Agent WebSocket Handler

**Files:**
- Modify: `backend/src/services/agent_websocket.py`

**Step 1: Add import for log_event**

At top of file, add:

```python
from tools.common import log_event
```

**Step 2: Add logging for successful connection**

In the `_handle_authentication` method, after successful authentication, add:

```python
        await log_event(
            "agent",
            "INFO",
            f"Agent connected: {agent.id}",
            ["agent", "lifecycle"],
            {
                "event_type": "AGENT_CONNECTED",
                "server_id": agent.server_id,
                "agent_id": agent.id,
                "success": True,
            },
        )
```

**Step 3: Add logging for disconnection**

In the `handle_connection` method, in the finally block or where the connection closes, add:

```python
        await log_event(
            "agent",
            "WARNING",
            f"Agent disconnected: {agent_id}",
            ["agent", "lifecycle"],
            {
                "event_type": "AGENT_DISCONNECTED",
                "server_id": server_id,
                "agent_id": agent_id,
                "success": True,
                "details": {"reason": "connection_closed"},
            },
        )
```

**Step 4: Commit**

```bash
git add backend/src/services/agent_websocket.py
git commit -m "feat(agent): add audit logging to websocket handler"
```

---

### Task 5: Add Logging to Agent Lifecycle Manager

**Files:**
- Modify: `backend/src/services/agent_lifecycle.py`

**Step 1: Add import for log_event**

At top of file, add:

```python
from tools.common import log_event
```

**Step 2: Add logging to `trigger_update` method**

After successful update trigger, add:

```python
        await log_event(
            "agent",
            "INFO",
            f"Agent update triggered: {agent_id}",
            ["agent", "lifecycle"],
            {
                "event_type": "AGENT_UPDATED",
                "agent_id": agent_id,
                "server_id": "",  # Get from agent if available
                "success": True,
            },
        )
```

**Step 3: Commit**

```bash
git add backend/src/services/agent_lifecycle.py
git commit -m "feat(agent): add audit logging to lifecycle manager"
```

---

### Task 6: Add Frontend Types and API Method

**Files:**
- Modify: `frontend/src/services/auditMcpClient.ts`

**Step 1: Add AgentAuditEntry type**

After `AuthAuditEntry` interface (around line 40), add:

```typescript
// Agent audit entry type
export interface AgentAuditEntry {
  id: string
  timestamp: string
  level: string
  event_type: string
  server_id: string
  server_name?: string
  agent_id: string
  success: boolean
  message: string
  details?: Record<string, unknown>
  tags: string[]
}

// Agent audit filter options
export interface AgentAuditFilters {
  serverId?: string
  eventType?: string
  successOnly?: boolean
  level?: string
  limit?: number
  offset?: number
}
```

**Step 2: Add getAgentAudit method to AuditMcpClient class**

After `getAuthAudit` method, add:

```typescript
  /**
   * Get agent audit log (admin only)
   *
   * Returns agent lifecycle events including installs, connections,
   * disconnections, and errors.
   */
  async getAgentAudit(filters: AgentAuditFilters = {}): Promise<AgentAuditEntry[]> {
    try {
      mcpLogger.info('Getting agent audit log', filters)

      const response = await this.mcpClient.callTool<{
        audit_entries: AgentAuditEntry[]
        total: number
      }>('get_agent_audit', {
        server_id: filters.serverId,
        event_type: filters.eventType,
        success_only: filters.successOnly,
        level: filters.level,
        limit: filters.limit ?? 50,
        offset: filters.offset ?? 0
      })

      if (!response.success) {
        mcpLogger.error('Failed to get agent audit', { error: response.error })
        return []
      }

      const entries = response.data?.audit_entries || []
      mcpLogger.info('Agent audit retrieved successfully', { count: entries.length })
      return entries
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      mcpLogger.error('Agent audit retrieval failed', { error: errorMessage })
      return []
    }
  }
```

**Step 3: Run frontend linting**

```bash
cd frontend && yarn lint
```

**Step 4: Commit**

```bash
git add frontend/src/services/auditMcpClient.ts
git commit -m "feat(audit): add agent audit API method"
```

---

### Task 7: Create useAgentAudit Hook

**Files:**
- Create: `frontend/src/hooks/useAgentAudit.ts`

**Step 1: Create the hook file**

```typescript
/**
 * useAgentAudit Hook
 *
 * Fetches and manages agent audit log data with filtering support.
 */

import { useState, useEffect, useCallback } from 'react'
import { useAuditMcpClient, AgentAuditEntry, AgentAuditFilters } from '@/services/auditMcpClient'

export interface UseAgentAuditReturn {
  entries: AgentAuditEntry[]
  isLoading: boolean
  error: string | null
  filters: AgentAuditFilters
  setFilters: (filters: AgentAuditFilters) => void
  refresh: () => Promise<void>
}

export function useAgentAudit(initialFilters: AgentAuditFilters = {}): UseAgentAuditReturn {
  const auditClient = useAuditMcpClient()
  const [entries, setEntries] = useState<AgentAuditEntry[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filters, setFilters] = useState<AgentAuditFilters>(initialFilters)

  const fetchAudit = useCallback(async () => {
    if (!auditClient) {
      setError('Audit client not available')
      setIsLoading(false)
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const data = await auditClient.getAgentAudit(filters)
      setEntries(data)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch agent audit'
      setError(message)
    } finally {
      setIsLoading(false)
    }
  }, [auditClient, filters])

  useEffect(() => {
    fetchAudit()
  }, [fetchAudit])

  return {
    entries,
    isLoading,
    error,
    filters,
    setFilters,
    refresh: fetchAudit
  }
}
```

**Step 2: Commit**

```bash
git add frontend/src/hooks/useAgentAudit.ts
git commit -m "feat(audit): add useAgentAudit hook"
```

---

### Task 8: Create AgentAuditTable Component

**Files:**
- Create: `frontend/src/components/audit/AgentAuditTable.tsx`

**Step 1: Create the component**

```typescript
/**
 * AgentAuditTable Component
 *
 * Displays agent audit log entries in a table with filtering and expandable rows.
 */

import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Collapse,
  Box,
  Typography,
  Stack,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent
} from '@mui/material'
import { ChevronDown, ChevronRight, RefreshCw } from 'lucide-react'
import { AgentAuditEntry, AgentAuditFilters } from '@/services/auditMcpClient'
import { Button } from '@/components/ui/Button'

interface AgentAuditTableProps {
  entries: AgentAuditEntry[]
  isLoading: boolean
  error: string | null
  filters: AgentAuditFilters
  onFilterChange: (filters: AgentAuditFilters) => void
  onRefresh: () => void
  compact?: boolean
  servers?: Array<{ id: string; name: string }>
}

const EVENT_TYPES = [
  'AGENT_INSTALLED',
  'AGENT_REGISTERED',
  'AGENT_CONNECTED',
  'AGENT_DISCONNECTED',
  'AGENT_REVOKED',
  'AGENT_UNINSTALLED',
  'AGENT_UPDATED',
  'AGENT_ERROR'
]

const LEVELS = ['INFO', 'WARNING', 'ERROR']

function getLevelColor(level: string): 'success' | 'warning' | 'error' | 'default' {
  switch (level) {
    case 'INFO':
      return 'success'
    case 'WARNING':
      return 'warning'
    case 'ERROR':
      return 'error'
    default:
      return 'default'
  }
}

function formatTimestamp(timestamp: string): string {
  return new Date(timestamp).toLocaleString()
}

interface ExpandableRowProps {
  entry: AgentAuditEntry
}

function ExpandableRow({ entry }: ExpandableRowProps) {
  const [open, setOpen] = useState(false)

  return (
    <>
      <TableRow
        hover
        onClick={() => setOpen(!open)}
        sx={{ cursor: 'pointer', '& > *': { borderBottom: 'unset' } }}
      >
        <TableCell padding="checkbox">
          <IconButton size="small">
            {open ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
          </IconButton>
        </TableCell>
        <TableCell>{formatTimestamp(entry.timestamp)}</TableCell>
        <TableCell>{entry.server_name || entry.server_id}</TableCell>
        <TableCell>
          <Chip
            label={entry.event_type.replace('AGENT_', '')}
            size="small"
            variant="outlined"
          />
        </TableCell>
        <TableCell>
          <Chip
            label={entry.level}
            size="small"
            color={getLevelColor(entry.level)}
          />
        </TableCell>
        <TableCell>{entry.message}</TableCell>
      </TableRow>
      <TableRow>
        <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={6}>
          <Collapse in={open} timeout="auto" unmountOnExit>
            <Box sx={{ margin: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Details
              </Typography>
              <Stack spacing={1}>
                <Typography variant="body2">
                  <strong>Agent ID:</strong> {entry.agent_id || 'N/A'}
                </Typography>
                <Typography variant="body2">
                  <strong>Server ID:</strong> {entry.server_id}
                </Typography>
                <Typography variant="body2">
                  <strong>Success:</strong> {entry.success ? 'Yes' : 'No'}
                </Typography>
                {entry.details && Object.keys(entry.details).length > 0 && (
                  <Typography variant="body2" component="pre" sx={{ fontSize: '0.75rem' }}>
                    {JSON.stringify(entry.details, null, 2)}
                  </Typography>
                )}
              </Stack>
            </Box>
          </Collapse>
        </TableCell>
      </TableRow>
    </>
  )
}

export function AgentAuditTable({
  entries,
  isLoading,
  error,
  filters,
  onFilterChange,
  onRefresh,
  compact = false,
  servers = []
}: AgentAuditTableProps) {
  const { t } = useTranslation()

  const handleServerChange = (event: SelectChangeEvent) => {
    onFilterChange({ ...filters, serverId: event.target.value || undefined })
  }

  const handleEventTypeChange = (event: SelectChangeEvent) => {
    onFilterChange({ ...filters, eventType: event.target.value || undefined })
  }

  const handleLevelChange = (event: SelectChangeEvent) => {
    onFilterChange({ ...filters, level: event.target.value || undefined })
  }

  const handleSuccessChange = (event: SelectChangeEvent) => {
    const value = event.target.value
    onFilterChange({
      ...filters,
      successOnly: value === '' ? undefined : value === 'true'
    })
  }

  if (error) {
    return (
      <Box sx={{ p: 2, textAlign: 'center' }}>
        <Typography color="error">{error}</Typography>
        <Button variant="ghost" size="sm" onClick={onRefresh} sx={{ mt: 1 }}>
          {t('common.retry')}
        </Button>
      </Box>
    )
  }

  return (
    <Stack spacing={2}>
      {!compact && (
        <Stack direction="row" spacing={2} flexWrap="wrap" alignItems="center">
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>{t('audit.server')}</InputLabel>
            <Select
              value={filters.serverId || ''}
              label={t('audit.server')}
              onChange={handleServerChange}
            >
              <MenuItem value="">{t('common.all')}</MenuItem>
              {servers.map((server) => (
                <MenuItem key={server.id} value={server.id}>
                  {server.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>{t('audit.eventType')}</InputLabel>
            <Select
              value={filters.eventType || ''}
              label={t('audit.eventType')}
              onChange={handleEventTypeChange}
            >
              <MenuItem value="">{t('common.all')}</MenuItem>
              {EVENT_TYPES.map((type) => (
                <MenuItem key={type} value={type}>
                  {type.replace('AGENT_', '')}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>{t('audit.level')}</InputLabel>
            <Select
              value={filters.level || ''}
              label={t('audit.level')}
              onChange={handleLevelChange}
            >
              <MenuItem value="">{t('common.all')}</MenuItem>
              {LEVELS.map((level) => (
                <MenuItem key={level} value={level}>
                  {level}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>{t('audit.status')}</InputLabel>
            <Select
              value={filters.successOnly === undefined ? '' : String(filters.successOnly)}
              label={t('audit.status')}
              onChange={handleSuccessChange}
            >
              <MenuItem value="">{t('common.all')}</MenuItem>
              <MenuItem value="true">{t('common.success')}</MenuItem>
              <MenuItem value="false">{t('common.failure')}</MenuItem>
            </Select>
          </FormControl>

          <Button variant="ghost" size="sm" onClick={onRefresh}>
            <RefreshCw size={16} />
          </Button>
        </Stack>
      )}

      <TableContainer component={Paper} variant="outlined">
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell padding="checkbox" />
              <TableCell>{t('audit.timestamp')}</TableCell>
              <TableCell>{t('audit.server')}</TableCell>
              <TableCell>{t('audit.event')}</TableCell>
              <TableCell>{t('audit.level')}</TableCell>
              <TableCell>{t('audit.message')}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={6} align="center" sx={{ py: 4 }}>
                  <CircularProgress size={24} />
                </TableCell>
              </TableRow>
            ) : entries.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} align="center" sx={{ py: 4 }}>
                  <Typography color="text.secondary">
                    {t('audit.noEntries')}
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              entries.map((entry) => (
                <ExpandableRow key={entry.id} entry={entry} />
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Stack>
  )
}
```

**Step 2: Create index file**

Create `frontend/src/components/audit/index.ts`:

```typescript
export { AgentAuditTable } from './AgentAuditTable'
```

**Step 3: Commit**

```bash
git add frontend/src/components/audit/
git commit -m "feat(audit): add AgentAuditTable component"
```

---

### Task 9: Add i18n Translations

**Files:**
- Modify: `frontend/src/i18n/locales/en.json`
- Modify: `frontend/src/i18n/locales/fr.json`

**Step 1: Add English translations**

Add under a new `"audit"` key:

```json
"audit": {
  "agentActivity": "Agent Activity",
  "agentActivityDescription": "Agent lifecycle events and connection history",
  "server": "Server",
  "eventType": "Event Type",
  "level": "Level",
  "status": "Status",
  "timestamp": "Timestamp",
  "event": "Event",
  "message": "Message",
  "noEntries": "No audit entries found",
  "viewAll": "View all agent activity"
}
```

**Step 2: Add French translations**

```json
"audit": {
  "agentActivity": "Activité des agents",
  "agentActivityDescription": "Événements du cycle de vie des agents et historique des connexions",
  "server": "Serveur",
  "eventType": "Type d'événement",
  "level": "Niveau",
  "status": "Statut",
  "timestamp": "Horodatage",
  "event": "Événement",
  "message": "Message",
  "noEntries": "Aucune entrée d'audit trouvée",
  "viewAll": "Voir toute l'activité des agents"
}
```

**Step 3: Commit**

```bash
git add frontend/src/i18n/locales/
git commit -m "feat(i18n): add agent audit translations"
```

---

### Task 10: Integrate into SecuritySettings Page

**Files:**
- Modify: `frontend/src/pages/settings/SecuritySettings.tsx`

**Step 1: Add imports**

```typescript
import { AgentAuditTable } from '@/components/audit'
import { useAgentAudit } from '@/hooks/useAgentAudit'
import { useServers } from '@/hooks/useServers'
```

**Step 2: Add hook calls inside the component**

```typescript
const { entries: agentAuditEntries, isLoading: auditLoading, error: auditError, filters: auditFilters, setFilters: setAuditFilters, refresh: refreshAudit } = useAgentAudit()
const { servers } = useServers()
```

**Step 3: Add Agent Activity section at the end of the component JSX**

Before the closing `</Box>` or similar, add:

```typescript
<Divider sx={{ my: 3 }} />

<Typography variant="h6" gutterBottom>
  {t('audit.agentActivity')}
</Typography>
<Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
  {t('audit.agentActivityDescription')}
</Typography>

<AgentAuditTable
  entries={agentAuditEntries}
  isLoading={auditLoading}
  error={auditError}
  filters={auditFilters}
  onFilterChange={setAuditFilters}
  onRefresh={refreshAudit}
  servers={servers.map(s => ({ id: s.id, name: s.name }))}
/>
```

**Step 4: Run frontend type check**

```bash
cd frontend && yarn typecheck
```

**Step 5: Commit**

```bash
git add frontend/src/pages/settings/SecuritySettings.tsx
git commit -m "feat(settings): add agent audit section to security settings"
```

---

### Task 11: Update Dashboard Agent Health Card

**Files:**
- Modify: `frontend/src/pages/dashboard/DashboardStats.tsx`

**Step 1: Update the "View all" link for Agent Health**

Find the Agent Health StatCard and update the links to navigate to agent audit:

```typescript
links={agentCounts.total > 0 ? [
  { label: t('audit.viewAll'), onClick: () => navigate('/settings?tab=security#agent-audit') }
] : undefined}
```

**Step 2: Commit**

```bash
git add frontend/src/pages/dashboard/DashboardStats.tsx
git commit -m "feat(dashboard): link agent health to audit view"
```

---

### Task 12: Write Unit Tests for useAgentAudit Hook

**Files:**
- Create: `frontend/src/hooks/__tests__/useAgentAudit.test.ts`

**Step 1: Create the test file**

```typescript
import { renderHook, waitFor, act } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useAgentAudit } from '../useAgentAudit'

// Mock the audit client
const mockGetAgentAudit = vi.fn()

vi.mock('@/services/auditMcpClient', () => ({
  useAuditMcpClient: () => ({
    getAgentAudit: mockGetAgentAudit
  })
}))

describe('useAgentAudit', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should fetch audit entries on mount', async () => {
    const mockEntries = [
      {
        id: 'agent-123',
        timestamp: '2026-01-25T10:00:00Z',
        level: 'INFO',
        event_type: 'AGENT_CONNECTED',
        server_id: 'srv-1',
        agent_id: 'agent-1',
        success: true,
        message: 'Agent connected',
        tags: ['agent']
      }
    ]
    mockGetAgentAudit.mockResolvedValue(mockEntries)

    const { result } = renderHook(() => useAgentAudit())

    expect(result.current.isLoading).toBe(true)

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.entries).toEqual(mockEntries)
    expect(result.current.error).toBeNull()
  })

  it('should handle errors', async () => {
    mockGetAgentAudit.mockRejectedValue(new Error('Network error'))

    const { result } = renderHook(() => useAgentAudit())

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.error).toBe('Network error')
    expect(result.current.entries).toEqual([])
  })

  it('should refetch when filters change', async () => {
    mockGetAgentAudit.mockResolvedValue([])

    const { result } = renderHook(() => useAgentAudit())

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    act(() => {
      result.current.setFilters({ serverId: 'srv-1' })
    })

    await waitFor(() => {
      expect(mockGetAgentAudit).toHaveBeenCalledWith({ serverId: 'srv-1' })
    })
  })
})
```

**Step 2: Run tests**

```bash
cd frontend && yarn test src/hooks/__tests__/useAgentAudit.test.ts
```

**Step 3: Commit**

```bash
git add frontend/src/hooks/__tests__/useAgentAudit.test.ts
git commit -m "test(audit): add useAgentAudit hook tests"
```

---

## Verification

After completing all tasks:

1. **Backend verification:**
   ```bash
   cd backend && make lint && make test
   ```

2. **Frontend verification:**
   ```bash
   cd frontend && yarn lint && yarn typecheck && yarn test
   ```

3. **Manual testing:**
   - Start the backend and frontend
   - Trigger agent events (install agent, connect/disconnect)
   - Go to Settings > Security
   - Verify Agent Activity section shows events
   - Test filters work correctly
   - Click Dashboard > Agent Health > View all
   - Verify it navigates to audit view

---

## Files Summary

| File | Action |
|------|--------|
| `backend/src/tools/audit/tools.py` | Modify - add get_agent_audit |
| `backend/src/services/agent_service.py` | Modify - add logging helper and calls |
| `backend/src/services/agent_websocket.py` | Modify - add connect/disconnect logging |
| `backend/src/services/agent_lifecycle.py` | Modify - add update logging |
| `frontend/src/services/auditMcpClient.ts` | Modify - add types and API method |
| `frontend/src/hooks/useAgentAudit.ts` | Create |
| `frontend/src/components/audit/AgentAuditTable.tsx` | Create |
| `frontend/src/components/audit/index.ts` | Create |
| `frontend/src/i18n/locales/en.json` | Modify - add translations |
| `frontend/src/i18n/locales/fr.json` | Modify - add translations |
| `frontend/src/pages/settings/SecuritySettings.tsx` | Modify - add audit section |
| `frontend/src/pages/dashboard/DashboardStats.tsx` | Modify - update link |
| `frontend/src/hooks/__tests__/useAgentAudit.test.ts` | Create |
