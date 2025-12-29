/**
 * Applications Page Component
 *
 * Modern app marketplace with search, filters, and installation management.
 */

import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Power, Trash2, X } from 'lucide-react'
import { Alert, Button, Card, Typography } from 'ui-toolkit'
import { App } from '@/types/app'
import { AppCard } from '@/components/applications/AppCard'
import { ApplicationFormDialog } from '@/components/applications/ApplicationFormDialog'
import { useApplications } from '@/hooks/useApplications'
import { useServers } from '@/hooks/useServers'
import { useToast } from '@/components/ui/Toast'
import { applicationLogger } from '@/services/systemLogger'
import { ApplicationsPageHeader } from './ApplicationsPageHeader'
import { ApplicationsSearchAndFilter } from './ApplicationsSearchAndFilter'
import { ApplicationsEmptyState } from './ApplicationsEmptyState'

export function ApplicationsPage() {
  const [searchParams] = useSearchParams()
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false)
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [isRemoving, setIsRemoving] = useState(false)
  const [isUninstalling, setIsUninstalling] = useState(false)
  const { addToast } = useToast()
  const {
    apps,
    categories,
    filter,
    setFilter,
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

  const handleSearch = (value: string) => {
    updateFilter({ search: value })
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
    setSelectedIds(new Set(apps.map(app => app.id)))
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

  const selectedCount = selectedIds.size
  const installedCount = apps.filter(app => app.status === 'installed').length

  // Count selected by type
  const selectedInstalledCount = Array.from(selectedIds).filter(id => {
    const app = apps.find(a => a.id === id)
    return app?.status === 'installed'
  }).length
  const selectedNonInstalledCount = selectedCount - selectedInstalledCount

  const allSelected = apps.length > 0 && selectedCount === apps.length

  return (
    <div className="space-y-4">
      {/* Ultra-compact header with inline Add App button */}
      <div className="space-y-2">
        <ApplicationsPageHeader onAddApp={handleAddApp} />

        {/* Ultra-compact search and filters in single line */}
        <ApplicationsSearchAndFilter
          filter={filter}
          onFilterChange={setFilter}
          onSearch={handleSearch}
          categories={categories}
        />
      </div>

      {/* Bulk action bar */}
      {apps.length > 0 && (
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
                {apps.length} app{apps.length > 1 ? 's' : ''} in catalog
                {installedCount > 0 && ` (${installedCount} deployed)`}
              </Typography>
            )}
          </div>
          <div className="flex items-center gap-2">
            {!allSelected && (
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

      {/* Ultra-compact grid with minimal gaps */}
      <div className="grid grid-cols-4 sm:grid-cols-6 md:grid-cols-8 lg:grid-cols-10 xl:grid-cols-12 2xl:grid-cols-14 gap-1.5">
        {apps.map((app) => (
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

      {!isLoading && apps.length === 0 && <ApplicationsEmptyState />}

      {error && (
        <Alert variant="danger" title="Error">
          {error}
        </Alert>
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
