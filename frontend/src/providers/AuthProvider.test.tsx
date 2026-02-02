/**
 * AuthProvider Test Suite
 *
 * Comprehensive tests for authentication provider including login/logout,
 * session persistence, token validation, and error handling.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { userEvent } from '@testing-library/user-event'
import { AuthProvider, useAuth } from './AuthProvider'
import { authService } from '@/services/auth/authService'
import { sessionService } from '@/services/auth/sessionService'

// Mock the auth services for this test file
vi.mock('@/services/auth/authService', () => ({
  authService: {
    login: vi.fn(),
    logout: vi.fn().mockResolvedValue(undefined),
    validateToken: vi.fn().mockResolvedValue(false),
    register: vi.fn()
  }
}))

vi.mock('@/services/auth/sessionService', () => ({
  sessionService: {
    validateSession: vi.fn().mockResolvedValue({ isValid: false, metadata: null }),
    createSession: vi.fn(),
    clearSession: vi.fn().mockResolvedValue(undefined),
    destroySession: vi.fn().mockResolvedValue(undefined),
    refreshSession: vi.fn().mockResolvedValue({ success: false }),
    renewSession: vi.fn().mockResolvedValue({ success: false }),
    getCurrentSession: vi.fn().mockReturnValue(null)
  }
}))

vi.mock('@/services/settingsService', () => ({
  settingsService: {
    initialize: vi.fn().mockResolvedValue(undefined),
    getSettings: vi.fn().mockReturnValue({}),
    updateSettings: vi.fn().mockResolvedValue(undefined)
  }
}))

vi.mock('@/services/systemLogger', () => ({
  securityLogger: {
    info: vi.fn(),
    warn: vi.fn(),
    error: vi.fn()
  }
}))

// Mock localStorage and sessionStorage
const mockLocalStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn()
}

const mockSessionStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn()
}

Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage
})

Object.defineProperty(window, 'sessionStorage', {
  value: mockSessionStorage
})

// Test component that uses auth
function TestComponent() {
  const { 
    user, 
    isAuthenticated, 
    isLoading, 
    error, 
    login, 
    logout, 
    refreshSession 
  } = useAuth()

  return (
    <div>
      <div data-testid="auth-state">
        {isLoading ? 'loading' : isAuthenticated ? 'authenticated' : 'unauthenticated'}
      </div>
      <div data-testid="user-info">
        {user ? `${user.username} (${user.role})` : 'No user'}
      </div>
      <div data-testid="error-info">
        {error || 'No error'}
      </div>
      <button 
        data-testid="login-btn" 
        onClick={() => login({ 
          username: 'admin', 
          password: 'TomoAdmin123!', 
          rememberMe: false 
        })}
      >
        Login
      </button>
      <button 
        data-testid="logout-btn" 
        onClick={logout}
      >
        Logout
      </button>
      <button 
        data-testid="refresh-btn" 
        onClick={refreshSession}
      >
        Refresh
      </button>
    </div>
  )
}

function renderWithAuth() {
  return render(
    <AuthProvider>
      <TestComponent />
    </AuthProvider>
  )
}

const mockUser = {
  id: '1',
  username: 'admin',
  email: 'admin@tomo.local',
  role: 'admin' as const,
  lastLogin: new Date().toISOString(),
  isActive: true
}

const mockSessionMetadata = {
  sessionId: 'test-session-123',
  userId: '1',
  userAgent: 'Mozilla/5.0',
  ipAddress: '127.0.0.1',
  startTime: new Date().toISOString(),
  lastActivity: new Date().toISOString(),
  expiryTime: new Date(Date.now() + 3600000).toISOString(),
  accessToken: 'mock-jwt-token-123',
  refreshToken: 'mock-refresh-token-123'
}

describe('AuthProvider', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Reset localStorage/sessionStorage mocks
    mockLocalStorage.getItem.mockReturnValue(null)
    mockSessionStorage.getItem.mockReturnValue(null)

    // Setup default successful login mock
    vi.mocked(authService.login).mockResolvedValue({
      user: mockUser,
      token: 'mock-jwt-token-123',
      expiresIn: 3600
    })

    // Setup default session creation mock
    vi.mocked(sessionService.createSession).mockResolvedValue(mockSessionMetadata)

    // Setup renew session mock
    vi.mocked(sessionService.renewSession).mockResolvedValue(mockSessionMetadata)
  })

  afterEach(() => {
    vi.clearAllTimers()
  })

  describe('Initial State', () => {
    it('should start with unauthenticated state', async () => {
      renderWithAuth()
      
      await waitFor(() => {
        expect(screen.getByTestId('auth-state')).toHaveTextContent('unauthenticated')
      })
      
      expect(screen.getByTestId('user-info')).toHaveTextContent('No user')
      expect(screen.getByTestId('error-info')).toHaveTextContent('No error')
    })

    it('should show loading state initially', () => {
      renderWithAuth()
      expect(screen.getByTestId('auth-state')).toHaveTextContent('loading')
    })

    it('should restore session from valid session metadata', async () => {
      const futureDate = new Date()
      futureDate.setHours(futureDate.getHours() + 1)

      // Mock localStorage to return stored user data
      mockLocalStorage.getItem.mockImplementation((key: string) => {
        if (key === 'tomo_user_data') {
          return JSON.stringify(mockUser)
        }
        return null
      })

      // Mock sessionService.validateSession to return a valid session
      vi.mocked(sessionService.validateSession).mockResolvedValueOnce({
        isValid: true,
        metadata: {
          sessionId: 'existing-session-123',
          userId: '1',
          userAgent: 'Mozilla/5.0',
          ipAddress: '127.0.0.1',
          startTime: new Date().toISOString(),
          lastActivity: new Date().toISOString(),
          expiryTime: futureDate.toISOString(),
          accessToken: 'mock-jwt-token',
          refreshToken: 'mock-refresh-token'
        }
      })

      renderWithAuth()

      await waitFor(() => {
        expect(screen.getByTestId('auth-state')).toHaveTextContent('authenticated')
      })

      expect(screen.getByTestId('user-info')).toHaveTextContent('admin (admin)')
    })

    it('should remain unauthenticated when session is invalid', async () => {
      // Session validation returns invalid
      vi.mocked(sessionService.validateSession).mockResolvedValueOnce({
        isValid: false,
        metadata: undefined
      })

      renderWithAuth()

      await waitFor(() => {
        expect(screen.getByTestId('auth-state')).toHaveTextContent('unauthenticated')
      })

      expect(screen.getByTestId('user-info')).toHaveTextContent('No user')
    })
  })

  describe('Login Flow', () => {
    it('should login successfully with valid credentials', async () => {
      const user = userEvent.setup()
      renderWithAuth()

      await waitFor(() => {
        expect(screen.getByTestId('auth-state')).toHaveTextContent('unauthenticated')
      })

      await user.click(screen.getByTestId('login-btn'))

      // Wait for login to complete
      await waitFor(() => {
        expect(screen.getByTestId('auth-state')).toHaveTextContent('authenticated')
      })

      expect(screen.getByTestId('user-info')).toHaveTextContent('admin (admin)')
      expect(authService.login).toHaveBeenCalled()
      expect(sessionService.createSession).toHaveBeenCalled()
    })

    it('should handle login failure gracefully', async () => {
      // Mock login to reject for this test
      vi.mocked(authService.login).mockRejectedValueOnce(new Error('Invalid credentials'))

      const user = userEvent.setup()

      const TestComponentWithInvalidLogin = () => {
        const { login, ...authProps } = useAuth()

        return (
          <div>
            <div data-testid="auth-state">
              {authProps.isLoading ? 'loading' : authProps.isAuthenticated ? 'authenticated' : 'unauthenticated'}
            </div>
            <div data-testid="error-info">
              {authProps.error || 'No error'}
            </div>
            <button
              data-testid="invalid-login-btn"
              onClick={() => login({
                username: 'invalid',
                password: 'invalid',
                rememberMe: false
              }).catch(() => { /* expected error */ })}
            >
              Invalid Login
            </button>
          </div>
        )
      }

      render(
        <AuthProvider>
          <TestComponentWithInvalidLogin />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('auth-state')).toHaveTextContent('unauthenticated')
      })

      await user.click(screen.getByTestId('invalid-login-btn'))

      await waitFor(() => {
        expect(screen.getByTestId('error-info')).toHaveTextContent('Invalid username or password')
      })
    })

    it('should store session data correctly with rememberMe=true', async () => {
      const user = userEvent.setup()
      const TestComponentWithRememberMe = () => {
        const { login, ...authProps } = useAuth()

        return (
          <div>
            <div data-testid="auth-state">
              {authProps.isLoading ? 'loading' : authProps.isAuthenticated ? 'authenticated' : 'unauthenticated'}
            </div>
            <button
              data-testid="remember-login-btn"
              onClick={() => login({
                username: 'admin',
                password: 'TomoAdmin123!',
                rememberMe: true
              })}
            >
              Login with Remember Me
            </button>
          </div>
        )
      }

      render(
        <AuthProvider>
          <TestComponentWithRememberMe />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('auth-state')).toHaveTextContent('unauthenticated')
      })

      await user.click(screen.getByTestId('remember-login-btn'))

      await waitFor(() => {
        expect(screen.getByTestId('auth-state')).toHaveTextContent('authenticated')
      })

      // Verify session was created with rememberMe flag
      expect(sessionService.createSession).toHaveBeenCalledWith(
        expect.objectContaining({
          rememberMe: true
        })
      )
    })
  })

  describe('Logout Flow', () => {
    it('should logout successfully', async () => {
      const user = userEvent.setup()
      renderWithAuth()

      // First login
      await waitFor(() => {
        expect(screen.getByTestId('auth-state')).toHaveTextContent('unauthenticated')
      })

      await user.click(screen.getByTestId('login-btn'))

      await waitFor(() => {
        expect(screen.getByTestId('auth-state')).toHaveTextContent('authenticated')
      })

      // Then logout
      await user.click(screen.getByTestId('logout-btn'))

      await waitFor(() => {
        expect(screen.getByTestId('auth-state')).toHaveTextContent('unauthenticated')
      })

      expect(screen.getByTestId('user-info')).toHaveTextContent('No user')
      expect(sessionService.destroySession).toHaveBeenCalled()
    })
  })

  describe('Session Management', () => {
    it('should refresh session for authenticated user', async () => {
      const user = userEvent.setup()

      // Setup renewSession mock
      vi.mocked(sessionService.renewSession).mockResolvedValue({
        sessionId: 'renewed-session-123',
        userId: '1',
        userAgent: 'Mozilla/5.0',
        ipAddress: '127.0.0.1',
        startTime: new Date().toISOString(),
        lastActivity: new Date().toISOString(),
        expiryTime: new Date(Date.now() + 7200000).toISOString(),
        accessToken: 'new-access-token',
        refreshToken: 'new-refresh-token'
      })

      renderWithAuth()

      await waitFor(() => {
        expect(screen.getByTestId('auth-state')).toHaveTextContent('unauthenticated')
      })

      // First login
      await user.click(screen.getByTestId('login-btn'))

      await waitFor(() => {
        expect(screen.getByTestId('auth-state')).toHaveTextContent('authenticated')
      })

      // Then refresh
      await user.click(screen.getByTestId('refresh-btn'))

      // Should still be authenticated after refresh
      await waitFor(() => {
        expect(screen.getByTestId('auth-state')).toHaveTextContent('authenticated')
      })

      expect(sessionService.renewSession).toHaveBeenCalled()
    })

    it('should logout on failed refresh', async () => {
      const user = userEvent.setup()

      // Mock renewSession to reject
      vi.mocked(sessionService.renewSession).mockRejectedValueOnce(new Error('Session expired'))

      renderWithAuth()

      await waitFor(() => {
        expect(screen.getByTestId('auth-state')).toHaveTextContent('unauthenticated')
      })

      // First login
      await user.click(screen.getByTestId('login-btn'))

      await waitFor(() => {
        expect(screen.getByTestId('auth-state')).toHaveTextContent('authenticated')
      })

      // Try to refresh but it will fail
      await user.click(screen.getByTestId('refresh-btn'))

      await waitFor(() => {
        expect(screen.getByTestId('auth-state')).toHaveTextContent('unauthenticated')
      })
    })
  })

  describe('Error Handling', () => {
    it('should handle context usage outside provider', () => {
      expect(() => {
        render(<TestComponent />)
      }).toThrow('useAuth must be used within an AuthProvider')
    })
  })
})