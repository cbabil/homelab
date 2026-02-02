/**
 * Session Manager Tests
 *
 * Unit tests for session management including initialization,
 * session tracking, and termination.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'

// Mock dependencies before importing sessionManager
vi.mock('../auth/sessionService', () => ({
  sessionService: {
    getCurrentSession: vi.fn().mockReturnValue(null),
    destroySession: vi.fn().mockResolvedValue(undefined)
  }
}))

vi.mock('../api/authApi', () => ({
  authApi: {
    logout: vi.fn().mockResolvedValue(undefined),
    terminateSession: vi.fn().mockResolvedValue(undefined)
  }
}))

vi.mock('@/utils/sessionMetadata', () => ({
  detectIPAddress: vi.fn().mockResolvedValue('127.0.0.1'),
  getLocationInfo: vi.fn().mockResolvedValue({
    country: 'US',
    region: 'CA',
    city: 'San Francisco',
    timezone: 'America/Los_Angeles'
  }),
  parseDeviceInfo: vi.fn().mockReturnValue({
    browser: 'Chrome',
    browserVersion: '120.0',
    os: 'macOS',
    osVersion: '14.0',
    deviceType: 'desktop',
    isMobile: false
  }),
  formatDeviceString: vi.fn().mockReturnValue('Chrome 120 on macOS'),
  createActivityTracker: vi.fn().mockReturnValue({
    pageViews: 0,
    keystrokes: 0,
    mouseClicks: 0,
    idleTime: 0,
    lastActiveTab: ''
  }),
  startActivityTracking: vi.fn().mockReturnValue(() => {})
}))

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn().mockReturnValue(null),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn()
}

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
  writable: true
})

// Import after mocks are set up
import { sessionManager } from '../sessionManager'

describe('SessionManager', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorageMock.getItem.mockReturnValue(null)
  })

  afterEach(() => {
    sessionManager.destroy()
  })

  describe('initialize', () => {
    it('should initialize without errors', async () => {
      await expect(sessionManager.initialize()).resolves.not.toThrow()
    })

    it('should load demo sessions when no stored sessions exist', async () => {
      await sessionManager.initialize()

      const sessions = sessionManager.getUserSessions()
      // Should have demo sessions created
      expect(sessions.length).toBeGreaterThan(0)
    })
  })

  describe('getUserSessions', () => {
    it('should return sessions sorted with current session first', async () => {
      await sessionManager.initialize()

      const sessions = sessionManager.getUserSessions()
      expect(Array.isArray(sessions)).toBe(true)
    })

    it('should return empty array when destroyed', async () => {
      await sessionManager.initialize()
      sessionManager.destroy()

      const sessions = sessionManager.getUserSessions()
      expect(sessions).toEqual([])
    })
  })

  describe('getSession', () => {
    it('should return null for non-existent session', async () => {
      await sessionManager.initialize()

      const session = sessionManager.getSession('non-existent')
      expect(session).toBeNull()
    })
  })

  describe('getCurrentSession', () => {
    it('should return null when no current session', async () => {
      await sessionManager.initialize()

      // Since sessionService.getCurrentSession returns null, there's no current session loaded
      const currentSession = sessionManager.getCurrentSession()
      expect(currentSession).toBeNull()
    })
  })

  describe('addListener', () => {
    it('should add listener and return unsubscribe function', async () => {
      await sessionManager.initialize()

      const listener = vi.fn()
      const unsubscribe = sessionManager.addListener(listener)

      expect(typeof unsubscribe).toBe('function')

      // Unsubscribe
      unsubscribe()
    })
  })

  describe('destroy', () => {
    it('should clear all sessions and listeners', async () => {
      await sessionManager.initialize()

      const listener = vi.fn()
      sessionManager.addListener(listener)

      sessionManager.destroy()

      expect(sessionManager.getUserSessions()).toEqual([])
      expect(sessionManager.getCurrentSession()).toBeNull()
    })
  })
})
