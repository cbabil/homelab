/**
 * Auth Operations
 * 
 * Core authentication operations including login, logout, and refresh
 * with JWT token management and state updates.
 */

import { LoginCredentials, AUTH_STORAGE_KEYS } from '@/types/auth'
import { authService } from '@/services/auth/authService'
import { storeAuthData, clearStoredAuth } from './authStorageHelpers'
import {
  createAuthenticatedState,
  createUnauthenticatedState,
  createErrorState
} from './authStateHelpers'

export interface AuthOperationResult {
  success: boolean
  authState?: any
  error?: string
}

/**
 * Perform login operation
 */
export async function performLogin(
  credentials: LoginCredentials
): Promise<AuthOperationResult> {
  try {
    const loginResponse = await authService.login(credentials)
    const sessionExpiry = storeAuthData(loginResponse, credentials.rememberMe || false)

    return {
      success: true,
      authState: createAuthenticatedState(
        loginResponse.user, 
        sessionExpiry, 
        loginResponse.tokenType || 'JWT'
      )
    }
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Login failed'
    return {
      success: false,
      error: errorMessage,
      authState: createErrorState(errorMessage)
    }
  }
}

/**
 * Perform logout operation
 */
export async function performLogout(): Promise<AuthOperationResult> {
  try {
    const token = localStorage.getItem(AUTH_STORAGE_KEYS.TOKEN)
    if (token) {
      await authService.logout(token)
    }
  } catch (error) {
    console.error('Logout cleanup error:', error)
  } finally {
    clearStoredAuth()
  }
  
  return {
    success: true,
    authState: createUnauthenticatedState()
  }
}

/**
 * Perform token refresh operation
 */
export async function performRefresh(): Promise<AuthOperationResult> {
  const refreshToken = localStorage.getItem(AUTH_STORAGE_KEYS.REFRESH_TOKEN)
  
  if (!refreshToken) {
    const logoutResult = await performLogout()
    return logoutResult
  }

  try {
    const loginResponse = await authService.refreshToken(refreshToken)
    const sessionExpiry = storeAuthData(loginResponse, true)

    return {
      success: true,
      authState: createAuthenticatedState(
        loginResponse.user, 
        sessionExpiry, 
        loginResponse.tokenType || 'JWT'
      )
    }
  } catch (error) {
    console.error('Failed to refresh session:', error)
    const logoutResult = await performLogout()
    return logoutResult
  }
}