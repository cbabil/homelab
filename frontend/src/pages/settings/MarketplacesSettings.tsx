/**
 * Marketplaces Settings Component
 *
 * Manage marketplace repositories for app discovery and deployment.
 * Allows adding, syncing, and removing Git-based app repositories.
 */

import { useEffect, useState } from 'react'
import { Plus, RefreshCw, Trash2, GitBranch, Globe, Package, Clock } from 'lucide-react'
import {
  IconButton,
  TextField,
  Chip,
  Card,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Select,
  MenuItem,
  FormControl,
  Alert,
  Box,
  Stack,
  Typography
} from '@mui/material'
import { Button } from '@/components/ui/Button'
import type { MarketplaceRepo, RepoType } from '@/types/marketplace'
import * as marketplaceService from '@/services/marketplaceService'
import { marketplaceLogger } from '@/services/systemLogger'

/**
 * Get chip color for status
 */
function getStatusColor(status: string): 'success' | 'warning' | 'error' | 'default' {
  switch (status) {
    case 'active': return 'success'
    case 'syncing': return 'warning'
    case 'error': return 'error'
    default: return 'default'
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

  const repoTypeOptions = [
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
    <Dialog open={isOpen} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>Add Marketplace Repository</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ pt: 1 }}>
          <Box>
            <Typography variant="body2" fontWeight={500} sx={{ mb: 0.75 }}>Repository Name</Typography>
            <TextField
              size="small"
              fullWidth
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., CasaOS App Store"
            />
          </Box>

          <Box>
            <Typography variant="body2" fontWeight={500} sx={{ mb: 0.75 }}>Git Repository URL</Typography>
            <TextField
              size="small"
              fullWidth
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://github.com/IceWhaleTech/CasaOS-AppStore"
            />
          </Box>

          <Box>
            <Typography variant="body2" fontWeight={500} sx={{ mb: 0.75 }}>Repository Type</Typography>
            <FormControl size="small" fullWidth>
              <Select
                value={repoType}
                onChange={(e) => setRepoType(e.target.value as RepoType)}
              >
                {repoTypeOptions.map((opt) => (
                  <MenuItem key={opt.value} value={opt.value}>{opt.label}</MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>

          <Box>
            <Typography variant="body2" fontWeight={500} sx={{ mb: 0.75 }}>Branch</Typography>
            <TextField
              size="small"
              fullWidth
              value={branch}
              onChange={(e) => setBranch(e.target.value)}
              placeholder="main"
            />
          </Box>

          {error && (
            <Alert severity="error">{error}</Alert>
          )}
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button variant="ghost" onClick={handleClose} disabled={isSubmitting}>
          Cancel
        </Button>
        <Button variant="primary" onClick={handleSubmit} disabled={!name || !url} loading={isSubmitting}>
          Add Repository
        </Button>
      </DialogActions>
    </Dialog>
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
    <Card sx={{ p: 2 }} elevation={1}>
      <Stack direction="row" alignItems="flex-start" justifyContent="space-between" spacing={2}>
        <Box sx={{ flex: 1, minWidth: 0 }}>
          <Stack direction="row" alignItems="center" spacing={1} flexWrap="wrap" sx={{ mb: 1 }}>
            <Typography variant="h6" fontWeight={600} noWrap>{repo.name}</Typography>
            <Chip size="small" color={getStatusColor(repo.status)} label={repo.status} />
            <Chip size="small" color="default" label={repo.repoType} />
          </Stack>

          <Stack spacing={0.5} sx={{ fontSize: '0.875rem', color: 'text.secondary' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
              <Globe style={{ height: 14, width: 14, flexShrink: 0 }} />
              <Typography variant="body2" noWrap>{repo.url}</Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
              <GitBranch style={{ height: 14, width: 14, flexShrink: 0 }} />
              <Typography variant="body2">{repo.branch}</Typography>
            </Box>
            <Stack direction="row" alignItems="center" spacing={2}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
                <Package style={{ height: 14, width: 14, flexShrink: 0 }} />
                <Typography variant="body2">{repo.appCount} apps</Typography>
              </Box>
              {repo.lastSynced && (
                <Typography variant="caption">
                  Synced: {new Date(repo.lastSynced).toLocaleString()}
                </Typography>
              )}
            </Stack>
          </Stack>

          {repo.errorMessage && (
            <Alert severity="error" sx={{ mt: 1, fontSize: '0.75rem' }}>
              {repo.errorMessage}
            </Alert>
          )}
        </Box>

        <Stack direction="row" alignItems="center" spacing={0.5}>
          <IconButton
            size="small"
            onClick={handleSync}
            disabled={isSyncing || repo.status === 'syncing' || isRemoving}
            title="Sync repository"
          >
            <RefreshCw className={`h-4 w-4 ${isSyncing || repo.status === 'syncing' ? 'animate-spin' : ''}`} />
          </IconButton>
          {repo.repoType !== 'official' && (
            <IconButton
              size="small"
              onClick={handleRemove}
              disabled={isRemoving || isSyncing || repo.status === 'syncing'}
              title="Remove repository"
              sx={{ color: 'error.main', '&:hover': { color: 'error.main' } }}
            >
              <Trash2 className="h-4 w-4" />
            </IconButton>
          )}
        </Stack>
      </Stack>
    </Card>
  )
}

/**
 * Marketplaces Settings Component
 */
const syncRateOptions = [
  { label: 'Daily', value: 'daily' },
  { label: 'Weekly', value: 'weekly' },
  { label: 'Monthly', value: 'monthly' }
]

export function MarketplacesSettings() {
  const [repos, setRepos] = useState<MarketplaceRepo[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isAddModalOpen, setIsAddModalOpen] = useState(false)
  const [syncRate, setSyncRate] = useState('monthly')

  useEffect(() => {
    loadRepos()
  }, [])

  const loadRepos = async () => {
    setIsLoading(true)
    setError(null)
    marketplaceLogger.info('Loading marketplace repositories')

    try {
      const data = await marketplaceService.getRepos()
      setRepos(data)
      marketplaceLogger.info(`Loaded ${data.length} marketplace repositories`)
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to load repositories'
      setError(errorMsg)
      marketplaceLogger.error(errorMsg)
    } finally {
      setIsLoading(false)
    }
  }

  const handleAddRepo = async (name: string, url: string, repoType: RepoType, branch: string) => {
    marketplaceLogger.info(`Adding marketplace repository: ${name}`)
    const newRepo = await marketplaceService.addRepo(name, url, repoType, branch)
    setRepos((prev) => [...prev, newRepo])
    marketplaceLogger.info(`Marketplace repository added: ${name}`)
  }

  const handleSyncRepo = async (repoId: string) => {
    const repo = repos.find(r => r.id === repoId)
    marketplaceLogger.info(`Syncing marketplace repository: ${repo?.name || repoId}`)

    try {
      setRepos((prev) =>
        prev.map((r) =>
          r.id === repoId ? { ...r, status: 'syncing' as const } : r
        )
      )

      const result = await marketplaceService.syncRepo(repoId)
      await loadRepos()

      marketplaceLogger.info(`Synced ${result.appCount} apps from ${repo?.name || repoId}`)
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to sync repository'
      marketplaceLogger.error(`Sync failed for ${repo?.name || repoId}: ${errorMsg}`)
      await loadRepos()
      throw err
    }
  }

  const handleRemoveRepo = async (repoId: string) => {
    const repo = repos.find(r => r.id === repoId)
    marketplaceLogger.info(`Removing marketplace repository: ${repo?.name || repoId}`)
    await marketplaceService.removeRepo(repoId)
    setRepos((prev) => prev.filter((r) => r.id !== repoId))
    marketplaceLogger.info(`Marketplace repository removed: ${repo?.name || repoId}`)
  }

  return (
    <Stack spacing={3}>
      {/* Repositories Header */}
      <Stack direction="row" alignItems="center" justifyContent="space-between">
        <Box>
          <Typography variant="h6" fontWeight={600}>Marketplace Repositories</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
            Configure repositories that provide applications for deployment
          </Typography>
        </Box>
        <Stack direction="row" alignItems="center" spacing={1.5}>
          <Stack direction="row" alignItems="center" spacing={1}>
            <Clock style={{ height: 16, width: 16, color: 'var(--mui-palette-text-secondary)' }} />
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <Select
                value={syncRate}
                onChange={(e) => setSyncRate(e.target.value)}
              >
                {syncRateOptions.map((opt) => (
                  <MenuItem key={opt.value} value={opt.value}>{opt.label}</MenuItem>
                ))}
              </Select>
            </FormControl>
          </Stack>
          <Button variant="primary" onClick={() => setIsAddModalOpen(true)} leftIcon={<Plus className="h-4 w-4" />}>
            Add Repository
          </Button>
        </Stack>
      </Stack>

      {isLoading && repos.length === 0 ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 6 }}>
          <Box sx={{
            width: 32,
            height: 32,
            borderRadius: '50%',
            border: 2,
            borderColor: 'primary.main',
            borderBottomColor: 'transparent',
            animation: 'spin 1s linear infinite',
            '@keyframes spin': {
              '0%': { transform: 'rotate(0deg)' },
              '100%': { transform: 'rotate(360deg)' }
            }
          }} />
        </Box>
      ) : error ? (
        <Alert severity="error">{error}</Alert>
      ) : repos.length === 0 ? (
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', py: 8, textAlign: 'center' }}>
          <Package style={{ height: 64, width: 64, color: 'var(--mui-palette-text-secondary)', marginBottom: 16 }} />
          <Typography variant="h6" gutterBottom>No marketplace repositories</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Add a Git repository to start discovering apps
          </Typography>
          <Button variant="primary" onClick={() => setIsAddModalOpen(true)} leftIcon={<Plus className="h-4 w-4" />}>
            Add Repository
          </Button>
        </Box>
      ) : (
        <Stack spacing={1.5}>
          {repos.map((repo) => (
            <RepoListItem
              key={repo.id}
              repo={repo}
              onSync={handleSyncRepo}
              onRemove={handleRemoveRepo}
            />
          ))}
        </Stack>
      )}

      <AddRepoModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        onAdd={handleAddRepo}
      />
    </Stack>
  )
}
