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

const USER_STORAGE_KEY = 'tomo_user_data'

/**
 * Store user data in localStorage for session persistence
 */
function storeUserData(user: User): void {
  try {
    localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user))
  } catch (error) {
    console.warn('Failed to store user data:', error)
  }
}

/**
 * Retrieve user data from localStorage
 */
function getStoredUserData(): User | null {
  try {
    const stored = localStorage.getItem(USER_STORAGE_KEY)
    if (stored) {
      return JSON.parse(stored) as User
    }
  } catch (error) {
    console.warn('Failed to retrieve user data:', error)
  }
  return null
}

/**
 * Clear user data from localStorage
 */
function clearStoredUserData(): void {
  try {
    localStorage.removeItem(USER_STORAGE_KEY)
  } catch (error) {
    console.warn('Failed to clear user data:', error)
  }
}

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
          // Retrieve stored user data from localStorage
          const storedUser = getStoredUserData()

          if (storedUser && storedUser.id === validation.metadata.userId) {
            // Use stored user data if it matches the session
            setAuthState({
              user: storedUser,
              isAuthenticated: true,
              isLoading: false,
              error: null,
              sessionExpiry: validation.metadata.expiryTime,
              activity: null,
              warning: null
            })
          } else {
            // No matching user data found - session is invalid
            // This can happen if localStorage was cleared but session cookie remains
            console.warn('Session valid but user data not found, clearing session')
            clearStoredUserData()
            setAuthState(prev => ({
              ...prev,
              isLoading: false,
              error: null
            }))
          }
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
    // Store user data in localStorage when user is updated
    if (update.user) {
      storeUserData(update.user)
    }
    setAuthState(prev => ({ ...prev, ...update }))
  }, [])

  const clearAuthState = useCallback(() => {
    // Clear stored user data on logout
    clearStoredUserData()
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