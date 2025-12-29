/**
 * Dashboard Page Component
 *
 * Modern dashboard with real-time data from the backend.
 */

import { Activity, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { useDashboardData } from './useDashboardData'
import { DashboardStats } from './DashboardStats'
import { DashboardResourceUsage } from './DashboardResourceUsage'
import { DashboardRecentActivity } from './DashboardRecentActivity'
import { DashboardQuickActions } from './DashboardQuickActions'

export function Dashboard() {
  const {
    dashboardData,
    healthStatus,
    loading,
    refreshing,
    lastUpdated,
    isConnected,
    refresh
  } = useDashboardData()

  if (!isConnected) {
    return <DashboardConnecting />
  }

  if (loading) {
    return <DashboardLoadingSkeleton />
  }

  return (
    <div className="space-y-6">
      <DashboardHeader
        healthStatus={healthStatus}
        lastUpdated={lastUpdated}
        refreshing={refreshing}
        onRefresh={refresh}
      />

      <DashboardStats data={dashboardData} />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <DashboardResourceUsage data={dashboardData} />
        </div>
        <div>
          <DashboardQuickActions />
        </div>
      </div>

      <DashboardRecentActivity activities={dashboardData?.recent_activities || []} />
    </div>
  )
}

function DashboardConnecting() {
  return (
    <div className="flex items-center justify-center min-h-[400px]">
      <div className="bg-card border border-border rounded-lg p-8 text-center max-w-md">
        <div className="w-16 h-16 mx-auto rounded-full bg-muted flex items-center justify-center mb-4">
          <Activity className="w-8 h-8 text-muted-foreground" />
        </div>
        <h2 className="text-2xl font-semibold mb-2">Connecting to Server...</h2>
        <p className="text-muted-foreground">
          Check notifications for connection status updates.
        </p>
      </div>
    </div>
  )
}

interface DashboardHeaderProps {
  healthStatus: { status: string } | null
  lastUpdated: Date | null
  refreshing: boolean
  onRefresh: () => void
}

function DashboardHeader({ healthStatus, lastUpdated, refreshing, onRefresh }: DashboardHeaderProps) {
  return (
    <div className="flex items-center justify-between">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          Monitor your homelab infrastructure and manage applications.
        </p>
      </div>
      <div className="flex items-center gap-3">
        {lastUpdated && (
          <span className="text-sm text-muted-foreground">
            Updated {lastUpdated.toLocaleTimeString()}
          </span>
        )}
        <Button
          onClick={onRefresh}
          variant="ghost"
          size="sm"
          disabled={refreshing}
          leftIcon={<RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />}
        >
          Refresh
        </Button>
        {healthStatus && (
          <span className={`px-2 py-1 text-xs font-medium rounded-full ${
            healthStatus.status === 'healthy'
              ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
              : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
          }`}>
            {healthStatus.status}
          </span>
        )}
      </div>
    </div>
  )
}

function DashboardLoadingSkeleton() {
  return (
    <div className="space-y-6">
      <div>
        <div className="h-8 w-48 bg-muted rounded animate-pulse mb-2" />
        <div className="h-5 w-96 bg-muted rounded animate-pulse" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-card border border-border rounded-lg p-4">
            <div className="h-4 w-20 bg-muted rounded animate-pulse mb-3" />
            <div className="h-8 w-16 bg-muted rounded animate-pulse mb-2" />
            <div className="h-3 w-24 bg-muted rounded animate-pulse" />
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-card border border-border rounded-lg p-4">
          <div className="h-6 w-36 bg-muted rounded animate-pulse mb-4" />
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i}>
                <div className="h-5 w-full bg-muted rounded animate-pulse mb-2" />
                <div className="h-2 w-full bg-muted rounded animate-pulse" />
              </div>
            ))}
          </div>
        </div>
        <div className="bg-card border border-border rounded-lg p-4">
          <div className="h-6 w-28 bg-muted rounded animate-pulse mb-4" />
          <div className="space-y-3">
            {[1, 2].map((i) => (
              <div key={i} className="h-10 w-full bg-muted rounded animate-pulse" />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
