/**
 * Cookie Utilities Tests
 *
 * Comprehensive test suite for secure cookie management functionality.
 * Tests security configurations, validation, and edge cases.
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { cookieUtils, CookieOptions, DEFAULT_SESSION_CONFIG } from '../cookieUtils'

// Mock document.cookie
let mockCookie = ''
Object.defineProperty(document, 'cookie', {
  get: () => mockCookie,
  set: (value) => { mockCookie = value },
  configurable: true
})

// Mock crypto.getRandomValues
Object.defineProperty(global, 'crypto', {
  value: {
    getRandomValues: vi.fn((arr) => {
      for (let i = 0; i < arr.length; i++) {
        arr[i] = Math.floor(Math.random() * 256)
      }
      return arr
    })
  }
})

// Mock location for secure context testing
const mockLocation = {
  protocol: 'https:',
  hostname: 'tomo.local'
}

Object.defineProperty(window, 'location', {
  value: mockLocation,
  writable: true
})

describe('CookieUtils', () => {
  beforeEach(() => {
    mockCookie = ''
    vi.clearAllMocks()
  })

  afterEach(() => {
    mockCookie = ''
  })

  describe('Cookie Configuration', () => {
    it('should have secure default configuration', () => {
      expect(DEFAULT_SESSION_CONFIG.name).toBe('tomo_session')
      expect(DEFAULT_SESSION_CONFIG.options.httpOnly).toBe(true)
      expect(DEFAULT_SESSION_CONFIG.options.secure).toBe(true)
      expect(DEFAULT_SESSION_CONFIG.options.sameSite).toBe('strict')
      expect(DEFAULT_SESSION_CONFIG.options.path).toBe('/')
    })

    it('should detect secure context correctly', () => {
      // Test HTTPS
      mockLocation.protocol = 'https:'
      mockLocation.hostname = 'tomo.local'

      // Create a new instance to test different contexts
      type CookieUtilsConstructor = new () => typeof cookieUtils
      const httpsUtils = new (cookieUtils.constructor as unknown as CookieUtilsConstructor)()
      const httpsConfig = (httpsUtils as typeof cookieUtils)['buildCookieConfig']({})
      expect(httpsConfig.secure).toBe(true)

      // Test localhost - should also be secure
      mockLocation.protocol = 'http:'
      mockLocation.hostname = 'localhost'
      const localhostUtils = new (cookieUtils.constructor as unknown as CookieUtilsConstructor)()
      const localhostConfig = (localhostUtils as typeof cookieUtils)['buildCookieConfig']({})
      expect(localhostConfig.secure).toBe(true)

      // Test insecure context - returns false for non-localhost HTTP
      mockLocation.protocol = 'http:'
      mockLocation.hostname = 'insecure.com'
      const insecureUtils = new (cookieUtils.constructor as unknown as CookieUtilsConstructor)()
      const insecureConfig = (insecureUtils as typeof cookieUtils)['buildCookieConfig']({})
      // Insecure context should return secure=false
      expect(insecureConfig.secure).toBe(false)
    })
  })

  describe('Cookie Operations', () => {
    it('should set cookie with security attributes', () => {
      cookieUtils.setSessionCookie('test_cookie', 'test_value', {
        httpOnly: false, // Allow for testing
        secure: false,
        maxAge: 3600000
      })

      // Cookie should be set (httpOnly=false allows browser-side setting)
      expect(mockCookie).toContain('test_cookie=test_value')
    })

    it('should get cookie value correctly', () => {
      mockCookie = 'test_cookie=test_value; path=/'

      const value = cookieUtils.getCookie('test_cookie')
      expect(value).toBe('test_value')
    })

    it('should return null for non-existent cookie', () => {
      const value = cookieUtils.getCookie('non_existent')
      expect(value).toBeNull()
    })

    it('should delete cookie by setting expiration', () => {
      mockCookie = 'test_cookie=value'

      cookieUtils.deleteCookie('test_cookie')

      // Should set expired cookie
      expect(mockCookie).toContain('expires=Thu, 01 Jan 1970 00:00:00 GMT')
    })
  })

  describe('Security Validation', () => {
    it('should validate secure cookie configuration', () => {
      const secureConfig: CookieOptions = {
        httpOnly: true,
        secure: true,
        sameSite: 'strict'
      }

      const isValid = cookieUtils.validateCookieConfig(secureConfig)
      expect(isValid).toBe(true)
    })

    it('should reject insecure cookie configuration', () => {
      const insecureConfig: CookieOptions = {
        httpOnly: false,
        secure: false,
        sameSite: 'lax'
      }

      const isValid = cookieUtils.validateCookieConfig(insecureConfig)
      expect(isValid).toBe(false)
    })

    it('should identify security issues in configuration', () => {
      const config: CookieOptions = { httpOnly: false }
      const isValid = cookieUtils.validateCookieConfig(config)
      expect(isValid).toBe(false)
    })
  })

  describe('Session ID Generation', () => {
    it('should generate unique session IDs', () => {
      const id1 = cookieUtils.generateSessionId()
      const id2 = cookieUtils.generateSessionId()

      expect(id1).not.toBe(id2)
      expect(id1).toMatch(/^\w+-[0-9a-f]+$/)
      expect(id2).toMatch(/^\w+-[0-9a-f]+$/)
    })

    it('should generate session IDs with correct format', () => {
      const sessionId = cookieUtils.generateSessionId()
      const parts = sessionId.split('-')

      expect(parts).toHaveLength(2)
      expect(parts[0]).toBeTruthy() // timestamp part
      expect(parts[1]).toBeTruthy() // random part
      expect(parts[1]).toHaveLength(32) // 16 bytes = 32 hex chars
    })

    it('should use crypto.getRandomValues for security', () => {
      cookieUtils.generateSessionId()
      expect(crypto.getRandomValues).toHaveBeenCalledWith(expect.any(Uint8Array))
    })
  })

  describe('Error Handling', () => {
    it('should handle cookie setting errors gracefully', () => {
      // Mock document.cookie to throw an error
      const originalDescriptor = Object.getOwnPropertyDescriptor(document, 'cookie')
      Object.defineProperty(document, 'cookie', {
        get: () => mockCookie,
        set: () => {
          throw new Error('Cookie error')
        },
        configurable: true
      })

      expect(() => {
        cookieUtils.setSessionCookie('error_cookie', 'value', { httpOnly: false })
      }).toThrow('Failed to set cookie error_cookie: Error: Cookie error')

      // Restore original descriptor
      if (originalDescriptor) {
        Object.defineProperty(document, 'cookie', originalDescriptor)
      }
    })

    it('should handle cookie getting errors gracefully', () => {
      // Mock document.cookie to throw an error
      const originalDescriptor = Object.getOwnPropertyDescriptor(document, 'cookie')
      Object.defineProperty(document, 'cookie', {
        get: () => {
          throw new Error('Cookie read error')
        },
        set: () => {},
        configurable: true
      })

      const value = cookieUtils.getCookie('error_cookie')
      expect(value).toBeNull()

      // Restore original descriptor
      if (originalDescriptor) {
        Object.defineProperty(document, 'cookie', originalDescriptor)
      }
    })

    it('should handle cookie deletion errors gracefully', () => {
      // Mock document.cookie to throw an error on set
      const originalDescriptor = Object.getOwnPropertyDescriptor(document, 'cookie')
      Object.defineProperty(document, 'cookie', {
        get: () => mockCookie,
        set: () => {
          throw new Error('Cookie delete error')
        },
        configurable: true
      })

      // Should not throw - errors are handled internally
      expect(() => cookieUtils.deleteCookie('error_cookie')).not.toThrow()

      // Restore original descriptor
      if (originalDescriptor) {
        Object.defineProperty(document, 'cookie', originalDescriptor)
      }
    })
  })

  describe('Cookie String Formatting', () => {
    it('should format cookie string with all attributes', () => {
      const options: CookieOptions = {
        maxAge: 3600000,
        path: '/test',
        domain: 'tomo.local',
        secure: true,
        sameSite: 'strict'
      }

      const formatted = cookieUtils['formatCookieString']('test', 'value', options)

      expect(formatted).toContain('test=value')
      expect(formatted).toContain('path=/test')
      expect(formatted).toContain('domain=tomo.local')
      expect(formatted).toContain('secure')
      expect(formatted).toContain('samesite=strict')
    })

    it('should handle negative maxAge for deletion', () => {
      const options: CookieOptions = { maxAge: -1 }

      const formatted = cookieUtils['formatCookieString']('test', '', options)

      expect(formatted).toContain('expires=Thu, 01 Jan 1970 00:00:00 GMT')
    })

    it('should encode cookie values', () => {
      const specialValue = 'value with spaces & symbols!'
      const formatted = cookieUtils['formatCookieString']('test', specialValue, {})

      expect(formatted).toContain(encodeURIComponent(specialValue))
    })
  })

  describe('Security Logging', () => {
    it('should have logSecurityEvent method for monitoring', () => {
      // The method exists but logging is disabled in production
      // Verify the method can be called without errors
      expect(() => {
        cookieUtils['logSecurityEvent']('test_event', { test: 'data' })
      }).not.toThrow()
    })
  })
})
