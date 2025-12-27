/**
 * Repository Manager Component
 *
 * Manages marketplace repositories with CRUD operations and sync functionality.
 * Shows repository list with status badges, sync controls, and add/remove actions.
 */

import { useEffect, useState } from 'react'
import { Plus, RefreshCw, Trash2, X, AlertCircle, CheckCircle, Clock } from 'lucide-react'
import type { MarketplaceRepo, RepoType } from '@/types/marketplace'
import * as marketplaceService from '@/services/marketplaceService'

/**
 * Status badge component with appropriate colors and icons
 */
function StatusBadge({ status }: { status: string }) {
  const variants = {
    active: {
      bg: 'bg-green-50',
      text: 'text-green-700',
      border: 'border-green-200',
      icon: CheckCircle
    },
    syncing: {
      bg: 'bg-yellow-50',
      text: 'text-yellow-700',
      border: 'border-yellow-200',
      icon: Clock
    },
    error: {
      bg: 'bg-red-50',
      text: 'text-red-700',
      border: 'border-red-200',
      icon: AlertCircle
    },
    disabled: {
      bg: 'bg-gray-50',
      text: 'text-gray-700',
      border: 'border-gray-200',
      icon: AlertCircle
    }
  }

  const variant = variants[status as keyof typeof variants] || variants.active
  const Icon = variant.icon

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium border ${variant.bg} ${variant.text} ${variant.border}`}>
      <Icon className="h-3 w-3" />
      {status}
    </span>
  )
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
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

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white p-6 rounded-lg border border-gray-200 max-w-md w-full mx-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Add Repository</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
            type="button"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Name Field */}
          <div>
            <label htmlFor="repo-name" className="block text-sm font-medium text-gray-700 mb-1">
              Repository Name
            </label>
            <input
              id="repo-name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              placeholder="e.g., Official Apps"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          {/* URL Field */}
          <div>
            <label htmlFor="repo-url" className="block text-sm font-medium text-gray-700 mb-1">
              Git Repository URL
            </label>
            <input
              id="repo-url"
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              required
              placeholder="https://github.com/user/repo"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          {/* Repository Type */}
          <div>
            <label htmlFor="repo-type" className="block text-sm font-medium text-gray-700 mb-1">
              Repository Type
            </label>
            <select
              id="repo-type"
              value={repoType}
              onChange={(e) => setRepoType(e.target.value as RepoType)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="official">Official</option>
              <option value="community">Community</option>
              <option value="personal">Personal</option>
            </select>
          </div>

          {/* Branch Field */}
          <div>
            <label htmlFor="repo-branch" className="block text-sm font-medium text-gray-700 mb-1">
              Branch
            </label>
            <input
              id="repo-branch"
              type="text"
              value={branch}
              onChange={(e) => setBranch(e.target.value)}
              required
              placeholder="main"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-md p-3">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-2 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Adding...' : 'Add Repository'}
            </button>
          </div>
        </form>
      </div>
    </div>
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
    <div className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-sm transition-shadow">
      <div className="flex items-start justify-between gap-4">
        {/* Repo Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2">
            <h3 className="font-semibold text-gray-900 truncate">{repo.name}</h3>
            <StatusBadge status={repo.status} />
            <span className="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded">
              {repo.repoType}
            </span>
          </div>

          <div className="space-y-1">
            <p className="text-sm text-gray-600 truncate">
              <span className="font-medium">URL:</span> {repo.url}
            </p>
            <p className="text-sm text-gray-600">
              <span className="font-medium">Branch:</span> {repo.branch}
            </p>
            <div className="flex items-center gap-4 text-sm text-gray-600">
              <span>
                <span className="font-medium">Apps:</span> {repo.appCount}
              </span>
              {repo.lastSynced && (
                <span>
                  <span className="font-medium">Last Synced:</span>{' '}
                  {new Date(repo.lastSynced).toLocaleString()}
                </span>
              )}
            </div>
          </div>

          {/* Error Message */}
          {repo.errorMessage && (
            <div className="mt-2 bg-red-50 border border-red-200 rounded-md p-2">
              <p className="text-xs text-red-800">{repo.errorMessage}</p>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2">
          <button
            onClick={handleSync}
            disabled={isSyncing || repo.status === 'syncing' || isRemoving}
            className="p-2 text-blue-600 hover:bg-blue-50 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            title="Sync repository"
          >
            <RefreshCw className={`h-4 w-4 ${isSyncing || repo.status === 'syncing' ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={handleRemove}
            disabled={isRemoving || isSyncing || repo.status === 'syncing'}
            className="p-2 text-red-600 hover:bg-red-50 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            title="Remove repository"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
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

    try {
      const data = await marketplaceService.getRepos()
      setRepos(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load repositories')
      console.error('Failed to load repos:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleAddRepo = async (name: string, url: string, repoType: RepoType, branch: string) => {
    const newRepo = await marketplaceService.addRepo(name, url, repoType, branch)
    setRepos((prev) => [...prev, newRepo])
  }

  const handleSyncRepo = async (repoId: string) => {
    try {
      // Optimistically update UI
      setRepos((prev) =>
        prev.map((repo) =>
          repo.id === repoId ? { ...repo, status: 'syncing' as const } : repo
        )
      )

      const result = await marketplaceService.syncRepo(repoId)

      // Reload repos to get updated status and app count
      await loadRepos()

      console.log(`Synced ${result.appCount} apps from repository`)
    } catch (err) {
      console.error('Failed to sync repo:', err)
      // Reload to get actual status
      await loadRepos()
      throw err
    }
  }

  const handleRemoveRepo = async (repoId: string) => {
    await marketplaceService.removeRepo(repoId)
    setRepos((prev) => prev.filter((repo) => repo.id !== repoId))
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Marketplace Repositories</h2>
          <p className="text-sm text-gray-600">
            Manage Git-based application repositories
          </p>
        </div>
        <button
          onClick={() => setIsAddModalOpen(true)}
          className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 transition-colors"
        >
          <Plus className="h-4 w-4" />
          Add Repository
        </button>
      </div>

      {/* Repository List */}
      {isLoading && repos.length === 0 ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      ) : error ? (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      ) : repos.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg border border-gray-200">
          <p className="text-gray-600 mb-4">No repositories configured</p>
          <button
            onClick={() => setIsAddModalOpen(true)}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-blue-600 hover:text-blue-700"
          >
            <Plus className="h-4 w-4" />
            Add your first repository
          </button>
        </div>
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
