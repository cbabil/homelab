/**
 * Auth Initializer
 * 
 * Handles authentication initialization and session restoration
 * with JWT token validation.
 */

import { settingsService } from '@/services/settingsService'
import { authService } from '@/services/auth/authService'
import { 
  getStoredAuthData, 
  isStoredSessionExpired,
  clearStoredAuth
} from './authStorageHelpers'
import {
  createAuthenticatedState,
  createErrorState
} from './authStateHelpers'
import type { AuthState } from '@/types/auth'

export interface AuthInitResult {
  success: boolean
  authState?: Partial<AuthState>
  error?: string
}

/**
 * Initialize authentication from stored data
 */
export async function initializeAuth(): Promise<AuthInitResult> {
  try {
    await settingsService.initialize()
    await authService.initialize()
    
    const storedData = getStoredAuthData()
    
    if (storedData.token && storedData.user && storedData.sessionExpiry) {
      if (!isStoredSessionExpired()) {
        const isValidToken = await authService.validateToken(storedData.token)
        
        if (isValidToken) {
          return {
            success: true,
            authState: createAuthenticatedState(
              storedData.user, 
              storedData.sessionExpiry!, 
              storedData.tokenType || 'JWT'
            )
          }
        }
      }
    }

    clearStoredAuth()
    return { success: true }
  } catch (error) {
    console.error('Failed to initialize auth:', error)
    clearStoredAuth()
    return {
      success: false,
      error: 'Failed to restore session',
      authState: createErrorState('Failed to restore session')
    }
  }
}