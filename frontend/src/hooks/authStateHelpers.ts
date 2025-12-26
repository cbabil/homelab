/**
 * Auth State Helpers
 * 
 * Helper functions for managing authentication state changes
 * and initialization with JWT token support.
 */

import { AuthState } from '@/types/auth'

/**
 * Create initial auth state
 */
export function createInitialAuthState(): AuthState {
  return {
    user: null,
    isAuthenticated: false,
    isLoading: true,
    error: null,
    sessionExpiry: null,
    activity: null,
    warning: null
  }
}

/**
 * Create authenticated state from auth data
 */
export function createAuthenticatedState(
  user: any,
  sessionExpiry: string,
  tokenType: 'JWT' | 'Bearer' = 'JWT'
): Partial<AuthState> {
  return {
    user,
    isAuthenticated: true,
    isLoading: false,
    sessionExpiry,
    tokenType,
    error: null
  }
}

/**
 * Create unauthenticated state
 */
export function createUnauthenticatedState(): AuthState {
  return {
    user: null,
    isAuthenticated: false,
    isLoading: false,
    error: null,
    sessionExpiry: null,
    activity: null,
    warning: null
  }
}

/**
 * Create loading state
 */
export function createLoadingState(error?: string): Partial<AuthState> {
  return {
    isLoading: true,
    error: error || null
  }
}

/**
 * Create error state
 */
export function createErrorState(error: string): Partial<AuthState> {
  return {
    isLoading: false,
    error
  }
}