import { renderHook, act } from '@testing-library/react'
import { describe, it, expect, beforeEach, vi, Mock } from 'vitest'
import { useAuthActions } from '../useAuthActions'
import type { AuthState, User } from '@/types/auth'
import { authService } from '@/services/auth/authService'
import { sessionService } from '@/services/auth/sessionService'
import { settingsService } from '@/services/settingsService'
import { securityLogger } from '@/services/systemLogger'

// Extended mock type for sessionService with getCurrentSession
type MockedSessionService = typeof sessionService & { getCurrentSession: Mock }

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
  email: 'admin@tomo.local',
  role: 'admin',
  lastLogin: new Date().toISOString(),
  isActive: true,
  ...overrides
})
describe('useAuthActions security logging', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    const expiryTime = new Date(Date.now() + 3600000).toISOString()

    const mockSettings = {
      security: {
        session: {
          timeout: '1h' as const,
          idleDetection: true,
          showWarningMinutes: 5,
          extendOnActivity: true
        },
        requirePasswordChange: false,
        passwordChangeInterval: 90,
        twoFactorEnabled: false
      },
      ui: {
        theme: 'dark' as const,
        language: 'en',
        timezone: 'UTC',
        notifications: true,
        compactMode: false,
        sidebarCollapsed: false
      },
      system: {
        autoRefresh: true,
        refreshInterval: 30,
        maxLogEntries: 1000,
        enableDebugMode: false,
        dataRetention: {
          logRetentionDays: 30,
          otherDataRetentionDays: 90,
          lastCleanupDate: undefined
        }
      },
      applications: {
        autoRefreshStatus: true,
        statusRefreshInterval: 0
      },
      notifications: {
        serverAlerts: true,
        resourceAlerts: true,
        updateAlerts: false
      },
      servers: {
        connectionTimeout: 30,
        retryCount: 3,
        autoRetry: true
      },
      agent: {
        preferAgent: true,
        autoUpdate: true,
        heartbeatInterval: 30,
        heartbeatTimeout: 90,
        commandTimeout: 120
      },
      lastUpdated: new Date().toISOString(),
      version: 1
    }

    vi.mocked(settingsService.initialize).mockResolvedValue(mockSettings)
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
    ;(sessionService as MockedSessionService).getCurrentSession = vi.fn(() => ({
      accessToken: 'token-123',
      sessionId: 'sess-1',
      userId: 'user-1',
      userAgent: 'test-agent',
      ipAddress: '127.0.0.1',
      startTime: new Date().toISOString(),
      lastActivity: new Date().toISOString(),
      expiryTime: new Date(Date.now() + 3600000).toISOString()
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
    ).rejects.toThrow('boom')

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
