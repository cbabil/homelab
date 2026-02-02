/**
 * Applications Hook
 *
 * Custom hook for managing application state and operations.
 */

import { useState, useCallback, useEffect } from 'react'
import { App, AppCategory, AppFilter } from '@/types/app'
import { useApplicationsService } from '@/hooks/useDataServices'
import { useApplicationFilter } from '@/hooks/useApplicationFilter'
import { useApplicationOperations } from '@/hooks/useApplicationOperations'
import { applicationLogger } from '@/services/systemLogger'

export function useApplications() {
  const { applicationsService, isConnected } = useApplicationsService()
  const [apps, setApps] = useState<App[]>([])
  const [categories, setCategories] = useState<AppCategory[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const { currentFilter, setFilter, updateFilter } = useApplicationFilter()

  const operations = useApplicationOperations({
    applicationsService,
    setApps,
    setCategories,
    setIsLoading,
    setError
  })

  const deriveCategories = useCallback((applications: App[]): AppCategory[] => {
    const map = new Map<string, AppCategory>()
    for (const app of applications) {
      if (!map.has(app.category.id)) {
        map.set(app.category.id, app.category)
      }
    }
    return Array.from(map.values())
  }, [])

  const fetchApplications = useCallback(async (activeFilter: AppFilter) => {
    if (!isConnected) {
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const response = await applicationsService.search(activeFilter)

      if (response.success && response.data) {
        setApps(response.data.apps)
        setError(null)

        if (response.data.total === 0) {
          applicationLogger.info('Application catalog returned no results', {
            source: 'useApplications',
            filters: activeFilter
          })
        } else {
          setCategories(deriveCategories(response.data.apps))
        }
      } else {
        setApps([])
        const errMessage = response.error || response.message
        if (errMessage && errMessage !== 'Failed to fetch applications') {
          setError(errMessage)
        } else {
          setError(null)
        }
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error occurred'
      setError(message)
      setApps([])
    } finally {
      setIsLoading(false)
    }
  }, [applicationsService, deriveCategories, isConnected])

  useEffect(() => {
    fetchApplications(currentFilter)
  }, [fetchApplications, currentFilter])

  const refresh = useCallback(() => fetchApplications(currentFilter), [fetchApplications, currentFilter])

  return {
    apps,
    categories,
    filter: currentFilter,
    isLoading,
    error,
    setFilter,
    updateFilter,
    refresh,
    ...operations
  }
}
