/**
 * Real Session Data Hook
 *
 * Custom hook for managing real session data from the backend MCP server,
 * providing real-time updates and session management capabilities.
 */

import { useState, useEffect, useCallback, useRef } from 'react'
import { useSessionMcpClient, BackendSession } from '@/services/sessionMcpClient'
import type { Session, SortKey } from '@/pages/settings/types'
import { usePageVisibility } from './usePageVisibility'

export interface UseRealSessionDataOptions {
  autoRefresh?: boolean
  refreshInterval?: number
}

export interface UseRealSessionDataReturn {
  sessions: Session[]
  isLoading: boolean
  error: string | null
  refreshSessions: () => Promise<void>
  terminateSession: (sessionId: string) => Promise<void>
  restoreSession: (sessionId: string) => Promise<void>
  getCurrentSession: () => Session | null
}

const DEFAULT_OPTIONS: Required<UseRealSessionDataOptions> = {
  autoRefresh: true,
  refreshInterval: 30000 // 30 seconds
}

/**
 * Parse user agent string to get a readable location/device description
 */
function parseUserAgent(userAgent: string | null): string {
  if (!userAgent) return 'Unknown Device'

  // Try to extract browser and OS info
  const browserMatch = userAgent.match(/(Chrome|Firefox|Safari|Edge|Opera)\/[\d.]+/)
  const osMatch = userAgent.match(/(Windows|Mac OS X|Linux|Android|iOS)[\s\d._]*/)

  const browser = browserMatch ? browserMatch[1] : 'Unknown Browser'
  const os = osMatch ? osMatch[1].replace('Mac OS X', 'macOS') : 'Unknown OS'

  return `${browser} on ${os}`
}

/**
 * Convert backend session to frontend Session type
 */
function convertToFrontendSession(backendSession: BackendSession): Session {
  return {
    id: backendSession.id,
    userId: backendSession.user_id,
    username: backendSession.username || 'Unknown',
    status: backendSession.status,
    started: new Date(backendSession.created_at),
    lastActivity: new Date(backendSession.last_activity),
    expiresAt: new Date(backendSession.expires_at),
    location: parseUserAgent(backendSession.user_agent),
    ip: backendSession.ip_address || 'Unknown',
    isCurrent: backendSession.is_current ?? false
  }
}

/**
 * Hook for managing real session data from backend MCP server
 */
export function useRealSessionData(
  options: UseRealSessionDataOptions = {}
): UseRealSessionDataReturn {
  const config = { ...DEFAULT_OPTIONS, ...options }
  const [sessions, setSessions] = useState<Session[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const sessionMcpClient = useSessionMcpClient()
  const isPageVisible = usePageVisibility()
  const isMounted = useRef(true)

  // Load sessions from backend
  const loadSessions = useCallback(async () => {
    if (!sessionMcpClient) {
      setError('MCP client not available')
      setIsLoading(false)
      return
    }

    try {
      setError(null)
      const backendSessions = await sessionMcpClient.getSessions()

      if (isMounted.current) {
        const frontendSessions = backendSessions.map(convertToFrontendSession)
        setSessions(frontendSessions)
        setIsLoading(false)
      }
    } catch (err) {
      if (isMounted.current) {
        setError(err instanceof Error ? err.message : 'Failed to load sessions')
        setIsLoading(false)
      }
      console.error('[useRealSessionData] Load error:', err)
    }
  }, [sessionMcpClient])

  // Initialize and load sessions
  useEffect(() => {
    isMounted.current = true
    loadSessions()

    return () => {
      isMounted.current = false
    }
  }, [loadSessions])

  // Auto-refresh sessions (only when page is visible)
  useEffect(() => {
    if (!config.autoRefresh || !isPageVisible || !sessionMcpClient) return

    const refreshInterval = setInterval(() => {
      loadSessions().catch(err => {
        console.error('[useRealSessionData] Auto-refresh error:', err)
      })
    }, config.refreshInterval)

    return () => clearInterval(refreshInterval)
  }, [config.autoRefresh, config.refreshInterval, isPageVisible, sessionMcpClient, loadSessions])

  const refreshSessions = useCallback(async () => {
    await loadSessions()
  }, [loadSessions])

  const terminateSession = useCallback(async (sessionId: string) => {
    if (!sessionMcpClient) {
      throw new Error('MCP client not available')
    }

    try {
      setError(null)
      const result = await sessionMcpClient.deleteSession(sessionId)

      if (!result.success) {
        throw new Error('Failed to terminate session')
      }

      // Refresh sessions after termination
      await loadSessions()
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to terminate session'
      setError(errorMessage)
      console.error('[useRealSessionData] Terminate error:', err)
      throw new Error(errorMessage)
    }
  }, [sessionMcpClient, loadSessions])

  const restoreSession = useCallback(async (sessionId: string) => {
    // Note: Backend doesn't support restore, so we just update local state
    // In the future, this could call a backend endpoint
    try {
      setError(null)

      const sessionIndex = sessions.findIndex(s => s.id === sessionId)
      if (sessionIndex === -1) {
        throw new Error('Session not found')
      }

      // Update local state - the backend would need a restore endpoint to actually restore
      const updatedSessions = [...sessions]
      updatedSessions[sessionIndex] = {
        ...updatedSessions[sessionIndex],
        status: 'active',
        lastActivity: new Date()
      }

      setSessions(updatedSessions)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to restore session'
      setError(errorMessage)
      console.error('[useRealSessionData] Restore error:', err)
      throw new Error(errorMessage)
    }
  }, [sessions])

  const getCurrentSession = useCallback((): Session | null => {
    // We don't have a way to identify the current session from backend yet
    // This would require the backend to return is_current flag
    return sessions.find(s => s.status === 'active') || null
  }, [sessions])

  return {
    sessions,
    isLoading,
    error,
    refreshSessions,
    terminateSession,
    restoreSession,
    getCurrentSession
  }
}

/**
 * Hook for real session data with sorting capabilities
 */
export function useRealSessionDataWithSort(
  options: UseRealSessionDataOptions = {}
): UseRealSessionDataReturn & {
  sortBy: SortKey
  sortOrder: 'asc' | 'desc'
  onSort: (key: SortKey) => void
  sortedSessions: Session[]
} {
  const sessionData = useRealSessionData(options)
  const [sortBy, setSortBy] = useState<SortKey>('status')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc')

  const onSort = useCallback((key: SortKey) => {
    if (sortBy === key) {
      setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc')
    } else {
      setSortBy(key)
      setSortOrder('asc')
    }
  }, [sortBy])

  const sortedSessions = useCallback(() => {
    const sorted = [...sessionData.sessions].sort((a, b) => {
      let aValue: string | number
      let bValue: string | number

      switch (sortBy) {
        case 'status':
          aValue = a.status
          bValue = b.status
          break
        case 'sessionId':
          aValue = a.id
          bValue = b.id
          break
        case 'started':
          aValue = a.started.getTime()
          bValue = b.started.getTime()
          break
        case 'lastActivity':
          aValue = a.lastActivity.getTime()
          bValue = b.lastActivity.getTime()
          break
        case 'location':
          aValue = a.location
          bValue = b.location
          break
        default:
          return 0
      }

      if (aValue < bValue) {
        return sortOrder === 'asc' ? -1 : 1
      }
      if (aValue > bValue) {
        return sortOrder === 'asc' ? 1 : -1
      }
      return 0
    })

    return sorted
  }, [sessionData.sessions, sortBy, sortOrder])

  return {
    ...sessionData,
    sortBy,
    sortOrder,
    onSort,
    sortedSessions: sortedSessions()
  }
}
