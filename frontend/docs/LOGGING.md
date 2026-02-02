# Frontend Logging Documentation

This document describes the logging system used in the Tomo frontend application.

## Overview

The frontend uses a centralized logging system (`systemLogger`) that stores logs in memory and localStorage for persistence. Logs can be viewed in the Logs page of the application.

## Logger Categories

| Logger | Category | Purpose |
|--------|----------|---------|
| `securityLogger` | Security | Authentication, login/logout events |
| `deploymentLogger` | Deployment | App deployment lifecycle |
| `applicationLogger` | Application | Application catalog events |
| `marketplaceLogger` | Marketplace | Marketplace and repository operations |
| `settingsLogger` | Settings | Settings changes and MCP config |
| `mcpLogger` | MCP | MCP client connection and tool calls |

## Log Levels

- `info` - Normal operations and successful actions
- `warn` - Warning conditions, recoverable issues
- `error` - Error conditions, failures

---

## Security Events (`securityLogger`)

**File:** `src/hooks/useAuthActions.ts`

| Event | Level | Data |
|-------|-------|------|
| Login attempt started | info | `username`, `rememberMe` |
| Login successful | info | `username`, `sessionId`, `expiresAt` |
| Login failed | warn | `username`, `reason` |
| Logout initiated | info | `username`, `sessionId`, `reason` |
| Logout completed | info | `username`, `sessionId` |
| Logout error | error | `error` |

---

## Deployment Events (`deploymentLogger`)

**File:** `src/hooks/useDeploymentModal.ts`

| Event | Level | Data |
|-------|-------|------|
| Deployment modal opened | info | `appId`, `appName`, `image` |
| Pre-flight checks passed | info | `appId`, `appName`, `serverId`, `serverName`, `checksCount` |
| Pre-flight checks failed | warn | `appId`, `appName`, `serverId`, `serverName`, `failedChecks` |
| Deployment started | info | `appId`, `appName`, `serverId`, `serverName`, `config` |
| Deployment initiated successfully | info | `appId`, `appName`, `serverId`, `serverName`, `installationId` |
| Deployment completed successfully | info | `appId`, `appName`, `installationId` |
| Deployment failed | error | `appId`, `appName`, `serverId`, `serverName`, `error` |
| Deployment error | error | `appId`, `appName`, `serverId`, `serverName`, `error` |
| Installation failed during deployment | error | `appId`, `appName`, `installationId`, `error` |
| Deployment cleanup completed | info | `serverId`, `installationId` |
| Deployment cleanup failed | error | `serverId`, `installationId` |

---

## Application Events (`applicationLogger`)

**File:** `src/hooks/useApplications.ts`

| Event | Level | Data |
|-------|-------|------|
| Application catalog returned no results | info | `serverId`, `categoryFilter` |

---

## Marketplace Events (`marketplaceLogger`)

**Files:** `src/pages/marketplace/MarketplacePage.tsx`, `src/pages/marketplace/RepoManager.tsx`, `src/pages/settings/MarketplacesSettings.tsx`

| Event | Level | Data |
|-------|-------|------|
| Loading marketplace data | info | - |
| Loaded apps from marketplace | info | `count` |
| Opening deployment modal | info | `appName` |
| Marketplace load error | error | `error` |
| Loading repositories | info | - |
| Loaded repositories | info | `count` |
| Adding repository | info | `name` |
| Repository added | info | `name` |
| Syncing repository | info | `name` |
| Synced apps from repository | info | `appCount`, `name` |
| Sync failed | error | `name`, `error` |
| Removing repository | info | `name` |
| Repository removed | info | `name` |

---

## Settings Events (`settingsLogger`)

**Files:** `src/pages/settings/useSettingsState.tsx`, `src/pages/settings/useSettingsHandlers.tsx`

| Event | Level | Data |
|-------|-------|------|
| Loaded MCP config from localStorage | info | `hasUrl`, `hasToken` |
| Failed to load MCP config | warn | `error` |
| Using default MCP configuration | info | - |
| Persisting MCP config | info | `hasUrl`, `hasToken` |
| MCP config saved | info | - |
| Failed to save MCP config | warn | `error` |
| Saving MCP configuration | info | - |
| MCP config validation failed | warn | `error` |
| MCP configuration saved successfully | info | `url`, `hasToken` |
| Failed to parse MCP configuration | error | - |
| Initiating MCP connection | info | - |
| No MCP server URL configured | error | - |
| Connecting to MCP server | info | `url` |
| MCP connection established | info | - |
| MCP connection failed | error | `error` |
| Initiating MCP disconnection | info | - |
| MCP disconnected successfully | info | - |
| MCP disconnection failed | error | `error` |

---

## MCP Events (`mcpLogger`)

**Files:** `src/services/mcpClient.ts`, `src/services/settingsMcpClient.ts`, `src/services/settingsService.ts`, `src/hooks/useSettings.ts`

### Connection Events

| Event | Level | Data |
|-------|-------|------|
| MCP Client initialized | info | `baseUrl` |
| Attempting to connect | info | `url` |
| MCP session established | info | `sessionId` |
| MCP connection established | info | `sessionId`, `toolsCount` |
| MCP connection failed | error | `error` |
| Event source closed | info | - |
| MCP connection state reset | info | - |
| Disconnecting from MCP | info | `sessionId`, `hasEventSource` |
| MCP client disconnected | info | - |

### Tool Call Events

| Event | Level | Data |
|-------|-------|------|
| Auto-connecting for tool call | info | `tool` |
| Calling MCP tool | info | `tool`, `params` |
| MCP session invalid, reconnecting | warn | `tool`, `attempt` |
| Reconnect attempt failed | error | `tool`, `attempt`, `error` |
| MCP tool call failed | error | `tool`, `status`, `message` |
| MCP tool call successful | info | `tool`, `success` |
| MCP tool call exception | error | `tool`, `error` |

### Event Subscription

| Event | Level | Data |
|-------|-------|------|
| Subscribing to MCP events | info | `events`, `url` |
| Closing existing event source | info | - |
| Event source connection opened | info | - |
| Event source error | error | `error` |

### Settings MCP Client

| Event | Level | Data |
|-------|-------|------|
| Settings MCP Client initialized | info | - |
| Getting settings from backend | info | `userId` |
| Settings retrieved successfully | info | `userId` |
| Failed to get settings | error | `error` |
| Updating settings in backend | info | `userId`, `updates` |
| Settings updated successfully | info | `userId` |
| Failed to update settings | error | `error` |
| Validating settings | info | - |
| Settings validation completed | info | `isValid` |
| Settings validation failed | error | `error` |
| Getting settings schema | info | - |
| Settings schema retrieved | info | - |
| Resetting user settings | info | `userId` |
| User settings reset successfully | info | `userId` |
| Getting settings audit log | info | `userId`, `limit`, `offset` |
| Settings audit retrieved | info | `count` |
| Initializing settings database | info | - |
| Settings database initialized | info | - |
| Settings MCP Client not available | warn | - |

### Settings Service

| Event | Level | Data |
|-------|-------|------|
| Initializing settings service | info | `hasMcpClient` |
| Settings loaded from database | info | - |
| Failed to load from database | warn | `error` |
| Settings loaded from localStorage | info | - |
| Failed to initialize settings | error | `error` |
| Failed to save to database | warn | `error` |
| Failed to reset via database | warn | `error` |
| Settings validation failed | warn | `errors` |
| Failed to load from localStorage | error | `error` |
| MCP client updated | info | `hasMcpClient` |
| Settings listener error | error | `error` |

---

## Usage

### Importing Loggers

```typescript
import {
  securityLogger,
  deploymentLogger,
  applicationLogger,
  marketplaceLogger,
  settingsLogger,
  mcpLogger
} from '@/services/systemLogger'
```

### Logging Examples

```typescript
// Info level
deploymentLogger.info('Deployment started', {
  appId: 'plex',
  serverId: 'srv-1'
})

// Warning level
securityLogger.warn('Login failed', {
  username: 'admin',
  reason: 'Invalid credentials'
})

// Error level
mcpLogger.error('Connection failed', {
  url: 'http://localhost:3001',
  error: 'Connection refused'
})
```

### Viewing Logs

Logs are accessible in two ways:

1. **Logs Page** - Navigate to the Logs page in the application UI
2. **Browser Console** - All logs are also output to the browser console
3. **localStorage** - Logs persist in `tomo-system-logs` key

---

## Log Storage

- **Maximum logs:** 1000 entries (oldest are pruned)
- **Persistence:** localStorage (`tomo-system-logs`)
- **Format:** JSON array of `SystemLogEntry` objects

```typescript
interface SystemLogEntry {
  id: string           // Unique ID (log_<timestamp>_<random>)
  timestamp: Date      // When the event occurred
  level: 'info' | 'warn' | 'error'
  category: string     // Logger category name
  message: string      // Human-readable message
  data?: unknown       // Additional structured data
}
```
