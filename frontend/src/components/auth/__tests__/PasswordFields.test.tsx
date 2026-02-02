/**
 * PasswordFields Test Suite
 *
 * Tests for the PasswordFields component.
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { PasswordFields } from '../PasswordFields'
import { RegistrationFormState } from '@/types/auth'
import { FormHandlers } from '@/utils/registrationFormHandlers'

describe('PasswordFields', () => {
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
    it('should render password fields', () => {
      render(<PasswordFields {...defaultProps} />)

      // Find by placeholder text since labels might not be directly associated
      expect(screen.getByPlaceholderText('Create password')).toBeInTheDocument()
      expect(screen.getByPlaceholderText('Confirm password')).toBeInTheDocument()
    })

    it('should render terms checkbox', () => {
      render(<PasswordFields {...defaultProps} />)

      expect(screen.getByRole('checkbox')).toBeInTheDocument()
    })

    it('should render submit button', () => {
      render(<PasswordFields {...defaultProps} />)

      expect(screen.getByRole('button', { name: 'Create Account' })).toBeInTheDocument()
    })
  })

  describe('Password Strength Indicator', () => {
    it('should not show password strength when not available', () => {
      render(
        <PasswordFields
          {...defaultProps}
          formState={createFormState({
            password: { value: '', error: '', isValid: false }
          })}
        />
      )

      expect(screen.queryByText('Fair')).not.toBeInTheDocument()
      expect(screen.queryByText('Weak')).not.toBeInTheDocument()
      expect(screen.queryByText('Strong')).not.toBeInTheDocument()
    })
  })

  describe('Form Submission', () => {
    it('should disable submit button when form is invalid', () => {
      render(
        <PasswordFields
          {...defaultProps}
          formHandlers={createFormHandlers({ isFormValid: false })}
        />
      )

      expect(screen.getByRole('button', { name: 'Create Account' })).toBeDisabled()
    })

    it('should enable submit button when form is valid', () => {
      render(
        <PasswordFields
          {...defaultProps}
          formHandlers={createFormHandlers({ isFormValid: true })}
        />
      )

      expect(screen.getByRole('button', { name: 'Create Account' })).not.toBeDisabled()
    })

    it('should show loading state when submitting', () => {
      render(
        <PasswordFields
          {...defaultProps}
          formState={createFormState({ isSubmitting: true })}
        />
      )

      // When loading, button shows a spinner
      expect(screen.getByLabelText('Loading')).toBeInTheDocument()
    })

    it('should disable submit button when submitting', () => {
      render(
        <PasswordFields
          {...defaultProps}
          formState={createFormState({ isSubmitting: true })}
          formHandlers={createFormHandlers({ isFormValid: true })}
        />
      )

      // Find the submit button (type="submit")
      const submitButton = screen.getByRole('button', { name: '' })
      expect(submitButton).toBeDisabled()
    })
  })

  describe('User Interactions', () => {
    it('should call handleInputChange when password changes', async () => {
      const user = userEvent.setup()
      const handleInputChange = vi.fn()
      render(
        <PasswordFields
          {...defaultProps}
          formHandlers={createFormHandlers({ handleInputChange })}
        />
      )

      const passwordInput = screen.getByPlaceholderText('Create password')
      await user.type(passwordInput, 'a')

      expect(handleInputChange).toHaveBeenCalledWith('password', expect.any(String))
    })

    it('should call handleInputChange when confirm password changes', async () => {
      const user = userEvent.setup()
      const handleInputChange = vi.fn()
      render(
        <PasswordFields
          {...defaultProps}
          formHandlers={createFormHandlers({ handleInputChange })}
        />
      )

      const confirmPasswordInput = screen.getByPlaceholderText('Confirm password')
      await user.type(confirmPasswordInput, 'a')

      expect(handleInputChange).toHaveBeenCalledWith('confirmPassword', expect.any(String))
    })

    it('should call handleTermsChange when terms checkbox changes', async () => {
      const user = userEvent.setup()
      const handleTermsChange = vi.fn()
      render(
        <PasswordFields
          {...defaultProps}
          formHandlers={createFormHandlers({ handleTermsChange })}
        />
      )

      const checkbox = screen.getByRole('checkbox')
      await user.click(checkbox)

      expect(handleTermsChange).toHaveBeenCalled()
    })

    it('should call onTogglePassword when visibility toggled', async () => {
      const user = userEvent.setup()
      const onTogglePassword = vi.fn()
      render(
        <PasswordFields
          {...defaultProps}
          onTogglePassword={onTogglePassword}
        />
      )

      // Find the show password button
      const toggleButton = screen.getAllByLabelText('Show password')[0]
      await user.click(toggleButton)

      expect(onTogglePassword).toHaveBeenCalled()
    })
  })

  describe('Error Display', () => {
    it('should show password error', () => {
      render(
        <PasswordFields
          {...defaultProps}
          formState={createFormState({
            password: { value: '', error: 'Password is required', isValid: false }
          })}
        />
      )

      expect(screen.getByText('Password is required')).toBeInTheDocument()
    })

    it('should show confirm password error', () => {
      render(
        <PasswordFields
          {...defaultProps}
          formState={createFormState({
            confirmPassword: { value: '', error: 'Passwords do not match', isValid: false }
          })}
        />
      )

      expect(screen.getByText('Passwords do not match')).toBeInTheDocument()
    })
  })
})
