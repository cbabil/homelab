/**
 * Dashboard Recent Activity Component
 *
 * Displays a list of recent system activities.
 */

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
import { Card, Badge } from 'ui-toolkit'
import { ActivityLog } from '@/types/mcp'

interface DashboardRecentActivityProps {
  activities: ActivityLog[]
}

const activityTypeConfig: Record<string, { icon: React.ComponentType<{ className?: string }>, color: string, bgColor: string }> = {
  server_connect: { icon: Server, color: 'text-green-600', bgColor: 'bg-green-100 dark:bg-green-900/30' },
  server_disconnect: { icon: Power, color: 'text-red-600', bgColor: 'bg-red-100 dark:bg-red-900/30' },
  app_start: { icon: CheckCircle, color: 'text-green-600', bgColor: 'bg-green-100 dark:bg-green-900/30' },
  app_stop: { icon: Power, color: 'text-yellow-600', bgColor: 'bg-yellow-100 dark:bg-yellow-900/30' },
  app_install: { icon: Download, color: 'text-blue-600', bgColor: 'bg-blue-100 dark:bg-blue-900/30' },
  app_uninstall: { icon: Trash2, color: 'text-red-600', bgColor: 'bg-red-100 dark:bg-red-900/30' },
  app_update: { icon: RefreshCw, color: 'text-purple-600', bgColor: 'bg-purple-100 dark:bg-purple-900/30' },
  settings_change: { icon: Settings, color: 'text-gray-600', bgColor: 'bg-gray-100 dark:bg-gray-900/30' },
  login: { icon: UserCheck, color: 'text-blue-600', bgColor: 'bg-blue-100 dark:bg-blue-900/30' },
  error: { icon: AlertCircle, color: 'text-red-600', bgColor: 'bg-red-100 dark:bg-red-900/30' },
  default: { icon: Activity, color: 'text-gray-600', bgColor: 'bg-gray-100 dark:bg-gray-900/30' }
}

function getActivityConfig(type: string) {
  return activityTypeConfig[type] || activityTypeConfig.default
}

function formatTimeAgo(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / (1000 * 60))
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  return date.toLocaleDateString()
}

function getActivityBadgeVariant(type: string): 'success' | 'warning' | 'danger' | 'neutral' | 'accent' {
  if (type.includes('connect') || type.includes('start') || type === 'login') return 'success'
  if (type.includes('disconnect') || type.includes('stop')) return 'warning'
  if (type.includes('error') || type.includes('uninstall')) return 'danger'
  if (type.includes('update') || type.includes('install')) return 'accent'
  return 'neutral'
}

export function DashboardRecentActivity({ activities }: DashboardRecentActivityProps) {
  return (
    <Card padding="md">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900/30">
            <Clock className="w-5 h-5 text-blue-600" />
          </div>
          <h2 className="text-lg font-semibold">Recent Activity</h2>
        </div>
        {activities.length > 0 && (
          <Badge variant="neutral" size="sm">
            {activities.length} events
          </Badge>
        )}
      </div>

      {activities.length === 0 ? (
        <div className="text-center py-8">
          <div className="w-12 h-12 mx-auto rounded-full bg-muted flex items-center justify-center mb-3">
            <Activity className="w-6 h-6 text-muted-foreground" />
          </div>
          <h3 className="text-sm font-medium mb-1">No recent activity</h3>
          <p className="text-xs text-muted-foreground">
            System events will appear here as they occur.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {activities.slice(0, 10).map((activity) => {
            const config = getActivityConfig(activity.activity_type)
            const Icon = config.icon

            return (
              <div
                key={activity.id}
                className="flex items-start gap-3 p-3 rounded-lg hover:bg-muted/50 transition-colors"
              >
                <div className={`p-2 rounded-lg ${config.bgColor} flex-shrink-0`}>
                  <Icon className={`w-4 h-4 ${config.color}`} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-sm font-medium truncate">
                      {activity.description}
                    </p>
                    <Badge
                      variant={getActivityBadgeVariant(activity.activity_type)}
                      size="sm"
                    >
                      {activity.activity_type.replace(/_/g, ' ')}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-xs text-muted-foreground">
                      {formatTimeAgo(activity.created_at)}
                    </span>
                    {activity.server_id && (
                      <>
                        <span className="text-xs text-muted-foreground">•</span>
                        <span className="text-xs text-muted-foreground">
                          {activity.server_id}
                        </span>
                      </>
                    )}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </Card>
  )
}
