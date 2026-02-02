/**
 * Dashboard Data Hook
 *
 * Fetches and manages dashboard data from the backend.
 * Backend is the single source of truth for all data.
 */

import { useEffect, useState, useCallback } from 'react'
import { useMCP } from '@/providers/MCPProvider'
import { DashboardSummary, HealthStatus } from '@/types/mcp'
import { ServerConnection } from '@/types/server'

// Refresh interval options (in seconds)
export const REFRESH_INTERVALS = [
  { value: 15, label: '15 seconds' },
  { value: 30, label: '30 seconds' },
  { value: 60, label: '1 minute' },
  { value: 120, label: '2 minutes' },
  { value: 300, label: '5 minutes' },
  { value: 0, label: 'Manual only' }
] as const

const STORAGE_KEY = 'dashboard_refresh_interval'
const DEFAULT_INTERVAL = 30

/** Backend server response */
interface BackendServer {
  id: string
  name: string
  host: string
  port: number
  username: string
  auth_type: string
  status: string
}

function getStoredRefreshInterval(): number {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      const value = parseInt(stored, 10)
      if (REFRESH_INTERVALS.some(i => i.value === value)) {
        return value
      }
    }
  } catch {
    // Ignore storage errors
  }
  return DEFAULT_INTERVAL
}

export function useDashboardData() {
  const { client, isConnected } = useMCP()
  const [dashboardData, setDashboardData] = useState<DashboardSummary | null>(null)
  const [healthStatus, setHealthStatus] = useState<HealthStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)
  const [refreshInterval, setRefreshIntervalState] = useState<number>(getStoredRefreshInterval)
  const [servers, setServers] = useState<ServerConnection[]>([])

  const fetchData = useCallback(async (showRefreshing = false) => {
    if (!isConnected) return

    try {
      if (showRefreshing) {
        setRefreshing(true)
      } else {
        setLoading(true)
      }

      // Fetch servers from backend
      const serversResult = await client.callTool<{
        success: boolean
        data?: { servers: BackendServer[] }
      }>('list_servers', {})

      let totalServers = 0
      let onlineServers = 0
      let offlineServers = 0

      if (serversResult.data?.success && serversResult.data.data?.servers) {
        const backendServers = serversResult.data.data.servers
        totalServers = backendServers.length
        onlineServers = backendServers.filter(s => s.status === 'connected').length
        offlineServers = totalServers - onlineServers
        setServers(backendServers.map(s => ({
          id: s.id,
          name: s.name,
          host: s.host,
          port: s.port,
          username: s.username,
          auth_type: s.auth_type as 'password' | 'key',
          status: s.status as ServerConnection['status'],
          created_at: new Date().toISOString(),
          docker_installed: false,
        })))
      } else {
        setServers([])
      }

      const [summaryResult, healthResult] = await Promise.all([
        client.callTool<DashboardSummary>('get_dashboard_summary', {}),
        client.callTool<HealthStatus>('get_health_status', {})
      ])

      if (summaryResult.success && summaryResult.data) {
        // Override server counts with backend data
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

  // Auto-refresh at configurable interval
  useEffect(() => {
    if (!isConnected || refreshInterval === 0) return

    const interval = setInterval(() => {
      fetchData(true)
    }, refreshInterval * 1000)

    return () => clearInterval(interval)
  }, [isConnected, fetchData, refreshInterval])

  const refresh = useCallback(() => {
    fetchData(true)
  }, [fetchData])

  const setRefreshInterval = useCallback((seconds: number) => {
    setRefreshIntervalState(seconds)
    try {
      localStorage.setItem(STORAGE_KEY, seconds.toString())
    } catch {
      // Ignore storage errors
    }
  }, [])

  return {
    dashboardData,
    healthStatus,
    loading,
    refreshing,
    lastUpdated,
    isConnected,
    refresh,
    servers,
    refreshInterval,
    setRefreshInterval
  }
}
