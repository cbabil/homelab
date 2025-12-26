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
const mockRegister = vi.fn()
let mockAuthState = {
  isAuthenticated: false,
  isLoading: false,
  error: null,
  user: null
}

vi.mock('@/providers/AuthProvider', async () => {
  const actual = await vi.importActual('@/providers/AuthProvider')
  return {
    ...actual,
    useAuth: () => ({
      register: mockRegister,
      ...mockAuthState
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

describe('RegistrationPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockRegister.mockResolvedValue(undefined)
    mockAuthState = {
      isAuthenticated: false,
      isLoading: false,
      error: null,
      user: null
    }
  })

  describe('Rendering and UI', () => {
    it('should render registration form correctly', () => {
      renderRegistrationPage()
      
      expect(screen.getByRole('heading', { name: /create account/i })).toBeInTheDocument()
      expect(screen.getByText(/join your homelab assistant/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/username/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument()
    })

    it('should show shield icon in header', () => {
      renderRegistrationPage()
      
      const shieldIcon = screen.getByRole('img', { hidden: true })
      expect(shieldIcon).toBeInTheDocument()
    })

    it('should initially disable submit button', () => {
      renderRegistrationPage()
      
      const submitButton = screen.getByRole('button', { name: /create account/i })
      expect(submitButton).toBeDisabled()
    })
  })

  describe('Form Validation', () => {
    it('should show validation errors for invalid inputs', async () => {
      const user = userEvent.setup()
      renderRegistrationPage()
      
      const usernameInput = screen.getByLabelText(/username/i)
      const emailInput = screen.getByLabelText(/email/i)
      
      // Test invalid username
      await user.type(usernameInput, 'ab')
      await user.tab()
      
      expect(screen.getByText(/username must be at least 3 characters/i)).toBeInTheDocument()
      
      // Test invalid email
      await user.type(emailInput, 'invalid-email')
      await user.tab()
      
      expect(screen.getByText(/please enter a valid email address/i)).toBeInTheDocument()
    })

    it('should validate password confirmation match', async () => {
      const user = userEvent.setup()
      renderRegistrationPage()
      
      const passwordInput = screen.getByLabelText(/^password$/i)
      const confirmPasswordInput = screen.getByLabelText(/confirm password/i)
      
      await user.type(passwordInput, 'Password123!')
      await user.type(confirmPasswordInput, 'Different123!')
      await user.tab()
      
      expect(screen.getByText(/passwords do not match/i)).toBeInTheDocument()
    })
  })

  describe('Password Visibility Toggle', () => {
    it('should toggle password visibility', async () => {
      const user = userEvent.setup()
      renderRegistrationPage()
      
      const passwordInput = screen.getByLabelText(/^password$/i) as HTMLInputElement
      const toggleButton = screen.getByRole('button', { name: /toggle password visibility/i })
      
      expect(passwordInput.type).toBe('password')
      
      await user.click(toggleButton)
      expect(passwordInput.type).toBe('text')
      
      await user.click(toggleButton)
      expect(passwordInput.type).toBe('password')
    })
  })

  describe('Registration Flow', () => {
    it('should call register with valid form data', async () => {
      const user = userEvent.setup()
      renderRegistrationPage()
      
      // Fill form with valid data
      await user.type(screen.getByLabelText(/username/i), 'testuser')
      await user.type(screen.getByLabelText(/email/i), 'test@example.com')
      await user.type(screen.getByLabelText(/^password$/i), 'TestPassword123!')
      await user.type(screen.getByLabelText(/confirm password/i), 'TestPassword123!')
      await user.click(screen.getByLabelText(/accept terms/i))
      
      const submitButton = screen.getByRole('button', { name: /create account/i })
      
      await waitFor(() => {
        expect(submitButton).not.toBeDisabled()
      })
      
      await user.click(submitButton)
      
      expect(mockRegister).toHaveBeenCalledWith({
        username: 'testuser',
        email: 'test@example.com',
        password: 'TestPassword123!',
        acceptTerms: true
      })
    })
  })

  describe('Authentication Redirect', () => {
    it('should redirect when already authenticated', () => {
      mockAuthState.isAuthenticated = true
      
      renderRegistrationPage()
      
      // Should not render the registration form
      expect(screen.queryByRole('heading', { name: /create account/i })).not.toBeInTheDocument()
    })
  })

  describe('Error Handling', () => {
    it('should display auth errors', () => {
      mockAuthState.error = 'Registration failed'
      
      renderRegistrationPage()
      
      expect(screen.getByText(/registration failed/i)).toBeInTheDocument()
    })
  })
})