/**
 * Settings Hook
 *
 * Custom React hook for managing user settings state with MCP integration.
 * Provides settings access, updates, subscription management, and database sync.
 */

import { useState, useEffect, useCallback } from 'react'
import {
  UserSettings,
  SettingsUpdateResult,
  SessionTimeout,
  SecuritySettings,
  UISettings,
  SystemSettings,
  ApplicationSettings,
  NotificationSettings,
  ServerConnectionSettings,
  AgentConnectionSettings,
} from '@/types/settings'

// Type for section updates - maps section key to its partial type
type SettingsSectionUpdates = {
  security: Partial<SecuritySettings>
  ui: Partial<UISettings>
  system: Partial<SystemSettings>
  applications: Partial<ApplicationSettings>
  notifications: Partial<NotificationSettings>
  servers: Partial<ServerConnectionSettings>
  agent: Partial<AgentConnectionSettings>
}
import { settingsService } from '@/services/settingsService'
import { useSettingsMcpClient } from '@/services/settingsMcpClient'
import { mcpLogger } from '@/services/systemLogger'

type SettingsSectionKey = keyof Omit<UserSettings, 'lastUpdated' | 'version'>

interface UseSettingsReturn {
  settings: UserSettings | null
  isLoading: boolean
  error: string | null
  isUsingDatabase: boolean
  updateSettings: <K extends SettingsSectionKey>(
    section: K,
    updates: SettingsSectionUpdates[K]
  ) => Promise<SettingsUpdateResult>
  resetSettings: () => Promise<SettingsUpdateResult>
  syncFromDatabase: () => Promise<SettingsUpdateResult>
  getSessionTimeoutMs: () => number
}

/**
 * Hook for managing user settings with MCP database integration
 */
export function useSettings(userId: string = 'default'): UseSettingsReturn {
  const [settings, setSettings] = useState<UserSettings | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isUsingDatabase, setIsUsingDatabase] = useState(false)
  const mcpClient = useSettingsMcpClient()

  // Initialize settings on mount with MCP integration
  useEffect(() => {
    const initializeSettings = async () => {
      try {
        setIsLoading(true)
        setError(null)

        mcpLogger.info('Initializing settings with MCP integration', {
          hasMcpClient: !!mcpClient,
          userId
        })

        // Initialize with MCP client
        const initialSettings = await settingsService.initialize(mcpClient, userId)
        setSettings(initialSettings)
        setIsUsingDatabase(settingsService.isUsingDatabase())
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to load settings'
        setError(errorMessage)
        mcpLogger.error('Settings initialization error:', err)
      } finally {
        setIsLoading(false)
      }
    }

    initializeSettings()
  }, [mcpClient, userId])

  // Subscribe to settings changes
  useEffect(() => {
    const unsubscribe = settingsService.subscribe((updatedSettings) => {
      setSettings(updatedSettings)
      setError(null)
    })

    return unsubscribe
  }, [])

  // Sync from database function
  const syncFromDatabase = useCallback(async (): Promise<SettingsUpdateResult> => {
    try {
      setError(null)
      const result = await settingsService.syncFromDatabase()

      if (result.success) {
        setIsUsingDatabase(settingsService.isUsingDatabase())
      } else {
        setError(result.error || 'Failed to sync from database')
      }

      return result
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Sync failed'
      setError(errorMessage)
      return { success: false, error: errorMessage }
    }
  }, [])

  // Update settings function
  const updateSettings = useCallback(async <K extends SettingsSectionKey>(
    section: K,
    updates: SettingsSectionUpdates[K]
  ): Promise<SettingsUpdateResult> => {
    try {
      setError(null)
      const result = await settingsService.updateSettings(section, updates)

      if (!result.success) {
        setError(result.error || 'Failed to update settings')
      } else {
        // Update database usage status after successful update
        setIsUsingDatabase(settingsService.isUsingDatabase())
      }

      return result
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Update failed'
      setError(errorMessage)
      return { success: false, error: errorMessage }
    }
  }, [])

  // Reset settings function
  const resetSettings = useCallback(async (): Promise<SettingsUpdateResult> => {
    try {
      setError(null)
      const result = await settingsService.resetSettings()

      if (!result.success) {
        setError(result.error || 'Failed to reset settings')
      } else {
        setIsUsingDatabase(settingsService.isUsingDatabase())
      }

      return result
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Reset failed'
      setError(errorMessage)
      return { success: false, error: errorMessage }
    }
  }, [])

  // Get session timeout in milliseconds
  const getSessionTimeoutMs = useCallback((): number => {
    return settingsService.getSessionTimeoutMs()
  }, [])

  return {
    settings,
    isLoading,
    error,
    isUsingDatabase,
    updateSettings,
    resetSettings,
    syncFromDatabase,
    getSessionTimeoutMs
  }
}

/**
 * Hook specifically for session timeout settings
 */
export function useSessionTimeout() {
  const { settings, updateSettings, getSessionTimeoutMs } = useSettings()
  
  const updateSessionTimeout = useCallback(async (timeout: SessionTimeout) => {
    if (!settings?.security.session) {
      return { success: false, error: 'Settings not loaded' }
    }

    return await updateSettings('security', {
      session: {
        ...settings.security.session,
        timeout
      }
    })
  }, [settings?.security.session, updateSettings])

  return {
    timeout: settings?.security.session.timeout,
    timeoutMs: getSessionTimeoutMs(),
    updateTimeout: updateSessionTimeout,
    idleDetection: settings?.security.session.idleDetection,
    showWarningMinutes: settings?.security.session.showWarningMinutes,
    extendOnActivity: settings?.security.session.extendOnActivity
  }
}