/**
 * Retention Settings Hook
 *
 * Manages data retention settings state with validation,
 * preview operations, and secure deletion workflows.
 * Fetches settings from backend via MCP tools.
 */

import { useState, useEffect, useCallback, useRef } from 'react'
import { useMCP } from '@/providers/MCPProvider'
import { mcpLogger } from '@/services/systemLogger'
import {
  RetentionSettings,
  RETENTION_LIMITS,
  RetentionPreviewResult,
  RetentionOperationResult
} from '@/types/settings'
import {
  DEFAULT_RETENTION_SETTINGS,
  GetSettingsResponse
} from './retentionSettingsTypes'
import {
  validateRetentionSettings,
  parseSettingsResponse,
  getMockPreview,
  fetchCSRFToken,
  executeCleanup,
  executePreview,
  updateSettingsViaBackend
} from './retentionSettingsHelpers'

export function useRetentionSettings() {
  const [settings, setSettings] = useState<RetentionSettings | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isOperationInProgress, setIsOperationInProgress] = useState(false)
  const [previewResult, setPreviewResult] = useState<RetentionPreviewResult | null>(null)
  const [csrfToken, setCsrfToken] = useState<string | null>(null)

  const { client, isConnected } = useMCP()
  const mcpClientRef = useRef(client)

  useEffect(() => {
    mcpClientRef.current = client
  }, [client])

  const loadRetentionSettings = useCallback(async () => {
    try {
      setIsLoading(true)
      setError(null)

      if (!isConnected || !mcpClientRef.current) {
        mcpLogger.warn('[useRetentionSettings] MCP not connected, using defaults')
        setSettings(DEFAULT_RETENTION_SETTINGS)
        setIsLoading(false)
        return
      }

      const response = await mcpClientRef.current.callTool<GetSettingsResponse>(
        'get_retention_settings',
        { params: {} }
      )

      if (response.success) {
        const responseData = response.data as GetSettingsResponse
        setSettings(parseSettingsResponse(responseData))
        mcpLogger.info('[useRetentionSettings] Settings loaded from backend')
      } else {
        mcpLogger.warn('[useRetentionSettings] Failed to load from backend, using defaults')
        setSettings(DEFAULT_RETENTION_SETTINGS)
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load retention settings'
      setError(errorMessage)
      mcpLogger.error('[useRetentionSettings] Failed to load:', { error: err })
      setSettings(DEFAULT_RETENTION_SETTINGS)
    } finally {
      setIsLoading(false)
    }
  }, [isConnected])

  useEffect(() => {
    loadRetentionSettings()
  }, [loadRetentionSettings])

  const updateRetentionSettings = useCallback(
    async (updates: Partial<RetentionSettings>) => {
      if (!settings) return { success: false, error: 'Settings not loaded' }

      try {
        setError(null)
        const newSettings = { ...settings, ...updates }

        const validation = validateRetentionSettings(newSettings)
        if (!validation.valid) {
          setError(validation.error || null)
          return { success: false, error: validation.error }
        }

        if (isConnected && mcpClientRef.current) {
          const result = await updateSettingsViaBackend(mcpClientRef.current, newSettings)
          if (result.success) {
            setSettings(result.data || newSettings)
            return { success: true }
          }
          setError(result.error || null)
          return { success: false, error: result.error }
        }

        setSettings(newSettings)
        return { success: true }
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Update failed'
        setError(errorMessage)
        mcpLogger.error('[useRetentionSettings] Update failed:', { error: err })
        return { success: false, error: errorMessage }
      }
    },
    [settings, isConnected]
  )

  const getCSRFToken = useCallback(async (): Promise<string | null> => {
    if (!isConnected || !mcpClientRef.current) {
      mcpLogger.warn('[useRetentionSettings] MCP not connected, cannot get CSRF token')
      return null
    }
    const token = await fetchCSRFToken(mcpClientRef.current)
    setCsrfToken(token)
    return token
  }, [isConnected])

  const previewCleanup = useCallback(
    async (retentionType: string = 'access_logs'): Promise<RetentionOperationResult> => {
      if (!settings) {
        return { success: false, operation: 'preview', error: 'Settings not loaded' }
      }

      try {
        setIsOperationInProgress(true)
        setError(null)

        if (isConnected && mcpClientRef.current) {
          const result = await executePreview(mcpClientRef.current, retentionType)
          if (result.success && result.preview) {
            setPreviewResult(result.preview)
            return { success: true, operation: 'preview', preview: result.preview }
          }
          setError(result.error || null)
          return { success: false, operation: 'preview', error: result.error }
        }

        mcpLogger.warn('[useRetentionSettings] MCP not connected, using mock preview')
        const mockPreview = getMockPreview()
        setPreviewResult(mockPreview)
        return { success: true, operation: 'preview', preview: mockPreview }
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Preview failed'
        setError(errorMessage)
        mcpLogger.error('[useRetentionSettings] Preview exception', { error: err })
        return { success: false, operation: 'preview', error: errorMessage }
      } finally {
        setIsOperationInProgress(false)
      }
    },
    [settings, isConnected]
  )

  const performCleanup = useCallback(
    async (retentionType: string = 'access_logs'): Promise<RetentionOperationResult> => {
      if (!settings) {
        return { success: false, operation: 'execute', error: 'Settings not loaded' }
      }
      if (!isConnected || !mcpClientRef.current) {
        return { success: false, operation: 'execute', error: 'Backend not connected' }
      }

      try {
        setIsOperationInProgress(true)
        setError(null)

        const token = await getCSRFToken()
        if (!token) {
          return { success: false, operation: 'execute', error: 'Failed to obtain CSRF token' }
        }

        const result = await executeCleanup(mcpClientRef.current, retentionType, token)
        if (result.success) {
          setPreviewResult(null)
          setCsrfToken(null)
        } else {
          setError(result.error || null)
        }
        return result
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Cleanup failed'
        setError(errorMessage)
        mcpLogger.error('[useRetentionSettings] Cleanup exception', { error: err })
        return { success: false, operation: 'execute', error: errorMessage }
      } finally {
        setIsOperationInProgress(false)
      }
    },
    [settings, isConnected, getCSRFToken]
  )

  return {
    settings,
    isLoading,
    error,
    isOperationInProgress,
    previewResult,
    csrfToken,
    isBackendConnected: isConnected,
    loadRetentionSettings,
    updateRetentionSettings,
    previewCleanup,
    performCleanup,
    getCSRFToken,
    validateRetentionSettings,
    limits: RETENTION_LIMITS
  }
}
