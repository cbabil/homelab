/**
 * BasicFormFields Test Suite
 *
 * Tests for the BasicFormFields component (username input)
 * including rendering, validation, and user interactions.
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BasicFormFields } from '../BasicFormFields'
import { RegistrationFormState } from '@/types/auth'
import { FormHandlers } from '@/utils/registrationFormHandlers'

const createFormState = (
  overrides: Partial<RegistrationFormState> = {}
): RegistrationFormState => ({
  username: { value: '', error: '', isValid: false },
  email: { value: '', error: '', isValid: false },
  password: { value: '', error: '', isValid: false },
  confirmPassword: { value: '', error: '', isValid: false },
  acceptTerms: { value: false, error: '', isValid: false },
  isSubmitting: false,
  ...overrides
})

const createFormHandlers = (
  overrides: Partial<FormHandlers> = {}
): FormHandlers => ({
  handleInputChange: vi.fn(),
  handleTermsChange: vi.fn(),
  handleSubmit: vi.fn(async (e) => e.preventDefault()),
  isFormValid: false,
  ...overrides
})

describe('BasicFormFields', () => {
  describe('Rendering', () => {
    it('should render username input', () => {
      render(
        <BasicFormFields
          formState={createFormState()}
          formHandlers={createFormHandlers()}
        />
      )

      expect(screen.getByLabelText(/username/i)).toBeInTheDocument()
    })

    it('should render with placeholder', () => {
      render(
        <BasicFormFields
          formState={createFormState()}
          formHandlers={createFormHandlers()}
        />
      )

      expect(screen.getByPlaceholderText('Enter username')).toBeInTheDocument()
    })

    it('should display current value', () => {
      render(
        <BasicFormFields
          formState={createFormState({
            username: { value: 'testuser', error: '', isValid: true }
          })}
          formHandlers={createFormHandlers()}
        />
      )

      expect(screen.getByDisplayValue('testuser')).toBeInTheDocument()
    })

    it('should be marked as required', () => {
      render(
        <BasicFormFields
          formState={createFormState()}
          formHandlers={createFormHandlers()}
        />
      )

      expect(screen.getByLabelText(/username/i)).toHaveAttribute('required')
    })
  })

  describe('Error State', () => {
    it('should display error message', () => {
      render(
        <BasicFormFields
          formState={createFormState({
            username: { value: '', error: 'Username is required', isValid: false }
          })}
          formHandlers={createFormHandlers()}
        />
      )

      expect(screen.getByText('Username is required')).toBeInTheDocument()
    })

    it('should show error styling when error is present', () => {
      render(
        <BasicFormFields
          formState={createFormState({
            username: { value: '', error: 'Invalid username', isValid: false }
          })}
          formHandlers={createFormHandlers()}
        />
      )

      expect(screen.getByLabelText(/username/i)).toHaveAttribute('aria-invalid', 'true')
    })
  })

  describe('Disabled State', () => {
    it('should disable input when isSubmitting is true', () => {
      render(
        <BasicFormFields
          formState={createFormState({ isSubmitting: true })}
          formHandlers={createFormHandlers()}
        />
      )

      expect(screen.getByLabelText(/username/i)).toBeDisabled()
    })

    it('should enable input when isSubmitting is false', () => {
      render(
        <BasicFormFields
          formState={createFormState({ isSubmitting: false })}
          formHandlers={createFormHandlers()}
        />
      )

      expect(screen.getByLabelText(/username/i)).not.toBeDisabled()
    })
  })

  describe('User Input', () => {
    it('should call handleInputChange when user types', async () => {
      const user = userEvent.setup()
      const handleInputChange = vi.fn()
      render(
        <BasicFormFields
          formState={createFormState()}
          formHandlers={createFormHandlers({ handleInputChange })}
        />
      )

      await user.type(screen.getByLabelText(/username/i), 'a')

      expect(handleInputChange).toHaveBeenCalledWith('username', 'a')
    })

    it('should call handleInputChange with full value', async () => {
      const user = userEvent.setup()
      const handleInputChange = vi.fn()
      render(
        <BasicFormFields
          formState={createFormState()}
          formHandlers={createFormHandlers({ handleInputChange })}
        />
      )

      await user.type(screen.getByLabelText(/username/i), 'test')

      // Called for each character
      expect(handleInputChange).toHaveBeenCalledTimes(4)
    })
  })

  describe('Accessibility', () => {
    it('should have correct id', () => {
      render(
        <BasicFormFields
          formState={createFormState()}
          formHandlers={createFormHandlers()}
        />
      )

      expect(screen.getByLabelText(/username/i)).toHaveAttribute('id', 'reg-username')
    })

    it('should have correct autoComplete attribute', () => {
      render(
        <BasicFormFields
          formState={createFormState()}
          formHandlers={createFormHandlers()}
        />
      )

      expect(screen.getByLabelText(/username/i)).toHaveAttribute('autocomplete', 'username')
    })

    it('should have type="text"', () => {
      render(
        <BasicFormFields
          formState={createFormState()}
          formHandlers={createFormHandlers()}
        />
      )

      expect(screen.getByLabelText(/username/i)).toHaveAttribute('type', 'text')
    })
  })
})
