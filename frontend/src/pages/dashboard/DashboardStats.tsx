/**
 * Dashboard Stats Component
 *
 * Displays server and application statistics in card format.
 */

import { Server, Package, CheckCircle, XCircle, AlertTriangle } from 'lucide-react'
import { DashboardSummary } from '@/types/mcp'

interface DashboardStatsProps {
  data: DashboardSummary | null
}

interface StatCardProps {
  title: string
  value: number
  icon: React.ReactNode
  iconBg: string
  subtitle?: string
  badge?: {
    label: string
    variant: 'success' | 'warning' | 'danger' | 'neutral'
  }
}

const badgeStyles = {
  success: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
  warning: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
  danger: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
  neutral: 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400'
}

function StatCard({ title, value, icon, iconBg, subtitle, badge }: StatCardProps) {
  return (
    <div className="bg-card border border-border rounded-lg p-4 h-full">
      <div className="flex items-start justify-between mb-3">
        <div className={`p-2 rounded-lg ${iconBg}`}>
          {icon}
        </div>
        {badge && (
          <span className={`px-2 py-1 text-xs font-medium rounded-full ${badgeStyles[badge.variant]}`}>
            {badge.label}
          </span>
        )}
      </div>
      <div className="space-y-1">
        <p className="text-3xl font-bold">{value}</p>
        <p className="text-sm font-medium text-foreground">{title}</p>
        {subtitle && (
          <p className="text-xs text-muted-foreground">{subtitle}</p>
        )}
      </div>
    </div>
  )
}

export function DashboardStats({ data }: DashboardStatsProps) {
  const stats: StatCardProps[] = [
    {
      title: 'Total Servers',
      value: data?.total_servers ?? 0,
      icon: <Server className="w-5 h-5 text-blue-600" />,
      iconBg: 'bg-blue-100 dark:bg-blue-900/30',
      subtitle: data ? `${data.online_servers} online, ${data.offline_servers} offline` : undefined,
      badge: data && data.online_servers > 0 ? {
        label: `${data.online_servers} Online`,
        variant: 'success'
      } : data && data.offline_servers > 0 ? {
        label: `${data.offline_servers} Offline`,
        variant: 'warning'
      } : undefined
    },
    {
      title: 'Total Applications',
      value: data?.total_apps ?? 0,
      icon: <Package className="w-5 h-5 text-purple-600" />,
      iconBg: 'bg-purple-100 dark:bg-purple-900/30',
      subtitle: data ? `${data.running_apps} running, ${data.stopped_apps} stopped` : undefined
    },
    {
      title: 'Running Apps',
      value: data?.running_apps ?? 0,
      icon: <CheckCircle className="w-5 h-5 text-green-600" />,
      iconBg: 'bg-green-100 dark:bg-green-900/30',
      badge: data && data.running_apps > 0 ? {
        label: 'Healthy',
        variant: 'success'
      } : undefined
    },
    {
      title: 'Issues',
      value: (data?.stopped_apps ?? 0) + (data?.error_apps ?? 0),
      icon: data?.error_apps ? <XCircle className="w-5 h-5 text-red-600" /> : <AlertTriangle className="w-5 h-5 text-yellow-600" />,
      iconBg: data?.error_apps ? 'bg-red-100 dark:bg-red-900/30' : 'bg-yellow-100 dark:bg-yellow-900/30',
      subtitle: data?.error_apps ? `${data.error_apps} errors, ${data.stopped_apps} stopped` : `${data?.stopped_apps ?? 0} stopped`,
      badge: data?.error_apps ? {
        label: 'Errors',
        variant: 'danger'
      } : data?.stopped_apps ? {
        label: 'Stopped',
        variant: 'warning'
      } : {
        label: 'All Clear',
        variant: 'success'
      }
    }
  ]

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {stats.map((stat) => (
        <StatCard key={stat.title} {...stat} />
      ))}
    </div>
  )
}
