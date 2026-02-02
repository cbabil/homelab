/**
 * Agent Status Helpers
 *
 * Types and helper functions for agent status management.
 */

import type { AgentInstallResult, AgentHealthInfo, AgentVersionInfo, AgentPingResult, AgentInfo } from '@/types/server'

export interface AgentInstallResponse {
  success: boolean
  data?: AgentInstallResult
  error?: string
  message?: string
}

export interface UseAgentStatusReturn {
  agentStatuses: Map<string, AgentInfo | null>
  isLoading: Map<string, boolean>
  fetchAgentStatus: (serverId: string) => Promise<AgentInfo | null>
  installAgent: (serverId: string) => Promise<AgentInstallResponse>
  uninstallAgent: (serverId: string) => Promise<boolean>
  revokeAgentToken: (serverId: string) => Promise<boolean>
  sendAgentCommand: (
    serverId: string,
    method: string,
    params?: Record<string, unknown>
  ) => Promise<unknown>
  refreshAllAgentStatuses: (serverIds: string[]) => Promise<void>
  checkAgentHealth: (serverId: string) => Promise<AgentHealthInfo | null>
  pingAgent: (serverId: string, timeout?: number) => Promise<AgentPingResult | null>
  checkAgentVersion: (serverId: string) => Promise<AgentVersionInfo | null>
  triggerAgentUpdate: (serverId: string) => Promise<boolean>
}

/** Update loading state for a server */
export function updateLoadingState(
  prev: Map<string, boolean>,
  serverId: string,
  loading: boolean
): Map<string, boolean> {
  return new Map(prev).set(serverId, loading)
}

/** Update agent status for a server */
export function updateAgentStatus(
  prev: Map<string, AgentInfo | null>,
  serverId: string,
  agentInfo: AgentInfo | null
): Map<string, AgentInfo | null> {
  return new Map(prev).set(serverId, agentInfo)
}
