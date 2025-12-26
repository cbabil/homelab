/**
 * LoginPage Test Suite
 * 
 * Comprehensive tests for LoginPage component including form validation,
 * password strength checking, authentication flow, and user experience.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { userEvent } from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { LoginPage } from './LoginPage'
import { AuthProvider } from '@/providers/AuthProvider'

// Mock the auth hook for controlled testing
const mockLogin = vi.fn()
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
      login: mockLogin,
      ...mockAuthState
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

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockLogin.mockResolvedValue(undefined)
    mockAuthState = {
      isAuthenticated: false,
      isLoading: false,
      error: null,
      user: null
    }
  })

  describe('Rendering and UI', () => {
    it('should render login form correctly', () => {
      renderLoginPage()
      
      expect(screen.getByRole('heading', { name: /welcome back/i })).toBeInTheDocument()
      expect(screen.getByText(/sign in to your homelab assistant/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/username/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
      expect(screen.getByRole('checkbox', { name: /remember me/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
    })

    it('should show demo credentials info', () => {
      renderLoginPage()
      
      expect(screen.getByText(/demo credentials/i)).toBeInTheDocument()
      expect(screen.getByText(/admin \/ HomeLabAdmin123!/)).toBeInTheDocument()
      expect(screen.getByText(/user \/ HomeLabUser123!/)).toBeInTheDocument()
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
      
      const usernameInput = screen.getByLabelText(/username/i)
      const passwordInput = screen.getByLabelText(/password/i)
      const submitButton = screen.getByRole('button', { name: /sign in/i })
      
      await user.type(usernameInput, 'admin')
      await user.type(passwordInput, 'HomeLabAdmin123!')
      
      await waitFor(() => {
        expect(submitButton).not.toBeDisabled()
      })
    })
  })

  describe('Authentication Flow', () => {
    it('should call login with correct credentials', async () => {
      const user = userEvent.setup()
      renderLoginPage()
      
      const usernameInput = screen.getByLabelText(/username/i)
      const passwordInput = screen.getByLabelText(/password/i)
      const rememberMeCheckbox = screen.getByLabelText(/remember me/i)
      const submitButton = screen.getByRole('button', { name: /sign in/i })
      
      await user.type(usernameInput, 'admin')
      await user.type(passwordInput, 'HomeLabAdmin123!')
      await user.click(rememberMeCheckbox)
      
      await waitFor(() => {
        expect(submitButton).not.toBeDisabled()
      })
      
      await user.click(submitButton)
      
      expect(mockLogin).toHaveBeenCalledWith({
        username: 'admin',
        password: 'HomeLabAdmin123!',
        rememberMe: true
      })
    })
  })

  describe('Security Features', () => {
    it('should have proper input attributes for security', () => {
      renderLoginPage()
      
      const usernameInput = screen.getByLabelText(/username/i)
      const passwordInput = screen.getByLabelText(/password/i)
      
      expect(usernameInput).toHaveAttribute('autoComplete', 'username')
      expect(passwordInput).toHaveAttribute('autoComplete', 'current-password')
      expect(passwordInput).toHaveAttribute('type', 'password')
    })
  })
})