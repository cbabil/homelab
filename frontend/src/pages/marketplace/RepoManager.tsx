/**
 * Repository Manager Component
 *
 * Manages marketplace repositories with CRUD operations and sync functionality.
 * Shows repository list with status badges, sync controls, and add/remove actions.
 */

import { useEffect, useState } from 'react'
import { Plus, RefreshCw, Trash2, GitBranch, Globe, Package } from 'lucide-react'
import { Button, Input, Badge, Card, Modal, Dropdown, Alert, EmptyState, type DropdownOption } from 'ui-toolkit'
import type { MarketplaceRepo, RepoType } from '@/types/marketplace'
import * as marketplaceService from '@/services/marketplaceService'
import { marketplaceLogger } from '@/services/systemLogger'

/**
 * Get badge variant for status
 */
function getStatusVariant(status: string): 'success' | 'warning' | 'danger' | 'neutral' {
  switch (status) {
    case 'active': return 'success'
    case 'syncing': return 'warning'
    case 'error': return 'danger'
    default: return 'neutral'
  }
}

/**
 * Add Repository Form Modal
 */
interface AddRepoModalProps {
  isOpen: boolean
  onClose: () => void
  onAdd: (name: string, url: string, repoType: RepoType, branch: string) => Promise<void>
}

function AddRepoModal({ isOpen, onClose, onAdd }: AddRepoModalProps) {
  const [name, setName] = useState('')
  const [url, setUrl] = useState('')
  const [repoType, setRepoType] = useState<RepoType>('community')
  const [branch, setBranch] = useState('main')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const repoTypeOptions: DropdownOption[] = [
    { label: 'Official', value: 'official' },
    { label: 'Community', value: 'community' },
    { label: 'Personal', value: 'personal' }
  ]

  const handleSubmit = async () => {
    if (!name || !url) return

    setIsSubmitting(true)
    setError(null)

    try {
      await onAdd(name, url, repoType, branch)
      // Reset form
      setName('')
      setUrl('')
      setRepoType('community')
      setBranch('main')
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add repository')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleClose = () => {
    setName('')
    setUrl('')
    setRepoType('community')
    setBranch('main')
    setError(null)
    onClose()
  }

  return (
    <Modal
      open={isOpen}
      onClose={handleClose}
      title="Add Repository"
      size="sm"
      footer={
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={handleClose} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={isSubmitting || !name || !url}>
            {isSubmitting ? 'Adding...' : 'Add Repository'}
          </Button>
        </div>
      }
    >
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1.5">Repository Name</label>
          <Input
            value={name}
            onChange={(value) => setName(value)}
            placeholder="e.g., Official Apps"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1.5">Git Repository URL</label>
          <Input
            value={url}
            onChange={(value) => setUrl(value)}
            placeholder="https://github.com/user/repo"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1.5">Repository Type</label>
          <Dropdown
            options={repoTypeOptions}
            value={repoType}
            onChange={(value) => setRepoType(value as RepoType)}
            placeholder="Select type"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1.5">Branch</label>
          <Input
            value={branch}
            onChange={(value) => setBranch(value)}
            placeholder="main"
          />
        </div>

        {error && (
          <Alert variant="danger">{error}</Alert>
        )}
      </div>
    </Modal>
  )
}

/**
 * Repository List Item Component
 */
interface RepoListItemProps {
  repo: MarketplaceRepo
  onSync: (repoId: string) => Promise<void>
  onRemove: (repoId: string) => Promise<void>
}

function RepoListItem({ repo, onSync, onRemove }: RepoListItemProps) {
  const [isSyncing, setIsSyncing] = useState(false)
  const [isRemoving, setIsRemoving] = useState(false)

  const handleSync = async () => {
    setIsSyncing(true)
    try {
      await onSync(repo.id)
    } finally {
      setIsSyncing(false)
    }
  }

  const handleRemove = async () => {
    if (!confirm(`Are you sure you want to remove "${repo.name}"? This will delete all apps from this repository.`)) {
      return
    }

    setIsRemoving(true)
    try {
      await onRemove(repo.id)
    } finally {
      setIsRemoving(false)
    }
  }

  return (
    <Card className="p-4 max-w-xl">
      <div className="flex items-start justify-between gap-4">
        {/* Repo Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2 flex-wrap">
            <h3 className="font-semibold truncate">{repo.name}</h3>
            <Badge variant={getStatusVariant(repo.status)}>{repo.status}</Badge>
            <Badge variant="neutral">{repo.repoType}</Badge>
          </div>

          <div className="space-y-1 text-sm text-muted-foreground">
            <p className="flex items-center gap-1.5 truncate">
              <Globe className="h-3.5 w-3.5 shrink-0" />
              <span className="truncate">{repo.url}</span>
            </p>
            <p className="flex items-center gap-1.5">
              <GitBranch className="h-3.5 w-3.5 shrink-0" />
              {repo.branch}
            </p>
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-1.5">
                <Package className="h-3.5 w-3.5 shrink-0" />
                {repo.appCount} apps
              </span>
              {repo.lastSynced && (
                <span className="text-xs">
                  Synced: {new Date(repo.lastSynced).toLocaleString()}
                </span>
              )}
            </div>
          </div>

          {/* Error Message */}
          {repo.errorMessage && (
            <Alert variant="danger" className="mt-2 text-xs">
              {repo.errorMessage}
            </Alert>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleSync}
            disabled={isSyncing || repo.status === 'syncing' || isRemoving}
            title="Sync repository"
          >
            <RefreshCw className={`h-4 w-4 ${isSyncing || repo.status === 'syncing' ? 'animate-spin' : ''}`} />
          </Button>
          {repo.repoType !== 'official' && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleRemove}
              disabled={isRemoving || isSyncing || repo.status === 'syncing'}
              title="Remove repository"
              className="text-destructive hover:text-destructive"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>
    </Card>
  )
}

/**
 * Main Repository Manager Component
 */
export function RepoManager() {
  const [repos, setRepos] = useState<MarketplaceRepo[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isAddModalOpen, setIsAddModalOpen] = useState(false)

  // Load repositories on mount
  useEffect(() => {
    loadRepos()
  }, [])

  const loadRepos = async () => {
    setIsLoading(true)
    setError(null)
    marketplaceLogger.info('Loading repositories')

    try {
      const data = await marketplaceService.getRepos()
      setRepos(data)
      marketplaceLogger.info(`Loaded ${data.length} repositories`)
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to load repositories'
      setError(errorMsg)
      marketplaceLogger.error(errorMsg)
    } finally {
      setIsLoading(false)
    }
  }

  const handleAddRepo = async (name: string, url: string, repoType: RepoType, branch: string) => {
    marketplaceLogger.info(`Adding repository: ${name}`)
    const newRepo = await marketplaceService.addRepo(name, url, repoType, branch)
    setRepos((prev) => [...prev, newRepo])
    marketplaceLogger.info(`Repository added: ${name}`)
  }

  const handleSyncRepo = async (repoId: string) => {
    const repo = repos.find(r => r.id === repoId)
    marketplaceLogger.info(`Syncing repository: ${repo?.name || repoId}`)

    try {
      // Optimistically update UI
      setRepos((prev) =>
        prev.map((r) =>
          r.id === repoId ? { ...r, status: 'syncing' as const } : r
        )
      )

      const result = await marketplaceService.syncRepo(repoId)

      // Reload repos to get updated status and app count
      await loadRepos()

      marketplaceLogger.info(`Synced ${result.appCount} apps from ${repo?.name || repoId}`)
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to sync repository'
      marketplaceLogger.error(`Sync failed for ${repo?.name || repoId}: ${errorMsg}`)
      // Reload to get actual status
      await loadRepos()
      throw err
    }
  }

  const handleRemoveRepo = async (repoId: string) => {
    const repo = repos.find(r => r.id === repoId)
    marketplaceLogger.info(`Removing repository: ${repo?.name || repoId}`)
    await marketplaceService.removeRepo(repoId)
    setRepos((prev) => prev.filter((r) => r.id !== repoId))
    marketplaceLogger.info(`Repository removed: ${repo?.name || repoId}`)
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          Manage Git-based application repositories
        </p>
        <Button onClick={() => setIsAddModalOpen(true)} className="px-6">
          <span className="inline-flex items-center gap-1.5">
            <Plus className="h-4 w-4" />
            Add
          </span>
        </Button>
      </div>

      {/* Repository List */}
      {isLoading && repos.length === 0 ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      ) : error ? (
        <Alert variant="danger">{error}</Alert>
      ) : repos.length === 0 ? (
        <EmptyState
          icon={Package}
          title="No repositories"
          message="Add a repository to start browsing apps"
          action={
            <Button onClick={() => setIsAddModalOpen(true)} className="px-6">
              <span className="inline-flex items-center gap-1.5">
                <Plus className="h-4 w-4" />
                Add
              </span>
            </Button>
          }
        />
      ) : (
        <div className="space-y-3">
          {repos.map((repo) => (
            <RepoListItem
              key={repo.id}
              repo={repo}
              onSync={handleSyncRepo}
              onRemove={handleRemoveRepo}
            />
          ))}
        </div>
      )}

      {/* Add Repository Modal */}
      <AddRepoModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        onAdd={handleAddRepo}
      />
    </div>
  )
}
