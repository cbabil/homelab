/**
 * Authentication Integration Tests
 * 
 * Integration tests to verify secure cookie-based authentication system
 * works correctly with settings service and provides expected security features.
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { settingsService } from '../../settingsService'
import { sessionService } from '../sessionService'
import { authApi } from '../../api/authApi'

// Mock localStorage for tests
const mockLocalStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn()
}

Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage
})

describe('Authentication Integration', () => {
  beforeEach(async () => {
    vi.clearAllMocks()
    mockLocalStorage.getItem.mockReturnValue(null)
    
    // Mock console methods to reduce test noise
    vi.spyOn(console, 'log').mockImplementation(() => {})
    vi.spyOn(console, 'error').mockImplementation(() => {})
    vi.spyOn(console, 'warn').mockImplementation(() => {})

    // Initialize settings service
    await settingsService.initialize()
    
    // Clear any existing sessions
    try {
      await sessionService.destroySession()
    } catch {
      // Ignore errors if no session exists
    }
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Settings Integration', () => {
    it('should use session timeout from settings service', async () => {
      // Verify that session service uses settings for timeout configuration
      const timeoutMs = settingsService.getSessionTimeoutMs()
      expect(timeoutMs).toBeGreaterThan(0)
      expect(typeof timeoutMs).toBe('number')
    })

    it('should respect settings for session warning timing', async () => {
      const settings = settingsService.getSettings()
      expect(settings.security.session.showWarningMinutes).toBeGreaterThan(0)
      expect(settings.security.session.showWarningMinutes).toBeLessThanOrEqual(30)
    })

    it('should create session with timeout from settings', async () => {
      const mockOptions = {
        userId: 'test-user',
        rememberMe: false,
        userAgent: 'Test Agent',
        ipAddress: '127.0.0.1'
      }

      const session = await sessionService.createSession(mockOptions)
      
      // Verify session has expiry time
      expect(session.expiryTime).toBeTruthy()
      
      const expiryTime = new Date(session.expiryTime)
      const now = new Date()
      const timeDiff = expiryTime.getTime() - now.getTime()
      
      // Should be approximately equal to settings timeout (within 10 seconds)
      const expectedTimeout = settingsService.getSessionTimeoutMs()
      expect(Math.abs(timeDiff - expectedTimeout)).toBeLessThan(10000)
    })
  })

  describe('Security Features', () => {
    it('should generate unique session IDs', async () => {
      const options1 = {
        userId: 'user1',
        rememberMe: false,
        userAgent: 'Agent 1',
        ipAddress: '127.0.0.1'
      }

      const options2 = {
        userId: 'user2',
        rememberMe: false,
        userAgent: 'Agent 2',
        ipAddress: '192.168.1.1'
      }

      const session1 = await sessionService.createSession(options1)
      const session2 = await sessionService.createSession(options2)

      expect(session1.sessionId).not.toBe(session2.sessionId)
      expect(session1.sessionId).toMatch(/^\w+-[0-9a-f]+$/)
      expect(session2.sessionId).toMatch(/^\w+-[0-9a-f]+$/)
    })

    it('should track session metadata securely', async () => {
      const options = {
        userId: 'secure-user',
        rememberMe: true,
        userAgent: 'Secure Agent/1.0',
        ipAddress: '10.0.0.1'
      }

      const session = await sessionService.createSession(options)

      expect(session).toEqual(expect.objectContaining({
        userId: 'secure-user',
        userAgent: 'Secure Agent/1.0',
        ipAddress: '10.0.0.1'
      }))

      expect(session.startTime).toBeTruthy()
      expect(session.lastActivity).toBeTruthy()
      expect(new Date(session.startTime)).toBeInstanceOf(Date)
      expect(new Date(session.lastActivity)).toBeInstanceOf(Date)
    })

    it('should validate session expiry correctly', async () => {
      const options = {
        userId: 'expiry-test',
        rememberMe: false,
        userAgent: 'Test Agent',
        ipAddress: '127.0.0.1'
      }

      const session = await sessionService.createSession(options)
      
      // Session should be valid immediately after creation
      const validation1 = await sessionService.validateSession()
      expect(validation1.isValid).toBe(true)

      // Simulate expired session by manipulating stored data
      const expiredSession = {
        ...session,
        expiryTime: new Date(Date.now() - 1000).toISOString() // 1 second ago
      }

      mockLocalStorage.getItem
        .mockReturnValueOnce(session.sessionId)
        .mockReturnValueOnce(btoa(JSON.stringify(expiredSession)))

      const validation2 = await sessionService.validateSession()
      expect(validation2.isValid).toBe(false)
      expect(validation2.reason).toBe('Session expired')
    })
  })

  describe('API Integration', () => {
    it('should integrate auth API with session service', async () => {
      const loginRequest = {
        credentials: {
          username: 'admin',
          password: 'HomeLabAdmin123!',
          rememberMe: true
        },
        userAgent: 'Test Browser/1.0',
        ipAddress: '192.168.1.100'
      }

      const loginResponse = await authApi.login(loginRequest)

      expect(loginResponse.user.username).toBe('admin')
      expect(loginResponse.token).toMatch(/^secure-jwt-token-/)
      expect(loginResponse.sessionId).toBeTruthy()

      // Verify session was created in session service
      const currentSession = sessionService.getCurrentSession()
      expect(currentSession).toBeTruthy()
      expect(currentSession?.userId).toBe(loginResponse.user.id)
      expect(currentSession?.sessionId).toBe(loginResponse.sessionId)
    })

    it('should handle logout properly', async () => {
      // First login
      const loginRequest = {
        credentials: {
          username: 'user',
          password: 'HomeLabUser123!',
          rememberMe: false
        },
        userAgent: 'Test Browser/1.0',
        ipAddress: '192.168.1.100'
      }

      await authApi.login(loginRequest)
      
      // Verify session exists
      let currentSession = sessionService.getCurrentSession()
      expect(currentSession).toBeTruthy()

      // Logout
      await authApi.logout()

      // Verify session is destroyed
      currentSession = sessionService.getCurrentSession()
      expect(currentSession).toBeNull()
    })

    it('should handle session refresh', async () => {
      // Login first
      const loginRequest = {
        credentials: {
          username: 'admin',
          password: 'HomeLabAdmin123!',
          rememberMe: true
        },
        userAgent: 'Test Browser/1.0',
        ipAddress: '192.168.1.100'
      }

      const loginResponse = await authApi.login(loginRequest)
      const originalSession = sessionService.getCurrentSession()

      expect(originalSession).toBeTruthy()

      // Wait a moment to ensure different timestamps
      await new Promise(resolve => setTimeout(resolve, 10))

      // Refresh session
      const refreshResponse = await authApi.refreshSession({
        sessionId: loginResponse.sessionId!,
        refreshToken: loginResponse.refreshToken!
      })

      expect(refreshResponse.user.id).toBe(loginResponse.user.id)
      expect(refreshResponse.token).toMatch(/^refreshed-token-/)

      const refreshedSession = sessionService.getCurrentSession()
      expect(refreshedSession).toBeTruthy()
      expect(refreshedSession?.sessionId).toBe(originalSession?.sessionId)
      expect(new Date(refreshedSession!.lastActivity).getTime()).toBeGreaterThan(
        new Date(originalSession!.lastActivity).getTime()
      )
    })
  })

  describe('Error Handling', () => {
    it('should handle invalid login credentials securely', async () => {
      const invalidRequest = {
        credentials: {
          username: 'hacker',
          password: 'wrongpassword'
        },
        userAgent: 'Malicious Client',
        ipAddress: '192.168.1.200'
      }

      await expect(authApi.login(invalidRequest)).rejects.toThrow(
        'Invalid username or password'
      )

      // Verify no session was created
      const currentSession = sessionService.getCurrentSession()
      expect(currentSession).toBeNull()
    })

    it('should handle storage errors gracefully', async () => {
      mockLocalStorage.setItem.mockImplementation(() => {
        throw new Error('Storage quota exceeded')
      })

      const options = {
        userId: 'test-user',
        rememberMe: false,
        userAgent: 'Test Agent',
        ipAddress: '127.0.0.1'
      }

      await expect(sessionService.createSession(options)).rejects.toThrow(
        'Failed to create session'
      )
    })
  })

  describe('Activity Tracking', () => {
    it('should record user activity properly', async () => {
      const options = {
        userId: 'active-user',
        rememberMe: false,
        userAgent: 'Active Agent',
        ipAddress: '127.0.0.1'
      }

      await sessionService.createSession(options)
      const originalActivity = sessionService.getCurrentSession()?.lastActivity

      // Wait a moment
      await new Promise(resolve => setTimeout(resolve, 10))

      // Record activity
      sessionService.recordActivity()

      const updatedActivity = sessionService.getCurrentSession()?.lastActivity
      expect(new Date(updatedActivity!).getTime()).toBeGreaterThan(
        new Date(originalActivity!).getTime()
      )
    })

    it('should calculate time to expiry correctly', async () => {
      const options = {
        userId: 'expiry-user',
        rememberMe: false,
        userAgent: 'Expiry Agent',
        ipAddress: '127.0.0.1'
      }

      await sessionService.createSession(options)
      
      const timeToExpiry = sessionService.getTimeToExpiry()
      const expectedTimeout = settingsService.getSessionTimeoutMs()
      
      // Should be approximately equal to timeout (within 10 seconds)
      expect(Math.abs(timeToExpiry - expectedTimeout)).toBeLessThan(10000)
      expect(timeToExpiry).toBeGreaterThan(0)
    })
  })
})