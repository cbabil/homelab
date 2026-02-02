/**
 * Session MCP Client
 *
 * MCP client for session operations (list, terminate, etc.).
 * Provides type-safe interface for managing user sessions from the backend.
 */

import { useMCP } from '@/providers/MCPProvider'
import { mcpLogger } from '@/services/systemLogger'

// Backend session type (matches SessionListResponse from backend)
export interface BackendSession {
  id: string
  user_id: string
  username: string | null
  ip_address: string | null
  user_agent: string | null
  created_at: string  // ISO string
  expires_at: string
  last_activity: string
  status: 'active' | 'idle' | 'expired' | 'terminated'
  is_current: boolean
}

// Response type for list_sessions
interface ListSessionsResponse {
  success: boolean
  data?: BackendSession[]
  message?: string
  error?: string
}

// Response type for delete_session
interface DeleteSessionResponse {
  success: boolean
  data?: { count: number }
  message?: string
  error?: string
}

/**
 * MCP-based Session Client
 *
 * Handles all session operations through the backend MCP tools
 * with proper error handling and type safety.
 */
export class SessionMcpClient {
  private mcpClient: ReturnType<typeof useMCP>['client']
  private isConnectedFn: () => boolean

  constructor(mcpClient: ReturnType<typeof useMCP>['client'], isConnected: () => boolean) {
    this.mcpClient = mcpClient
    this.isConnectedFn = isConnected
    mcpLogger.info('Session MCP Client initialized')
  }

  /**
   * Get sessions list
   *
   * @param userId - Filter by user ID (admin can specify other users)
   * @param status - Filter by session status
   */
  async getSessions(
    userId?: string,
    status?: 'active' | 'idle' | 'expired' | 'terminated'
  ): Promise<BackendSession[]> {
    try {
      mcpLogger.info('Getting sessions list', { userId, status })

      // Build inner params object
      const innerParams: Record<string, unknown> = {}
      if (userId) innerParams.user_id = userId
      if (status) innerParams.status = status

      // Backend SessionTools expects { params: {...} } structure
      const response = await this.mcpClient.callTool<ListSessionsResponse>('list_sessions', { params: innerParams })

      if (!response.success) {
        mcpLogger.error('Failed to get sessions', { error: response.error })
        return []
      }

      // Handle the response data structure
      const responseData = response.data as ListSessionsResponse
      const sessions = responseData?.data || []
      mcpLogger.info('Sessions retrieved successfully', { count: sessions.length })
      return sessions
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      mcpLogger.error('Sessions retrieval failed', { error: errorMessage })
      return []
    }
  }

  /**
   * Delete/terminate a session
   *
   * @param sessionId - Session ID to terminate
   */
  async deleteSession(sessionId: string): Promise<{ success: boolean; count: number }> {
    try {
      mcpLogger.info('Deleting session', { sessionId })

      // Backend SessionTools expects { params: {...} } structure
      const response = await this.mcpClient.callTool<DeleteSessionResponse>('delete_session', {
        params: { session_id: sessionId }
      })

      if (!response.success) {
        mcpLogger.error('Failed to delete session', { error: response.error })
        return { success: false, count: 0 }
      }

      const responseData = response.data as DeleteSessionResponse
      const count = responseData?.data?.count || 0
      mcpLogger.info('Session deleted successfully', { sessionId, count })
      return { success: true, count }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      mcpLogger.error('Session deletion failed', { error: errorMessage })
      return { success: false, count: 0 }
    }
  }

  /**
   * Delete all sessions for current user (except current session)
   */
  async deleteAllSessions(excludeCurrent: boolean = true): Promise<{ success: boolean; count: number }> {
    try {
      mcpLogger.info('Deleting all sessions', { excludeCurrent })

      // Backend SessionTools expects { params: {...} } structure
      const response = await this.mcpClient.callTool<DeleteSessionResponse>('delete_session', {
        params: { all: true, exclude_current: excludeCurrent }
      })

      if (!response.success) {
        mcpLogger.error('Failed to delete all sessions', { error: response.error })
        return { success: false, count: 0 }
      }

      const responseData = response.data as DeleteSessionResponse
      const count = responseData?.data?.count || 0
      mcpLogger.info('All sessions deleted successfully', { count })
      return { success: true, count }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      mcpLogger.error('Delete all sessions failed', { error: errorMessage })
      return { success: false, count: 0 }
    }
  }

  /**
   * Check if the MCP client is connected
   */
  isConnected(): boolean {
    return this.isConnectedFn()
  }
}

/**
 * Hook to get Session MCP Client
 */
export function useSessionMcpClient(): SessionMcpClient | null {
  try {
    const { client, isConnected } = useMCP()
    return new SessionMcpClient(client, () => isConnected)
  } catch (_error) {
    // useMCP will throw if not within MCPProvider
    mcpLogger.warn('Session MCP Client not available - no MCP provider')
    return null
  }
}
