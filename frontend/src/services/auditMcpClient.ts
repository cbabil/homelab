/**
 * Audit MCP Client
 *
 * MCP client for audit operations (settings audit, auth audit).
 * Provides type-safe interface for accessing audit trails.
 */

import { useMemo } from 'react'
import { useMCP } from '@/providers/MCPProvider'
import { mcpLogger } from '@/services/systemLogger'

// Settings audit entry type
export interface SettingsAuditEntry {
  id: number
  table_name: string
  record_id: string
  user_id: string
  setting_key: string
  old_value: unknown
  new_value: unknown
  change_type: string
  change_reason?: string
  client_ip?: string
  user_agent?: string
  created_at: string
  checksum?: string
}

// Auth audit entry type
export interface AuthAuditEntry {
  id: string
  timestamp: string
  level: string
  event_type: string
  username: string
  success: boolean
  client_ip?: string
  user_agent?: string
  message: string
  tags: string[]
}

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

// Agent audit result with pagination info
export interface AgentAuditResult {
  entries: AgentAuditEntry[]
  total: number
  truncated?: boolean
}

/**
 * MCP-based Audit Client
 *
 * Handles all audit operations through the backend MCP tools
 * with proper error handling and type safety.
 */
export class AuditMcpClient {
  private mcpClient: ReturnType<typeof useMCP>['client']

  constructor(mcpClient: ReturnType<typeof useMCP>['client'], _isConnected: () => boolean) {
    this.mcpClient = mcpClient
    mcpLogger.info('Audit MCP Client initialized')
  }

  /**
   * Get settings audit log (admin only)
   *
   * @param filterUserId - Filter entries by the user who made the changes
   * @param settingKey - Filter entries by specific setting key
   * @param limit - Maximum entries to return
   * @param offset - Number of entries to skip for pagination
   */
  async getSettingsAudit(
    filterUserId?: string,
    settingKey?: string,
    limit: number = 50,
    offset: number = 0
  ): Promise<SettingsAuditEntry[]> {
    try {
      mcpLogger.info('Getting settings audit log', { filterUserId, settingKey, limit, offset })

      const response = await this.mcpClient.callTool<{ audit_entries: SettingsAuditEntry[] }>('get_settings_audit', {
        filter_user_id: filterUserId,
        setting_key: settingKey,
        limit,
        offset
      })

      if (!response.success) {
        mcpLogger.error('Failed to get settings audit', { error: response.error })
        return []
      }

      const entries = response.data?.audit_entries || []
      mcpLogger.info('Settings audit retrieved successfully', { count: entries.length })
      return entries
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      mcpLogger.error('Settings audit retrieval failed', { error: errorMessage })
      return []
    }
  }

  /**
   * Get auth audit log (admin only)
   *
   * Returns authentication events including logins, logouts, and failures.
   *
   * @param eventType - Filter by event type (LOGIN, LOGOUT, etc.)
   * @param username - Filter by username involved in the event
   * @param successOnly - Filter by success status (true=success, false=failure, undefined=all)
   * @param limit - Maximum entries to return
   * @param offset - Number of entries to skip for pagination
   */
  async getAuthAudit(
    eventType?: string,
    username?: string,
    successOnly?: boolean,
    limit: number = 50,
    offset: number = 0
  ): Promise<AuthAuditEntry[]> {
    try {
      mcpLogger.info('Getting auth audit log', { eventType, username, successOnly, limit, offset })

      const response = await this.mcpClient.callTool<{ audit_entries: AuthAuditEntry[] }>('get_auth_audit', {
        event_type: eventType,
        username,
        success_only: successOnly,
        limit,
        offset
      })

      if (!response.success) {
        mcpLogger.error('Failed to get auth audit', { error: response.error })
        return []
      }

      const entries = response.data?.audit_entries || []
      mcpLogger.info('Auth audit retrieved successfully', { count: entries.length })
      return entries
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      mcpLogger.error('Auth audit retrieval failed', { error: errorMessage })
      return []
    }
  }

  /**
   * Get agent audit log (admin only)
   *
   * Returns agent lifecycle events including installs, connections,
   * disconnections, and errors.
   */
  async getAgentAudit(filters: AgentAuditFilters = {}): Promise<AgentAuditResult> {
    try {
      mcpLogger.info('Getting agent audit log', filters)

      const response = await this.mcpClient.callTool<{
        audit_entries: AgentAuditEntry[]
        total: number
        truncated?: boolean
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
        return { entries: [], total: 0 }
      }

      const entries = response.data?.audit_entries || []
      const total = response.data?.total ?? entries.length
      const truncated = response.data?.truncated
      mcpLogger.info('Agent audit retrieved successfully', { count: entries.length, total, truncated })
      return { entries, total, truncated }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      mcpLogger.error('Agent audit retrieval failed', { error: errorMessage })
      return { entries: [], total: 0 }
    }
  }

}

/**
 * Hook to get Audit MCP Client
 *
 * Memoizes the client instance to avoid recreating on every render.
 */
export function useAuditMcpClient(): AuditMcpClient | null {
  try {
    const { client, isConnected } = useMCP()
    return useMemo(
      () => new AuditMcpClient(client, () => isConnected),
      [client, isConnected]
    )
  } catch (_error) {
    // useMCP will throw if not within MCPProvider
    mcpLogger.warn('Audit MCP Client not available - no MCP provider')
    return null
  }
}
