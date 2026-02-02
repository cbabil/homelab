/**
 * LoginPage Clean State Test
 *
 * Tests to verify that the login page loads without any error messages
 * and only shows errors after user interaction and form submission.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
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

describe('LoginPage Clean Initial State', () => {
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

  it('should load without any error messages initially', async () => {
    renderLoginPage()

    // Wait for component to fully render
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /welcome back/i })).toBeInTheDocument()
    })

    // Verify no error messages are present initially
    expect(screen.queryByText(/invalid username or password/i)).not.toBeInTheDocument()

    // Check that no error alert is shown
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()

    // Verify form is in clean state
    expect(screen.getByRole('textbox', { name: /username/i })).toHaveValue('')
    expect(getPasswordField()).toHaveValue('')
  })

  it('should show error only after form submission with invalid credentials', async () => {
    const user = userEvent.setup()

    // Mock login failure
    mockLogin.mockRejectedValue(new Error('Invalid username or password'))

    renderLoginPage()

    // Wait for form to be ready
    await waitFor(() => {
      expect(screen.getByRole('textbox', { name: /username/i })).toBeInTheDocument()
    })

    // Initially no errors
    expect(screen.queryByText(/invalid username or password/i)).not.toBeInTheDocument()

    // Fill form with valid-format but wrong credentials
    const usernameInput = screen.getByRole('textbox', { name: /username/i })
    const passwordInput = getPasswordField()

    await user.type(usernameInput, 'wronguser')
    await user.type(passwordInput, 'WrongPassword123!')

    // Still no errors before submission
    expect(screen.queryByText(/invalid username or password/i)).not.toBeInTheDocument()

    // Submit the form
    const submitButton = screen.getByRole('button', { name: /sign in/i })

    await waitFor(() => {
      expect(submitButton).not.toBeDisabled()
    })

    await user.click(submitButton)

    // Now error should appear after submission
    await waitFor(() => {
      expect(screen.getByText(/invalid username or password/i)).toBeInTheDocument()
    }, { timeout: 3000 })
  })

  it('should not show authentication context errors on initial load', async () => {
    renderLoginPage()

    // Wait for component to render
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /welcome back/i })).toBeInTheDocument()
    })

    // Verify no error alert is shown initially
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('should maintain clean state during typing', async () => {
    const user = userEvent.setup()
    renderLoginPage()

    await waitFor(() => {
      expect(screen.getByRole('textbox', { name: /username/i })).toBeInTheDocument()
    })

    const usernameInput = screen.getByRole('textbox', { name: /username/i })
    const passwordInput = getPasswordField()

    // Type in fields
    await user.type(usernameInput, 'test')
    await user.type(passwordInput, 'test123')

    // No errors should appear while typing
    expect(screen.queryByText(/invalid username or password/i)).not.toBeInTheDocument()
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()

    // Clear fields
    await user.clear(usernameInput)
    await user.clear(passwordInput)

    // Still no errors should appear
    expect(screen.queryByText(/invalid username or password/i)).not.toBeInTheDocument()
  })
})
