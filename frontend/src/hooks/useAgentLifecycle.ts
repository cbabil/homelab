/**
 * useAgentLifecycle Hook
 *
 * Hook for agent lifecycle operations (health, ping, version, update).
 */

import { useCallback } from 'react'
import type { AgentHealthInfo, AgentVersionInfo, AgentPingResult } from '@/types/server'
import { useMCP } from '@/providers/MCPProvider'

interface UseAgentLifecycleReturn {
  checkAgentHealth: (serverId: string) => Promise<AgentHealthInfo | null>
  pingAgent: (serverId: string, timeout?: number) => Promise<AgentPingResult | null>
  checkAgentVersion: (serverId: string) => Promise<AgentVersionInfo | null>
  triggerAgentUpdate: (serverId: string) => Promise<boolean>
}

export function useAgentLifecycle(
  setLoading: (serverId: string, loading: boolean) => void,
  fetchAgentStatus: (serverId: string) => Promise<unknown>
): UseAgentLifecycleReturn {
  const { client, isConnected } = useMCP()

  const checkAgentHealth = useCallback(async (serverId: string): Promise<AgentHealthInfo | null> => {
    if (!isConnected) return null
    try {
      const response = await client.callTool<{ success: boolean; data: AgentHealthInfo }>(
        'check_agent_health', { server_id: serverId }
      )
      return response.data?.success ? response.data.data : null
    } catch { return null }
  }, [client, isConnected])

  const pingAgent = useCallback(async (serverId: string, timeout = 5): Promise<AgentPingResult | null> => {
    if (!isConnected) return null
    try {
      const response = await client.callTool<{ data: AgentPingResult }>(
        'ping_agent', { server_id: serverId, timeout }
      )
      return response.data?.data || null
    } catch { return null }
  }, [client, isConnected])

  const checkAgentVersion = useCallback(async (serverId: string): Promise<AgentVersionInfo | null> => {
    if (!isConnected) return null
    try {
      const response = await client.callTool<{ success: boolean; data: AgentVersionInfo }>(
        'check_agent_version', { server_id: serverId }
      )
      return response.data?.success ? response.data.data : null
    } catch { return null }
  }, [client, isConnected])

  const triggerAgentUpdate = useCallback(async (serverId: string): Promise<boolean> => {
    if (!isConnected) return false
    setLoading(serverId, true)
    try {
      const response = await client.callTool<{ success: boolean; message: string }>(
        'trigger_agent_update', { server_id: serverId }
      )
      if (response.data?.success) {
        await fetchAgentStatus(serverId)
        return true
      }
      return false
    } catch (error) {
      console.error(`Failed to trigger agent update for ${serverId}:`, error)
      return false
    } finally {
      setLoading(serverId, false)
    }
  }, [client, isConnected, fetchAgentStatus, setLoading])

  return { checkAgentHealth, pingAgent, checkAgentVersion, triggerAgentUpdate }
}
