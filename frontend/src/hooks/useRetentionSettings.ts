/**
 * Retention Settings Hook
 *
 * Manages data retention settings state with validation,
 * preview operations, and secure deletion workflows.
 */

import { useState, useEffect, useCallback } from 'react'
import { settingsService } from '@/services/settingsService'
import {
  DataRetentionSettings,
  RETENTION_LIMITS,
  RetentionPreviewResult,
  RetentionOperationResult,
  RetentionOperationType
} from '@/types/settings'

export function useRetentionSettings() {
  const [settings, setSettings] = useState<DataRetentionSettings | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isOperationInProgress, setIsOperationInProgress] = useState(false)
  const [previewResult, setPreviewResult] = useState<RetentionPreviewResult | null>(null)

  // Load initial retention settings
  useEffect(() => {
    loadRetentionSettings()
  }, [])

  const loadRetentionSettings = useCallback(async () => {
    try {
      setIsLoading(true)
      setError(null)

      await settingsService.initialize()
      const userSettings = settingsService.getSettings()
      setSettings(userSettings.system.dataRetention)
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to load retention settings'
      setError(errorMessage)
      console.error('[useRetentionSettings] Failed to load:', error)
    } finally {
      setIsLoading(false)
    }
  }, [])

  const updateRetentionSettings = useCallback(async (
    updates: Partial<DataRetentionSettings>
  ) => {
    if (!settings) return

    try {
      setError(null)

      // Validate before updating
      const newSettings = { ...settings, ...updates }
      const isValid = validateRetentionSettings(newSettings)

      if (!isValid.valid) {
        setError(isValid.error)
        return { success: false, error: isValid.error }
      }

      const result = await settingsService.updateSettings('system', {
        dataRetention: newSettings
      })

      if (result.success && result.settings) {
        setSettings(result.settings.system.dataRetention)
        console.log('[useRetentionSettings] Settings updated successfully')
        return { success: true }
      } else {
        setError(result.error || 'Failed to update settings')
        return { success: false, error: result.error }
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Update failed'
      setError(errorMessage)
      console.error('[useRetentionSettings] Update failed:', error)
      return { success: false, error: errorMessage }
    }
  }, [settings])

  // Validate retention settings
  const validateRetentionSettings = (retentionSettings: DataRetentionSettings) => {
    if (retentionSettings.logRetentionDays < RETENTION_LIMITS.LOG_MIN_DAYS ||
        retentionSettings.logRetentionDays > RETENTION_LIMITS.LOG_MAX_DAYS) {
      return {
        valid: false,
        error: `Log retention must be between ${RETENTION_LIMITS.LOG_MIN_DAYS}-${RETENTION_LIMITS.LOG_MAX_DAYS} days`
      }
    }

    if (retentionSettings.otherDataRetentionDays < RETENTION_LIMITS.OTHER_DATA_MIN_DAYS ||
        retentionSettings.otherDataRetentionDays > RETENTION_LIMITS.OTHER_DATA_MAX_DAYS) {
      return {
        valid: false,
        error: `Other data retention must be between ${RETENTION_LIMITS.OTHER_DATA_MIN_DAYS}-${RETENTION_LIMITS.OTHER_DATA_MAX_DAYS} days`
      }
    }

    return { valid: true }
  }

  // Mock preview operation - would integrate with backend MCP tools
  const previewCleanup = useCallback(async (): Promise<RetentionOperationResult> => {
    if (!settings) {
      return { success: false, operation: 'preview', error: 'Settings not loaded' }
    }

    try {
      setIsOperationInProgress(true)
      setError(null)

      // Mock preview result - in real implementation would call backend
      const mockPreview: RetentionPreviewResult = {
        logEntriesAffected: Math.floor(Math.random() * 1000),
        otherDataAffected: Math.floor(Math.random() * 500),
        estimatedSpaceFreed: `${(Math.random() * 100).toFixed(1)} MB`,
        affectedTables: ['log_entries', 'system_events', 'audit_logs']
      }

      setPreviewResult(mockPreview)

      return {
        success: true,
        operation: 'preview',
        preview: mockPreview
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Preview failed'
      setError(errorMessage)
      return { success: false, operation: 'preview', error: errorMessage }
    } finally {
      setIsOperationInProgress(false)
    }
  }, [settings])

  return {
    settings,
    isLoading,
    error,
    isOperationInProgress,
    previewResult,
    loadRetentionSettings,
    updateRetentionSettings,
    previewCleanup,
    validateRetentionSettings,
    // Validation limits for UI
    limits: RETENTION_LIMITS
  }
}