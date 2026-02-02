/**
 * RegistrationForm Test Suite
 *
 * Tests for the RegistrationForm component.
 */

import React from 'react'
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { RegistrationForm } from '../RegistrationForm'
import { RegistrationFormState } from '@/types/auth'
import { FormHandlers } from '@/utils/registrationFormHandlers'

// Mock i18n
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        'auth.haveAccount': 'Already have an account?',
        'auth.signIn': 'Sign in'
      }
      return translations[key] || key
    }
  })
}))

function renderWithRouter(ui: React.ReactElement) {
  return render(<BrowserRouter>{ui}</BrowserRouter>)
}

describe('RegistrationForm', () => {
  const createFormState = (overrides: Partial<RegistrationFormState> = {}): RegistrationFormState => ({
    username: { value: '', error: '', isValid: false },
    email: { value: '', error: '', isValid: false },
    password: { value: '', error: '', isValid: false },
    confirmPassword: { value: '', error: '', isValid: false },
    acceptTerms: { value: false, error: '', isValid: false },
    isSubmitting: false,
    submitError: undefined,
    ...overrides
  })

  const createFormHandlers = (overrides: Partial<FormHandlers> = {}): FormHandlers => ({
    handleInputChange: vi.fn(),
    handleTermsChange: vi.fn(),
    handleSubmit: vi.fn(async (e) => e.preventDefault()),
    isFormValid: false,
    ...overrides
  })

  const defaultProps = {
    formState: createFormState(),
    formHandlers: createFormHandlers(),
    showPassword: false,
    showConfirmPassword: false,
    onTogglePassword: vi.fn(),
    onToggleConfirmPassword: vi.fn()
  }

  describe('Rendering', () => {
    it('should render basic form fields', () => {
      renderWithRouter(<RegistrationForm {...defaultProps} />)

      // BasicFormFields should be rendered - check by placeholder
      expect(screen.getByPlaceholderText('Enter username')).toBeInTheDocument()
    })

    it('should render password fields', () => {
      renderWithRouter(<RegistrationForm {...defaultProps} />)

      expect(screen.getByPlaceholderText('Create password')).toBeInTheDocument()
      expect(screen.getByPlaceholderText('Confirm password')).toBeInTheDocument()
    })

    it('should render sign in link', () => {
      renderWithRouter(<RegistrationForm {...defaultProps} />)

      expect(screen.getByText('Already have an account?')).toBeInTheDocument()
      expect(screen.getByRole('link', { name: 'Sign in' })).toBeInTheDocument()
    })

    it('should link to login page', () => {
      renderWithRouter(<RegistrationForm {...defaultProps} />)

      const signInLink = screen.getByRole('link', { name: 'Sign in' })
      expect(signInLink).toHaveAttribute('href', '/login')
    })
  })

  describe('Error Display', () => {
    it('should show submit error when present in formState', () => {
      renderWithRouter(
        <RegistrationForm
          {...defaultProps}
          formState={createFormState({ submitError: 'Registration failed' })}
        />
      )

      expect(screen.getByText('Registration failed')).toBeInTheDocument()
    })

    it('should show error prop when provided', () => {
      renderWithRouter(
        <RegistrationForm
          {...defaultProps}
          error="An error occurred"
        />
      )

      expect(screen.getByText('An error occurred')).toBeInTheDocument()
    })

    it('should show error in alert component', () => {
      renderWithRouter(
        <RegistrationForm
          {...defaultProps}
          formState={createFormState({ submitError: 'Error message' })}
        />
      )

      expect(screen.getByRole('alert')).toBeInTheDocument()
    })

    it('should not show alert when no errors', () => {
      renderWithRouter(<RegistrationForm {...defaultProps} />)

      expect(screen.queryByRole('alert')).not.toBeInTheDocument()
    })
  })

  describe('Form State', () => {
    it('should pass form state values to child components', () => {
      renderWithRouter(
        <RegistrationForm
          {...defaultProps}
          formState={createFormState({
            username: { value: 'testuser', error: '', isValid: true }
          })}
        />
      )

      expect(screen.getByDisplayValue('testuser')).toBeInTheDocument()
    })
  })
})
