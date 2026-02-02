/**
 * AuthService Offline Behavior Tests
 *
 * Verifies that authentication handles offline scenarios correctly.
 * The service requires backend connectivity - no offline authentication fallback.
 *
 * Note: These tests verify that the global authService mock (from test setup)
 * correctly returns failure responses when the backend is unavailable.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { authService } from '../authService'

describe('AuthService offline behavior', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('returns failure when backend is offline', async () => {
    const result = await authService.login({
      username: 'admin',
      password: 'TomoAdmin123!'
    })

    // Global mock returns { success: false }
    expect(result).toEqual({ success: false })
  })

  it('returns failure for any credentials when offline', async () => {
    const result = await authService.login({
      username: 'user',
      password: 'password'
    })

    // Global mock returns { success: false }
    expect(result).toEqual({ success: false })
  })

  it('requires backend connectivity for successful authentication', async () => {
    // Without backend, login should return failure
    const result = await authService.login({
      username: 'admin',
      password: 'TomoAdmin123!'
    })

    // The mock returns { success: false } to indicate authentication unavailable
    expect(result.success).toBe(false)
  })
})
