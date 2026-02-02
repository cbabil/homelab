/**
 * Notification Dropdown Component
 *
 * Displays notification list in a dropdown menu with actions.
 */

import { useState, useRef, useEffect } from 'react'
import { Bell } from 'lucide-react'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import IconButton from '@mui/material/IconButton'
import Badge from '@mui/material/Badge'
import Paper from '@mui/material/Paper'
import Divider from '@mui/material/Divider'
import MuiButton from '@mui/material/Button'
import { NotificationItem } from '@/components/ui/NotificationItem'
import { useNotifications } from '@/providers/NotificationProvider'

export function NotificationDropdown() {
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const { notifications, unreadCount, markAsRead, markAllAsRead, removeNotification, clearAll } = useNotifications()

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  return (
    <Box sx={{ position: 'relative' }} ref={dropdownRef}>
      <IconButton
        onClick={() => setIsOpen(!isOpen)}
        title="Notifications"
        sx={{
          color: 'text.secondary',
          '&:hover': {
            color: 'text.primary',
          },
        }}
      >
        <Badge
          badgeContent={unreadCount}
          color="error"
          sx={{
            '& .MuiBadge-badge': {
              fontSize: '0.625rem',
              height: 12,
              minWidth: 12,
              padding: '0 2px',
            },
          }}
        >
          <Bell style={{ width: 20, height: 20 }} />
        </Badge>
      </IconButton>

      {isOpen && (
        <Paper
          elevation={3}
          sx={{
            position: 'absolute',
            right: 0,
            mt: 1,
            width: 320,
            borderRadius: 2,
            zIndex: 1300,
            maxHeight: '80vh',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          <Box sx={{ p: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Typography variant="h6" sx={{ fontSize: '1.125rem', fontWeight: 600 }}>
                Notifications
              </Typography>
              {notifications.length > 0 && (
                <Box sx={{ display: 'flex', gap: 1 }}>
                  {unreadCount > 0 && (
                    <MuiButton
                      onClick={markAllAsRead}
                      size="small"
                      sx={{
                        minWidth: 'auto',
                        p: 0,
                        fontSize: '0.75rem',
                        textTransform: 'none',
                        color: 'primary.main',
                        '&:hover': {
                          textDecoration: 'underline',
                          bgcolor: 'transparent',
                        },
                      }}
                    >
                      Mark all read
                    </MuiButton>
                  )}
                  <MuiButton
                    onClick={clearAll}
                    size="small"
                    sx={{
                      minWidth: 'auto',
                      p: 0,
                      fontSize: '0.75rem',
                      textTransform: 'none',
                      color: 'text.secondary',
                      '&:hover': {
                        textDecoration: 'underline',
                        bgcolor: 'transparent',
                      },
                    }}
                  >
                    Clear all
                  </MuiButton>
                </Box>
              )}
            </Box>
            {unreadCount > 0 && (
              <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                {unreadCount} unread notification{unreadCount !== 1 ? 's' : ''}
              </Typography>
            )}
          </Box>

          <Divider />

          <Box sx={{ maxHeight: 384, overflowY: 'auto' }}>
            {notifications.length === 0 ? (
              <Box sx={{ p: 4, textAlign: 'center' }}>
                <Bell
                  style={{
                    width: 48,
                    height: 48,
                    margin: '0 auto 12px',
                    color: 'rgba(0, 0, 0, 0.38)',
                  }}
                />
                <Typography variant="body2" color="text.secondary">
                  No notifications
                </Typography>
              </Box>
            ) : (
              <Box>
                {notifications.map((notification, index) => (
                  <Box key={notification.id}>
                    <NotificationItem
                      notification={notification}
                      onMarkAsRead={markAsRead}
                      onRemove={removeNotification}
                    />
                    {index < notifications.length - 1 && <Divider />}
                  </Box>
                ))}
              </Box>
            )}
          </Box>
        </Paper>
      )}
    </Box>
  )
}
