/**
 * Applications Hook
 * 
 * Custom hook for managing application state and operations.
 */

import { useState, useCallback, useEffect } from 'react'
import { App, AppCategory, AppFilter } from '@/types/app'
import { useApplicationsService } from '@/hooks/useDataServices'
import { applicationLogger } from '@/services/systemLogger'

export function useApplications() {
  const { applicationsService, isConnected } = useApplicationsService()
  const [apps, setApps] = useState<App[]>([])
  const [categories, setCategories] = useState<AppCategory[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [currentFilter, setCurrentFilter] = useState<AppFilter>({})

  const deriveCategories = useCallback((applications: App[]): AppCategory[] => {
    const map = new Map<string, AppCategory>()
    for (const app of applications) {
      if (!map.has(app.category.id)) {
        map.set(app.category.id, app.category)
      }
    }
    return Array.from(map.values())
  }, [])

  const sanitizeFilter = useCallback((filter: AppFilter): AppFilter => {
    const sanitized: AppFilter = {}
    if (filter.category) sanitized.category = filter.category
    if (filter.status) sanitized.status = filter.status
    if (filter.search && filter.search.trim().length > 0) sanitized.search = filter.search.trim()
    if (filter.featured !== undefined) sanitized.featured = filter.featured
    if (filter.tags && filter.tags.length > 0) sanitized.tags = filter.tags
    if (filter.sortBy) sanitized.sortBy = filter.sortBy
    if (filter.sortOrder) sanitized.sortOrder = filter.sortOrder
    return sanitized
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

  const filtersEqual = useCallback((a: AppFilter, b: AppFilter) => {
    return JSON.stringify(a) === JSON.stringify(b)
  }, [])

  const setFilter = useCallback((nextFilter: AppFilter) => {
    setCurrentFilter(prev => {
      const sanitized = sanitizeFilter(nextFilter)
      return filtersEqual(prev, sanitized) ? prev : sanitized
    })
  }, [filtersEqual, sanitizeFilter])

  const updateFilter = useCallback((updates: Partial<AppFilter>) => {
    setCurrentFilter(prev => {
      const sanitized = sanitizeFilter({ ...prev, ...updates })
      return filtersEqual(prev, sanitized) ? prev : sanitized
    })
  }, [filtersEqual, sanitizeFilter])

  const addApplication = useCallback(async (appData: Partial<App>) => {
    setIsLoading(true)
    setError(null)

    try {
      await new Promise(resolve => setTimeout(resolve, 1000))

      if (!appData.category) {
        throw new Error('Category is required')
      }

      const newApp: App = {
        id: `custom-${Date.now()}`,
        name: appData.name || '',
        description: appData.description || '',
        version: appData.version || '1.0.0',
        category: appData.category,
        tags: appData.tags || [],
        author: appData.author || '',
        repository: appData.repository,
        documentation: appData.documentation,
        license: appData.license || '',
        requirements: appData.requirements || {},
        status: 'available',
        installCount: 0,
        rating: 0,
        featured: false,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        connectedServerId: undefined
      }
      
      setApps(prev => [newApp, ...prev])
      setCategories(prev => {
        if (prev.some(cat => cat.id === newApp.category.id)) {
          return prev
        }
        return [...prev, newApp.category]
      })
      return newApp
    } catch (err) {
      setError('Failed to add application')
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [])

  const updateApplication = useCallback(async (id: string, appData: Partial<App>) => {
    setIsLoading(true)
    setError(null)
    
    try {
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 800))
      
      setApps(prev => prev.map(app => 
        app.id === id 
          ? { ...app, ...appData, updatedAt: new Date().toISOString() }
          : app
      ))
    } catch (err) {
      setError('Failed to update application')
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [])

  const deleteApplication = useCallback(async (id: string) => {
    setIsLoading(true)
    setError(null)
    
    try {
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 500))
      
      setApps(prev => prev.filter(app => app.id !== id))
    } catch (err) {
      setError('Failed to delete application')
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [])

  const installApplication = useCallback(async (id: string) => {
    setIsLoading(true)
    setError(null)
    
    try {
      // Set status to installing
      setApps(prev => prev.map(app => 
        app.id === id ? { ...app, status: 'installing' } : app
      ))
      
      // Simulate installation time
      await new Promise(resolve => setTimeout(resolve, 3000))
      
      // Set status to installed
      setApps(prev => prev.map(app => 
        app.id === id 
          ? { ...app, status: 'installed', installCount: (app.installCount || 0) + 1 }
          : app
      ))
    } catch (err) {
      setError('Failed to install application')
      setApps(prev => prev.map(app => 
        app.id === id ? { ...app, status: 'error' } : app
      ))
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [])

  const refresh = useCallback(() => fetchApplications(currentFilter), [fetchApplications, currentFilter])

  return {
    apps,
    categories,
    filter: currentFilter,
    isLoading,
    error,
    setFilter,
    updateFilter,
    addApplication,
    updateApplication,
    deleteApplication,
    installApplication,
    refresh
  }
}
