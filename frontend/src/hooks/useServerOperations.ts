/**
 * Server Operations Helper Functions
 *
 * Extracted helper logic for server connection and save operations.
 * No localStorage - backend is single source of truth.
 */

import { ServerConnection, ServerConnectionInput, SystemInfo } from '@/types/server'
import type { MCPResponse } from '@/types/mcp'

/** Simplified MCP client interface for tool calls */
interface MCPToolClient {
  callTool: <T>(name: string, params: Record<string, unknown>) => Promise<MCPResponse<T>>
}

/** Result from a server connection attempt */
export interface ConnectionResult {
  success: boolean
  error?: string
  isMcpError?: boolean
}

/** Check if an error message indicates an MCP/Backend error */
export function isMcpErrorMessage(errorMsg: string): boolean {
  return errorMsg.includes('MCP') || errorMsg.includes('Backend')
}

/** Calculate server stats */
export function calculateServerStats(servers: ServerConnection[]) {
  const connectedCount = servers.filter(s => s.status === 'connected').length
  const totalServers = servers.length
  const healthPercentage = Math.round((connectedCount / totalServers) * 100) || 0
  return { connectedCount, totalServers, healthPercentage }
}

/** Filter servers by search term */
export function filterServers(servers: ServerConnection[], searchTerm: string): ServerConnection[] {
  const term = searchTerm.toLowerCase()
  return servers.filter(server =>
    server.name.toLowerCase().includes(term) ||
    server.host.toLowerCase().includes(term) ||
    server.username.toLowerCase().includes(term)
  )
}

/** Create server data payload for backend */
export function createServerPayload(
  serverId: string,
  serverData: ServerConnectionInput,
  systemInfo?: SystemInfo
) {
  return {
    server_id: serverId,
    name: serverData.name,
    host: serverData.host,
    port: serverData.port,
    username: serverData.username,
    auth_type: serverData.auth_type,
    password: serverData.auth_type === 'password' ? serverData.credentials.password : undefined,
    private_key: serverData.auth_type === 'key' ? serverData.credentials.private_key : undefined,
    system_info: systemInfo
  }
}

/** Response from add_server backend call */
interface AddServerResponse {
  success: boolean
  message?: string
  server_id?: string
  was_existing?: boolean
}

/** Add new server to backend. Returns the actual server_id (may differ if server already existed). */
export async function addServerToBackend(
  client: MCPToolClient,
  serverId: string,
  serverData: ServerConnectionInput,
  systemInfo?: SystemInfo
): Promise<string> {
  const payload = createServerPayload(serverId, serverData, systemInfo)
  const response = await client.callTool<AddServerResponse>('add_server', payload)
  if (!response.data?.success) {
    throw new Error(response.data?.message || 'Failed to add server to backend')
  }
  // Return the actual server_id from backend (may be different if server already existed)
  return response.data.server_id || serverId
}
