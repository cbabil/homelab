/**
 * Settings Provider
 *
 * Context provider for application settings management with MCP integration.
 * Provides settings state, functions, and database sync throughout the app.
 */

import React, { createContext, useContext } from 'react'
import { useSettings } from '@/hooks/useSettings'
import { UserSettings, SettingsUpdateResult } from '@/types/settings'

interface SettingsContextType {
  settings: UserSettings | null
  isLoading: boolean
  error: string | null
  isUsingDatabase: boolean
  updateSettings: (
    section: keyof Omit<UserSettings, 'lastUpdated' | 'version'>,
    updates: any
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