/**
 * Applications Page Component
 *
 * Browse and manage installed applications.
 * Features tab navigation, search, filtering, and showcases deployed apps.
 */

import { useEffect, useState, useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Power, Trash2, X, Plus, Filter, Rocket } from 'lucide-react'
import { Tabs, Search, Alert, Typography, Button, Card, Carousel, Pagination, EmptyState } from 'ui-toolkit'
import { App } from '@/types/app'
import { AppCard } from '@/components/applications/AppCard'
import { ApplicationFormDialog } from '@/components/applications/ApplicationFormDialog'
import { useApplications } from '@/hooks/useApplications'
import { useServers } from '@/hooks/useServers'
import { useToast } from '@/components/ui/Toast'
import { applicationLogger } from '@/services/systemLogger'

type TabType = 'all' | 'deployed'

const tabItems = [
  { label: 'All Apps', value: 'all' },
  { label: 'Deployed', value: 'deployed' }
]

const ITEMS_PER_PAGE = 24

export function ApplicationsPage() {
  const [searchParams] = useSearchParams()
  const [activeTab, setActiveTab] = useState<TabType>('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string | undefined>()
  const [showFilters, setShowFilters] = useState(false)
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false)
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [isRemoving, setIsRemoving] = useState(false)
  const [isUninstalling, setIsUninstalling] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const { addToast } = useToast()
  const {
    apps,
    categories,
    updateFilter,
    addApplication,
    removeApplications,
    uninstallApplication,
    uninstallApplications,
    isLoading,
    error
  } = useApplications()
  const { servers } = useServers()

  // Read URL parameters and update filter
  useEffect(() => {
    const categoryParam = searchParams.get('category') || undefined
    updateFilter({ category: categoryParam })
  }, [searchParams, updateFilter])

  // Reset page when search/filter/tab changes
  useEffect(() => {
    setCurrentPage(1)
  }, [searchQuery, selectedCategory, activeTab])

  const handleSearch = (value: string) => {
    setSearchQuery(value)
    updateFilter({ search: value })
  }

  const handleCategoryChange = (categoryId: string | undefined) => {
    setSelectedCategory(categoryId)
    updateFilter({ category: categoryId })
    setShowFilters(false)
  }

  const handleAddApp = () => {
    setIsAddDialogOpen(true)
  }

  const handleSaveApp = async (appData: Partial<App>) => {
    try {
      await addApplication(appData)
      setIsAddDialogOpen(false)
    } catch (error) {
      console.error('Failed to add application:', error)
    }
  }

  // Selection handlers
  const handleToggleSelect = (appId: string) => {
    setSelectedIds(prev => {
      const next = new Set(prev)
      if (next.has(appId)) {
        next.delete(appId)
      } else {
        next.add(appId)
      }
      return next
    })
  }

  const handleClearSelection = () => {
    setSelectedIds(new Set())
  }

  const handleSelectAll = () => {
    setSelectedIds(new Set(displayApps.map(app => app.id)))
  }

  const handleBulkRemove = async () => {
    if (selectedIds.size === 0) return

    setIsRemoving(true)
    try {
      const result = await removeApplications(Array.from(selectedIds))
      setSelectedIds(new Set())

      if (result.removedCount > 0) {
        addToast({
          type: 'success',
          title: `Removed ${result.removedCount} application${result.removedCount > 1 ? 's' : ''}`
        })
      }
      if (result.skippedCount > 0) {
        addToast({
          type: 'warning',
          title: `Skipped ${result.skippedCount} installed app${result.skippedCount > 1 ? 's' : ''}`,
          message: 'Uninstall them first to remove from catalog'
        })
      }
    } catch (err) {
      addToast({
        type: 'error',
        title: 'Failed to remove applications'
      })
    } finally {
      setIsRemoving(false)
    }
  }

  const handleUninstall = async (appId: string, serverId?: string) => {
    try {
      await uninstallApplication(appId, serverId)
      addToast({
        type: 'success',
        title: 'Application uninstalled'
      })
    } catch (err) {
      addToast({
        type: 'error',
        title: 'Failed to uninstall application'
      })
    }
  }

  const handleDeploy = (appId: string) => {
    const app = apps.find(a => a.id === appId)

    if (servers.length === 0) {
      applicationLogger.warn('Deploy attempted with no servers configured', {
        source: 'ApplicationsPage',
        appId,
        appName: app?.name
      })
      addToast({
        type: 'warning',
        title: 'No servers configured',
        message: 'Add a server in the Servers page before deploying applications'
      })
      return
    }
    // TODO: Open deployment dialog to select server and configure
    console.log('Deploy app:', app?.name, 'to one of', servers.length, 'servers')
  }

  const handleBulkUninstall = async () => {
    const installedSelectedIds = Array.from(selectedIds).filter(id => {
      const app = apps.find(a => a.id === id)
      return app?.status === 'installed'
    })

    if (installedSelectedIds.length === 0) return

    setIsUninstalling(true)
    try {
      const result = await uninstallApplications(installedSelectedIds)
      setSelectedIds(new Set())

      if (result.uninstalledCount > 0) {
        addToast({
          type: 'success',
          title: `Uninstalled ${result.uninstalledCount} application${result.uninstalledCount > 1 ? 's' : ''}`
        })
      }
      if (result.skippedCount > 0) {
        addToast({
          type: 'warning',
          title: `Skipped ${result.skippedCount} app${result.skippedCount > 1 ? 's' : ''}`,
          message: 'Some applications could not be uninstalled'
        })
      }
    } catch (err) {
      addToast({
        type: 'error',
        title: 'Failed to uninstall applications'
      })
    } finally {
      setIsUninstalling(false)
    }
  }

  // Filter apps based on tab and search
  const deployedApps = useMemo(() => apps.filter(app => app.status === 'installed'), [apps])

  const filteredApps = useMemo(() => {
    let result = activeTab === 'deployed' ? deployedApps : apps

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
  }, [apps, deployedApps, activeTab, searchQuery, selectedCategory])

  const displayApps = filteredApps
  const totalApps = displayApps.length
  const totalPages = Math.ceil(totalApps / ITEMS_PER_PAGE)

  // Paginated apps
  const paginatedApps = useMemo(() => {
    const start = (currentPage - 1) * ITEMS_PER_PAGE
    return displayApps.slice(start, start + ITEMS_PER_PAGE)
  }, [displayApps, currentPage])

  // Build category options
  const categoryOptions = [
    { label: 'All Categories', value: '' },
    ...categories.map((cat) => ({
      label: cat.name,
      value: cat.id
    }))
  ]

  // Selection counts
  const selectedCount = selectedIds.size
  const selectedInstalledCount = Array.from(selectedIds).filter(id => {
    const app = apps.find(a => a.id === id)
    return app?.status === 'installed'
  }).length
  const selectedNonInstalledCount = selectedCount - selectedInstalledCount
  const allSelected = displayApps.length > 0 && selectedCount === displayApps.length

  return (
    <div className="flex flex-col h-full">
      {/* Header Row: Title + Tabs + Search */}
      <div className="flex flex-col lg:flex-row lg:items-center gap-3 mb-4">
        <div className="shrink-0 mr-4">
          <Typography variant="h2">Applications</Typography>
        </div>

        <Tabs
          items={tabItems}
          active={activeTab}
          onChange={(value) => setActiveTab(value as TabType)}
          variant="underline"
        />

        <div className="flex gap-2 lg:ml-auto items-center">
          <Search
            value={searchQuery}
            onChange={handleSearch}
            placeholder="Search apps..."
          />
          <div className="relative">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowFilters(!showFilters)}
              className="p-2"
            >
              <Filter className="h-4 w-4" />
            </Button>
            {showFilters && (
              <div className="absolute right-0 top-full mt-1 z-20 bg-popover border border-border rounded-lg shadow-lg p-2 min-w-[200px]">
                <p className="text-xs text-muted-foreground mb-2 px-2">Category</p>
                {categoryOptions.map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => handleCategoryChange(opt.value || undefined)}
                    className={`w-full text-left px-2 py-1.5 text-sm rounded hover:bg-muted ${selectedCategory === opt.value || (!selectedCategory && !opt.value) ? 'bg-primary/10 text-primary' : ''}`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            )}
          </div>
          <Button
            onClick={handleAddApp}
            variant="primary"
            size="sm"
            leftIcon={<Plus size={14} />}
          >
            Add App
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto space-y-4">
        {/* Deployed Apps Carousel - only show on All Apps tab when not searching */}
        {activeTab === 'all' && !searchQuery && !selectedCategory && deployedApps.length > 0 && (
          <section className="px-4">
            <Typography variant="small" muted className="flex items-center gap-1.5 mb-2 font-semibold">
              <Rocket className="h-4 w-4 text-green-500" />
              Deployed
            </Typography>
            <Carousel gap={8}>
              {deployedApps.map((app) => (
                <div key={app.id} className="w-[100px]">
                  <AppCard
                    app={app}
                    isSelected={selectedIds.has(app.id)}
                    onToggleSelect={handleToggleSelect}
                    onUninstall={handleUninstall}
                  />
                </div>
              ))}
            </Carousel>
          </section>
        )}

        {/* Bulk Action Bar */}
        {totalApps > 0 && (
          <Card padding="sm" elevation="xs" className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {selectedCount > 0 ? (
                <>
                  <Typography variant="body-strong">
                    {selectedCount} selected
                    {selectedInstalledCount > 0 && selectedNonInstalledCount > 0 && (
                      <Typography as="span" variant="body" muted>
                        {' '}({selectedInstalledCount} deployed, {selectedNonInstalledCount} available)
                      </Typography>
                    )}
                  </Typography>
                  <button
                    type="button"
                    onClick={handleClearSelection}
                    className="text-xs text-muted-foreground hover:text-foreground transition-colors"
                    title="Clear selection"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </>
              ) : (
                <Typography variant="body" muted>
                  {activeTab === 'deployed'
                    ? `${totalApps} deployed app${totalApps !== 1 ? 's' : ''}`
                    : `${totalApps} app${totalApps !== 1 ? 's' : ''} in catalog`
                  }
                  {activeTab === 'all' && deployedApps.length > 0 && ` (${deployedApps.length} deployed)`}
                </Typography>
              )}
            </div>
            <div className="flex items-center gap-2">
              {!allSelected && displayApps.length > 0 && (
                <Button variant="ghost" size="sm" onClick={handleSelectAll}>
                  Select all
                </Button>
              )}
              {selectedInstalledCount > 0 && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleBulkUninstall}
                  disabled={isUninstalling}
                  leftIcon={<Power size={14} />}
                  className="text-orange-600 hover:text-orange-700"
                >
                  {isUninstalling ? 'Uninstalling...' : `Uninstall (${selectedInstalledCount})`}
                </Button>
              )}
              {selectedNonInstalledCount > 0 && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleBulkRemove}
                  disabled={isRemoving}
                  leftIcon={<Trash2 size={14} />}
                  className="text-red-600 hover:text-red-700"
                >
                  {isRemoving ? 'Removing...' : `Remove (${selectedNonInstalledCount})`}
                </Button>
              )}
            </div>
          </Card>
        )}

        {/* Apps Grid */}
        {totalApps > 0 && (
          <section>
            <Typography variant="small" muted className="mb-6 font-semibold">
              {searchQuery || selectedCategory
                ? `${totalApps} ${totalApps === 1 ? 'App' : 'Apps'} Found`
                : activeTab === 'deployed'
                  ? `Deployed Apps (${totalApps})`
                  : `All Apps (${totalApps})`
              }
            </Typography>
            <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-8 xl:grid-cols-10 2xl:grid-cols-12 gap-2 pt-2">
              {paginatedApps.map((app) => (
                <AppCard
                  key={app.id}
                  app={app}
                  isSelected={selectedIds.has(app.id)}
                  onToggleSelect={handleToggleSelect}
                  onUninstall={app.status === 'installed' ? handleUninstall : undefined}
                  onDeploy={app.status !== 'installed' ? handleDeploy : undefined}
                />
              ))}
            </div>
          </section>
        )}

        {/* Empty States */}
        {!isLoading && totalApps === 0 && !searchQuery && !selectedCategory && (
          <EmptyState
            icon={Rocket}
            title={activeTab === 'deployed' ? 'No deployed apps' : 'No apps available'}
            message={activeTab === 'deployed'
              ? 'Deploy an app from the All Apps tab or import from Marketplace'
              : 'Import apps from the Marketplace to get started'
            }
          />
        )}

        {!isLoading && totalApps === 0 && (searchQuery || selectedCategory) && (
          <div className="text-center py-8 bg-muted rounded-lg border border-border">
            <Typography variant="small" muted>No apps found matching your criteria</Typography>
          </div>
        )}

        {/* Loading */}
        {isLoading && (
          <div className="flex justify-center py-8">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
          </div>
        )}

        {/* Error */}
        {error && (
          <Alert variant="danger" title="Error">
            {error}
          </Alert>
        )}
      </div>

      {/* Pagination - Fixed at bottom */}
      {totalPages > 1 && (
        <div className="shrink-0 mt-auto">
          <Pagination
            currentPage={currentPage}
            totalPages={totalPages}
            onPageChange={setCurrentPage}
          />
        </div>
      )}

      <ApplicationFormDialog
        isOpen={isAddDialogOpen}
        onClose={() => setIsAddDialogOpen(false)}
        onSave={handleSaveApp}
        categories={categories}
        title="Add Custom Application"
      />
    </div>
  )
}
