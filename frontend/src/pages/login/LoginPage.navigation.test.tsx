/**
 * LoginPage Form Behavior Test Suite
 * 
 * Tests to verify that the login form properly handles form submission,
 * stays on the same page during validation failures, and manages state correctly.
 */

import React from 'react'
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

describe('LoginPage Form Behavior', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockAuthState = {
      isAuthenticated: false,
      isLoading: false,
      error: null,
      user: null
    }
  })

  it('should stay on login page and show error when form submission fails', async () => {
    const user = userEvent.setup()
    
    // Mock login failure
    mockLogin.mockRejectedValue(new Error('Invalid username or password'))
    
    renderLoginPage()
    
    const usernameInput = screen.getByLabelText(/username/i)
    const passwordInput = screen.getByLabelText(/password/i)
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
    expect(screen.getByLabelText(/username/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
  })

  it('should show loading state during authentication and return to normal after failure', async () => {
    const user = userEvent.setup()
    
    // Mock delayed login failure
    mockLogin.mockImplementation(() => 
      new Promise((_, reject) => 
        setTimeout(() => reject(new Error('Invalid username or password')), 300)
      )
    )
    
    renderLoginPage()
    
    const usernameInput = screen.getByLabelText(/username/i)
    const passwordInput = screen.getByLabelText(/password/i)
    const submitButton = screen.getByRole('button', { name: /sign in/i })
    
    await user.type(usernameInput, 'invalid')
    await user.type(passwordInput, 'invalid')
    
    await waitFor(() => {
      expect(submitButton).not.toBeDisabled()
    })
    
    // Submit form
    await user.click(submitButton)
    
    // Should show loading state immediately
    expect(screen.getByRole('button', { name: /signing in/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /signing in/i })).toBeDisabled()
    
    // Wait for login to complete and show error
    await waitFor(() => {
      expect(screen.getByText(/invalid username or password/i)).toBeInTheDocument()
    }, { timeout: 1000 })
    
    // Should return to normal state
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign in/i })).not.toBeDisabled()
  })

  it('should prevent rapid successive form submissions', async () => {
    const user = userEvent.setup()
    
    mockLogin.mockImplementation(() => 
      new Promise((_, reject) => 
        setTimeout(() => reject(new Error('Invalid username or password')), 200)
      )
    )
    
    renderLoginPage()
    
    const usernameInput = screen.getByLabelText(/username/i)
    const passwordInput = screen.getByLabelText(/password/i)
    
    await user.type(usernameInput, 'invalid')
    await user.type(passwordInput, 'invalid')
    
    const submitButton = screen.getByRole('button', { name: /sign in/i })
    
    await waitFor(() => {
      expect(submitButton).not.toBeDisabled()
    })
    
    // Click submit button
    await user.click(submitButton)
    
    // Button should be disabled immediately (showing loading state)
    expect(screen.getByRole('button', { name: /signing in/i })).toBeDisabled()
    
    // Try to click again - should not register because button is disabled
    const loadingButton = screen.getByRole('button', { name: /signing in/i })
    await user.click(loadingButton)
    
    // Should only call login once
    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledTimes(1)
    })
  })

  it('should clear previous error messages when user starts typing', async () => {
    const user = userEvent.setup()
    
    // Mock login failure
    mockLogin.mockRejectedValue(new Error('Invalid username or password'))
    
    renderLoginPage()
    
    const usernameInput = screen.getByLabelText(/username/i)
    const passwordInput = screen.getByLabelText(/password/i)
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
    
    const usernameInput = screen.getByLabelText(/username/i)
    const passwordInput = screen.getByLabelText(/password/i)
    const rememberMeCheckbox = screen.getByLabelText(/remember me/i)
    const submitButton = screen.getByRole('button', { name: /sign in/i })
    
    // Fill form
    await user.type(usernameInput, 'admin')
    await user.type(passwordInput, 'HomeLabAdmin123!')
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
        password: 'HomeLabAdmin123!',
        rememberMe: true
      })
    })
  })
})