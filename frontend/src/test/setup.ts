/**
 * Vitest Test Setup
 *
 * Global test configuration and utilities.
 * Includes DOM testing library setup and custom matchers.
 */

import '@testing-library/jest-dom'
import { cleanup } from '@testing-library/react'
import { afterEach, beforeAll, afterAll, vi } from 'vitest'
import { server } from './mocks/server'
import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import enTranslations from '../i18n/locales/en.json'

// Initialize i18n for tests with actual translations
i18n
  .use(initReactI18next)
  .init({
    lng: 'en',
    fallbackLng: 'en',
    ns: ['translation'],
    defaultNS: 'translation',
    interpolation: {
      escapeValue: false
    },
    resources: {
      en: {
        translation: enTranslations
      }
    }
  })

// Mock authentication services globally
vi.mock('@/services/settingsService', () => ({
  settingsService: {
    initialize: vi.fn().mockResolvedValue(undefined),
    getSettings: vi.fn().mockReturnValue({
      security: {
        session: {
          timeout: 60,
          showWarningMinutes: 5
        }
      }
    }),
    updateSettings: vi.fn().mockResolvedValue(undefined),
    getSessionTimeoutMs: vi.fn().mockReturnValue(3600000)
  }
}))

vi.mock('@/services/auth/sessionService', () => ({
  sessionService: {
    initialize: vi.fn().mockResolvedValue(undefined),
    validateSession: vi.fn().mockResolvedValue({
      isValid: false,
      metadata: null
    }),
    createSession: vi.fn().mockResolvedValue({
      sessionId: 'test-session-id',
      userId: 'test-user',
      userAgent: 'Test Agent',
      ipAddress: '127.0.0.1',
      startTime: new Date().toISOString(),
      lastActivity: new Date().toISOString(),
      expiryTime: new Date(Date.now() + 3600000).toISOString()
    }),
    clearSession: vi.fn().mockResolvedValue(undefined),
    destroySession: vi.fn().mockResolvedValue(undefined),
    refreshSession: vi.fn().mockResolvedValue({ success: false }),
    renewSession: vi.fn().mockResolvedValue({ success: false }),
    getCurrentSession: vi.fn().mockReturnValue(null),
    getSessionMetadata: vi.fn().mockReturnValue(null),
    isSessionValid: vi.fn().mockReturnValue(false),
    getTimeToExpiry: vi.fn().mockReturnValue(3600000),
    recordActivity: vi.fn()
  }
}))

vi.mock('@/services/auth/authService', () => ({
  authService: {
    login: vi.fn().mockResolvedValue({ success: false }),
    logout: vi.fn().mockResolvedValue(undefined),
    validateToken: vi.fn().mockResolvedValue(false)
  }
}))

vi.mock('@/services/mcpClient', () => ({
  TomoMCPClient: vi.fn().mockImplementation(() => ({
    connect: vi.fn().mockResolvedValue(undefined),
    disconnect: vi.fn().mockResolvedValue(undefined),
    isConnected: vi.fn().mockReturnValue(false)
  }))
}))

// Establish API mocking before all tests
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))

// Reset any request handlers that we may add during the tests
afterEach(() => {
  server.resetHandlers()
  cleanup()
})

// Clean up after the tests are finished
afterAll(() => server.close())

// Mock window.matchMedia for responsive component tests
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => {}
  })
})

// Mock IntersectionObserver for component visibility tests
global.IntersectionObserver = class IntersectionObserver {
  root = null
  rootMargin = ''
  thresholds: readonly number[] = []

  constructor(_callback: IntersectionObserverCallback, _options?: IntersectionObserverInit) {}
  observe() { return null }
  disconnect() { return null }
  unobserve() { return null }
  takeRecords(): IntersectionObserverEntry[] { return [] }
} as unknown as typeof IntersectionObserver

// Mock IndexedDB for authentication services
type EventListener = (event: { type: string }) => void

class MockIDBRequest {
  result: unknown = null
  error: unknown = null
  readyState: string = 'pending'
  private listeners: { [key: string]: EventListener[] } = {}

  addEventListener(type: string, listener: EventListener) {
    if (!this.listeners[type]) this.listeners[type] = []
    this.listeners[type].push(listener)
  }

  removeEventListener(type: string, listener: EventListener) {
    if (this.listeners[type]) {
      this.listeners[type] = this.listeners[type].filter(l => l !== listener)
    }
  }

  dispatchEvent(event: { type: string }) {
    if (this.listeners[event.type]) {
      this.listeners[event.type].forEach(listener => listener(event))
    }
  }

  succeed(result: unknown) {
    this.result = result
    this.readyState = 'done'
    setTimeout(() => this.dispatchEvent({ type: 'success' }), 0)
  }

  fail(error: unknown) {
    this.error = error
    this.readyState = 'done'
    setTimeout(() => this.dispatchEvent({ type: 'error' }), 0)
  }
}

class MockIDBDatabase {
  createObjectStore() {
    return {
      createIndex: () => {}
    }
  }

  transaction() {
    return {
      objectStore: () => ({
        add: () => {
          const req = new MockIDBRequest()
          req.succeed(undefined)
          return req
        },
        put: () => {
          const req = new MockIDBRequest()
          req.succeed(undefined)
          return req
        },
        get: () => {
          const req = new MockIDBRequest()
          req.succeed(undefined)
          return req
        },
        delete: () => {
          const req = new MockIDBRequest()
          req.succeed(undefined)
          return req
        },
        clear: () => {
          const req = new MockIDBRequest()
          req.succeed(undefined)
          return req
        },
        index: () => ({
          get: () => {
            const req = new MockIDBRequest()
            req.succeed(undefined)
            return req
          }
        })
      })
    }
  }
}

const indexedDBMock = {
  open: () => {
    const req = new MockIDBRequest()
    req.succeed(new MockIDBDatabase())
    return req
  }
}

Object.defineProperty(global, 'indexedDB', {
  writable: true,
  value: indexedDBMock
})

// Mock crypto.subtle for JWT operations
if (!global.crypto) {
  Object.defineProperty(global, 'crypto', {
    writable: true,
    value: {
      subtle: {
        generateKey: () => Promise.resolve({ extractable: true }),
        exportKey: () => Promise.resolve(new ArrayBuffer(32)),
        importKey: () => Promise.resolve({}),
        sign: () => Promise.resolve(new ArrayBuffer(32)),
        verify: () => Promise.resolve(true),
        encrypt: () => Promise.resolve(new ArrayBuffer(32)),
        decrypt: () => Promise.resolve(new ArrayBuffer(32))
      },
      getRandomValues: <T extends ArrayBufferView | null>(arr: T): T => {
        if (arr && 'length' in arr) {
          for (let i = 0; i < (arr as unknown as ArrayLike<number>).length; i++) {
            (arr as unknown as number[])[i] = Math.floor(Math.random() * 256)
          }
        }
        return arr
      }
    }
  })
}