/**
 * useServerDeployment Hook
 *
 * Handles deploying to individual servers and status polling.
 */

import { useCallback } from 'react'
import { useMCP } from '@/providers/MCPProvider'
import { ServerConnection } from '@/types/server'
import { DeploymentConfig, DeploymentResult, ServerDeploymentStatus } from '@/types/deployment'
import { InstallationStatusData } from '../useInstallationStatus'
import { buildConfigPayload, parseStatusResponse } from './helpers'
import { deploymentLogger } from '@/services/systemLogger'

interface UseServerDeploymentOptions {
  config: DeploymentConfig
  updateServerStatus: (id: string, updates: Partial<ServerDeploymentStatus>) => void
}

export interface UseServerDeploymentReturn {
  deployToServer: (
    server: ServerConnection,
    appId: string,
    appName: string
  ) => Promise<{ success: boolean; installationId?: string; error?: string }>
}

export function useServerDeployment(
  options: UseServerDeploymentOptions
): UseServerDeploymentReturn {
  const { client } = useMCP()
  const { config, updateServerStatus } = options

  // Start polling for installation status
  const startStatusPolling = useCallback(
    (serverId: string, installationId: string) => {
      const pollInterval = setInterval(async () => {
        try {
          const statusResponse = await client.callTool<{
            success: boolean
            data?: InstallationStatusData
          }>('get_installation_status', { installation_id: installationId })

          if (statusResponse.success && statusResponse.data) {
            const statusToolResult = statusResponse.data as {
              success?: boolean
              data?: InstallationStatusData
            }
            const statusData = statusToolResult.data

            if (statusData) {
              const { status, progress } = parseStatusResponse(statusData)
              updateServerStatus(serverId, {
                status,
                progress,
                error: statusData.error_message,
              })

              if (['running', 'error', 'stopped'].includes(statusData.status)) {
                clearInterval(pollInterval)
              }
            }
          }
        } catch {
          // Continue polling on errors
        }
      }, 2000)

      // Clean up polling after 5 minutes max
      setTimeout(() => clearInterval(pollInterval), 5 * 60 * 1000)
    },
    [client, updateServerStatus]
  )

  // Deploy to a single server
  const deployToServer = useCallback(
    async (
      server: ServerConnection,
      appId: string,
      appName: string
    ): Promise<{ success: boolean; installationId?: string; error?: string }> => {
      updateServerStatus(server.id, { status: 'pulling', progress: 0 })

      try {
        const response = await client.callTool<DeploymentResult>('add_app', {
          server_id: server.id,
          app_id: appId,
          config: buildConfigPayload(config),
        })
        if (response.success && response.data) {
          const toolResult = response.data as {
            success?: boolean
            data?: { installation_id?: string }
            message?: string
            error?: string
          }

          if (!toolResult.success) {
            const errorMsg = toolResult.message || toolResult.error || 'Deployment failed'
            deploymentLogger.error('Deployment tool returned error', {
              appId,
              serverId: server.id,
              error: errorMsg,
            })
            updateServerStatus(server.id, { status: 'error', progress: 0, error: errorMsg })
            return { success: false, error: errorMsg }
          }

          const installationId = toolResult.data?.installation_id

          deploymentLogger.info('Deployment initiated on server', {
            appId,
            appName,
            serverId: server.id,
            serverName: server.name,
            installationId,
          })

          if (installationId) {
            startStatusPolling(server.id, installationId)
          }

          return { success: true, installationId }
        } else {
          const errorMsg = response.error || response.message || 'Deployment failed'
          updateServerStatus(server.id, { status: 'error', progress: 0, error: errorMsg })
          return { success: false, error: errorMsg }
        }
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : 'Unknown error'
        updateServerStatus(server.id, { status: 'error', progress: 0, error: errorMsg })
        return { success: false, error: errorMsg }
      }
    },
    [client, config, updateServerStatus, startStatusPolling]
  )

  return { deployToServer }
}
