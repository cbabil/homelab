/**
 * LoginPage Clean State Test
 * 
 * Tests to verify that the login page loads without any error messages
 * and only shows errors after user interaction and form submission.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { LoginPage } from './LoginPage'
import { AuthProvider } from '@/providers/AuthProvider'

// Mock auth services to simulate clean initial state
vi.mock('@/services/auth/authService', () => ({
  authService: {
    initialize: vi.fn().mockResolvedValue(undefined),
    login: vi.fn().mockRejectedValue(new Error('Invalid username or password')),
    validateToken: vi.fn().mockResolvedValue(false)
  }
}))

vi.mock('@/services/auth/sessionService', () => ({
  sessionService: {
    initialize: vi.fn().mockResolvedValue(undefined),
    validateSession: vi.fn().mockResolvedValue({
      isValid: false,
      reason: 'Authentication required'
    }),
    createSession: vi.fn().mockRejectedValue(new Error('Mock session error'))
  }
}))

vi.mock('@/services/settingsService', () => ({
  settingsService: {
    initialize: vi.fn().mockResolvedValue(undefined),
    getSessionTimeoutMs: vi.fn().mockReturnValue(3600000)
  }
}))

const renderLoginPage = () => {
  return render(
    <BrowserRouter>
      <AuthProvider>
        <LoginPage />
      </AuthProvider>
    </BrowserRouter>
  )
}

describe('LoginPage Clean Initial State', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should load without any error messages initially', async () => {
    renderLoginPage()

    // Wait for component to fully render
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /welcome back/i })).toBeInTheDocument()
    })

    // Verify no error messages are present initially
    expect(screen.queryByText(/invalid username or password/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/error/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/failed/i)).not.toBeInTheDocument()
    
    // Check that no error alert is shown
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
    
    // Verify form is in clean state
    expect(screen.getByLabelText(/username/i)).toHaveValue('')
    expect(screen.getByLabelText(/password/i)).toHaveValue('')
    
    // Demo credentials should be shown (this is informational, not an error)
    expect(screen.getByText(/demo credentials/i)).toBeInTheDocument()
  })

  it('should show error only after form submission with invalid credentials', async () => {
    renderLoginPage()

    // Wait for form to be ready
    await waitFor(() => {
      expect(screen.getByLabelText(/username/i)).toBeInTheDocument()
    })

    // Initially no errors
    expect(screen.queryByText(/invalid username or password/i)).not.toBeInTheDocument()

    // Fill form with valid-format but wrong credentials
    const usernameInput = screen.getByLabelText(/username/i)
    const passwordInput = screen.getByLabelText(/password/i)
    
    fireEvent.change(usernameInput, { target: { value: 'wronguser' } })
    fireEvent.change(passwordInput, { target: { value: 'WrongPassword123!' } })

    // Still no errors before submission
    expect(screen.queryByText(/invalid username or password/i)).not.toBeInTheDocument()

    // Submit the form
    const submitButton = screen.getByRole('button', { name: /sign in|signing in/i })
    fireEvent.click(submitButton)

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

    // Even if auth context has errors, they should not be displayed initially
    // Only form submission errors should be shown
    const errorElements = screen.queryAllByText(/error|fail|invalid|expired|session/i)
    
    // Filter out expected non-error text
    const actualErrors = errorElements.filter(element => {
      const text = element.textContent?.toLowerCase() || ''
      // These are expected UI text, not errors
      return !text.includes('demo') && 
             !text.includes('forgot') && 
             !text.includes('remember') &&
             !text.includes('sign') &&
             !text.includes('welcome') &&
             !text.includes('homelab')
    })

    expect(actualErrors).toHaveLength(0)
  })

  it('should maintain clean state during typing', async () => {
    renderLoginPage()

    await waitFor(() => {
      expect(screen.getByLabelText(/username/i)).toBeInTheDocument()
    })

    const usernameInput = screen.getByLabelText(/username/i)
    const passwordInput = screen.getByLabelText(/password/i)

    // Type in fields
    fireEvent.change(usernameInput, { target: { value: 'test' } })
    fireEvent.change(passwordInput, { target: { value: 'test123' } })

    // No errors should appear while typing
    expect(screen.queryByText(/invalid username or password/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/error/i)).not.toBeInTheDocument()
    
    // Clear fields
    fireEvent.change(usernameInput, { target: { value: '' } })
    fireEvent.change(passwordInput, { target: { value: '' } })

    // Still no errors should appear
    expect(screen.queryByText(/invalid username or password/i)).not.toBeInTheDocument()
  })
})