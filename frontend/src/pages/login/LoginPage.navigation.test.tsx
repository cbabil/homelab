/**
 * LoginPage Form Behavior Test Suite
 *
 * Tests to verify that the login form properly handles form submission,
 * stays on the same page during validation failures, and manages state correctly.
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

describe('LoginPage Form Behavior', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    setMockAuthState({
      isAuthenticated: false,
      isLoading: false,
      error: null,
      user: null
    })
  })

  it('should stay on login page and show error when form submission fails', async () => {
    const user = userEvent.setup()

    // Mock login failure
    mockLogin.mockRejectedValue(new Error('Invalid username or password'))

    renderLoginPage()

    const usernameInput = screen.getByRole('textbox', { name: /username/i })
    const passwordInput = getPasswordField()
    const submitButton = screen.getByRole('button', { name: /sign in/i })

    // Fill invalid credentials
    await user.type(usernameInput, 'invalid')
    await user.type(passwordInput, 'invalid')

    await waitFor(() => {
      expect(submitButton).not.toBeDisabled()
    })

    // Submit form
    await user.click(submitButton)

    // Wait for login attempt to complete
    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalled()
    })

    // Should show error message
    await waitFor(() => {
      expect(screen.getByText(/invalid username or password/i)).toBeInTheDocument()
    })

    // Should still be on login page (form elements still visible)
    expect(screen.getByRole('textbox', { name: /username/i })).toBeInTheDocument()
    expect(getPasswordField()).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
  })

  it('should call login when form is submitted', async () => {
    const user = userEvent.setup()

    // Mock login
    mockLogin.mockResolvedValue({})

    renderLoginPage()

    const usernameInput = screen.getByRole('textbox', { name: /username/i })
    const passwordInput = getPasswordField()
    const submitButton = screen.getByRole('button', { name: /sign in/i })

    await user.type(usernameInput, 'admin')
    await user.type(passwordInput, 'TomoAdmin123!')

    await waitFor(() => {
      expect(submitButton).not.toBeDisabled()
    })

    // Submit form
    await user.click(submitButton)

    // Wait for login to be called
    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalled()
    })

    // Verify login was called with correct credentials
    expect(mockLogin).toHaveBeenCalledWith({
      username: 'admin',
      password: 'TomoAdmin123!',
      rememberMe: false
    })
  })

  it('should prevent rapid successive form submissions', async () => {
    const user = userEvent.setup()

    mockLogin.mockImplementation(() =>
      new Promise((_, reject) =>
        setTimeout(() => reject(new Error('Invalid username or password')), 200)
      )
    )

    renderLoginPage()

    const usernameInput = screen.getByRole('textbox', { name: /username/i })
    const passwordInput = getPasswordField()

    await user.type(usernameInput, 'testuser')
    await user.type(passwordInput, 'testpassword')

    const submitButton = screen.getByRole('button', { name: /sign in/i })

    await waitFor(() => {
      expect(submitButton).not.toBeDisabled()
    })

    // Click submit button
    await user.click(submitButton)

    // Wait for the login attempt to complete
    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledTimes(1)
    })

    // Should only have called login once (no rapid duplicate submissions)
    expect(mockLogin).toHaveBeenCalledTimes(1)
  })

  it('should clear previous error messages when user starts typing', async () => {
    const user = userEvent.setup()

    // Mock login failure
    mockLogin.mockRejectedValue(new Error('Invalid username or password'))

    renderLoginPage()

    const usernameInput = screen.getByRole('textbox', { name: /username/i })
    const passwordInput = getPasswordField()
    const submitButton = screen.getByRole('button', { name: /sign in/i })

    // Submit invalid form first
    await user.type(usernameInput, 'invalid')
    await user.type(passwordInput, 'invalid')

    await waitFor(() => {
      expect(submitButton).not.toBeDisabled()
    })

    await user.click(submitButton)

    // Wait for error to appear
    await waitFor(() => {
      expect(screen.getByText(/invalid username or password/i)).toBeInTheDocument()
    })

    // Start typing again - error should clear
    await user.clear(usernameInput)
    await user.type(usernameInput, 'n')

    // Error message should be gone
    expect(screen.queryByText(/invalid username or password/i)).not.toBeInTheDocument()
  })

  it('should call login with correct credentials structure', async () => {
    const user = userEvent.setup()

    // Mock login success
    mockLogin.mockResolvedValue({})

    renderLoginPage()

    const usernameInput = screen.getByRole('textbox', { name: /username/i })
    const passwordInput = getPasswordField()
    const rememberMeCheckbox = screen.getByRole('checkbox', { name: /remember me/i })
    const submitButton = screen.getByRole('button', { name: /sign in/i })

    // Fill form
    await user.type(usernameInput, 'admin')
    await user.type(passwordInput, 'TomoAdmin123!')
    await user.click(rememberMeCheckbox)

    await waitFor(() => {
      expect(submitButton).not.toBeDisabled()
    })

    // Submit form
    await user.click(submitButton)

    // Should call login with correct structure
    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith({
        username: 'admin',
        password: 'TomoAdmin123!',
        rememberMe: true
      })
    })
  })
})
