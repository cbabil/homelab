/**
 * Session Row Component
 *
 * Individual session row with status, actions, and hover tooltip.
 */

import { useTranslation } from 'react-i18next'
import { Trash2, RotateCcw, User } from 'lucide-react'
import { Box, Stack, Typography, Chip, TableRow, TableCell, Tooltip } from '@mui/material'
import type { Session } from '../types'
import { formatDateTime, formatTimeAgo } from '../utils'
import { useAuth } from '@/providers/AuthProvider'
import { Button } from '@/components/ui/Button'

interface SessionRowProps {
  session: Session
  onTerminateSession: (sessionId: string) => void
  onRestoreSession: (sessionId: string) => void
}

export function SessionRow({
  session,
  onTerminateSession,
  onRestoreSession
}: SessionRowProps) {
  const { t } = useTranslation()
  // Get current user from auth context
  const { user } = useAuth()

  // Determine if this is the current session by checking if location contains "Current"
  // In a real implementation, this would be a proper flag from the session data
  const isCurrentSession = session.location.includes('Current') || session.location.includes('current')

  // Check if user is admin
  const isAdmin = user?.role === 'admin'

  // Can terminate session if user is admin and it's not the current session
  const canTerminate = isAdmin && !isCurrentSession && session.status === 'active'

  const statusColorMap: Record<string, string> = {
    active: 'success.main',
    expired: 'warning.main',
    terminated: 'error.main'
  }

  return (
    <TableRow sx={{ '&:hover': { bgcolor: 'action.hover' } }}>
      <TableCell sx={{ px: 2, py: 1.5 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Tooltip title={session.status.charAt(0).toUpperCase() + session.status.slice(1)}>
            <Box
              sx={{
                width: 8,
                height: 8,
                borderRadius: '50%',
                bgcolor: statusColorMap[session.status] || 'grey.500',
                cursor: 'help'
              }}
            />
          </Tooltip>
        </Box>
      </TableCell>
      <TableCell sx={{ px: 2, py: 1.5 }}>
        <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
          {session.id}
        </Typography>
      </TableCell>
      <TableCell sx={{ px: 2, py: 1.5 }}>
        <Typography variant="body2" color="text.secondary">
          {formatDateTime(session.started)}
        </Typography>
      </TableCell>
      <TableCell sx={{ px: 2, py: 1.5 }}>
        <Typography variant="body2" color="text.secondary">
          {formatTimeAgo(session.lastActivity)}
        </Typography>
      </TableCell>
      <TableCell sx={{ px: 2, py: 1.5 }}>
        <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
          {session.ip}
        </Typography>
      </TableCell>
      <TableCell sx={{ px: 2, py: 1.5 }}>
        <Stack direction="row" spacing={1} alignItems="center" justifyContent="center">
          {/* Check if this is the current session */}
          {isCurrentSession ? (
            <Chip
              icon={<User style={{ width: 12, height: 12 }} />}
              label={t('settings.sessionTable.you')}
              size="small"
              sx={{
                height: 24,
                fontSize: 11,
                fontWeight: 500,
                bgcolor: 'info.light',
                color: 'info.dark',
                '& .MuiChip-icon': {
                  marginLeft: 0.5,
                  color: 'inherit'
                }
              }}
            />
          ) : (
            <>
              {session.status === 'terminated' ? (
                <Typography variant="caption" color="text.secondary" sx={{ px: 1, py: 0.5 }}>
                  {t('settings.sessionTable.terminated')}
                </Typography>
              ) : session.status === 'expired' ? (
                isAdmin ? (
                  <Button
                    onClick={() => onRestoreSession(session.id)}
                    variant="ghost"
                    size="icon"
                    sx={{
                      color: 'info.main',
                      '&:hover': {
                        color: 'info.dark',
                        bgcolor: 'info.light'
                      }
                    }}
                    title={t('settings.sessionTable.restoreSession')}
                  >
                    <RotateCcw className="h-4 w-4" />
                  </Button>
                ) : (
                  <Typography variant="caption" color="text.secondary" sx={{ px: 1, py: 0.5 }}>
                    {t('settings.sessionTable.expired')}
                  </Typography>
                )
              ) : (
                canTerminate ? (
                  <Button
                    onClick={() => onTerminateSession(session.id)}
                    variant="ghost"
                    size="icon"
                    sx={{
                      color: 'error.main',
                      '&:hover': {
                        color: 'error.dark',
                        bgcolor: 'error.light'
                      }
                    }}
                    title={t('settings.sessionTable.terminateSession')}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                ) : (
                  <Typography variant="caption" color="text.secondary" sx={{ px: 1, py: 0.5 }}>
                    {!isAdmin ? t('settings.sessionTable.adminOnly') : t('settings.sessionTable.active')}
                  </Typography>
                )
              )}
            </>
          )}
        </Stack>
      </TableCell>
    </TableRow>
  )
}