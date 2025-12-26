/**
 * Session Table Component
 * 
 * Displays active sessions with sorting and management actions.
 */

import type { Session, SortKey } from '../types'
import { sortSessions } from '../utils'
import { SessionTableHeader } from './SessionTableHeader'
import { SessionRow } from './SessionRow'

interface SessionTableProps {
  sessions: Session[]
  sortBy: SortKey
  sortOrder: 'asc' | 'desc'
  hoveredStatus: string | null
  onSort: (key: SortKey) => void
  onTerminateSession: (sessionId: string) => void
  onRestoreSession: (sessionId: string) => void
  onHoveredStatusChange: (sessionId: string | null) => void
}

export function SessionTable({
  sessions,
  sortBy,
  sortOrder,
  hoveredStatus,
  onSort,
  onTerminateSession,
  onRestoreSession,
  onHoveredStatusChange
}: SessionTableProps) {
  const sortedSessions = sortSessions(sessions, sortBy, sortOrder)

  return (
    <div className="bg-card rounded-lg border p-0 overflow-hidden">
      <div className="p-3 border-b border-border">
        <h4 className="text-sm font-semibold text-primary">Sessions</h4>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-border">
          <SessionTableHeader
            sortBy={sortBy}
            sortOrder={sortOrder}
            onSort={onSort}
          />
          <tbody className="bg-background divide-y divide-border">
            {sortedSessions.map((session) => (
              <SessionRow
                key={session.id}
                session={session}
                hoveredStatus={hoveredStatus}
                onTerminateSession={onTerminateSession}
                onRestoreSession={onRestoreSession}
                onHoveredStatusChange={onHoveredStatusChange}
              />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}