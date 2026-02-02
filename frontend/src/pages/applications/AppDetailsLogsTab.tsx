/**
 * App Details Logs Tab Component
 *
 * Logs tab content showing filtered application logs with pagination.
 */

import { RefObject } from 'react'
import { useTranslation } from 'react-i18next'
import { RefreshCw, FileText, AlertCircle, ChevronLeft, ChevronRight } from 'lucide-react'
import { Box, IconButton, Typography, Alert, Stack } from '@mui/material'
import { LogEntry as LogEntryType } from '@/types/logs'
import { SeverityIndicator } from '@/pages/logs/SeverityIndicator'
import { formatLogTimestamp } from '@/utils/timezone'

interface AppDetailsLogsTabProps {
  logs: LogEntryType[]
  paginatedLogs: LogEntryType[]
  logsLoading: boolean
  logsError: string | null
  logsPage: number
  totalLogsPages: number
  userTimezone: string
  onPageChange: (page: number) => void
  logsContainerRef: RefObject<HTMLDivElement | null>
}

export function AppDetailsLogsTab({
  logs,
  paginatedLogs,
  logsLoading,
  logsError,
  logsPage,
  totalLogsPages,
  userTimezone,
  onPageChange,
  logsContainerRef
}: AppDetailsLogsTabProps) {
  const { t } = useTranslation()

  return (
    <Box ref={logsContainerRef} sx={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
      {/* Header */}
      <Stack direction="row" spacing={1} sx={{ mb: 1.5, flexShrink: 0, alignItems: 'center' }}>
        <FileText size={16} style={{ opacity: 0.5 }} />
        <Typography variant="caption" color="text.secondary">
          {logs.length > 0
            ? t('applications.logs.entries', { count: logs.length })
            : t('applications.logs.noLogs')}
        </Typography>
      </Stack>

      {/* Error state */}
      {logsError && (
        <Alert severity="error" icon={<AlertCircle size={16} />} sx={{ mb: 1.5, flexShrink: 0 }}>
          <Typography variant="body2">{logsError}</Typography>
        </Alert>
      )}

      {/* Loading state */}
      {logsLoading && logs.length === 0 && (
        <Box
          sx={{
            flex: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}
        >
          <RefreshCw size={20} className="animate-spin" style={{ opacity: 0.5 }} />
        </Box>
      )}

      {/* Empty state */}
      {!logsLoading && !logsError && logs.length === 0 && (
        <Box
          sx={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            textAlign: 'center'
          }}
        >
          <FileText size={40} style={{ opacity: 0.5, marginBottom: 8 }} />
          <Typography variant="body2" color="text.secondary">
            {t('applications.logs.noLogsForApp')}
          </Typography>
        </Box>
      )}

      {/* Logs Table */}
      {logs.length > 0 && (
        <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
          {/* Column Headers */}
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              py: 0.75,
              borderBottom: 1,
              borderColor: 'divider',
              flexShrink: 0
            }}
          >
            <Box sx={{ width: 64, flexShrink: 0 }}>
              <Typography variant="caption" fontWeight={500} color="text.secondary">
                {t('applications.logs.level')}
              </Typography>
            </Box>
            <Box sx={{ flex: 1, minWidth: 0 }}>
              <Typography variant="caption" fontWeight={500} color="text.secondary">
                {t('applications.logs.message')}
              </Typography>
            </Box>
            <Box sx={{ width: 176, flexShrink: 0, textAlign: 'right' }}>
              <Typography variant="caption" fontWeight={500} color="text.secondary">
                {t('applications.logs.time')}
              </Typography>
            </Box>
          </Box>

          {/* Log Rows */}
          <Box sx={{ flex: 1, overflow: 'hidden' }}>
            {paginatedLogs.map((log, index) => (
              <Box
                key={log.id}
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  py: 0.25,
                  bgcolor: index % 2 === 1 ? 'action.hover' : 'transparent',
                  '&:hover': {
                    bgcolor: 'action.selected'
                  },
                  transition: 'background-color 0.2s'
                }}
              >
                <Box sx={{ width: 64, flexShrink: 0 }}>
                  <SeverityIndicator level={log.level} className="scale-75 origin-left" />
                </Box>
                <Box sx={{ flex: 1, minWidth: 0, pr: 1 }}>
                  <Typography
                    variant="caption"
                    sx={{
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                      display: 'block',
                      color:
                        log.level === 'error' || log.level === 'critical'
                          ? 'error.main'
                          : 'text.primary'
                    }}
                    title={log.message}
                  >
                    {log.message}
                  </Typography>
                </Box>
                <Box sx={{ width: 176, flexShrink: 0, textAlign: 'right' }}>
                  <Typography variant="caption" color="text.secondary" sx={{ whiteSpace: 'nowrap' }}>
                    {formatLogTimestamp(log.timestamp, userTimezone)}
                  </Typography>
                </Box>
              </Box>
            ))}
          </Box>

          {/* Pagination */}
          {totalLogsPages > 1 && (
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                pt: 1.5,
                borderTop: 1,
                borderColor: 'divider',
                mt: 1.5,
                flexShrink: 0
              }}
            >
              <Typography variant="caption" color="text.secondary">
                {t('applications.logs.pageOf', { current: logsPage, total: totalLogsPages })}
              </Typography>
              <Stack direction="row" spacing={0.5}>
                <IconButton
                  size="small"
                  onClick={() => onPageChange(Math.max(1, logsPage - 1))}
                  disabled={logsPage === 1}
                  sx={{ width: 28, height: 28 }}
                >
                  <ChevronLeft size={16} />
                </IconButton>
                <IconButton
                  size="small"
                  onClick={() => onPageChange(Math.min(totalLogsPages, logsPage + 1))}
                  disabled={logsPage === totalLogsPages}
                  sx={{ width: 28, height: 28 }}
                >
                  <ChevronRight size={16} />
                </IconButton>
              </Stack>
            </Box>
          )}
        </Box>
      )}
    </Box>
  )
}
