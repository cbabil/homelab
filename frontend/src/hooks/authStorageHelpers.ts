/**
 * Auth Storage Helpers
 * 
 * Helper functions for storing and managing authentication data
 * in localStorage/sessionStorage with JWT token support.
 */

import { LoginResponse, User, AUTH_STORAGE_KEYS } from '@/types/auth'

/**
 * Store authentication data with JWT token metadata
 */
export function storeAuthData(
  loginResponse: LoginResponse, 
  rememberMe: boolean
): string {
  const sessionExpiry = new Date()
  sessionExpiry.setSeconds(sessionExpiry.getSeconds() + loginResponse.expiresIn)

  const storage = rememberMe ? localStorage : sessionStorage
  storage.setItem(AUTH_STORAGE_KEYS.TOKEN, loginResponse.token)
  storage.setItem(AUTH_STORAGE_KEYS.USER, JSON.stringify(loginResponse.user))
  storage.setItem(AUTH_STORAGE_KEYS.SESSION_EXPIRY, sessionExpiry.toISOString())
  storage.setItem(AUTH_STORAGE_KEYS.TOKEN_TYPE, loginResponse.tokenType || 'JWT')
  
  if (rememberMe) {
    localStorage.setItem(AUTH_STORAGE_KEYS.REMEMBER_ME, 'true')
    if (loginResponse.refreshToken) {
      localStorage.setItem(AUTH_STORAGE_KEYS.REFRESH_TOKEN, loginResponse.refreshToken)
    }
  }

  return sessionExpiry.toISOString()
}

/**
 * Clear all stored authentication data
 */
export function clearStoredAuth(): void {
  Object.values(AUTH_STORAGE_KEYS).forEach(key => {
    localStorage.removeItem(key)
    sessionStorage.removeItem(key)
  })
}

/**
 * Get stored authentication data
 */
export interface StoredAuthData {
  token: string | null
  user: User | null
  sessionExpiry: string | null
  tokenType: 'JWT' | 'Bearer' | null
}

export function getStoredAuthData(): StoredAuthData {
  return {
    token: localStorage.getItem(AUTH_STORAGE_KEYS.TOKEN),
    user: (() => {
      const storedUser = localStorage.getItem(AUTH_STORAGE_KEYS.USER)
      try {
        return storedUser ? JSON.parse(storedUser) as User : null
      } catch {
        return null
      }
    })(),
    sessionExpiry: localStorage.getItem(AUTH_STORAGE_KEYS.SESSION_EXPIRY),
    tokenType: localStorage.getItem(AUTH_STORAGE_KEYS.TOKEN_TYPE) as 'JWT' | 'Bearer' | null
  }
}

/**
 * Check if stored session is expired
 */
export function isStoredSessionExpired(): boolean {
  const sessionExpiry = localStorage.getItem(AUTH_STORAGE_KEYS.SESSION_EXPIRY)
  if (!sessionExpiry) return true
  
  const expiryDate = new Date(sessionExpiry)
  return expiryDate <= new Date()
}