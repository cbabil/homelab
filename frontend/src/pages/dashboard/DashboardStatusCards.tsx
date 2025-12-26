/**
 * Dashboard Status Cards Component
 * 
 * Status cards displaying system metrics and health information.
 */

import { CheckCircle, AlertCircle, Activity, Package, Clock } from 'lucide-react'
import { HealthStatus } from '@/types/mcp'
import { cn } from '@/utils/cn'

interface DashboardStatusCardsProps {
  healthStatus: HealthStatus | null
}

export function DashboardStatusCards({ healthStatus }: DashboardStatusCardsProps) {
  const statusCards = [
    {
      title: 'System Status',
      value: healthStatus?.status || 'Unknown',
      icon: healthStatus?.status === 'healthy' ? CheckCircle : AlertCircle,
      color: healthStatus?.status === 'healthy' ? 'text-green-500' : 'text-red-500',
      bgColor: healthStatus?.status === 'healthy' ? 'bg-green-50 dark:bg-green-950/50' : 'bg-red-50 dark:bg-red-950/50'
    },
    {
      title: 'Version',
      value: healthStatus?.version || 'N/A',
      icon: Activity,
      color: 'text-blue-500',
      bgColor: 'bg-blue-50 dark:bg-blue-950/50'
    },
    {
      title: 'Components',
      value: healthStatus?.components ? Object.keys(healthStatus.components).length.toString() : '0',
      icon: Package,
      color: 'text-purple-500',
      bgColor: 'bg-purple-50 dark:bg-purple-950/50'
    },
    {
      title: 'Last Updated',
      value: healthStatus?.timestamp ? new Date(healthStatus.timestamp).toLocaleTimeString() : 'N/A',
      icon: Clock,
      color: 'text-orange-500',
      bgColor: 'bg-orange-50 dark:bg-orange-950/50'
    }
  ]

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {statusCards.map((card) => (
        <div 
          key={card.title}
          className={cn(
            "bg-card p-6 rounded-xl border card-hover",
            card.bgColor
          )}
        >
          <div className="flex items-center justify-between mb-4">
            <div className={cn("p-2 rounded-lg", card.bgColor)}>
              <card.icon className={cn("w-5 h-5", card.color)} />
            </div>
          </div>
          
          <div className="space-y-1">
            <p className="text-2xl font-bold">{card.value}</p>
            <p className="text-sm text-muted-foreground">{card.title}</p>
          </div>
        </div>
      ))}
    </div>
  )
}