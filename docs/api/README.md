# API Reference

This document provides comprehensive API reference for the Homelab Assistant MCP tools.

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Health Tools](#health-tools)
4. [Server Management Tools](#server-management-tools)
5. [Application Management Tools](#application-management-tools)
6. [Monitoring Tools](#monitoring-tools)
7. [System Tools](#system-tools)
8. [Error Codes](#error-codes)

## Overview

The Homelab Assistant API is implemented using the Model Context Protocol (MCP). All functionality is exposed through "tools" that can be called with structured parameters and return standardized responses.

### Base URL

- Development: `http://localhost:8000`
- Production: Configure via `VITE_MCP_SERVER_URL`

### Request Format

All API calls use the MCP format:

```http
POST /mcp
Content-Type: application/json

{
  "method": "tools/call",
  "params": {
    "name": "tool_name",
    "arguments": {
      "param1": "value1",
      "param2": "value2"
    }
  }
}
```

### Response Format

All responses follow this structure:

```json
{
  "success": boolean,
  "data": any,              // Present on success
  "message": string,        // Human-readable message
  "error": string,          // Error code on failure
  "metadata": {             // Optional metadata
    "execution_time_ms": number,
    "request_id": string,
    "timestamp": string
  }
}
```

## Authentication

Currently, the API does not require authentication. This will be enhanced in future versions with:
- API key authentication
- Role-based access control
- Session management

## Health Tools

### `get_health_status`

Get comprehensive health status of the MCP server.

**Parameters:** None

**Response:**
```typescript
interface HealthStatusResponse {
  status: 'healthy' | 'unhealthy' | 'degraded'
  timestamp: string
  version: string
  components: Record<string, string>
  configuration: {
    ssh_timeout: number
    max_connections: number
  }
}
```

**Example:**
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "timestamp": "2025-09-05T10:30:00Z",
    "version": "0.1.0",
    "components": {
      "mcp_server": "healthy",
      "configuration": "healthy",
      "logging": "healthy"
    },
    "configuration": {
      "ssh_timeout": 30,
      "max_connections": 10
    }
  },
  "message": "Health check completed successfully"
}
```

**Errors:**
- `HEALTH_CHECK_ERROR`: Health check failed

### `ping`

Simple connectivity test.

**Parameters:** None

**Response:**
```json
{
  "success": true,
  "message": "pong",
  "timestamp": "2025-09-05T10:30:00Z"
}
```

## Server Management Tools

### `test_server_connection`

Test SSH connection to a remote server.

**Parameters:**
- `host` (string, required): Server hostname or IP address
- `port` (integer, optional): SSH port (default: 22)
- `username` (string, required): SSH username
- `auth_type` (string, required): Authentication type ("password" or "key")
- `credentials` (object, required): Authentication credentials

**Credentials Object:**

For password authentication:
```typescript
{
  password: string
}
```

For key authentication:
```typescript
{
  private_key: string,    // Private key content
  passphrase?: string     // Optional passphrase
}
```

**Response:**
```typescript
interface ServerConnectionTestResponse {
  success: boolean
  message: string
  latency_ms?: number
  system_info?: {
    os: string
    kernel: string
    architecture: string
    uptime: string
    docker_version?: string
  }
}
```

**Example:**
```json
{
  "success": true,
  "data": {
    "success": true,
    "message": "Connection successful",
    "latency_ms": 45,
    "system_info": {
      "os": "Ubuntu 22.04.3 LTS",
      "kernel": "5.15.0-78-generic",
      "architecture": "x86_64",
      "uptime": "up 5 days, 3 hours, 22 minutes",
      "docker_version": "24.0.5"
    }
  },
  "message": "Connection test completed"
}
```

**Errors:**
- `VALIDATION_ERROR`: Invalid input parameters
- `SSH_CONNECTION_ERROR`: SSH connection failed
- `AUTHENTICATION_ERROR`: SSH authentication failed

### `prepare_server` (Planned)

Prepare a remote server with Docker and dependencies.

**Parameters:**
- `host` (string, required): Server hostname or IP
- `port` (integer, optional): SSH port (default: 22)
- `username` (string, required): SSH username
- `auth_type` (string, required): "password" or "key"
- `credentials` (object, required): Authentication data
- `server_name` (string, optional): Friendly name for server

**Response:**
```typescript
interface PrepareServerResponse {
  server_id: string
  preparation_log: string[]
  docker_version: string
  system_info: SystemInfo
}
```

**Example:**
```json
{
  "success": true,
  "data": {
    "server_id": "srv_1693905600_001",
    "preparation_log": [
      "Checking for existing Docker installation...",
      "Docker not found, installing...",
      "✓ apt-get update completed",
      "✓ Docker GPG key added",
      "✓ Docker repository added",
      "✓ Docker installed successfully",
      "✓ User added to docker group"
    ],
    "docker_version": "24.0.5",
    "system_info": {
      "os": "Ubuntu 22.04.3 LTS",
      "kernel": "5.15.0-78-generic", 
      "architecture": "x86_64",
      "uptime": "up 5 days, 3 hours, 25 minutes"
    }
  },
  "message": "Server prepared successfully"
}
```

**Errors:**
- `VALIDATION_ERROR`: Invalid parameters
- `SSH_CONNECTION_ERROR`: Cannot connect to server
- `PREPARATION_ERROR`: Server preparation failed

### `list_servers` (Planned)

List all configured servers.

**Parameters:** None

**Response:**
```typescript
interface ListServersResponse {
  servers: ServerConnection[]
  total: number
}

interface ServerConnection {
  id: string
  name: string
  host: string
  port: number
  username: string
  status: 'connected' | 'disconnected' | 'error' | 'preparing'
  created_at: string
  last_connected?: string
  system_info?: SystemInfo
}
```

## Application Management Tools

### `list_applications` (Planned)

Get available applications from catalog.

**Parameters:**
- `category` (string, optional): Filter by category
- `search` (string, optional): Search term

**Response:**
```typescript
interface ListApplicationsResponse {
  applications: Application[]
  categories: string[]
  total: number
}

interface Application {
  id: string
  name: string
  display_name: string
  description: string
  category: string
  icon_url: string
  docker_image: string
  default_ports: PortMapping[]
  environment_variables: EnvironmentVariable[]
  volume_mounts: VolumeMount[]
  dependencies: string[]
  min_resources: ResourceRequirements
  tags: string[]
}
```

### `install_app` (Planned)

Install a containerized application on a server.

**Parameters:**
- `server_id` (string, required): Target server identifier
- `app_id` (string, required): Application identifier from catalog
- `configuration` (object, optional): App-specific configuration
- `custom_ports` (array, optional): Custom port mappings
- `environment_variables` (object, optional): Environment variables

**Response:**
```typescript
interface InstallAppResponse {
  installation_id: string
  container_id: string
  access_urls: string[]
  installation_log: string[]
}
```

**Example:**
```json
{
  "success": true,
  "data": {
    "installation_id": "inst_portainer_1693905800",
    "container_id": "a1b2c3d4e5f6",
    "access_urls": [
      "http://192.168.1.100:9000"
    ],
    "installation_log": [
      "Pulling Docker image portainer/portainer-ce:latest...",
      "✓ Image pulled successfully",
      "Creating container directories...",
      "✓ /var/lib/portainer created",
      "Starting container...",
      "✓ Container started: a1b2c3d4e5f6"
    ]
  },
  "message": "Portainer installed successfully"
}
```

**Errors:**
- `VALIDATION_ERROR`: Invalid parameters
- `SERVER_NOT_FOUND`: Server does not exist
- `APP_NOT_FOUND`: Application not in catalog
- `INSTALLATION_ERROR`: Installation failed
- `DOCKER_ERROR`: Docker operation failed

### `uninstall_app` (Planned)

Remove an installed application.

**Parameters:**
- `server_id` (string, required): Target server
- `app_name` (string, required): Installed application name
- `remove_data` (boolean, optional): Remove persistent data (default: false)

**Response:**
```typescript
interface UninstallAppResponse {
  cleanup_log: string[]
  removed_containers: string[]
  removed_volumes: string[]
  removed_images: string[]
}
```

### `list_installed_apps` (Planned)

List installed applications on a server.

**Parameters:**
- `server_id` (string, required): Target server

**Response:**
```typescript
interface ListInstalledAppsResponse {
  applications: InstalledApplication[]
  total: number
}

interface InstalledApplication {
  id: string
  server_id: string
  app_id: string
  name: string
  container_id: string
  status: 'running' | 'stopped' | 'error' | 'installing' | 'uninstalling'
  ports: PortMapping[]
  access_urls: string[]
  installed_at: string
  updated_at: string
  resource_usage?: ResourceUsage
}
```

## Monitoring Tools

### `get_server_status` (Planned)

Get comprehensive server and application status.

**Parameters:**
- `server_id` (string, required): Server identifier

**Response:**
```typescript
interface ServerStatusResponse {
  server_info: {
    id: string
    name: string
    host: string
    status: 'online' | 'offline' | 'error'
    last_seen: string
    uptime: string
  }
  resources: {
    cpu_percent: number
    memory_percent: number
    disk_usage: {
      total: number
      used: number
      free: number
      percent: number
    }
    network_io: {
      bytes_sent: number
      bytes_recv: number
    }
  }
  applications: Array<{
    name: string
    status: 'running' | 'stopped' | 'error'
    container_id: string
    ports: number[]
    resource_usage: {
      cpu_percent: number
      memory_mb: number
      network_io: {
        rx_bytes: number
        tx_bytes: number
      }
    }
  }>
}
```

### `get_server_logs` (Planned)

Retrieve server logs.

**Parameters:**
- `server_id` (string, required): Server identifier
- `lines` (integer, optional): Number of lines to retrieve (default: 100)
- `filter` (string, optional): Filter pattern

**Response:**
```typescript
interface ServerLogsResponse {
  logs: Array<{
    timestamp: string
    level: 'info' | 'warn' | 'error' | 'debug'
    message: string
    source: string
  }>
  total_lines: number
  has_more: boolean
}
```

## System Tools

### `full_cleanup` (Planned)

Perform complete server cleanup and reset.

**Parameters:**
- `server_id` (string, required): Target server
- `confirm_cleanup` (boolean, required): Safety confirmation

**Response:**
```typescript
interface FullCleanupResponse {
  cleanup_summary: {
    containers_removed: number
    images_removed: number
    volumes_removed: number
    networks_removed: number
    disk_space_freed: string
  }
  cleanup_log: string[]
}
```

**Example:**
```json
{
  "success": true,
  "data": {
    "cleanup_summary": {
      "containers_removed": 5,
      "images_removed": 8,
      "volumes_removed": 3,
      "networks_removed": 2,
      "disk_space_freed": "2.4 GB"
    },
    "cleanup_log": [
      "Stopping all containers...",
      "✓ 5 containers stopped",
      "Removing containers...",
      "✓ 5 containers removed",
      "Removing unused images...",
      "✓ 8 images removed",
      "Removing unused volumes...",
      "✓ 3 volumes removed",
      "Pruning networks...",
      "✓ 2 networks removed",
      "✓ Cleanup completed"
    ]
  },
  "message": "Server cleanup completed successfully"
}
```

**Errors:**
- `VALIDATION_ERROR`: Invalid parameters
- `SERVER_NOT_FOUND`: Server does not exist
- `CLEANUP_ERROR`: Cleanup operation failed
- `CONFIRMATION_REQUIRED`: confirm_cleanup must be true

## Error Codes

### Validation Errors
- `VALIDATION_ERROR`: Input validation failed
- `MISSING_PARAMETER`: Required parameter not provided
- `INVALID_FORMAT`: Parameter format is invalid

### Connection Errors
- `CONNECTION_ERROR`: General connection failure
- `SSH_CONNECTION_ERROR`: SSH connection failed
- `AUTHENTICATION_ERROR`: Authentication failed
- `TIMEOUT_ERROR`: Operation timed out

### Resource Errors
- `SERVER_NOT_FOUND`: Server does not exist
- `APP_NOT_FOUND`: Application not in catalog
- `CONTAINER_NOT_FOUND`: Docker container not found
- `ALREADY_EXISTS`: Resource already exists

### System Errors
- `DOCKER_ERROR`: Docker operation failed
- `SYSTEM_ERROR`: Internal system error
- `EXECUTION_ERROR`: Tool execution failed
- `INSUFFICIENT_PERMISSIONS`: Permission denied

### Security Errors
- `UNAUTHORIZED`: Access denied
- `FORBIDDEN`: Operation not allowed
- `CREDENTIAL_ERROR`: Credential-related error

## Rate Limiting

The API implements rate limiting to prevent abuse:

- **Health endpoints**: 60 requests per minute
- **Server operations**: 30 requests per minute  
- **Application operations**: 20 requests per minute
- **System operations**: 10 requests per minute

Rate limit headers are included in responses:
```http
X-RateLimit-Limit: 30
X-RateLimit-Remaining: 29
X-RateLimit-Reset: 1693906200
```

## Webhooks (Future)

Future versions will support webhooks for real-time notifications:

- Server status changes
- Application installation completion
- System alerts and errors

## SDKs

### TypeScript/JavaScript

```typescript
import { HomelabMCPClient } from '@homelab/mcp-client'

const client = new HomelabMCPClient('http://localhost:8000')

// Test server connection
const result = await client.callTool('test_server_connection', {
  host: '192.168.1.100',
  username: 'user',
  auth_type: 'password',
  credentials: { password: 'secret' }
})

console.log(result.data)
```

### Python

```python
from homelab_client import HomelabClient

client = HomelabClient('http://localhost:8000')

# Install application
result = await client.install_app(
    server_id='srv_001',
    app_id='portainer',
    custom_ports=[9000]
)

print(result['data'])
```

---

For more information, see:
- [Developer Guide](../developer/) - Development setup and examples
- [MCP Protocol](../developer/mcp-protocol.md) - Protocol implementation details
- [User Guide](../user/) - End-user documentation
