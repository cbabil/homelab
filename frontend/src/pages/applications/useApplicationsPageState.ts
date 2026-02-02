/**
 * Applications Page State Hook
 *
 * Manages selection, bulk operations, and pagination state for deployed applications.
 */

import { useState, useCallback, useMemo, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useApplications } from '@/hooks/useApplications'
import { useServers } from '@/hooks/useServers'
import { useToast } from '@/components/ui/Toast'
import { useDeploymentModal } from '@/hooks/useDeploymentModal'

const ITEMS_PER_PAGE = 24

export function useApplicationsPageState() {
  const [searchParams] = useSearchParams()
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string | undefined>()
  const [showFilters, setShowFilters] = useState(false)
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [isUninstalling, setIsUninstalling] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const { addToast } = useToast()
  const {
    apps,
    categories,
    updateFilter,
    uninstallApplication,
    uninstallApplications,
    isLoading,
    error
  } = useApplications()
  const { servers } = useServers()
  const deploymentModal = useDeploymentModal()

  useEffect(() => {
    const categoryParam = searchParams.get('category') || undefined
    updateFilter({ category: categoryParam })
  }, [searchParams, updateFilter])

  useEffect(() => {
    setCurrentPage(1)
  }, [searchQuery, selectedCategory])

  const handleSearch = useCallback((value: string) => {
    setSearchQuery(value)
    updateFilter({ search: value })
  }, [updateFilter])

  const handleCategoryChange = useCallback((categoryId: string | undefined) => {
    setSelectedCategory(categoryId)
    updateFilter({ category: categoryId })
    setShowFilters(false)
  }, [updateFilter])

  const handleToggleSelect = useCallback((appId: string) => {
    setSelectedIds(prev => {
      const next = new Set(prev)
      if (next.has(appId)) {
        next.delete(appId)
      } else {
        next.add(appId)
      }
      return next
    })
  }, [])

  const handleClearSelection = useCallback(() => {
    setSelectedIds(new Set())
  }, [])

  // Only show deployed/installed apps
  const deployedApps = useMemo(() => apps.filter(app => app.status === 'installed'), [apps])

  const filteredApps = useMemo(() => {
    let result = deployedApps

    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      result = result.filter(app =>
        app.name.toLowerCase().includes(query) ||
        app.description?.toLowerCase().includes(query)
      )
    }

    if (selectedCategory) {
      result = result.filter(app => app.category?.id === selectedCategory)
    }

    return result
  }, [deployedApps, searchQuery, selectedCategory])

  const displayApps = filteredApps
  const totalApps = displayApps.length
  const totalPages = Math.ceil(totalApps / ITEMS_PER_PAGE)

  const paginatedApps = useMemo(() => {
    const start = (currentPage - 1) * ITEMS_PER_PAGE
    return displayApps.slice(start, start + ITEMS_PER_PAGE)
  }, [displayApps, currentPage])

  const handleSelectAll = useCallback(() => {
    setSelectedIds(new Set(displayApps.map(app => app.id)))
  }, [displayApps])

  const handleUninstall = useCallback(async (appId: string, serverId?: string) => {
    try {
      await uninstallApplication(appId, serverId)
      addToast({ type: 'success', title: 'Application uninstalled' })
    } catch (_err) {
      addToast({ type: 'error', title: 'Failed to uninstall application' })
    }
  }, [uninstallApplication, addToast])

  const handleBulkUninstall = useCallback(async () => {
    if (selectedIds.size === 0) return

    setIsUninstalling(true)
    try {
      const result = await uninstallApplications(Array.from(selectedIds))
      setSelectedIds(new Set())
      if (result.uninstalledCount > 0) {
        addToast({ type: 'success', title: `Uninstalled ${result.uninstalledCount} application${result.uninstalledCount > 1 ? 's' : ''}` })
      }
      if (result.skippedCount > 0) {
        addToast({ type: 'warning', title: `Skipped ${result.skippedCount} app${result.skippedCount > 1 ? 's' : ''}`, message: 'Some applications could not be uninstalled' })
      }
    } catch (_err) {
      addToast({ type: 'error', title: 'Failed to uninstall applications' })
    } finally {
      setIsUninstalling(false)
    }
  }, [selectedIds, uninstallApplications, addToast])

  const categoryOptions = useMemo(() => [
    { label: 'All Categories', value: '' },
    ...categories.map((cat) => ({ label: cat.name, value: cat.id }))
  ], [categories])

  const selectedCount = selectedIds.size
  const allSelected = displayApps.length > 0 && selectedCount === displayApps.length

  return {
    searchQuery,
    selectedCategory,
    showFilters,
    setShowFilters,
    selectedIds,
    isUninstalling,
    currentPage,
    setCurrentPage,
    apps: deployedApps,
    categories,
    displayApps,
    paginatedApps,
    totalApps,
    totalPages,
    isLoading,
    error,
    categoryOptions,
    selectedCount,
    allSelected,
    servers,
    deploymentModal,
    handleSearch,
    handleCategoryChange,
    handleToggleSelect,
    handleClearSelection,
    handleSelectAll,
    handleUninstall,
    handleBulkUninstall
  }
}
