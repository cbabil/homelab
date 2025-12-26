/**
 * Security Settings Hook
 * 
 * Manages security settings state including session management
 * and timeout configuration integrated with real session service.
 */

import { useState, useEffect, useCallback } from 'react'
import type { SortKey } from '@/pages/settings/types'
import { sessionService } from '@/services/auth/sessionService'
import { settingsService } from '@/services/settingsService'
import { useRealSessionDataWithSort } from './useRealSessionData'

export function useSecuritySettings() {
  // Use real session data with sorting
  const {
    sortBy,
    sortOrder,
    onSort,
    sortedSessions,
    isLoading: sessionsLoading,
    error: sessionsError,
    refreshSessions,
    terminateSession: realTerminateSession,
    restoreSession: realRestoreSession
  } = useRealSessionDataWithSort({ autoRefresh: true })
  
  const [hoveredStatus, setHoveredStatus] = useState<string | null>(null)
  const [sessionTimeout, setSessionTimeout] = useState('1h')
  const [isLoading, setIsLoading] = useState(true)

  // Load initial settings
  useEffect(() => {
    loadSessionTimeout()
  }, [])

  // Update loading state based on session loading
  useEffect(() => {
    setIsLoading(sessionsLoading)
  }, [sessionsLoading])

  // Handle session loading errors
  useEffect(() => {
    if (sessionsError) {
      console.error('[useSecuritySettings] Session error:', sessionsError)
      // Could show user notification here
    }
  }, [sessionsError])

  const loadSessionTimeout = useCallback(async () => {
    try {
      await settingsService.initialize()
      const settings = settingsService.getSettings()
      setSessionTimeout(settings.security.session.timeout)
    } catch (error) {
      console.error('Failed to load session timeout:', error)
    }
  }, [])

  // Sort is handled by useRealSessionDataWithSort hook
  const handleSort = useCallback((key: SortKey) => {
    onSort(key)
  }, [onSort])

  const handleSessionTimeoutChange = useCallback(async (timeout: string) => {
    try {
      const result = await settingsService.updateSettings('security', {
        session: { 
          timeout: timeout as any,
          idleDetection: true,
          showWarningMinutes: 5,
          extendOnActivity: true
        }
      })
      
      if (result.success) {
        setSessionTimeout(timeout)
        // Optionally refresh current session with new timeout
        await sessionService.renewSession()
        // Refresh sessions to show updated data
        await refreshSessions()
        console.log('[useSecuritySettings] Session timeout updated:', timeout)
      }
    } catch (error) {
      console.error('[useSecuritySettings] Failed to update session timeout:', error)
    }
  }, [refreshSessions])

  const handleTerminateSession = useCallback(async (sessionId: string) => {
    try {
      console.log('[useSecuritySettings] Terminating session:', sessionId)
      
      // Use real session termination
      await realTerminateSession(sessionId)
      
      console.log('[useSecuritySettings] Session terminated successfully:', sessionId)
    } catch (error) {
      console.error('[useSecuritySettings] Failed to terminate session:', error)
      // Could show user notification here
      throw error
    }
  }, [realTerminateSession])

  const handleRestoreSession = useCallback(async (sessionId: string) => {
    try {
      console.log('[useSecuritySettings] Restoring session:', sessionId)
      
      // Use real session restoration
      await realRestoreSession(sessionId)
      
      console.log('[useSecuritySettings] Session restored successfully:', sessionId)
    } catch (error) {
      console.error('[useSecuritySettings] Failed to restore session:', error)
      // Could show user notification here
      throw error
    }
  }, [realRestoreSession])

  return {
    sessions: sortedSessions, // Use sorted sessions from real data
    sortBy,
    sortOrder,
    hoveredStatus,
    sessionTimeout,
    isLoading,
    error: sessionsError,
    onSort: handleSort,
    onTerminateSession: handleTerminateSession,
    onRestoreSession: handleRestoreSession,
    onHoveredStatusChange: setHoveredStatus,
    onSessionTimeoutChange: handleSessionTimeoutChange,
    refreshSessions
  }
}