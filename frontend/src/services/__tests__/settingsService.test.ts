/**
 * Settings Service Tests
 * 
 * Unit tests for settings service functionality including
 * initialization, updates, validation, and persistence.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { settingsService } from '../settingsService'
import { DEFAULT_SETTINGS, SETTINGS_STORAGE_KEYS } from '@/types/settings'

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

describe('SettingsService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    localStorageMock.clear()
  })

  describe('initialize', () => {
    it('should return default settings when no stored settings exist', async () => {
      localStorageMock.getItem.mockReturnValue(null)
      
      const settings = await settingsService.initialize()
      
      expect(settings).toEqual(expect.objectContaining({
        security: expect.objectContaining({
          session: expect.objectContaining({
            timeout: '1h',
            idleDetection: true
          })
        }),
        version: 1
      }))
      
      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        SETTINGS_STORAGE_KEYS.USER_SETTINGS,
        expect.stringContaining('"timeout":"1h"')
      )
    })

    it('should load valid stored settings', async () => {
      const storedSettings = {
        ...DEFAULT_SETTINGS,
        security: {
          ...DEFAULT_SETTINGS.security,
          session: {
            ...DEFAULT_SETTINGS.security.session,
            timeout: '4h'
          }
        }
      }
      
      localStorageMock.getItem.mockReturnValue(JSON.stringify(storedSettings))
      
      const settings = await settingsService.initialize()
      
      expect(settings.security.session.timeout).toBe('4h')
      expect(localStorageMock.setItem).not.toHaveBeenCalled()
    })

    it('should fall back to defaults for invalid stored settings', async () => {
      localStorageMock.getItem.mockReturnValue('invalid-json')
      
      const settings = await settingsService.initialize()
      
      expect(settings).toEqual(expect.objectContaining(DEFAULT_SETTINGS))
    })
  })

  describe('getSettings', () => {
    it('should return current settings after initialization', async () => {
      await settingsService.initialize()
      
      const settings = settingsService.getSettings()
      
      expect(settings).toBeDefined()
      expect(settings.version).toBe(1)
    })

    it('should throw error if not initialized', () => {
      // Reset service state
      settingsService['settings'] = null
      
      expect(() => settingsService.getSettings()).toThrow(
        'Settings not initialized. Call initialize() first.'
      )
    })
  })

  describe('updateSettings', () => {
    beforeEach(async () => {
      await settingsService.initialize()
    })

    it('should update security settings successfully', async () => {
      const result = await settingsService.updateSettings('security', {
        session: {
          timeout: '4h',
          idleDetection: false,
          showWarningMinutes: 10,
          extendOnActivity: false
        }
      })
      
      expect(result.success).toBe(true)
      expect(result.settings?.security.session.timeout).toBe('4h')
      expect(result.settings?.security.session.idleDetection).toBe(false)
    })

    it('should validate timeout values', async () => {
      const result = await settingsService.updateSettings('security', {
        session: {
          timeout: 'invalid' as any
        }
      })
      
      expect(result.success).toBe(false)
      expect(result.error).toContain('Invalid session timeout value')
    })

    it('should update version and timestamp', async () => {
      const initialSettings = settingsService.getSettings()
      const initialVersion = initialSettings.version
      
      await settingsService.updateSettings('ui', { theme: 'light' })
      
      const updatedSettings = settingsService.getSettings()
      expect(updatedSettings.version).toBe(initialVersion + 1)
      expect(new Date(updatedSettings.lastUpdated).getTime()).toBeGreaterThan(
        new Date(initialSettings.lastUpdated).getTime()
      )
    })
  })

  describe('resetSettings', () => {
    it('should reset to default settings', async () => {
      await settingsService.initialize()
      
      // Make some changes
      await settingsService.updateSettings('ui', { theme: 'light' })
      
      const result = await settingsService.resetSettings()
      
      expect(result.success).toBe(true)
      expect(result.settings?.ui.theme).toBe('dark') // Default theme
    })
  })

  describe('getSessionTimeoutMs', () => {
    it('should return timeout in milliseconds', async () => {
      await settingsService.initialize()
      
      const timeoutMs = settingsService.getSessionTimeoutMs()
      
      expect(timeoutMs).toBe(60 * 60 * 1000) // 1 hour in ms
    })

    it('should return default timeout when not initialized', () => {
      // Reset service state
      settingsService['settings'] = null
      
      const timeoutMs = settingsService.getSessionTimeoutMs()
      
      expect(timeoutMs).toBe(60 * 60 * 1000) // Default 1 hour
    })
  })

  describe('subscribe', () => {
    it('should notify subscribers of changes', async () => {
      await settingsService.initialize()
      
      const callback = vi.fn()
      const unsubscribe = settingsService.subscribe(callback)
      
      await settingsService.updateSettings('ui', { theme: 'light' })
      
      expect(callback).toHaveBeenCalledWith(
        expect.objectContaining({
          ui: expect.objectContaining({ theme: 'light' })
        })
      )
      
      unsubscribe()
    })

    it('should handle subscription errors gracefully', async () => {
      await settingsService.initialize()
      
      const errorCallback = vi.fn(() => {
        throw new Error('Callback error')
      })
      
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      
      settingsService.subscribe(errorCallback)
      await settingsService.updateSettings('ui', { theme: 'light' })
      
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        'Settings listener error:',
        expect.any(Error)
      )
      
      consoleErrorSpy.mockRestore()
    })
  })
})