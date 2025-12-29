/**
 * Dashboard Data Hook
 *
 * Fetches and manages dashboard data from the backend.
 * Server counts use frontend storage for consistency with Servers page.
 */

import { useEffect, useState, useCallback } from 'react'
import { useMCP } from '@/providers/MCPProvider'
import { DashboardSummary, HealthStatus } from '@/types/mcp'
import { serverStorageService } from '@/services/serverStorageService'

export function useDashboardData() {
  const { client, isConnected } = useMCP()
  const [dashboardData, setDashboardData] = useState<DashboardSummary | null>(null)
  const [healthStatus, setHealthStatus] = useState<HealthStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)

  const fetchData = useCallback(async (showRefreshing = false) => {
    if (!isConnected) return

    try {
      if (showRefreshing) {
        setRefreshing(true)
      } else {
        setLoading(true)
      }

      // Get server counts from frontend storage (same source as Servers page)
      const servers = serverStorageService.getAllServers()
      const totalServers = servers.length
      const onlineServers = servers.filter(s => s.status === 'connected').length
      const offlineServers = totalServers - onlineServers

      const [summaryResult, healthResult] = await Promise.all([
        client.callTool<DashboardSummary>('get_dashboard_summary', {}),
        client.callTool<HealthStatus>('get_health_status', {})
      ])

      if (summaryResult.success && summaryResult.data) {
        // Override server counts with frontend storage data
        setDashboardData({
          ...summaryResult.data,
          total_servers: totalServers,
          online_servers: onlineServers,
          offline_servers: offlineServers
        })
      } else {
        // Even if backend fails, show server counts
        setDashboardData({
          total_servers: totalServers,
          online_servers: onlineServers,
          offline_servers: offlineServers,
          total_apps: 0,
          running_apps: 0,
          stopped_apps: 0,
          error_apps: 0,
          avg_cpu_percent: 0,
          avg_memory_percent: 0,
          avg_disk_percent: 0,
          recent_activities: []
        })
      }

      if (healthResult.success && healthResult.data) {
        setHealthStatus(healthResult.data)
      }

      setLastUpdated(new Date())
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [client, isConnected])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  // Auto-refresh every 30 seconds
  useEffect(() => {
    if (!isConnected) return

    const interval = setInterval(() => {
      fetchData(true)
    }, 30000)

    return () => clearInterval(interval)
  }, [isConnected, fetchData])

  const refresh = useCallback(() => {
    fetchData(true)
  }, [fetchData])

  return {
    dashboardData,
    healthStatus,
    loading,
    refreshing,
    lastUpdated,
    isConnected,
    refresh
  }
}
