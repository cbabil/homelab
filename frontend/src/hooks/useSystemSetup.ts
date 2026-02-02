/**
 * System Setup Hook
 *
 * Checks if the system needs initial setup (no admin user exists).
 * Used to redirect to setup page on first launch.
 */

import { useState, useEffect, useCallback } from 'react'
import { useMCP } from '@/providers/MCPProvider'

interface SystemSetupStatus {
  needsSetup: boolean
  isLoading: boolean
  error: string | null
  refetch: () => Promise<void>
}

interface CheckSystemSetupData {
  needs_setup: boolean
  is_setup: boolean
  app_name: string
}

interface CheckSystemSetupResponse {
  success: boolean
  data: CheckSystemSetupData
}

export function useSystemSetup(): SystemSetupStatus {
  const { client, isConnected } = useMCP()
  const [needsSetup, setNeedsSetup] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [hasChecked, setHasChecked] = useState(false)

  const checkSetup = useCallback(async () => {
    if (!isConnected) {
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const result = await client.callTool<CheckSystemSetupResponse>(
        'get_system_setup',
        {}
      )

      // result.data is the backend's full response {success, data}
      // result.data.data is the actual setup data {needs_setup, is_setup, app_name}
      if (result.success && result.data?.success && result.data?.data) {
        setNeedsSetup(result.data.data.needs_setup)
      } else {
        setError(result.message || 'Failed to check system setup')
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to check system status'
      setError(errorMessage)
    } finally {
      setIsLoading(false)
      setHasChecked(true)
    }
  }, [client, isConnected])

  // Only check setup ONCE on initial mount when connected
  // Don't re-check on subsequent isConnected changes to avoid flickering
  useEffect(() => {
    if (isConnected && !hasChecked) {
      checkSetup()
    }
  }, [isConnected, hasChecked, checkSetup])

  // Manual refetch resets hasChecked to allow re-checking
  const refetch = useCallback(async () => {
    setHasChecked(false)
    await checkSetup()
  }, [checkSetup])

  return {
    needsSetup,
    isLoading,
    error,
    refetch
  }
}
