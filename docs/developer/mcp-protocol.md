# MCP Protocol Implementation Guide

This document provides detailed information about the Model Context Protocol (MCP) implementation in the Tomo project.

## Table of Contents

1. [Overview](#overview)
2. [Protocol Specification](#protocol-specification)
3. [Backend Implementation](#backend-implementation)
4. [Frontend Implementation](#frontend-implementation)
5. [Tool Development](#tool-development)
6. [Error Handling](#error-handling)
7. [Real-time Features](#real-time-features)
8. [Best Practices](#best-practices)

## Overview

The Tomo uses the Model Context Protocol (MCP) for all frontend-backend communication. MCP provides a standardized way to expose backend functionality as "tools" that can be called from the frontend with type safety and consistent error handling.

### Why MCP?

- **Type Safety**: Tools are defined with strict schemas
- **Consistency**: Standardized request/response format
- **Extensibility**: Easy to add new capabilities
- **Error Handling**: Built-in error response patterns
- **Real-time**: Native support for events and subscriptions

### Architecture

```
┌─────────────────┐         ┌─────────────────┐
│   Frontend      │         │   Backend       │
│                 │         │                 │
│  MCPClient ◄────┼─────────┼───► FastMCP     │
│                 │   HTTP  │                 │
│  EventSource ◄──┼─────────┼───► Events      │
└─────────────────┘  WebSock└─────────────────┘
```

## Protocol Specification

### Request Format

All MCP requests follow this structure:

```json
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

All MCP responses follow this structure:

```json
{
  "success": boolean,
  "data": any,              // Present on success
  "message": string,        // Human-readable message
  "error": string,          // Present on failure
  "metadata": {             // Optional metadata
    "execution_time_ms": number,
    "request_id": string,
    "timestamp": string
  }
}
```

### HTTP Transport

- **Endpoint**: `POST /mcp`
- **Content-Type**: `application/json`
- **Status Codes**:
  - `200`: Successful tool call (check `success` field)
  - `400`: Invalid request format
  - `404`: Tool not found
  - `500`: Server error

## Backend Implementation

### FastMCP Server Setup

```python
# backend/src/main.py
from fastmcp import FastMCP
from tools.health_tools import register_health_tools
from lib.config import load_config

app = FastMCP(
    name="tomo",
    version="0.1.0",
    instructions="Tomo management and automation server",
)

config = load_config()
register_health_tools(app, config)
```

### Tool Definition

Tools are defined using the `@tool` decorator:

```python
from fastmcp import tool
from typing import Dict, Any, Optional

@tool
async def example_tool(
    required_param: str,
    optional_param: Optional[int] = 10,
    config_param: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Example tool demonstrating MCP patterns.
    
    Args:
        required_param: A required string parameter
        optional_param: An optional integer with default value
        config_param: Optional configuration dictionary
        
    Returns:
        dict: Standardized MCP response
    """
    try:
        # Validate inputs
        if not required_param or len(required_param) == 0:
            return {
                "success": False,
                "error": "VALIDATION_ERROR",
                "message": "required_param cannot be empty"
            }
        
        # Perform operation
        result = perform_operation(required_param, optional_param, config_param or {})
        
        return {
            "success": True,
            "data": result,
            "message": f"Operation completed for {required_param}"
        }
        
    except ValueError as e:
        return {
            "success": False,
            "error": "VALIDATION_ERROR", 
            "message": str(e)
        }
    except Exception as e:
        logger.error("Tool execution failed", tool="example_tool", error=str(e))
        return {
            "success": False,
            "error": "EXECUTION_ERROR",
            "message": f"Tool execution failed: {str(e)}"
        }
```

### Tool Registration

Tools must be registered with the FastMCP app:

```python
# Method 1: Class-based tools
class ServerTools:
    def __init__(self, ssh_service):
        self.ssh_service = ssh_service
    
    @tool
    async def test_connection(self, host: str, port: int = 22) -> dict:
        # Tool implementation
        pass

app.include_tools(ServerTools(ssh_service))

# Method 2: Function-based tools
@tool
async def standalone_tool() -> dict:
    return {"success": True, "message": "Hello from standalone tool"}

app.include_tools(standalone_tool)
```

### Error Standardization

All tools should return consistent error formats:

```python
# Success response
{
    "success": True,
    "data": {"key": "value"},
    "message": "Operation completed successfully"
}

# Validation error
{
    "success": False,
    "error": "VALIDATION_ERROR",
    "message": "Invalid input: host cannot be empty"
}

# Execution error  
{
    "success": False,
    "error": "SSH_CONNECTION_ERROR",
    "message": "Failed to connect to server: Connection refused"
}

# System error
{
    "success": False,
    "error": "SYSTEM_ERROR",
    "message": "Internal server error occurred"
}
```

### Standard Error Codes

- `VALIDATION_ERROR`: Input validation failed
- `AUTHENTICATION_ERROR`: Authentication/authorization failed
- `CONNECTION_ERROR`: Network or connection issues
- `SSH_CONNECTION_ERROR`: SSH-specific connection issues
- `DOCKER_ERROR`: Docker operation failures
- `SYSTEM_ERROR`: Internal system errors
- `NOT_FOUND`: Resource not found
- `ALREADY_EXISTS`: Resource already exists
- `EXECUTION_ERROR`: General execution failure

## Frontend Implementation

### MCP Client

The frontend uses a custom MCP client implementation:

```typescript
// frontend/src/services/mcpClient.ts
import { MCPClient, MCPRequest, MCPResponse } from '@/types/mcp'

export class TomoMCPClient implements MCPClient {
  private baseUrl: string
  private connected: boolean = false

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl.replace(/\/$/, '')
  }

  async connect(): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/health`)
      if (!response.ok) {
        throw new Error(`Connection failed: ${response.statusText}`)
      }
      this.connected = true
    } catch (error) {
      this.connected = false
      throw new Error(`Failed to connect to MCP server: ${error}`)
    }
  }

  async callTool<T>(name: string, params: Record<string, unknown>): Promise<MCPResponse<T>> {
    if (!this.connected) {
      await this.connect()
    }

    const request: MCPRequest = {
      method: 'tools/call',
      params: { name, arguments: params }
    }

    try {
      const response = await fetch(`${this.baseUrl}/mcp`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request)
      })

      if (!response.ok) {
        throw new Error(`MCP call failed: ${response.status} ${response.statusText}`)
      }

      return await response.json()
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        message: 'MCP tool call failed'
      }
    }
  }

  isConnected(): boolean {
    return this.connected
  }
}
```

### React Integration

#### MCP Provider

```typescript
// frontend/src/providers/MCPProvider.tsx
import React, { createContext, useContext, useEffect, useState } from 'react'
import { TomoMCPClient } from '@/services/mcpClient'

interface MCPContextType {
  client: TomoMCPClient | null
  isConnected: boolean
  error: string | null
}

const MCPContext = createContext<MCPContextType>({
  client: null,
  isConnected: false,
  error: null
})

export function MCPProvider({ children }: { children: React.ReactNode }) {
  const [client] = useState(() => new TomoMCPClient(
    import.meta.env.VITE_MCP_SERVER_URL || 'http://localhost:8000'
  ))
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    client.connect()
      .then(() => {
        setIsConnected(true)
        setError(null)
      })
      .catch((err) => {
        setIsConnected(false)
        setError(err.message)
      })
  }, [client])

  return (
    <MCPContext.Provider value={{ client, isConnected, error }}>
      {children}
    </MCPContext.Provider>
  )
}

export const useMCP = () => {
  const context = useContext(MCPContext)
  if (!context.client) {
    throw new Error('useMCP must be used within MCPProvider')
  }
  return context.client
}
```

#### Component Usage

```typescript
// frontend/src/components/ServerConnectionTest.tsx
import React, { useState } from 'react'
import { useMCP } from '@/providers/MCPProvider'
import { ServerConnectionTest } from '@/types/mcp'

export function ServerConnectionTest() {
  const mcp = useMCP()
  const [testing, setTesting] = useState(false)
  const [result, setResult] = useState<ServerConnectionTest | null>(null)

  const testConnection = async () => {
    setTesting(true)
    
    try {
      const response = await mcp.callTool<ServerConnectionTest>('test_server_connection', {
        host: '192.168.1.100',
        port: 22,
        username: 'user',
        auth_type: 'password',
        credentials: { password: 'secret' }
      })
      
      if (response.success) {
        setResult(response.data!)
      } else {
        console.error('Connection test failed:', response.error)
        setResult({ 
          success: false, 
          message: response.error || 'Unknown error' 
        })
      }
    } catch (error) {
      console.error('MCP call failed:', error)
    } finally {
      setTesting(false)
    }
  }

  return (
    <div>
      <button onClick={testConnection} disabled={testing}>
        {testing ? 'Testing...' : 'Test Connection'}
      </button>
      
      {result && (
        <div className={result.success ? 'text-green-600' : 'text-red-600'}>
          {result.message}
          {result.success && result.system_info && (
            <pre>{JSON.stringify(result.system_info, null, 2)}</pre>
          )}
        </div>
      )}
    </div>
  )
}
```

### TypeScript Types

```typescript
// frontend/src/types/mcp.ts
export interface MCPRequest {
  method: string
  params: {
    name: string
    arguments: Record<string, unknown>
  }
}

export interface MCPResponse<T = unknown> {
  success: boolean
  data?: T
  message?: string
  error?: string
  metadata?: {
    execution_time_ms: number
    request_id: string
    timestamp: string
  }
}

export interface MCPClient {
  connect(): Promise<void>
  disconnect(): Promise<void>
  callTool<T>(name: string, params: Record<string, unknown>): Promise<MCPResponse<T>>
  subscribeTo(events: string[]): EventSource
  isConnected(): boolean
}

// Tool-specific response types
export interface ServerConnectionTest {
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

export interface HealthStatus {
  status: 'healthy' | 'unhealthy' | 'degraded'
  timestamp: string
  version: string
  components: Record<string, string>
  configuration?: Record<string, unknown>
}
```

## Tool Development

### Tool Development Workflow

1. **Define Tool Interface**: Start with TypeScript interfaces
2. **Implement Backend Tool**: Create the Python tool function
3. **Register Tool**: Add to FastMCP app
4. **Test Tool**: Write unit and integration tests
5. **Use in Frontend**: Call from React components

### Example: Creating a New Tool

#### 1. Define TypeScript Interface

```typescript
// frontend/src/types/docker.ts
export interface ContainerInfo {
  id: string
  name: string
  image: string
  status: 'running' | 'stopped' | 'error'
  ports: Array<{
    container_port: number
    host_port: number
    protocol: 'tcp' | 'udp'
  }>
  created: string
  started?: string
}

export interface ListContainersResponse {
  containers: ContainerInfo[]
  total: number
}
```

#### 2. Implement Backend Tool

```python
# backend/src/tools/docker_tools.py
from fastmcp import tool
from typing import Dict, Any, List
import docker
import structlog

logger = structlog.get_logger("docker_tools")

class DockerTools:
    def __init__(self, ssh_service):
        self.ssh_service = ssh_service
    
    @tool
    async def list_containers(
        self,
        server_id: str,
        status_filter: str = "all"
    ) -> Dict[str, Any]:
        """
        List Docker containers on a remote server.
        
        Args:
            server_id: Target server identifier
            status_filter: Filter by status ('all', 'running', 'stopped')
            
        Returns:
            dict: List of containers with details
        """
        try:
            # Validate inputs
            if not server_id:
                return {
                    "success": False,
                    "error": "VALIDATION_ERROR",
                    "message": "server_id is required"
                }
            
            valid_filters = ["all", "running", "stopped"]
            if status_filter not in valid_filters:
                return {
                    "success": False,
                    "error": "VALIDATION_ERROR", 
                    "message": f"status_filter must be one of: {valid_filters}"
                }
            
            # Get SSH connection
            client = await self.ssh_service.get_connection(server_id)
            
            # Build docker command
            cmd = "docker ps"
            if status_filter == "all":
                cmd += " -a"
            elif status_filter == "stopped":
                cmd += " -a --filter status=exited"
            
            cmd += " --format 'table {{.ID}}\\t{{.Names}}\\t{{.Image}}\\t{{.Status}}\\t{{.Ports}}\\t{{.CreatedAt}}'"
            
            # Execute command
            stdin, stdout, stderr = client.exec_command(cmd)
            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()
            
            if error:
                logger.error("Docker command failed", error=error)
                return {
                    "success": False,
                    "error": "DOCKER_ERROR",
                    "message": f"Docker command failed: {error}"
                }
            
            # Parse output
            containers = self._parse_container_list(output)
            
            return {
                "success": True,
                "data": {
                    "containers": containers,
                    "total": len(containers)
                },
                "message": f"Found {len(containers)} containers"
            }
            
        except Exception as e:
            logger.error("Failed to list containers", server_id=server_id, error=str(e))
            return {
                "success": False,
                "error": "EXECUTION_ERROR",
                "message": f"Failed to list containers: {str(e)}"
            }
    
    def _parse_container_list(self, output: str) -> List[Dict[str, Any]]:
        """Parse docker ps output into structured data."""
        containers = []
        lines = output.split('\n')[1:]  # Skip header
        
        for line in lines:
            if line.strip():
                parts = line.split('\t')
                if len(parts) >= 6:
                    containers.append({
                        "id": parts[0],
                        "name": parts[1],
                        "image": parts[2],
                        "status": "running" if "Up" in parts[3] else "stopped",
                        "ports": self._parse_ports(parts[4]),
                        "created": parts[5]
                    })
        
        return containers
    
    def _parse_ports(self, port_str: str) -> List[Dict[str, Any]]:
        """Parse Docker port mappings."""
        # Implement port parsing logic
        return []
```

#### 3. Register Tool

```python
# backend/src/main.py
from tools.docker_tools import DockerTools

app.include_tools(DockerTools(ssh_service))
```

#### 4. Test Tool

```python
# backend/tests/unit/test_docker_tools.py
import pytest
from unittest.mock import AsyncMock, patch
from tools.docker_tools import DockerTools

@pytest.fixture
def docker_tools():
    ssh_service = AsyncMock()
    return DockerTools(ssh_service)

@pytest.mark.asyncio
async def test_list_containers_success(docker_tools):
    # Mock SSH service
    mock_client = AsyncMock()
    mock_stdout = AsyncMock()
    mock_stdout.read.return_value = b"CONTAINER ID\tNAMES\tIMAGE\tSTATUS\tPORTS\tCREATED\nabc123\ttest\tnginx\tUp 1 hour\t80->8080/tcp\t2 hours ago"
    mock_stderr = AsyncMock()
    mock_stderr.read.return_value = b""
    
    mock_client.exec_command.return_value = (None, mock_stdout, mock_stderr)
    docker_tools.ssh_service.get_connection.return_value = mock_client
    
    # Test tool
    result = await docker_tools.list_containers("server-1", "running")
    
    assert result["success"] is True
    assert len(result["data"]["containers"]) == 1
    assert result["data"]["containers"][0]["name"] == "test"
```

#### 5. Use in Frontend

```typescript
// frontend/src/components/ContainerList.tsx
import React, { useEffect, useState } from 'react'
import { useMCP } from '@/providers/MCPProvider'
import { ListContainersResponse } from '@/types/docker'

interface Props {
  serverId: string
}

export function ContainerList({ serverId }: Props) {
  const mcp = useMCP()
  const [containers, setContainers] = useState<ListContainersResponse | null>(null)
  const [loading, setLoading] = useState(false)
  
  useEffect(() => {
    loadContainers()
  }, [serverId])
  
  const loadContainers = async () => {
    setLoading(true)
    
    try {
      const response = await mcp.callTool<ListContainersResponse>('list_containers', {
        server_id: serverId,
        status_filter: 'all'
      })
      
      if (response.success) {
        setContainers(response.data!)
      } else {
        console.error('Failed to load containers:', response.error)
      }
    } catch (error) {
      console.error('MCP call failed:', error)
    } finally {
      setLoading(false)
    }
  }
  
  if (loading) return <div>Loading containers...</div>
  if (!containers) return <div>No containers found</div>
  
  return (
    <div>
      <h3>Containers ({containers.total})</h3>
      {containers.containers.map(container => (
        <div key={container.id} className="border p-4 rounded">
          <h4>{container.name}</h4>
          <p>Image: {container.image}</p>
          <p>Status: {container.status}</p>
          <p>Created: {container.created}</p>
        </div>
      ))}
    </div>
  )
}
```

## Error Handling

### Backend Error Handling

```python
@tool
async def example_with_error_handling(param: str) -> dict:
    """Example tool with comprehensive error handling."""
    try:
        # Input validation
        if not param or len(param.strip()) == 0:
            return {
                "success": False,
                "error": "VALIDATION_ERROR",
                "message": "Parameter cannot be empty"
            }
        
        # Business logic that might fail
        result = risky_operation(param)
        
        return {
            "success": True,
            "data": result,
            "message": "Operation completed successfully"
        }
        
    except ValidationError as e:
        logger.warning("Validation failed", param=param, error=str(e))
        return {
            "success": False,
            "error": "VALIDATION_ERROR",
            "message": str(e)
        }
    
    except ConnectionError as e:
        logger.error("Connection failed", param=param, error=str(e))
        return {
            "success": False,
            "error": "CONNECTION_ERROR", 
            "message": f"Connection failed: {str(e)}"
        }
    
    except Exception as e:
        logger.error("Unexpected error", param=param, error=str(e), exc_info=True)
        return {
            "success": False,
            "error": "SYSTEM_ERROR",
            "message": "An unexpected error occurred"
        }
```

### Frontend Error Handling

```typescript
// Error handling utility
export class MCPError extends Error {
  constructor(
    public code: string,
    message: string,
    public response?: MCPResponse
  ) {
    super(message)
    this.name = 'MCPError'
  }
}

// Enhanced MCP client with error handling
export class TomoMCPClient {
  async callTool<T>(name: string, params: Record<string, unknown>): Promise<T> {
    const response = await this.callToolRaw<T>(name, params)
    
    if (!response.success) {
      throw new MCPError(
        response.error || 'UNKNOWN_ERROR',
        response.message || 'Tool call failed',
        response
      )
    }
    
    return response.data!
  }
  
  async callToolSafe<T>(
    name: string, 
    params: Record<string, unknown>
  ): Promise<{ data: T | null; error: MCPError | null }> {
    try {
      const data = await this.callTool<T>(name, params)
      return { data, error: null }
    } catch (error) {
      return { 
        data: null, 
        error: error instanceof MCPError ? error : new MCPError('UNKNOWN_ERROR', String(error))
      }
    }
  }
}

// Component usage with error handling
export function MyComponent() {
  const mcp = useMCP()
  const [error, setError] = useState<string | null>(null)
  
  const handleOperation = async () => {
    setError(null)
    
    const { data, error: mcpError } = await mcp.callToolSafe('my_tool', { param: 'value' })
    
    if (mcpError) {
      setError(mcpError.message)
      
      // Handle specific error types
      switch (mcpError.code) {
        case 'VALIDATION_ERROR':
          // Show validation feedback
          break
        case 'CONNECTION_ERROR':
          // Show connection issues
          break
        default:
          // Generic error handling
          break
      }
    } else {
      // Handle success
      console.log('Success:', data)
    }
  }
  
  return (
    <div>
      {error && <div className="error">{error}</div>}
      <button onClick={handleOperation}>Execute Operation</button>
    </div>
  )
}
```

## Real-time Features

### Event Streaming (Future)

The MCP protocol supports real-time events through Server-Sent Events:

```python
# Backend event streaming
@app.get("/events")
async def event_stream(events: str = ""):
    async def event_generator():
        while True:
            # Generate events based on subscription
            event_data = await get_server_status()
            yield f"data: {json.dumps(event_data)}\n\n"
            await asyncio.sleep(5)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache"}
    )
```

```typescript
// Frontend event subscription
export function useServerMonitoring(serverId: string) {
  const mcp = useMCP()
  const [status, setStatus] = useState(null)
  
  useEffect(() => {
    const eventSource = mcp.subscribeTo(['server_status'])
    
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.server_id === serverId) {
        setStatus(data)
      }
    }
    
    return () => eventSource.close()
  }, [serverId])
  
  return status
}
```

## Best Practices

### Tool Design

1. **Single Responsibility**: Each tool should do one thing well
2. **Consistent Naming**: Use descriptive, action-oriented names
3. **Input Validation**: Always validate inputs before processing
4. **Error Handling**: Return consistent error formats
5. **Documentation**: Include comprehensive docstrings
6. **Logging**: Log operations for debugging and auditing

### Performance

1. **Async Operations**: Use async/await for I/O operations
2. **Connection Pooling**: Reuse SSH connections when possible
3. **Timeout Handling**: Set appropriate timeouts for operations
4. **Resource Cleanup**: Always close connections and clean up resources
5. **Caching**: Cache expensive operations where appropriate

### Security

1. **Input Sanitization**: Sanitize all user inputs
2. **Credential Protection**: Never log or return sensitive data
3. **Command Injection**: Validate and escape command parameters
4. **Authorization**: Implement proper access controls
5. **Audit Logging**: Log security-relevant operations

### Testing

1. **Unit Tests**: Test individual tools in isolation
2. **Integration Tests**: Test MCP communication end-to-end
3. **Mock Dependencies**: Mock external services in tests
4. **Error Scenarios**: Test error conditions and edge cases
5. **Performance Tests**: Test tools under load

---

This MCP protocol implementation provides a solid foundation for extending the Tomo with new capabilities while maintaining consistency, type safety, and reliability across the entire system.
