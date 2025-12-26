/**
 * Session Service Tests
 * 
 * Comprehensive test suite for secure session management functionality.
 * Tests session creation, validation, renewal, and security features.
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { sessionService, SessionMetadata, CreateSessionOptions } from '../sessionService'
import { settingsService } from '../../settingsService'

// Mock dependencies
vi.mock('../cookieUtils', async () => {
  const actual = await vi.importActual('../cookieUtils') as any
  return {
    ...actual,
    cookieUtils: {
      generateSessionId: vi.fn(() => '1234567890-abcdef0123456789'),
      setSessionCookie: vi.fn(),
      getCookie: vi.fn(),
      deleteCookie: vi.fn()
    }
  }
})

vi.mock('../../settingsService', () => ({
  settingsService: {
    getSessionTimeoutMs: vi.fn(() => 3600000), // 1 hour
    getSettings: vi.fn(() => ({
      security: {
        session: {
          showWarningMinutes: 5
        }
      }
    }))
  }
}))

// Mock localStorage
const mockLocalStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn()
}

Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage
})

describe('SessionService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockLocalStorage.getItem.mockReturnValue(null)
    
    // Mock console methods
    vi.spyOn(console, 'log').mockImplementation(() => {})
    vi.spyOn(console, 'error').mockImplementation(() => {})
    vi.spyOn(console, 'warn').mockImplementation(() => {})
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Session Creation', () => {
    const mockOptions: CreateSessionOptions = {
      userId: 'user123',
      rememberMe: true,
      userAgent: 'Mozilla/5.0',
      ipAddress: '127.0.0.1'
    }

    it('should create new session with correct metadata', async () => {
      const session = await sessionService.createSession(mockOptions)

      expect(session).toEqual(expect.objectContaining({
        sessionId: '1234567890-abcdef0123456789',
        userId: 'user123',
        userAgent: 'Mozilla/5.0',
        ipAddress: '127.0.0.1'
      }))

      expect(session.startTime).toBeTruthy()
      expect(session.lastActivity).toBeTruthy()
      expect(session.expiryTime).toBeTruthy()
    })

    it('should set correct expiry time based on settings', async () => {
      const beforeCreate = new Date()
      const session = await sessionService.createSession(mockOptions)
      const afterCreate = new Date()

      const expiryTime = new Date(session.expiryTime)
      const expectedMin = new Date(beforeCreate.getTime() + 3600000)
      const expectedMax = new Date(afterCreate.getTime() + 3600000)

      expect(expiryTime.getTime()).toBeGreaterThanOrEqual(expectedMin.getTime())
      expect(expiryTime.getTime()).toBeLessThanOrEqual(expectedMax.getTime())
    })

    it('should store session metadata', async () => {
      await sessionService.createSession(mockOptions)

      expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
        'session_1234567890-abcdef0123456789',
        expect.any(String)
      )
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
        'current_session_id',
        '1234567890-abcdef0123456789'
      )
    })

    it('should log session creation event', async () => {
      await sessionService.createSession(mockOptions)

      expect(console.log).toHaveBeenCalledWith(
        '[Session]',
        'session_created',
        expect.objectContaining({
          sessionId: '1234567890-abcdef0123456789',
          userId: 'user123',
          rememberMe: true
        })
      )
    })

    it('should handle session creation errors', async () => {
      mockLocalStorage.setItem.mockImplementation(() => {
        throw new Error('Storage error')
      })

      await expect(sessionService.createSession(mockOptions)).rejects.toThrow(
        'Failed to create session: Error: Failed to store session: Error: Storage error'
      )

      expect(console.log).toHaveBeenCalledWith(
        '[Session]',
        'session_create_error',
        expect.objectContaining({ error: expect.stringContaining('Storage error') })
      )
    })
  })

  describe('Session Validation', () => {
    it('should validate active session successfully', async () => {
      const mockSession: SessionMetadata = {
        sessionId: '1234567890-abcdef0123456789',
        userId: 'user123',
        userAgent: 'Mozilla/5.0',
        ipAddress: '127.0.0.1',
        startTime: new Date().toISOString(),
        lastActivity: new Date().toISOString(),
        expiryTime: new Date(Date.now() + 3600000).toISOString() // 1 hour from now
      }

      mockLocalStorage.getItem
        .mockReturnValueOnce('1234567890-abcdef0123456789') // current_session_id
        .mockReturnValueOnce(btoa(JSON.stringify(mockSession))) // session data

      const result = await sessionService.validateSession()

      expect(result.isValid).toBe(true)
      expect(result.metadata).toEqual(mockSession)
    })

    it('should reject expired session', async () => {
      const expiredSession: SessionMetadata = {
        sessionId: '1234567890-abcdef0123456789',
        userId: 'user123',
        userAgent: 'Mozilla/5.0',
        ipAddress: '127.0.0.1',
        startTime: new Date(Date.now() - 7200000).toISOString(),
        lastActivity: new Date(Date.now() - 3600000).toISOString(),
        expiryTime: new Date(Date.now() - 1800000).toISOString() // 30 minutes ago
      }

      mockLocalStorage.getItem
        .mockReturnValueOnce('1234567890-abcdef0123456789')
        .mockReturnValueOnce(btoa(JSON.stringify(expiredSession)))

      const result = await sessionService.validateSession()

      expect(result.isValid).toBe(false)
      expect(result.reason).toBe('Session expired')
    })

    it('should handle missing session', async () => {
      mockLocalStorage.getItem.mockReturnValue(null)

      const result = await sessionService.validateSession()

      expect(result.isValid).toBe(false)
      expect(result.reason).toBe('No session found')
    })

    it('should update last activity on validation', async () => {
      const mockSession: SessionMetadata = {
        sessionId: '1234567890-abcdef0123456789',
        userId: 'user123',
        userAgent: 'Mozilla/5.0',
        ipAddress: '127.0.0.1',
        startTime: new Date().toISOString(),
        lastActivity: new Date(Date.now() - 600000).toISOString(), // 10 minutes ago
        expiryTime: new Date(Date.now() + 3600000).toISOString()
      }

      mockLocalStorage.getItem
        .mockReturnValueOnce('1234567890-abcdef0123456789')
        .mockReturnValueOnce(btoa(JSON.stringify(mockSession)))

      const beforeValidation = new Date()
      await sessionService.validateSession()
      const afterValidation = new Date()

      // Verify that setItem was called to update session with new lastActivity
      const setItemCalls = mockLocalStorage.setItem.mock.calls
      const sessionUpdateCall = setItemCalls.find(call => 
        call[0] === 'session_1234567890-abcdef0123456789'
      )

      expect(sessionUpdateCall).toBeTruthy()

      const updatedSession = JSON.parse(atob(sessionUpdateCall[1])) as SessionMetadata
      const lastActivityTime = new Date(updatedSession.lastActivity)

      expect(lastActivityTime.getTime()).toBeGreaterThanOrEqual(beforeValidation.getTime())
      expect(lastActivityTime.getTime()).toBeLessThanOrEqual(afterValidation.getTime())
    })
  })

  describe('Session Renewal', () => {
    it('should renew active session successfully', async () => {
      const existingSession: SessionMetadata = {
        sessionId: '1234567890-abcdef0123456789',
        userId: 'user123',
        userAgent: 'Mozilla/5.0',
        ipAddress: '127.0.0.1',
        startTime: new Date().toISOString(),
        lastActivity: new Date().toISOString(),
        expiryTime: new Date(Date.now() + 1800000).toISOString() // 30 minutes from now
      }

      mockLocalStorage.getItem
        .mockReturnValueOnce('1234567890-abcdef0123456789')
        .mockReturnValueOnce(btoa(JSON.stringify(existingSession)))

      const beforeRenewal = new Date()
      const renewed = await sessionService.renewSession()
      const afterRenewal = new Date()

      expect(renewed.sessionId).toBe(existingSession.sessionId)
      expect(renewed.userId).toBe(existingSession.userId)

      const newExpiryTime = new Date(renewed.expiryTime)
      const expectedMinExpiry = new Date(beforeRenewal.getTime() + 3600000)
      const expectedMaxExpiry = new Date(afterRenewal.getTime() + 3600000)

      expect(newExpiryTime.getTime()).toBeGreaterThanOrEqual(expectedMinExpiry.getTime())
      expect(newExpiryTime.getTime()).toBeLessThanOrEqual(expectedMaxExpiry.getTime())
    })

    it('should throw error when no session to renew', async () => {
      mockLocalStorage.getItem.mockReturnValue(null)

      await expect(sessionService.renewSession()).rejects.toThrow(
        'No active session to renew'
      )
    })

    it('should log session renewal event', async () => {
      const existingSession: SessionMetadata = {
        sessionId: '1234567890-abcdef0123456789',
        userId: 'user123',
        userAgent: 'Mozilla/5.0',
        ipAddress: '127.0.0.1',
        startTime: new Date().toISOString(),
        lastActivity: new Date().toISOString(),
        expiryTime: new Date(Date.now() + 1800000).toISOString()
      }

      mockLocalStorage.getItem
        .mockReturnValueOnce('1234567890-abcdef0123456789')
        .mockReturnValueOnce(btoa(JSON.stringify(existingSession)))

      await sessionService.renewSession()

      expect(console.log).toHaveBeenCalledWith(
        '[Session]',
        'session_renewed',
        expect.objectContaining({
          sessionId: '1234567890-abcdef0123456789',
          newExpiry: expect.any(String)
        })
      )
    })
  })

  describe('Session Destruction', () => {
    it('should destroy session and clean up', async () => {
      // Set up a current session
      await sessionService.createSession({
        userId: 'user123',
        rememberMe: false,
        userAgent: 'Mozilla/5.0',
        ipAddress: '127.0.0.1'
      })

      vi.clearAllMocks() // Clear creation calls

      await sessionService.destroySession()

      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith(
        'session_1234567890-abcdef0123456789'
      )
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('current_session_id')

      expect(console.log).toHaveBeenCalledWith(
        '[Session]',
        'session_destroyed',
        expect.objectContaining({ sessionId: '1234567890-abcdef0123456789' })
      )
    })

    it('should handle destruction errors gracefully', async () => {
      mockLocalStorage.removeItem.mockImplementation(() => {
        throw new Error('Storage error')
      })

      // Set up session first
      await sessionService.createSession({
        userId: 'user123',
        rememberMe: false,
        userAgent: 'Mozilla/5.0',
        ipAddress: '127.0.0.1'
      })

      await expect(sessionService.destroySession()).rejects.toThrow()

      expect(console.log).toHaveBeenCalledWith(
        '[Session]',
        'session_destroy_error',
        expect.objectContaining({ error: expect.stringContaining('Storage error') })
      )
    })
  })

  describe('Activity Recording', () => {
    it('should record user activity', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      sessionService.recordActivity()

      // Should not throw or error
      expect(consoleSpy).not.toHaveBeenCalled()

      consoleSpy.mockRestore()
    })
  })

  describe('Time to Expiry', () => {
    it('should return correct time to expiry', async () => {
      const mockSession: SessionMetadata = {
        sessionId: '1234567890-abcdef0123456789',
        userId: 'user123',
        userAgent: 'Mozilla/5.0',
        ipAddress: '127.0.0.1',
        startTime: new Date().toISOString(),
        lastActivity: new Date().toISOString(),
        expiryTime: new Date(Date.now() + 1800000).toISOString() // 30 minutes from now
      }

      // Create session to set currentSession
      await sessionService.createSession({
        userId: 'user123',
        rememberMe: false,
        userAgent: 'Mozilla/5.0',
        ipAddress: '127.0.0.1'
      })

      const timeToExpiry = sessionService.getTimeToExpiry()

      // Should be approximately 30 minutes (allowing for test execution time)
      expect(timeToExpiry).toBeGreaterThan(1790000) // 29.8 minutes
      expect(timeToExpiry).toBeLessThan(1810000) // 30.2 minutes
    })

    it('should return 0 when no session exists', () => {
      const timeToExpiry = sessionService.getTimeToExpiry()
      expect(timeToExpiry).toBe(0)
    })
  })
})