/**
 * Repository Table Sub-Components
 *
 * Reusable table components for the Repository Manager.
 */

import type { ReactNode } from 'react'
import { RefreshCw, Trash2, GitBranch, Globe, Power } from 'lucide-react'
import {
  IconButton,
  Chip,
  Box,
  Typography,
  Stack,
  TableHead,
  TableRow,
  TableCell,
  Tooltip
} from '@mui/material'
import { useTranslation } from 'react-i18next'
import type { MarketplaceRepo } from '@/types/marketplace'

export type SortField = 'name' | 'appCount'
export type SortDirection = 'asc' | 'desc'

/**
 * Get chip color for status
 */
export function getStatusColor(status: string): 'success' | 'warning' | 'error' | 'default' {
  switch (status) {
    case 'active': return 'success'
    case 'syncing': return 'warning'
    case 'error': return 'error'
    case 'disabled': return 'default'
    default: return 'default'
  }
}

interface SortButtonProps {
  field: SortField
  currentField: SortField
  direction: SortDirection
  onSort: (field: SortField) => void
  children: ReactNode
}

function SortButton({ field, currentField, direction, onSort, children }: SortButtonProps) {
  const isActive = currentField === field

  return (
    <Box
      component="button"
      type="button"
      onClick={(e) => {
        e.stopPropagation()
        onSort(field)
      }}
      sx={{
        display: 'inline-flex',
        alignItems: 'center',
        fontSize: '0.75rem',
        fontWeight: 500,
        color: 'text.secondary',
        bgcolor: 'transparent',
        border: 'none',
        cursor: 'pointer',
        transition: 'color 0.2s',
        '&:hover': { color: 'text.primary' }
      }}
    >
      <span>{children}</span>
      <Box component="span" sx={{ fontSize: '0.75rem', ml: 0.5 }}>
        {isActive ? (direction === 'asc' ? '↑' : '↓') : ''}
      </Box>
    </Box>
  )
}

/**
 * Empty state when no repositories exist or match the search
 */
interface RepoEmptyStateProps {
  hasRepos: boolean
}

export function RepoEmptyState({ hasRepos }: RepoEmptyStateProps) {
  const { t } = useTranslation()

  return (
    <Box sx={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <Box sx={{ textAlign: 'center', p: 6 }}>
        <Box sx={{
          width: 64, height: 64, mx: 'auto', borderRadius: 3, bgcolor: 'action.hover',
          display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 2
        }}>
          <Globe style={{ width: 32, height: 32, opacity: 0.5 }} />
        </Box>
        <Typography variant="h6" sx={{ mb: 1 }}>
          {!hasRepos ? t('marketplace.noRepositories') : t('marketplace.noMatchingRepos')}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3, maxWidth: 448, mx: 'auto' }}>
          {!hasRepos ? t('marketplace.noRepositoriesDescription') : t('marketplace.noMatchingReposDescription')}
        </Typography>
      </Box>
    </Box>
  )
}

/**
 * Table row for a single repository
 */
interface RepoTableRowProps {
  repo: MarketplaceRepo
  isSyncing: boolean
  onSync: (repoId: string) => void
  onRemove: (repoId: string) => void
  onToggle: (repoId: string, enabled: boolean) => void
}

export function RepoTableRow({ repo, isSyncing, onSync, onRemove, onToggle }: RepoTableRowProps) {
  const { t } = useTranslation()

  // Show 'disabled' status when repo is not enabled, otherwise show actual status
  const displayStatus = repo.enabled ? repo.status : 'disabled'

  return (
    <TableRow
      sx={{
        borderBottom: 1, borderColor: 'divider',
        transition: 'background-color 0.2s', '&:hover': { bgcolor: 'action.hover' },
        opacity: repo.enabled ? 1 : 0.6
      }}
    >
      <TableCell sx={{ px: 2, py: 1.5 }}>
        <Typography variant="body2" fontWeight={500} noWrap>{repo.name}</Typography>
      </TableCell>
      <TableCell sx={{ px: 2, py: 1.5 }}>
        <Stack direction="row" spacing={0.5} alignItems="center">
          <Globe style={{ width: 14, height: 14, flexShrink: 0, opacity: 0.5 }} />
          <Typography variant="body2" color="text.secondary" noWrap>{repo.url}</Typography>
        </Stack>
      </TableCell>
      <TableCell sx={{ px: 2, py: 1.5 }}>
        <Stack direction="row" spacing={0.5} alignItems="center">
          <GitBranch style={{ width: 14, height: 14, flexShrink: 0, opacity: 0.5 }} />
          <Typography variant="body2" color="text.secondary">{repo.branch}</Typography>
        </Stack>
      </TableCell>
      <TableCell sx={{ px: 2, py: 1.5, textAlign: 'center' }}>
        <Typography variant="body2" color="text.secondary">{repo.appCount}</Typography>
      </TableCell>
      <TableCell sx={{ px: 2, py: 1.5 }}>
        <Chip size="small" label={repo.repoType} variant="outlined" />
      </TableCell>
      <TableCell sx={{ px: 2, py: 1.5 }}>
        <Chip size="small" color={getStatusColor(displayStatus)} label={displayStatus} />
      </TableCell>
      <TableCell sx={{ px: 2, py: 1.5 }}>
        <Stack direction="row" spacing={-0.5} sx={{ justifyContent: 'center', alignItems: 'center' }}>
          <Tooltip title={repo.enabled ? t('marketplace.disableRepository') : t('marketplace.enableRepository')}>
            <IconButton
              size="small"
              onClick={() => onToggle(repo.id, !repo.enabled)}
              disabled={isSyncing}
              sx={{
                width: 24,
                height: 24,
                color: repo.enabled ? 'success.main' : 'text.disabled',
                '&:hover': { color: repo.enabled ? 'error.main' : 'success.main', bgcolor: 'transparent' }
              }}
            >
              <Power style={{ width: 14, height: 14 }} />
            </IconButton>
          </Tooltip>
          <IconButton
            size="small"
            onClick={() => onSync(repo.id)}
            disabled={isSyncing || !repo.enabled}
            title={t('marketplace.syncRepository')}
            sx={{ width: 24, height: 24, color: 'text.secondary', '&:hover': { color: 'text.primary', bgcolor: 'transparent' } }}
          >
            <RefreshCw style={{ width: 14, height: 14 }} className={isSyncing ? 'animate-spin' : ''} />
          </IconButton>
          {repo.repoType !== 'official' && (
            <IconButton
              size="small"
              onClick={() => onRemove(repo.id)}
              disabled={isSyncing}
              title={t('marketplace.removeRepository')}
              sx={{ width: 24, height: 24, color: 'text.secondary', '&:hover': { color: 'error.main', bgcolor: 'transparent' } }}
            >
              <Trash2 style={{ width: 14, height: 14 }} />
            </IconButton>
          )}
        </Stack>
      </TableCell>
    </TableRow>
  )
}

/**
 * Table header for the repository list
 */
interface RepoTableHeaderProps {
  sortField: SortField
  sortDirection: SortDirection
  onSort: (field: SortField) => void
}

export function RepoTableHeader({ sortField, sortDirection, onSort }: RepoTableHeaderProps) {
  const { t } = useTranslation()
  const cellSx = { px: 2, py: 1.5, fontWeight: 500, fontSize: '0.75rem', color: 'text.secondary' }

  return (
    <TableHead>
      <TableRow sx={{ bgcolor: 'action.hover', borderBottom: 1, borderColor: 'divider', position: 'sticky', top: 0 }}>
        <TableCell sx={{ ...cellSx, textAlign: 'left', width: '20%' }}>
          <SortButton field="name" currentField={sortField} direction={sortDirection} onSort={onSort}>
            {t('marketplace.columns.name')}
          </SortButton>
        </TableCell>
        <TableCell sx={{ ...cellSx, textAlign: 'left', width: '30%' }}>
          {t('marketplace.columns.url')}
        </TableCell>
        <TableCell sx={{ ...cellSx, textAlign: 'left', width: '10%' }}>
          {t('marketplace.columns.branch')}
        </TableCell>
        <TableCell sx={{ ...cellSx, textAlign: 'center', width: '8%' }}>
          <SortButton field="appCount" currentField={sortField} direction={sortDirection} onSort={onSort}>
            {t('marketplace.columns.apps')}
          </SortButton>
        </TableCell>
        <TableCell sx={{ ...cellSx, textAlign: 'left', width: '10%' }}>
          {t('marketplace.columns.type')}
        </TableCell>
        <TableCell sx={{ ...cellSx, textAlign: 'left', width: '10%' }}>
          {t('marketplace.columns.status')}
        </TableCell>
        <TableCell sx={{ ...cellSx, textAlign: 'center', width: '12%' }}>
          {t('common.actions')}
        </TableCell>
      </TableRow>
    </TableHead>
  )
}
