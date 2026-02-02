/**
 * Session Management Hook
 * 
 * Manages session activity tracking, idle detection, and warning notifications.
 * Integrates with session manager and settings for configurable behavior.
 */

import { useState, useEffect, useCallback } from 'react'
import {
  AuthState,
  SessionActivity,
  SessionWarning
} from '@/types/auth'
import { sessionManager } from '@/services/sessionManager'
import { settingsService } from '@/services/settingsService'

export function useSessionManagement(authState: AuthState) {
  const [activity, setActivity] = useState<SessionActivity | null>(null)
  const [warning, setWarning] = useState<SessionWarning | null>(null)

  // Initialize session manager when authenticated
  useEffect(() => {
    if (authState.isAuthenticated) {
      sessionManager.initialize().catch(err => {
        console.error('Failed to initialize session manager:', err)
      })
      // Create initial activity state
      setActivity({
        lastActivity: new Date().toISOString(),
        isIdle: false,
        idleDuration: 0,
        activityCount: 0
      })
    } else {
      sessionManager.destroy()
      setActivity(null)
      setWarning(null)
    }

    return () => {
      if (!authState.isAuthenticated) {
        sessionManager.destroy()
      }
    }
  }, [authState.isAuthenticated])

  // Monitor session expiry and show warnings
  useEffect(() => {
    if (!authState.isAuthenticated || !authState.sessionExpiry) {
      setWarning(null)
      return
    }

    const checkSessionWarning = () => {
      const expiryTime = new Date(authState.sessionExpiry!).getTime()
      const now = Date.now()
      const timeRemaining = expiryTime - now
      const minutesRemaining = Math.floor(timeRemaining / 60000)

      // Get warning threshold from settings (default 5 minutes)
      const warningThreshold = settingsService.getSettings()?.security.session.showWarningMinutes || 5

      if (minutesRemaining <= 0) {
        setWarning(null) // Session expired
      } else if (minutesRemaining <= 2) {
        setWarning({
          isShowing: true,
          minutesRemaining,
          warningLevel: 'critical'
        })
      } else if (minutesRemaining <= warningThreshold) {
        setWarning({
          isShowing: true,
          minutesRemaining,
          warningLevel: minutesRemaining <= 3 ? 'warning' : 'info'
        })
      } else {
        setWarning(null)
      }
    }

    // Check immediately
    checkSessionWarning()

    // Check every 2 minutes
    const interval = setInterval(checkSessionWarning, 120000)

    return () => clearInterval(interval)
  }, [authState.isAuthenticated, authState.sessionExpiry])

  // Update activity state periodically
  useEffect(() => {
    if (!authState.isAuthenticated) {
      return
    }

    const updateActivity = () => {
      const lastActivityStr = localStorage.getItem('tomo-last-activity')
      const activityCountStr = localStorage.getItem('tomo-activity-count')

      if (lastActivityStr) {
        const lastActivityTime = new Date(lastActivityStr).getTime()
        const now = Date.now()
        const idleDuration = now - lastActivityTime
        const isIdle = idleDuration > 300000 // 5 minutes

        setActivity({
          lastActivity: lastActivityStr,
          isIdle,
          idleDuration,
          activityCount: parseInt(activityCountStr || '0', 10)
        })
      }
    }

    const interval = setInterval(updateActivity, 300000) // Update every 5 minutes

    return () => clearInterval(interval)
  }, [authState.isAuthenticated])

  // Record activity function
  const recordActivity = useCallback(() => {
    if (authState.isAuthenticated) {
      const now = new Date().toISOString()
      const currentCount = parseInt(localStorage.getItem('tomo-activity-count') || '0', 10)
      const newCount = currentCount + 1

      localStorage.setItem('tomo-last-activity', now)
      localStorage.setItem('tomo-activity-count', newCount.toString())

      setActivity({
        lastActivity: now,
        isIdle: false,
        idleDuration: 0,
        activityCount: newCount
      })
    }
  }, [authState.isAuthenticated])

  // Dismiss warning function
  const dismissWarning = useCallback(() => {
    setWarning(null)
  }, [])

  // Extend session function
  const extendSession = useCallback(async () => {
    if (!authState.isAuthenticated || !settingsService.getSettings()?.security.session.extendOnActivity) {
      return
    }

    try {
      // Record activity to extend session
      recordActivity()
      
      // Create new expiry time based on current settings
      const timeoutMs = settingsService.getSessionTimeoutMs()
      const newExpiry = new Date(Date.now() + timeoutMs)
      
      // Update session expiry in storage
      localStorage.setItem('tomo-session-expiry', newExpiry.toISOString())
      
      // Dismiss any current warning
      setWarning(null)
      
    } catch (error) {
      console.error('Failed to extend session:', error)
    }
  }, [authState.isAuthenticated, recordActivity])

  return {
    activity,
    warning,
    recordActivity,
    dismissWarning,
    extendSession
  }
}