/**
 * Quick Stats Component
 * 
 * Compact stats display for the sidebar showing key metrics.
 * Features animated counters, status indicators, and hover effects.
 */

import { memo } from 'react'
import { Link } from 'react-router-dom'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { cn } from '@/utils/cn'
import { NavigationStats } from '@/hooks/useNavigation'

interface QuickStatsProps {
  stats: NavigationStats
  className?: string
}

interface StatItemProps {
  label: string
  value: number | string
  total?: number
  href?: string
  trend?: 'up' | 'down' | 'neutral'
  trendValue?: string
  color?: 'default' | 'success' | 'warning' | 'danger'
}

const StatItem = memo(({ 
  label, 
  value, 
  total, 
  href, 
  trend, 
  trendValue, 
  color = 'default' 
}: StatItemProps) => {
  const percentage = total ? Math.round((Number(value) / total) * 100) : 0
  
  const colorClasses = {
    default: 'text-foreground',
    success: 'text-green-600 dark:text-green-400',
    warning: 'text-yellow-600 dark:text-yellow-400',
    danger: 'text-red-600 dark:text-red-400'
  }

  const content = (
    <div className={cn(
      'flex flex-col space-y-1 p-2 rounded-md transition-all duration-200',
      'border border-border/30 bg-muted/20',
      href && 'hover:bg-muted/40 hover:border-border/50 cursor-pointer'
    )}>
      <div className="flex items-center justify-between">
        <span className="text-xs text-muted-foreground font-medium">{label}</span>
      </div>
      
      <div className="flex items-baseline space-x-1">
        <span className={cn('text-base font-semibold', colorClasses[color])}>
          {value}
        </span>
        {total && (
          <span className="text-xs text-muted-foreground">
            / {total}
          </span>
        )}
      </div>
      
      {total && percentage > 0 && (
        <div className="mt-0.5">
          <div className="h-1 bg-muted rounded-full overflow-hidden">
            <div 
              className={cn(
                'h-full transition-all duration-500 rounded-full',
                color === 'success' && 'bg-green-500/80',
                color === 'warning' && 'bg-yellow-500/80',
                color === 'danger' && 'bg-red-500/80',
                color === 'default' && 'bg-primary/80'
              )}
              style={{ width: `${percentage}%` }}
            />
          </div>
        </div>
      )}
    </div>
  )

  return href ? (
    <Link to={href} className="block">
      {content}
    </Link>
  ) : content
})

StatItem.displayName = 'StatItem'

export const QuickStats = memo(({ stats, className }: QuickStatsProps) => {
  const serverConnectionRate = stats.totalServers > 0 
    ? (stats.connectedServers / stats.totalServers) * 100 
    : 0

  const appInstallRate = stats.totalApps > 0 
    ? (stats.installedApps / stats.totalApps) * 100 
    : 0

  return (
    <div className={cn('quick-stats space-y-2', className)}>
      <div className="px-3">
        <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
          Quick Overview
        </h4>
      </div>

      <div className="px-3 space-y-2">
        {/* Server Status */}
        <StatItem
          label="Servers Online"
          value={stats.connectedServers}
          total={stats.totalServers}
          href="/servers"
          color={serverConnectionRate >= 80 ? 'success' : serverConnectionRate >= 60 ? 'warning' : 'danger'}
        />

        {/* Applications */}
        <StatItem
          label="Apps Installed"
          value={stats.installedApps}
          total={stats.totalApps}
          href="/applications?status=installed"
          color={appInstallRate >= 50 ? 'success' : appInstallRate >= 25 ? 'warning' : 'default'}
        />

        {/* Critical Alerts */}
        {stats.criticalAlerts > 0 && (
          <StatItem
            label="Critical Alerts"
            value={stats.criticalAlerts}
            href="/logs"
            color="danger"
          />
        )}
      </div>
    </div>
  )
})

QuickStats.displayName = 'QuickStats'
