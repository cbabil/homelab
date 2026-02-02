/**
 * Settings Provider
 *
 * Context provider for application settings management with MCP integration.
 * Provides settings state, functions, and database sync throughout the app.
 */

import React, { createContext, useContext } from 'react'
import { useSettings } from '@/hooks/useSettings'
import {
  UserSettings,
  SettingsUpdateResult,
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

type SettingsSectionKey = keyof Omit<UserSettings, 'lastUpdated' | 'version'>

interface SettingsContextType {
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

const SettingsContext = createContext<SettingsContextType | undefined>(undefined)

interface SettingsProviderProps {
  children: React.ReactNode
}

export function SettingsProvider({ children }: SettingsProviderProps) {
  const settingsHook = useSettings()

  return (
    <SettingsContext.Provider value={settingsHook}>
      {children}
    </SettingsContext.Provider>
  )
}

/**
 * Hook to use settings context
 */
export function useSettingsContext(): SettingsContextType {
  const context = useContext(SettingsContext)
  
  if (context === undefined) {
    throw new Error('useSettingsContext must be used within a SettingsProvider')
  }
  
  return context
}

// Export context for testing
export { SettingsContext }