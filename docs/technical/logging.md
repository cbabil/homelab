# Logging Specification

## Overview

The Tomo application uses a centralized logging system to track system events, user actions, and errors. Logs are stored in localStorage and displayed in the Logs page.

## Log Structure

```typescript
interface SystemLogEntry {
  id: string          // Unique identifier
  timestamp: Date     // When the event occurred
  level: LogLevel     // Severity level
  category: string    // Source category
  message: string     // Human-readable description
  data?: any          // Additional context (optional)
}
```

## Log Levels

| Level | Purpose | Example |
|-------|---------|---------|
| `success` | Successful operations | "MCP connection established" |
| `info` | General information | "Loading repositories" |
| `warn` | Warnings (non-fatal issues) | "Failed to load from database, falling back to localStorage" |
| `error` | Errors requiring attention | "MCP connection failed" |

## Categories

### MCP (Protocol)
Logs related to Model Context Protocol communication.

| Event | Level | Message | Data |
|-------|-------|---------|------|
| Client initialized | info | "MCP Client initialized" | `{ baseUrl }` |
| Connection attempt | info | "Attempting to connect to MCP server" | `{ url }` |
| Session established | info | "MCP session established" | `{ sessionId }` |
| Connection success | success | "MCP connection established" | `{ sessionId, url }` |
| Connection failed | error | "MCP connection failed" | `error` |
| Disconnected | info | "MCP client disconnected" | - |
| Tool call started | info | "Calling MCP tool" | `{ tool, params }` |
| Tool call success | success | "Tool call completed: {name}" | `{ tool, resultType, hasStructuredContent }` |
| Tool call failed | error | "MCP tool call failed" | `{ tool, error, code }` |
| Session invalid | warn | "MCP session invalid, attempting reconnect" | `{ tool, status }` |
| Reconnect failed | error | "Reconnect attempt failed" | `{ tool, error }` |

### Application
Logs related to the application catalog.

| Event | Level | Message | Data |
|-------|-------|---------|------|
| Apps loaded | success | "Loaded {count} applications" | `{ source, total }` |
| No results | info | "Application catalog returned no results" | `{ source, filters }` |
| App added | success | "Added application: {name}" | `{ appId }` |
| Add failed | error | "Failed to add application" | `{ error, appData }` |
| Apps removed | success | "Removed {count} application(s)" | `{ removed, skipped }` |
| Remove failed | error | "Failed to remove applications" | `{ error, ids }` |
| App uninstalled | success | "Uninstalled application: {appId}" | `{ appId, serverId }` |
| Uninstall failed | error | "Failed to uninstall application" | `{ error, appId, serverId }` |
| Deploy warning | warn | "Deploy attempted with no servers configured" | `{ appId, appName }` |

### Settings
Logs related to configuration and settings.

| Event | Level | Message | Data |
|-------|-------|---------|------|
| Config loaded | info | "Loaded MCP config from localStorage" | `{ hasPort, hasUrl }` |
| Config saved | info | "MCP configuration saved successfully" | `{ port, url }` |
| Load failed | warn | "Failed to load MCP config from localStorage" | `error` |
| Save failed | warn | "Failed to save MCP config to localStorage" | `error` |
| Validation failed | warn | "MCP config validation failed" | `{ error }` |
| Parse error | error | "Failed to parse MCP configuration JSON" | - |

### Security
Logs related to authentication and authorization.

| Event | Level | Message | Data |
|-------|-------|---------|------|
| Login started | info | "Login attempt started" | `{ username }` |
| Login success | info | "Login successful" | `{ username, userId }` |
| Login failed | warn | "Login failed" | `{ username, reason }` |
| Logout started | info | "Logout initiated" | `{ userId }` |
| Logout complete | info | "Logout completed" | `{ userId }` |
| Logout error | error | "Logout error" | `{ error }` |

### Marketplace
Logs related to the app marketplace.

| Event | Level | Message | Data |
|-------|-------|---------|------|
| Loading repos | info | "Loading repositories" | - |
| Repos loaded | info | "Loaded {count} repositories" | - |
| Repo load failed | error | Error message | - |
| Adding repo | info | "Adding repository: {name}" | - |
| Repo added | info | "Repository added: {name}" | - |
| Syncing repo | info | "Syncing repository: {name}" | - |
| Sync success | info | "Synced {count} apps from {name}" | - |
| Sync failed | error | "Sync failed for {name}: {error}" | - |
| Removing repo | info | "Removing repository: {name}" | - |
| Repo removed | info | "Repository removed: {name}" | - |
| Loading apps | info | "Loading marketplace data" | - |
| Apps loaded | info | "Loaded {count} apps from marketplace" | - |
| Load failed | error | Error message | - |
| Importing app | info | "Importing app: {name}" | - |

### Server (Planned)
Logs related to server management.

| Event | Level | Message | Data |
|-------|-------|---------|------|
| Server added | success | "Server added: {name}" | `{ serverId, host }` |
| Server removed | info | "Server removed: {name}" | `{ serverId }` |
| Connection test | info | "Testing server connection" | `{ serverId }` |
| Test success | success | "Server connection successful" | `{ serverId, latency }` |
| Test failed | error | "Server connection failed" | `{ serverId, error }` |

### Network (Planned)
Logs related to network operations.

| Event | Level | Message | Data |
|-------|-------|---------|------|
| Request started | info | "HTTP request: {method} {url}" | `{ method, url }` |
| Request success | success | "HTTP response: {status}" | `{ status, duration }` |
| Request failed | error | "HTTP request failed" | `{ error, url }` |
| Timeout | warn | "Request timeout" | `{ url, timeout }` |

## Storage

- **Location**: `localStorage` with key `tomo-system-logs`
- **Max entries**: 1000 (oldest entries are removed when limit exceeded)
- **Persistence**: Logs persist across browser sessions

## Usage Examples

```typescript
import { mcpLogger, applicationLogger, securityLogger } from '@/services/systemLogger'

// Log a successful operation
mcpLogger.success('Connected to server', { url: 'http://localhost:3001' })

// Log information
applicationLogger.info('Loading applications', { filter: 'installed' })

// Log a warning
securityLogger.warn('Login failed', { username: 'admin', reason: 'Invalid password' })

// Log an error
mcpLogger.error('Connection lost', { error: 'Network timeout' })
```

## Viewing Logs

Logs can be viewed in the application's Logs page:
- **Filter by category**: Use tabs to filter by log source
- **Filter by severity**: Use dropdown to filter by level
- **Export**: Download logs as JSON file
- **Purge**: Clear all stored logs

## Best Practices

1. **Be descriptive**: Messages should be clear and actionable
2. **Include context**: Add relevant data in the `data` parameter
3. **Use appropriate levels**: Don't log info as error or vice versa
4. **Avoid sensitive data**: Never log passwords, tokens, or PII
5. **Log both success and failure**: Track the complete lifecycle of operations
