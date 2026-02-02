/**
 * Cache Utils Tests
 *
 * Unit tests for cache clearing functionality.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { clearTomoCaches } from '../cacheUtils'
import { SETTINGS_STORAGE_KEYS } from '@/types/settings'

// Mock systemLogger
vi.mock('@/services/systemLogger', () => ({
  systemLogger: {
    clearLogs: vi.fn()
  }
}))

// Mock authStorageHelpers
vi.mock('@/hooks/authStorageHelpers', () => ({
  clearStoredAuth: vi.fn()
}))

const LOG_STORAGE_KEY = 'tomo-system-logs'
const SESSION_MANAGER_STORAGE_KEY = 'sessionManager_sessions'

describe('cacheUtils', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    sessionStorage.clear()
  })

  afterEach(() => {
    localStorage.clear()
    sessionStorage.clear()
  })

  describe('clearTomoCaches', () => {
    it('should clear system logs from localStorage', () => {
      localStorage.setItem(LOG_STORAGE_KEY, JSON.stringify([{ message: 'test log' }]))

      clearTomoCaches()

      expect(localStorage.getItem(LOG_STORAGE_KEY)).toBeNull()
    })

    it('should clear settings cache', () => {
      // Set up settings data
      Object.values(SETTINGS_STORAGE_KEYS).forEach((key) => {
        localStorage.setItem(key, 'test-value')
      })

      clearTomoCaches()

      // Verify all settings keys are cleared
      Object.values(SETTINGS_STORAGE_KEYS).forEach((key) => {
        expect(localStorage.getItem(key)).toBeNull()
      })
    })

    it('should clear session manager cache', () => {
      localStorage.setItem(SESSION_MANAGER_STORAGE_KEY, JSON.stringify({ sessions: [] }))

      clearTomoCaches()

      expect(localStorage.getItem(SESSION_MANAGER_STORAGE_KEY)).toBeNull()
    })

    it('should call systemLogger.clearLogs', async () => {
      const { systemLogger } = await import('@/services/systemLogger')

      clearTomoCaches()

      expect(systemLogger.clearLogs).toHaveBeenCalled()
    })

    it('should call clearStoredAuth', async () => {
      const { clearStoredAuth } = await import('@/hooks/authStorageHelpers')

      clearTomoCaches()

      expect(clearStoredAuth).toHaveBeenCalled()
    })

    it('should handle errors gracefully without throwing', () => {
      // Mock localStorage.removeItem to throw an error
      const originalRemoveItem = localStorage.removeItem
      localStorage.removeItem = vi.fn().mockImplementation(() => {
        throw new Error('Storage error')
      })

      // Should not throw
      expect(() => clearTomoCaches()).not.toThrow()

      // Restore
      localStorage.removeItem = originalRemoveItem
    })

    it('should clear all tomo-related cache keys', () => {
      // Set up various cache data
      localStorage.setItem(LOG_STORAGE_KEY, 'logs')
      localStorage.setItem(SESSION_MANAGER_STORAGE_KEY, 'sessions')
      Object.values(SETTINGS_STORAGE_KEYS).forEach((key) => {
        localStorage.setItem(key, 'setting')
      })

      clearTomoCaches()

      // Verify core tomo keys are cleared
      expect(localStorage.getItem(LOG_STORAGE_KEY)).toBeNull()
      expect(localStorage.getItem(SESSION_MANAGER_STORAGE_KEY)).toBeNull()
    })

    it('should not affect non-tomo localStorage keys', () => {
      // Set up non-tomo data
      localStorage.setItem('other-app-key', 'other-data')
      localStorage.setItem('user-preferences', 'preferences')

      clearTomoCaches()

      // Non-tomo keys should remain
      expect(localStorage.getItem('other-app-key')).toBe('other-data')
      expect(localStorage.getItem('user-preferences')).toBe('preferences')
    })

    it('should continue clearing other caches if one fails', async () => {
      const { systemLogger } = await import('@/services/systemLogger')
      vi.mocked(systemLogger.clearLogs).mockImplementation(() => {
        throw new Error('Logger error')
      })

      localStorage.setItem(SESSION_MANAGER_STORAGE_KEY, 'sessions')

      // Should not throw and should still clear other caches
      expect(() => clearTomoCaches()).not.toThrow()
      expect(localStorage.getItem(SESSION_MANAGER_STORAGE_KEY)).toBeNull()
    })
  })
})
