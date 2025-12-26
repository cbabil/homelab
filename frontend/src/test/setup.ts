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

// Mock authentication services globally
vi.mock('@/services/settingsService', () => ({
  settingsService: {
    initialize: vi.fn().mockResolvedValue(undefined),
    getSettings: vi.fn().mockReturnValue({}),
    updateSettings: vi.fn().mockResolvedValue(undefined)
  }
}))

vi.mock('@/services/auth/sessionService', () => ({
  sessionService: {
    validateSession: vi.fn().mockResolvedValue({
      isValid: false,
      metadata: null
    }),
    createSession: vi.fn().mockResolvedValue(undefined),
    clearSession: vi.fn().mockResolvedValue(undefined),
    destroySession: vi.fn().mockResolvedValue(undefined),
    refreshSession: vi.fn().mockResolvedValue({ success: false }),
    renewSession: vi.fn().mockResolvedValue({ success: false })
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
  HomelabMCPClient: vi.fn().mockImplementation(() => ({
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
  thresholds = []

  constructor() {}
  observe() { return null }
  disconnect() { return null }
  unobserve() { return null }
  takeRecords() { return [] }
} as any

// Mock IndexedDB for authentication services
class MockIDBRequest {
  result: any = null
  error: any = null
  readyState: string = 'pending'
  private listeners: { [key: string]: Function[] } = {}

  addEventListener(type: string, listener: Function) {
    if (!this.listeners[type]) this.listeners[type] = []
    this.listeners[type].push(listener)
  }

  removeEventListener(type: string, listener: Function) {
    if (this.listeners[type]) {
      this.listeners[type] = this.listeners[type].filter(l => l !== listener)
    }
  }

  dispatchEvent(event: { type: string }) {
    if (this.listeners[event.type]) {
      this.listeners[event.type].forEach(listener => listener(event))
    }
  }

  succeed(result: any) {
    this.result = result
    this.readyState = 'done'
    setTimeout(() => this.dispatchEvent({ type: 'success' }), 0)
  }

  fail(error: any) {
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
      getRandomValues: (arr: any) => {
        for (let i = 0; i < arr.length; i++) {
          arr[i] = Math.floor(Math.random() * 256)
        }
        return arr
      }
    }
  })
}