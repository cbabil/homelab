/**
 * SetupPage Test Suite
 *
 * Tests for SetupPage component including form validation,
 * admin account creation, and user experience.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { userEvent } from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { SetupPage } from './SetupPage'

// Mock useSystemSetup hook
const mockUseSystemSetup = vi.fn()
vi.mock('@/hooks/useSystemSetup', () => ({
  useSystemSetup: () => mockUseSystemSetup()
}))

// Mock MCP provider
const mockCallTool = vi.fn()
vi.mock('@/providers/MCPProvider', () => ({
  useMCP: () => ({
    client: { callTool: mockCallTool },
    isConnected: true
  })
}))

function renderSetupPage() {
  return render(
    <BrowserRouter>
      <SetupPage />
    </BrowserRouter>
  )
}

// Helper to get password field by placeholder
function getPasswordField() {
  return screen.getByPlaceholderText('Admin Password')
}

function getConfirmPasswordField() {
  return screen.getByPlaceholderText('Confirm Admin Password')
}

describe('SetupPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockUseSystemSetup.mockReturnValue({
      needsSetup: true,
      isLoading: false
    })
    mockCallTool.mockResolvedValue({
      success: true,
      data: { success: true, message: 'Admin created' }
    })
  })

  describe('Rendering and UI', () => {
    it('should render setup form correctly', async () => {
      renderSetupPage()

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /welcome to tomo assistant/i })).toBeInTheDocument()
      })
      expect(screen.getByText(/let's set up your admin account/i)).toBeInTheDocument()
      expect(screen.getByRole('textbox', { name: /admin username/i })).toBeInTheDocument()
      expect(getPasswordField()).toBeInTheDocument()
      expect(getConfirmPasswordField()).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /create admin account/i })).toBeInTheDocument()
    })

    it('should show logo in header', async () => {
      renderSetupPage()

      await waitFor(() => {
        const logo = screen.getByRole('img', { name: /tomo assistant logo/i })
        expect(logo).toBeInTheDocument()
      })
    })

    it('should initially disable submit button', async () => {
      renderSetupPage()

      await waitFor(() => {
        const submitButton = screen.getByRole('button', { name: /create admin account/i })
        expect(submitButton).toBeDisabled()
      })
    })

    it('should show loading state while checking setup status', () => {
      mockUseSystemSetup.mockReturnValue({
        needsSetup: true,
        isLoading: true
      })

      renderSetupPage()

      expect(screen.getByText(/loading/i)).toBeInTheDocument()
    })
  })

  describe('Form Validation', () => {
    it('should show validation error for short username', async () => {
      const user = userEvent.setup()
      renderSetupPage()

      await waitFor(() => {
        expect(screen.getByRole('textbox', { name: /admin username/i })).toBeInTheDocument()
      })

      const usernameInput = screen.getByRole('textbox', { name: /admin username/i })
      await user.type(usernameInput, 'ab')
      await user.tab()

      await waitFor(() => {
        expect(screen.getByText(/username must be at least 3 characters/i)).toBeInTheDocument()
      })
    })

    it('should show password requirements', async () => {
      const user = userEvent.setup()
      renderSetupPage()

      await waitFor(() => {
        expect(getPasswordField()).toBeInTheDocument()
      })

      const passwordInput = getPasswordField()
      await user.type(passwordInput, 'weak')

      // Should show password requirements (look for the list element that contains requirements)
      await waitFor(() => {
        // The password strength indicator should show requirement feedback
        const listItems = screen.getAllByRole('listitem')
        expect(listItems.length).toBeGreaterThan(0)
      })
    })

    it('should show password mismatch error', async () => {
      const user = userEvent.setup()
      renderSetupPage()

      await waitFor(() => {
        expect(getPasswordField()).toBeInTheDocument()
      })

      const passwordInput = getPasswordField()
      const confirmPasswordInput = getConfirmPasswordField()

      await user.type(passwordInput, 'StrongPassword123!')
      await user.type(confirmPasswordInput, 'DifferentPassword123!')
      await user.tab()

      await waitFor(() => {
        expect(screen.getByText(/passwords do not match/i)).toBeInTheDocument()
      })
    })
  })

  describe('Password Visibility Toggle', () => {
    it('should toggle password visibility', async () => {
      const user = userEvent.setup()
      renderSetupPage()

      await waitFor(() => {
        expect(getPasswordField()).toBeInTheDocument()
      })

      const passwordInput = getPasswordField() as HTMLInputElement
      expect(passwordInput.type).toBe('password')

      // Find and click the toggle button (first one for password field)
      const toggleButtons = screen.getAllByRole('button').filter(btn =>
        btn.querySelector('svg')
      )

      if (toggleButtons.length > 0) {
        await user.click(toggleButtons[0])
        expect(passwordInput.type).toBe('text')
      }
    })
  })

  describe('Form Submission', () => {
    it('should enable submit button when form is valid', async () => {
      const user = userEvent.setup()
      renderSetupPage()

      await waitFor(() => {
        expect(screen.getByRole('textbox', { name: /admin username/i })).toBeInTheDocument()
      })

      const usernameInput = screen.getByRole('textbox', { name: /admin username/i })
      const passwordInput = getPasswordField()
      const confirmPasswordInput = getConfirmPasswordField()

      await user.type(usernameInput, 'adminuser')
      await user.type(passwordInput, 'StrongPassword123!')
      await user.type(confirmPasswordInput, 'StrongPassword123!')

      await waitFor(() => {
        const submitButton = screen.getByRole('button', { name: /create admin account/i })
        expect(submitButton).not.toBeDisabled()
      })
    })

    it('should show success message after successful submission', async () => {
      const user = userEvent.setup()
      renderSetupPage()

      await waitFor(() => {
        expect(screen.getByRole('textbox', { name: /admin username/i })).toBeInTheDocument()
      })

      const usernameInput = screen.getByRole('textbox', { name: /admin username/i })
      const passwordInput = getPasswordField()
      const confirmPasswordInput = getConfirmPasswordField()

      await user.type(usernameInput, 'adminuser')
      await user.type(passwordInput, 'StrongPassword123!')
      await user.type(confirmPasswordInput, 'StrongPassword123!')

      const submitButton = screen.getByRole('button', { name: /create admin account/i })
      await waitFor(() => {
        expect(submitButton).not.toBeDisabled()
      })

      await user.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/setup complete/i)).toBeInTheDocument()
      })
    })

    it('should show error message on failed submission', async () => {
      mockCallTool.mockResolvedValue({
        success: false,
        message: 'Server error'
      })

      const user = userEvent.setup()
      renderSetupPage()

      await waitFor(() => {
        expect(screen.getByRole('textbox', { name: /admin username/i })).toBeInTheDocument()
      })

      const usernameInput = screen.getByRole('textbox', { name: /admin username/i })
      const passwordInput = getPasswordField()
      const confirmPasswordInput = getConfirmPasswordField()

      await user.type(usernameInput, 'adminuser')
      await user.type(passwordInput, 'StrongPassword123!')
      await user.type(confirmPasswordInput, 'StrongPassword123!')

      const submitButton = screen.getByRole('button', { name: /create admin account/i })
      await waitFor(() => {
        expect(submitButton).not.toBeDisabled()
      })

      await user.click(submitButton)

      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument()
      })
    })
  })

  describe('Security Features', () => {
    it('should have secure password fields', async () => {
      renderSetupPage()

      await waitFor(() => {
        expect(getPasswordField()).toBeInTheDocument()
      })

      const passwordInput = getPasswordField()
      const confirmPasswordInput = getConfirmPasswordField()

      expect(passwordInput).toHaveAttribute('type', 'password')
      expect(passwordInput).toHaveAttribute('autocomplete', 'new-password')
      expect(confirmPasswordInput).toHaveAttribute('type', 'password')
      expect(confirmPasswordInput).toHaveAttribute('autocomplete', 'new-password')
    })
  })

  describe('Accessibility', () => {
    it('should have accessible form structure', async () => {
      renderSetupPage()

      await waitFor(() => {
        expect(screen.getByRole('heading', { level: 4 })).toBeInTheDocument()
      })
      expect(screen.getByRole('textbox', { name: /admin username/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /create admin account/i })).toBeInTheDocument()
    })
  })
})
