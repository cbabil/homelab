/**
 * Server Info Service
 *
 * Handles fetching system information from remote servers via SSH.
 * Uses MCP backend to execute SSH commands and retrieve system info.
 */

import { SystemInfo, ServerConnection } from '@/types/server'

export interface ServerInfoFetchResult {
  success: boolean
  system_info?: SystemInfo
  docker_installed?: boolean
  error?: string
  message: string
}

// MCP client type for dependency injection
interface MCPClient {
  callTool: <T>(name: string, params: Record<string, unknown>) => Promise<{
    success: boolean
    data?: T
    error?: string
    message?: string
  }>
}

interface TestConnectionResponse {
  success?: boolean
  system_info?: SystemInfo
  docker_installed?: boolean
  agent_installed?: boolean
  message?: string
  error?: string
}

class ServerInfoService {
  private mcpClient: MCPClient | null = null

  /**
   * Set the MCP client for backend communication
   * Must be called before using fetchServerInfo
   */
  setMCPClient(client: MCPClient | null) {
    this.mcpClient = client
  }

  /**
   * Fetch comprehensive system information from a server
   * Uses the backend test_connection tool to get real system info
   */
  async fetchServerInfo(server: ServerConnection): Promise<ServerInfoFetchResult> {
    return this.fetchServerInfoById(server.id)
  }

  /**
   * Fetch system information by server ID
   * Used when testing connection before adding server to localStorage
   */
  async fetchServerInfoById(serverId: string): Promise<ServerInfoFetchResult> {
    if (!this.mcpClient) {
      return {
        success: false,
        error: 'MCP client not available',
        message: 'Backend connection not established'
      }
    }

    try {
      // Call the backend test_connection tool which fetches system info via SSH
      const response = await this.mcpClient.callTool<TestConnectionResponse>('test_connection', {
        server_id: serverId
      })

      if (response.success && response.data) {
        const backendResponse = response.data

        // Check tool-level success (not just MCP wrapper success)
        if (!backendResponse.success) {
          return {
            success: false,
            error: backendResponse.error || backendResponse.message || 'Connection failed',
            message: backendResponse.message || 'Failed to fetch server information'
          }
        }

        const systemInfo = backendResponse.system_info
        const dockerInstalled = backendResponse.docker_installed ?? false

        return {
          success: true,
          system_info: systemInfo,
          docker_installed: dockerInstalled,
          message: 'Server information retrieved successfully'
        }
      }

      return {
        success: false,
        error: response.error || 'Unknown error',
        message: 'Failed to fetch server information'
      }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        message: 'Failed to fetch server information'
      }
    }
  }
}

export const serverInfoService = new ServerInfoService()