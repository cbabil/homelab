import { renderHook, act } from '@testing-library/react'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { useAuthActions } from '../useAuthActions'
import type { AuthState, User } from '@/types/auth'
import { authService } from '@/services/auth/authService'
import { sessionService } from '@/services/auth/sessionService'
import { settingsService } from '@/services/settingsService'
import { securityLogger } from '@/services/systemLogger'

vi.mock('@/services/systemLogger', () => ({
  securityLogger: { info: vi.fn(), warn: vi.fn(), error: vi.fn() }
}))

const baseAuthState: AuthState = {
  user: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,
  sessionExpiry: null,
  activity: null,
  warning: null
}

const makeUser = (overrides: Partial<User> = {}): User => ({
  id: 'user-1',
  username: 'admin',
  email: 'admin@homelab.local',
  role: 'admin',
  lastLogin: new Date().toISOString(),
  isActive: true,
  ...overrides
})
describe('useAuthActions security logging', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    const expiryTime = new Date(Date.now() + 3600000).toISOString()
    vi.mocked(settingsService.initialize).mockResolvedValue(undefined)
    vi.mocked(sessionService.createSession).mockResolvedValue({
      sessionId: 'sess-1',
      userId: 'user-1',
      userAgent: 'agent',
      ipAddress: '127.0.0.1',
      startTime: new Date().toISOString(),
      lastActivity: new Date().toISOString(),
      expiryTime
    })
    vi.mocked(sessionService.destroySession).mockResolvedValue(undefined)
    ;(sessionService as any).getCurrentSession = vi.fn(() => ({
      accessToken: 'token-123',
      sessionId: 'sess-1',
      userId: 'user-1'
    }))
  })

  it('logs successful login', async () => {
    const user = makeUser()
    vi.mocked(authService.login).mockResolvedValue({ user, token: 'token-123', expiresIn: 3600 })
    const { result } = renderHook(() => useAuthActions({
      authState: baseAuthState,
      updateAuthState: vi.fn(),
      clearAuthState: vi.fn()
    }))

    await act(async () => {
      await result.current.login({ username: 'admin', password: 'secret', rememberMe: false })
    })

    expect(securityLogger.info).toHaveBeenCalledWith('Login attempt started', {
      rememberMe: false,
      username: 'admin'
    })
    expect(securityLogger.info).toHaveBeenCalledWith('Login successful', {
      sessionExpiry: expect.any(String),
      userId: 'user-1',
      username: 'admin'
    })
  })
  it('logs failed login', async () => {
    vi.mocked(authService.login).mockRejectedValue(new Error('boom'))
    const { result } = renderHook(() => useAuthActions({
      authState: baseAuthState,
      updateAuthState: vi.fn(),
      clearAuthState: vi.fn()
    }))

    await expect(
      result.current.login({ username: 'admin', password: 'bad', rememberMe: false })
    ).rejects.toThrow('Invalid username or password')

    expect(securityLogger.warn).toHaveBeenCalledWith('Login failed', {
      reason: 'boom',
      username: 'admin'
    })
  })
  it('logs logout completion', async () => {
    vi.mocked(authService.logout).mockResolvedValue(undefined)
    const authState: AuthState = {
      ...baseAuthState,
      user: makeUser(),
      isAuthenticated: true
    }
    const { result } = renderHook(() => useAuthActions({
      authState,
      updateAuthState: vi.fn(),
      clearAuthState: vi.fn()
    }))

    await act(async () => {
      await result.current.logout()
    })

    expect(securityLogger.info).toHaveBeenCalledWith('Logout initiated', {
      username: 'admin'
    })
    expect(securityLogger.info).toHaveBeenCalledWith('Logout completed', {
      hadToken: true,
      username: 'admin'
    })
  })
})
