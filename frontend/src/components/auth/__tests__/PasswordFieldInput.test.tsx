/**
 * PasswordFieldInput Test Suite
 *
 * Tests for the PasswordFieldInput component including rendering,
 * visibility toggle, validation, and accessibility.
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { PasswordFieldInput } from '../PasswordFieldInput'

describe('PasswordFieldInput', () => {
  const defaultProps = {
    id: 'password',
    label: 'Password',
    value: '',
    placeholder: 'Enter password',
    showPassword: false,
    isValid: true,
    isSubmitting: false,
    autoComplete: 'current-password',
    onChange: vi.fn(),
    onToggleVisibility: vi.fn()
  }

  // Helper to get the password input by placeholder
  const getPasswordInput = () => screen.getByPlaceholderText('Enter password')

  describe('Rendering', () => {
    it('should render password input', () => {
      render(<PasswordFieldInput {...defaultProps} />)

      expect(getPasswordInput()).toBeInTheDocument()
    })

    it('should render with label', () => {
      render(<PasswordFieldInput {...defaultProps} label="New Password" />)

      expect(screen.getByPlaceholderText('Enter password')).toBeInTheDocument()
    })

    it('should render with placeholder', () => {
      render(<PasswordFieldInput {...defaultProps} />)

      expect(screen.getByPlaceholderText('Enter password')).toBeInTheDocument()
    })

    it('should display current value', () => {
      render(<PasswordFieldInput {...defaultProps} value="secret123" />)

      expect(screen.getByDisplayValue('secret123')).toBeInTheDocument()
    })

    it('should render visibility toggle button', () => {
      render(<PasswordFieldInput {...defaultProps} />)

      expect(screen.getByRole('button', { name: /show password/i })).toBeInTheDocument()
    })
  })

  describe('Password Visibility', () => {
    it('should show password field type when showPassword is false', () => {
      render(<PasswordFieldInput {...defaultProps} showPassword={false} />)

      expect(getPasswordInput()).toHaveAttribute('type', 'password')
    })

    it('should show text field type when showPassword is true', () => {
      render(<PasswordFieldInput {...defaultProps} showPassword={true} />)

      expect(getPasswordInput()).toHaveAttribute('type', 'text')
    })

    it('should call onToggleVisibility when visibility button clicked', async () => {
      const user = userEvent.setup()
      const onToggleVisibility = vi.fn()
      render(<PasswordFieldInput {...defaultProps} onToggleVisibility={onToggleVisibility} />)

      await user.click(screen.getByRole('button', { name: /show password/i }))

      expect(onToggleVisibility).toHaveBeenCalledTimes(1)
    })

    it('should show "Hide password" label when password is visible', () => {
      render(<PasswordFieldInput {...defaultProps} showPassword={true} />)

      expect(screen.getByRole('button', { name: /hide password/i })).toBeInTheDocument()
    })
  })

  describe('Error State', () => {
    it('should display error message', () => {
      render(<PasswordFieldInput {...defaultProps} error="Password is required" />)

      expect(screen.getByText('Password is required')).toBeInTheDocument()
    })

    it('should show error styling when error is present', () => {
      render(<PasswordFieldInput {...defaultProps} error="Invalid password" />)

      // MUI TextField adds aria-invalid when in error state
      expect(getPasswordInput()).toHaveAttribute('aria-invalid', 'true')
    })
  })

  describe('Disabled State', () => {
    it('should disable input when isSubmitting is true', () => {
      render(<PasswordFieldInput {...defaultProps} isSubmitting={true} />)

      expect(getPasswordInput()).toBeDisabled()
    })

    it('should disable visibility toggle when isSubmitting is true', () => {
      render(<PasswordFieldInput {...defaultProps} isSubmitting={true} />)

      expect(screen.getByRole('button', { name: /show password/i })).toBeDisabled()
    })

    it('should enable input when isSubmitting is false', () => {
      render(<PasswordFieldInput {...defaultProps} isSubmitting={false} />)

      expect(getPasswordInput()).not.toBeDisabled()
    })
  })

  describe('User Input', () => {
    it('should call onChange when user types', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      render(<PasswordFieldInput {...defaultProps} onChange={onChange} />)

      await user.type(getPasswordInput(), 'a')

      expect(onChange).toHaveBeenCalledWith('a')
    })

    it('should call onChange for each character', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      render(<PasswordFieldInput {...defaultProps} onChange={onChange} />)

      await user.type(getPasswordInput(), 'abc')

      expect(onChange).toHaveBeenCalledTimes(3)
    })
  })

  describe('Accessibility', () => {
    it('should have correct id', () => {
      render(<PasswordFieldInput {...defaultProps} id="test-password" />)

      expect(getPasswordInput()).toHaveAttribute('id', 'test-password')
    })

    it('should have correct autoComplete attribute', () => {
      render(<PasswordFieldInput {...defaultProps} autoComplete="new-password" />)

      expect(getPasswordInput()).toHaveAttribute('autocomplete', 'new-password')
    })

    it('should be marked as required', () => {
      render(<PasswordFieldInput {...defaultProps} />)

      expect(getPasswordInput()).toHaveAttribute('required')
    })
  })
})
