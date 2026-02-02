/**
 * Auth Operations Tests
 *
 * Unit tests for authentication operations including login, logout, and refresh.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { performLogin, performLogout, performRefresh } from '../authOperations'
import { authService } from '@/services/auth/authService'
import { AUTH_STORAGE_KEYS } from '@/types/auth'

// Mock authService
vi.mock('@/services/auth/authService', () => ({
  authService: {
    login: vi.fn(),
    logout: vi.fn(),
    refreshToken: vi.fn()
  }
}))

describe('authOperations', () => {
  beforeEach(() => {
    // Clear all mocks
    vi.clearAllMocks()

    // Clear storage
    localStorage.clear()
    sessionStorage.clear()
  })

  afterEach(() => {
    localStorage.clear()
    sessionStorage.clear()
  })

  describe('performLogout', () => {
    it('should call authService.logout with token when token exists', async () => {
      const mockToken = 'test-jwt-token'
      localStorage.setItem(AUTH_STORAGE_KEYS.TOKEN, mockToken)
      vi.mocked(authService.logout).mockResolvedValue(undefined)

      const result = await performLogout()

      expect(authService.logout).toHaveBeenCalledWith(mockToken)
      expect(result.success).toBe(true)
    })

    it('should not call authService.logout when no token exists', async () => {
      const result = await performLogout()

      expect(authService.logout).not.toHaveBeenCalled()
      expect(result.success).toBe(true)
    })

    it('should clear all auth data from localStorage', async () => {
      // Set up auth data
      localStorage.setItem(AUTH_STORAGE_KEYS.TOKEN, 'test-token')
      localStorage.setItem(AUTH_STORAGE_KEYS.USER, JSON.stringify({ id: '1', username: 'admin' }))
      localStorage.setItem(AUTH_STORAGE_KEYS.SESSION_EXPIRY, new Date().toISOString())
      localStorage.setItem(AUTH_STORAGE_KEYS.REFRESH_TOKEN, 'refresh-token')
      localStorage.setItem(AUTH_STORAGE_KEYS.REMEMBER_ME, 'true')
      localStorage.setItem(AUTH_STORAGE_KEYS.TOKEN_TYPE, 'JWT')

      await performLogout()

      // Verify all keys are cleared
      expect(localStorage.getItem(AUTH_STORAGE_KEYS.TOKEN)).toBeNull()
      expect(localStorage.getItem(AUTH_STORAGE_KEYS.USER)).toBeNull()
      expect(localStorage.getItem(AUTH_STORAGE_KEYS.SESSION_EXPIRY)).toBeNull()
      expect(localStorage.getItem(AUTH_STORAGE_KEYS.REFRESH_TOKEN)).toBeNull()
      expect(localStorage.getItem(AUTH_STORAGE_KEYS.REMEMBER_ME)).toBeNull()
      expect(localStorage.getItem(AUTH_STORAGE_KEYS.TOKEN_TYPE)).toBeNull()
    })

    it('should clear all auth data from sessionStorage', async () => {
      // Set up auth data in sessionStorage
      sessionStorage.setItem(AUTH_STORAGE_KEYS.TOKEN, 'test-token')
      sessionStorage.setItem(AUTH_STORAGE_KEYS.USER, JSON.stringify({ id: '1', username: 'admin' }))
      sessionStorage.setItem(AUTH_STORAGE_KEYS.SESSION_EXPIRY, new Date().toISOString())

      await performLogout()

      // Verify all keys are cleared
      expect(sessionStorage.getItem(AUTH_STORAGE_KEYS.TOKEN)).toBeNull()
      expect(sessionStorage.getItem(AUTH_STORAGE_KEYS.USER)).toBeNull()
      expect(sessionStorage.getItem(AUTH_STORAGE_KEYS.SESSION_EXPIRY)).toBeNull()
    })

    it('should return unauthenticated state after logout', async () => {
      localStorage.setItem(AUTH_STORAGE_KEYS.TOKEN, 'test-token')
      vi.mocked(authService.logout).mockResolvedValue(undefined)

      const result = await performLogout()

      expect(result.success).toBe(true)
      expect(result.authState).toBeDefined()
      expect(result.authState?.isAuthenticated).toBe(false)
      expect(result.authState?.user).toBeNull()
    })

    it('should handle logout API errors gracefully', async () => {
      localStorage.setItem(AUTH_STORAGE_KEYS.TOKEN, 'test-token')
      vi.mocked(authService.logout).mockRejectedValue(new Error('Network error'))

      const result = await performLogout()

      // Should still succeed and clear data even if API call fails
      expect(result.success).toBe(true)
      expect(localStorage.getItem(AUTH_STORAGE_KEYS.TOKEN)).toBeNull()
    })

    it('should clear auth data even when logout API fails', async () => {
      localStorage.setItem(AUTH_STORAGE_KEYS.TOKEN, 'test-token')
      localStorage.setItem(AUTH_STORAGE_KEYS.USER, JSON.stringify({ id: '1' }))
      vi.mocked(authService.logout).mockRejectedValue(new Error('Server error'))

      await performLogout()

      // Auth data should still be cleared
      expect(localStorage.getItem(AUTH_STORAGE_KEYS.TOKEN)).toBeNull()
      expect(localStorage.getItem(AUTH_STORAGE_KEYS.USER)).toBeNull()
    })
  })

  describe('performLogin', () => {
    const mockCredentials = {
      username: 'admin',
      password: 'password123',
      rememberMe: false
    }

    const mockLoginResponse = {
      token: 'new-jwt-token',
      refreshToken: 'refresh-token',
      expiresIn: 3600,
      tokenType: 'JWT' as const,
      user: {
        id: '1',
        username: 'admin',
        email: 'admin@example.com',
        role: 'admin' as const,
        isActive: true,
        createdAt: new Date().toISOString(),
        lastLogin: new Date().toISOString()
      }
    }

    it('should store auth data on successful login', async () => {
      vi.mocked(authService.login).mockResolvedValue(mockLoginResponse)

      const result = await performLogin(mockCredentials)

      expect(result.success).toBe(true)
      expect(sessionStorage.getItem(AUTH_STORAGE_KEYS.TOKEN)).toBe(mockLoginResponse.token)
    })

    it('should return authenticated state on successful login', async () => {
      vi.mocked(authService.login).mockResolvedValue(mockLoginResponse)

      const result = await performLogin(mockCredentials)

      expect(result.success).toBe(true)
      expect(result.authState?.isAuthenticated).toBe(true)
      expect(result.authState?.user).toEqual(mockLoginResponse.user)
    })

    it('should handle login errors', async () => {
      vi.mocked(authService.login).mockRejectedValue(new Error('Invalid credentials'))

      const result = await performLogin(mockCredentials)

      expect(result.success).toBe(false)
      expect(result.error).toBe('Invalid credentials')
    })

    it('should store in localStorage when rememberMe is true', async () => {
      vi.mocked(authService.login).mockResolvedValue(mockLoginResponse)

      await performLogin({ ...mockCredentials, rememberMe: true })

      expect(localStorage.getItem(AUTH_STORAGE_KEYS.TOKEN)).toBe(mockLoginResponse.token)
      expect(localStorage.getItem(AUTH_STORAGE_KEYS.REMEMBER_ME)).toBe('true')
    })
  })

  describe('performRefresh', () => {
    const mockLoginResponse = {
      token: 'new-jwt-token',
      refreshToken: 'new-refresh-token',
      expiresIn: 3600,
      tokenType: 'JWT' as const,
      user: {
        id: '1',
        username: 'admin',
        email: 'admin@example.com',
        role: 'admin' as const,
        isActive: true,
        createdAt: new Date().toISOString(),
        lastLogin: new Date().toISOString()
      }
    }

    it('should refresh token successfully', async () => {
      localStorage.setItem(AUTH_STORAGE_KEYS.REFRESH_TOKEN, 'old-refresh-token')
      vi.mocked(authService.refreshToken).mockResolvedValue(mockLoginResponse)

      const result = await performRefresh()

      expect(result.success).toBe(true)
      expect(authService.refreshToken).toHaveBeenCalledWith('old-refresh-token')
    })

    it('should logout when no refresh token exists', async () => {
      const result = await performRefresh()

      expect(result.success).toBe(true)
      expect(result.authState?.isAuthenticated).toBe(false)
    })

    it('should logout on refresh error', async () => {
      localStorage.setItem(AUTH_STORAGE_KEYS.REFRESH_TOKEN, 'expired-refresh-token')
      vi.mocked(authService.refreshToken).mockRejectedValue(new Error('Token expired'))

      const result = await performRefresh()

      expect(result.success).toBe(true)
      expect(result.authState?.isAuthenticated).toBe(false)
      expect(localStorage.getItem(AUTH_STORAGE_KEYS.REFRESH_TOKEN)).toBeNull()
    })
  })
})
