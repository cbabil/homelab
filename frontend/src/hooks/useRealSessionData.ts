/**
 * Real Session Data Hook
 * 
 * Custom hook for managing real session data with the sessionManager,
 * providing real-time updates and session management capabilities.
 */

import { useState, useEffect, useCallback, useRef } from 'react'
import { sessionManager, SessionListEntry } from '@/services/sessionManager'
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
  refreshInterval: 300000 // 5 minutes
}

/**
 * Hook for managing real session data from sessionManager
 */
export function useRealSessionData(
  options: UseRealSessionDataOptions = {}
): UseRealSessionDataReturn {
  const config = { ...DEFAULT_OPTIONS, ...options }
  const [sessions, setSessions] = useState<SessionListEntry[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isInitialized, setIsInitialized] = useState(false)
  const unsubscribeRef = useRef<(() => void) | null>(null)
  const isPageVisible = usePageVisibility()

  // Initialize session manager
  useEffect(() => {
    let mounted = true

    const initialize = async () => {
      try {
        setIsLoading(true)
        setError(null)

        // Initialize session manager if not already done
        if (!isInitialized) {
          await sessionManager.initialize()
          setIsInitialized(true)
        }

        // Load initial sessions
        const initialSessions = sessionManager.getUserSessions()
        
        if (mounted) {
          setSessions(initialSessions)
          setIsLoading(false)
        }

        // Subscribe to session updates
        unsubscribeRef.current = sessionManager.addListener((updatedSessions) => {
          if (mounted) {
            setSessions(updatedSessions)
            setError(null)
          }
        })
      } catch (err) {
        if (mounted) {
          setError(err instanceof Error ? err.message : 'Failed to initialize session manager')
          setIsLoading(false)
        }
        console.error('[useRealSessionData] Initialization error:', err)
      }
    }

    initialize()

    return () => {
      mounted = false
      if (unsubscribeRef.current) {
        unsubscribeRef.current()
        unsubscribeRef.current = null
      }
    }
  }, [isInitialized])

  // Auto-refresh sessions (only when page is visible)
  useEffect(() => {
    if (!config.autoRefresh || !isInitialized || !isPageVisible) return

    const refreshInterval = setInterval(() => {
      sessionManager.refreshSessions().catch(err => {
        console.error('[useRealSessionData] Auto-refresh error:', err)
        setError(err instanceof Error ? err.message : 'Failed to refresh sessions')
      })
    }, config.refreshInterval)

    return () => clearInterval(refreshInterval)
  }, [config.autoRefresh, config.refreshInterval, isInitialized, isPageVisible])

  // Convert SessionListEntry to Session for compatibility
  const convertedSessions = sessions.map((session): Session => ({
    id: session.id,
    status: session.status,
    started: session.started,
    lastActivity: session.lastActivity,
    location: session.location,
    ip: session.ip
  }))

  const refreshSessions = useCallback(async () => {
    try {
      setError(null)
      await sessionManager.refreshSessions()
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to refresh sessions'
      setError(errorMessage)
      console.error('[useRealSessionData] Refresh error:', err)
      throw new Error(errorMessage)
    }
  }, [])

  const terminateSession = useCallback(async (sessionId: string) => {
    try {
      setError(null)
      
      // Find the full session ID from display ID
      const session = sessions.find(s => s.id === sessionId)
      if (!session) {
        throw new Error('Session not found')
      }

      await sessionManager.terminateSession(session.sessionId)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to terminate session'
      setError(errorMessage)
      console.error('[useRealSessionData] Terminate error:', err)
      throw new Error(errorMessage)
    }
  }, [sessions])

  const restoreSession = useCallback(async (sessionId: string) => {
    try {
      setError(null)
      
      // Find the session
      const sessionIndex = sessions.findIndex(s => s.id === sessionId)
      if (sessionIndex === -1) {
        throw new Error('Session not found')
      }

      // For now, just update the session status locally
      // In production, this would make an API call to restore the session
      const updatedSessions = [...sessions]
      updatedSessions[sessionIndex] = {
        ...updatedSessions[sessionIndex],
        status: 'active',
        lastActivity: new Date()
      }
      
      setSessions(updatedSessions)
      
      console.log('[useRealSessionData] Restored session:', sessionId)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to restore session'
      setError(errorMessage)
      console.error('[useRealSessionData] Restore error:', err)
      throw new Error(errorMessage)
    }
  }, [sessions])

  const getCurrentSession = useCallback((): Session | null => {
    const currentSession = sessions.find(s => s.isCurrentSession)
    
    if (!currentSession) return null

    return {
      id: currentSession.id,
      status: currentSession.status,
      started: currentSession.started,
      lastActivity: currentSession.lastActivity,
      location: currentSession.location,
      ip: currentSession.ip
    }
  }, [sessions])

  return {
    sessions: convertedSessions,
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
      let aValue: any
      let bValue: any

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