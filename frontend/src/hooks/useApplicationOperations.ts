/**
 * Application Operations Hook
 *
 * Handles CRUD and install/uninstall operations for applications.
 */

import { useCallback, Dispatch, SetStateAction } from 'react'
import { App, AppCategory } from '@/types/app'
import { ApplicationsDataService } from '@/services/applicationsDataService'

interface UseApplicationOperationsProps {
  applicationsService: ApplicationsDataService
  setApps: Dispatch<SetStateAction<App[]>>
  setCategories: Dispatch<SetStateAction<AppCategory[]>>
  setIsLoading: (loading: boolean) => void
  setError: (error: string | null) => void
}

export function useApplicationOperations({
  applicationsService,
  setApps,
  setCategories,
  setIsLoading,
  setError
}: UseApplicationOperationsProps) {

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
  }, [setApps, setCategories, setError, setIsLoading])

  const updateApplication = useCallback(async (id: string, appData: Partial<App>) => {
    setIsLoading(true)
    setError(null)

    try {
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
  }, [setApps, setError, setIsLoading])

  const deleteApplication = useCallback(async (id: string) => {
    setIsLoading(true)
    setError(null)

    try {
      await new Promise(resolve => setTimeout(resolve, 500))
      setApps(prev => prev.filter(app => app.id !== id))
    } catch (err) {
      setError('Failed to delete application')
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [setApps, setError, setIsLoading])

  const installApplication = useCallback(async (id: string) => {
    setIsLoading(true)
    setError(null)

    try {
      setApps(prev => prev.map(app =>
        app.id === id ? { ...app, status: 'installing' } : app
      ))

      await new Promise(resolve => setTimeout(resolve, 3000))

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
  }, [setApps, setError, setIsLoading])

  const removeApplications = useCallback(async (ids: string[]) => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await applicationsService.removeBulk(ids)

      if (response.success && response.data) {
        setApps(prev => prev.filter(app => !response.data!.removed.includes(app.id)))
        return response.data
      } else {
        throw new Error(response.error || 'Failed to remove applications')
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to remove applications'
      setError(message)
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [applicationsService, setApps, setError, setIsLoading])

  const uninstallApplication = useCallback(async (appId: string, serverId?: string) => {
    setIsLoading(true)
    setError(null)

    try {
      const response = serverId
        ? await applicationsService.uninstall(appId, serverId)
        : await applicationsService.markUninstalled(appId)

      if (response.success) {
        setApps(prev => prev.map(app =>
          app.id === appId
            ? { ...app, status: 'available', connectedServerId: undefined }
            : app
        ))
        return true
      } else {
        throw new Error(response.error || 'Failed to uninstall application')
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to uninstall application'
      setError(message)
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [applicationsService, setApps, setError, setIsLoading])

  const uninstallApplications = useCallback(async (ids: string[]) => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await applicationsService.markUninstalledBulk(ids)

      if (response.success && response.data) {
        setApps(prev => prev.map(app =>
          response.data!.uninstalled.includes(app.id)
            ? { ...app, status: 'available', connectedServerId: undefined }
            : app
        ))
        return response.data
      } else {
        throw new Error(response.error || 'Failed to uninstall applications')
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to uninstall applications'
      setError(message)
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [applicationsService, setApps, setError, setIsLoading])

  return {
    addApplication,
    updateApplication,
    deleteApplication,
    installApplication,
    removeApplications,
    uninstallApplication,
    uninstallApplications
  }
}
