/**
 * Audit Table Row Component
 *
 * Expandable row component for displaying audit entry details.
 */

import { Fragment } from 'react'
import { useTranslation } from 'react-i18next'
import {
  Box,
  TableCell,
  TableRow,
  Typography,
  Chip,
  IconButton,
  Collapse
} from '@mui/material'
import { ChevronDown, ChevronRight } from 'lucide-react'
import type { AgentAuditEntry } from '@/services/auditMcpClient'

interface LevelBadgeProps {
  level: string
}

/**
 * Level badge with color coding
 */
export function LevelBadge({ level }: LevelBadgeProps) {
  const colorMap: Record<string, 'success' | 'warning' | 'error' | 'default'> = {
    INFO: 'success',
    WARNING: 'warning',
    ERROR: 'error'
  }
  const color = colorMap[level.toUpperCase()] || 'default'

  return (
    <Chip
      label={level}
      size="small"
      color={color}
      sx={{ height: 20, fontSize: '0.7rem', '& .MuiChip-label': { px: 1 } }}
    />
  )
}

interface AuditTableRowProps {
  entry: AgentAuditEntry
  isExpanded: boolean
  onToggle: () => void
  formatTimestamp: (ts: string) => string
}

/**
 * Expandable row component for showing entry details
 */
export function AuditTableRow({ entry, isExpanded, onToggle, formatTimestamp }: AuditTableRowProps) {
  const { t } = useTranslation()
  const hasDetails = entry.details && Object.keys(entry.details).length > 0

  return (
    <Fragment>
      <TableRow
        hover
        onClick={hasDetails ? onToggle : undefined}
        sx={{
          cursor: hasDetails ? 'pointer' : 'default',
          '& td': { py: 1, borderBottom: isExpanded ? 0 : undefined }
        }}
      >
        <TableCell sx={{ width: 32, pr: 0 }}>
          {hasDetails && (
            <IconButton size="small" sx={{ p: 0.25 }}>
              {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
            </IconButton>
          )}
        </TableCell>
        <TableCell sx={{ whiteSpace: 'nowrap' }}>
          <Typography variant="body2" color="text.secondary">
            {formatTimestamp(entry.timestamp)}
          </Typography>
        </TableCell>
        <TableCell>
          <Typography variant="body2" fontWeight={500}>
            {entry.server_name || entry.server_id}
          </Typography>
        </TableCell>
        <TableCell>
          <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
            {entry.event_type}
          </Typography>
        </TableCell>
        <TableCell>
          <LevelBadge level={entry.level} />
        </TableCell>
        <TableCell sx={{ maxWidth: 300 }}>
          <Typography variant="body2" noWrap title={entry.message}>
            {entry.message}
          </Typography>
        </TableCell>
        <TableCell sx={{ width: 60 }}>
          <Chip
            label={entry.success ? t('common.success') : t('common.failed')}
            size="small"
            color={entry.success ? 'success' : 'error'}
            variant="outlined"
            sx={{ height: 20, fontSize: '0.65rem' }}
          />
        </TableCell>
      </TableRow>

      {hasDetails && (
        <TableRow>
          <TableCell colSpan={7} sx={{ py: 0, bgcolor: 'action.hover' }}>
            <Collapse in={isExpanded} timeout="auto" unmountOnExit>
              <Box sx={{ py: 2, px: 3 }}>
                <Typography variant="caption" fontWeight={600} color="text.secondary" sx={{ mb: 1, display: 'block' }}>
                  {t('audit.details')}
                </Typography>
                <Box
                  component="pre"
                  sx={{
                    m: 0, p: 1.5, bgcolor: 'background.paper', borderRadius: 1, border: 1,
                    borderColor: 'divider', fontSize: '0.75rem', fontFamily: 'monospace', overflow: 'auto', maxHeight: 200
                  }}
                >
                  {JSON.stringify(entry.details, null, 2)}
                </Box>
                {entry.tags.length > 0 && (
                  <Box sx={{ mt: 1.5 }}>
                    <Typography variant="caption" color="text.secondary" sx={{ mr: 1 }}>
                      {t('audit.tags')}:
                    </Typography>
                    {entry.tags.map((tag) => (
                      <Chip key={tag} label={tag} size="small" sx={{ mr: 0.5, height: 18, fontSize: '0.65rem' }} />
                    ))}
                  </Box>
                )}
              </Box>
            </Collapse>
          </TableCell>
        </TableRow>
      )}
    </Fragment>
  )
}
