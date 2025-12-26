/**
 * Dashboard Page Component
 * 
 * Modern dashboard with animated cards, status indicators, and quick actions.
 * Features responsive grid layout and smooth loading states.
 */

import { useEffect, useState } from 'react'
import { Activity } from 'lucide-react'
import { useMCP } from '@/providers/MCPProvider'
import { HealthStatus } from '@/types/mcp'
import { DashboardStatusCards } from './DashboardStatusCards'
import { DashboardLoadingState } from './DashboardLoadingState'
import { DashboardQuickActions } from './DashboardQuickActions'
import { DashboardSystemHealth } from './DashboardSystemHealth'

export function Dashboard() {
  const { client, isConnected } = useMCP()
  const [healthStatus, setHealthStatus] = useState<HealthStatus | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchHealthStatus = async () => {
      if (!isConnected) return

      try {
        setLoading(true)
        const result = await client.callTool<HealthStatus>('get_health_status', {})
        
        if (result.success && result.data) {
          setHealthStatus(result.data)
        }
      } catch (error) {
        console.error('Failed to fetch health status:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchHealthStatus()
  }, [client, isConnected])

  if (!isConnected) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center space-y-4">
          <div className="w-16 h-16 mx-auto rounded-full bg-muted flex items-center justify-center">
            <Activity className="w-8 h-8 text-muted-foreground" />
          </div>
          <h2 className="text-2xl font-semibold">Connecting to Server...</h2>
          <p className="text-muted-foreground max-w-md">
            Check notifications for connection status updates.
          </p>
        </div>
      </div>
    )
  }

  if (loading) {
    return <DashboardLoadingState />
  }

  return (
    <div className="space-y-8">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          Monitor your homelab infrastructure and manage applications.
        </p>
      </div>

      <DashboardStatusCards healthStatus={healthStatus} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <DashboardQuickActions />
        <DashboardSystemHealth healthStatus={healthStatus} />
      </div>
    </div>
  )
}