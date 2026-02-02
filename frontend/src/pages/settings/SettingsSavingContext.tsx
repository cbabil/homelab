/**
 * Settings Saving Context
 *
 * Provides saving state across all settings tabs.
 */

import { createContext, useContext, useState, ReactNode } from 'react'

interface SettingsSavingContextType {
  isSaving: boolean
  setIsSaving: (saving: boolean) => void
}

const SettingsSavingContext = createContext<SettingsSavingContextType | null>(null)

export function SettingsSavingProvider({ children }: { children: ReactNode }) {
  const [isSaving, setIsSaving] = useState(false)

  return (
    <SettingsSavingContext.Provider value={{ isSaving, setIsSaving }}>
      {children}
    </SettingsSavingContext.Provider>
  )
}

export function useSettingsSaving() {
  const context = useContext(SettingsSavingContext)
  if (!context) {
    throw new Error('useSettingsSaving must be used within SettingsSavingProvider')
  }
  return context
}
