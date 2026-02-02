/**
 * Notification Item Component
 *
 * Individual notification item with actions for mark as read and remove.
 */

import { Check, X, AlertCircle, CheckCircle, Info, AlertTriangle } from 'lucide-react'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import IconButton from '@mui/material/IconButton'
import { useTheme } from '@mui/material/styles'

interface Notification {
  id: string
  type: 'info' | 'success' | 'warning' | 'error'
  title: string
  message: string
  timestamp: Date
  read: boolean
}

interface NotificationItemProps {
  notification: Notification
  onMarkAsRead: (id: string) => void
  onRemove: (id: string) => void
}

const iconMap = {
  error: AlertCircle,
  success: CheckCircle,
  warning: AlertTriangle,
  info: Info
}

function formatTime(timestamp: Date): string {
  const now = new Date()
  const diff = now.getTime() - timestamp.getTime()
  const minutes = Math.floor(diff / (1000 * 60))

  if (minutes < 1) return 'Just now'
  if (minutes < 60) return `${minutes}m ago`

  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`

  const days = Math.floor(hours / 24)
  return `${days}d ago`
}

export function NotificationItem({ notification, onMarkAsRead, onRemove }: NotificationItemProps) {
  const theme = useTheme()
  const Icon = iconMap[notification.type]

  const iconColorMap = {
    error: theme.palette.error.main,
    success: theme.palette.success.main,
    warning: theme.palette.warning.main,
    info: theme.palette.info.main,
  }

  return (
    <Box
      sx={{
        p: 2,
        bgcolor: !notification.read ? 'action.hover' : 'transparent',
        transition: 'background-color 0.2s',
        '&:hover': {
          bgcolor: 'action.selected',
        },
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1.5 }}>
        <Box
          sx={{
            mt: 0.25,
            color: iconColorMap[notification.type],
            display: 'flex',
            flexShrink: 0,
          }}
        >
          <Icon style={{ width: 16, height: 16 }} />
        </Box>
        <Box sx={{ flex: 1, minWidth: 0 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Typography
              variant="body2"
              sx={{
                fontWeight: 500,
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}
            >
              {notification.title}
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, ml: 1, flexShrink: 0 }}>
              {!notification.read && (
                <IconButton
                  onClick={() => onMarkAsRead(notification.id)}
                  size="small"
                  title="Mark as read"
                  sx={{ width: 24, height: 24 }}
                >
                  <Check style={{ width: 12, height: 12 }} />
                </IconButton>
              )}
              <IconButton
                onClick={() => onRemove(notification.id)}
                size="small"
                title="Remove"
                sx={{ width: 24, height: 24, color: 'text.secondary' }}
              >
                <X style={{ width: 12, height: 12 }} />
              </IconButton>
            </Box>
          </Box>
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{
              mt: 0.5,
              display: '-webkit-box',
              WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical',
              overflow: 'hidden',
            }}
          >
            {notification.message}
          </Typography>
          <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
            {formatTime(notification.timestamp)}
          </Typography>
        </Box>
      </Box>
    </Box>
  )
}
