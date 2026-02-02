/**
 * useDeploymentActions Hook
 *
 * Handles deployment orchestration, cleanup, and retry actions.
 */

import { useCallback } from 'react'
import { useMCP } from '@/providers/MCPProvider'
import { useToast } from '@/components/ui/Toast'
import { App } from '@/types/app'
import { ServerConnection } from '@/types/server'
import {
  DeploymentConfig,
  DeploymentResult,
  DeploymentStep,
  ServerDeploymentStatus,
} from '@/types/deployment'
import { useServerDeployment } from './useServerDeployment'
import { deploymentLogger } from '@/services/systemLogger'

interface DeploymentActionsState {
  selectedApp: App | null
  selectedServerIds: string[]
  config: DeploymentConfig
  deploymentResult: DeploymentResult | null
  setStep: (step: DeploymentStep) => void
  setIsDeploying: (deploying: boolean) => void
  setError: (error: string | null) => void
  setDeploymentResult: (result: DeploymentResult | null) => void
  setTargetServerStatuses: (statuses: ServerDeploymentStatus[]) => void
  updateServerStatus: (id: string, updates: Partial<ServerDeploymentStatus>) => void
}

export interface UseDeploymentActionsReturn {
  deploy: (servers: ServerConnection[]) => Promise<boolean>
  cleanup: () => Promise<boolean>
  retryDeployment: (servers: ServerConnection[]) => Promise<boolean>
}

export function useDeploymentActions(
  state: DeploymentActionsState
): UseDeploymentActionsReturn {
  const { client, isConnected } = useMCP()
  const { addToast } = useToast()

  const {
    selectedApp,
    selectedServerIds,
    config,
    deploymentResult,
    setStep,
    setIsDeploying,
    setError,
    setDeploymentResult,
    setTargetServerStatuses,
    updateServerStatus,
  } = state

  const { deployToServer } = useServerDeployment({
    config,
    updateServerStatus,
  })

  const deploy = useCallback(
    async (servers: ServerConnection[]): Promise<boolean> => {
      if (!selectedApp || selectedServerIds.length === 0) {
        setError('Please select at least one server')
        return false
      }

      if (!isConnected) {
        setError('Not connected to MCP server')
        addToast({
          type: 'error',
          title: 'Connection Error',
          message: 'Not connected to the backend server',
          duration: 4000,
        })
        return false
      }

      const selectedServers = servers.filter((s) => selectedServerIds.includes(s.id))
      if (selectedServers.length === 0) {
        setError('Selected servers not found')
        return false
      }

      const invalidServers = selectedServers.filter(
        (s) => s.status !== 'connected' || !s.docker_installed
      )
      if (invalidServers.length > 0) {
        const names = invalidServers.map((s) => s.name).join(', ')
        setError(`Some servers are not ready: ${names}`)
        addToast({
          type: 'error',
          title: 'Servers Not Ready',
          message: `${invalidServers.length} server(s) are offline or missing Docker`,
          duration: 5000,
        })
        return false
      }

      setIsDeploying(true)
      setError(null)
      setStep('success')

      const initialStatuses: ServerDeploymentStatus[] = selectedServers.map((s) => ({
        serverId: s.id,
        serverName: s.name,
        progress: 0,
        status: 'pending',
      }))
      setTargetServerStatuses(initialStatuses)

      deploymentLogger.info('Multi-server deployment started', {
        appId: selectedApp.id,
        appName: selectedApp.name,
        serverCount: selectedServers.length,
        serverNames: selectedServers.map((s) => s.name),
        config: {
          ports: config.ports,
          volumes: config.volumes,
          envCount: config.env ? Object.keys(config.env).length : 0,
        },
      })

      let anySuccess = false
      let firstResult: DeploymentResult | null = null
      const errors: { serverName: string; error: string }[] = []

      for (const server of selectedServers) {
        const result = await deployToServer(server, selectedApp.id, selectedApp.name)
        if (result.success && !firstResult) {
          firstResult = {
            success: true,
            installationId: result.installationId,
            serverId: server.id,
            appId: selectedApp.id,
          }
          anySuccess = true
        } else if (!result.success && result.error) {
          errors.push({ serverName: server.name, error: result.error })
        }
      }

      if (firstResult) {
        setDeploymentResult(firstResult)
      }
      setIsDeploying(false)

      if (anySuccess) {
        addToast({
          type: 'success',
          title: 'Deployment Started',
          message: `${selectedApp.name} is being installed on ${selectedServers.length} server(s)`,
          duration: 5000,
        })
        return true
      } else {
        setStep('error')
        // Show specific error if only one server, otherwise suggest checking logs
        const errorMessage = errors.length === 1
          ? errors[0].error
          : `Deployment failed on ${errors.length} server(s). Check the audit logs for details.`
        setError(errorMessage)
        addToast({
          type: 'error',
          title: 'Deployment Failed',
          message: errorMessage,
          duration: 6000,
        })
        return false
      }
    },
    [
      selectedApp,
      selectedServerIds,
      isConnected,
      config,
      addToast,
      deployToServer,
      setStep,
      setIsDeploying,
      setError,
      setDeploymentResult,
      setTargetServerStatuses,
    ]
  )

  const cleanup = useCallback(async (): Promise<boolean> => {
    if (selectedServerIds.length === 0 || !deploymentResult?.installationId) {
      return false
    }
    if (!isConnected) return false

    const serverId = selectedServerIds[0]

    try {
      const response = await client.callTool<{ message: string }>(
        'cleanup_failed_deployment',
        { server_id: serverId, installation_id: deploymentResult.installationId }
      )

      if (response.success) {
        addToast({
          type: 'info',
          title: 'Cleanup Complete',
          message: response.data?.message || 'Failed deployment cleaned up',
          duration: 4000,
        })
        deploymentLogger.info('Deployment cleanup completed', {
          serverId,
          installationId: deploymentResult.installationId,
        })
        return true
      }
      return false
    } catch {
      deploymentLogger.error('Deployment cleanup failed', {
        serverId,
        installationId: deploymentResult?.installationId,
      })
      return false
    }
  }, [selectedServerIds, deploymentResult, isConnected, client, addToast])

  const retryDeployment = useCallback(
    async (servers: ServerConnection[]): Promise<boolean> => {
      setError(null)
      setDeploymentResult(null)
      setTargetServerStatuses(
        servers.map((s) => ({
          serverId: s.id,
          serverName: s.name,
          status: 'pending' as const,
          progress: 0,
        }))
      )
      return deploy(servers)
    },
    [deploy, setError, setDeploymentResult, setTargetServerStatuses]
  )

  return { deploy, cleanup, retryDeployment }
}
