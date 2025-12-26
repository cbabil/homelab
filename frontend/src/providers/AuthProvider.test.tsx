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
import { AUTH_STORAGE_KEYS } from '@/types/auth'

// Global service mocks are provided by test setup
// Individual tests can override these mocks as needed

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
          password: 'HomeLabAdmin123!', 
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

describe('AuthProvider', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Reset localStorage/sessionStorage mocks
    mockLocalStorage.getItem.mockReturnValue(null)
    mockSessionStorage.getItem.mockReturnValue(null)
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

    it('should restore session from localStorage', async () => {
      const mockUser = {
        id: '1',
        username: 'admin',
        email: 'admin@homelab.local',
        role: 'admin' as const,
        lastLogin: '2023-01-01T00:00:00Z',
        isActive: true
      }
      
      const futureDate = new Date()
      futureDate.setHours(futureDate.getHours() + 1)
      
      mockLocalStorage.getItem.mockImplementation((key) => {
        switch (key) {
          case AUTH_STORAGE_KEYS.TOKEN:
            return 'mock-jwt-token'
          case AUTH_STORAGE_KEYS.USER:
            return JSON.stringify(mockUser)
          case AUTH_STORAGE_KEYS.SESSION_EXPIRY:
            return futureDate.toISOString()
          default:
            return null
        }
      })

      renderWithAuth()
      
      await waitFor(() => {
        expect(screen.getByTestId('auth-state')).toHaveTextContent('authenticated')
      })
      
      expect(screen.getByTestId('user-info')).toHaveTextContent('admin (admin)')
    })

    it('should clear expired session', async () => {
      const mockUser = {
        id: '1',
        username: 'admin',
        email: 'admin@homelab.local',
        role: 'admin' as const,
        lastLogin: '2023-01-01T00:00:00Z',
        isActive: true
      }
      
      const pastDate = new Date()
      pastDate.setHours(pastDate.getHours() - 1)
      
      mockLocalStorage.getItem.mockImplementation((key) => {
        switch (key) {
          case AUTH_STORAGE_KEYS.TOKEN:
            return 'mock-jwt-token'
          case AUTH_STORAGE_KEYS.USER:
            return JSON.stringify(mockUser)
          case AUTH_STORAGE_KEYS.SESSION_EXPIRY:
            return pastDate.toISOString()
          default:
            return null
        }
      })

      renderWithAuth()
      
      await waitFor(() => {
        expect(screen.getByTestId('auth-state')).toHaveTextContent('unauthenticated')
      })
      
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith(AUTH_STORAGE_KEYS.TOKEN)
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith(AUTH_STORAGE_KEYS.USER)
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
      
      // Should show loading state during login
      expect(screen.getByTestId('auth-state')).toHaveTextContent('loading')
      
      // Wait for login to complete
      await waitFor(() => {
        expect(screen.getByTestId('auth-state')).toHaveTextContent('authenticated')
      })
      
      expect(screen.getByTestId('user-info')).toHaveTextContent('admin (admin)')
    })

    it('should handle login failure gracefully', async () => {
      const user = userEvent.setup()
      renderWithAuth()

      await waitFor(() => {
        expect(screen.getByTestId('auth-state')).toHaveTextContent('unauthenticated')
      })

      // Mock invalid credentials by patching the login function
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
              })}
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
                password: 'HomeLabAdmin123!', 
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

      // Verify localStorage calls
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
        AUTH_STORAGE_KEYS.TOKEN,
        expect.stringMatching(/^mock-jwt-token/)
      )
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
        AUTH_STORAGE_KEYS.REMEMBER_ME,
        'true'
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

      expect(screen.getByTestId('auth-state')).toHaveTextContent('unauthenticated')
      expect(screen.getByTestId('user-info')).toHaveTextContent('No user')
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith(AUTH_STORAGE_KEYS.TOKEN)
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith(AUTH_STORAGE_KEYS.USER)
    })
  })

  describe('Session Management', () => {
    it('should handle refresh token flow', async () => {
      const user = userEvent.setup()
      
      // Mock refresh token in localStorage
      mockLocalStorage.getItem.mockImplementation((key) => {
        if (key === AUTH_STORAGE_KEYS.REFRESH_TOKEN) {
          return 'mock-refresh-token-123'
        }
        return null
      })

      renderWithAuth()

      await waitFor(() => {
        expect(screen.getByTestId('auth-state')).toHaveTextContent('unauthenticated')
      })

      await user.click(screen.getByTestId('refresh-btn'))

      await waitFor(() => {
        expect(screen.getByTestId('auth-state')).toHaveTextContent('authenticated')
      })
    })

    it('should logout on failed refresh', async () => {
      const user = userEvent.setup()
      
      // Mock invalid refresh token
      mockLocalStorage.getItem.mockImplementation((key) => {
        if (key === AUTH_STORAGE_KEYS.REFRESH_TOKEN) {
          return 'invalid-refresh-token'
        }
        return null
      })

      renderWithAuth()

      await waitFor(() => {
        expect(screen.getByTestId('auth-state')).toHaveTextContent('unauthenticated')
      })

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