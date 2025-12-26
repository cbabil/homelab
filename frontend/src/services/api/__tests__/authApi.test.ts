/**
 * Auth API Tests
 * 
 * Comprehensive test suite for authentication API service functionality.
 * Tests login, logout, session management, and error handling.
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { authApi, SessionCreateRequest, SessionRefreshRequest } from '../authApi'
import { LoginCredentials } from '@/types/auth'

// Mock session service
const mockSessionService = {
  createSession: vi.fn(),
  validateSession: vi.fn(),
  renewSession: vi.fn(),
  destroySession: vi.fn(),
  getCurrentSession: vi.fn()
}

vi.mock('../../auth/sessionService', () => ({
  sessionService: mockSessionService
}))

describe('AuthApiService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    
    // Mock console methods
    vi.spyOn(console, 'log').mockImplementation(() => {})
    vi.spyOn(console, 'error').mockImplementation(() => {})
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Login', () => {
    const validCredentials: LoginCredentials = {
      username: 'admin',
      password: 'HomeLabAdmin123!',
      rememberMe: true
    }

    const loginRequest: SessionCreateRequest = {
      credentials: validCredentials,
      userAgent: 'Mozilla/5.0',
      ipAddress: '127.0.0.1'
    }

    it('should login successfully with valid admin credentials', async () => {
      const mockSessionMetadata = {
        sessionId: 'session-123',
        userId: '1',
        userAgent: 'Mozilla/5.0',
        ipAddress: '127.0.0.1',
        startTime: new Date().toISOString(),
        lastActivity: new Date().toISOString(),
        expiryTime: new Date(Date.now() + 3600000).toISOString()
      }

      mockSessionService.createSession.mockResolvedValue(mockSessionMetadata)

      const result = await authApi.login(loginRequest)

      expect(result.user.username).toBe('admin')
      expect(result.user.role).toBe('admin')
      expect(result.token).toMatch(/^secure-jwt-token-/)
      expect(result.refreshToken).toMatch(/^secure-refresh-token-/)
      expect(result.expiresIn).toBe(3600)
      expect(result.sessionId).toBe('session-123')

      expect(mockSessionService.createSession).toHaveBeenCalledWith({
        userId: '1',
        rememberMe: true,
        userAgent: 'Mozilla/5.0',
        ipAddress: '127.0.0.1'
      })
    })

    it('should login successfully with valid user credentials', async () => {
      const userCredentials: LoginCredentials = {
        username: 'user',
        password: 'HomeLabUser123!',
        rememberMe: false
      }

      const userRequest: SessionCreateRequest = {
        credentials: userCredentials,
        userAgent: 'Mozilla/5.0',
        ipAddress: '127.0.0.1'
      }

      const mockSessionMetadata = {
        sessionId: 'session-456',
        userId: '2',
        userAgent: 'Mozilla/5.0',
        ipAddress: '127.0.0.1',
        startTime: new Date().toISOString(),
        lastActivity: new Date().toISOString(),
        expiryTime: new Date(Date.now() + 3600000).toISOString()
      }

      mockSessionService.createSession.mockResolvedValue(mockSessionMetadata)

      const result = await authApi.login(userRequest)

      expect(result.user.username).toBe('user')
      expect(result.user.role).toBe('user')
      expect(result.sessionId).toBe('session-456')

      expect(mockSessionService.createSession).toHaveBeenCalledWith({
        userId: '2',
        rememberMe: false,
        userAgent: 'Mozilla/5.0',
        ipAddress: '127.0.0.1'
      })
    })

    it('should reject invalid credentials', async () => {
      const invalidCredentials: LoginCredentials = {
        username: 'invalid',
        password: 'wrongpassword'
      }

      const invalidRequest: SessionCreateRequest = {
        credentials: invalidCredentials,
        userAgent: 'Mozilla/5.0',
        ipAddress: '127.0.0.1'
      }

      await expect(authApi.login(invalidRequest)).rejects.toThrow(
        'Invalid username or password'
      )

      expect(mockSessionService.createSession).not.toHaveBeenCalled()
    })

    it('should log successful login', async () => {
      const mockSessionMetadata = {
        sessionId: 'session-123',
        userId: '1',
        userAgent: 'Mozilla/5.0',
        ipAddress: '127.0.0.1',
        startTime: new Date().toISOString(),
        lastActivity: new Date().toISOString(),
        expiryTime: new Date(Date.now() + 3600000).toISOString()
      }

      mockSessionService.createSession.mockResolvedValue(mockSessionMetadata)

      await authApi.login(loginRequest)

      expect(console.log).toHaveBeenCalledWith(
        '[AuthAPI]',
        'login_success',
        expect.objectContaining({
          userId: '1',
          sessionId: 'session-123'
        })
      )
    })

    it('should log failed login attempts', async () => {
      const invalidRequest: SessionCreateRequest = {
        credentials: { username: 'hacker', password: 'invalid' },
        userAgent: 'Mozilla/5.0',
        ipAddress: '192.168.1.100'
      }

      await expect(authApi.login(invalidRequest)).rejects.toThrow()

      expect(console.log).toHaveBeenCalledWith(
        '[AuthAPI]',
        'login_error',
        expect.objectContaining({
          username: 'hacker',
          error: expect.stringContaining('Invalid username or password')
        })
      )
    })

    it('should handle session creation errors', async () => {
      mockSessionService.createSession.mockRejectedValue(new Error('Session creation failed'))

      await expect(authApi.login(loginRequest)).rejects.toThrow('Session creation failed')

      expect(console.log).toHaveBeenCalledWith(
        '[AuthAPI]',
        'login_error',
        expect.objectContaining({
          error: expect.stringContaining('Session creation failed')
        })
      )
    })
  })

  describe('Session Refresh', () => {
    const refreshRequest: SessionRefreshRequest = {
      sessionId: 'session-123',
      refreshToken: 'refresh-token-123'
    }

    it('should refresh session successfully', async () => {
      const mockValidation = {
        isValid: true,
        metadata: {
          sessionId: 'session-123',
          userId: '1',
          userAgent: 'Mozilla/5.0',
          ipAddress: '127.0.0.1',
          startTime: new Date().toISOString(),
          lastActivity: new Date().toISOString(),
          expiryTime: new Date(Date.now() + 3600000).toISOString()
        }
      }

      const mockRenewedSession = {
        sessionId: 'session-123',
        userId: '1',
        userAgent: 'Mozilla/5.0',
        ipAddress: '127.0.0.1',
        startTime: new Date().toISOString(),
        lastActivity: new Date().toISOString(),
        expiryTime: new Date(Date.now() + 7200000).toISOString() // 2 hours
      }

      mockSessionService.validateSession.mockResolvedValue(mockValidation)
      mockSessionService.renewSession.mockResolvedValue(mockRenewedSession)

      const result = await authApi.refreshSession(refreshRequest)

      expect(result.user.id).toBe('1')
      expect(result.token).toMatch(/^refreshed-token-/)
      expect(result.refreshToken).toMatch(/^refreshed-refresh-token-/)
      expect(result.sessionId).toBe('session-123')

      expect(console.log).toHaveBeenCalledWith(
        '[AuthAPI]',
        'session_refreshed',
        expect.objectContaining({
          sessionId: 'session-123',
          userId: '1'
        })
      )
    })

    it('should reject refresh for invalid session', async () => {
      mockSessionService.validateSession.mockResolvedValue({
        isValid: false,
        reason: 'Session expired'
      })

      await expect(authApi.refreshSession(refreshRequest)).rejects.toThrow(
        'Invalid session for refresh'
      )

      expect(mockSessionService.renewSession).not.toHaveBeenCalled()
    })

    it('should handle refresh errors', async () => {
      mockSessionService.validateSession.mockRejectedValue(new Error('Validation failed'))

      await expect(authApi.refreshSession(refreshRequest)).rejects.toThrow('Validation failed')

      expect(console.log).toHaveBeenCalledWith(
        '[AuthAPI]',
        'refresh_error',
        expect.objectContaining({
          sessionId: 'session-123',
          error: expect.stringContaining('Validation failed')
        })
      )
    })
  })

  describe('Logout', () => {
    it('should logout successfully', async () => {
      const mockCurrentSession = {
        sessionId: 'session-123',
        userId: '1'
      }

      mockSessionService.getCurrentSession.mockReturnValue(mockCurrentSession)
      mockSessionService.destroySession.mockResolvedValue(undefined)

      await authApi.logout()

      expect(mockSessionService.destroySession).toHaveBeenCalled()
      expect(console.log).toHaveBeenCalledWith(
        '[AuthAPI]',
        'logout_success',
        expect.objectContaining({
          sessionId: 'session-123',
          userId: '1'
        })
      )
    })

    it('should handle logout when no session exists', async () => {
      mockSessionService.getCurrentSession.mockReturnValue(null)

      await authApi.logout()

      expect(mockSessionService.destroySession).toHaveBeenCalled()
      // Should not log success when no session exists
      expect(console.log).not.toHaveBeenCalledWith(
        '[AuthAPI]',
        'logout_success',
        expect.any(Object)
      )
    })

    it('should handle logout errors', async () => {
      const mockCurrentSession = { sessionId: 'session-123', userId: '1' }
      mockSessionService.getCurrentSession.mockReturnValue(mockCurrentSession)
      mockSessionService.destroySession.mockRejectedValue(new Error('Destroy failed'))

      await expect(authApi.logout()).rejects.toThrow('Destroy failed')

      expect(console.log).toHaveBeenCalledWith(
        '[AuthAPI]',
        'logout_error',
        expect.objectContaining({
          error: expect.stringContaining('Destroy failed')
        })
      )
    })
  })

  describe('Session Validation', () => {
    it('should validate session successfully', async () => {
      mockSessionService.validateSession.mockResolvedValue({
        isValid: true,
        metadata: { sessionId: 'session-123' }
      })

      const isValid = await authApi.validateSession()
      expect(isValid).toBe(true)
    })

    it('should return false for invalid session', async () => {
      mockSessionService.validateSession.mockResolvedValue({
        isValid: false,
        reason: 'Session expired'
      })

      const isValid = await authApi.validateSession()
      expect(isValid).toBe(false)
    })

    it('should handle validation errors', async () => {
      mockSessionService.validateSession.mockRejectedValue(new Error('Validation error'))

      const isValid = await authApi.validateSession()
      expect(isValid).toBe(false)

      expect(console.log).toHaveBeenCalledWith(
        '[AuthAPI]',
        'validation_error',
        expect.objectContaining({
          error: expect.stringContaining('Validation error')
        })
      )
    })
  })

  describe('Get Current Session', () => {
    it('should return current session metadata', async () => {
      const mockValidation = {
        isValid: true,
        metadata: {
          sessionId: 'session-123',
          userId: '1',
          userAgent: 'Mozilla/5.0',
          ipAddress: '127.0.0.1',
          startTime: new Date().toISOString(),
          lastActivity: new Date().toISOString(),
          expiryTime: new Date(Date.now() + 3600000).toISOString()
        }
      }

      mockSessionService.validateSession.mockResolvedValue(mockValidation)

      const session = await authApi.getCurrentSession()
      expect(session).toEqual(mockValidation.metadata)
    })

    it('should return null for invalid session', async () => {
      mockSessionService.validateSession.mockResolvedValue({
        isValid: false,
        reason: 'No session'
      })

      const session = await authApi.getCurrentSession()
      expect(session).toBeNull()
    })
  })

  describe('List User Sessions', () => {
    it('should list sessions for current user', async () => {
      const mockSession = {
        sessionId: 'session-123',
        userId: 'user123',
        userAgent: 'Mozilla/5.0',
        ipAddress: '127.0.0.1',
        startTime: new Date().toISOString(),
        lastActivity: new Date().toISOString(),
        expiryTime: new Date(Date.now() + 3600000).toISOString()
      }

      mockSessionService.getCurrentSession.mockReturnValue(mockSession)

      const result = await authApi.listUserSessions('user123')

      expect(result.sessions).toHaveLength(1)
      expect(result.sessions[0]).toEqual(mockSession)
      expect(result.total).toBe(1)
    })

    it('should return empty list for different user', async () => {
      const mockSession = {
        sessionId: 'session-123',
        userId: 'user123'
      }

      mockSessionService.getCurrentSession.mockReturnValue(mockSession)

      const result = await authApi.listUserSessions('other-user')

      expect(result.sessions).toHaveLength(0)
      expect(result.total).toBe(0)
    })

    it('should handle list sessions errors', async () => {
      mockSessionService.getCurrentSession.mockImplementation(() => {
        throw new Error('Session error')
      })

      await expect(authApi.listUserSessions('user123')).rejects.toThrow('Session error')

      expect(console.log).toHaveBeenCalledWith(
        '[AuthAPI]',
        'list_sessions_error',
        expect.objectContaining({
          userId: 'user123',
          error: expect.stringContaining('Session error')
        })
      )
    })
  })

  describe('Terminate Session', () => {
    it('should terminate current session', async () => {
      const mockSession = {
        sessionId: 'session-123',
        userId: 'user123'
      }

      mockSessionService.getCurrentSession.mockReturnValue(mockSession)
      mockSessionService.destroySession.mockResolvedValue(undefined)

      await authApi.terminateSession('session-123')

      expect(mockSessionService.destroySession).toHaveBeenCalled()
      expect(console.log).toHaveBeenCalledWith(
        '[AuthAPI]',
        'session_terminated',
        expect.objectContaining({
          sessionId: 'session-123',
          userId: 'user123'
        })
      )
    })

    it('should not terminate different session', async () => {
      const mockSession = { sessionId: 'other-session', userId: 'user123' }
      mockSessionService.getCurrentSession.mockReturnValue(mockSession)

      await authApi.terminateSession('session-123')

      expect(mockSessionService.destroySession).not.toHaveBeenCalled()
    })

    it('should handle termination errors', async () => {
      const mockSession = { sessionId: 'session-123', userId: 'user123' }
      mockSessionService.getCurrentSession.mockReturnValue(mockSession)
      mockSessionService.destroySession.mockRejectedValue(new Error('Destroy failed'))

      await expect(authApi.terminateSession('session-123')).rejects.toThrow('Destroy failed')

      expect(console.log).toHaveBeenCalledWith(
        '[AuthAPI]',
        'terminate_session_error',
        expect.objectContaining({
          sessionId: 'session-123',
          error: expect.stringContaining('Destroy failed')
        })
      )
    })
  })
})