/**
 * Agent Audit Table Component
 *
 * Displays agent audit log entries with filtering, expandable rows for details,
 * and color-coded severity levels. Follows MUI patterns from the codebase.
 */

import { useState, useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import {
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography
} from '@mui/material'
import type { AgentAuditEntry, AgentAuditFilters } from '@/services/auditMcpClient'
import type { ServerConnection } from '@/types/server'
import { useSettingsContext } from '@/providers/SettingsProvider'
import { formatLogTimestamp } from '@/utils/timezone'
import { AuditTableRow } from './AuditTableRow'
import { AuditFilterControls } from './AuditFilterControls'
import { AuditLoadingState, AuditEmptyState, AuditErrorState } from './AuditTableStates'

export interface AgentAuditTableProps {
  entries: AgentAuditEntry[]
  isLoading: boolean
  error: string | null
  filters: AgentAuditFilters
  onFilterChange: (filters: AgentAuditFilters) => void
  onRefresh: () => Promise<void>
  compact?: boolean
  servers: ServerConnection[]
}

/**
 * Table header component
 */
function AuditTableHeader() {
  const { t } = useTranslation()
  return (
    <TableHead>
      <TableRow>
        <TableCell sx={{ width: 32, bgcolor: 'background.paper' }} />
        <TableCell sx={{ bgcolor: 'background.paper', whiteSpace: 'nowrap' }}>
          <Typography variant="caption" fontWeight={600} color="text.secondary">
            {t('audit.columns.timestamp')}
          </Typography>
        </TableCell>
        <TableCell sx={{ bgcolor: 'background.paper' }}>
          <Typography variant="caption" fontWeight={600} color="text.secondary">
            {t('audit.columns.server')}
          </Typography>
        </TableCell>
        <TableCell sx={{ bgcolor: 'background.paper' }}>
          <Typography variant="caption" fontWeight={600} color="text.secondary">
            {t('audit.columns.event')}
          </Typography>
        </TableCell>
        <TableCell sx={{ bgcolor: 'background.paper' }}>
          <Typography variant="caption" fontWeight={600} color="text.secondary">
            {t('audit.columns.level')}
          </Typography>
        </TableCell>
        <TableCell sx={{ bgcolor: 'background.paper' }}>
          <Typography variant="caption" fontWeight={600} color="text.secondary">
            {t('audit.columns.message')}
          </Typography>
        </TableCell>
        <TableCell sx={{ bgcolor: 'background.paper', width: 60 }}>
          <Typography variant="caption" fontWeight={600} color="text.secondary">
            {t('audit.columns.status')}
          </Typography>
        </TableCell>
      </TableRow>
    </TableHead>
  )
}

/**
 * Main Agent Audit Table Component
 */
export function AgentAuditTable({
  entries,
  isLoading,
  error,
  filters,
  onFilterChange,
  onRefresh,
  compact = false,
  servers
}: AgentAuditTableProps) {
  const { settings } = useSettingsContext()
  const userTimezone = settings?.ui.timezone || 'UTC'
  const [expandedId, setExpandedId] = useState<string | null>(null)

  const formatTimestamp = useMemo(
    () => (timestamp: string) => formatLogTimestamp(timestamp, userTimezone),
    [userTimezone]
  )

  const handleToggleExpand = (id: string) => {
    setExpandedId((prev) => (prev === id ? null : id))
  }

  if (error) {
    return <AuditErrorState error={error} />
  }

  return (
    <Box sx={{ bgcolor: 'background.paper', borderRadius: 2, border: 1, borderColor: 'divider', overflow: 'hidden' }}>
      {!compact && (
        <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
          <AuditFilterControls
            filters={filters}
            onFilterChange={onFilterChange}
            onRefresh={onRefresh}
            isLoading={isLoading}
            servers={servers}
          />
        </Box>
      )}

      {isLoading ? (
        <AuditLoadingState />
      ) : entries.length === 0 ? (
        <AuditEmptyState />
      ) : (
        <TableContainer sx={{ maxHeight: compact ? 300 : 600 }}>
          <Table stickyHeader size="small">
            <AuditTableHeader />
            <TableBody>
              {entries.map((entry) => (
                <AuditTableRow
                  key={entry.id}
                  entry={entry}
                  isExpanded={expandedId === entry.id}
                  onToggle={() => handleToggleExpand(entry.id)}
                  formatTimestamp={formatTimestamp}
                />
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  )
}
