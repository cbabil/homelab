/**
 * Auth State Hook
 * 
 * Manages authentication state and session monitoring.
 * Extracted from AuthProvider for better organization.
 */

import { useState, useEffect, useCallback } from 'react'
import type { AuthState, User } from '@/types/auth'
import { sessionService } from '@/services/auth/sessionService'
import { settingsService } from '@/services/settingsService'

export function useAuthState() {
  const [authState, setAuthState] = useState<AuthState>({
    user: null,
    isAuthenticated: false,
    isLoading: true,
    error: null,
    sessionExpiry: null,
    activity: null,
    warning: null
  })

  // Initialize auth state from session
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        // Initialize settings service first
        await settingsService.initialize()
        
        const validation = await sessionService.validateSession()
        
        if (validation.isValid && validation.metadata) {
          // In production, get user data from backend using session
          // For now, reconstruct from session metadata
          const mockUser: User = {
            id: validation.metadata.userId,
            username: 'admin', // Would be fetched from backend
            email: 'admin@homelab.local',
            role: 'admin',
            lastLogin: validation.metadata.startTime,
            isActive: true,
            preferences: {
              theme: 'dark',
              notifications: true
            }
          }

          setAuthState({
            user: mockUser,
            isAuthenticated: true,
            isLoading: false,
            error: null,
            sessionExpiry: validation.metadata.expiryTime,
            activity: null,
            warning: null
          })
        } else {
          setAuthState(prev => ({
            ...prev,
            isLoading: false,
            error: null
          }))
        }
      } catch (error) {
        console.error('Failed to initialize auth:', error)
        setAuthState(prev => ({
          ...prev,
          isLoading: false,
          error: null
        }))
      }
    }

    initializeAuth()
  }, [])

  // Monitor session expiry
  useEffect(() => {
    if (!authState.isAuthenticated) {
      return
    }

    const checkSession = async () => {
      const validation = await sessionService.validateSession()
      if (!validation.isValid) {
        setAuthState(prev => ({
          ...prev,
          isAuthenticated: false,
          user: null,
          error: null
        }))
      }
    }

    // Check session every 5 minutes
    const interval = setInterval(checkSession, 300000)
    return () => clearInterval(interval)
  }, [authState.isAuthenticated])

  const updateAuthState = useCallback((update: Partial<AuthState>) => {
    setAuthState(prev => ({ ...prev, ...update }))
  }, [])

  const clearAuthState = useCallback(() => {
    setAuthState({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      sessionExpiry: null,
      activity: null,
      warning: null
    })
  }, [])

  return {
    authState,
    updateAuthState,
    clearAuthState
  }
}