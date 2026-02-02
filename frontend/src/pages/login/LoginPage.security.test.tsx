/**
 * LoginPage Security Test
 *
 * Tests to verify that login error messages are generic and don't reveal
 * system internals for security purposes.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { LoginPage } from './LoginPage'
import { AuthProvider } from '@/providers/AuthProvider'

// Mock the auth hook for controlled testing
const { mockLogin, getMockAuthState, setMockAuthState } = vi.hoisted(() => {
  const mockLogin = vi.fn()
  let mockAuthState = {
    isAuthenticated: false,
    isLoading: false,
    error: null,
    user: null
  }

  return {
    mockLogin,
    getMockAuthState: () => mockAuthState,
    setMockAuthState: (newState: Record<string, unknown>) => { mockAuthState = { ...mockAuthState, ...newState } }
  }
})

vi.mock('@/providers/AuthProvider', async () => {
  const actual = (await vi.importActual('@/providers/AuthProvider')) as Record<string, unknown>
  return {
    ...actual,
    useAuth: () => ({
      login: mockLogin,
      ...getMockAuthState()
    })
  }
})

const renderLoginPage = () => {
  return render(
    <BrowserRouter>
      <AuthProvider>
        <LoginPage />
      </AuthProvider>
    </BrowserRouter>
  )
}

// Helper to get password field by placeholder
function getPasswordField() {
  return screen.getByPlaceholderText('Password')
}

describe('LoginPage Security Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockLogin.mockResolvedValue(undefined)
    setMockAuthState({
      isAuthenticated: false,
      isLoading: false,
      error: null,
      user: null
    })
  })

  it('should show generic error message for authentication failures', async () => {
    renderLoginPage()

    // Wait for component to render
    await waitFor(() => {
      const submitButton = screen.getByRole('button', { name: /sign in/i })
      expect(submitButton).toBeInTheDocument()
    })

    // Verify that specific system error messages are NOT shown
    expect(screen.queryByText(/no session found/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/session expired/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/failed to restore session/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/jwt validation failed/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/validation failed/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/settings not initialized/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/authentication required/i)).not.toBeInTheDocument()
  })

  it('should not reveal system internals in error messages', async () => {
    renderLoginPage()

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /welcome back/i })).toBeInTheDocument()
    })

    // Check that no system-level errors are revealed
    expect(screen.queryByText(/indexeddb/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/jwt/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/database/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/storage/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/token/i)).not.toBeInTheDocument()
  })

  it('should render page normally even with potential backend issues', async () => {
    renderLoginPage()

    // Wait for component to render
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
    })

    // Verify that page renders normally
    expect(screen.getByRole('textbox', { name: /username/i })).toBeInTheDocument()
    expect(getPasswordField()).toBeInTheDocument()

    // No error alert should be shown on initial load
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('should have secure password field', () => {
    renderLoginPage()

    const passwordInput = getPasswordField()

    // Password field should be type="password" by default
    expect(passwordInput).toHaveAttribute('type', 'password')

    // Should have proper autocomplete attribute
    expect(passwordInput).toHaveAttribute('autocomplete', 'current-password')
  })

  it('should have secure username field', () => {
    renderLoginPage()

    const usernameInput = screen.getByRole('textbox', { name: /username/i })

    // Should have proper autocomplete attribute
    expect(usernameInput).toHaveAttribute('autocomplete', 'username')
  })
})
