/**
 * useAgentStatus Hook
 *
 * Custom hook for managing agent status and operations.
 * Provides agent installation, status monitoring, and command sending.
 */

import { useState, useCallback } from 'react'
import type { AgentInfo, AgentInstallResult } from '@/types/server'
import { useMCP } from '@/providers/MCPProvider'
import { updateLoadingState, updateAgentStatus, UseAgentStatusReturn } from './agentStatusHelpers'
import { useAgentLifecycle } from './useAgentLifecycle'

export function useAgentStatus(): UseAgentStatusReturn {
  const [agentStatuses, setAgentStatuses] = useState<Map<string, AgentInfo | null>>(new Map())
  const [isLoading, setIsLoading] = useState<Map<string, boolean>>(new Map())
  const { client, isConnected } = useMCP()

  const setLoading = useCallback((serverId: string, loading: boolean) => {
    setIsLoading((prev) => updateLoadingState(prev, serverId, loading))
  }, [])

  const setStatus = useCallback((serverId: string, agentInfo: AgentInfo | null) => {
    setAgentStatuses((prev) => updateAgentStatus(prev, serverId, agentInfo))
  }, [])

  const fetchAgentStatus = useCallback(
    async (serverId: string): Promise<AgentInfo | null> => {
      if (!isConnected) return null

      setLoading(serverId, true)
      try {
        const response = await client.callTool<{
          success: boolean
          data: AgentInfo | null
          message: string
        }>('get_agent_status', { server_id: serverId })

        const agentInfo = response.data?.data || null
        setStatus(serverId, agentInfo)
        return agentInfo
      } catch (error) {
        console.error(`Failed to fetch agent status for ${serverId}:`, error)
        setStatus(serverId, null)
        return null
      } finally {
        setLoading(serverId, false)
      }
    },
    [client, isConnected, setLoading, setStatus]
  )

  const installAgent = useCallback(
    async (serverId: string): Promise<{
      success: boolean
      data?: AgentInstallResult
      error?: string
      message?: string
    }> => {
      if (!isConnected) {
        return { success: false, error: 'NOT_CONNECTED', message: 'MCP not connected' }
      }

      setLoading(serverId, true)
      try {
        const response = await client.callTool<{
          success: boolean
          data: AgentInstallResult
          message: string
          error?: string
        }>('install_agent', { server_id: serverId })

        if (response.data?.success) {
          // Refresh agent status after installation
          await fetchAgentStatus(serverId)
          return { success: true, data: response.data.data }
        }
        return {
          success: false,
          error: response.data?.error,
          message: response.data?.message,
        }
      } catch (error) {
        console.error(`Failed to install agent on ${serverId}:`, error)
        return {
          success: false,
          error: 'UNKNOWN_ERROR',
          message: error instanceof Error ? error.message : 'Unknown error',
        }
      } finally {
        setLoading(serverId, false)
      }
    },
    [client, isConnected, fetchAgentStatus, setLoading]
  )

  const uninstallAgent = useCallback(
    async (serverId: string): Promise<boolean> => {
      if (!isConnected) return false

      setLoading(serverId, true)
      try {
        const response = await client.callTool<{
          success: boolean
          message: string
        }>('uninstall_agent', { server_id: serverId })

        if (response.data?.success) {
          setStatus(serverId, null)
          return true
        }
        return false
      } catch (error) {
        console.error(`Failed to uninstall agent on ${serverId}:`, error)
        return false
      } finally {
        setLoading(serverId, false)
      }
    },
    [client, isConnected, setLoading, setStatus]
  )

  const revokeAgentToken = useCallback(
    async (serverId: string): Promise<boolean> => {
      if (!isConnected) return false

      setLoading(serverId, true)
      try {
        const response = await client.callTool<{
          success: boolean
          message: string
        }>('revoke_agent_token', { server_id: serverId })

        if (response.data?.success) {
          setStatus(serverId, null)
          return true
        }
        return false
      } catch (error) {
        console.error(`Failed to revoke agent token on ${serverId}:`, error)
        return false
      } finally {
        setLoading(serverId, false)
      }
    },
    [client, isConnected, setLoading, setStatus]
  )

  const sendAgentCommand = useCallback(
    async (
      serverId: string,
      method: string,
      params?: Record<string, unknown>
    ): Promise<unknown> => {
      if (!isConnected) throw new Error('MCP not connected')

      const response = await client.callTool<{
        success: boolean
        data: unknown
        message: string
        error?: string
      }>('send_agent_command', {
        server_id: serverId,
        method,
        params,
      })

      if (!response.data?.success) {
        throw new Error(response.data?.message || 'Agent command failed')
      }

      return response.data.data
    },
    [client, isConnected]
  )

  const refreshAllAgentStatuses = useCallback(
    async (serverIds: string[]): Promise<void> => {
      await Promise.all(serverIds.map((id) => fetchAgentStatus(id)))
    },
    [fetchAgentStatus]
  )

  // Lifecycle methods from separate hook
  const { checkAgentHealth, pingAgent, checkAgentVersion, triggerAgentUpdate } =
    useAgentLifecycle(setLoading, fetchAgentStatus)

  return {
    agentStatuses,
    isLoading,
    fetchAgentStatus,
    installAgent,
    uninstallAgent,
    revokeAgentToken,
    sendAgentCommand,
    refreshAllAgentStatuses,
    // Lifecycle methods
    checkAgentHealth,
    pingAgent,
    checkAgentVersion,
    triggerAgentUpdate,
  }
}
