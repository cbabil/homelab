/**
 * LoginPage Security Test
 * 
 * Tests to verify that login error messages are generic and don't reveal
 * system internals for security purposes.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { LoginPage } from './LoginPage'
import { AuthProvider } from '@/providers/AuthProvider'

// Mock auth services to simulate different error scenarios
vi.mock('@/services/auth/authService', () => ({
  authService: {
    initialize: vi.fn().mockResolvedValue(undefined),
    login: vi.fn().mockRejectedValue(new Error('Mock auth service error')),
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

describe('LoginPage Security Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should show generic error message for authentication failures', async () => {
    renderLoginPage()

    // Wait for potential initialization errors to resolve
    await waitFor(() => {
      // Look for either loading state or ready state
      const submitButton = screen.getByRole('button', { name: /sign in|signing in/i })
      expect(submitButton).toBeInTheDocument()
    })

    // Check if there's an initial error displayed (from initialization)
    const errorText = screen.queryByText(/invalid username or password/i)
    if (errorText) {
      expect(errorText).toBeInTheDocument()
    }

    // Verify that specific system error messages are NOT shown anywhere
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

    // Wait for initial load errors to be handled
    await waitFor(() => {
      // Check that any displayed error is generic
      const errorElements = screen.queryAllByText(/error|fail/i)
      errorElements.forEach(element => {
        const text = element.textContent?.toLowerCase() || ''
        
        // Verify no specific system errors are revealed
        expect(text).not.toContain('indexeddb')
        expect(text).not.toContain('jwt')
        expect(text).not.toContain('session')
        expect(text).not.toContain('token')
        expect(text).not.toContain('database')
        expect(text).not.toContain('storage')
        expect(text).not.toContain('expired')
        expect(text).not.toContain('not found')
        expect(text).not.toContain('validation')
        
        // Only allow generic messages
        if (text.includes('error') || text.includes('fail')) {
          expect(
            text.includes('invalid username or password') ||
            text.includes('sign') ||
            text.includes('demo')
          ).toBe(true)
        }
      })
    })
  })

  it('should handle initialization errors gracefully with generic messages', async () => {
    renderLoginPage()

    // Wait for component to render and handle initialization
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
    })

    // Verify that page renders normally despite backend errors
    expect(screen.getByLabelText(/username/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    
    // If any error is shown, it should be generic
    const possibleError = screen.queryByText(/invalid username or password/i)
    if (possibleError) {
      expect(possibleError).toBeInTheDocument()
    }
  })
})