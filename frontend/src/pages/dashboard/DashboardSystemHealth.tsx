/**
 * Dashboard System Health Component
 * 
 * System health status panel showing overall health information.
 */

import { Activity } from 'lucide-react'
import { HealthStatus } from '@/types/mcp'
import { cn } from '@/utils/cn'

interface DashboardSystemHealthProps {
  healthStatus: HealthStatus | null
}

export function DashboardSystemHealth({ healthStatus }: DashboardSystemHealthProps) {
  return (
    <div className="card-feature">
      <div className="flex items-center space-x-3 mb-6">
        <div className="p-2 rounded-lg bg-green-100 dark:bg-green-900/50">
          <Activity className="w-5 h-5 text-green-600 dark:text-green-400" />
        </div>
        <h2 className="text-xl font-semibold">System Health</h2>
      </div>
      
      <div className="space-y-4">
        <div className="flex items-center justify-between p-3 rounded-lg bg-accent/50">
          <span className="text-sm font-medium">Overall Status</span>
          <div className="flex items-center space-x-2">
            <div className={cn(
              "w-2 h-2 rounded-full",
              healthStatus?.status === 'healthy' ? 'bg-green-500' : 'bg-red-500'
            )} />
            <span className="text-sm capitalize">{healthStatus?.status || 'Unknown'}</span>
          </div>
        </div>
        
        <p className="text-sm text-muted-foreground">
          All systems are running normally. Last health check completed successfully.
        </p>
      </div>
    </div>
  )
}