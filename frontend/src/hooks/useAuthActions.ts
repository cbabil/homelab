/**
 * Auth Actions Hook
 * 
 * Handles authentication actions like login, logout, and session refresh.
 * Extracted from AuthProvider for better organization.
 */

import { useCallback } from 'react'
import type { AuthState, LoginCredentials, RegistrationCredentials, AUTH_STORAGE_KEYS } from '@/types/auth'
import { authService } from '@/services/auth/authService'
import { sessionService } from '@/services/auth/sessionService'
import { settingsService } from '@/services/settingsService'
import { securityLogger } from '@/services/systemLogger'

interface UseAuthActionsProps {
  authState: AuthState
  updateAuthState: (update: Partial<AuthState>) => void
  clearAuthState: () => void
}

export function useAuthActions({
  authState,
  updateAuthState,
  clearAuthState
}: UseAuthActionsProps) {
  
  const login = useCallback(async (credentials: LoginCredentials) => {
    updateAuthState({
      isLoading: true,
      error: null
    })

    try {
      // Initialize settings service if needed
      await settingsService.initialize()
      securityLogger.info('Login attempt started', {
        username: credentials.username,
        rememberMe: Boolean(credentials.rememberMe)
      })
      
      // Authenticate with backend
      const loginResponse = await authService.login(credentials)
      
      // Create secure session
      const sessionMetadata = await sessionService.createSession({
        userId: loginResponse.user.id,
        rememberMe: credentials.rememberMe || false,
        userAgent: navigator.userAgent,
        ipAddress: 'localhost' // Would be determined by backend
      })

      updateAuthState({
        user: loginResponse.user,
        isAuthenticated: true,
        isLoading: false,
        error: null,
        sessionExpiry: sessionMetadata.expiryTime
      })

      securityLogger.info('Login successful', {
        username: loginResponse.user.username,
        userId: loginResponse.user.id,
        sessionExpiry: sessionMetadata.expiryTime
      })
    } catch (error) {
      const errorMessage = 'Invalid username or password'
      updateAuthState({
        isLoading: false,
        error: errorMessage
      })
      securityLogger.warn('Login failed', {
        username: credentials.username,
        reason: error instanceof Error ? error.message : 'unknown-error'
      })
      throw new Error(errorMessage)
    }
  }, [updateAuthState])

  const logout = useCallback(async () => {
    try {
      securityLogger.info('Logout initiated', {
        username: authState.user?.username || 'unknown'
      })
      // Get current session info before destroying it
      const sessionMetadata = sessionService.getCurrentSession()
      let currentToken = sessionMetadata?.accessToken

      console.log('🔍 Session metadata for logout:', sessionMetadata)

      // Try to get token from different sources
      if (!currentToken) {
        // Try to get from localStorage or sessionStorage using correct keys
        try {
          const storedToken = localStorage.getItem(AUTH_STORAGE_KEYS.TOKEN) ||
                             sessionStorage.getItem(AUTH_STORAGE_KEYS.TOKEN)
          if (storedToken) {
            currentToken = storedToken
            console.log('🎟️ Found token in storage')
          }
        } catch (e) {
          console.warn('Could not access token storage:', e)
        }
      }

      // If we still don't have a token, try to get current user info for username
      let fallbackUsername: string | undefined
      if (!currentToken && authState.user) {
        fallbackUsername = authState.user.username
        console.log('🔄 Using fallback username from authState:', fallbackUsername)
      }

      console.log('🎟️ Current token for logout:', currentToken ? 'Token found' : 'No token')

      // Call auth service logout with token for backend logging
      if (currentToken) {
        console.log('✅ Calling authService.logout with token')
        await authService.logout(currentToken)
      } else if (fallbackUsername) {
        console.log('🔄 Calling authService.logout with fallback username')
        // Modify authService.logout to accept username directly
        await authService.logout(undefined, fallbackUsername)
      } else {
        console.log('⚠️ Calling authService.logout without token or username')
      await authService.logout()
      }

      // Destroy session
      await sessionService.destroySession()

      // Clear auth state
      clearAuthState()

      securityLogger.info('Logout completed', {
        username: authState.user?.username || 'unknown',
        hadToken: Boolean(currentToken)
      })
    } catch (error) {
      console.error('Logout error:', error)
      // Clear state anyway to ensure user is logged out
      clearAuthState()
      securityLogger.error('Logout error', {
        username: authState.user?.username || 'unknown',
        reason: error instanceof Error ? error.message : 'unknown-error'
      })
    }
  }, [clearAuthState, authState])

  const refreshSession = useCallback(async () => {
    try {
      updateAuthState({ isLoading: true })
      
      const renewedSession = await sessionService.renewSession()
      
      updateAuthState({
        isLoading: false,
        sessionExpiry: renewedSession.expiryTime,
        error: null
      })
    } catch (error) {
      console.error('Failed to refresh session:', error)
      await logout()
    }
  }, [updateAuthState, logout])

  const register = useCallback(async (credentials: RegistrationCredentials) => {
    updateAuthState({
      isLoading: true,
      error: null
    })

    try {
      // Initialize settings service if needed
      await settingsService.initialize()
      
      // Register new user with backend
      const registrationResponse = await authService.register(credentials)
      
      // Create secure session for new user
      const sessionMetadata = await sessionService.createSession({
        userId: registrationResponse.user.id,
        rememberMe: false, // Don't remember new registrations by default
        userAgent: navigator.userAgent,
        ipAddress: 'localhost' // Would be determined by backend
      })

      updateAuthState({
        user: registrationResponse.user,
        isAuthenticated: true,
        isLoading: false,
        error: null,
        sessionExpiry: sessionMetadata.expiryTime
      })
    } catch (error) {
      const errorMessage = 'Registration failed. Please try again.'
      updateAuthState({
        isLoading: false,
        error: errorMessage
      })
      throw new Error(errorMessage)
    }
  }, [updateAuthState])

  return {
    login,
    register,
    logout,
    refreshSession
  }
}
