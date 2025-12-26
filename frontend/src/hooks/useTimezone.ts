/**
 * Timezone Hook
 *
 * Custom React hook for managing timezone functionality.
 * Provides timezone service initialization and settings integration.
 */

import { useState, useEffect, useCallback } from 'react'
import { timezoneService } from '@/services/timezoneService'
import { useSettingsContext } from '@/providers/SettingsProvider'
import { TimezoneInfo, TimezoneGroup } from '@/types/timezone'

interface UseTimezoneReturn {
  isInitialized: boolean
  isLoading: boolean
  error: string | null
  currentTimezone: string
  timezoneGroups: TimezoneGroup[]
  popularTimezones: TimezoneInfo[]
  updateTimezone: (timezone: string) => Promise<void>
  getTimezoneById: (id: string) => TimezoneInfo | null
}

/**
 * Hook for managing timezone functionality
 */
export function useTimezone(): UseTimezoneReturn {
  const { settings, updateSettings } = useSettingsContext()
  const [isInitialized, setIsInitialized] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Initialize timezone service on mount
  useEffect(() => {
    const initializeService = async () => {
      try {
        setIsLoading(true)
        setError(null)

        await timezoneService.initialize()
        setIsInitialized(true)
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to initialize timezone service'
        setError(errorMessage)
        console.error('Timezone service initialization error:', err)
      } finally {
        setIsLoading(false)
      }
    }

    initializeService()
  }, [])

  // Get current timezone from settings
  const currentTimezone = settings?.ui.timezone || 'UTC'

  // Get timezone data (only after initialization)
  const timezoneGroups = isInitialized ? timezoneService.getTimezoneGroups() : []
  const popularTimezones = isInitialized ? timezoneService.getPopularTimezones() : []

  // Update timezone in settings
  const updateTimezone = useCallback(async (timezone: string) => {
    try {
      setError(null)
      const result = await updateSettings('ui', {
        ...settings?.ui,
        timezone
      })

      if (!result.success) {
        setError(result.error || 'Failed to update timezone')
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update timezone'
      setError(errorMessage)
    }
  }, [settings?.ui, updateSettings])

  // Get timezone by ID
  const getTimezoneById = useCallback((id: string): TimezoneInfo | null => {
    return isInitialized ? timezoneService.getTimezoneById(id) : null
  }, [isInitialized])

  return {
    isInitialized,
    isLoading,
    error,
    currentTimezone,
    timezoneGroups,
    popularTimezones,
    updateTimezone,
    getTimezoneById
  }
}