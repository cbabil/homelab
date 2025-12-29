/**
 * Quick Stats Component
 *
 * Compact stats display for the sidebar showing key metrics.
 */

import { memo } from 'react'
import { Link } from 'react-router-dom'
import { Server, Package, AlertTriangle } from 'lucide-react'
import { cn } from '@/utils/cn'
import { NavigationStats } from '@/hooks/useNavigation'

interface QuickStatsProps {
  stats: NavigationStats
  className?: string
}

export const QuickStats = memo(({ stats, className }: QuickStatsProps) => {
  const serverStatus = stats.totalServers > 0
    ? stats.connectedServers === stats.totalServers ? 'success' : 'warning'
    : 'default'

  return (
    <div className={cn('py-2 px-4 mb-4', className)}>
      <h4 className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-2">
        Overview
      </h4>

      <div className="grid grid-cols-2 gap-2">
        {/* Servers */}
        <Link
          to="/servers"
          className="flex items-center gap-2 p-2 rounded-md hover:bg-accent/50 transition-colors"
        >
          <div className={cn(
            'w-8 h-8 rounded-md flex items-center justify-center',
            serverStatus === 'success' && 'bg-green-500/10 text-green-500',
            serverStatus === 'warning' && 'bg-yellow-500/10 text-yellow-500',
            serverStatus === 'default' && 'bg-muted text-muted-foreground'
          )}>
            <Server className="w-4 h-4" />
          </div>
          <div className="min-w-0">
            <div className="text-sm font-medium leading-none">
              {stats.connectedServers}/{stats.totalServers}
            </div>
            <div className="text-[10px] text-muted-foreground mt-0.5">Servers</div>
          </div>
        </Link>

        {/* Apps */}
        <Link
          to="/applications"
          className="flex items-center gap-2 p-2 rounded-md hover:bg-accent/50 transition-colors"
        >
          <div className="w-8 h-8 rounded-md flex items-center justify-center bg-primary/10 text-primary">
            <Package className="w-4 h-4" />
          </div>
          <div className="min-w-0">
            <div className="text-sm font-medium leading-none">
              {stats.installedApps}/{stats.totalApps}
            </div>
            <div className="text-[10px] text-muted-foreground mt-0.5">Apps</div>
          </div>
        </Link>

        {/* Alerts - only show if there are any */}
        {stats.criticalAlerts > 0 && (
          <Link
            to="/logs"
            className="col-span-2 flex items-center gap-2 p-2 rounded-md bg-red-500/10 hover:bg-red-500/20 transition-colors"
          >
            <div className="w-8 h-8 rounded-md flex items-center justify-center bg-red-500/20 text-red-500">
              <AlertTriangle className="w-4 h-4" />
            </div>
            <div className="min-w-0">
              <div className="text-sm font-medium leading-none text-red-500">
                {stats.criticalAlerts} Alert{stats.criticalAlerts !== 1 ? 's' : ''}
              </div>
              <div className="text-[10px] text-red-400 mt-0.5">Needs attention</div>
            </div>
          </Link>
        )}
      </div>
    </div>
  )
})

QuickStats.displayName = 'QuickStats'
