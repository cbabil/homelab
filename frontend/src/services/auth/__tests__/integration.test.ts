/**
 * Authentication Integration Tests
 *
 * Tests to verify authentication system behavior using mocked services.
 * Uses global mocks from test/setup.ts for consistent test environment.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { settingsService } from '../../settingsService'
import { sessionService } from '../sessionService'

describe('Authentication Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Settings Integration', () => {
    it('should use session timeout from settings service', () => {
      const timeoutMs = settingsService.getSessionTimeoutMs()
      expect(timeoutMs).toBeGreaterThan(0)
      expect(typeof timeoutMs).toBe('number')
    })

    it('should respect settings for session warning timing', () => {
      const settings = settingsService.getSettings()
      expect(settings.security.session.showWarningMinutes).toBeGreaterThan(0)
      expect(settings.security.session.showWarningMinutes).toBeLessThanOrEqual(30)
    })

    it('should create session with proper structure', async () => {
      const mockOptions = {
        userId: 'test-user',
        rememberMe: false,
        userAgent: 'Test Agent',
        ipAddress: '127.0.0.1'
      }

      const session = await sessionService.createSession(mockOptions)

      expect(session).toBeDefined()
      expect(session.sessionId).toBeDefined()
      expect(session.expiryTime).toBeDefined()
      expect(sessionService.createSession).toHaveBeenCalledWith(mockOptions)
    })
  })

  describe('Session Service', () => {
    it('should provide time to expiry', () => {
      const timeToExpiry = sessionService.getTimeToExpiry()
      expect(typeof timeToExpiry).toBe('number')
      expect(timeToExpiry).toBeGreaterThanOrEqual(0)
    })

    it('should allow recording activity', () => {
      sessionService.recordActivity()
      expect(sessionService.recordActivity).toHaveBeenCalled()
    })

    it('should validate session', async () => {
      const result = await sessionService.validateSession()
      expect(result).toHaveProperty('isValid')
      expect(sessionService.validateSession).toHaveBeenCalled()
    })

    it('should get current session', () => {
      const session = sessionService.getCurrentSession()
      // Mock returns null by default
      expect(session).toBeNull()
      expect(sessionService.getCurrentSession).toHaveBeenCalled()
    })

    it('should destroy session', async () => {
      await sessionService.destroySession()
      expect(sessionService.destroySession).toHaveBeenCalled()
    })

    it('should renew session', async () => {
      await sessionService.renewSession()
      expect(sessionService.renewSession).toHaveBeenCalled()
    })
  })

  describe('Service Initialization', () => {
    it('should initialize settings service', async () => {
      await settingsService.initialize()
      expect(settingsService.initialize).toHaveBeenCalled()
    })

    it('should initialize session service', async () => {
      await sessionService.initialize()
      expect(sessionService.initialize).toHaveBeenCalled()
    })
  })
})
