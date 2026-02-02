/**
 * Session Table Component
 *
 * Displays active sessions with sorting and management actions.
 */

import { useTranslation } from 'react-i18next'
import { Box, Card, Typography, Table, TableBody } from '@mui/material'
import type { Session, SortKey } from '../types'
import { sortSessions } from '../utils'
import { SessionTableHeader } from './SessionTableHeader'
import { SessionRow } from './SessionRow'

interface SessionTableProps {
  sessions: Session[]
  sortBy: SortKey
  sortOrder: 'asc' | 'desc'
  onSort: (key: SortKey) => void
  onTerminateSession: (sessionId: string) => void
  onRestoreSession: (sessionId: string) => void
}

export function SessionTable({
  sessions,
  sortBy,
  sortOrder,
  onSort,
  onTerminateSession,
  onRestoreSession
}: SessionTableProps) {
  const { t } = useTranslation()
  const sortedSessions = sortSessions(sessions, sortBy, sortOrder)

  return (
    <Card sx={{ overflow: 'hidden' }}>
      <Box sx={{ p: 1.5, borderBottom: 1, borderColor: 'divider' }}>
        <Typography variant="body2" fontWeight={600} color="primary.main">
          {t('settings.securitySettings.sessions')}
        </Typography>
      </Box>
      <Box sx={{ overflow: 'auto' }}>
        <Table size="small">
          <SessionTableHeader
            sortBy={sortBy}
            sortOrder={sortOrder}
            onSort={onSort}
          />
          <TableBody>
            {sortedSessions.map((session) => (
              <SessionRow
                key={session.id}
                session={session}
                onTerminateSession={onTerminateSession}
                onRestoreSession={onRestoreSession}
              />
            ))}
          </TableBody>
        </Table>
      </Box>
    </Card>
  )
}