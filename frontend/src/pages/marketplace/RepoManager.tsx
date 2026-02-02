/**
 * Repository Manager Component
 *
 * Manages marketplace repositories with CRUD operations and sync functionality.
 * Uses DataTable for consistent design with other pages.
 */

import { useEffect, useState, useMemo, useRef, forwardRef, useImperativeHandle } from 'react'
import { Alert, Box, Typography, Table, TableBody } from '@mui/material'
import { useTranslation } from 'react-i18next'
import { TablePagination } from '@/components/ui/TablePagination'
import { useDynamicRowCount } from '@/hooks/useDynamicRowCount'
import type { MarketplaceRepo, RepoType } from '@/types/marketplace'
import * as marketplaceService from '@/services/marketplaceService'
import { marketplaceLogger } from '@/services/systemLogger'
import { AddRepoModal } from './AddRepoModal'
import {
  RepoEmptyState,
  RepoTableRow,
  RepoTableHeader,
  type SortField,
  type SortDirection
} from './RepoTableComponents'

export interface RepoManagerRef {
  refresh: () => Promise<void>
}

interface RepoManagerProps {
  searchQuery?: string
  isAddModalOpen?: boolean
  onAddModalClose?: () => void
}

export const RepoManager = forwardRef<RepoManagerRef, RepoManagerProps>(function RepoManager(
  { searchQuery = '', isAddModalOpen = false, onAddModalClose },
  ref
) {
  const { t } = useTranslation()
  const containerRef = useRef<HTMLDivElement>(null)
  const [repos, setRepos] = useState<MarketplaceRepo[]>([])
  const [error, setError] = useState<string | null>(null)
  const [syncingRepoIds, setSyncingRepoIds] = useState<Set<string>>(new Set())
  const [sortField, setSortField] = useState<SortField>('name')
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc')
  const [currentPage, setCurrentPage] = useState(1)

  // Dynamic row count based on container height
  const ITEMS_PER_PAGE = useDynamicRowCount(containerRef, { rowHeight: 52 })

  // Expose refresh method via ref
  useImperativeHandle(ref, () => ({
    refresh: loadRepos
  }))

  // Load repositories on mount
  useEffect(() => {
    loadRepos()
  }, [])

  const loadRepos = async () => {
    setError(null)
    marketplaceLogger.info('Loading repositories')

    try {
      const data = await marketplaceService.getRepos()
      setRepos(data)
      marketplaceLogger.info(`Loaded ${data.length} repositories`)
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : t('marketplace.errors.loadFailed')
      setError(errorMsg)
      marketplaceLogger.error(errorMsg)
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
      setSyncingRepoIds(prev => new Set(prev).add(repoId))
      setRepos((prev) =>
        prev.map((r) =>
          r.id === repoId ? { ...r, status: 'syncing' as const } : r
        )
      )

      const result = await marketplaceService.syncRepo(repoId)
      await loadRepos()
      marketplaceLogger.info(`Synced ${result.appCount} apps from ${repo?.name || repoId}`)
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : t('marketplace.errors.syncFailed')
      marketplaceLogger.error(`Sync failed for ${repo?.name || repoId}: ${errorMsg}`)
      await loadRepos()
    } finally {
      setSyncingRepoIds(prev => {
        const next = new Set(prev)
        next.delete(repoId)
        return next
      })
    }
  }

  const handleRemoveRepo = async (repoId: string) => {
    const repo = repos.find(r => r.id === repoId)
    if (!confirm(t('marketplace.confirmRemoveRepo', { name: repo?.name }))) {
      return
    }

    marketplaceLogger.info(`Removing repository: ${repo?.name || repoId}`)
    await marketplaceService.removeRepo(repoId)
    setRepos((prev) => prev.filter((r) => r.id !== repoId))
    marketplaceLogger.info(`Repository removed: ${repo?.name || repoId}`)
  }

  const handleToggleRepo = async (repoId: string, enabled: boolean) => {
    const repo = repos.find(r => r.id === repoId)
    const action = enabled ? 'Enabling' : 'Disabling'
    marketplaceLogger.info(`${action} repository: ${repo?.name || repoId}`)

    try {
      // Optimistically update UI
      setRepos((prev) =>
        prev.map((r) =>
          r.id === repoId ? { ...r, enabled } : r
        )
      )

      await marketplaceService.toggleRepo(repoId, enabled)
      const actionDone = enabled ? 'enabled' : 'disabled'
      marketplaceLogger.info(`Repository ${actionDone}: ${repo?.name || repoId}`)
    } catch (err) {
      // Revert on error
      setRepos((prev) =>
        prev.map((r) =>
          r.id === repoId ? { ...r, enabled: !enabled } : r
        )
      )
      const errorMsg = err instanceof Error ? err.message : t('marketplace.errors.toggleFailed')
      marketplaceLogger.error(`Toggle failed for ${repo?.name || repoId}: ${errorMsg}`)
      setError(errorMsg)
    }
  }

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection('asc')
    }
    setCurrentPage(1)
  }

  // Filtered repos by search
  const filteredRepos = useMemo(() => {
    if (!searchQuery.trim()) return repos
    const query = searchQuery.toLowerCase()
    return repos.filter(
      (repo) =>
        repo.name.toLowerCase().includes(query) ||
        repo.url.toLowerCase().includes(query) ||
        repo.branch.toLowerCase().includes(query) ||
        repo.repoType.toLowerCase().includes(query)
    )
  }, [repos, searchQuery])

  // Sorted repos
  const sortedRepos = useMemo(() => {
    return [...filteredRepos].sort((a, b) => {
      let comparison = 0
      switch (sortField) {
        case 'name':
          comparison = a.name.localeCompare(b.name)
          break
        case 'appCount':
          comparison = a.appCount - b.appCount
          break
      }
      return sortDirection === 'asc' ? comparison : -comparison
    })
  }, [filteredRepos, sortField, sortDirection])

  // Pagination
  const totalPages = Math.ceil(sortedRepos.length / ITEMS_PER_PAGE)
  const paginatedRepos = useMemo(() => {
    const start = (currentPage - 1) * ITEMS_PER_PAGE
    return sortedRepos.slice(start, start + ITEMS_PER_PAGE)
  }, [sortedRepos, currentPage, ITEMS_PER_PAGE])

  // Reset page when items per page or search changes
  useEffect(() => {
    setCurrentPage(1)
  }, [ITEMS_PER_PAGE, searchQuery])

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Repository count */}
      <Typography variant="body2" color="text.secondary" fontWeight={600} sx={{ mb: 2 }}>
        {searchQuery
          ? t('marketplace.repositoryCountFiltered', { filtered: filteredRepos.length, total: repos.length })
          : t('marketplace.repositoryCount', { count: repos.length })}
      </Typography>

      {/* Error */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Repository Table */}
      <Box ref={containerRef} sx={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        {filteredRepos.length === 0 ? (
          <RepoEmptyState hasRepos={repos.length > 0} />
        ) : (
          <Box sx={{ flex: 1, overflow: 'auto' }}>
            <Table sx={{ tableLayout: 'fixed' }}>
              <RepoTableHeader
                sortField={sortField}
                sortDirection={sortDirection}
                onSort={handleSort}
              />
              <TableBody>
                {paginatedRepos.map((repo) => (
                  <RepoTableRow
                    key={repo.id}
                    repo={repo}
                    isSyncing={syncingRepoIds.has(repo.id) || repo.status === 'syncing'}
                    onSync={handleSyncRepo}
                    onRemove={handleRemoveRepo}
                    onToggle={handleToggleRepo}
                  />
                ))}
              </TableBody>
            </Table>
          </Box>
        )}
      </Box>

      {/* Pagination */}
      {repos.length > 0 && (
        <TablePagination
          currentPage={currentPage}
          totalPages={totalPages}
          onPageChange={setCurrentPage}
        />
      )}

      {/* Add Repository Modal */}
      <AddRepoModal
        isOpen={isAddModalOpen}
        onClose={onAddModalClose ?? (() => {})}
        onAdd={handleAddRepo}
      />
    </Box>
  )
})
