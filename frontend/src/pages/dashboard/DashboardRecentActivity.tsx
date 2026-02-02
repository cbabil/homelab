/**
 * Dashboard Recent Activity Component
 *
 * Displays a clean timeline of recent system activities.
 */

import React from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import {
  Clock,
  Server,
  Settings,
  AlertCircle,
  CheckCircle,
  RefreshCw,
  Power,
  Download,
  Trash2,
  UserCheck,
  Activity
} from 'lucide-react'
import { Box, Card, Typography, Stack, Chip } from '@mui/material'
import { ActivityLog } from '@/types/mcp'

interface ServerInfo {
  id: string
  name: string
}

interface DashboardRecentActivityProps {
  activities: ActivityLog[]
  servers?: ServerInfo[]
}

const activityTypeConfig: Record<string, { icon: React.ComponentType<{ className?: string }>, color: string }> = {
  server_connect: { icon: Server, color: '#10b981' },
  server_disconnect: { icon: Power, color: '#ef4444' },
  app_start: { icon: CheckCircle, color: '#10b981' },
  app_stop: { icon: Power, color: '#f59e0b' },
  app_install: { icon: Download, color: '#3b82f6' },
  app_uninstall: { icon: Trash2, color: '#ef4444' },
  app_update: { icon: RefreshCw, color: '#8b5cf6' },
  settings_change: { icon: Settings, color: '#6b7280' },
  login: { icon: UserCheck, color: '#3b82f6' },
  error: { icon: AlertCircle, color: '#ef4444' },
  default: { icon: Activity, color: '#6b7280' }
}

function getActivityConfig(type: string) {
  return activityTypeConfig[type] || activityTypeConfig.default
}

function useTimeAgo() {
  const { t } = useTranslation()

  return (dateString: string): string => {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / (1000 * 60))
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

    if (diffMins < 1) return t('logs.timeAgo.justNow')
    if (diffMins < 60) return t('logs.timeAgo.minutesAgo', { count: diffMins })
    if (diffHours < 24) return t('logs.timeAgo.hoursAgo', { count: diffHours })
    if (diffDays < 7) return t('logs.timeAgo.daysAgo', { count: diffDays })
    return date.toLocaleDateString()
  }
}

function formatActivityType(type: string): string {
  return type.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')
}

export function DashboardRecentActivity({ activities, servers = [] }: DashboardRecentActivityProps) {
  const { t } = useTranslation()
  const formatTimeAgo = useTimeAgo()

  const serverMap = React.useMemo(() => {
    const map = new Map<string, string>()
    servers.forEach(s => map.set(s.id, s.name))
    return map
  }, [servers])

  const getServerName = (serverId: string): string => {
    return serverMap.get(serverId) || serverId
  }

  return (
    <Card sx={{ p: 2.5, flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 2.5 }}>
        <Stack direction="row" spacing={1} alignItems="center">
          <Clock className="w-4 h-4" style={{ color: '#3b82f6' }} />
          <Typography variant="body2" fontWeight={600}>
            {t('dashboard.recentActivity')}
          </Typography>
        </Stack>
        <Link
          to="/logs"
          style={{
            fontSize: 12,
            color: 'var(--mui-palette-text-secondary)',
            textDecoration: 'none',
            transition: 'color 0.2s'
          }}
        >
          {t('common.viewAll')}
        </Link>
      </Stack>

      {activities.length === 0 ? (
        <Stack alignItems="center" justifyContent="center" sx={{ flex: 1, textAlign: 'center' }}>
          <Activity className="w-8 h-8" style={{ color: 'var(--mui-palette-text-secondary)', marginBottom: 12 }} />
          <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
            {t('dashboard.noRecentActivity')}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {t('dashboard.eventsWillAppear')}
          </Typography>
        </Stack>
      ) : (
        <Stack spacing={0.5} sx={{ flex: 1, overflow: 'auto', minHeight: 0 }}>
          {activities.map((activity, index) => {
            const config = getActivityConfig(activity.activity_type)
            const Icon = config.icon

            return (
              <Stack
                key={activity.id}
                direction="row"
                spacing={1.5}
                alignItems="center"
                sx={{
                  py: 1.25,
                  px: 1,
                  mx: -1,
                  borderRadius: 1,
                  transition: 'background-color 0.2s',
                  '&:hover': {
                    bgcolor: 'action.hover'
                  }
                }}
              >
                <Box sx={{ position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'center', width: 24, minWidth: 24 }}>
                  <Box component="span" sx={{ display: 'flex', color: config.color }}>
                    <Icon className="w-4 h-4" />
                  </Box>
                  {/* Timeline connector */}
                  {index < activities.length - 1 && (
                    <Box sx={{
                      position: 'absolute',
                      top: '100%',
                      left: '50%',
                      transform: 'translateX(-50%)',
                      width: 1,
                      height: 12,
                      bgcolor: 'divider'
                    }} />
                  )}
                </Box>

                <Box sx={{ flex: 1, minWidth: 0 }}>
                  <Typography variant="body2" noWrap>
                    {activity.description}
                  </Typography>
                  <Stack direction="row" spacing={1} alignItems="center" sx={{ mt: 0.25 }}>
                    <Typography variant="caption" color="text.secondary">
                      {formatTimeAgo(activity.created_at)}
                    </Typography>
                    {activity.server_id && (
                      <>
                        <Typography variant="caption" color="text.secondary">·</Typography>
                        <Typography variant="caption" color="text.secondary" noWrap>
                          {getServerName(activity.server_id)}
                        </Typography>
                      </>
                    )}
                  </Stack>
                </Box>

                <Chip
                  label={formatActivityType(activity.activity_type)}
                  size="small"
                  sx={{
                    fontSize: 10,
                    fontWeight: 500,
                    height: 20,
                    bgcolor: 'action.hover',
                    color: config.color
                  }}
                />
              </Stack>
            )
          })}

        </Stack>
      )}
    </Card>
  )
}
