/**
 * Dashboard Resource Usage Component
 *
 * Displays CPU, memory, and disk usage with progress bars.
 */

import { Cpu, MemoryStick, HardDrive, Activity } from 'lucide-react'
import { DashboardSummary } from '@/types/mcp'

interface DashboardResourceUsageProps {
  data: DashboardSummary | null
}

interface ResourceBarProps {
  label: string
  value: number
  icon: React.ReactNode
  color: string
  bgColor: string
}

const badgeStyles = {
  success: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
  warning: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
  danger: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
}

function ResourceBar({ label, value, icon, color, bgColor }: ResourceBarProps) {
  const percentage = Math.min(Math.max(value, 0), 100)
  const variant = percentage >= 90 ? 'danger' : percentage >= 70 ? 'warning' : 'success'

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className={`p-1.5 rounded ${bgColor}`}>
            {icon}
          </div>
          <span className="text-sm font-medium">{label}</span>
        </div>
        <span className={`px-2 py-1 text-xs font-medium rounded-full ${badgeStyles[variant]}`}>
          {percentage.toFixed(1)}%
        </span>
      </div>
      <div className="h-2 bg-muted rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${color}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  )
}

export function DashboardResourceUsage({ data }: DashboardResourceUsageProps) {
  const resources: ResourceBarProps[] = [
    {
      label: 'CPU Usage',
      value: data?.avg_cpu_percent ?? 0,
      icon: <Cpu className="w-4 h-4 text-blue-600" />,
      color: 'bg-blue-500',
      bgColor: 'bg-blue-100 dark:bg-blue-900/30'
    },
    {
      label: 'Memory Usage',
      value: data?.avg_memory_percent ?? 0,
      icon: <MemoryStick className="w-4 h-4 text-purple-600" />,
      color: 'bg-purple-500',
      bgColor: 'bg-purple-100 dark:bg-purple-900/30'
    },
    {
      label: 'Disk Usage',
      value: data?.avg_disk_percent ?? 0,
      icon: <HardDrive className="w-4 h-4 text-orange-600" />,
      color: 'bg-orange-500',
      bgColor: 'bg-orange-100 dark:bg-orange-900/30'
    }
  ]

  const hasData = data && (data.avg_cpu_percent > 0 || data.avg_memory_percent > 0 || data.avg_disk_percent > 0)

  return (
    <div className="bg-card border border-border rounded-lg p-4 h-full">
      <div className="flex items-center gap-2 mb-6">
        <div className="p-2 rounded-lg bg-green-100 dark:bg-green-900/30">
          <Activity className="w-5 h-5 text-green-600" />
        </div>
        <h2 className="text-lg font-semibold">Resource Usage</h2>
      </div>

      {hasData ? (
        <div className="space-y-5">
          {resources.map((resource) => (
            <ResourceBar key={resource.label} {...resource} />
          ))}
        </div>
      ) : (
        <div className="text-center py-8">
          <Activity className="w-12 h-12 text-muted-foreground mx-auto mb-3" />
          <p className="text-sm text-muted-foreground">
            No resource data available.
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            Connect a server to see resource metrics.
          </p>
        </div>
      )}
    </div>
  )
}
