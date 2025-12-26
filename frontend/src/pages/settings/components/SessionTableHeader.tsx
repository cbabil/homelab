/**
 * Session Table Header Component
 * 
 * Table header with sortable columns for session management.
 */

import type { SortKey } from '../types'
import { SortableHeader } from './SortableHeader'

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
  return (
    <thead className="bg-muted/50">
      <tr>
        <SortableHeader 
          label="Status" 
          sortKey="status" 
          currentSort={sortBy} 
          sortOrder={sortOrder} 
          onSort={onSort}
        />
        <SortableHeader 
          label="Session ID" 
          sortKey="sessionId" 
          currentSort={sortBy} 
          sortOrder={sortOrder} 
          onSort={onSort}
        />
        <SortableHeader 
          label="Started" 
          sortKey="started" 
          currentSort={sortBy} 
          sortOrder={sortOrder} 
          onSort={onSort}
        />
        <SortableHeader 
          label="Last Activity" 
          sortKey="lastActivity" 
          currentSort={sortBy} 
          sortOrder={sortOrder} 
          onSort={onSort}
        />
        <SortableHeader 
          label="Location" 
          sortKey="location" 
          currentSort={sortBy} 
          sortOrder={sortOrder} 
          onSort={onSort}
        />
        <SortableHeader 
          label="Actions" 
          sortKey="actions" 
          currentSort={sortBy} 
          sortOrder={sortOrder} 
          onSort={onSort}
        />
      </tr>
    </thead>
  )
}