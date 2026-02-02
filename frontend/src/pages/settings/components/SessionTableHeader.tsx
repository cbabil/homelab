/**
 * Session Table Header Component
 *
 * Table header with sortable columns for session management.
 */

import { useTranslation } from 'react-i18next'
import { TableHead, TableRow } from '@mui/material'
import type { SxProps, Theme } from '@mui/material'
import type { SortKey } from '../types'
import { SortableHeader } from './SortableHeader'

const styles: Record<string, SxProps<Theme>> = {
  thead: {
    bgcolor: 'action.hover'
  }
}

interface SessionTableHeaderProps {
  sortBy: SortKey
  sortOrder: 'asc' | 'desc'
  onSort: (key: SortKey) => void
}

export function SessionTableHeader({
  sortBy,
  sortOrder,
  onSort
}: SessionTableHeaderProps) {
  const { t } = useTranslation()

  return (
    <TableHead sx={styles.thead}>
      <TableRow>
        <SortableHeader
          label={t('settings.sessionTable.status')}
          sortKey="status"
          currentSort={sortBy}
          sortOrder={sortOrder}
          onSort={onSort}
        />
        <SortableHeader
          label={t('settings.sessionTable.sessionId')}
          sortKey="sessionId"
          currentSort={sortBy}
          sortOrder={sortOrder}
          onSort={onSort}
        />
        <SortableHeader
          label={t('settings.sessionTable.started')}
          sortKey="started"
          currentSort={sortBy}
          sortOrder={sortOrder}
          onSort={onSort}
        />
        <SortableHeader
          label={t('settings.sessionTable.lastActivity')}
          sortKey="lastActivity"
          currentSort={sortBy}
          sortOrder={sortOrder}
          onSort={onSort}
        />
        <SortableHeader
          label={t('settings.sessionTable.location')}
          sortKey="location"
          currentSort={sortBy}
          sortOrder={sortOrder}
          onSort={onSort}
        />
        <SortableHeader
          label={t('settings.sessionTable.actions')}
          sortKey="actions"
          currentSort={sortBy}
          sortOrder={sortOrder}
          onSort={onSort}
        />
      </TableRow>
    </TableHead>
  )
}