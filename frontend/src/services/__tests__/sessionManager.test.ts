/**
 * Session Manager Tests
 * 
 * Unit tests for session activity tracking, idle detection,
 * and warning calculations.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { sessionManager } from '../sessionManager'
import { settingsService } from '../settingsService'
import { AUTH_STORAGE_KEYS } from '@/types/auth'

// Mock settings service
vi.mock('../settingsService', () => ({
  settingsService: {
    getSettings: vi.fn(() => ({
      security: {
        session: {
          timeout: '1h',
          idleDetection: true,
          showWarningMinutes: 5,
          extendOnActivity: true
        }
      }
    }))
  }
}))

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn()
}

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock
})

// Mock DOM methods
Object.defineProperty(document, 'addEventListener', {
  value: vi.fn()
})

Object.defineProperty(document, 'removeEventListener', {
  value: vi.fn()
})

describe('SessionManager', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
    sessionManager.cleanup()
  })

  describe('initialize', () => {
    it('should set up activity listeners', () => {
      sessionManager.initialize()
      
      const expectedEvents = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart']
      expectedEvents.forEach(event => {
        expect(document.addEventListener).toHaveBeenCalledWith(
          event,
          expect.any(Function),
          { passive: true }
        )
      })
    })

    it('should load activity from storage', () => {
      const lastActivity = new Date().toISOString()
      localStorageMock.getItem.mockImplementation((key) => {
        if (key === AUTH_STORAGE_KEYS.LAST_ACTIVITY) return lastActivity
        if (key === AUTH_STORAGE_KEYS.ACTIVITY_COUNT) return '10'
        return null
      })
      
      sessionManager.initialize()
      
      const activity = sessionManager.getActivityState()
      expect(activity.lastActivity).toBe(lastActivity)
      expect(activity.activityCount).toBe(10)
    })
  })

  describe('recordActivity', () => {
    beforeEach(() => {
      sessionManager.initialize()
    })

    it('should update last activity and count', () => {
      const activity = sessionManager.recordActivity()
      
      expect(activity.activityCount).toBe(1)
      expect(new Date(activity.lastActivity)).toBeInstanceOf(Date)
      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        AUTH_STORAGE_KEYS.LAST_ACTIVITY,
        expect.any(String)
      )
      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        AUTH_STORAGE_KEYS.ACTIVITY_COUNT,
        '1'
      )
    })

    it('should increment activity count on subsequent calls', () => {
      sessionManager.recordActivity()
      const activity = sessionManager.recordActivity()
      
      expect(activity.activityCount).toBe(2)
    })
  })

  describe('getActivityState', () => {
    beforeEach(() => {
      sessionManager.initialize()
    })

    it('should return current activity state', () => {
      const activity = sessionManager.getActivityState()
      
      expect(activity).toEqual({
        lastActivity: expect.any(String),
        isIdle: expect.any(Boolean),
        idleDuration: expect.any(Number),
        activityCount: expect.any(Number)
      })
    })

    it('should detect idle state after 5 minutes', () => {
      // Simulate 6 minutes of inactivity
      vi.advanceTimersByTime(6 * 60 * 1000)
      
      const activity = sessionManager.getActivityState()
      
      expect(activity.isIdle).toBe(true)
      expect(activity.idleDuration).toBeGreaterThan(5 * 60 * 1000)
    })
  })

  describe('calculateWarning', () => {
    beforeEach(() => {
      sessionManager.initialize()
    })

    it('should return null for sessions with plenty of time', () => {
      const futureExpiry = new Date(Date.now() + 10 * 60 * 1000).toISOString() // 10 minutes
      
      const warning = sessionManager.calculateWarning(futureExpiry)
      
      expect(warning).toBeNull()
    })

    it('should return warning for sessions expiring within warning period', () => {
      const soonExpiry = new Date(Date.now() + 3 * 60 * 1000).toISOString() // 3 minutes
      
      const warning = sessionManager.calculateWarning(soonExpiry)
      
      expect(warning).toEqual({
        isShowing: true,
        minutesRemaining: 3,
        warningLevel: 'warning'
      })
    })

    it('should return critical warning for sessions expiring in 1 minute', () => {
      const criticalExpiry = new Date(Date.now() + 60 * 1000).toISOString() // 1 minute
      
      const warning = sessionManager.calculateWarning(criticalExpiry)
      
      expect(warning).toEqual({
        isShowing: true,
        minutesRemaining: 1,
        warningLevel: 'critical'
      })
    })

    it('should return critical warning for expired sessions', () => {
      const pastExpiry = new Date(Date.now() - 60 * 1000).toISOString() // 1 minute ago
      
      const warning = sessionManager.calculateWarning(pastExpiry)
      
      expect(warning).toEqual({
        isShowing: true,
        minutesRemaining: 0,
        warningLevel: 'critical'
      })
    })
  })

  describe('cleanup', () => {
    it('should remove event listeners', () => {
      sessionManager.initialize()
      sessionManager.cleanup()
      
      const expectedEvents = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart']
      expectedEvents.forEach(event => {
        expect(document.removeEventListener).toHaveBeenCalledWith(
          event,
          expect.any(Function)
        )
      })
    })

    it('should clear timers', () => {
      sessionManager.initialize()
      
      const clearTimeoutSpy = vi.spyOn(global, 'clearTimeout')
      
      sessionManager.cleanup()
      
      expect(clearTimeoutSpy).toHaveBeenCalled()
    })
  })
})