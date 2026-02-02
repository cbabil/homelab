/**
 * useDeploymentValidation Hook
 *
 * Handles preflight checks and config validation for deployments.
 */

import { useCallback } from 'react'
import { useMCP } from '@/providers/MCPProvider'
import { useToast } from '@/components/ui/Toast'
import { App } from '@/types/app'
import { ServerConnection } from '@/types/server'
import {
  DeploymentConfig,
  PreflightResult,
  ValidationResult,
} from '@/types/deployment'
import { buildConfigPayload } from './helpers'
import { deploymentLogger } from '@/services/systemLogger'

interface ValidationState {
  selectedApp: App | null
  selectedServerIds: string[]
  config: DeploymentConfig
  setPreflightResult: (result: PreflightResult | null) => void
  setIsRunningPreflight: (running: boolean) => void
  setValidationResult: (result: ValidationResult | null) => void
  setIsValidating: (validating: boolean) => void
  setError: (error: string | null) => void
}

export interface UseDeploymentValidationReturn {
  validateConfig: () => Promise<boolean>
  runPreflight: (servers: ServerConnection[]) => Promise<boolean>
}

export function useDeploymentValidation(
  state: ValidationState
): UseDeploymentValidationReturn {
  const { client, isConnected } = useMCP()
  const { addToast } = useToast()

  const {
    selectedApp,
    selectedServerIds,
    config,
    setPreflightResult,
    setIsRunningPreflight,
    setValidationResult,
    setIsValidating,
    setError,
  } = state

  const validateConfig = useCallback(async (): Promise<boolean> => {
    if (!selectedApp) return false
    if (!isConnected) return true // Skip validation if not connected

    setIsValidating(true)
    setError(null)

    try {
      const response = await client.callTool<ValidationResult>(
        'validate_deployment_config',
        { app_id: selectedApp.id, config: buildConfigPayload(config) }
      )

      if (response.success && response.data) {
        setValidationResult(response.data)
        if (!response.data.valid) {
          const errorMsg = response.data.errors.join(', ')
          setError(errorMsg)
          addToast({
            type: 'error',
            title: 'Config Validation Failed',
            message: errorMsg,
            duration: 5000,
          })
          return false
        }
        if (response.data.warnings.length > 0) {
          addToast({
            type: 'warning',
            title: 'Config Warnings',
            message: response.data.warnings.join(', '),
            duration: 5000,
          })
        }
        return true
      }
      return true // If validation service unavailable, proceed anyway
    } catch (err) {
      const errorMsg =
        err instanceof Error ? err.message : 'Validation service unavailable'
      addToast({
        type: 'warning',
        title: 'Validation Skipped',
        message: errorMsg,
        duration: 4000,
      })
      return true
    } finally {
      setIsValidating(false)
    }
  }, [
    selectedApp,
    isConnected,
    client,
    config,
    addToast,
    setValidationResult,
    setIsValidating,
    setError,
  ])

  const runPreflight = useCallback(
    async (servers: ServerConnection[]): Promise<boolean> => {
      if (!selectedApp || selectedServerIds.length === 0) {
        setError('Please select at least one server')
        return false
      }

      if (!isConnected) return true // Skip preflight if not connected

      const firstServerId = selectedServerIds[0]
      const server = servers.find((s) => s.id === firstServerId)
      if (!server) {
        setError('Selected server not found')
        return false
      }

      setIsRunningPreflight(true)
      setError(null)

      try {
        const response = await client.callTool<PreflightResult>(
          'run_preflight_checks',
          {
            server_id: firstServerId,
            app_id: selectedApp.id,
            config: buildConfigPayload(config),
          }
        )

        if (response.success && response.data) {
          setPreflightResult(response.data)
          if (!response.data.passed) {
            const failedChecks = response.data.checks.filter((c) => !c.passed)
            const errorMsg = failedChecks.map((c) => c.message).join(', ')
            setError(errorMsg)
            addToast({
              type: 'error',
              title: 'Pre-flight Checks Failed',
              message: `${failedChecks.length} check(s) failed`,
              duration: 5000,
            })
            deploymentLogger.warn('Pre-flight checks failed', {
              appId: selectedApp.id,
              appName: selectedApp.name,
              serverId: firstServerId,
              serverName: server.name,
              failedChecks: failedChecks.map((c) => c.name),
            })
            return false
          }
          addToast({
            type: 'success',
            title: 'Pre-flight Checks Passed',
            message: `${response.data.checks.length} checks passed`,
            duration: 3000,
          })
          deploymentLogger.info('Pre-flight checks passed', {
            appId: selectedApp.id,
            appName: selectedApp.name,
            serverId: firstServerId,
            serverName: server.name,
            checksCount: response.data.checks.length,
          })
          return true
        }
        addToast({
          type: 'warning',
          title: 'Pre-flight Skipped',
          message: 'Could not run pre-flight checks. Proceed with caution.',
          duration: 4000,
        })
        return true
      } catch (err) {
        const errorMsg =
          err instanceof Error ? err.message : 'Pre-flight check failed'
        setError(errorMsg)
        addToast({
          type: 'error',
          title: 'Pre-flight Error',
          message: errorMsg,
          duration: 5000,
        })
        return false
      } finally {
        setIsRunningPreflight(false)
      }
    },
    [
      selectedApp,
      selectedServerIds,
      isConnected,
      client,
      config,
      addToast,
      setPreflightResult,
      setIsRunningPreflight,
      setError,
    ]
  )

  return { validateConfig, runPreflight }
}
