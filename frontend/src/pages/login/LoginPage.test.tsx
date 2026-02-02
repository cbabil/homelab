/**
 * LoginPage Test Suite
 *
 * Tests for LoginPage component including form validation,
 * authentication flow, and user experience.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { userEvent } from '@testing-library/user-event'
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

function renderLoginPage() {
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

describe('LoginPage', () => {
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

  describe('Rendering and UI', () => {
    it('should render login form correctly', () => {
      renderLoginPage()

      expect(screen.getByRole('heading', { name: /welcome back/i })).toBeInTheDocument()
      expect(screen.getByText(/sign in to your account to continue/i)).toBeInTheDocument()
      expect(screen.getByRole('textbox', { name: /username/i })).toBeInTheDocument()
      expect(getPasswordField()).toBeInTheDocument()
      expect(screen.getByRole('checkbox', { name: /remember me/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
    })

    it('should show registration link', () => {
      renderLoginPage()

      expect(screen.getByText(/don't have an account/i)).toBeInTheDocument()
      expect(screen.getByRole('link', { name: /create account/i })).toBeInTheDocument()
    })

    it('should show forgot password link', () => {
      renderLoginPage()

      expect(screen.getByRole('link', { name: /forgot password/i })).toBeInTheDocument()
    })

    it('should initially disable submit button', () => {
      renderLoginPage()

      const submitButton = screen.getByRole('button', { name: /sign in/i })
      expect(submitButton).toBeDisabled()
    })
  })

  describe('Form Validation', () => {
    it('should enable submit button with valid form', async () => {
      const user = userEvent.setup()
      renderLoginPage()

      const usernameInput = screen.getByRole('textbox', { name: /username/i })
      const passwordInput = getPasswordField()
      const submitButton = screen.getByRole('button', { name: /sign in/i })

      await user.type(usernameInput, 'admin')
      await user.type(passwordInput, 'TomoAdmin123!')

      await waitFor(() => {
        expect(submitButton).not.toBeDisabled()
      })
    })

    it('should keep submit button disabled with empty username', async () => {
      const user = userEvent.setup()
      renderLoginPage()

      const passwordInput = getPasswordField()
      const submitButton = screen.getByRole('button', { name: /sign in/i })

      await user.type(passwordInput, 'TomoAdmin123!')

      expect(submitButton).toBeDisabled()
    })

    it('should keep submit button disabled with empty password', async () => {
      const user = userEvent.setup()
      renderLoginPage()

      const usernameInput = screen.getByRole('textbox', { name: /username/i })
      const submitButton = screen.getByRole('button', { name: /sign in/i })

      await user.type(usernameInput, 'admin')

      expect(submitButton).toBeDisabled()
    })
  })

  describe('Authentication Flow', () => {
    it('should call login with correct credentials', async () => {
      const user = userEvent.setup()
      renderLoginPage()

      const usernameInput = screen.getByRole('textbox', { name: /username/i })
      const passwordInput = getPasswordField()
      const rememberMeCheckbox = screen.getByRole('checkbox', { name: /remember me/i })
      const submitButton = screen.getByRole('button', { name: /sign in/i })

      await user.type(usernameInput, 'admin')
      await user.type(passwordInput, 'TomoAdmin123!')
      await user.click(rememberMeCheckbox)

      await waitFor(() => {
        expect(submitButton).not.toBeDisabled()
      })

      await user.click(submitButton)

      expect(mockLogin).toHaveBeenCalledWith({
        username: 'admin',
        password: 'TomoAdmin123!',
        rememberMe: true
      })
    })

    it('should call login without remember me', async () => {
      const user = userEvent.setup()
      renderLoginPage()

      const usernameInput = screen.getByRole('textbox', { name: /username/i })
      const passwordInput = getPasswordField()
      const submitButton = screen.getByRole('button', { name: /sign in/i })

      await user.type(usernameInput, 'admin')
      await user.type(passwordInput, 'TomoAdmin123!')

      await waitFor(() => {
        expect(submitButton).not.toBeDisabled()
      })

      await user.click(submitButton)

      expect(mockLogin).toHaveBeenCalledWith({
        username: 'admin',
        password: 'TomoAdmin123!',
        rememberMe: false
      })
    })
  })

  describe('Security Features', () => {
    it('should have proper input attributes for security', () => {
      renderLoginPage()

      const usernameInput = screen.getByRole('textbox', { name: /username/i })
      const passwordInput = getPasswordField()

      expect(usernameInput).toHaveAttribute('autocomplete', 'username')
      expect(passwordInput).toHaveAttribute('autocomplete', 'current-password')
      expect(passwordInput).toHaveAttribute('type', 'password')
    })

    it('should toggle password visibility', async () => {
      const user = userEvent.setup()
      renderLoginPage()

      const passwordInput = getPasswordField() as HTMLInputElement
      const toggleButton = screen.getByRole('button', { name: /show password/i })

      expect(passwordInput.type).toBe('password')

      await user.click(toggleButton)

      expect(passwordInput.type).toBe('text')
    })
  })

  describe('Accessibility', () => {
    it('should have accessible form structure', () => {
      renderLoginPage()

      expect(screen.getByRole('heading', { level: 4 })).toBeInTheDocument()
      expect(screen.getByRole('textbox', { name: /username/i })).toBeInTheDocument()
      expect(screen.getByRole('checkbox', { name: /remember me/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
    })
  })
})
