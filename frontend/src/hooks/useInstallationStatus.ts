/**
 * useInstallationStatus Hook
 *
 * Polls installation status during deployment.
 * Stops on terminal states (running, error, stopped).
 */

import { useState, useEffect, useCallback, useRef } from 'react'
import { useMCP } from '@/providers/MCPProvider'

export type InstallationStatus =
  | 'pending'
  | 'pulling'
  | 'creating'
  | 'running'
  | 'stopped'
  | 'error'

export interface InstallationStatusData {
  id: string
  status: InstallationStatus
  app_id: string
  server_id: string
  container_name?: string
  container_id?: string
  error_message?: string
  installed_at?: string
  started_at?: string
  step_durations?: {
    pulling?: number
    creating?: number
    starting?: number
  }
}

export interface UseInstallationStatusOptions {
  /** Polling interval in ms (default: 2000) */
  pollInterval?: number
  /** Callback when installation completes successfully */
  onComplete?: (data: InstallationStatusData) => void
  /** Callback when installation fails */
  onError?: (error: string, data?: InstallationStatusData) => void
  /** Callback on each status update */
  onStatusChange?: (status: InstallationStatus, data: InstallationStatusData) => void
}

export interface UseInstallationStatusReturn {
  /** Current installation status data */
  statusData: InstallationStatusData | null
  /** Whether polling is active */
  isPolling: boolean
  /** Last error from polling */
  error: string | null
  /** Start polling for an installation */
  startPolling: (installationId: string) => void
  /** Stop polling */
  stopPolling: () => void
  /** Reset state */
  reset: () => void
}

const TERMINAL_STATES: InstallationStatus[] = ['running', 'stopped', 'error']
const DEFAULT_POLL_INTERVAL = 2000

export function useInstallationStatus(
  options: UseInstallationStatusOptions = {}
): UseInstallationStatusReturn {
  const {
    pollInterval = DEFAULT_POLL_INTERVAL,
    onComplete,
    onError,
    onStatusChange
  } = options

  const { client, isConnected } = useMCP()

  const [statusData, setStatusData] = useState<InstallationStatusData | null>(null)
  const [isPolling, setIsPolling] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Use refs to track current polling state without causing re-renders
  const installationIdRef = useRef<string | null>(null)
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const lastStatusRef = useRef<InstallationStatus | null>(null)

  const stopPolling = useCallback(() => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current)
      pollIntervalRef.current = null
    }
    setIsPolling(false)
    installationIdRef.current = null
  }, [])

  const reset = useCallback(() => {
    stopPolling()
    setStatusData(null)
    setError(null)
    lastStatusRef.current = null
  }, [stopPolling])

  const fetchStatus = useCallback(async () => {
    const installationId = installationIdRef.current
    if (!installationId || !isConnected) {
      return
    }

    try {
      const response = await client.callTool<InstallationStatusData>('get_installation_status', {
        installation_id: installationId
      })

      if (response.success && response.data) {
        const data = response.data
        setStatusData(data)
        setError(null)

        // Notify on status change
        if (data.status !== lastStatusRef.current) {
          lastStatusRef.current = data.status
          onStatusChange?.(data.status, data)
        }

        // Handle terminal states
        if (TERMINAL_STATES.includes(data.status)) {
          stopPolling()

          if (data.status === 'running') {
            onComplete?.(data)
          } else if (data.status === 'error') {
            const errorMsg = data.error_message || 'Installation failed'
            setError(errorMsg)
            onError?.(errorMsg, data)
          }
        }
      } else {
        const errorMsg = response.error || response.message || 'Failed to get status'
        setError(errorMsg)
        // Don't stop polling on transient errors
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to poll status'
      setError(errorMsg)
      // Don't stop polling on transient errors - let caller decide
    }
  }, [isConnected, client, onComplete, onError, onStatusChange, stopPolling])

  const startPolling = useCallback((installationId: string) => {
    // Stop any existing polling
    stopPolling()

    installationIdRef.current = installationId
    lastStatusRef.current = null
    setError(null)
    setIsPolling(true)

    // Fetch immediately
    fetchStatus()

    // Then poll at interval
    pollIntervalRef.current = setInterval(fetchStatus, pollInterval)
  }, [stopPolling, fetchStatus, pollInterval])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current)
      }
    }
  }, [])

  return {
    statusData,
    isPolling,
    error,
    startPolling,
    stopPolling,
    reset
  }
}
