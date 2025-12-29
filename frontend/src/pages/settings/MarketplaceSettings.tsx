/**
 * Marketplace Settings Component
 *
 * Configure marketplace repositories for discovering and installing apps.
 */

import { useState, useEffect } from 'react'
import { Plus, Trash2, RefreshCw, ExternalLink, CheckCircle, AlertCircle, Clock } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { MarketplaceRepo, RepoStatus } from '@/types/marketplace'
import * as marketplaceService from '@/services/marketplaceService'

const OFFICIAL_MARKETPLACE_URL = 'https://github.com/cbabil/homelab-marketplace'

interface AddRepoFormData {
  name: string
  url: string
  branch: string
}

export function MarketplaceSettings() {
  const [repos, setRepos] = useState<MarketplaceRepo[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showAddForm, setShowAddForm] = useState(false)
  const [formData, setFormData] = useState<AddRepoFormData>({ name: '', url: '', branch: 'main' })
  const [submitting, setSubmitting] = useState(false)
  const [syncingId, setSyncingId] = useState<string | null>(null)

  const officialRepo = repos.find(r => r.repoType === 'official')
  const customRepos = repos.filter(r => r.repoType !== 'official')

  useEffect(() => {
    loadRepos()
  }, [])

  const loadRepos = async () => {
    try {
      setLoading(true)
      const result = await marketplaceService.getRepos()
      // Ensure result is an array
      setRepos(Array.isArray(result) ? result : [])
      setError(null)
    } catch (err) {
      console.error('Failed to load repos:', err)
      setError(err instanceof Error ? err.message : 'Failed to load marketplace repositories')
      setRepos([])
    } finally {
      setLoading(false)
    }
  }

  const handleSetupOfficial = async () => {
    try {
      setSubmitting(true)
      await marketplaceService.addRepo(
        'Homelab Marketplace',
        OFFICIAL_MARKETPLACE_URL,
        'official',
        'master'
      )
      await loadRepos()
    } catch (err) {
      setError('Failed to add official marketplace')
    } finally {
      setSubmitting(false)
    }
  }

  const handleAddCustom = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.name || !formData.url) return

    try {
      setSubmitting(true)
      await marketplaceService.addRepo(
        formData.name,
        formData.url,
        'community',
        formData.branch || 'main'
      )
      setFormData({ name: '', url: '', branch: 'main' })
      setShowAddForm(false)
      await loadRepos()
    } catch (err) {
      setError('Failed to add repository')
    } finally {
      setSubmitting(false)
    }
  }

  const handleRemove = async (repoId: string) => {
    if (!confirm('Remove this marketplace repository?')) return

    try {
      await marketplaceService.removeRepo(repoId)
      await loadRepos()
    } catch (err) {
      setError('Failed to remove repository')
    }
  }

  const handleSync = async (repoId: string) => {
    try {
      setSyncingId(repoId)
      await marketplaceService.syncRepo(repoId)
      await loadRepos()
    } catch (err) {
      setError('Failed to sync repository')
    } finally {
      setSyncingId(null)
    }
  }

  const StatusBadge = ({ status }: { status: RepoStatus }) => {
    const config = {
      active: { icon: CheckCircle, class: 'text-green-500', label: 'Active' },
      syncing: { icon: Clock, class: 'text-yellow-500', label: 'Syncing' },
      error: { icon: AlertCircle, class: 'text-red-500', label: 'Error' },
      disabled: { icon: AlertCircle, class: 'text-gray-500', label: 'Disabled' }
    }
    const cfg = config[status] || config.disabled
    const Icon = cfg.icon
    return (
      <span className={`flex items-center gap-1 text-xs ${cfg.class}`}>
        <Icon className="h-3 w-3" />
        {cfg.label}
      </span>
    )
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <RefreshCw className="h-5 w-5 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {error && (
        <div className="bg-destructive/10 text-destructive px-3 py-2 rounded-lg text-sm">
          {error}
        </div>
      )}

      {/* Official Marketplace */}
      <div className="bg-card rounded-lg border p-3">
        <h4 className="text-sm font-semibold mb-3 text-primary">Official Marketplace</h4>

        {officialRepo ? (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="font-medium text-sm">{officialRepo.name}</span>
                <StatusBadge status={officialRepo.status} />
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleSync(officialRepo.id)}
                  disabled={syncingId === officialRepo.id}
                  leftIcon={<RefreshCw className={`h-4 w-4 ${syncingId === officialRepo.id ? 'animate-spin' : ''}`} />}
                >
                  Sync
                </Button>
                <a
                  href={officialRepo.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-muted-foreground hover:text-foreground"
                >
                  <ExternalLink className="h-4 w-4" />
                </a>
              </div>
            </div>
            <p className="text-xs text-muted-foreground">
              {officialRepo.appCount} apps available • Last synced: {
                officialRepo.lastSynced
                  ? new Date(officialRepo.lastSynced).toLocaleString()
                  : 'Never'
              }
            </p>
          </div>
        ) : (
          <div className="text-center py-4">
            <p className="text-sm text-muted-foreground mb-3">
              Connect to the official Homelab Marketplace to discover curated apps.
            </p>
            <Button
              variant="primary"
              size="sm"
              onClick={handleSetupOfficial}
              disabled={submitting}
              leftIcon={<Plus className="h-4 w-4" />}
            >
              {submitting ? 'Adding...' : 'Add Official Marketplace'}
            </Button>
          </div>
        )}
      </div>

      {/* Custom Marketplaces */}
      <div className="bg-card rounded-lg border p-3">
        <div className="flex items-center justify-between mb-3">
          <h4 className="text-sm font-semibold text-primary">Custom Marketplaces</h4>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowAddForm(!showAddForm)}
            leftIcon={<Plus className="h-4 w-4" />}
          >
            Add
          </Button>
        </div>

        {showAddForm && (
          <form onSubmit={handleAddCustom} className="mb-4 p-3 bg-muted rounded-lg space-y-3">
            <div>
              <label className="block text-xs font-medium mb-1">Name</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="My Custom Marketplace"
                className="w-full px-2 py-1.5 text-sm border border-input rounded bg-background"
                required
              />
            </div>
            <div>
              <label className="block text-xs font-medium mb-1">Git Repository URL</label>
              <input
                type="url"
                value={formData.url}
                onChange={(e) => setFormData({ ...formData, url: e.target.value })}
                placeholder="https://github.com/user/marketplace"
                className="w-full px-2 py-1.5 text-sm border border-input rounded bg-background"
                required
              />
            </div>
            <div>
              <label className="block text-xs font-medium mb-1">Branch</label>
              <input
                type="text"
                value={formData.branch}
                onChange={(e) => setFormData({ ...formData, branch: e.target.value })}
                placeholder="main"
                className="w-full px-2 py-1.5 text-sm border border-input rounded bg-background"
              />
            </div>
            <div className="flex gap-2">
              <Button type="submit" variant="primary" size="sm" disabled={submitting}>
                {submitting ? 'Adding...' : 'Add Repository'}
              </Button>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => {
                  setShowAddForm(false)
                  setFormData({ name: '', url: '', branch: 'main' })
                }}
              >
                Cancel
              </Button>
            </div>
          </form>
        )}

        {customRepos.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-4">
            No custom marketplaces configured. Add your own Git repositories to discover more apps.
          </p>
        ) : (
          <div className="space-y-2">
            {customRepos.map((repo) => (
              <div key={repo.id} className="flex items-center justify-between p-2 bg-muted rounded">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-sm">{repo.name}</span>
                    <StatusBadge status={repo.status} />
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {repo.appCount} apps • {repo.branch}
                  </p>
                </div>
                <div className="flex items-center gap-1">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleSync(repo.id)}
                    disabled={syncingId === repo.id}
                  >
                    <RefreshCw className={`h-4 w-4 ${syncingId === repo.id ? 'animate-spin' : ''}`} />
                  </Button>
                  <a
                    href={repo.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="p-1 text-muted-foreground hover:text-foreground"
                  >
                    <ExternalLink className="h-4 w-4" />
                  </a>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleRemove(repo.id)}
                    className="text-destructive hover:text-destructive"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Info */}
      <div className="bg-muted/50 rounded-lg p-3">
        <p className="text-xs text-muted-foreground">
          Marketplace repositories contain YAML app definitions that can be installed to your homelab.
          Custom marketplaces allow you to share apps within your organization or community.
        </p>
      </div>
    </div>
  )
}
