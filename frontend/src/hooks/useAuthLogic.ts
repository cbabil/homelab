/**
 * Auth Logic Hook
 * 
 * Core authentication logic with JWT-based session management.
 * Handles login, logout, and session management with real JWT tokens.
 */

import { useState, useEffect, useCallback } from 'react'
import { LoginCredentials } from '@/types/auth'
import { createInitialAuthState, createLoadingState } from './authStateHelpers'
import { initializeAuth } from './authInitializer'
import { performLogin, performLogout, performRefresh } from './authOperations'

export function useAuthLogic() {
  const [authState, setAuthState] = useState(createInitialAuthState())

  // Initialize auth state from storage with JWT validation
  useEffect(() => {
    const handleInitialize = async () => {
      const result = await initializeAuth()
      
      if (result.success) {
        if (result.authState) {
          setAuthState(prev => ({ ...prev, ...result.authState }))
        } else {
          setAuthState(prev => ({ ...prev, isLoading: false }))
        }
      } else {
        setAuthState(prev => ({ ...prev, ...result.authState }))
      }
    }

    handleInitialize()
  }, [])

  const login = useCallback(async (credentials: LoginCredentials) => {
    setAuthState(prev => ({ ...prev, ...createLoadingState() }))
    
    const result = await performLogin(credentials)
    setAuthState(prev => ({ ...prev, ...result.authState }))
    
    if (!result.success) {
      throw new Error(result.error)
    }
  }, [])

  const logout = useCallback(async () => {
    const result = await performLogout()
    setAuthState(result.authState)
  }, [])

  const refreshSession = useCallback(async () => {
    setAuthState(prev => ({ ...prev, ...createLoadingState() }))
    const result = await performRefresh()
    setAuthState(prev => ({ ...prev, ...result.authState }))
  }, [])

  return {
    authState,
    login,
    logout,
    refreshSession
  }
}