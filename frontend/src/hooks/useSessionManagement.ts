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
      sessionManager.initialize()
      setActivity(sessionManager.getActivityState())
    } else {
      sessionManager.cleanup()
      setActivity(null)
      setWarning(null)
    }

    return () => {
      if (!authState.isAuthenticated) {
        sessionManager.cleanup()
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
      const warningState = sessionManager.calculateWarning(authState.sessionExpiry!)
      setWarning(warningState)
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
      setActivity(sessionManager.getActivityState())
    }

    const interval = setInterval(updateActivity, 300000) // Update every 5 minutes
    
    return () => clearInterval(interval)
  }, [authState.isAuthenticated])

  // Record activity function
  const recordActivity = useCallback(() => {
    if (authState.isAuthenticated) {
      const newActivity = sessionManager.recordActivity()
      setActivity(newActivity)
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
      localStorage.setItem('homelab-session-expiry', newExpiry.toISOString())
      
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