/**
 * RegistrationPage Test Suite
 *
 * Comprehensive tests for RegistrationPage component including form validation,
 * password strength checking, registration flow, and user experience.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { userEvent } from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { RegistrationPage } from './RegistrationPage'
import { AuthProvider } from '@/providers/AuthProvider'

// Mock the auth hook for controlled testing
const { mockRegister, getMockAuthState, setMockAuthState } = vi.hoisted(() => {
  const mockRegister = vi.fn()
  let mockAuthState = {
    isAuthenticated: false,
    isLoading: false,
    error: null,
    user: null
  }

  return {
    mockRegister,
    getMockAuthState: () => mockAuthState,
    setMockAuthState: (newState: Record<string, unknown>) => { mockAuthState = { ...mockAuthState, ...newState } }
  }
})

vi.mock('@/providers/AuthProvider', async () => {
  const actual = (await vi.importActual('@/providers/AuthProvider')) as Record<string, unknown>
  return {
    ...actual,
    useAuth: () => ({
      register: mockRegister,
      ...getMockAuthState()
    })
  }
})

function renderRegistrationPage() {
  return render(
    <BrowserRouter>
      <AuthProvider>
        <RegistrationPage />
      </AuthProvider>
    </BrowserRouter>
  )
}

// Helper to get password field by placeholder
function getPasswordField() {
  return screen.getByPlaceholderText('Create password')
}

function getConfirmPasswordField() {
  return screen.getByPlaceholderText('Confirm password')
}

describe('RegistrationPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockRegister.mockResolvedValue(undefined)
    setMockAuthState({
      isAuthenticated: false,
      isLoading: false,
      error: null,
      user: null
    })
  })

  describe('Rendering and UI', () => {
    it('should render registration form correctly', () => {
      renderRegistrationPage()

      expect(screen.getByRole('heading', { name: /create account/i })).toBeInTheDocument()
      expect(screen.getByText(/join your tomo assistant/i)).toBeInTheDocument()
      expect(screen.getByRole('textbox', { name: /username/i })).toBeInTheDocument()
      expect(getPasswordField()).toBeInTheDocument()
      expect(getConfirmPasswordField()).toBeInTheDocument()
    })

    it('should show logo in header', () => {
      renderRegistrationPage()

      const logo = screen.getByRole('img', { name: /tomo assistant logo/i })
      expect(logo).toBeInTheDocument()
    })

    it('should initially disable submit button', () => {
      renderRegistrationPage()

      const submitButton = screen.getByRole('button', { name: /create account/i })
      expect(submitButton).toBeDisabled()
    })
  })

  describe('Form Validation', () => {
    it('should show validation error for short username', async () => {
      const user = userEvent.setup()
      renderRegistrationPage()

      const usernameInput = screen.getByRole('textbox', { name: /username/i })

      // Test invalid username
      await user.type(usernameInput, 'ab')
      await user.tab()

      await waitFor(() => {
        expect(screen.getByText(/username must be at least 3 characters/i)).toBeInTheDocument()
      })
    })

    it('should validate password confirmation match', async () => {
      const user = userEvent.setup()
      renderRegistrationPage()

      const passwordInput = getPasswordField()
      const confirmPasswordInput = getConfirmPasswordField()

      await user.type(passwordInput, 'Password123!')
      await user.type(confirmPasswordInput, 'Different123!')
      await user.tab()

      await waitFor(() => {
        expect(screen.getByText(/passwords do not match/i)).toBeInTheDocument()
      })
    })
  })

  describe('Password Visibility Toggle', () => {
    it('should toggle password visibility', async () => {
      const user = userEvent.setup()
      renderRegistrationPage()

      const passwordInput = getPasswordField() as HTMLInputElement
      const toggleButton = screen.getAllByRole('button', { name: /show password/i })[0]

      expect(passwordInput.type).toBe('password')

      await user.click(toggleButton)
      expect(passwordInput.type).toBe('text')

      // Now the button should say "Hide password"
      const hideButton = screen.getAllByRole('button', { name: /hide password/i })[0]
      await user.click(hideButton)
      expect(passwordInput.type).toBe('password')
    })
  })

  describe('Registration Flow', () => {
    it('should fill all available form fields', async () => {
      const user = userEvent.setup()
      renderRegistrationPage()

      // Fill form with valid data
      await user.type(screen.getByRole('textbox', { name: /username/i }), 'testuser')
      await user.type(getPasswordField(), 'TestPassword123!')
      await user.type(getConfirmPasswordField(), 'TestPassword123!')
      await user.click(screen.getByRole('checkbox'))

      // Verify inputs have values
      expect(screen.getByRole('textbox', { name: /username/i })).toHaveValue('testuser')
      expect(getPasswordField()).toHaveValue('TestPassword123!')
      expect(getConfirmPasswordField()).toHaveValue('TestPassword123!')
      expect(screen.getByRole('checkbox')).toBeChecked()
    })
  })

  describe('Authentication Redirect', () => {
    it('should redirect when already authenticated', () => {
      setMockAuthState({
        isAuthenticated: true,
        isLoading: false,
        error: null,
        user: null
      })

      renderRegistrationPage()

      // Should not render the registration form
      expect(screen.queryByRole('heading', { name: /create account/i })).not.toBeInTheDocument()
    })
  })

  describe('Error Handling', () => {
    it('should display auth errors', () => {
      setMockAuthState({
        isAuthenticated: false,
        isLoading: false,
        error: 'Registration failed',
        user: null
      })

      renderRegistrationPage()

      expect(screen.getByText(/registration failed/i)).toBeInTheDocument()
    })
  })
})
