/**
 * MCP Protocol Types
 * 
 * TypeScript definitions for Model Context Protocol communication.
 * Matches the backend tool definitions and response formats.
 */

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

export interface MCPToolDefinition {
  name: string
  description: string
  parameters: Record<string, unknown>
}

export interface MCPServerInfo {
  name: string
  version: string
  description: string
  tools: MCPToolDefinition[]
}

export interface HealthStatus {
  status: 'healthy' | 'unhealthy' | 'degraded'
  timestamp: string
  version: string
  components: Record<string, string>
  configuration?: Record<string, unknown>
}

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